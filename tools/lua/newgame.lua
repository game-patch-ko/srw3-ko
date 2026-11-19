-- start a new game from title, advance text with A, capture every SHOT frames
local outdir = "C:/work/sfc/tools/shots/ng/"
local SHOT, LAST = 120, 16000
local n = 0
local log = io.open(outdir .. "log.txt", "w")
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5600 and (n % 40) < 4 then inp.start = true end
  if n >= 5600 and (n % 50) < 4 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n % SHOT == 0 and n >= 5100 then
    local f = io.open(outdir .. string.format("n%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
    local blk = emu.read(0x0E39, emu.memType.snesMemory)
    local msg = emu.read(0x0E38, emu.memType.snesMemory)
    log:write(string.format("%d blk=%02X msg=%02X\n", n, blk, msg)); log:flush()
  end
  if n >= LAST then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
