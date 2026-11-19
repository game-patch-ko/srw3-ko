"""Build the SRW3 Korean test ROM.

  python build_ko.py            -> ../out/srw3_ko_test.smc

Steps
  1. expand 1.5MB -> 2MB (banks $B0-$BF)
  2. hook code at $B0:8000
     - prefix decode (E8-EF + F0-F2) for dialogue $81:85AF, window text $80:C82D,
       string printer $81:EDF6
     - glyph wrapper at $80:C90E: codes >= $100 read the hangul font in banks $B1-$B3
  3. hangul font (2816 slots) at $B1:8000
  4. optional test text (see testtext.py)
  5. fix header checksum
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'Dai-3-Ji Super Robot Taisen (J).smc')
OUT = os.path.join(HERE, '..', 'out', 'srw3_ko_test.smc')

CODE_BANK = 0xB0
FONT_BANK = 0xB1


def s2f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + ((a & 0xFFFF) - 0x8000)


class Asm:
    """Tiny assembler: emit raw bytes, labels and 8-bit relative branches."""
    def __init__(self, org):
        self.org = org
        self.buf = bytearray()
        self.labels = {}
        self.fix = []

    def pc(self):
        return self.org + len(self.buf)

    def label(self, name):
        self.labels[name] = self.pc()

    def b(self, *bs):
        for x in bs:
            if isinstance(x, (bytes, bytearray)):
                self.buf += x
            else:
                self.buf.append(x)

    def br(self, op, name):
        self.buf += bytes([op, 0])
        self.fix.append((len(self.buf) - 1, name))

    def long(self, op, addr):
        self.buf += bytes([op, addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16])

    def done(self):
        for pos, name in self.fix:
            d = self.labels[name] - (self.org + pos + 1)
            assert -128 <= d <= 127, name
            self.buf[pos] = d & 0xFF
        return bytes(self.buf)


def build_hooks():
    a = Asm(CODE_BANK << 16 | 0x8000)

    # --- hook_pref: A = prefix byte (16-bit, m16). out: $00 = internal hi byte (1..0B)
    a.label('hook_pref')
    a.b(0xC9, 0xF0, 0x00)          # CMP #$00F0
    a.br(0x90, 'pref_lo')          # BCC
    a.b(0x38, 0xE9, 0xEF, 0x00)    # SEC / SBC #$00EF   F0->1 F1->2 F2->3
    a.b(0x85, 0x00, 0x6B)          # STA $00 / RTL
    a.label('pref_lo')
    a.b(0x38, 0xE9, 0xE4, 0x00)    # SEC / SBC #$00E4   E8->4 .. EF->B
    a.b(0x85, 0x00, 0x6B)          # STA $00 / RTL

    # --- hook_word: for $81:EDFB. A = [$20],y word (lo=prefix, hi=xx) -> internal code
    a.label('hook_word')
    a.b(0xB7, 0x20, 0xEB)          # LDA [$20],y / XBA
    a.b(0xC9, 0x00, 0xF0)          # CMP #$F000
    a.br(0x90, 'word_lo')
    a.b(0x38, 0xE9, 0x00, 0xEF, 0x6B)   # SEC / SBC #$EF00 / RTL
    a.label('word_lo')
    a.b(0x38, 0xE9, 0x00, 0xE4, 0x6B)   # SEC / SBC #$E400 / RTL

    # --- glyph wrapper, entered by JML from $80:C90E (caller did JSL $00C90E)
    a.label('glyph')
    a.b(0x08, 0xC2, 0x30)          # PHP / REP #$30
    a.b(0x85, 0x00)                # STA $00
    a.b(0xC9, 0x00, 0x01)          # CMP #$0100
    a.br(0xB0, 'g_hangul')         # BCS
    a.b(0x28)                      # PLP
    a.b(0xAE, 0x20, 0x0E)          # LDX $0E20
    a.long(0x5C, 0x80C913)         # JML $80C913 (original continues, RTL to caller)
    a.label('g_hangul')
    a.b(0x38, 0xE9, 0x00, 0x01)    # SEC / SBC #$0100     -> glyph index
    a.b(0x48)                      # PHA
    a.b(0x29, 0xFF, 0x03)          # AND #$03FF
    a.b(0x0A, 0x0A, 0x0A, 0x0A, 0x0A)  # ASL x5
    a.b(0x09, 0x00, 0x80)          # ORA #$8000            -> address in font bank
    a.b(0x2C, 0x1A, 0x0E)          # BIT $0E1A  (bit15: original uses Y=code*32-$1000)
    a.br(0x10, 'g_noadj')          # BPL
    a.b(0x38, 0xE9, 0x00, 0x10)    # SEC / SBC #$1000
    a.label('g_noadj')
    a.b(0x85, 0xF4, 0x18)          # STA $F4 / CLC
    a.b(0x69, 0x08, 0x00, 0x85, 0xF7)  # ADC #8 / STA $F7
    a.b(0x69, 0x08, 0x00, 0x85, 0xFA)  # ADC #8 / STA $FA
    a.b(0x69, 0x08, 0x00, 0x85, 0xFD)  # ADC #8 / STA $FD
    a.b(0x68, 0xEB)                # PLA / XBA
    a.b(0x29, 0xFF, 0x00, 0x4A, 0x4A)  # AND #$00FF / LSR / LSR  -> idx >> 10
    a.b(0x18, 0x69, FONT_BANK, 0x00)   # CLC / ADC #FONT_BANK
    a.b(0xE2, 0x20)                # SEP #$20
    a.b(0x85, 0xF6, 0x85, 0xF9, 0x85, 0xFC, 0x85, 0xFF)
    a.b(0xC2, 0x20)                # REP #$20
    a.b(0xA9, 0x00, 0x01, 0x85, 0x00)  # LDA #$0100 / STA $00  (fake code: first kanji)
    a.b(0x28, 0x08)                # PLP / PHP  (caller's flags for original routine)
    a.b(0xAE, 0x20, 0x0E)          # LDX $0E20
    a.long(0x22, 0x80C913)         # JSL $80C913
    a.b(0xC2, 0x30)                # REP #$30
    a.long(0xAF, 0x908003)         # LDA $908003  (original font pointer)
    a.b(0x85, 0xF4, 0x18)
    a.b(0x69, 0x08, 0x00, 0x85, 0xF7)
    a.b(0x69, 0x08, 0x00, 0x85, 0xFA)
    a.b(0x69, 0x08, 0x00, 0x85, 0xFD)
    a.b(0xE2, 0x20)
    a.long(0xAF, 0x908005)         # LDA $908005  (bank byte)
    a.b(0x85, 0xF6, 0x85, 0xF9, 0x85, 0xFC, 0x85, 0xFF)
    a.b(0x28, 0x6B)                # PLP / RTL
    code = a.done()
    return code, a.labels


def patch(rom, snes, old, new):
    o = s2f(snes)
    assert rom[o:o + len(old)] == bytes(old), ('%06X' % snes, rom[o:o + len(old)].hex(), bytes(old).hex())
    assert len(new) == len(old)
    rom[o:o + len(new)] = bytes(new)


def jsl(addr):
    return [0x22, addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16]


def fix_checksum(rom):
    hdr = 0x7FC0
    rom[hdr + 0x1C:hdr + 0x20] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[hdr + 0x1E] = s & 0xFF
    rom[hdr + 0x1F] = s >> 8
    c = s ^ 0xFFFF
    rom[hdr + 0x1C] = c & 0xFF
    rom[hdr + 0x1D] = c >> 8
    return s


def build(test_text=True, out=OUT):
    sys.path.insert(0, HERE)
    import kofont
    rom = bytearray(open(SRC, 'rb').read())
    assert len(rom) == 0x180000
    rom += b'\xFF' * (0x200000 - len(rom))

    code, L = build_hooks()
    co = s2f(CODE_BANK << 16 | 0x8000)
    rom[co:co + len(code)] = code

    # dialogue decode $81:85AF
    patch(rom, 0x8185AF,
          [0xC9, 0xF0, 0x00, 0x90, 0x0E, 0x1A, 0x29, 0x03, 0x00, 0x85, 0x00],
          [0xC9, 0xE8, 0x00, 0x90, 0x0E] + jsl(L['hook_pref']) + [0xEA, 0xEA])
    # window text-mode decode $80:C82D
    patch(rom, 0x80C82D,
          [0xC9, 0xF0, 0x00, 0x90, 0x45, 0x1A, 0x29, 0x03, 0x00, 0x85, 0x00],
          [0xC9, 0xE8, 0x00, 0x90, 0x45] + jsl(L['hook_pref']) + [0xEA, 0xEA])
    # string printer $81:EDF6 / EDFB
    patch(rom, 0x81EDF6, [0xC9, 0xF0, 0x00], [0xC9, 0xE8, 0x00])
    patch(rom, 0x81EDFB, [0xB7, 0x20, 0x1A, 0xEB, 0x29, 0xFF, 0x03],
          jsl(L['hook_word']) + [0xEA, 0xEA, 0xEA])
    # glyph routine entry $80:C90E  (STA $00 / LDX $0E20 ...)
    patch(rom, 0x80C90E, [0x85, 0x00, 0xAE, 0x20],
          [0x5C, L['glyph'] & 0xFF, (L['glyph'] >> 8) & 0xFF, L['glyph'] >> 16])

    # Korean punctuation: redraw the Japanese 。(E4) and 、(3A) as . and ,
    # (1-byte glyphs: 8x16 1bpp at $90:8856 + code*16)
    PUNCT = {0xE4: {12: 0x60, 13: 0x60},
             0x3A: {11: 0x60, 12: 0x60, 13: 0x20, 14: 0x40}}
    for c, rows in PUNCT.items():
        o = 0x80856 + c * 16
        rom[o:o + 16] = bytes(rows.get(y, 0) for y in range(16))

    font = kofont.build_font()
    fo = s2f(FONT_BANK << 16 | 0x8000)
    rom[fo:fo + len(font)] = font

    if test_text:
        import testtext
        testtext.apply(rom)
        testtext.apply_dialogue(rom)

    s = fix_checksum(rom)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(rom)
    print('wrote %s (%d bytes) checksum %04X, hooks %s' % (
        os.path.normpath(out), len(rom), s, {k: '%06X' % v for k, v in L.items()}))


if __name__ == '__main__':
    build(test_text='--no-test' not in sys.argv)
