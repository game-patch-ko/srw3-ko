local outdir = "C:/work/sfc/tools/shots/ng/"
local n = 0
local hits = {CA09=0, CBC6=0, WRAP=0, HANG=0}
local firstCA = nil
emu.addMemoryCallback(function() hits.CA09 = hits.CA09 + 1; if not firstCA then firstCA = n end end, emu.callbackType.exec, 0x80CA09)
emu.addMemoryCallback(function() hits.CBC6 = hits.CBC6 + 1 end, emu.callbackType.exec, 0x80CBC6)
emu.addMemoryCallback(function() hits.WRAP = hits.WRAP + 1 end, emu.callbackType.exec, 0xB08025)
emu.addMemoryCallback(function() hits.HANG = hits.HANG + 1 end, emu.callbackType.exec, 0xB08037)
emu.addEventCallback(function()
  local inp = {}
  if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
  if n >= 5800 and (n % 60) < 6 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 9000 and n % 300 == 0 then
    local f = io.open(outdir .. string.format("p%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 12000 then
    local f = io.open(outdir .. "paths.txt", "w")
    f:write(string.format("CA09=%d CBC6=%d wrapper=%d hangul=%d firstCA09frame=%s\n", hits.CA09, hits.CBC6, hits.WRAP, hits.HANG, tostring(firstCA)))
    f:close(); emu.stop(0)
  end
end, emu.eventType.endFrame)
