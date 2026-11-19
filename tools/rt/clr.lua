
local OUT = "C:/work/sfc/tools/shots/clr/"
local n = 0
local seq = {{9000,"b"},{9060,"b"},{9120,"up"},{9150,"up"},{9180,"up"},{9210,"up"},{9260,"a"},{9330,"a"},{9400,"left"},{9440,"a"},{9800,"a"},{9900,"a"},{10000,"a"},{10100,"a"},{10200,"a"},{10300,"a"},{10400,"a"},{10500,"a"},{10600,"a"},{10700,"a"},{10800,"a"},{10900,"a"},{11000,"a"},{11200,"a"},{11400,"a"},{11600,"a"},{11800,"a"},{12000,"a"},{12200,"a"},{12400,"a"}}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == 9240 then
    for i = 0, 15 do emu.write16(0x7E1836 + 2 * i, 0, emu.memType.snesMemory) end
  end
  if n >= 8900 and n % 60 == 0 then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 13000 then emu.stop(0) end
end, emu.eventType.endFrame)
