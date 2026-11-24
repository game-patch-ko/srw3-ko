-- Dump VRAM, CGRAM and PPU state while the stage title is on screen.
local OUT = "C:/work/sfc/srw3-ko/tools/shots/"
local AT = 6880
local n = 0
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == AT then
    local function dump(name, mt, size)
      local t = {}
      for i = 0, size - 1 do t[#t + 1] = string.char(emu.read(i, mt)) end
      local f = io.open(OUT .. name, "wb"); f:write(table.concat(t)); f:close()
    end
    dump("t_vram.bin", emu.memType.snesVideoRam, 0x10000)
    dump("t_cgram.bin", emu.memType.snesCgRam, 0x200)
    local st = emu.getState()
    local f = io.open(OUT .. "t_ppu.txt", "w")
    local keys = {}
    for k, v in pairs(st) do if string.find(k, "ppu") then keys[#keys + 1] = k end end
    table.sort(keys)
    for _, k in ipairs(keys) do f:write(k .. " = " .. tostring(st[k]) .. "\n") end
    f:close()
    local g = io.open(OUT .. "t_screen.png", "wb"); g:write(emu.takeScreenshot()); g:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
