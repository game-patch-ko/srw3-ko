-- Stage title: log every glyph draw (A = char code) with the caller (return address on the stack)
-- around frame 6620, and which glyph path runs ($80:CA09 vs $80:CBC6 vs the KO wrapper $B0:8025).
local OUT = "C:/work/sfc/srw3-ko/tools/shots/"
local A, B = 6700, 6860
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titleglyph.txt", "w")
local function stack3()
  local st = emu.getState()
  local sp = st["cpu.sp"]
  return emu.read(sp + 1, M) + emu.read(sp + 2, M) * 256 + emu.read(sp + 3, M) * 65536
end
local function hook(tag)
  return function()
    if n < A or n > B then return end
    local st = emu.getState()
    log:write(string.format("%d %s A=%04X X=%04X Y=%04X ret=%06X DB=%02X\n", n, tag, st["cpu.a"] & 0xFFFF,
      st["cpu.x"] & 0xFFFF, st["cpu.y"] & 0xFFFF, stack3(), st["cpu.dbr"] or 0))
    log:flush()
  end
end
emu.addMemoryCallback(hook("C90E"), emu.callbackType.exec, 0x00C90E)
emu.addMemoryCallback(hook("CA09"), emu.callbackType.exec, 0x00CA09)
emu.addMemoryCallback(hook("CBC6"), emu.callbackType.exec, 0x00CBC6)
emu.addMemoryCallback(hook("B08025"), emu.callbackType.exec, 0xB08025)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
