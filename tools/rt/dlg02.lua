
local outdir = "C:/work/sfc/tools/shots/dlg02/"
local n = 0
local MODE = "game"
local seq = {{9000,'a'},{9120,'b'},{9200,'right'},{9230,'right'},{9300,'a'},{9420,'down'},{9480,'a'},{9600,'b'},{9660,'b'},{9740,'start'},{9860,'b'},{9940,'x'},{10060,'b'},{10140,'y'}}
emu.addEventCallback(function()
  local inp = {}
  if MODE == "game" then
    if n >= 5150 and n < 5300 and (n % 40) < 8 then inp.start = true end
    if n >= 5800 and n < 8900 and (n % 60) < 6 then inp.a = true end
    for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 5100 and n % 60 == 0 then
    local f = io.open(outdir .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= 9000 then emu.stop(0) end
end, emu.eventType.endFrame)
