-- usage: frames list via global; take screenshots at given frames then stop
local outdir = "C:/work/sfc/srw3-ko/tools/shots/"
local frames = {300, 600, 900, 1200}
local n = 0
local idx = 1
emu.addEventCallback(function()
  n = n + 1
  if idx <= #frames and n == frames[idx] then
    local png = emu.takeScreenshot()
    local f = io.open(outdir .. "f" .. n .. ".png", "wb"); f:write(png); f:close()
    idx = idx + 1
    if idx > #frames then emu.stop(0) end
  end
end, emu.eventType.endFrame)
