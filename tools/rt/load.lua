-- title -> LOAD -> slot 1, then the given presses; screenshot every 30 frames
-- edit SEQ for the screens to visit. Run with out/srw3_auto.smc (its .srm = copy of the user's save).
local OUT = "C:/work/sfc/srw3-ko/tools/shots/ld/"
local SEQ = {
  -- title menu (START CONTINUE LOAD, horizontal) is up by frame ~4520
  {4560, "right"}, {4600, "right"},  -- START -> CONTINUE -> LOAD
  {4650, "a"},
  {4900, "a"},                -- slot 1
  {5100, "a"},
}
local LAST = 6400
local n = 0
emu.addEventCallback(function()
  local inp = {}
  for _, s in ipairs(SEQ) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= 4400 and n % 30 == 0 then
    local f = io.open(OUT .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= LAST then emu.stop(0) end
end, emu.eventType.endFrame)
