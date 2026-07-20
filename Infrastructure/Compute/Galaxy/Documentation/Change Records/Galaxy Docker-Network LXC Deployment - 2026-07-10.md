# Galaxy Docker-Network LXC Deployment

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

**Implementation window:** 2026-07-10 through 2026-07-11  
**System:** Proxmox VE cluster `Galaxy`, UniFi Access-A (VLAN 85), and LXC 107 `docker-network`  
**Status:** Infrastructure and platform access complete; first-peer/VPN path, automated renewal path, and bounded logging subsequently verified

## Scope

Provision a dedicated Debian 13 LXC on `blue-server` for network-access services, establish hardened SSH and Docker runtime access, place the guest on Access-A, and restrict its Internet egress to the protocols required for package, image, certificate, and time synchronization operations. The LXC hosts NetBird and Nginx Proxy Manager; detailed platform configuration and remaining application work are owned by their records under `Platforms/`.

## Starting State

- CTID 107 was unused, and no dedicated `docker-network` guest existed.
- Access-A already existed as VLAN 85 with subnet `192.168.85.0/24`, gateway `192.168.85.1`, and reserved static range `.2` through `.5`.
- The existing UniFi `Allow Internal to <YOUR_ORG_NAME>-Access` and `Allow VPN to <YOUR_ORG_NAME>-Access` policies provided the intended inbound zone paths.
- There were no workload-specific `<YOUR_ORG_NAME>`-Access-to-External egress rules and no internal DNS record for `<YOUR_NETBIRD_DOMAIN>`.

## Completed Implementation

1. I created unprivileged LXC 107 `docker-network` on `blue-server` from Debian GNU/Linux 13 (trixie).
2. I assigned 2 vCPU, 4 GiB memory, 1 GiB swap, and a 32 GiB `local-lvm` root disk.
3. I enabled `nesting=1,keyctl=1`, guest firewall processing, automatic boot, and HA desired state `started`.
4. I connected `eth0` to VLAN 85 through `vmbr0` with static address `192.168.85.2/24`; both gateway and DNS use `192.168.85.1`.
5. I created the `<YOUR_ADMIN_USERNAME>` administrator, copied the three approved administrative public keys, granted NOPASSWD sudo, disabled root SSH, and disabled password and keyboard-interactive SSH authentication.
6. I added the LXC to SSH Manager as `docker_network` and verified key-based access.
7. I installed Docker Engine and Compose and deployed Nginx Proxy Manager 2.15.1 and NetBird 0.74.3 under `/opt/docker`.
8. I created the following order-sensitive UniFi policies with logging enabled and automatic respond-policy generation disabled:

   | Order | Policy | Source | Destination | Protocol / port | Result |
   |---:|---|---|---|---|---|
   | 10000 | `Allow docker-network Web Egress` | `192.168.85.2`, `<YOUR_ORG_NAME>`-Access | External | TCP 80, 443 | Allow |
   | 10001 | `Allow docker-network NTP Egress` | `192.168.85.2`, `<YOUR_ORG_NAME>`-Access | External | UDP 123 | Allow |
   | 10002 | `Block <YOUR_ORG_NAME>-Access Other External Egress` | Any, `<YOUR_ORG_NAME>`-Access | External | Any IPv4 | Block |

9. I added the UniFi local DNS A record `<YOUR_NETBIRD_DOMAIN>` to `192.168.85.2` with TTL 300 seconds.
10. I issued and assigned the Cloudflare DNS-01 wildcard/apex certificate in Nginx Proxy Manager, enabled Force SSL and HTTP/2, verified the authenticated NetBird dashboard over HTTPS, and passed a controlled restart of both Compose projects.
11. I removed the installer and temporary files left over from my deployment steps and restricted the NetBird secret configuration files and NPM database to owner-only mode 0600.

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
| SSH | Public-key only as `<YOUR_ADMIN_USERNAME>`; root and password-based SSH disabled |
| Hosted workloads | Nginx Proxy Manager 2.15.1; NetBird 0.74.3 |

