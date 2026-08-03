# Cloudflare Tunnel: edge-01

**Created:** 2026-07-24  
**Last updated:** 2026-07-24

I run one Cloudflare Tunnel, `edge-01`, & manage its configuration from the Cloudflare Zero Trust dashboard rather than a local file. The connector runs as cloudflared on the edge-01 host. This tunnel is the only inbound path from the Internet to my services; the router forwards no ports.

## Identity

| Field | Value |
|---|---|
| Name | edge-01 |
| Tunnel ID | `<YOUR_TUNNEL_ID>` |
| Created | 2026-02-14 |
| Configuration source | Remote (dashboard-managed) |
| Connector host | edge-01, `192.168.90.10`, VLAN 90, Debian 13 |
| cloudflared version | 2026.6.1 |
| Connections | 4, healthy (verified 2026-07-24) |
| Public DNS zone | <YOUR_PUBLIC_DOMAIN> |

## Ingress rules

Cloudflare evaluates these in order. I edit them in the dashboard. The local `/etc/cloudflared/config.yml` on edge-01 holds only the tunnel ID, the credentials-file path, & a placeholder `http_status:404` ingress that the dashboard configuration overrides, so reading that file alone won't show the live routing.

| Order | Hostname | Origin service | Notes |
|---|---|---|---|
| 1 | `coolify-a1.<YOUR_PUBLIC_DOMAIN>` | `http://192.168.80.10:8000` | Coolify control panel, direct to app-01, skips Caddy |
| 2 | `*.<YOUR_PUBLIC_DOMAIN>` | `http://localhost:80` | Caddy on edge-01, carries every deployed app |
| 3 | (catch-all) | `http_status:404` | Anything unmatched |

## DNS

Both hostnames are proxied CNAMEs into the tunnel in the `<YOUR_PUBLIC_DOMAIN>` zone:

- `*.<YOUR_PUBLIC_DOMAIN>` CNAME `<YOUR_TUNNEL_ID>.cfargotunnel.com`, proxied
- `coolify-a1.<YOUR_PUBLIC_DOMAIN>` CNAME the same target, proxied

## Credentials

The connector authenticates with `/home/<YOUR_ADMIN_USERNAME>/.cloudflared/<YOUR_TUNNEL_ID>.json` on edge-01. I don't store that file or its contents in this repository.

## Access & firewall

Cloudflare Access protects `coolify-a1.<YOUR_PUBLIC_DOMAIN>`; see [Access applications](../applications.md). A UniFi policy limits edge-01 to app-01 on TCP 80 & 8000; see the UniFi section of the [Coolify Access Hardening record](../../Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

## Account zones

I hold four zones in this Cloudflare account: `<YOUR_BASE_DOMAIN>`, `<YOUR_PUBLIC_DOMAIN>`, `<YOUR_PERSONAL_DOMAIN_NAME>.com`, & `<YOUR_PERSONAL_DOMAIN_NAME>.me`. External service ingress currently uses `<YOUR_PUBLIC_DOMAIN>`.

## Related

- End-to-end design: [External Service Ingress](../../../../../Architecture/External-Service-Ingress.md)
