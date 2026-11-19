-- Metasprite ids drawn while the title is up ($0A id, $0B set; handler $80:D595).
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6870, 6871
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titleids.txt", "w")
emu.addMemoryCallback(function()
  if n < A or n > B then return end
  log:write(string.format("%d set=%02X id=%02X x=%04X y=%04X\n", n, emu.read(0x0B, M) & 0x3F, emu.read(0x0A, M),
    emu.read16(0x0E, M), emu.read16(0x10, M))); log:flush()
end, emu.callbackType.exec, 0x00D595)
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
