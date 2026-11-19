-- CPU writes to the VRAM ports ($2116-$2119) around the stage title: PC, address set, values.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6740, 6860
local n = 0
local log = io.open(OUT .. "titlevram.txt", "w")
local cnt = 0
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  cnt = cnt + 1
  if cnt > 600 then return end
  local st = emu.getState()
  log:write(string.format("%d %04X=%02X pc=%02X:%04X X=%04X Y=%04X A=%04X\n", n, addr, val, st["cpu.k"], st["cpu.pc"],
    st["cpu.x"] & 0xFFFF, st["cpu.y"] & 0xFFFF, st["cpu.a"] & 0xFFFF))
  log:flush()
end, emu.callbackType.write, 0x2115, 0x2119)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then log:write("total " .. cnt .. "\n"); log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
