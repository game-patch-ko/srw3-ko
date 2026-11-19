
local OUT = "C:/work/sfc/tools/shots/m3/"
local n = 0
local seq = {{9000,"a"},{9120,"b"},{9200,"right"},{9230,"right"},{9300,"up"},{9360,"a"},{9600,"right"},{9800,"right"},{10000,"down"},{10100,"down"},{10300,"b"},{10400,"b"}}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 8900 and n % 50 == 0 then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 10500 then emu.stop(0) end
end, emu.eventType.endFrame)
