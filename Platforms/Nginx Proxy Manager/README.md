# Nginx Proxy Manager

**Created:** 2026-07-11  
**Last updated:** 2026-07-22

I run Nginx Proxy Manager on the `docker-network` LXC. It provides internal HTTPS for NetBird and 19 application interfaces while keeping the administrator UI on its existing IP and port.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Runtime healthy; 20 proxy hosts Online, automated renewal path, restart recovery, & bounded logging verified |
| Compute | Galaxy CT 107 `docker-network`, Debian 13, `192.168.85.2` |
| NPM release | 2.15.1 |
| Live path | `/opt/docker/nginx-proxy-manager` |
| Container | `nginx-proxy-manager` |
| Guest bindings | TCP 80, 81, and 443 |
| Docker network | External `proxy`, `172.31.85.0/24` |
| Fixed container address | `172.31.85.10` |
| Persistent data | Live `data/` and `letsencrypt/` bind mounts |
| Shared certificate | Let's Encrypt wildcard/apex certificate; expires `2026-10-08 23:49:46 UTC` |
| Shared TLS policy | Certificate assigned; Force SSL and HTTP/2 enabled; HSTS disabled |

The NPM health check passes and the administrative UI returns HTTP `200` at `http://192.168.85.2:81`. I don't assign a domain name to that administrator interface. The original NetBird host remains unchanged, and the 19 internal application hosts added on 2026-07-22 report Online. Every new host redirects HTTP to HTTPS, presents the wildcard certificate, & returns an application response. Public DNS returns NXDOMAIN for the new names.

## Records

- [Deployment record](Documentation/Deployment.md)
- [Operations runbook](Documentation/Runbook.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)
- [Internal proxy-host inventory](Configuration/internal-proxy-hosts.md)
- [Internal HTTPS service onboarding (2026-07-22)](Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [NetBird/NPM operational follow-ups and hardening descope (2026-07-12)](../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [NetBird platform](../Netbird/README.md)

## Layout

- `Documentation/`: deployment history, dated changes, operating procedure, troubleshooting, and remaining work
- `Configuration/`: reader-editable Compose reference, NetBird advanced routes, & the current internal proxy-host inventory

## Network Boundaries

- NPM holds fixed address `172.31.85.10`; NetBird trusts only `172.31.85.10/32` as its HTTP proxy.
- TCP 80, 81, & 443 bind on `192.168.85.2`; no WAN ingress points at the guest.
- UniFi resolves the 19 internal application names to `192.168.85.2` and permits NPM only to their approved backend web ports.
- NPM's `Public` access-list label means no NPM access list is assigned. The new names still have no public DNS record or Internet path.
