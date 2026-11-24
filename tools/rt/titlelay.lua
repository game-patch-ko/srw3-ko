-- Which layout (table/entry/pointer) is drawn around the stage title, and the bytes it reads.
local OUT = "C:/work/sfc/srw3-ko/tools/shots/"
local A, B = 6740, 6860
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titlelay.txt", "w")
emu.addMemoryCallback(function()
  if n < A or n > B then return end
  local st = emu.getState()
  log:write(string.format("%d layout tbl=%02X ent=%02X ptr=%02X%04X\n", n, emu.read(0x01, M), (st["cpu.y"] & 0xFFFF) // 2,
    emu.read(0x1C, M), emu.read16(0x1A, M))); log:flush()
end, emu.callbackType.exec, 0x00C7F1)
emu.addMemoryCallback(function()
  if n < A or n > B then return end
  local a = emu.read(0x1C, M) * 65536 + emu.read16(0x1A, M)
  log:write(string.format("%d read %06X = %02X\n", n, a, emu.read(a, M))); log:flush()
end, emu.callbackType.exec, 0x00CDA5)
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