The HA resource is backed by node-local `local-lvm`. I accepted that this starts and monitors the guest but doesn't provide shared-storage failover to another node.

## Troubleshooting During the Change

- My first web-egress policy create request was rejected with `api.err.FirewallPolicyCreateRespondTrafficPolicyNotAllowed`. UniFi attempted to create a respond-traffic companion that isn't permitted for this zone direction. I set `create_allow_respond=false`; all three rules then passed preview & appeared in the requested order.
- My hand-built UDP NTP probe returned no usable response, so I didn't accept it as proof of UDP 123 egress. I installed `ntpsec-ntpdig` in the guest, and `ntpdig -4 -t 5 -j time.cloudflare.com` returned structured time data from a stratum-3 server with exit code 0.

## Verification

- The guest started, reported Debian 13.1, & reached `192.168.85.1` with 0% packet loss.
- SSH Manager connected as `<YOUR_ADMIN_USERNAME>`; passwordless sudo returned exit code 0, the SSH service was active, & all three approved public-key fingerprints were present.
- `ha-manager` reported `ct:107` on `blue-server` with state `started`.
- HTTP to `deb.debian.org` returned 200, and HTTPS to the Docker registry returned the expected unauthenticated 401 response, proving TCP 80/443 egress.
- `ntpdig` reached `time.cloudflare.com` and returned valid time data, proving UDP 123 egress.
- A direct TCP DNS attempt to `<YOUR_EXTERNAL_DNS_IP>:53` timed out as expected under the final block rule.
- The UniFi resolver at `192.168.85.1` and a Windows client both returned `192.168.85.2` for `<YOUR_NETBIRD_DOMAIN>`.
- Nginx Proxy Manager, the NetBird dashboard, & the NetBird server containers were running; direct NPM administration and the NetBird identity endpoint returned HTTP 200.
- The Let's Encrypt wildcard/apex certificate passed validation, `https://<YOUR_NETBIRD_DOMAIN>` returned HTTP 200, & the existing authenticated NetBird dashboard session loaded through NPM.
- Both Compose projects restarted; readiness passed on the second check, NPM returned `healthy`, `nginx -t` passed, & direct/HTTPS probes returned 200.

## Walkthrough

### Step 1: Check the target node and guest ID

**Action:** I checked the `blue-server` guest list for CTID 107, reviewed its CPU, memory, & storage use, checked VLAN 85 and the UniFi controller, & inspected `pvestatd`. I found `pvestatd` failed, restarted it, & verified it active before creating the guest.

**Observed result:** CTID 107 didn't appear in the guest list. The node summary showed 1.46% use across 4 CPUs, 1.74 GiB of 11.57 GiB RAM in use, 4.53 GiB of 67.73 GiB local disk in use, and 0 B of 8 GiB swap in use. These values left more than the planned 4 GiB RAM allocation available.

**Verification:** The Proxmox node summary displayed the guest inventory and the measured resources listed above, and `pvestatd` returned active after the restart. The exact VLAN 85 and controller preflight output remains in the local S01 transcript quarantine because it wasn't cleared for the public tree.

**Evidence:**

