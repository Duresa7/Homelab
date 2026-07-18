# Galaxy Docker-Network LXC Deployment

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

**Implementation window:** 2026-07-10 through 2026-07-11  
**System:** Proxmox VE cluster `Galaxy`, UniFi Access-A (VLAN 85), and LXC 107 `docker-network`  
**Status:** Infrastructure and platform access complete; first-peer/VPN path, automated renewal path, and bounded logging subsequently verified

## Scope

Provision a dedicated Debian 13 LXC on `blue-server` for network-access services, establish hardened SSH and Docker runtime access, place the guest on Access-A, and restrict its Internet egress to the protocols required for package, image, certificate, and time synchronization operations. The LXC hosts NetBird and Nginx Proxy Manager; detailed platform configuration and remaining application work are owned by their records under `Platforms/`.

## Starting State

- CTID 107 was unused, and no dedicated `docker-network` guest existed.
- Access-A already existed as VLAN 85 with subnet `192.168.85.0/24`, gateway `192.168.85.1`, and reserved static range `.2` through `.5`.
- The existing UniFi `Allow Internal to REDACTED_PRIVATE_ORG_LABEL-Access` and `Allow VPN to REDACTED_PRIVATE_ORG_LABEL-Access` policies provided the intended inbound zone paths.
- There were no workload-specific REDACTED_PRIVATE_ORG_LABEL-Access-to-External egress rules and no internal DNS record for `REDACTED_CUSTOM_DOMAIN_016`.

## Completed Implementation

1. I created unprivileged LXC 107 `docker-network` on `blue-server` from Debian GNU/Linux 13 (trixie).
2. I assigned 2 vCPU, 4 GiB memory, 1 GiB swap, and a 32 GiB `local-lvm` root disk.
3. I enabled `nesting=1,keyctl=1`, guest firewall processing, automatic boot, and HA desired state `started`.
4. I connected `eth0` to VLAN 85 through `vmbr0` with static address `192.168.85.2/24`; both gateway and DNS use `192.168.85.1`.
5. I created the `REDACTED_USER_001` administrator, copied the three approved administrative public keys, granted NOPASSWD sudo, disabled root SSH, and disabled password and keyboard-interactive SSH authentication.
6. I added the LXC to SSH Manager as `docker_network` and verified key-based access.
7. I installed Docker Engine and Compose and deployed Nginx Proxy Manager 2.15.1 and NetBird 0.74.3 under `/opt/docker`.
8. I created the following order-sensitive UniFi policies with logging enabled and automatic respond-policy generation disabled:

   | Order | Policy | Source | Destination | Protocol / port | Result |
   |---:|---|---|---|---|---|
   | 10000 | `Allow docker-network Web Egress` | `192.168.85.2`, REDACTED_PRIVATE_ORG_LABEL-Access | External | TCP 80, 443 | Allow |
   | 10001 | `Allow docker-network NTP Egress` | `192.168.85.2`, REDACTED_PRIVATE_ORG_LABEL-Access | External | UDP 123 | Allow |
   | 10002 | `Block REDACTED_PRIVATE_ORG_LABEL-Access Other External Egress` | Any, REDACTED_PRIVATE_ORG_LABEL-Access | External | Any IPv4 | Block |

9. I added the UniFi local DNS A record `REDACTED_CUSTOM_DOMAIN_016` to `192.168.85.2` with TTL 300 seconds.
10. I issued and assigned the Cloudflare DNS-01 wildcard/apex certificate in Nginx Proxy Manager, enabled Force SSL and HTTP/2, verified the authenticated NetBird dashboard over HTTPS, and passed a controlled restart of both Compose projects.
11. I removed task-generated installer and temporary leftovers and restricted the NetBird secret configuration files and NPM database to owner-only mode 0600.

## Resulting LXC Configuration

| Setting | Value |
|---|---|
| CTID / hostname | `107` / `docker-network` |
| Node | `blue-server` |
| OS | Debian GNU/Linux 13 (trixie) |
| CPU / memory / swap | 2 vCPU / 4 GiB / 1 GiB |
| Root storage | `local-lvm:vm-107-disk-0`, 32 GiB |
| Container mode | Unprivileged; `nesting=1,keyctl=1` |
| Boot / HA | `onboot=1`; HA state `started` |
| Network | `eth0`, `vmbr0`, VLAN 85, firewall enabled |
| Addressing | `192.168.85.2/24`; gateway and DNS `192.168.85.1` |
| SSH | Public-key only as `REDACTED_USER_001`; root and password-based SSH disabled |
| Hosted workloads | Nginx Proxy Manager 2.15.1; NetBird 0.74.3 |

The HA resource is backed by node-local `local-lvm`. I accepted that this starts and monitors the guest but does not provide shared-storage failover to another node.

## Troubleshooting During the Change

- My first web-egress policy create request was rejected with `api.err.FirewallPolicyCreateRespondTrafficPolicyNotAllowed`. UniFi was attempting to create a respond-traffic companion that is not permitted for this zone direction. I corrected the request to set `create_allow_respond=false`; all three rules then passed preview, applied successfully, and appeared in the intended order.
- My hand-built UDP NTP probe returned no usable response, so I did not accept it as proof of UDP 123 egress. I installed `ntpsec-ntpdig` in the guest, and `ntpdig -4 -t 5 -j time.cloudflare.com` returned structured time data from a stratum-3 server with exit code 0.

## Verification

