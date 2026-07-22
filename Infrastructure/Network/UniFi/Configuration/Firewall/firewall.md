# UniFi Firewall Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-22

The gateway runs UniFi's zone-based V2 firewall. I maintain 39 custom policies; UniFi maintains the other 234 for zone defaults, connection state, return companions, & gateway services.

## Custom Policies

All 39 user-defined policies are enabled, use connection state `ALL`, & run on the `Always` schedule. I last checked the controller on 2026-07-22 after adding the NPM backend paths.

| Policy | Enabled | Action | Index | Protocol | IP Ver | Source Zone | Source Match | Dest Zone | Dest Match | Dest Port | Conn State | Schedule | Logging | Description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Block DMZ to Internal | Yes | BLOCK | 40000 | All | Both | Dmz | Any | Internal | Any | Any | All | Always | On | Prevent DMZ workloads from laterally accessing Internal networks |
| DMZ Allow List | Yes | ALLOW | 10001 | All | Both | Internal | Clients (3 MACs) | Dmz | Any | Any | All | Always | On | Whitelisted admin devices into DMZ |
| Block DMZ to LAN | Yes | BLOCK | 40001 | All | Both | Dmz | Any | Internal | Any | Any | All | Always | On | - |
| Allow VPN to `<YOUR_ORG_NAME>`-Mgmt | Yes | ALLOW | 10000 | All | Both | Vpn | Any | `<YOUR_ORG_NAME>`-Mgmt | Any | Any | All | Always | Off | - |
| Allow VPN to `<YOUR_ORG_NAME>`-Servers | Yes | ALLOW | 10000 | All | Both | Vpn | Any | `<YOUR_ORG_NAME>`-Servers | Any | Any | All | Always | Off | - |
| Allow `<YOUR_ORG_NAME>`-Mgmt to `<YOUR_ORG_NAME>`-Servers | Yes | ALLOW | 10000 | All | Both | `<YOUR_ORG_NAME>`-Mgmt | Any | `<YOUR_ORG_NAME>`-Servers | Any | Any | All | Always | Off | - |
| Allow Internal to `<YOUR_ORG_NAME>`-Mgmt | Yes | ALLOW | 10000 | All | Both | Internal | Any | `<YOUR_ORG_NAME>`-Mgmt | Any | Any | All | Always | On | - |
| Allow Internal to `<YOUR_ORG_NAME>`-Servers | Yes | ALLOW | 10000 | All | Both | Internal | Any | `<YOUR_ORG_NAME>`-Servers | Any | Any | All | Always | On | - |
| Allow Internal to `<YOUR_ORG_NAME>`-Access | Yes | ALLOW | 10000 | All | Both | Internal | Any | `<YOUR_ORG_NAME>`-Access | Any | Any | All | Always | On | LAN access to network access / connectivity services (reverse proxy, remote-access mesh, and similar ingress tooling) |
| Allow VPN to `<YOUR_ORG_NAME>`-Access | Yes | ALLOW | 10000 | All | Both | Vpn | Any | `<YOUR_ORG_NAME>`-Access | Any | Any | All | Always | Off | Remote VPN clients reach network access / connectivity services for off-LAN administration |
| Allow docker-network Web Egress | Yes | ALLOW | 10000 | TCP | IPv4 | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | External | Any | 80, 443 | All | Always | On | Permit package, image, certificate, and application HTTPS/HTTP egress from `docker-network` |
| Allow docker-network NTP Egress | Yes | ALLOW | 10001 | UDP | IPv4 | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | External | Any | 123 | All | Always | On | Permit time synchronization from `docker-network` |
| Block `<YOUR_ORG_NAME>`-Access Other External Egress | Yes | BLOCK | 10002 | All | IPv4 | `<YOUR_ORG_NAME>`-Access | Any | External | Any | Any | All | Always | On | Default-deny remaining `<YOUR_ORG_NAME>`-Access Internet egress after the two workload-specific allows |
| Allow Internal to `<YOUR_ORG_NAME>`-Security | Yes | ALLOW | 10000 | All | Both | Internal | Any | `<YOUR_ORG_NAME>`-Security | Any | Any | All | Always | On | LAN access to security and monitoring services (SIEM, detection, log/metrics tooling) |
| Allow VPN to `<YOUR_ORG_NAME>`-Security | Yes | ALLOW | 10000 | All | Both | Vpn | Any | `<YOUR_ORG_NAME>`-Security | Any | Any | All | Always | Off | Remote VPN clients reach security and monitoring services for off-LAN administration |
| Allow Security Workloads Web Egress | Yes | ALLOW | 10000 | TCP | IPv4 | `<YOUR_ORG_NAME>`-Security | IPs 192.168.72.2, 192.168.72.3 | External | Any | 80, 443 | All | Always | On | Permit package, image, certificate, and application HTTPS/HTTP egress from the two Security-A workloads |
| Allow Security Workloads NTP Egress | Yes | ALLOW | 10001 | UDP | IPv4 | `<YOUR_ORG_NAME>`-Security | IPs 192.168.72.2, 192.168.72.3 | External | Any | 123 | All | Always | On | Permit time synchronization from the two Security-A workloads |
| Block `<YOUR_ORG_NAME>`-Security Other External Egress | Yes | BLOCK | 10002 | All | IPv4 | `<YOUR_ORG_NAME>`-Security | Any | External | Any | Any | All | Always | On | Default-deny remaining Security-A Internet egress after the two workload-specific allows |
| Allow DMZ to `<YOUR_ORG_NAME>`-Servers | Yes | ALLOW | 10000 | TCP | Both | Dmz | Client (1 MAC, edge-01) | `<YOUR_ORG_NAME>`-Servers | Network: SERVERS-A | Any | All | Always | On | edge-01 can reach app-01 (ports 8080/80 per notes) |
| Allow `<YOUR_ORG_NAME>`-Servers to Wazuh - Security-A | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Servers | Any | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | Port group: Wazuh Ports | All | Always | Off | Agent access to the Wazuh manager on Security-A; automatic return policy enabled |
| Allow DMZ to Wazuh - Security-A | Yes | ALLOW | 10001 | TCP | Both | Dmz | Client (1 MAC, edge-01) | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | Port group: Wazuh Ports | All | Always | On | DMZ Wazuh-agent path to Security-A; automatic return policy enabled |
| Allow Devices to Personal-A | Yes | ALLOW | 10001 | All | Both | Internal | Clients (9 MACs) | Internal | Network: Personal-A | Any | All | Always | On | Includes M1-Dev (`192.168.10.92`) |
| Block Trusted to Personal-A | Yes | BLOCK | 10002 | All | Both | Internal | Network: Trusted | Internal | Network: Personal-A | Any | All | Always | Off | - |
| Allow Security to DMZ monitoring | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | Dmz | IP 192.168.90.10 | 9100 | All | Always | On | Prometheus on security-01 scrapes node_exporter on edge-01; automatic return policy enabled |
| Allow Security to Proxmox monitoring | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | `<YOUR_ORG_NAME>`-Mgmt | IPs 192.168.70.10–.13 | 9100, 8006 | All | Always | On | Prometheus and PVE exporter reach Proxmox monitoring/API endpoints; automatic return policy enabled |
| Device Access to Proxmox | Yes | ALLOW | 10001 | All | Both | Internal | Clients (4 MACs) | `<YOUR_ORG_NAME>`-Mgmt | Any | Port group: Proxmox-Admin-Ports | All | Always | Off | Access to Proxmox GUI / SSH |
| Allow A-Servers to Portainer Edge | Yes | ALLOW | 10000 | All | Both | `<YOUR_ORG_NAME>`-Servers | Any | Internal | IP 192.168.40.35 | Port group: Portainer Edge Agents | All | Always | On | `<YOUR_ORG_NAME>`-Servers VMs reach Portainer Edge tunnel/API on docker-main |
| Allow Identity Sync Service Connection | Yes | ALLOW | 10000 | All | Both | External | Any | Gateway | Any | Port group: Identity Sync 9543 | All | Always | Off | - |
| VPN: Temp Ban | Yes | BLOCK | 10000 | All | Both | Vpn | Network: Temp | Internal | Networks: Personal-A, Secure, Secure Client, AD-SERVERS, Management | Any | All | Always | On | - |
| VPN: Temp #2 | Yes | BLOCK | 10001 | All | Both | Vpn | Network: Temp | `<YOUR_ORG_NAME>`-Servers | Any | Any | All | Always | On | - |
| Docker-main Allowed -> Server | Yes | ALLOW | 10002 | All | IPv4 | Internal | Client (1 MAC, docker-main) | `<YOUR_ORG_NAME>`-Mgmt | Network: MGMT-A | Port group: Proxmox-Admin-Ports | All | Always | Off | - |
| Docker -> Jedi PC | Yes | ALLOW | 10003 | All | Both | Internal | Client (1 MAC, docker-main) | Internal | Network: Secure | Any | All | Always | Off | - |
| Allow VPN --> Internal Zone | Yes | ALLOW | 10001 | All | Both | Vpn | Network: `<YOUR_VPN_NETWORK>` | Internal | Any | Any | All | Always | On | Approved VPN network reaches Internal-zone services |
| Allow Device --> media-01 | Yes | ALLOW | 10004 | All | Both | Internal | Clients (2 MACs) | Internal | Network: Personal-A | Any | All | Always | On | Two approved devices reach media-01 |
| Allow NPM to media-01 web UIs | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | Internal | IP 192.168.40.42 | 5055, 7878, 8080, 8096, 8989, 9696 | All | Always | On | NPM reaches only the six approved media web interfaces |
| Allow NPM to ansible-01 Semaphore | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | Internal | IP 192.168.40.36 | 3000 | All | Always | On | NPM reaches Semaphore only |
| Allow NPM to docker-main web UIs | Yes | ALLOW | 10002 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | Internal | IP 192.168.40.35 | 2283, 3000, 3001, 6060, 8080, 8090, 8384, 9443 | All | Always | On | NPM reaches only the eight approved Docker Main web interfaces |
| Allow NPM to security-01 web UIs | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | 443, 3000, 9090 | All | Always | On | NPM reaches Wazuh, Grafana, & Prometheus only |
| Allow NPM to splunk-siem web UI | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.3 | 8000 | All | Always | On | NPM reaches Splunk Web only |

