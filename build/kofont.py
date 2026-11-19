"""Korean font + encoding for the SRW3 Korean patch.

Glyph index i (0..2815) <-> 2-byte code: PREFIX[i >> 8], i & 0xFF
  PREFIX = F0 F1 F2 E8 E9 EA EB EC ED EE EF   (internal code = 0x100 + i)
Index 0..2349 = KS X 1001 hangul in KS order.
Glyph format = original kanji format: 32 bytes, left 8x16 column then right 8x16 column,
1bpp, drawn area rows 2..13, columns 0..11.

Default font: NanumGothic 12px (SIL Open Font License 1.1), rendered 1-bit with FreeType
hinting. Ink is kept in rows 1..14 (most glyphs sit in rows 2..13 like the original kanji).
"""
import os
from PIL import Image, ImageDraw, ImageFont

PREFIX = [0xF0, 0xF1, 0xF2, 0xE8, 0xE9, 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF]
MAX_GLYPHS = len(PREFIX) * 256  # 2816


def ksx1001_hangul():
    out = []
    for hi in range(0xB0, 0xC9):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode('euc-kr'))
            except UnicodeDecodeError:
                pass
    assert len(out) == 2350, len(out)
    return out


HANGUL = ksx1001_hangul()
HANGUL_INDEX = {c: i for i, c in enumerate(HANGUL)}


def code_bytes(i):
    return bytes([PREFIX[i >> 8], i & 0xFF])


DEFAULT_FONT = os.path.join(os.environ.get('SRW3_FONTDIR') or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Windows/Fonts'), 'NanumGothic.ttf')  # SRW3_FONTDIR overrides


def render_glyph(ch, font, yoff):
    im = Image.new('1', (16, 16), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'          # no anti-aliasing: hinted 1-bit outline
    d.text((0, yoff), ch, font=font, fill=1)
    px = im.load()
    out = bytearray(32)
    for y in range(16):
        for x in range(16):
            if px[x, y] and x < 12 and 1 <= y <= 14:
                out[(x // 8) * 16 + y] |= 0x80 >> (x % 8)
    return bytes(out)


def _ss_image(ch, font_big, k, yoff, dx=0, dy=0):
    im = Image.new('L', (16 * k, 16 * k), 0)
    d = ImageDraw.Draw(im)
    d.text((dx, yoff * k + dy), ch, font=font_big, fill=255)
    return im.resize((16, 16), Image.BOX)


def ss_align(font_big, k, yoff, sample):
    """sub-pixel shift (dx, dy) that puts the font's pixel grid on ours: values closest to 0/255"""
    best = None
    for dy in range(-k // 2, k // 2 + 1):
        for dx in range(-k // 2, k // 2 + 1):
            score = 0
            for c in sample:
                score += sum(min(v, 255 - v) for v in _ss_image(c, font_big, k, yoff, dx, dy).getdata())
            if best is None or score < best[0]:
                best = (score, dx, dy)
    return best[1], best[2]


def render_glyph_ss(ch, font_big, k, yoff, dx=0, dy=0):
    """pixel fonts: draw k times larger and box-downsample (FreeType hinting at 12px drops 1px strokes)"""
    px = _ss_image(ch, font_big, k, yoff, dx, dy).load()
    out = bytearray(32)
    for y in range(16):
        for x in range(16):
            if px[x, y] >= 128 and x < 12 and 1 <= y <= 14:
                out[(x // 8) * 16 + y] |= 0x80 >> (x % 8)
    return bytes(out)


def build_font(path=None, index=0, size=None):
    # SRW3_KOFONT / SRW3_KOFONT_SIZE: try another font without editing this file (font comparison)
    path = path or os.environ.get('SRW3_KOFONT') or DEFAULT_FONT
    size = size or int(os.environ.get('SRW3_KOFONT_SIZE', '12'))
    index = index or int(os.environ.get('SRW3_KOFONT_INDEX', '0'))   # face in a .ttc (gulim.ttc: 1 = GulimChe)
    font = ImageFont.truetype(path, size, index=index)
    # place glyph so that its ink box sits inside rows 2..13
    top = min(font.getbbox(c)[1] for c in HANGUL[:200])
    yoff = 2 - top
    k = int(os.environ.get('SRW3_KOFONT_SS', '0'))   # SRW3_KOFONT_SS=10: supersampled rendering for pixel fonts
    if k:
        big = ImageFont.truetype(path, size * k, index=index)
        top = min(big.getbbox(c)[1] for c in HANGUL[:200]) / k
        yoff = round(2 - top)
        dx, dy = ss_align(big, k, yoff, '하를대화확실한')
    data = bytearray()
    for c in HANGUL:
        data += render_glyph_ss(c, big, k, yoff, dx, dy) if k else render_glyph(c, font, yoff)
    data += bytes(32 * (MAX_GLYPHS - len(HANGUL)))
    return bytes(data)
