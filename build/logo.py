"""Korean title logo 「제3차 슈퍼로봇대전」 (START / CONTINUE / LOAD stay in English).

Title screen (HANDOFF.md section 13): Mode 1, the logo is BG2 = palette 1, tiles from graphics
asset 5 ($21:CA18, LZ, 16 KB, loaded to VRAM word $2000). The BG2 tilemap is a fixed rectangle:
rows 8-15, columns 3-29, one distinct tile per cell (blank = tile 0x064). We keep that map and
repaint the tiles of those cells, then recompress asset 5 to $B0:B000.

  python logo.py preview out.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'analysis'))
import lz
import lzc

FONTDIR = os.path.join(os.environ.get('SRW3_FONTDIR') or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Windows/Fonts'), '')  # SRW3_FONTDIR overrides
ASSET_TABLE = 0x108000
ASSET = 5
ORIG_SRC = 0x21CA18
NEW_SRC = 0xB0B000
W, H = 216, 64                      # BG2 columns 3-29, rows 8-15
# palette 1 (title screen CGRAM 16-31)
PAL = [(0, 0, 0), (248, 248, 248), (248, 248, 168), (248, 248, 0), (248, 216, 0), (248, 184, 0),
       (248, 152, 0), (248, 120, 0), (248, 88, 0), (216, 56, 0), (184, 0, 0), (120, 0, 0),
       (0, 0, 152), (0, 0, 120), (0, 0, 88), (0, 0, 40)]
BLANK = 0x064
# original BG2 tilemap, rows 8-15 x columns 3-29 (VRAM dump of the title screen); one tile per cell
MAP = [
    [0x064, 0x000, 0x001, 0x002, 0x003, 0x004, 0x005, 0x006, 0x007, 0x008, 0x009, 0x00A, 0x00B, 0x00C, 0x00D, 0x00E, 0x00F, 0x020, 0x021, 0x022, 0x023, 0x024, 0x025, 0x026, 0x027, 0x028, 0x029],
    [0x064, 0x010, 0x011, 0x012, 0x013, 0x014, 0x015, 0x016, 0x017, 0x018, 0x019, 0x01A, 0x01B, 0x01C, 0x01D, 0x01E, 0x01F, 0x030, 0x031, 0x032, 0x033, 0x034, 0x035, 0x036, 0x037, 0x038, 0x039],
    [0x064, 0x02A, 0x02B, 0x02C, 0x02D, 0x02E, 0x02F, 0x040, 0x041, 0x042, 0x043, 0x044, 0x045, 0x046, 0x047, 0x048, 0x049, 0x04A, 0x04B, 0x04C, 0x04D, 0x04E, 0x04F, 0x060, 0x061, 0x062, 0x063],
    [0x064, 0x03A, 0x03B, 0x03C, 0x03D, 0x03E, 0x03F, 0x050, 0x051, 0x052, 0x053, 0x054, 0x055, 0x056, 0x057, 0x058, 0x059, 0x05A, 0x05B, 0x05C, 0x05D, 0x05E, 0x05F, 0x070, 0x071, 0x072, 0x073],
    [0x064, 0x065, 0x066, 0x067, 0x068, 0x069, 0x06A, 0x06B, 0x06C, 0x06D, 0x06E, 0x06F, 0x080, 0x081, 0x082, 0x083, 0x084, 0x085, 0x086, 0x087, 0x088, 0x089, 0x08A, 0x08B, 0x08C, 0x08D, 0x064],
    [0x074, 0x075, 0x076, 0x077, 0x078, 0x079, 0x07A, 0x07B, 0x07C, 0x07D, 0x07E, 0x07F, 0x090, 0x091, 0x092, 0x093, 0x094, 0x095, 0x096, 0x097, 0x098, 0x099, 0x09A, 0x09B, 0x09C, 0x09D, 0x064],
    [0x08E, 0x08F, 0x0A0, 0x0A1, 0x0A2, 0x0A3, 0x0A4, 0x0A5, 0x0A6, 0x0A7, 0x0A8, 0x0A9, 0x0AA, 0x0AB, 0x0AC, 0x0AD, 0x0AE, 0x0AF, 0x0C0, 0x0C1, 0x0C2, 0x0C3, 0x0C4, 0x0C5, 0x0C6, 0x0C7, 0x064],
    [0x09E, 0x09F, 0x0B0, 0x0B1, 0x0B2, 0x0B3, 0x0B4, 0x0B5, 0x0B6, 0x0B7, 0x0B8, 0x0B9, 0x0BA, 0x0BB, 0x0BC, 0x0BD, 0x0BE, 0x0BF, 0x0D0, 0x0D1, 0x0D2, 0x0D3, 0x0D4, 0x0D5, 0x0D6, 0x0D7, 0x064],
]


def tile_map():
    return {(r, c): t for r, row in enumerate(MAP) for c, t in enumerate(row) if t != BLANK}


def mask_text(text, font, w, h, skew=0.0, thresh=80):
    """text rendered 4x, sheared, scaled to w x h with box filtering, then thresholded
    (a low threshold thickens strokes without filling the counters)"""
    f = ImageFont.truetype(font, h * 4)
    l, t, r, b = f.getbbox(text)
    im = Image.new('L', (r - l + 16, b - t + 16), 0)
    ImageDraw.Draw(im).text((8 - l, 8 - t), text, font=f, fill=255)
    if skew:
        im = im.transform((im.width + int(im.height * skew) + 2, im.height), Image.AFFINE,
                          (1, skew, -im.height * skew, 0, 1, 0), Image.BILINEAR)
    im = im.crop(im.getbbox())
    im = im.resize((w, h), Image.BOX)
    return im.point(lambda v: 255 if v >= thresh else 0)


def draw():
    canvas = [[0] * W for _ in range(H)]
    # big line, slanted
    big = mask_text('슈퍼로봇대전', FONTDIR + 'NanumSquareEB.ttf', 172, 48, skew=0.18, thresh=70)
    small = [mask_text(c, FONTDIR + 'NanumSquareEB.ttf', 17 if c != '3' else 12, 17, thresh=45) for c in ('제', '3', '차')]
    layers = []                       # (mask, x, y)
    bx, by = 36, 5
    layers.append((big, bx, by))
    sy = 1
    for m in small:
        layers.append((m, 10 + (20 - m.width) // 2, sy))
        sy += 21

    def on(m, x, y, px, py):
        u, v = px - x, py - y
        return 0 <= u < m.width and 0 <= v < m.height and m.getpixel((u, v))
    # extrusion: blue, 4 px down-right, darker further back
    for d, colr in ((3, 15), (2, 13), (1, 12)):
        for m, x, y in layers:
            for py in range(H):
                for px in range(W):
                    if on(m, x + d, y + d, px, py):
                        canvas[py][px] = colr
    # face: vertical gradient yellow -> orange, white rim on top-left
    for m, x, y in layers:
        hgt = m.height
        for py in range(H):
            for px in range(W):
                if on(m, x, y, px, py):
                    v = (py - y) / max(1, hgt - 1)
                    idx = [2, 3, 3, 4, 5, 6, 7, 8, 9][min(8, int(v * 9))]
                    if not on(m, x, y, px - 1, py) or not on(m, x, y, px, py - 1):
                        idx = 1 if v < 0.5 else 3
                    canvas[py][px] = idx
    # dark outline around everything for contrast on the dark background
    out = [row[:] for row in canvas]
    for py in range(H):
        for px in range(W):
            if canvas[py][px] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    qx, qy = px + dx, py + dy
                    if 0 <= qx < W and 0 <= qy < H and canvas[qy][qx] in range(1, 12):
                        out[py][px] = 11
                        break
    for r, row in enumerate(MAP):
        for c, t in enumerate(row):
            if t == BLANK:
                for py in range(r * 8, r * 8 + 8):
                    for px in range(c * 8, c * 8 + 8):
                        if out[py][px]:
                            raise SystemExit('logo: pixel in blank cell row %d col %d' % (r, c))
    return out


def encode_into(asset, canvas):
    data = bytearray(asset)
    for (r, c), t in tile_map().items():
        o = t * 32
        for y in range(8):
            row = canvas[r * 8 + y][c * 8:c * 8 + 8]
            for plane in range(4):
                b = 0
                for x in range(8):
                    if row[x] & (1 << plane):
                        b |= 0x80 >> x
                data[o + 16 * (plane // 2) + 2 * y + (plane & 1)] = b
    return bytes(data)


def f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def apply(rom, rom_orig):
    asset, _ = lz.decompress(rom_orig, ORIG_SRC)
    new = encode_into(asset, draw())
    comp = lzc.compress(new)
    o = f(NEW_SRC)
    assert len(comp) <= 0x8000 - (NEW_SRC & 0x7FFF), 'logo does not fit in bank $B0'
    rom[o:o + len(comp)] = comp
    a = f(ASSET_TABLE) + 3 * ASSET
    assert rom_orig[a:a + 3] == bytes([ORIG_SRC & 0xFF, (ORIG_SRC >> 8) & 0xFF, ORIG_SRC >> 16])
    rom[a:a + 3] = bytes([NEW_SRC & 0xFF, (NEW_SRC >> 8) & 0xFF, NEW_SRC >> 16])
    return len(comp)


def preview(path):
    cv = draw()
    im = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W):
            im.putpixel((x, y), PAL[cv[y][x]] if cv[y][x] else (40, 20, 30))
    im.resize((W * 4, H * 4), Image.NEAREST).save(path)


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        preview(sys.argv[2])
