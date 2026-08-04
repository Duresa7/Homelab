# Caddy Configuration

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

This folder holds the file Caddy actually reads, not a description of it.

| File | Live path | Captured |
|---|---|---|
| `Caddyfile` | `/etc/caddy/Caddyfile` on edge-01, root-owned, mode 644 | 2026-08-04, byte-for-byte from the running host |

The live file was last written on 2026-05-12 and Caddy reports 2.6.2. The comment header is Caddy's own default text, kept because it is what is on disk.

Two timestamped backups sit beside the live file on edge-01, `Caddyfile.bak.20260512-112939` and `Caddyfile.bak.20260512-112953`. They are not captured here: they are editing residue from the original write, and the `.gitignore` residue patterns would drop them anyway.

To restore, copy `Caddyfile` to `/etc/caddy/Caddyfile`, run `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then `systemctl reload caddy`. Reload rather than restart, so an open tunnel connection is not dropped for a config that fails to parse.

The [platform README](../README.md) explains where Caddy sits in the ingress path and why it serves plain HTTP.
