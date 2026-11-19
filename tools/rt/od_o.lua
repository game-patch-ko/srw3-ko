
local OUT = "C:/work/sfc/tools/shots/od/"
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

local seq = {}
emu.addEventCallback(function()
  local inp = {}
  if false and n >= 5150 and (n % 40) < 8 then inp.start = true end
  if false and n >= 5800 and (n % 60) < 6 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if false then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 12000 then emu.stop(0) end
end, emu.eventType.endFrame)
