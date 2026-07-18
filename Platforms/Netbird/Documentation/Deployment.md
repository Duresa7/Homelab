# NetBird Deployment

**Created:** 2026-07-11  
**Last updated:** 2026-07-17

**Implementation started:** 2026-07-10  
**Status:** Operational — HTTPS publication, authenticated administrator access, controlled Compose restart, and the first-peer + routed VPN path into Access-A all verified

## Scope

Deploy NetBird and its Nginx Proxy Manager dependency on a new Debian 13 LXC named `docker-network`. The service is isolated on VLAN 85, uses the established `/opt/docker/<service>` Compose layout, and is reachable through an internal UniFi DNS record. Nginx Proxy Manager routes the dashboard, HTTP API, WebSocket, and gRPC paths and terminates a Let's Encrypt certificate issued through Cloudflare DNS-01.

The combined implementation evidence is retained in the [deployment evidence index](../Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Evidence-Index.md).

## Starting State

- VLAN 85 already existed and was available to the Proxmox environment.
- No dedicated NetBird/Nginx Proxy Manager LXC or NetBird platform deployment existed.
- The approved name, address, and guest ID were `docker-network`, `192.168.85.2/24`, and CT 107.
- The existing `docker-blue` LXC provided the three approved administrative public keys used for the new guest.
- `REDACTED_CUSTOM_DOMAIN_016` did not yet have the required internal DNS record, certificate, or reverse-proxy host.

## Implementation

### 1. Compute and access foundation

CT 107 `docker-network` was created on `blue-server` with Debian 13, 2 vCPU, 4 GiB RAM, 1 GiB swap, and a 32 GiB `local-lvm` root disk. It is an unprivileged LXC with nesting and keyctl enabled, VLAN 85 on `eth0`, address `192.168.85.2/24`, gateway and DNS `192.168.85.1`, `onboot` enabled, and the Proxmox guest firewall enabled.

The `REDACTED_USER_001` account has the three approved SSH keys and NOPASSWD sudo. SSH permits public-key authentication while rejecting root, password, and keyboard-interactive login. The guest was added to HA in the started state. The use of node-local `local-lvm` was explicitly accepted; the HA resource therefore does not provide storage-backed cross-node failover.

