local outdir = "C:/work/sfc/tools/shots/ng/"
local n, polls = 0, 0
local log = io.open(outdir .. "inp.txt", "w")
emu.addEventCallback(function()
  polls = polls + 1
  if n >= 5150 and n < 5600 and (n % 40) < 8 then emu.setInput({start=true}, 0) end
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 5150 and n < 5200 then
    local ok, gi = pcall(emu.getInput, 0)
    local s = ok and tostring(gi and gi.start) or ("err " .. tostring(gi))
    log:write(string.format("%d polls=%d getInput.start=%s 4218=%02X\n", n, polls, s, emu.read(0x4218, emu.memType.snesMemory)))
  end
  if n == 5700 then local f = io.open(outdir .. "after.png", "wb"); f:write(emu.takeScreenshot()); f:close() end
  if n >= 5700 then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
