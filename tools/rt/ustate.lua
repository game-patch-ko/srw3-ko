-- Load a copy of the user's Mesen save state (intermission), press the given buttons, take screenshots.
-- loadSavestate must run inside a CPU exec callback, so it is done from the NMI handler ($00:828F).
-- Intermission command menu order: 저장하기, 파워업, 능력보기, 교체, 유닛 폐기, 다음 맵 (cursor starts on 저장하기)
local OUT = "C:/work/sfc/tools/shots/im2/"
local STATE = OUT .. "user_state.mss"
local SEQ = {
  {60, "down"}, {100, "a"},                 -- 파워업
  {220, "a"}, {340, "a"}, {460, "b"}, {520, "b"}, {580, "b"}, {640, "b"},
  {700, "down"}, {740, "a"},                -- 능력보기
  {860, "a"}, {980, "b"}, {1040, "b"}, {1100, "b"},
  {1160, "down"}, {1200, "a"},              -- 교체
  {1320, "a"}, {1440, "b"}, {1500, "b"}, {1560, "b"},
  {1620, "down"}, {1660, "a"},              -- 유닛 폐기
  {1780, "a"}, {1900, "b"}, {1960, "b"}, {2020, "b"},
}
local LAST = 2100
local n, loaded, t = 0, false, 0
local log = io.open(OUT .. "ustate.txt", "w")
local data = io.open(STATE, "rb"):read("a")
emu.addMemoryCallback(function()
  if not loaded and n >= 30 then
    local ok, e = pcall(emu.loadSavestate, data)
    log:write("load " .. tostring(ok) .. " " .. tostring(e) .. "\n"); log:flush()
    loaded = true; t = 0
  end
end, emu.callbackType.exec, 0x00828F)
emu.addEventCallback(function()
  local inp = {}
  if loaded then for _, s in ipairs(SEQ) do if t >= s[1] and t < s[1] + 6 then inp[s[2]] = true end end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if loaded then
    t = t + 1
    if t % 30 == 0 then local f = io.open(OUT .. string.format("s%05d.png", t), "wb"); f:write(emu.takeScreenshot()); f:close() end
    if t >= LAST then log:close(); emu.stop(0) end
  end
end, emu.eventType.endFrame)
