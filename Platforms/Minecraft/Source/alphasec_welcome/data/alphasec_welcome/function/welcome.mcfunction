tellraw @s [{"text":"Welcome to ","color":"gray"},{"text":"AlphaSec United Minecraft","color":"gold","bold":true},{"text":" server for ","color":"gray"},{"text":"Mobi and Friends.","color":"yellow"}]
tellraw @s [{"text":"Discord: ","color":"gray"},{"text":"Alphafly","color":"white"}]
tellraw @s [{"text":"Instagram: @_bigdogd_","color":"aqua","underlined":true,"click_event":{"action":"open_url","url":"https://www.instagram.com/_bigdogd_/"}},{"text":" | ","color":"gray"},{"text":"X: @AlphaFLy_TV","color":"aqua","underlined":true,"click_event":{"action":"open_url","url":"https://x.com/AlphaFLy_TV"}}]
tellraw @s [{"text":"AlphaSec United","color":"aqua","underlined":true,"click_event":{"action":"open_url","url":"https://www.alphasecunited.com/"}},{"text":" | ","color":"gray"},{"text":"Duresa Kadi Portfolio","color":"aqua","underlined":true,"click_event":{"action":"open_url","url":"https://duresakadi.com/"}}]
scoreboard players set @s asu.wlc.leave 0
scoreboard players operation @s asu.wlc.session = #current asu.wlc.session
