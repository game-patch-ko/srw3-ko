"""python make_menu.py <outdir> <lua> "<frame:button,...>" <last> [shotevery]
New game -> stage 1 (same opening inputs as the other scripts), then the given presses; screenshots every N frames from 8900."""
import sys, os
outdir, lua, seq, last = sys.argv[1:5]
every = int(sys.argv[5]) if len(sys.argv) > 5 else 20
pairs = [p.split(':') for p in seq.split(',') if p]
tbl = ','.join('{%s,"%s"}' % (f, b) for f, b in pairs)
os.makedirs(outdir, exist_ok=True)
open(lua, 'w').write(r'''
local OUT = "%s/"
local n = 0
local seq = {%s}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n %% 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n %% 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 8900 and n %% %d == 0 then
    local f = io.open(OUT .. string.format("%%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= %s then emu.stop(0) end
end, emu.eventType.endFrame)
''' % (outdir.replace('\\', '/'), tbl, every, last))
