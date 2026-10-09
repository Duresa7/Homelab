# Status probe

**Created:** 2026-10-09  
**Last updated:** 2026-10-09

I use [minecraft-status.py](minecraft-status.py) to check the Minecraft Java status protocol. It reports the server version, protocol, player count, description and response time without logging in or changing the world. I reused the probe from the retired Game Servers platform.

```bash
python3 Platforms/Minecraft/Tests/minecraft-status.py 192.168.80.118
```

The deployment check returned Minecraft 26.3, protocol 777, zero connected players and a 20-player limit. I also ran the same probe against `127.0.0.1` on `alpha-prod-01`. Public tunnel verification is pending.
