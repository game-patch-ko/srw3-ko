-- Who writes the RAM buffers that become the stage title tiles ($7E:8000-$7E:A7FF) before frame 6775.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6776, 6860
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titlewr.txt", "w")
local seen = {}
local cnt = {}
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X", st["cpu.k"], st["cpu.pc"])
  cnt[k] = (cnt[k] or 0) + 1
  if not seen[k] then
    seen[k] = true
    log:write(string.format("%d first write by %s at %06X val=%02X A=%04X X=%04X Y=%04X DB=%02X D=%04X\n",
      n, k, addr, val, st["cpu.a"] & 0xFFFF, st["cpu.x"] & 0xFFFF, st["cpu.y"] & 0xFFFF, st["cpu.dbr"] or 0, st["cpu.d"] or 0))
    log:flush()
  end
end, emu.callbackType.write, 0x7E0000, 0x7FFFFF)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == 6861 then
    for k, v in pairs(cnt) do log:write(string.format("count %s %d\n", k, v)) end
    -- dump the two buffers for offline decoding
    local f = io.open(OUT .. "title_7E8000.bin", "wb")
    local t = {}
    for i = 0, 0x27FF do t[#t + 1] = string.char(emu.read(0x7E8000 + i, M)) end
    f:write(table.concat(t)); f:close()
    log:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
