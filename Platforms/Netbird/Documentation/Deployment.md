# NetBird Deployment

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

**Implementation started:** 2026-07-10  
**Status:** Operational; HTTPS publication, authenticated administrator access, controlled Compose restart, & the first-peer plus routed VPN path into Access-A all verified

## Scope

I deployed NetBird and Nginx Proxy Manager on Debian 13 LXC 107 `docker-network`. The service runs on VLAN 85 in `/opt/docker/<service>` projects and resolves through an internal UniFi DNS record. Nginx Proxy Manager routes the dashboard, HTTP API, WebSocket, & gRPC paths and terminates a Let's Encrypt certificate issued through Cloudflare DNS-01.

The infrastructure-owned [Galaxy Docker-Network LXC walkthrough](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md) holds the 11-step sequence for the guest, SSH, Docker, UniFi, DNS, TLS, proxy, & restart evidence. This record follows the same deployment from the NetBird platform boundary.

## Starting State

- VLAN 85 already existed and was available to the Proxmox environment.
- No dedicated NetBird/Nginx Proxy Manager LXC or NetBird platform deployment existed.
- I had settled on the name, address, and guest ID: `docker-network`, `192.168.85.2/24`, and CT 107.
- `<YOUR_NETBIRD_DOMAIN>` didn't yet have the required internal DNS record, certificate, or reverse-proxy host.

## Platform Deployment Summary

### Compute and access foundation

NetBird depends on CT 107 `docker-network` on `blue-server`, VLAN 85 address `192.168.85.2/24`, key-only administrative SSH, and HA desired state `started`. I keep the resource choices, hardening steps, troubleshooting, and S01 through S03 evidence in the [Galaxy infrastructure walkthrough](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md) instead of duplicating them here.

### Docker runtime

The platform depends on Docker Engine 29.6.1, Docker Compose 5.3.1, and:

- `/opt/docker/netbird`
- `/opt/docker/nginx-proxy-manager`
- external Docker network `proxy`, subnet `172.31.85.0/24`

