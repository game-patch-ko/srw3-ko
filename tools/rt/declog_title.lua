-- Log every call of the LZ decompressor $80:885A (src $10-$12, dst $13-$14 bank $15) between frames A and B,
-- with the caller (return address) and how far the source pointer advanced.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 0, 4700
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "declog.txt", "w")
local function r24(a) return emu.read(a, M) + emu.read(a + 1, M) * 256 + emu.read(a + 2, M) * 65536 end
emu.addMemoryCallback(function()
  if n < A or n > B then return end
  local st = emu.getState()
  local sp = st["cpu.sp"]
  local ret = r24(sp + 1)
  log:write(string.format("%d dec src=%06X dst=%02X:%04X caller=%06X\n", n, r24(0x10), emu.read(0x15, M), emu.read16(0x13, M), ret))
  log:flush()
end, emu.callbackType.exec, 0x00885A)
emu.addMemoryCallback(function()
  if n < A or n > B then return end
  local st = emu.getState()
  log:write(string.format("%d end  srcY=%04X dstX=%04X\n", n, st["cpu.y"] & 0xFFFF, st["cpu.x"] & 0xFFFF)); log:flush()
end, emu.callbackType.exec, 0x0088F8)
emu.addEventCallback(function()
  local inp = {}
  if false and n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if false and n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
