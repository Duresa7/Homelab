# Cloudflare Tunnel: edge-01

**Created:** 2026-07-24  
**Last updated:** 2026-10-02

I run one Cloudflare Tunnel, `edge-01`, and manage its configuration from the Cloudflare Zero Trust dashboard rather than a local file. The connector runs as cloudflared on the edge-01 host. This tunnel is the only inbound path from the Internet to my services; the router forwards no ports.

## Identity

| Field | Value |
|---|---|
| Name | edge-01 |
| Tunnel ID | `<REDACTED_TUNNEL_ID>` |
| Created | 2026-02-14 |
| Configuration source | Remote (dashboard-managed) |
| Connector host | edge-01, `192.168.30.10`, VLAN 30, Debian 13 |
| cloudflared version | 2026.9.3 binary installed during the [2026-10-02 guest package updates](../../../../Operations/Maintenance/Guest%20Package%20Updates%20-%202026-10-02.md); local metrics still report the running process on 2026.8.3 with four connections. Restart is deferred to the Edge 01 reboot. I last restarted the connector on 2026-09-06 at 2:21 PM EDT, moving the running process from 2026.7.3 to 2026.8.3 |
| Connections | 4, healthy, read through the Cloudflare API on 2026-09-06 after the restart: four QUIC connections to Ashburn edge locations, all reporting 2026.8.3, opened at 14:21 EDT |
| Public DNS zone | alphsec.com |

## Ingress rules

Cloudflare evaluates these in order. I edit them in the dashboard. The local `/etc/cloudflared/config.yml` on edge-01 holds only the tunnel ID, the credentials-file path, and a placeholder `http_status:404` ingress that the dashboard configuration overrides, so reading that file alone won't show the live routing.

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

## Access and firewall

Cloudflare Access protects `coolify-a1.alphsec.com`; see [Access applications](applications.md). A UniFi policy limits edge-01 to app-01 on TCP 80 and 8000; see the UniFi section of the [Coolify Access Hardening record](../Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

## Account zones

I hold four zones in this Cloudflare account: `alphasecunited.com`, `alphsec.com`, `duresakadi.com`, and `duresakadi.me`. External service ingress currently uses `alphsec.com`.

## Related

- End-to-end design: [External Service Ingress](../../../../Architecture/External-Service-Ingress.md)

## Uptime monitoring

On 2026-09-15 I added `edge-uptime.timer`, which runs `/usr/local/lib/edge-uptime.py` every minute. I read the connector metric on loopback port 20241 and probe the local Caddy HTTP listener and Coolify origin on `192.168.80.10:8000`. The collector writes only the connection count, two origin results, and a timestamp to `/var/lib/prometheus/node-exporter/edge-uptime.prom`. The existing node_exporter scrape carries these into Prometheus without another listener or firewall rule. I verified four connections, both origins responding, and the timer active. The private [Uptime dashboard and measurement limits](../../../../Platforms/Prometheus/Documentation/Change%20Records/Uptime%20Dashboard%20-%202026-09-15.md) cover the display.
