# Join welcome

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

I installed a vanilla datapack on `alpha-prod-01` to show a private welcome message when a player joins Minecraft. I deployed it at 6:29 PM Eastern without restarting the container. The [source](../../Source/alphasec_welcome/) matches the seven files under `/opt/docker/minecraft/data/world/datapacks/alphasec_welcome/`.

## Message and behavior

The message contains four chat lines:

> Welcome to AlphaSec United Minecraft server for Mobi and Friends.  
> Discord: Alphafly  
> Instagram: @\_bigdogd\_ | X: @AlphaFLy_TV  
> AlphaSec United | Duresa Kadi Portfolio

I used gold and yellow for the welcome, white for the Discord name, and underlined aqua for the four clickable links. Instagram opens `https://www.instagram.com/_bigdogd_/`, X opens `https://x.com/AlphaFLy_TV`, and the websites open `https://www.alphasecunited.com/` and `https://duresakadi.com/`. Discord is a text label because no invite URL was supplied.

The pack targets data pack format 121.0 for Minecraft 26.3. Its load function initializes two scoreboard objectives and advances a session counter. Its tick function welcomes players whose session counter differs, or whose leave-game statistic has increased. The welcome function resets those scores after sending the four lines through `tellraw @s`. This also shows the welcome to connected players after a data reload. The server-list MOTD remains `AlphaSec United Minecraft`.

## Deployment and verification

The [deployment capture](../../Evidence/Join%20Welcome%20-%202026-10-11/Deployment.json) records file extraction, matching SHA-256 hashes, `reload`, and the enabled pack list. The first scoreboard query returned `Unknown scoreboard objective 'asu.wlc.session'`. The server had logged that it was paused after 60 seconds without players.

At 6:30:51 PM Eastern I explicitly ran the registered `#minecraft:load` and `#minecraft:tick` functions through the container console. Both resolved to the welcome pack's functions. The [function verification](../../Evidence/Join%20Welcome%20-%202026-10-11/Function%20Verification.json) shows session counter 2, initialized storage `1b`, and both `vanilla` and `file/alphasec_welcome` enabled. This checked function registration and initialization with no players online; it did not exercise player-targeted chat delivery.

At 6:31:23 PM Eastern, `save-all flush` returned `Saved the game`. The [save and health capture](../../Evidence/Join%20Welcome%20-%202026-10-11/Save%20and%20Health%20Verification.json) shows the same running, healthy container with zero automatic restarts.

At 6:33:53 PM Eastern I [checked live state again](../../Evidence/Join%20Welcome%20-%202026-10-11/Final%20Live%20Verification.json). All seven deployed file hashes matched the local source, the world directory inode remained `2621621`, and the container was healthy with zero automatic restarts and its original 5:55:27 PM Eastern start time. The [LAN probe](../../Evidence/Join%20Welcome%20-%202026-10-11/Final%20LAN%20Status.json) returned in 4.0 ms and the [public SRV probe](../../Evidence/Join%20Welcome%20-%202026-10-11/Final%20Public%20SRV%20Status.json) in 160.9 ms. Both reported Minecraft 26.3, protocol 777, zero players and a 20-player limit.

The deployment is complete. I have not verified the rendered chat, clickable links, or join/reconnect behavior with an authenticated player. The [public server-list ping limitation](DNS%20Publication%20-%202026-10-09.md) remains. I created no snapshot or backup. Because this pack lives inside the world, a future world reset must reinstall it from the source.
