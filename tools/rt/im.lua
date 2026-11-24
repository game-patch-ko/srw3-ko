-- probe: game mode byte $95 (dispatcher $81:8C3F, table $81:8C48; 0x0A = intermission init $81:8FBE)
local OUT = "C:/work/sfc/srw3-ko/tools/shots/im/"
local SETAT, SETVAL = 9100, 0x0A
local n = 0
local M = emu.memType.snesMemory
local ml = io.open(OUT .. "mode.txt", "w")
local last = -1
emu.addMemoryCallback(function()
  ml:write(string.format("%d dispatch $95=%02X\n", n, emu.read(0x95, M))); ml:flush()
end, emu.callbackType.exec, 0x018C3F)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  if n >= 9200 and (n % 90) < 4 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  local v = emu.read(0x95, M)
  if v ~= last then ml:write(string.format("%d $95=%02X\n", n, v)); ml:flush(); last = v end
  if n == SETAT then emu.write(0x95, SETVAL, M); ml:write("set\n") end
  if n >= 8900 and n % 40 == 0 then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 10600 then ml:close(); emu.stop(0) end
end, emu.eventType.endFrame)
