"""Lua that logs which code reads given ROM ranges (name tables).  args: outfile mode last path ranges(start:len,...)"""
import sys
tpl = r'''
local out = io.open("OUTFILE", "w")
local n = 0
local MODE = "MODEV"
local seen = {}
local seq = {{9000,'a'},{9120,'b'},{9200,'right'},{9230,'right'},{9300,'a'},{9420,'down'},{9480,'a'},{9600,'b'},{9660,'b'},{9740,'start'},{9860,'b'},{9940,'x'},{10060,'b'},{10140,'y'}}
local function cb(addr, val)
  local s = emu.getState()
  local key = string.format("%02X:%04X", s["cpu.k"], s["cpu.pc"])
  local c = seen[key]
  if c == nil then
    seen[key] = 1
    out:write(string.format("%d %s addr=%06X X=%04X Y=%04X\n", n, key, addr, s["cpu.x"], s["cpu.y"]))
  end
end
RANGES
emu.addEventCallback(function()
  local inp = {}
  if MODE == "game" then
    if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
    if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
    for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= LAST then out:close(); emu.stop(0) end
end, emu.eventType.endFrame)
'''
outfile, mode, last, path, ranges = sys.argv[1:6]
rl = []
for r in ranges.split(','):
    a, l = r.split(':'); a = int(a, 16); l = int(l)
    rl.append('emu.addMemoryCallback(cb, emu.callbackType.read, 0x%06X, 0x%06X)' % (a, a + l - 1))
open(path, 'w').write(tpl.replace('OUTFILE', outfile).replace('MODEV', mode).replace('LAST', last).replace('RANGES', '\n'.join(rl)))
