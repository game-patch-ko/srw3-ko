"""SRW3 script extraction / insertion.

  python srwtext.py extract            -> ../script/*.txt   (only creates files that do not exist)
  python srwtext.py extract --force    -> overwrite script files (translations are lost!)
  python srwtext.py build              -> ../out/srw3_ko.smc  (hooks + font + relocated text)
  python srwtext.py build --no-tr      -> ../out/srw3_reloc_only.smc (ignore translations; regression test)

Model
  * A "block" is a 16-bit pointer table whose strings live in the same bank.
    Dialogue blocks are listed in $80:D2D7, name/system tables in $80:D277.
  * Every pointer target gets a label  S<file offset>.  Text is cut into segments at labels;
    segments of one region must stay contiguous (a segment without {END} falls through).
  * Blocks that share labels form one group and are rebuilt into the same bank.
  * KO line empty  -> original bytes are kept (pointers relocated).
"""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'Dai-3-Ji Super Robot Taisen (J).smc')
SCRIPT_DIR = os.path.join(ROOT, 'script')
OUT = os.path.join(ROOT, 'out', 'srw3_ko.smc')
TBL = os.path.join(ROOT, 'analysis', 'srw3_jp.tbl')

sys.path.insert(0, HERE)
import kofont  # noqa: E402

D2D7 = 0x52D7   # dialogue block table (16 x 24-bit)
D277 = 0x5277   # system table list (32 x 24-bit)
LAYOUT_TABLES = (0x1BB0F, 0x1D830, 0x63D77)   # D277 00 / 01 / 08
LAYOUT_FRAME_TABLE = 0x1EB51                   # D277 02: frames only, stays in place
EDA2 = 0x81EDA2  # LDA $03BB0F,x  (route names, table 00 entries $92+)
EDA8 = 0x81EDA8  # LDA #$0003     (bank of those strings)
TEXT_BANKS = list(range(0xB4, 0xC0))   # free banks for relocated text
DLG_MAX_PX = 240                       # $0E34 = 60 units (4px), measured 2026-11-18; over it the game drops the char and wraps
DLG_CONT_PX = 232                      # continuation lines start at 2 units (indent)
NAME_PX = 48                           # {name:xx} pilot name: 4 hangul covers all but a few enemy short names (sys11)
DLG_MAX_LINES = 3                      # lines per dialogue window (no original speech has more)
BATTLE_GROUPS = {'dlg01', 'dlg0C', 'dlg0D'}  # battle-screen speech: $0E34 = 50 units, 2-line window (measured)
BTL_MAX_PX, BTL_CONT_PX, BTL_MAX_LINES = 200, 192, 2
LAY_MAX_PX = 232                       # layout text run (prologue: 240px+ wraps around)

# ---------------------------------------------------------------- character tables
JP = {}
for line in open(TBL, encoding='utf-8'):
    line = line.rstrip('\n')
    if '=' in line and not line.startswith('F3') and not line.startswith('FF'):
        k, v = line.split('=', 1)
        JP[bytes.fromhex(k)] = v
JP_SINGLE_INV = {}
for k, v in JP.items():
    if len(k) == 1 and len(v) == 1 and v not in JP_SINGLE_INV:
        JP_SINGLE_INV[v] = k[0]
# bracketed glyph names like [AL] (E6) [L] (E7): one byte, written as several characters
JP_MULTI = sorted((v for k, v in JP.items() if len(k) == 1 and len(v) > 1 and v.startswith('[')), key=len, reverse=True)
for v in JP_MULTI:
    JP_SINGLE_INV.setdefault(v, next(k[0] for k, x in JP.items() if len(k) == 1 and x == v))
KO_EXTRA = {',': 0x3A, '.': 0xE4, '~': 0x13, '-': 0x11, ':': 0xE5, '=': 0xE3, '…': 0x0A}


