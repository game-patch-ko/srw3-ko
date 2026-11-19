-- Which code reads which ROM area while the stage 1 title (第1話『暗雲』) is being set up and shown.
-- Logs unique (PC, ROM bank) pairs for reads in banks $80-$AF / $00-$2F between frames A and B,
-- plus VRAM DMA writes ($2116/$2117 address, $4302.. source) via register write callbacks.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6600, 6820
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titleread.txt", "w")
local seen = {}
local function rd(addr)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X bank=%02X", st["cpu.k"], st["cpu.pc"], (addr >> 16) & 0xFF)
  if not seen[k] then seen[k] = addr; log:write(string.format("%d read %s first=%06X\n", n, k, addr)); log:flush() end
end
emu.addMemoryCallback(rd, emu.callbackType.read, 0x888000, 0xAFFFFF)
emu.addMemoryCallback(rd, emu.callbackType.read, 0x088000, 0x2FFFFF)
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  local src = emu.read(0x4302, M) + emu.read(0x4303, M) * 256 + emu.read(0x4304, M) * 65536
  local dst = emu.read16(0x2116, M)
  log:write(string.format("%d DMA en=%02X src(ch0)=%06X vram=%04X\n", n, val, src, dst)); log:flush()
end, emu.callbackType.write, 0x420B, 0x420B)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == 6760 then local f = io.open(OUT .. "titleread.png", "wb"); f:write(emu.takeScreenshot()); f:close() end
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
