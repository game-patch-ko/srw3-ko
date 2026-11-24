local n = 0
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == 9100 then
    local f = io.open("C:/work/sfc/srw3-ko/tools/shots/wram.bin", "wb")
    local t = {}
    for i = 0, 0x1FFFF do t[#t + 1] = string.char(emu.read(0x7E0000 + i, emu.memType.snesMemory)) end
    f:write(table.concat(t)); f:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
