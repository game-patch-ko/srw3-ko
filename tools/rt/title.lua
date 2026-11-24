local n, g, lay, dlg = 0, 0, 0, 0
local log = io.open("C:/work/sfc/srw3-ko/tools/shots/title.txt", "w")
emu.addMemoryCallback(function() g = g + 1 end, emu.callbackType.exec, 0xB08025)
emu.addMemoryCallback(function() lay = lay + 1 end, emu.callbackType.exec, 0x00CDA5)
emu.addMemoryCallback(function() dlg = dlg + 1 end, emu.callbackType.exec, 0x018B4F)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 6400 and n <= 8000 and n % 20 == 0 then
    log:write(string.format("%d glyph=%d lay=%d dlg=%d\n", n, g, lay, dlg)); g, lay, dlg = 0, 0, 0
    if n % 100 == 0 then local f = io.open(string.format("C:/work/sfc/srw3-ko/tools/shots/t%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close() end
  end
  if n > 8000 then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