The `pvestatd` service on `blue-server` was found failed during the work. It was restarted and verified active before the deployment continued. See the [troubleshooting log](Troubleshooting-Log.md#1-pvestatd-was-failed-on-blue-server).

### 2. Docker runtime

Docker Engine 29.6.1 and Docker Compose 5.3.1 were installed. The deployment uses:

- `/opt/docker/netbird`
- `/opt/docker/nginx-proxy-manager`
- external Docker network `proxy`, subnet `172.31.85.0/24`

### 3. Nginx Proxy Manager dependency

Nginx Proxy Manager 2.15.1 was deployed and verified healthy. It binds the guest's TCP ports 80, 81, and 443 and holds fixed address `172.31.85.10` on `proxy`. The first-run administrator setup is complete. The NetBird proxy host is saved and Online with its advanced routes, Let's Encrypt certificate, Force SSL, and HTTP/2 applied.

### 4. NetBird control plane

The official v0.74.3 `getting-started.sh` installer was downloaded and verified with SHA-256:

```text
371ac85e4f56dc8e6d3abf14601f35d0d061b3712f2e60ce76f2e6832f3a1461
```

The Nginx Proxy Manager integration option was selected with localhost-only direct service bindings and the existing external `proxy` network. The resulting deployment contains:

- `netbird-dashboard` — dashboard on `127.0.0.1:8080`
- `netbird-server` — combined management, signal, relay, STUN, and embedded identity-provider service on `127.0.0.1:8081` and `3478/udp`

The generated proxy trust value was corrected from the installer's built-in Traefik address `172.30.0.10/32` to Nginx Proxy Manager's fixed address `172.31.85.10/32`. Both containers were healthy after recreation, Nginx Proxy Manager could resolve and reach them over `proxy`, and the dashboard and embedded identity-provider probes returned HTTP `200`.

The live `config.yaml`, `dashboard.env`, generated datastore, and secret values remain only on the host and are excluded from the repository.

After the generated runtime was verified, the downloaded `getting-started.sh` installer was removed from the live project. The deployed Compose and configuration files remain in `/opt/docker/netbird`; the one-time installer is not part of the operating service.

### 5. UniFi dependencies

Three ordered REDACTED_PRIVATE_ORG_LABEL-Access-to-External policies now govern CT 107 egress:

1. Allow `docker-network` TCP 80 and 443.
2. Allow `docker-network` UDP 123.
3. Block all other REDACTED_PRIVATE_ORG_LABEL-Access IPv4 traffic to External.

HTTP, HTTPS, and NTP were verified. TCP DNS to `REDACTED_IPV4_001:53` timed out as expected, while DNS through gateway `192.168.85.1` remained available.

UniFi internal DNS now has an enabled A record with TTL 300:

```text
REDACTED_CUSTOM_DOMAIN_016 -> 192.168.85.2
```

Resolution was verified from both CT 107 and the Windows operator workstation.

### 6. Nginx Proxy Manager routing

The proxy host `REDACTED_CUSTOM_DOMAIN_016` is saved and Online with default upstream `http://netbird-dashboard:80`, Block Common Exploits enabled, and WebSocket Support enabled. The 1,296-character advanced configuration was applied to route NetBird API, OAuth2, WebSocket, signal, management, and gRPC requests to `netbird-server:80`.

Nginx configuration validation succeeded, and an HTTP request through NPM with Host header `REDACTED_CUSTOM_DOMAIN_016` returned the NetBird dashboard with HTTP `200`. A zone-scoped Cloudflare DNS Write token named `REDACTED_1PASSWORD_ITEM_TITLE_002` was stored in the 1Password REDACTED_1PASSWORD_VAULT_002 vault without retaining its value in Git or evidence. Nginx Proxy Manager used it to issue a Let's Encrypt certificate for `*.REDACTED_CUSTOM_DOMAIN_001` and `REDACTED_CUSTOM_DOMAIN_001`. The certificate was assigned to the NetBird host with Force SSL and HTTP/2 enabled. The intended HTTPS URL returned `200`, and Chrome displayed an authenticated NetBird administrator dashboard.

### 7. Controlled restart validation

The Nginx Proxy Manager and NetBird Compose projects were restarted in a controlled sequence. Nginx Proxy Manager returned to `healthy`, both NetBird containers returned to the running state, `nginx -t` remained successful, and `https://REDACTED_CUSTOM_DOMAIN_016` continued to return HTTP `200`. This validates Compose-level restart persistence.

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
| Internal name | `REDACTED_CUSTOM_DOMAIN_016` -> `192.168.85.2` |
| HTTPS certificate | Let's Encrypt wildcard/apex certificate issued through Cloudflare DNS-01 |
| Certificate renewal | Non-interactive DNS-01 path verified by staging dry-run; NPM checks hourly and renews within 30 days of expiry |
| Container logging | `json-file`, `max-size=10m`, `max-file=3` on both NetBird containers |
| Cloudflare credential | Zone-scoped `REDACTED_1PASSWORD_ITEM_TITLE_002` token stored in 1Password REDACTED_1PASSWORD_VAULT_002; value excluded from Git and evidence |
| NPM proxy host | Online; advanced routes, Force SSL, and HTTP/2 applied |
| NetBird administrator | Existing administrator authenticated through the intended HTTPS URL |

## Verification Performed

- Docker and Compose versions returned the expected installed versions.
- Both NetBird containers remained up after the trusted-proxy correction.
- Direct dashboard and embedded identity-provider probes returned HTTP `200`.
- Nginx Proxy Manager resolved both container names and received HTTP `200` from the dashboard and embedded identity provider over `proxy`.
- The saved proxy host reports Online, `nginx -t` succeeds, and a Host-header request through NPM returns the NetBird dashboard with HTTP `200`.
- The Let's Encrypt certificate covers the wildcard and apex names and is assigned to the NetBird proxy host.
- The non-interactive Cloudflare DNS-01 renewal configuration and NPM's hourly renewal timer were inspected; a Let's Encrypt staging dry-run succeeded for lineage `npm-1` on 2026-07-12.
- Force SSL and HTTP/2 are enabled, and the intended HTTPS URL returns HTTP `200` through internal UniFi DNS.
- An authenticated administrator dashboard was observed through the intended HTTPS URL.
- Controlled restarts returned Nginx Proxy Manager to `healthy`, both NetBird containers to the running state, and the HTTPS endpoint to `200`.
- Docker inspection confirmed bounded `json-file` logging with `max-size=10m` and `max-file=3` on `netbird-server` and `netbird-dashboard`.
- Gateway DNS returned the intended internal A record.
- Approved web and NTP egress succeeded; a non-approved external TCP DNS test was blocked.

These checks prove the direct control plane, its network dependencies, HTTPS publication, administrator authentication, Compose-level restart persistence, automated certificate-renewal path, and bounded container logging. First-peer enrollment and the routed VPN client path into Access-A were subsequently validated on 2026-07-12 — see [NetBird First Peer and Routed VPN Path - 2026-07-12](Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md). Renewal and logging follow-ups are recorded in [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Recovery and Rollback

- Stop or restart NetBird from `/opt/docker/netbird` with Docker Compose; do not remove the named volume during routine recovery.
- Preserve the live Compose environment, `config.yaml`, `dashboard.env`, and `netbird_data` volume together. They contain service identity and secrets and must be handled as protected backup material.
- If a future image update fails, restore the recorded working image digest or version and recreate the two containers without deleting `netbird_data`.
- Nginx Proxy Manager is a separate Compose project and can be stopped or repaired without deleting NetBird data.
- UniFi DNS and firewall rollback belongs with the UniFi owner. Remove only the record or rules created for this deployment and preserve their documented order.
- Removing CT 107 is a final rollback only after protected application data is backed up and the service is intentionally retired.

## Operational Status

No further platform hardening is tracked. The operator intentionally descoped the remaining human-dependent or declined items on 2026-07-12; see [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md). Recovery and rollback guidance above remains reference material rather than backlog.
