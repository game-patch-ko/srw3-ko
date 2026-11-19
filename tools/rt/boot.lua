-- Screenshots every 150 frames from power-on to the title menu (no input).
local OUT = "C:/work/sfc/tools/shots/boot/"
local n = 0
emu.addEventCallback(function()
  n = n + 1
  if n % 150 == 0 then local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close() end
  if n >= 4650 then emu.stop(0) end
end, emu.eventType.endFrame)
