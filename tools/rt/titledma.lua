-- All DMA transfers (every enabled channel) between frames A and B: source, size, B-bus target, VRAM address.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6740, 6900
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titledma.txt", "w")
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  for ch = 0, 7 do
    if (val >> ch) & 1 == 1 then
      local b = 0x4300 + ch * 0x10
      local ctl = emu.read(b, M)
      local bbus = emu.read(b + 1, M)
      local src = emu.read(b + 2, M) + emu.read(b + 3, M) * 256 + emu.read(b + 4, M) * 65536
      local size = emu.read(b + 5, M) + emu.read(b + 6, M) * 256
      local st = emu.getState()
      log:write(string.format("%d ch%d ctl=%02X bbus=21%02X src=%06X size=%04X vram=%04X pc=%02X:%04X\n",
        n, ch, ctl, bbus, src, size, emu.read16(0x2116, M), st["cpu.k"], st["cpu.pc"]))
    end
  end
  log:flush()
end, emu.callbackType.write, 0x420B, 0x420B)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n % 10 == 0 and n >= A and n <= B then
    local f = io.open(OUT .. string.format("td%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
