"""Korean stage titles (the 『...』 sprite text shown when a stage starts).

Called from srwtext.build() on the ROM bytearray before the checksum, and standalone:
  python titles.py preview out.png     draw all Korean titles as they will appear

Facts (HANDOFF.md section 12):
- Title font = graphics asset 3 (table $10:8000, 3 bytes per entry), LZ (analysis/lz.py), 32 KB =
  8 blocks of 4 KB, each 32 glyphs of 16x16 (4bpp sprite tiles; glyph g = tiles
  (g%8)*2 + (g//8)*32, +1, +16, +17). Colours: 11 body, 14 shadow.
- At title time sprite tiles 0x180 <- block 0 (digits, 第 話 『 』), 0x000 <- block 1,
  0x080 <- the stage's block (2..6, listed in tr/titles.tsv).
- Line 2 metasprites 0xC0-0xF2 in set 0 (pointer table $83:8D8A, 2-byte pointers into bank $03);
  record = count, then per sprite: tile, attr (bit0 = tile bit 8, 0x10 base), dy, dx.
New layout: glyphs used by more than one block group go to block 1 and to the free slots of block 0
(slots 14-31); the rest to the stage's own block. 第/話 become 제/화. The font is recompressed
(analysis/lzc.py) to $B0:9000 and asset 3 points there; records are rewritten in place.
"""
import collections
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'analysis'))
import lz
import lzc