The installation and S04 terminal evidence remain in the [Galaxy infrastructure walkthrough](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md#step-4-install-and-verify-docker).

### Nginx Proxy Manager dependency

I deployed Nginx Proxy Manager 2.15.1; Docker reported status `healthy`. It binds the guest's TCP ports 80, 81, & 443 and holds fixed address `172.31.85.10` on `proxy`. The first-run administrator setup is complete. The NetBird proxy host is saved and Online with its routes, Let's Encrypt certificate, Force SSL, & HTTP/2 applied.

### NetBird control plane

I downloaded the official v0.74.3 `getting-started.sh` installer and verified it with SHA-256:

```text
371ac85e4f56dc8e6d3abf14601f35d0d061b3712f2e60ce76f2e6832f3a1461
```

I selected the Nginx Proxy Manager integration option with localhost-only direct service bindings and the existing external `proxy` network. The resulting deployment contains:

- `netbird-dashboard`: dashboard on `127.0.0.1:8080`
- `netbird-server`: combined management, signal, relay, STUN, and embedded identity-provider service on `127.0.0.1:8081` and `3478/udp`

I corrected the generated proxy trust value from the installer's built-in Traefik address `172.30.0.10/32` to Nginx Proxy Manager's fixed address `172.31.85.10/32`. Both containers were healthy after recreation, Nginx Proxy Manager could resolve and reach them over `proxy`, and the dashboard and embedded identity-provider probes returned HTTP `200`.

After I verified the generated runtime, I removed the downloaded `getting-started.sh` installer from the live project. The deployed Compose and configuration files remain in `/opt/docker/netbird`; the one-time installer isn't part of the operating service.

### UniFi dependencies

Three ordered `<YOUR_ORG_NAME>`-Access-to-External policies now govern CT 107 egress:

1. Allow `docker-network` TCP 80 and 443.
2. Allow `docker-network` UDP 123.
3. Block all other `<YOUR_ORG_NAME>`-Access IPv4 traffic to External.

I verified HTTP, HTTPS, and NTP. TCP DNS to `<YOUR_EXTERNAL_DNS_IP>:53` timed out as expected, while DNS through gateway `192.168.85.1` remained available.

UniFi internal DNS now has an enabled A record with TTL 300:

```text
<YOUR_NETBIRD_DOMAIN> -> 192.168.85.2
```

I verified resolution from both CT 107 and my Windows workstation.

### Nginx Proxy Manager routing

The proxy host `<YOUR_NETBIRD_DOMAIN>` is saved and Online with default upstream `http://netbird-dashboard:80`, Block Common Exploits enabled, and WebSocket Support enabled. I applied the 1,296-character advanced configuration to route NetBird API, OAuth2, WebSocket, signal, management, and gRPC requests to `netbird-server:80`.

Nginx configuration validation succeeded, and a request through NPM with Host header `<YOUR_NETBIRD_DOMAIN>` returned HTTP `200`. Nginx Proxy Manager issued a Let's Encrypt certificate for `*.<YOUR_BASE_DOMAIN>` and `<YOUR_BASE_DOMAIN>` through Cloudflare DNS-01. I assigned it to the NetBird host with Force SSL and HTTP/2 enabled. The intended HTTPS URL returned `200`, and the authenticated administrator dashboard loaded.

### Controlled restart validation

I restarted the Nginx Proxy Manager & NetBird Compose projects in sequence. Nginx Proxy Manager returned to `healthy`, both NetBird containers returned to the running state, `nginx -t` passed, & `https://<YOUR_NETBIRD_DOMAIN>` returned HTTP `200`. The restart reused the saved proxy host, certificate, and NetBird datastore; I didn't recreate configuration.

## Resulting Configuration

| Setting | Value |
|---|---|
| Guest | CT 107 `docker-network`, Debian 13 |
| Guest network | `192.168.85.2/24`, gateway/DNS `192.168.85.1`, VLAN 85 |
| Docker/Compose | 29.6.1 / 5.3.1 |
| NetBird | v0.74.4 at `/opt/docker/netbird` (deployed v0.74.3; updated 2026-07-12) |
| NetBird containers | `netbird-dashboard`, `netbird-server` |
| Direct ports | `127.0.0.1:8080`, `127.0.0.1:8081`, `3478/udp` |
| Shared proxy network | `proxy`, `172.31.85.0/24` |
| Trusted HTTP proxy | `172.31.85.10/32` |
| Internal name | `<YOUR_NETBIRD_DOMAIN>` -> `192.168.85.2` |
| HTTPS certificate | Let's Encrypt wildcard/apex certificate issued through Cloudflare DNS-01 |
| Certificate renewal | Non-interactive DNS-01 path verified by staging dry-run; NPM checks hourly and renews within 30 days of expiry |
| Container logging | `json-file`, `max-size=10m`, `max-file=3` on both NetBird containers |
| NPM proxy host | Online; advanced routes, Force SSL, and HTTP/2 applied |
| NetBird administrator | Existing administrator authenticated through `https://<YOUR_NETBIRD_DOMAIN>` |

## Verification Performed

- Docker Engine returned 29.6.1 & Docker Compose returned 5.3.1.
- Both NetBird containers remained up after the trusted-proxy correction.
- Direct dashboard and embedded identity-provider probes returned HTTP `200`.
- Nginx Proxy Manager resolved both container names and received HTTP `200` from the dashboard and embedded identity provider over `proxy`.
- The saved proxy host reports Online, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`.
- The Let's Encrypt certificate covers the wildcard and apex names and is assigned to the NetBird proxy host.
- I inspected the non-interactive Cloudflare DNS-01 renewal configuration and NPM's hourly renewal timer; a Let's Encrypt staging dry-run succeeded for lineage `npm-1` on 2026-07-12.
- Force SSL & HTTP/2 are enabled, & `https://<YOUR_NETBIRD_DOMAIN>` returns HTTP `200` through internal UniFi DNS.
- I observed an authenticated administrator dashboard at `https://<YOUR_NETBIRD_DOMAIN>`.
- Controlled restarts returned Nginx Proxy Manager to `healthy`, both NetBird containers to the running state, and the HTTPS endpoint to `200`.
- Docker inspection confirmed bounded `json-file` logging with `max-size=10m` and `max-file=3` on `netbird-server` and `netbird-dashboard`.
- Gateway DNS returned `192.168.85.2` for `<YOUR_NETBIRD_DOMAIN>`.
- Approved web and NTP egress succeeded; a non-approved external TCP DNS test was blocked.

These checks prove the direct control plane, its network dependencies, HTTPS publication, administrator authentication, Compose-level restart persistence, automated certificate-renewal path, and bounded container logging. I validated first-peer enrollment and the routed VPN client path into Access-A on 2026-07-12; see [NetBird First Peer and Routed VPN Path - 2026-07-12](Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md). Renewal and logging follow-ups are recorded in [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Recovery and Rollback

- Stop or restart NetBird from `/opt/docker/netbird` with Docker Compose; do not remove the named volume during routine recovery.
- Preserve the live Compose environment, `config.yaml`, `dashboard.env`, and `netbird_data` volume together before an update or migration.
- If a future image update fails, restore the recorded working image digest or version and recreate the two containers without deleting `netbird_data`.
- Nginx Proxy Manager is a separate Compose project and can be stopped or repaired without deleting NetBird data.
- UniFi DNS and firewall rollback belongs with the UniFi records. Remove only the record or rules created for this deployment and preserve their documented order.
- Removing CT 107 is a final rollback only after the application state is backed up and the service is intentionally retired.

## Closed NetBird Work

No further platform hardening is tracked. I intentionally descoped the remaining manual or declined items on 2026-07-12; see [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md). Recovery and rollback guidance above remains reference material rather than backlog.