The `<YOUR_ORG_NAME>`-Access and `<YOUR_ORG_NAME>`-Security egress trios are order-sensitive and use index order 10000, 10001, then 10002. I disabled UniFi automatic respond-policy generation on all six egress entries (`create_allow_respond=false`). I created the four cross-zone Security-A inbound/monitoring allows with automatic respond-policy generation enabled; setting that flag only after creation did not materialize a return companion on this controller.

## UniFi-Generated Policies

The controller creates these for the zone matrix, state tracking, & gateway services. I don't edit them by hand.

| Category | Count | Purpose |
|---|---|---|
| Block All Traffic | 106 | Default-deny catch-all for each zone pair (lowest priority) |
| Allow All Traffic | 37 | Default-allow for permitted / intra-zone pairs (lowest priority) |
| Block Invalid Traffic | 22 | Drops packets in an invalid conntrack state |
| Allow Return Traffic | 18 | Stateful return path for established/related connections |
| Auto "(Return)" companions | 27 | Auto-created reverse rule for custom policies that request a response path |
| Isolated Networks | 9 | Blocks generated by per-network isolation toggle |
| Allow mDNS | 2 | Multicast DNS / service discovery |
| Allow DHCPv6 | 2 | DHCPv6 leasing |
| Other controller service policies | 11 | WireGuard, gateway services, IPv6 discovery/autoconfiguration, and controller-managed special cases |

The controller held 273 live policies on 2026-07-22: 39 user-defined and 234 controller-maintained. The five NPM policies produced five enabled return companions.

The 2026-07-12 Security-A additions and MGMT-A rule retirement are documented in [Security-A Migration - 2026-07-12](../../Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md).

The five NPM backend policies and their route verification are documented in [Internal HTTPS Service Onboarding - 2026-07-22](../../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).
