-- Find the decompressor: code writing $7F:0000-$7F:FFFF and the ROM ranges read, frames A..B.
local OUT = "C:/work/sfc/tools/shots/"
local A, B = 6680, 6772
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "titledec.txt", "w")
local wpc, rlo, rhi, rcnt = {}, {}, {}, {}
emu.addMemoryCallback(function(addr, val)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X", st["cpu.k"], st["cpu.pc"])
  if not wpc[k] then wpc[k] = {addr, addr, 0} end
  local w = wpc[k]
  if addr < w[1] then w[1] = addr end
  if addr > w[2] then w[2] = addr end
  w[3] = w[3] + 1
end, emu.callbackType.write, 0x7F0000, 0x7FFFFF)
local function rd(addr)
  if n < A or n > B then return end
  local st = emu.getState()
  local k = string.format("%02X:%04X", st["cpu.k"], st["cpu.pc"])
  if not rcnt[k] then rcnt[k] = 0; rlo[k] = addr; rhi[k] = addr end
  rcnt[k] = rcnt[k] + 1
  if addr < rlo[k] then rlo[k] = addr end
  if addr > rhi[k] then rhi[k] = addr end
end
emu.addMemoryCallback(rd, emu.callbackType.read, 0x888000, 0xAFFFFF)
emu.addMemoryCallback(rd, emu.callbackType.read, 0x088000, 0x2FFFFF)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n > B then
    for k, w in pairs(wpc) do log:write(string.format("write %s %06X-%06X count=%d\n", k, w[1], w[2], w[3])) end
    for k, c in pairs(rcnt) do log:write(string.format("read  %s %06X-%06X count=%d\n", k, rlo[k], rhi[k], c)) end
    log:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
