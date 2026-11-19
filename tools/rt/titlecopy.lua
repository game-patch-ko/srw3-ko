-- Who reads the decompressed title font ($7F:0000-$7F:7FFF) after it is unpacked (frame 6708) and
-- before the title shows; log PC, registers, the direct page pointers, first few addresses.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6708, 6880
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titlecopy.txt", "w")
local cnt, first = {}, {}
emu.addMemoryCallback(function(addr)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X", st["cpu.k"], st["cpu.pc"])
  cnt[k] = (cnt[k] or 0) + 1
  if cnt[k] <= 3 then
    log:write(string.format("%d read %s %06X X=%04X Y=%04X A=%04X DB=%02X\n", n, k, addr, st["cpu.x"] & 0xFFFF,
      st["cpu.y"] & 0xFFFF, st["cpu.a"] & 0xFFFF, st["cpu.dbr"] or 0)); log:flush()
  end
end, emu.callbackType.read, 0x7F0000, 0x7F7FFF)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then
    for k, v in pairs(cnt) do log:write(string.format("count %s %d\n", k, v)) end
    log:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
