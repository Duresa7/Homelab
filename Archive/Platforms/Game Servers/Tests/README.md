# Game Servers Tests

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

[minecraft-status.py](minecraft-status.py) performs a Minecraft Java status handshake and prints the version, protocol, player count, MOTD, and latency. It uses only the Python standard library; SRV mode additionally requires `dig` from the host's DNS utilities.

Test the public player-facing name exactly as a Minecraft client resolves it:

```bash
python3 minecraft-status.py minecraft.alphasecunited.com --srv
```

SRV mode resolves `_minecraft._tcp.minecraft.alphasecunited.com`, connects to the returned target and port, and keeps the relay hostname out of its JSON output. A direct endpoint can be checked with `--port`; `--srv` and `--port` are intentionally mutually exclusive.
