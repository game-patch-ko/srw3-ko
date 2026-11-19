-- auto-press: Start/A pulses; screenshot every SHOT frames; log block/msg vars
local outdir = "C:/work/sfc/tools/shots/"
local SHOT, LAST = 300, 9000
local n = 0
local log = io.open(outdir .. "log.txt", "w")
emu.addEventCallback(function()
  local inp = {}
  local t = n % 120
  if n > 600 then
    if t < 4 then inp.start = (n % 480 < 120) end
    if t >= 60 and t < 64 then inp.a = true end
  end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n % SHOT == 0 then
    local f = io.open(outdir .. string.format("e%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
    local blk = emu.read(0x0E39, emu.memType.snesMemory)
    local msg = emu.read(0x0E38, emu.memType.snesMemory)
    local ad = emu.read16(0xAD, emu.memType.snesMemory) ; local af = emu.read(0xAF, emu.memType.snesMemory)
    log:write(string.format("%d blk=%02X msg=%02X ptr=%02X:%04X\n", n, blk, msg, af, ad)); log:flush()
  end
  if n >= LAST then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
