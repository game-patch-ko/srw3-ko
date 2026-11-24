local outdir = "C:/work/sfc/srw3-ko/tools/rt/prologue/"
local n = 0
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 5300 and n % 40 == 0 then
    local f = io.open(outdir .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 7400 then emu.stop(0) end
end, emu.eventType.endFrame)