- The guest started successfully, reported Debian 13.1, and reached `192.168.85.1` with 0% packet loss.
- SSH Manager connected as `REDACTED_USER_001`; passwordless sudo succeeded, the SSH service was active, and all three expected public-key fingerprints were present.
- `ha-manager` reported `ct:107` on `blue-server` with state `started`.
- HTTP to `deb.debian.org` returned 200, and HTTPS to the Docker registry returned the expected unauthenticated 401 response, proving TCP 80/443 egress.
- `ntpdig` reached `time.cloudflare.com` and returned valid time data, proving UDP 123 egress.
- A direct TCP DNS attempt to `REDACTED_IPV4_001:53` timed out as expected under the final block rule.
- The UniFi resolver at `192.168.85.1` and a Windows client both returned `192.168.85.2` for `REDACTED_CUSTOM_DOMAIN_016`.
- Nginx Proxy Manager, the NetBird dashboard, and the NetBird server containers were running; direct NPM administration and the NetBird identity endpoint returned HTTP 200.
- The Let's Encrypt wildcard/apex certificate validated successfully, `https://REDACTED_CUSTOM_DOMAIN_016` returned HTTP 200, and the existing authenticated NetBird dashboard session loaded through NPM.
- Both Compose projects restarted successfully; readiness was reached on the second check, NPM returned healthy, `nginx -t` passed, and direct/HTTPS probes returned 200.

## Step Evidence

The screenshots below capture each step's verified end state in the Proxmox, NPM, UniFi, and NetBird interfaces.

### S01: live preflight

I confirmed CTID availability, node capacity, VLAN readiness, and the starting controller state before creating anything.

### S02: LXC creation

The created guest showed the intended resource, storage, and VLAN configuration, and the gateway was reachable.

<details>
<summary>Step S02 screenshot: validated docker-network LXC</summary>

![Validated LXC configuration](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S02-Docker-Network-LXC-Created-2026-07-10.jpg)

</details>

### S03: SSH hardening and HA

Key-only access, SSH hardening, administrator sudo, and the HA state all passed.

<details>
<summary>Step S03 screenshot: SSH and HA ready</summary>

![SSH hardening and HA state](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S03-Docker-Network-SSH-HA-Ready-2026-07-10.jpg)

</details>

### S04: Docker runtime

Docker, Compose, and the deployment path were ready.

### S05: Nginx Proxy Manager deployment

NPM came up healthy on first run and I initialized the protected administrator.

<details>
<summary>Step S05 screenshot: NPM healthy first run</summary>

![NPM healthy first-run state](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05-NPM-First-Run-Healthy-2026-07-10.jpg)

</details>

<details>
<summary>Step S05 screenshot: NPM administrator initialized</summary>

![NPM initialized administrator](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05-NPM-Admin-Initialized-2026-07-11.jpg)

</details>

### S05A: UniFi egress policies

The final ordered Access-A egress policy set was in place and behaved as intended for allowed and blocked traffic.

<details>
<summary>Step S05A screenshot: Access-A egress policies after change</summary>

![Access-A egress policy set](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg)

</details>

### S06: internal DNS

The internal DNS A record, its TTL, and the resolver result all matched the intended values.

<details>
<summary>Step S06 screenshot: UniFi internal DNS record</summary>

![UniFi internal DNS record](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

</details>

### S07: TLS and proxy

Certificate issuance and assignment, Force SSL, HTTP/2, the advanced routes, and HTTPS validation all passed.

<details>
<summary>Step S07 screenshot: wildcard certificate issued</summary>

![Wildcard certificate issued](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S07A-NPM-Wildcard-Certificate-Issued-2026-07-11.jpg)

</details>

<details>
<summary>Step S07 screenshot: NetBird proxy online</summary>

![NetBird proxy online in NPM](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S07-NPM-NetBird-Proxy-Online-2026-07-11.jpg)

</details>

### S08: NetBird control plane

The NetBird deployment and version checks passed, HTTPS login worked, and the authenticated dashboard loaded.

<details>
<summary>Step S08 screenshot: authenticated NetBird dashboard</summary>

![Authenticated NetBird dashboard](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S08-NetBird-Authenticated-Dashboard-2026-07-11.jpg)

</details>

### S09: restart validation

The controlled Compose restart passed: containers reached readiness, Nginx validated, HTTPS returned 200, and the authenticated UI was restored.

<details>
<summary>Step S09 screenshot: NetBird healthy after restart</summary>

![NetBird healthy after restart](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S09-NetBird-Healthy-After-Restart-2026-07-11.jpg)

</details>

### S10: cleanup and permissions

I removed the task-generated leftovers and confirmed owner-only permissions on the secret files.

## Rollback

1. Stop the NetBird and Nginx Proxy Manager Compose projects before removing the guest.
2. Remove UniFi policies `REDACTED_UNIFI_POLICY_ID_001`, `REDACTED_UNIFI_POLICY_ID_002`, and `REDACTED_UNIFI_POLICY_ID_003` in reverse order if the Access-A egress policy set must be reverted.
3. Remove local DNS record `REDACTED_UNIFI_DNS_RECORD_ID_001` if the hostname is no longer served by this LXC.
4. Remove `ct:107` from HA before stopping or destroying the guest.
5. Remove the `docker_network` SSH Manager entry if LXC 107 is retired.

Destruction of the LXC and its `local-lvm` disk is intentionally not automated and requires a separately approved destructive change.

## Follow-on Status

I validated first-peer enrollment and the routed VPN path on 2026-07-12, then verified the non-interactive ACME renewal path and bounded logging. I intentionally descoped the controlled guest reboot and the remaining hardening items I declined. See the platform [operational follow-ups/descope record](../../../../../Platforms/Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md). No infrastructure follow-up remains tracked from this change.
