# Caddy

**Created:** 2026-07-24  
**Last updated:** 2026-09-25

I run Caddy as the edge reverse proxy on edge-01. It gives the Cloudflare Tunnel a single wildcard origin and forwards every `*.alphsec.com` request to the Coolify proxy on app-01. It's the external counterpart to Nginx Proxy Manager, which handles internal services. Public services live under `alphsec.com`; internal HTTPS names live under `alphasecunited.com`. Caddy only sees traffic that already arrived through the tunnel.

## Current state

| Item | Value |
|---|---|
| Host | edge-01, `192.168.30.10`, VLAN 30, Debian 13 |
| Caddy version | 2.6.2, unit active on 2026-09-25 |
| Service | `caddy.service`, systemd, enabled and active |
| Config | `/etc/caddy/Caddyfile`, root-owned, mode 644 |
| Listener | HTTP on port 80 only; `auto_https off` |
| Upstream | `192.168.80.10:80`, the Coolify Traefik proxy |
| Co-located | cloudflared 2026.8.3, the tunnel connector, unit active on 2026-09-25 |

TLS terminates at Cloudflare's edge, so Caddy serves plain HTTP on port 80 and requests no certificates. On 2026-08-04 two timestamped copies sat beside the live file (`Caddyfile.bak.20260512-112939` and `Caddyfile.bak.20260512-112953`). My rule is that a host keeps no config copies once the new file works, so they are due for removal; I have not checked since whether they are still there.

## Configuration

The live file is versioned at [Configuration/Caddyfile](Configuration/Caddyfile), captured byte-for-byte from edge-01 on 2026-08-04. It is one global block and one site block.

`header_up Host {host}` preserves the original hostname so Traefik on app-01 can route by Host. The match is the wildcard `*.alphsec.com`, so any new subdomain reaches Traefik with no Caddy change.

## Where Caddy sits

`Cloudflare edge -> Tunnel edge-01 -> Caddy :80 (this host) -> Traefik on app-01 :80 -> app container`. The [External Service Ingress design](../../Architecture/External-Service-Ingress.md) covers the full path and the firewall boundary between VLAN 30 and VLAN 80.

## Related

- [Access Paths](../../Architecture/Access-Paths.md): the five ways into the lab and where Caddy sits among them

- [Cloudflare Tunnel edge-01](../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md)
- [Coolify platform](../Coolify/README.md)
- [Nginx Proxy Manager, the internal proxy](../Nginx%20Proxy%20Manager/README.md)
