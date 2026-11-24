-- Stage 1: end the first player turn and let the enemy phase run (A pressed periodically), screenshots every 30 frames.
local OUT = "C:/work/sfc/tools/shots/ep/"
local n = 0
local seq = {{9000,"b"},{9060,"b"},{9120,"up"},{9150,"up"},{9180,"up"},{9210,"up"},{9260,"a"},{9400,"a"},{9520,"a"}}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  if n >= 9700 and (n % 50) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 9300 and n % 30 == 0 then local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close() end
  if n >= 16000 then emu.stop(0) end
end, emu.eventType.endFrame)
