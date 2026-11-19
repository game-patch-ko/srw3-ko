-- While the title is up: every ROM read (banks 80-BF and 00-3F) with its PC, frames A..B.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6870, 6872
local n = 0
local log = io.open(OUT .. "titlespr.txt", "w")
local seen = {}
local function rd(addr)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X %06X", st["cpu.k"], st["cpu.pc"], addr)
  if not seen[k] then seen[k] = true; log:write(n .. " " .. k .. "\n") end
end
emu.addMemoryCallback(rd, emu.callbackType.read, 0x808000, 0xBFFFFF)
emu.addMemoryCallback(rd, emu.callbackType.read, 0x028000, 0x3FFFFF)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
