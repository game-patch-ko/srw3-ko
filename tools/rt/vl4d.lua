
local OUT = "C:/work/sfc/tools/shots/vl4/"
local T = {{1,0},{1,1},{1,2},{1,3},{1,4},{1,5},{1,6},{1,7},{1,8},{1,9}}
local M = emu.memType.snesMemory
local log = io.open(OUT .. "lay.txt", "w")
local n, idx, armed, cur = 0, 0, false, nil
local SAVEAT, state, t0 = 9255, nil, -1
local function entry_addr(t, k)
  local p = 0x80D277 + 3 * t
  local base = emu.read(p, M) + emu.read(p + 1, M) * 256 + emu.read(p + 2, M) * 65536
  local bank = base & 0xFF0000
  local a = base + 2 * k
  return bank + emu.read(a, M) + emu.read(a + 1, M) * 256
end
emu.addMemoryCallback(function()
  if armed and emu.read(0x01, M) == 0 and (emu.getState()["cpu.y"] & 0xFFFF) == 0x22 then
    armed = false
    local tg = T[idx]
    local a = entry_addr(tg[1], tg[2])
    emu.write16(0x1A, a & 0xFFFF, M); emu.write(0x1C, (a >> 16) & 0xFF, M)
    cur = string.format("%d %02X %06X", tg[1], tg[2], a)
  end
end, emu.callbackType.exec, 0x00C7F1)
local seq = {{9000,"b"},{9060,"b"},{9120,"up"},{9150,"up"},{9180,"up"},{9210,"up"}}
emu.addEventCallback(function()
  local inp = {}
  if state == nil then
    if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
    if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
    for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  elseif t0 >= 0 and n - t0 < 4 then
    inp.a = true
  end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  if state == nil and n == SAVEAT then local ok, r = pcall(emu.createSavestate); log:write("create " .. tostring(ok) .. " " .. (ok and tostring(#r) or tostring(r)) .. "
"); log:flush(); if ok then state = r end end
  if state ~= nil and (t0 < 0 or n - t0 == 60) then
    if t0 >= 0 then
      local tg = T[idx]
      local name = string.format("%d_%02X.png", tg[1], tg[2])
      if cur then local f = io.open(OUT .. name, "wb"); f:write(emu.takeScreenshot()); f:close() end
      log:write(name .. " " .. (cur or "not-hijacked") .. "\n"); log:flush()
    end
    idx = idx + 1
    if idx > #T then log:close(); emu.stop(0); return end
    local ok, e = pcall(emu.loadSavestate, state); if not ok then log:write("load err " .. tostring(e) .. "
"); log:flush() end
    armed = true; cur = nil; t0 = n
  end
end, emu.eventType.startFrame)
emu.addEventCallback(function() n = n + 1 end, emu.eventType.endFrame)
