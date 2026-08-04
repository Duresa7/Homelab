# Cloudflare Tunnel: edge-01

**Created:** 2026-07-24  
**Last updated:** 2026-07-24

I run one Cloudflare Tunnel, `edge-01`, & manage its configuration from the Cloudflare Zero Trust dashboard rather than a local file. The connector runs as cloudflared on the edge-01 host. This tunnel is the only inbound path from the Internet to my services; the router forwards no ports.

## Identity

| Field | Value |
|---|---|
| Name | edge-01 |
| Tunnel ID | `<REDACTED_TUNNEL_ID>` |
| Created | 2026-02-14 |
| Configuration source | Remote (dashboard-managed) |
| Connector host | edge-01, `192.168.90.10`, VLAN 90, Debian 13 |
| cloudflared version | 2026.6.1 |
| Connections | 4, healthy (verified 2026-07-24) |
| Public DNS zone | alphsec.com |

## Ingress rules

Cloudflare evaluates these in order. I edit them in the dashboard. The local `/etc/cloudflared/config.yml` on edge-01 holds only the tunnel ID, the credentials-file path, & a placeholder `http_status:404` ingress that the dashboard configuration overrides, so reading that file alone won't show the live routing.

| Order | Hostname | Origin service | Notes |
|---|---|---|---|
| 1 | `coolify-a1.alphsec.com` | `http://192.168.80.10:8000` | Coolify control panel, direct to app-01, skips Caddy |
| 2 | `*.alphsec.com` | `http://localhost:80` | Caddy on edge-01, carries every deployed app |
| 3 | (catch-all) | `http_status:404` | Anything unmatched |

## DNS

Both hostnames are proxied CNAMEs into the tunnel in the `alphsec.com` zone:

- `*.alphsec.com` CNAME `<REDACTED_TUNNEL_ID>.cfargotunnel.com`, proxied
- `coolify-a1.alphsec.com` CNAME the same target, proxied

## Credentials

The connector authenticates with `/home/dkadi/.cloudflared/<REDACTED_TUNNEL_ID>.json` on edge-01. I don't store that file or its contents in this repository.

## Access & firewall

Cloudflare Access protects `coolify-a1.alphsec.com`; see [Access applications](applications.md). A UniFi policy limits edge-01 to app-01 on TCP 80 & 8000; see the UniFi section of the [Coolify Access Hardening record](../Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

## Account zones

I hold four zones in this Cloudflare account: `alphasecunited.com`, `alphsec.com`, `duresakadi.com`, & `duresakadi.me`. External service ingress currently uses `alphsec.com`.

## Related

- End-to-end design: [External Service Ingress](../../../../Architecture/External-Service-Ingress.md)