def f2s(o):
    return 0x800000 | (o // 0x8000) << 16 | (0x8000 + o % 0x8000)


def s2f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + ((a & 0xFFFF) - 0x8000)


def lab(o):
    return 'S%06X' % o


# ---------------------------------------------------------------- tokenizer
# token: (kind, data)
#   ch   : raw glyph bytes (1 or 2)
#   ctl  : raw control bytes without pointer
#   if   : (argword, target)          F9 aa aa pp pp
#   goto : target                     F9 pp pp   (terminates)
#   rand : [targets]                  F7 n pp..
#   f8j  : (sub, target)              F8 06/07 pp pp
#   end  : None                       FF
TWO_BYTE = (0xF0, 0xF1, 0xF2)


def tokenize(rom, o, stop=None):
    """tokens from o until a terminator (FF or F9-goto) or until offset stop"""
    bank = o // 0x8000
    base = bank * 0x8000 - 0x8000
    toks = []
    i = o
    while True:
        if stop is not None and i >= stop:
            return toks, i
        c = rom[i]
        if c == 0xFF:
            toks.append(('end', None)); return toks, i + 1
        if c in TWO_BYTE:
            toks.append(('ch', bytes(rom[i:i + 2]))); i += 2; continue
        if c < 0xF3:
            toks.append(('ch', bytes([c]))); i += 1; continue
        if c in (0xF3, 0xF4, 0xFC, 0xFE):
            toks.append(('ctl', bytes([c]))); i += 1; continue
        if c in (0xF5, 0xFA, 0xFD):
            toks.append(('ctl', bytes(rom[i:i + 2]))); i += 2; continue
        if c in (0xF6, 0xFB):
            toks.append(('ctl', bytes(rom[i:i + 3]))); i += 3; continue
        if c == 0xF8:
            sub = rom[i + 1]
            if sub in (6, 7):
                p = rom[i + 2] | rom[i + 3] << 8
                toks.append(('f8j', (sub, base + p))); i += 4; continue
            toks.append(('ctl', bytes(rom[i:i + 4]))); i += 4; continue
        if c == 0xF9:
            a = rom[i + 1] | rom[i + 2] << 8
            if a >= 0x8000:
                toks.append(('goto', base + a)); return toks, i + 3
            p = rom[i + 3] | rom[i + 4] << 8
            toks.append(('if', (a, base + p))); i += 5; continue
        if c == 0xF7:
            n = rom[i + 1]
            ts = [base + (rom[i + 2 + 2 * k] | rom[i + 3 + 2 * k] << 8) for k in range(n)]
            toks.append(('rand', ts)); i += 2 + 2 * n; continue
        raise ValueError('unknown byte %02X at %06X' % (c, i))


def tok_targets(t):
    k, d = t
    if k == 'if':
        return [d[1]]
    if k == 'goto':
        return [d]
    if k == 'rand':
        return list(d)
    if k == 'f8j':
        return [d[1]]
    return []


# window-layout interpreter ($80:C7F5, jump table $80:D257): argument bytes incl. opcode
LAY_LEN = {0xF0: 4, 0xF1: 3, 0xF2: 2, 0xF3: 1, 0xF4: 2, 0xF5: 2, 0xF6: 3, 0xF7: 5,
           0xF8: 4, 0xF9: 4, 0xFA: 2, 0xFB: 1, 0xFC: 3, 0xFD: 3, 0xFE: 2}


def tokenize_lay(rom, o, stop=None, text=False, calls=None, resolve=None, modes=None):
    """layout stream: tile mode (bytes = tile numbers) or text mode (F4 arg bit6).
    returns tokens, end offset, text mode at end.  F6 calls -> calls list (entry, table, text)"""
    toks = []
    i = o
    while True:
        if stop is not None and i >= stop:
            return toks, i, text
        c = rom[i]
        if c == 0xFF:
            toks.append(('end', None))
            if modes is not None:
                modes.append(text)
            return toks, i + 1, text
        if text and c in TWO_BYTE:
            toks.append(('ch', bytes(rom[i:i + 2]))); i += 2; continue
        if c >= 0xF0 and not (text and c < 0xF3):
            n = LAY_LEN[c]
            b = bytes(rom[i:i + n])
            if c == 0xF4:
                text = bool(b[1] & 0x40)
            if c == 0xF6 and calls is not None:
                calls.append((b[1], b[2], text))
            toks.append(('ctl', b)); i += n
            if c == 0xF6 and resolve is not None:
                text = resolve(b[1], b[2], text)   # callee may leave text mode on
            if modes is not None:
                modes.append(text)
            continue
        if text:
            toks.append(('ch', bytes([c])))
        elif toks and toks[-1][0] == 'tile':
            toks[-1] = ('tile', toks[-1][1] + bytes([c]))
        else:
            toks.append(('tile', bytes([c])))
            if modes is not None:
                modes.append(text)
        i += 1


# ---------------------------------------------------------------- text <-> tokens
def tok_to_text(t, lay=False):
    k, d = t
    if k == 'tile':
        return '{t:%s}' % d.hex().upper()
    if lay and k == 'ctl' and d[0] != 0xF3:
        return '{%s}' % ':'.join('%02X' % x for x in d)
    if k == 'ch':
        return JP.get(d, '{$%s}' % d.hex().upper())
    if k == 'end':
        return '{END}'
    if k == 'goto':
        return '{goto:%s}' % lab(d)
    if k == 'if':
        return '{if:%04X:%s}' % (d[0], lab(d[1]))
    if k == 'rand':
        return '{rand:%s}' % ','.join(lab(x) for x in d)
    if k == 'f8j':
        return '{F8:%02X:%s}' % (d[0], lab(d[1]))
    b = d
    if b[0] == 0xF3:
        return '{n}'
    if b[0] == 0xF4:
        return '{w}'
    if b[0] == 0xFD:
        return '{face:%02X}' % b[1]
    if b[0] == 0xFA:
        return '{name:%02X}' % b[1]
    return '{%s}' % ':'.join('%02X' % x for x in b)


TAG = re.compile(r'\{([^}]*)\}')


def text_to_tokens(s, where):
    toks = []
    pos = 0
    for m in list(TAG.finditer(s)) + [None]:
        chunk = s[pos:m.start()] if m else s[pos:]
        i = 0
        while i < len(chunk):
            multi = next((k for k in JP_MULTI if chunk.startswith(k, i)), None)
            if multi:                      # named single-byte glyphs such as [AL] [L]
                toks.append(('ch', bytes([JP_SINGLE_INV[multi]])))
                i += len(multi)
                continue
            ch = chunk[i]
            i += 1
            if ch in kofont.HANGUL_INDEX:
                toks.append(('ch', kofont.code_bytes(kofont.HANGUL_INDEX[ch])))
            elif ch in JP_SINGLE_INV:
                toks.append(('ch', bytes([JP_SINGLE_INV[ch]])))
            elif ch in KO_EXTRA:
                toks.append(('ch', bytes([KO_EXTRA[ch]])))
            else:
                raise ValueError('%s: cannot encode %r (not in KS X 1001 hangul / single-byte table)' % (where, ch))
        if not m:
            break
        tag = m.group(1)
        pos = m.end()
        if tag == 'n':
            toks.append(('ctl', b'\xF3'))
        elif tag == 'w':
            toks.append(('ctl', b'\xF4'))
        elif tag == 'END':
            toks.append(('end', None))
        elif tag.startswith('face:'):
            toks.append(('ctl', bytes([0xFD, int(tag[5:], 16)])))
        elif tag.startswith('name:'):
            toks.append(('ctl', bytes([0xFA, int(tag[5:], 16)])))
        elif tag.startswith('goto:'):
            toks.append(('goto', int(tag[6:], 16)))
        elif tag.startswith('if:'):
            _, a, l = tag.split(':')
            toks.append(('if', (int(a, 16), int(l[1:], 16))))
        elif tag.startswith('rand:'):
            toks.append(('rand', [int(x[1:], 16) for x in tag[5:].split(',')]))
        elif tag.startswith('F8:') and tag.count(':') == 2 and tag.split(':')[2].startswith('S'):
            _, sub, l = tag.split(':')
            toks.append(('f8j', (int(sub, 16), int(l[1:], 16))))
        elif tag.startswith('t:'):
            toks.append(('tile', bytes.fromhex(tag[2:])))
        elif tag.startswith('$'):
            toks.append(('ch', bytes.fromhex(tag[1:])))
        elif re.fullmatch(r'[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2})*', tag):
            toks.append(('ctl', bytes(int(x, 16) for x in tag.split(':'))))
        else:
            raise ValueError('%s: unknown tag {%s}' % (where, tag))
    return toks


def tok_width(toks):
    """pixel width of the widest line (1-byte glyph 8px, 2-byte 12px)"""
    best = cur = 0
    for k, d in toks:
        if k == 'ch':
            cur += 12 if len(d) == 2 else 8
        elif k == 'ctl' and d[0] in (0xF3, 0xF4, 0xFD):
            best = max(best, cur); cur = 0
    return max(best, cur)


def dlg_lines(toks):
    """(line index inside a speech, width) for dialogue; {w}/{face} start a new speech"""
    out = []
    cur = line = 0
    for k, d in toks:
        if k == 'ch':
            cur += 12 if len(d) == 2 else 8
        elif k == 'ctl' and d[0] == 0xFA and len(d) > 1 and 4 <= d[1] <= 7:
            cur += NAME_PX                 # {name:xx}: a pilot name inserted at run time
        elif k == 'ctl' and d[0] == 0xF3:
            out.append((line, cur)); cur = 0; line += 1
        elif k == 'ctl' and d[0] in (0xF4, 0xFD):
            if cur:
                out.append((line, cur))
            cur = 0; line = 0
    out.append((line, cur))
    return out


# ---------------------------------------------------------------- structure discovery
def table_len(rom, T, others):
    """entries until the smallest in-bank pointer (strings follow the table)"""
    bank = T // 0x8000
    n = 0
    lo = 0x10000
    while True:
        w = rom[T + 2 * n] | rom[T + 2 * n + 1] << 8
        if w >= 0x8000:
            lo = min(lo, w)
        n += 1
        if bank * 0x8000 + lo - 0x8000 <= T + 2 * n or (T + 2 * n) in others:
            return n


def discover(rom):
    """returns dict with blocks, groups, segments"""
    # ---- blocks
    blocks = {}   # table file offset -> info
    for i in range(16):
        v = rom[D2D7 + 3 * i] | rom[D2D7 + 3 * i + 1] << 8 | rom[D2D7 + 3 * i + 2] << 16
        if not (0x08 <= (v >> 16) & 0x7F <= 0x0C) or (v & 0xFFFF) < 0x8000:
            continue
        o = s2f(v)
        blocks.setdefault(o, {'kind': 'dlg', 'ids': [], 'list': 'D2D7'})['ids'].append(i)
    for i in range(0x10, 0x1B):
        v = rom[D277 + 3 * i] | rom[D277 + 3 * i + 1] << 8 | rom[D277 + 3 * i + 2] << 16
        o = s2f(v)
        blocks.setdefault(o, {'kind': 'sys', 'ids': [], 'list': 'D277'})['ids'].append(i)
    for i in range(0x00, 0x10):
        v = rom[D277 + 3 * i] | rom[D277 + 3 * i + 1] << 8 | rom[D277 + 3 * i + 2] << 16
        o = s2f(v)
        if o in LAYOUT_TABLES:
            blocks.setdefault(o, {'kind': 'lay', 'ids': [], 'list': 'D277'})['ids'].append(i)
    tables = set(blocks) | {LAYOUT_FRAME_TABLE}   # entries pointing at a table = unused marker
    fixed_len = {0x40000: 64, 0x4031E: 177}
    for T, b in blocks.items():
        b['n'] = fixed_len.get(T) or table_len(rom, T, tables)
        b['cmd'] = (T == 0x4031E)
    # ---- entries and roots
    labels = {}  # target -> set(owner table)
    cmds = {}    # cmd offset -> (prefix bytes, kind, targets)
    lmode = {}   # layout label -> starts in text mode

    def add(t, owner):
        labels.setdefault(t, set()).add(owner)

    for T, b in blocks.items():
        bank = T // 0x8000
        ents = []
        for k in range(b['n']):
            w = rom[T + 2 * k] | rom[T + 2 * k + 1] << 8
            t = bank * 0x8000 + w - 0x8000
            if w < 0x8000:
                ents.append(('raw', w))
            elif t in tables:
                ents.append(('dummy', w))
            elif b['cmd'] and rom[t] == 0xFA and rom[t + 2] in (0xF7, 0xF9):
                pre = bytes(rom[t:t + 2])
                op = rom[t + 2]
                if op == 0xF7:
                    n = rom[t + 3]
                    ts = [bank * 0x8000 + (rom[t + 4 + 2 * j] | rom[t + 5 + 2 * j] << 8) - 0x8000 for j in range(n)]
                    cmds[t] = (pre, 'rand', ts)
                else:
                    assert op == 0xF9
                    ts = [bank * 0x8000 + (rom[t + 3] | rom[t + 4] << 8) - 0x8000]
                    cmds[t] = (pre, 'goto', ts)
                for x in ts:
                    add(x, T)
                ents.append(('cmd', t))
            else:
                add(t, T)
                ents.append(('lab', t))
                if b['kind'] == 'lay':
                    # table 00 entries >= $92 are plain strings printed by $81:EDEA
                    text = (T == 0x1BB0F and k >= 0x92)
                    lmode[t] = lmode.get(t, False) or text
        b['ents'] = ents
    # ---- layout labels: end offsets, text mode inherited through F6 calls
    lay_id = {}
    for T, b in blocks.items():
        for i in b['ids']:
            if b['list'] == 'D277':
                lay_id[i] = T
    ends = {}
    memo = {}

    def resolve(entry, tbl, text, depth=0):
        T = lay_id.get(tbl)
        if T is None or blocks[T]['kind'] not in ('lay', 'sys') or entry >= blocks[T]['n'] or depth > 8:
            return text
        kind, x = blocks[T]['ents'][entry]
        if kind != 'lab':
            return text
        key = (x, text)
        if key not in memo:
            memo[key] = text
            memo[key] = tokenize_lay(rom, x, text=text,
                                     resolve=lambda e2, t2, m2: resolve(e2, t2, m2, depth + 1))[2]
        return memo[key]
    for t in list(lmode):
        # entries made only of characters are plain strings called in text mode
        if not lmode[t]:
            tk, _, _ = tokenize_lay(rom, t, text=True)
            if len(tk) > 1 and all(k in ('ch', 'end') for k, _ in tk):
                lmode[t] = True
    changed = True
    while changed:
        changed = False
        for t in list(lmode):
            calls = []
            _, e, _ = tokenize_lay(rom, t, text=lmode[t], calls=calls, resolve=resolve)
            ends[t] = e
            for entry, tbl, text in calls:
                T = lay_id.get(tbl)
                if T is None or blocks[T]['kind'] != 'lay' or entry >= blocks[T]['n']:
                    continue
                kind, x = blocks[T]['ents'][entry]
                if kind == 'lab' and text and not lmode[x]:
                    lmode[x] = True; changed = True
    # ---- follow pointers inside strings
    todo = [t for t in labels if t not in lmode]
    while todo:
        t = todo.pop()
        if t in ends:
            continue
        toks, e = tokenize(rom, t)
        ends[t] = e
        owners = labels[t]
        for tk in toks:
            for x in tok_targets(tk):
                for ow in owners:
                    add(x, ow)
                if x not in ends:
                    todo.append(x)
    # propagate owners until stable (labels reached from several owners)
    changed = True
    while changed:
        changed = False
        for t in list(ends):
            if t in lmode:
                continue
            toks, _ = tokenize(rom, t)
            for tk in toks:
                for x in tok_targets(tk):
                    if not labels[t] <= labels[x]:
                        labels[x] |= labels[t]; changed = True
    # ---- regions: merge overlapping [t, end)
    iv = sorted((t, ends[t]) for t in ends)
    regions = []
    for a, e in iv:
        if regions and a < regions[-1][1]:
            regions[-1][1] = max(regions[-1][1], e)
            regions[-1][2].append(a)
        else:
            regions.append([a, e, [a]])
    # ---- groups: union of tables sharing labels
    parent = {T: T for T in blocks}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for t, ow in labels.items():
        ow = list(ow)
        for o2 in ow[1:]:
            parent[find(o2)] = find(ow[0])
    for a, e, labs in regions:   # a contiguous region must stay in one bank
        ow = [o for l in labs for o in labels[l]]
        for o2 in ow[1:]:
            parent[find(o2)] = find(ow[0])
    groups = {}
    for T in blocks:
        groups.setdefault(find(T), []).append(T)
    # ---- segments per region
    segs = {}   # label -> dict(region, next, toks)
    region_of_group = {}
    for a, e, labs in regions:
        labs = sorted(set(labs))
        toks, _ = tokenize(rom, a, stop=None) if False else (None, None)
        g = find(next(iter(labels[a])))
        region_of_group.setdefault(g, []).append((a, e, labs))
        lay = a in lmode
        text = lmode.get(a, False)
        for i, l in enumerate(labs):
            stop = labs[i + 1] if i + 1 < len(labs) else None
            if lay:
                if l in FORCE_TEXT:
                    text = True            # string called from code in text mode (found on screen, 2026-11-18)
                start_text = text
                md = []
                tk, end, text = tokenize_lay(rom, l, stop=stop, text=text, resolve=resolve, modes=md)
            else:
                tk, end = tokenize(rom, l, stop=stop)
            if stop is not None and end != stop:
                raise ValueError('label %06X not on a token boundary' % stop)
            segs[l] = {'toks': tk, 'group': g, 'next': stop, 'lay': lay}
            if lay:
                segs[l]['text'] = start_text
                segs[l]['modes'] = md   # text mode after each non-character token
                if l in lmode and lmode[l] != start_text:
                    segs[l]['mode_conflict'] = True
    return {'blocks': blocks, 'groups': groups, 'regions': region_of_group, 'segs': segs,
            'cmds': cmds, 'labels': labels}


# ---------------------------------------------------------------- script files
def group_name(info, g):
    ts = sorted(info['groups'][g])
    b = info['blocks']
    parts = []
    for T in ts:
        if b[T]['kind'] == 'lay':
            parts.append('lay%02X' % b[T]['ids'][0])
            continue
        parts.append('%s%s' % ('dlg' if b[T]['kind'] == 'dlg' else 'sys',
                                '-'.join('%02X' % i for i in b[T]['ids'])))
    return '_'.join(parts)


HEADER = """# 제3차 슈퍼로봇대전 번역 스크립트  ({name})
# - 'KO:' 줄에 번역을 씁니다. 비워 두면 원문이 그대로 들어갑니다.
# - 태그는 지우거나 바꾸지 마세요(위치 이동은 가능):
#     {{n}} 줄바꿈  {{w}} 키 입력 대기  {{face:xx}} 얼굴  {{name:xx}} 이름 삽입  {{END}} 끝
#     {{if:..}} {{goto:..}} {{rand:..}} {{F8:..}} 은 분기(라벨 포함) — 반드시 유지
# - 한글은 KS X 1001 완성형 2,350자만 쓸 수 있습니다(예: 똠, 뷁 불가).
# - [라벨] 옆 '->' 는 이 조각이 {{END}} 없이 다음 조각으로 이어진다는 뜻입니다.
"""


LAY_HEADER = """# [창 레이아웃] 프롤로그·엔딩·상태창 등. 글자만 바꾸고 {..} 태그는 순서·값 모두 그대로 두세요.
#   {t:..} 창 틀 타일, {F4:40} 글자 모드 켜기, {F4:00} 타일 모드, {FD:xx:yy} 위치, {F5:xx} 대기
#   위치가 고정된 칸이 많으므로 원문보다 넓어지면 옆 칸을 덮을 수 있습니다(빌드 경고 확인).
"""


def write_scripts(info, force=False):
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    written = []
    for g, ts in sorted(info['groups'].items()):
        name = group_name(info, g)
        path = os.path.join(SCRIPT_DIR, name + '.txt')
        if os.path.exists(path) and not force:
            continue
        lines = [HEADER.format(name=name)]
        if any(info['blocks'][T]['kind'] == 'lay' for T in ts):
            lines.append(LAY_HEADER)
        refs = {}
        for T in ts:
            b = info['blocks'][T]
            for k, (kind, v) in enumerate(b['ents']):
                if kind == 'lab':
                    refs.setdefault(v, []).append('%s%02X#%02X' % ({'dlg': 'D', 'sys': 'N', 'lay': 'L'}[b['kind']], b['ids'][0], k))
        for a, e, labs in sorted(info['regions'].get(g, [])):
            for l in sorted(set(labs)):
                s = info['segs'][l]
                if s.get('lay') and not any(k == 'ch' for k, _ in s['toks']):
                    continue   # window frame without text: nothing to translate
                jp = ''.join(tok_to_text(t, s.get('lay')) for t in s['toks'])
                r = ' '.join(refs.get(l, [])[:4])
                lines.append('[%s]%s%s' % (lab(l), ' -> %s' % lab(s['next']) if s['next'] else '',
                                           ('  ' + r) if r else ''))
                lines.append('JP: ' + jp)
                lines.append('KO: ')
                lines.append('')
        open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        written.append(path)
    return written


def read_scripts():
    tr = {}
    if not os.path.isdir(SCRIPT_DIR):
        return tr
    for fn in sorted(os.listdir(SCRIPT_DIR)):
        if not fn.endswith('.txt'):
            continue
        cur = None
        for ln, line in enumerate(open(os.path.join(SCRIPT_DIR, fn), encoding='utf-8'), 1):
            line = line.rstrip('\n')
            m = re.match(r'\[S([0-9A-F]{6})\]', line)
            if m:
                cur = int(m.group(1), 16)
            elif line.startswith('KO:') and cur is not None:
                t = line[4:] if line.startswith('KO: ') else line[3:]   # leading spaces are text
                if t.strip():
                    if cur in tr:
                        raise ValueError('%s:%d: label S%06X already translated at %s' % (fn, ln, cur, tr[cur][1]))
                    tr[cur] = (t, '%s:%d' % (fn, ln))
    return tr


# ---------------------------------------------------------------- insertion
def ptr_targets_multiset(toks):
    out = []
    for t in toks:
        if t[0] in ('if', 'goto', 'rand', 'f8j'):
            out.append((t[0], tuple(tok_targets(t))))
    return sorted(out)


def encode_tokens(toks, addr_of):
    out = bytearray()
    for k, d in toks:
        if k in ('ch', 'ctl', 'tile'):
            out += d
        elif k == 'end':
            out.append(0xFF)
        elif k == 'goto':
            a = addr_of(d); out += bytes([0xF9, a & 0xFF, a >> 8])
        elif k == 'if':
            a = addr_of(d[1]); out += bytes([0xF9, d[0] & 0xFF, d[0] >> 8, a & 0xFF, a >> 8])
        elif k == 'rand':
            out += bytes([0xF7, len(d)])
            for x in d:
                a = addr_of(x); out += bytes([a & 0xFF, a >> 8])
        elif k == 'f8j':
            a = addr_of(d[1]); out += bytes([0xF8, d[0], a & 0xFF, a >> 8])
    return bytes(out)


def check_tokens(toks, where):
    """no {END}/{goto} before the last token; no raw-hex branch or terminator bytes"""
    for i, (k, d) in enumerate(toks):
        if k in ('end', 'goto') and i != len(toks) - 1:
            raise ValueError('%s: {END}/{goto} only allowed at the very end' % where)
        if k == 'ctl' and d[0] in (0xF7, 0xF8, 0xF9, 0xFF):
            if not (d[0] == 0xF8 and len(d) == 4 and d[1] not in (6, 7)):
                raise ValueError('%s: raw tag {%s} not allowed (use {END}/{if}/{goto}/{rand}/{F8:..})'
                                 % (where, ':'.join('%02X' % x for x in d)))


def merge_tiles(toks):
    out = []
    for t in toks:
        if t[0] == 'tile' and out and out[-1][0] == 'tile':
            out[-1] = ('tile', out[-1][1] + t[1])
        else:
            out.append(t)
    return out


def check_layout(s, toks, where, warnings):
    """layout: frame/controls must be identical, characters only where text mode is on"""
    def frame(ts):
        return b''.join((bytes([0xFF]) if k == 'end' else d) for k, d in ts if k != 'ch')
    if frame(toks) != frame(s['toks']):
        raise ValueError('%s: layout tags differ from JP (only characters may change)' % where)
    def runs(ts, text):
        out = []
        cur = None
        j = 0
        for k, d in ts:
            if k == 'ch':
                if not text:
                    raise ValueError('%s: characters in tile mode' % where)
                cur = (cur or 0) + (12 if len(d) == 2 else 8)
            else:
                if cur is not None:
                    out.append(cur); cur = None
                text = s['modes'][j]
                j += 1
        if cur is not None:
            out.append(cur)
        return out
    a = runs(s['toks'], s['text'])
    b = runs(toks, s['text'])
    for i, (x, y) in enumerate(zip(a, b)):
        if y > LAY_MAX_PX:
            warnings.append('%s: text run %d is %dpx > %dpx (wraps off screen)' % (where, i + 1, y, LAY_MAX_PX))
        elif y > x:
            warnings.append('%s: text run %d is %dpx > original %dpx' % (where, i + 1, y, x))
    if len(a) != len(b):
        warnings.append('%s: number of text runs changed (%d -> %d)' % (where, len(a), len(b)))


UNTRANSLATED_KANJI = []
# layout strings the mode propagation misses (called directly from code); they start in text mode
FORCE_TEXT = {0x01C4F4, 0x01C528, 0x01C55A, 0x01D38A, 0x01D3B2, 0x01DCDC,
              0x01DF80, 0x01DFAF, 0x01DFC8, 0x01DFD6, 0x01E6E2, 0x01E705}
LABEL_ADDR = {}                         # label -> (group, SNES address, length) of the last emit


def build_group_blob(info, g, tr, warnings):
    """returns (size_fn, emit_fn) using two passes over a base address"""
    ts = sorted(info['groups'][g])
    regs = sorted(info['regions'].get(g, []))
    seg_toks = {}
    maxlen = None
    for a, e, labs in regs:
        for l in sorted(set(labs)):
            s = info['segs'][l]
            if l in tr and s.get('lay'):
                text, where = tr[l]
                toks = merge_tiles(text_to_tokens(text, where))
                if any(k == 'end' for k, _ in toks[:-1]):
                    raise ValueError('%s: {END} only allowed at the very end' % where)
                check_layout(s, toks, where, warnings)
                seg_toks[l] = toks
            elif l in tr:
                text, where = tr[l]
                toks = text_to_tokens(text, where)
                check_tokens(toks, where)
                if ptr_targets_multiset(toks) != ptr_targets_multiset(s['toks']):
                    raise ValueError('%s: branch tags differ from JP' % where)
                if (s['next'] is None) != (toks and toks[-1][0] in ('end', 'goto')):
                    raise ValueError('%s: {END} must %s' % (where, 'end the line' if s['next'] is None else 'not be used (falls through)'))
                ow = tok_width(s['toks'])
                nw = tok_width(toks)
                if any(info['blocks'][T]['kind'] == 'sys' for T in ts):
                    if nw > ow:
                        warnings.append('%s: width %dpx > original %dpx' % (where, nw, ow))
                    if maxlen is None:
                        maxlen = max(len(encode_tokens(info['segs'][x]['toks'], lambda _: 0x8000))
                                     for _, _, lb in regs for x in lb)
                    nb = len(encode_tokens(toks, lambda _: 0x8000))
                    if nb > maxlen:
                        warnings.append('%s: %d bytes > longest original string in this table (%d bytes);'
                                        ' check RAM buffers' % (where, nb, maxlen))
                else:
                    if group_name(info, g) in BATTLE_GROUPS:
                        mx, cont, ml = BTL_MAX_PX, BTL_CONT_PX, BTL_MAX_LINES
                    else:
                        mx, cont, ml = DLG_MAX_PX, DLG_CONT_PX, DLG_MAX_LINES
                    for li, w in dlg_lines(toks):
                        lim = mx if li == 0 else cont
                        if w > lim:
                            warnings.append('%s: line %d is %dpx > %dpx (auto-wrap)' % (where, li + 1, w, lim))
                        if li >= ml:
                            warnings.append('%s: speech has more than %d lines (window scrolls)' % (where, ml))
                seg_toks[l] = toks
            else:
                seg_toks[l] = s['toks']
                if any(k == 'ch' and len(d) == 2 for k, d in s['toks']):
                    UNTRANSLATED_KANJI.append(l)

    def emit(base):
        """base = SNES address (bank:offset) of blob start; returns bytes, label map"""
        addr = {}
        out = bytearray()
        cur = base
        layout = []
        # dummy string for unused entries
        dummy = cur; out.append(0xFF); cur += 1
        # tables
        tab_at = {}
        for T in ts:
            tab_at[T] = cur
            cur += 2 * info['blocks'][T]['n']
            out += bytes(2 * info['blocks'][T]['n'])
        # commands
        cmd_at = {}
        for T in ts:
            for kind, v in info['blocks'][T]['ents']:
                if kind == 'cmd' and v not in cmd_at:
                    pre, ck, tg = info['cmds'][v]
                    size = 2 + (2 + 2 * len(tg) if ck == 'rand' else 3)
                    cmd_at[v] = (cur, len(out)); cur += size; out += bytes(size)
        # segments: first pass sizes with fake addresses
        for a, e, labs in regs:
            for l in sorted(set(labs)):
                addr[l] = cur
                b = encode_tokens(seg_toks[l], lambda x: 0x8000)
                layout.append((l, len(out)))
                cur += len(b); out += bytes(len(b))

        def A(x):
            if x not in addr:
                raise KeyError('label %s not in group' % lab(x))
            return addr[x] & 0xFFFF
        for l, pos in layout:
            b = encode_tokens(seg_toks[l], A)
            out[pos:pos + len(b)] = b
            LABEL_ADDR[l] = (group_name(info, g), addr[l], len(b))
        for v, (sa, pos) in cmd_at.items():
            pre, ck, tg = info['cmds'][v]
            if ck == 'rand':
                b = pre + bytes([0xF7, len(tg)]) + b''.join(bytes([A(x) & 0xFF, A(x) >> 8]) for x in tg)
            else:
                b = pre + bytes([0xF9, A(tg[0]) & 0xFF, A(tg[0]) >> 8])
            out[pos:pos + len(b)] = b
        for T in ts:
            p = tab_at[T] - base + 1 - 1
            for k, (kind, v) in enumerate(info['blocks'][T]['ents']):
                if kind == 'raw':
                    w = v
                elif kind == 'dummy':
                    w = dummy & 0xFFFF
                elif kind == 'cmd':
                    w = cmd_at[v][0] & 0xFFFF
                else:
                    w = A(v)
                out[p + 2 * k] = w & 0xFF
                out[p + 2 * k + 1] = w >> 8
        return bytes(out), tab_at
    return emit


def build(out=OUT, use_tr=True):
    import build_ko
    tmp = out + '.base'
    build_ko.build(test_text=False, out=tmp)
    rom = bytearray(open(tmp, 'rb').read())
    os.remove(tmp)
    orig = open(SRC, 'rb').read()
    info = discover(orig)
    tr = read_scripts() if use_tr else {}
    warnings = []
    # place groups (largest first) into free banks
    blobs = []
    for g in info['groups']:
        emit = build_group_blob(info, g, tr, warnings)
        size = len(emit(0xB48000)[0])
        blobs.append((size, g, emit))
    blobs.sort(key=lambda x: -x[0])
    free = {bk: 0x8000 for bk in TEXT_BANKS}
    used = {}
    for size, g, emit in blobs:
        bk = next((b for b in TEXT_BANKS if free[b] >= size), None)
        if bk is None:
            raise RuntimeError('group %s (%d bytes) does not fit any free bank' % (group_name(info, g), size))
        base = bk << 16 | (0x8000 + 0x8000 - free[bk])
        data, tab_at = emit(base)
        o = s2f(base)
        rom[o:o + len(data)] = data
        free[bk] -= size
        used.setdefault(bk, []).append((group_name(info, g), size))
        for T, na in tab_at.items():
            if T == 0x1BB0F:      # direct reference: route names printed by $81:EDEA
                o2 = s2f(EDA2)
                assert rom[o2] == 0xBF and rom[o2 + 1:o2 + 4] == bytes([0x0F, 0xBB, 0x03])
                rom[o2 + 1:o2 + 4] = bytes([na & 0xFF, (na >> 8) & 0xFF, na >> 16])
                o3 = s2f(EDA8)
                assert rom[o3:o3 + 3] == bytes([0xA9, 0x03, 0x00])
                rom[o3 + 1] = na >> 16
            b = info['blocks'][T]
            lst = D2D7 if b['list'] == 'D2D7' else D277
            for i in b['ids']:
                rom[lst + 3 * i] = na & 0xFF
                rom[lst + 3 * i + 1] = (na >> 8) & 0xFF
                rom[lst + 3 * i + 2] = na >> 16
    if use_tr:
        import titles
        tn, rn, gn = titles.apply(rom, orig)
        print('stage titles: font %d bytes at $B0:9000, records %d bytes, %d glyphs' % (tn, rn, gn))
        import logo
        print('title logo: %d bytes at $B0:B000' % logo.apply(rom, orig))
    s = build_ko.fix_checksum(rom)
    open(out, 'wb').write(rom)
    write_ips(orig, rom, os.path.splitext(out)[0] + '.ips')
    with open(os.path.splitext(out)[0] + '_labels.tsv', 'w', encoding='utf-8', newline='\n') as f:
        for l in sorted(LABEL_ADDR, key=lambda x: LABEL_ADDR[x][1]):
            g, a, n = LABEL_ADDR[l]
            f.write('%s\t%s\t%06X\t%d\n' % (lab(l), g, a, n))
    print('wrote %s  checksum %04X  translated segments: %d' % (os.path.normpath(out), s, len(tr)))
    for bk in sorted(used):
        print('  bank $%02X: %s  (free %d)' % (bk, ', '.join('%s %dB' % x for x in used[bk]), free[bk]))
    for w in warnings:
        print('  WARN', w)
    if UNTRANSLATED_KANJI:
        print('  NOTE %d untranslated segment(s) still contain kanji; they show as wrong hangul until translated'
              % len(set(UNTRANSLATED_KANJI)))


def write_ips(a, b, path):
    """IPS patch (supports growth up to 16MB); records split at 0xFFFF bytes"""
    out = bytearray(b'PATCH')
    i = 0
    n = len(b)
    while i < n:
        if i < len(a) and a[i] == b[i]:
            i += 1
            continue
        j = i
        while j < n and j - i < 0xFFFF and not (j < len(a) and a[j] == b[j] and j + 1 < n and j + 1 < len(a) and a[j + 1] == b[j + 1]):
            j += 1
        if i == 0x454F46:          # 'EOF' offset must not start a record
            i -= 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + b[i:j]
        i = j
    out += b'EOF'
    open(path, 'wb').write(out)
    print('wrote %s (%d bytes)' % (os.path.normpath(path), len(out)))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'extract':
        info = discover(open(SRC, 'rb').read())
        ws = write_scripts(info, force='--force' in sys.argv)
        print('groups: %d, segments: %d, written: %d file(s)' % (len(info['groups']), len(info['segs']), len(ws)))
        for g, ts in sorted(info['groups'].items()):
            print('  %s' % group_name(info, g))
    elif cmd == 'build':
        if '--no-tr' in sys.argv:
            build(out=os.path.join(ROOT, 'out', 'srw3_reloc_only.smc'), use_tr=False)
        else:
            build()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
