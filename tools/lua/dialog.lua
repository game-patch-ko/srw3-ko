local outdir = "C:/work/sfc/srw3-ko/tools/shots/ng/"
local n = 0
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and (n % 150) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 5500 and n % 75 == 0 then
    local f = io.open(outdir .. string.format("d%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 8000 then emu.stop(0) end
end, emu.eventType.endFrame)
