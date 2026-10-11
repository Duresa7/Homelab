# Status probe

**Created:** 2026-10-09  
**Last updated:** 2026-10-09

I use [minecraft-status.py](minecraft-status.py) to check the Minecraft Java status protocol. It reports the server version, protocol, player count, description and response time without logging in or changing the world. I reused the probe from the retired Game Servers platform.

```bash
python3 Platforms/Minecraft/Tests/minecraft-status.py 192.168.80.118
```

The deployment check returned Minecraft 26.3, protocol 777, zero connected players and a 20-player limit. I also ran the same probe against `127.0.0.1` on `alpha-prod-01`. After transferring the retained Playit tunnel to the shared agent on 2026-10-09, I resolved its public Minecraft SRV record and queried the resulting target. That response matched the local version and player limit in 280.6 ms. The [deployment record](../Documentation/Change%20Records/Deployment%20-%202026-10-09.md#playit) links the redacted verification export.

After restoring `minecraft.alphasecunited.com` in Cloudflare, I verified its SRV route and the initial login transport. The SRV status probe sends the resolved target hostname in its handshake; it does not reproduce Minecraft 26.3's server-list ping, which sends the entered hostname and is rejected by Playit for the custom name. The [DNS publication record](../Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md) holds that limitation and the protocol checks.
