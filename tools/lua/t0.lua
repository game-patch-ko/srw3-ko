local n=0
emu.addEventCallback(function() n=n+1; if n==60 then emu.stop(7) end end, emu.eventType.endFrame)
