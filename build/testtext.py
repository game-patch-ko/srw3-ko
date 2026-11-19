"""Test text for the Korean hook: overwrite battle quotes in place (same length or shorter).

Covers what the attract-mode demo battle shows:
  block $0D (table $8B:F3AF, 144 entries) and the quote commands of block $01 ($88:831E).
"""
import kofont

SINGLE = {' ': 0x00, '!': 0x15, '?': 0x14, '「': 0x3E, '」': 0x3F, '・': 0x3B, '、': 0x3A,
          '。': 0xE4, ',': 0x3A, '.': 0xE4, '～': 0x13, 'ー': 0x11, '(': 0x3C, ')': 0x3D, '/': 0x0F, '+': 0x10, '%': 0x0E}
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    SINGLE[c] = 0x16 + i
for i in range(10):
    SINGLE[str(i)] = 0x30 + i


def encode(text):
    out = bytearray()
    for ch in text:
        if ch in kofont.HANGUL_INDEX:
            out += kofont.code_bytes(kofont.HANGUL_INDEX[ch])
        elif ch == '\n':
            out.append(0xF3)
        else:
            out.append(SINGLE[ch])
    return bytes(out)


H = kofont.HANGUL
EDGE = ''.join(H[i] for i in (0, 255, 256, 767, 768, 1023, 1024, 2047, 2048, 2349))
LINES = ['한글 출력 시험! 가나다라', EDGE, '좋아, 간다!!', '이 정도 공격으로는!',
         '아직 끝나지 않았어!', '피할 수 있을까?']


def fit(line, room):
    """longest prefix of line whose encoding fits in room bytes"""
    best = b''
    for k in range(1, len(line) + 1):
        e = encode(line[:k])
        if len(e) > room:
            break
        best = e
    return best


def rewrite(rom, o, n):
    """rewrite FF-terminated string at file offset o in place"""
    end = rom.index(0xFF, o)
    length = end - o
    i = o
    head = bytearray()
    # keep leading control codes (FA xx / FD xx / F4) and the opening quote
    while i < end and rom[i] in (0xFA, 0xFD, 0xF4):
        k = 1 if rom[i] == 0xF4 else 2
        head += rom[i:i + k]; i += k
    quoted = i < end and rom[i] == 0x3E
    if quoted:
        head.append(0x3E)
    room = length - len(head) - (1 if quoted else 0)
    body = fit(LINES[n % len(LINES)], room)
    if not body:
        return False
    new = bytes(head) + body + (b'\x3F' if quoted else b'') + b'\xFF'
    rom[o:o + len(new)] = new
    return True


def apply(rom):
    done = set()
    targets = []
    T = 0x5F3AF
    for i in range(144):
        w = rom[T + 2 * i] | rom[T + 2 * i + 1] << 8
        targets.append(0x58000 + w - 0x8000)
    T = 0x4031E
    for i in range(177):
        w = rom[T + 2 * i] | rom[T + 2 * i + 1] << 8
        c = 0x40000 + w - 0x8000
        if rom[c] != 0xFA:
            continue
        if rom[c + 2] == 0xF7:
            for k in range(rom[c + 3]):
                p = rom[c + 4 + 2 * k] | rom[c + 5 + 2 * k] << 8
                targets.append(0x40000 + p - 0x8000)
        elif rom[c + 2] == 0xF9:
            p = rom[c + 3] | rom[c + 4] << 8
            targets.append(0x40000 + p - 0x8000)
    n = 0
    for t in targets:
        if t in done:
            continue
        done.add(t)
        if rewrite(rom, t, n):
            n += 1
    print('test text: rewrote %d strings' % n)


DIALOGUE = ('여기 피프스 루나에서 몇 달 전부터 연달아 일어나고 있는 '
            '의문의 실종 사건을 조사하는 것이 이번 임무다. '
            '연방군 전투 부대가 통째로 사라지고 있다는 그 사건 말이지? '
            '가나다라마바사아자차카타파하 한글 줄바꿈과 폭을 시험합니다.')


def rewrite_spans(rom, o):
    """replace the inside of every 「...」 in the FF-terminated string at o, same byte length"""
    end = rom.index(0xFF, o)
    i = o
    pos = 0
    while i < end:
        b = rom[i]
        if b in (0xF0, 0xF1, 0xF2, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF):
            i += 2; continue
        if b in (0xFA, 0xFD):
            i += 2; continue
        if b == 0x3E:
            j = rom.index(0x3F, i + 1)
            room = j - i - 1
            text = DIALOGUE[pos:] + DIALOGUE
            body = fit(text, room)
            pos = (pos + len(body) // 2) % len(DIALOGUE)
            body = body + b'\x00' * (room - len(body))
            rom[i + 1:j] = body
            i = j + 1; continue
        i += 1


def apply_dialogue(rom):
    T = 0x48000   # block $02 ($89:8000), first stage intermission
    for k in range(4):
        w = rom[T + 2 * k] | rom[T + 2 * k + 1] << 8
        rewrite_spans(rom, 0x48000 + w - 0x8000)
    print('test text: dialogue block $02 msgs 0-3')
