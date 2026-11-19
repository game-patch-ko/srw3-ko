-- Sprite table ($00:0500, 544 bytes, DMA'd to OAM each frame) while the stage title is shown,
-- and which code writes it (PC, first value) in frames A..B.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6870, 6880
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titleoam.txt", "w")
local seen = {}
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X", st["cpu.k"], st["cpu.pc"])
  if not seen[k] then
    seen[k] = true
    log:write(string.format("%d write by %s at %04X val=%02X A=%04X X=%04X Y=%04X DB=%02X\n", n, k, addr & 0xFFFF, val,
      st["cpu.a"] & 0xFFFF, st["cpu.x"] & 0xFFFF, st["cpu.y"] & 0xFFFF, st["cpu.dbr"] or 0))
    log:flush()
  end
end, emu.callbackType.write, 0x000500, 0x00071F)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == B then
    for i = 0, 127 do
      local b = 0x0500 + i * 4
      local x, y, t, a = emu.read(b, M), emu.read(b + 1, M), emu.read(b + 2, M), emu.read(b + 3, M)
      local hi = emu.read(0x0700 + (i // 4), M)
      local xh = (hi >> ((i % 4) * 2)) & 1
      local big = (hi >> ((i % 4) * 2 + 1)) & 1
      if y < 224 then log:write(string.format("spr %3d x=%3d y=%3d tile=%02X attr=%02X big=%d\n", i, x + 256 * xh, y, t, a, big)) end
    end
    log:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
