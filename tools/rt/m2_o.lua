
local OUT = "C:/work/sfc/srw3-ko/tools/shots/m2/"
local n = 0

local seenJ = {}
local jlog = io.open(OUT .. "orphans.txt", "w")
local function note(tag, a)
  if (a >> 16) < 0xB0 and ((a >> 16) & 0x7F) >= 0x01 then
    local k = string.format("%s %06X", tag, a)
    if not seenJ[k] then seenJ[k] = true; jlog:write(k .. "\n"); jlog:flush() end
  end
end
emu.addMemoryCallback(function()
  local M = emu.memType.snesMemory
  local a = emu.read(0x1C, M) * 65536 + emu.read16(0x1A, M)
  note("lay", a)
end, emu.callbackType.exec, 0x00CDA5)
emu.addMemoryCallback(function()
  local M = emu.memType.snesMemory
  local a = emu.read(0xAF, M) * 65536 + emu.read16(0xAD, M)
  note("dlg", a)
end, emu.callbackType.exec, 0x018B4F)

local seq = {{9000,"b"},{9060,"b"},{9120,"up"},{9150,"up"},{9180,"up"},{9210,"up"},{9260,"a"},{9320,"down"},{9350,"a"},{9560,"b"},{9640,"down"},{9670,"down"},{9700,"a"},{9880,"down"},{9940,"a"},{10080,"b"},{10140,"b"},{10200,"down"},{10230,"a"},{10360,"a"},{10480,"b"},{10540,"down"},{10570,"a"},{10700,"b"},{10760,"down"},{10790,"a"},{10920,"b"},{10980,"b"},{11040,"down"},{11070,"a"},{11250,"b"},{11320,"down"},{11350,"a"},{11500,"b"}}
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 8900 and n % 30 == 0 then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 11600 then emu.stop(0) end
end, emu.eventType.endFrame)
