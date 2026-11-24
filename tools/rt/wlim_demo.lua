local out = io.open("C:/work/sfc/srw3-ko/tools/rt/wlim.txt", "w")
local n = 0
local seen = {}
emu.addMemoryCallback(function()
  local lim = emu.read(0x0E34, emu.memType.snesMemory) 
  local cur = emu.read(0x0E32, emu.memType.snesMemory)
  local ln = emu.read(0x0E33, emu.memType.snesMemory)
  local k = string.format("lim=%d line=%d", lim, ln)
  if seen[k] == nil then seen[k] = 999 end
  if cur < seen[k] then seen[k] = cur end
end, emu.callbackType.exec, 0x0185D5)
emu.addEventCallback(function()
  local inp = {}
  if false and n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if false and n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 9500 then
    for k, v in pairs(seen) do out:write(k .. " minstart=" .. v .. "\n") end
    out:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