![Proxmox web UI showing the blue-server node summary during the preflight check, with the node's guest list, uptime, and resource usage visible](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S01-Proxmox-Blue-Server-Preflight-2026-07-10.jpg)

### Step 2: Create the docker-network LXC

**Action:** I created unprivileged CT 107 `docker-network` from Debian 13 with 2 vCPU, 4 GiB memory, 1 GiB swap, a 32 GiB `local-lvm` disk, `nesting=1,keyctl=1`, automatic boot, guest firewall processing, and `eth0` on VLAN 85 at `192.168.85.2/24`.

**Observed result:** Proxmox created & started CT 107 with 2 vCPU, 4 GiB memory, 1 GiB swap, a 32 GiB disk, unprivileged mode, & `eth0` on VLAN 85 at `192.168.85.2/24`.

**Verification:** The guest reached gateway `192.168.85.1` with 0% packet loss.

**Evidence:**

![Validated LXC configuration](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S02-Docker-Network-LXC-Created-2026-07-10.jpg)

### Step 3: Harden SSH and add the guest to HA

**Action:** I created the `<YOUR_ADMIN_USERNAME>` administrator, installed the three approved public keys, granted NOPASSWD sudo, disabled root & password-based SSH, added the guest to SSH Manager as `docker_network`, & set its HA desired state to `started`.

**Observed result:** Key-only SSH and passwordless sudo worked, while root, password, and keyboard-interactive authentication were disabled. Proxmox showed CT 107 running as an unprivileged container on `blue-server`, with HA desired state `started`.

**Verification:** SSH Manager connected with an approved key, all three fingerprints were present, & `ha-manager` reported `ct:107` started on `blue-server`. The SSH checks are retained only in the local S03 transcript quarantine. The public screenshot verifies the running container, unprivileged setting, assigned resources, address, node, & HA state.

**Evidence:**

![Proxmox summary showing CT 107 running as an unprivileged container on blue-server with HA state started](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S03-Docker-Network-SSH-HA-Ready-2026-07-10.jpg)

### Step 4: Install and verify Docker

**Action:** I installed Docker Engine & Docker Compose, created `/opt/docker/netbird` and `/opt/docker/nginx-proxy-manager`, & created external network `proxy` with subnet `172.31.85.0/24`.

**Observed result:** Docker Engine 29.6.1 & Docker Compose 5.3.1 returned their versions, and the `proxy` network existed at `172.31.85.0/24`.

**Verification:** I ran the public-safe verification commands retained in the terminal capture:

```sh
set -o pipefail
printf 'timestamp='; date --iso-8601=seconds
id
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}'
docker compose version
printf 'docker_service='; systemctl is-active docker
docker info --format 'driver={{.Driver}} cgroup={{.CgroupDriver}}'
docker network inspect -f 'name={{.Name}} subnet={{(index .IPAM.Config 0).Subnet}} gateway={{(index .IPAM.Config 0).Gateway}}' proxy
find /opt/docker -maxdepth 1 -mindepth 1 -type d -printf '%p %u:%g %m\n'
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

The capture showed the client & server versions, Compose version, active service, network subnet, directory ownership, & exit code 0. The installation request and complete raw output remain in the local-only scrub quarantine.

**Evidence:**

![Terminal capture showing Docker Engine 29.6.1 client and server, Docker Compose v5.3.1, the proxy network at 172.31.85.0/24, and exit code 0](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S04-Docker-Runtime-Current-Validation-2026-07-11.jpg)

### Step 5: Deploy Nginx Proxy Manager

**Action:** I deployed Nginx Proxy Manager 2.15.1 with TCP 80, 81, and 443 published and fixed address `172.31.85.10` on the `proxy` network, then initialized its administrator account.

**Observed result:** NPM returned its first-run page over HTTP 200 & accepted the protected administrator setup.

**Verification:** The administration UI returned HTTP 200 before and after initialization.

**Evidence:**

![NPM healthy first-run state](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05-NPM-First-Run-Healthy-2026-07-10.jpg)

![NPM initialized administrator](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05-NPM-Admin-Initialized-2026-07-11.jpg)

### Step 5A: Apply the Access-A egress policies

**Action:** I created ordered allow rules for CT 107 TCP 80/443 and UDP 123, followed by a block for all other Access-A IPv4 traffic to External. I disabled automatic respond-policy generation after the first web-rule request was rejected.

**Observed result:** UniFi saved the TCP 80/443 allow, UDP 123 allow, & catch-all IPv4 block in that order, with logging enabled on all three.

**Verification:** HTTP returned 200, the Docker registry returned its expected unauthenticated 401, `ntpdig` returned valid time data, and direct TCP DNS to `<YOUR_EXTERNAL_DNS_IP>:53` timed out under the block rule.

**Evidence:**

![Access-A egress policy set](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg)

### Step 6: Add internal DNS

**UI action:** I added the UniFi local A record `<YOUR_NETBIRD_DOMAIN>` pointing to `192.168.85.2` with TTL 300 seconds.

**Observed result:** The controller saved the enabled DNS record.

**Verification:** The UniFi resolver and a Windows client both returned `192.168.85.2` for the hostname.

**Evidence:**

![UniFi internal DNS record](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

### Step 7: Issue TLS and publish the NetBird proxy

**Action:** I issued the Cloudflare DNS-01 wildcard/apex certificate, assigned it to the NetBird proxy host, enabled Force SSL & HTTP/2, & applied the API, WebSocket, signal, management, & gRPC routes.

**Observed result:** The certificate was issued and the NetBird proxy host reported Online.

**Verification:** `nginx -t` passed & `https://<YOUR_NETBIRD_DOMAIN>` returned HTTP 200.

**Evidence:**

![Wildcard certificate issued](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S07A-NPM-Wildcard-Certificate-Issued-2026-07-11.jpg)

![NetBird proxy online in NPM](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S07-NPM-NetBird-Proxy-Online-2026-07-11.jpg)

### Step 8: Deploy the NetBird control plane

**Action:** I verified the official v0.74.3 installer checksum, selected Nginx Proxy Manager integration, kept direct services on loopback, joined both containers to `proxy`, and corrected the trusted proxy to `172.31.85.10/32`.

**Observed result:** `netbird-dashboard` listened on `127.0.0.1:8080`, `netbird-server` listened on `127.0.0.1:8081` and `3478/udp`, & the authenticated dashboard loaded through NPM.

**Verification:** The direct dashboard and identity-provider probes returned HTTP 200 and the published login completed.

**Evidence:**

![Authenticated NetBird dashboard](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S08-NetBird-Authenticated-Dashboard-2026-07-11.jpg)

### Step 9: Test restart persistence

**Action:** I restarted the Nginx Proxy Manager and NetBird Compose projects in a controlled sequence.

**Observed result:** NPM returned to `healthy` & both NetBird containers returned to running state.

**Verification:** Readiness passed on the second check, `nginx -t` passed, HTTPS returned 200, & the authenticated UI loaded again.

**Evidence:**

![NetBird healthy after restart](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S09-NetBird-Healthy-After-Restart-2026-07-11.jpg)

### Step 10: Remove temporary files and restrict permissions

**Action:** I removed the downloaded installer and other deployment leftovers, then set the NetBird secret configuration files and NPM database to owner-only mode 0600.

**Observed result:** The one-time installer was absent & the retained secret-bearing files reported mode 0600.

**Verification:** I checked the live paths and file modes after cleanup.

**Evidence:** The local S10 transcript holds the path & mode checks. No secret-bearing file content is published.

## Rollback

1. Stop the NetBird and Nginx Proxy Manager Compose projects before removing the guest.
2. Remove UniFi policies `<YOUR_ACCESS_EGRESS_POLICY_ID_A>`, `<YOUR_ACCESS_EGRESS_POLICY_ID_B>`, and `<YOUR_ACCESS_EGRESS_POLICY_ID_C>` in reverse order if the Access-A egress policy set must be reverted.
3. Remove local DNS record `<YOUR_NETBIRD_DNS_RECORD_ID>` if the hostname is no longer served by this LXC.
4. Remove `ct:107` from HA before stopping or destroying the guest.
5. Remove the `docker_network` SSH Manager entry if LXC 107 is retired.

Destruction of the LXC and its `local-lvm` disk is intentionally not automated and requires a separately approved destructive change.

## Follow-on Status

I validated first-peer enrollment and the routed VPN path on 2026-07-12, then verified the non-interactive ACME renewal path and bounded logging. I intentionally descoped the controlled guest reboot and the remaining hardening items I declined. See the platform [operational follow-ups/descope record](../../../../../Platforms/Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md). No infrastructure follow-up remains tracked from this change.