TSV = os.path.join(HERE, '..', 'tr', 'titles.tsv')
FONT_TTF = os.path.join(os.environ.get('SRW3_FONTDIR') or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Windows/Fonts'), 'NanumGothic.ttf')  # SRW3_FONTDIR overrides
FONT_SIZE = 15
ASSET_TABLE = 0x108000
ASSET = 3
ORIG_SRC = 0x20C182
NEW_SRC = 0xB09000
SET0 = 0x038D8A
REC_AREA = (0x039DA1, 0x03A4AC)      # original records 0xC0..0xF2, rewritten in place
FIRST_ID = 0xC0
BODY, SHADOW = 11, 14
BLOCK0_FREE = list(range(14, 32))
DIGIT_GLYPH = {str(d): d for d in range(10)}   # block 0 glyphs 0..9


def f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def load_titles():
    rows = []
    for ln in open(TSV, encoding='utf-8'):
        if ln.strip() and not ln.startswith('#'):
            i, b, jp, ko = ln.rstrip('\n').split('\t')
            rows.append((int(i, 16), int(b), jp, ko))
    return rows


def glyph_pixels(ch, font):
    """16x16 list of colour indices: 1-bit NanumGothic body + shadow on the left"""
    im = Image.new('1', (16, 16), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    l, t, r, b = font.getbbox(ch)
    w, h = r - l, b - t
    x = 1 + (15 - w) // 2 - l
    y = (16 - 15) // 2 + (15 - 14) // 2 - font.getbbox('가')[1]
    d.text((x, y), ch, font=font, fill=1)
    p = im.load()
    out = [[0] * 16 for _ in range(16)]
    for yy in range(16):
        for xx in range(16):
            if p[xx, yy]:
                out[yy][xx] = BODY
    for yy in range(16):
        for xx in range(1, 16):
            if out[yy][xx] == BODY and out[yy][xx - 1] == 0:
                out[yy][xx - 1] = SHADOW
    return out


def put_glyph(font_data, block, slot, px):
    base = block * 0x1000
    t0 = (slot % 8) * 2 + (slot // 8) * 32
    for yy in range(16):
        for xx in range(16):
            t = t0 + (xx // 8) + (yy // 8) * 16
            o = base + t * 32
            v = px[yy][xx]
            bit = 0x80 >> (xx % 8)
            r = yy % 8
            for plane in range(4):
                a = o + 16 * (plane // 2) + 2 * r + (plane & 1)
                if v & (1 << plane):
                    font_data[a] |= bit
                else:
                    font_data[a] &= ~bit & 0xFF


def clear_glyph(font_data, block, slot):
    put_glyph(font_data, block, slot, [[0] * 16 for _ in range(16)])


def plan(rows):
    """returns {char: (block, slot)} and the per-title text"""
    groups = collections.defaultdict(set)
    for i, b, jp, ko in rows:
        for c in ko:
            if c not in ' /' and c not in DIGIT_GLYPH:
                groups[b].add(c)
    share = collections.Counter()
    for g in groups.values():
        for c in g:
            share[c] += 1
    shared = sorted([c for c, k in share.items() if k > 1], key=lambda c: (-share[c], c))
    slots = [(1, s) for s in range(32)] + [(0, s) for s in BLOCK0_FREE]
    if len(shared) > len(slots):
        raise SystemExit('titles: %d shared glyphs > %d common slots' % (len(shared), len(slots)))
    where = {}
    for c, sl in zip(shared, slots):
        where[c] = sl
    for b, g in sorted(groups.items()):
        own = sorted(c for c in g if c not in where)
        if len(own) > 32:
            raise SystemExit('titles: block %d needs %d glyphs > 32' % (b, len(own)))
        for s, c in enumerate(own):
            where[(b, c)] = (b, s)
    return where


def tile_of(where, b, c):
    if c in DIGIT_GLYPH:
        blk, s = 0, DIGIT_GLYPH[c]
    elif c in where:
        blk, s = where[c]
    else:
        blk, s = where[(b, c)]
    t = (s % 8) * 2 + (s // 8) * 32
    return t + {0: 0x180, 1: 0x000}.get(blk, 0x080)


def record(where, b, ko):
    """sprite list: 』 first, glyphs right to left, 『 last (like the original)"""
    lines = ko.split('/')
    adv = lambda c: 8 if c == ' ' else 16
    widths = [sum(adv(c) for c in ln) for ln in lines]
    total = 16 + max(widths) + 16
    start = -(total // 2)
    start -= start % 2
    spr = []
    for li, ln in enumerate(lines):
        x = start + 16
        for c in ln:
            if c != ' ':
                spr.append((tile_of(where, b, c), 16 * li, x))
            x += adv(c)
    last_end = start + 16 + widths[-1]
    out = [(0x1AA, 16 * (len(lines) - 1) + 4, last_end)]
    out += list(reversed(spr))
    out.append((0x1A8, -4, start))
    data = bytearray([len(out)])
    for t, dy, dx in out:
        data += bytes([t & 0xFF, 0x10 | (t >> 8), dy & 0xFF, dx & 0xFF])
    return bytes(data)


def build_font(rom_orig, rows, where):
    font, _ = lz.decompress(rom_orig, ORIG_SRC)
    font = bytearray(font)
    ttf = ImageFont.truetype(FONT_TTF, FONT_SIZE)
    # blocks 1..7 are rebuilt; block 0 keeps digits and brackets
    for blk in range(1, 8):
        for s in range(32):
            clear_glyph(font, blk, s)
    for s in BLOCK0_FREE:
        clear_glyph(font, 0, s)
    put_glyph(font, 0, 10, glyph_pixels('제', ttf))
    put_glyph(font, 0, 11, glyph_pixels('화', ttf))
    for key, (blk, s) in where.items():
        c = key if isinstance(key, str) else key[1]
        put_glyph(font, blk, s, glyph_pixels(c, ttf))
    return bytes(font)


def apply(rom, rom_orig):
    rows = load_titles()
    where = plan(rows)
    font = build_font(rom_orig, rows, where)
    comp = lzc.compress(font)
    o = f(NEW_SRC)
    assert len(comp) <= 0x8000 - (NEW_SRC & 0x7FFF), 'title font does not fit in bank $B0'
    assert all(b == 0xFF for b in rom[o:o + len(comp)]) or all(b == 0 for b in rom[o:o + len(comp)]) \
        or rom[o:o + len(comp)] == comp, 'bank $B0 area for the title font is not free'
    rom[o:o + len(comp)] = comp
    a = f(ASSET_TABLE) + 3 * ASSET
    assert rom_orig[a:a + 3] == bytes([ORIG_SRC & 0xFF, (ORIG_SRC >> 8) & 0xFF, ORIG_SRC >> 16])
    rom[a:a + 3] = bytes([NEW_SRC & 0xFF, (NEW_SRC >> 8) & 0xFF, NEW_SRC >> 16])
    # metasprite records
    pos = REC_AREA[0]
    for i, b, jp, ko in rows:
        rec = record(where, b, ko)
        if pos + len(rec) > REC_AREA[1]:
            raise SystemExit('titles: records exceed the original area')
        rom[f(pos):f(pos) + len(rec)] = rec
        pt = f(SET0) + 2 * i
        rom[pt] = pos & 0xFF
        rom[pt + 1] = (pos >> 8) & 0xFF
        pos += len(rec)
    return len(comp), pos - REC_AREA[0], len(where)


def preview(path):
    rows = load_titles()
    where = plan(rows)
    rom = open(lz.ROM, 'rb').read()
    font = build_font(rom, rows, where)
    from tiles import decode_tile
    pal = {0: (0, 0, 0), BODY: (255, 255, 255), SHADOW: (90, 90, 140)}

    def g16(t):
        im = Image.new('RGB', (16, 16))
        blk = 0 if t >= 0x180 else (1 if t < 0x080 else None)
        for sub, (ox, oy) in zip((0, 1, 16, 17), ((0, 0), (8, 0), (0, 8), (8, 8))):
            tt = t + sub
            if tt >= 0x180:
                o = (tt - 0x180) * 32
            elif tt < 0x080:
                o = 0x1000 + tt * 32
            else:
                o = cur_block * 0x1000 + (tt - 0x080) * 32
            px = decode_tile(font, o, 4)
            for y in range(8):
                for x in range(8):
                    im.putpixel((ox + x, oy + y), pal.get(px[y][x], (255, 0, 0)))
        return im
    sheet = Image.new('RGB', (256 * 2, 48 * ((len(rows) + 1) // 2)))
    for k, (i, b, jp, ko) in enumerate(rows):
        cur_block = b
        rec = record(where, b, ko)
        im = Image.new('RGB', (256, 48))
        n = rec[0]
        for j in range(n):
            t, a, dy, dx = rec[1 + 4 * j:5 + 4 * j]
            t |= (a & 1) << 8
            dy = dy - 256 if dy > 127 else dy
            dx = dx - 256 if dx > 127 else dx
            im.paste(g16(t), (128 + dx, 12 + dy))
        sheet.paste(im, ((k % 2) * 256, (k // 2) * 48))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(path)
    print(len(rows), 'titles,', len(where), 'glyph placements')


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        preview(sys.argv[2])
