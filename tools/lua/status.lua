local outdir = "C:/work/sfc/srw3-ko/tools/shots/status/"
local n = 0
local seq = {{9000,'a'},{9120,'b'},{9200,'right'},{9230,'right'},{9300,'up'},{9360,'a'},{9700,'right'},{9800,'right'},{9900,'b'},{9960,'b'}}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 9280 and n % 40 == 0 then
    local f = io.open(outdir .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 10080 then emu.stop(0) end
end, emu.eventType.endFrame)
