# UniFi Firewall Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-26

The gateway runs UniFi's zone-based V2 firewall. I maintain 61 custom policies; UniFi maintains the rest for zone defaults, connection state, return companions, & gateway services.

## Custom Policies

All 61 user-defined policies are enabled, use connection state `ALL`, & run on the `Always` schedule. The live controller held 52 before the 2026-07-26 monitoring relocation, not the 43 this inventory previously claimed. The missing nine were the retained Kasm policies. I added 13 policies for `monitor-01`, including the DNS policy found during execution, deleted six superseded Security-A monitoring policies, and narrowed the retained NPM-to-`security-01` policy to port 443. Moving PeaNUT to `monitor-01` later the same day added the two 8090 policies at the end of the table and dropped 8090 from the docker-main entry.

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
| Allow edge-01 to app-01 Web | Yes | ALLOW | 10000 | TCP | Both | Dmz | Client (1 MAC, edge-01) | `<YOUR_ORG_NAME>`-Servers | IP 192.168.80.10 | Port group: App Access (80, 8000) | All | Always | On | edge-01 reaches only app-01 HTTP ingress and the Coolify interface |
| Allow `<YOUR_ORG_NAME>`-Servers to Wazuh - Security-A | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Servers | Any | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | Port group: Wazuh Ports | All | Always | Off | Agent access to the Wazuh manager on Security-A; automatic return policy enabled |
| Allow DMZ to Wazuh - Security-A | Yes | ALLOW | 10001 | TCP | Both | Dmz | Client (1 MAC, edge-01) | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | Port group: Wazuh Ports | All | Always | On | DMZ Wazuh-agent path to Security-A; automatic return policy enabled |
| Allow Devices to Personal-A | Yes | ALLOW | 10001 | All | Both | Internal | Clients (9 MACs) | Internal | Network: Personal-A | Any | All | Always | On | Includes M1-Dev (`192.168.10.92`) |
| Block Trusted to Personal-A | Yes | BLOCK | 10002 | All | Both | Internal | Network: Trusted | Internal | Network: Personal-A | Any | All | Always | Off | - |
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
| Allow NPM to docker-main web UIs | Yes | ALLOW | 10002 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | Internal | IP 192.168.40.35 | 2283, 3000, 3001, 6060, 8080, 8384, 9443 | All | Always | On | NPM reaches only the seven approved Docker Main web interfaces |
| Allow NPM to security-01 Wazuh | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.2 | 443 | All | Always | On | NPM reaches the Wazuh dashboard only |
| Allow NPM to splunk-siem web UI | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | `<YOUR_ORG_NAME>`-Security | IP 192.168.72.3 | 8000 | All | Always | On | NPM reaches Splunk Web only |
| KASM Allow KASM-BROWSER DHCP to Gateway | Yes | ALLOW | 10000 | UDP | IPv4 | KASM-BROWSER | Any, source port 68 | Gateway | Any | 67 | All | Always | On | Permit DHCP for the browser segment |
| KASM Allow KASM-BROWSER NTP to Gateway | Yes | ALLOW | 10002 | UDP | IPv4 | KASM-BROWSER | Any | Gateway | Any | 123 | All | Always | On | Permit gateway NTP for the browser segment |
| KASM Block KASM-BROWSER Other Gateway | Yes | BLOCK | 10003 | All | IPv4 | KASM-BROWSER | Any | Gateway | Any | Any | All | Always | On | Deny other gateway services from the browser segment |
| KASM Allow MALWARE-OFFLINE DHCP to Gateway | Yes | ALLOW | 10000 | UDP | IPv4 | MALWARE-OFFLINE | Any, source port 68 | Gateway | Any | 67 | All | Always | On | Permit DHCP for the offline malware segment |
| KASM Block MALWARE-OFFLINE Other Gateway | Yes | BLOCK | 10001 | All | IPv4 | MALWARE-OFFLINE | Any | Gateway | Any | Any | All | Always | On | Deny other gateway services from the offline malware segment |
| KASM Allow EVIDENCE-QUARANTINE DHCP to Gateway | Yes | ALLOW | 10000 | UDP | IPv4 | EVIDENCE-QUARANTINE | Any, source port 68 | Gateway | Any | 67 | All | Always | On | Permit DHCP for the evidence segment |
| KASM Block EVIDENCE-QUARANTINE Other Gateway | Yes | BLOCK | 10001 | All | IPv4 | EVIDENCE-QUARANTINE | Any | Gateway | Any | Any | All | Always | On | Deny other gateway services from the evidence segment |
| KASM Block MALWARE-OFFLINE External | Yes | BLOCK | 10000 | All | IPv4 | MALWARE-OFFLINE | Any | External | Any | Any | All | Always | On | Keep the offline malware segment off the Internet |
| KASM Block EVIDENCE-QUARANTINE External | Yes | BLOCK | 10000 | All | IPv4 | EVIDENCE-QUARANTINE | Any | External | Any | Any | All | Always | On | Keep the evidence segment off the Internet |
| Allow Monitor to Personal-A monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | Internal | IPs 192.168.40.35, .36, .39, .42 | 9100, 9101 | All | Always | On | Prometheus scrapes node_exporter and cAdvisor on docker-main, ansible-01, docker-blue, and media-01; automatic return policy enabled |
| Allow Monitor to A-Servers monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | `<YOUR_ORG_NAME>`-Servers | IPs 192.168.80.10, 192.168.80.118 | 9100, 9101 | All | Always | On | Prometheus scrapes node_exporter and cAdvisor on app-01 and alpha-prod-01; automatic return policy enabled |
| Allow Monitor to A-Access monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | 9100, 9101, 443 | All | Always | On | Prometheus scrapes docker-network and probes the NPM HTTPS front door; automatic return policy enabled |
| Allow Monitor to A-Security monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | `<YOUR_ORG_NAME>`-Security | IPs 192.168.72.2, 192.168.72.3 | 9100, 9101 | All | Always | On | Prometheus scrapes security-01 and splunk-siem; automatic return policy enabled |
| Allow Monitor to DMZ monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | Dmz | IP 192.168.90.10 | 9100 | All | Always | On | Prometheus scrapes node_exporter on edge-01; automatic return policy enabled |
| Allow Monitor to Proxmox monitoring | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | `<YOUR_ORG_NAME>`-Mgmt | IPs 192.168.70.10–.13 | 9100, 8006 | All | Always | On | Prometheus and the PVE exporter reach the Proxmox monitoring and API endpoints; automatic return policy enabled |
| Allow Monitor to Proxmox NUT | Yes | ALLOW | 10001 | TCP | Both | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | `<YOUR_ORG_NAME>`-Mgmt | IPs 192.168.70.10, 192.168.70.13 | 3493 | All | Always | On | The NUT exporter and PeaNUT both read `ups01` and `ups02`; automatic return policy enabled |
| Allow Monitor Web Egress | Yes | ALLOW | 10000 | TCP | IPv4 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | External | Any | 80, 443 | All | Always | On | Permit package, image, certificate, and application web egress from monitor-01 |
| Allow Monitor NTP Egress | Yes | ALLOW | 10001 | UDP | IPv4 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | External | Any | 123 | All | Always | On | Permit time synchronization from monitor-01 |
| Allow NPM to monitor-01 web UIs | Yes | ALLOW | 10000 | TCP | Both | `<YOUR_ORG_NAME>`-Access | IP 192.168.85.2 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | 3000, 8090, 9090 | All | Always | On | NPM reaches Grafana, PeaNUT, and Prometheus; automatic return policy enabled |
| Allow Secure to monitor-01 break-glass | Yes | ALLOW | 10000 | TCP | Both | Internal | IP 192.168.50.241 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | 3000, 8090, 9090 | All | Always | On | Jedi PC can reach the three web interfaces directly; automatic return policy enabled |
| Allow Automation to monitor-01 SSH | Yes | ALLOW | 10001 | TCP | Both | Internal | IP 192.168.40.36 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | 22 | All | Always | On | ansible-01 reaches the restricted SSH account; automatic return policy enabled |
| Allow Monitor DNS to Gateway | Yes | ALLOW | 10000 | All | IPv4 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | Gateway | Any | 53 | All | Always | On | Permit gateway DNS over TCP and UDP after the initial split-horizon lookup failed |
| Allow VPN Management Access to PeaNUT | Yes | ALLOW | 10000 | TCP | Both | Vpn | Network: `<YOUR_VPN_NETWORK>` | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | 8090 | All | Always | On | Remote VPN clients reach the UPS dashboard only; automatic return policy enabled |
| Allow <YOUR_ADMIN_USERNAME> MacBook Air M3 to PeaNUT | Yes | ALLOW | 10002 | TCP | Both | Internal | IP 192.168.10.27 | `<YOUR_ORG_NAME>`-Monitor | IP 192.168.73.2 | 8090 | All | Always | On | One fixed-IP laptop on Trusted reaches the UPS dashboard only; automatic return policy enabled |

The `<YOUR_ORG_NAME>`-Access and `<YOUR_ORG_NAME>`-Security egress trios are order-sensitive and use index order 10000, 10001, then 10002. I disabled UniFi automatic respond-policy generation on all six egress entries (`create_allow_respond=false`). The `<YOUR_ORG_NAME>`-Monitor web and NTP egress pair follows the same order without a terminal zone-wide block because the zone defaults already deny unmatched traffic. I enabled automatic response policies for the cross-zone monitoring, NPM, break-glass, and SSH paths.

Zone names and policy descriptions have to be edited in the controller UI. The management plugin exposes no zone-rename operation, and it silently drops `description` from a policy update rather than failing, so a change that looks applied may not be.

A UniFi policy is not sufficient on its own for anything landing on a Proxmox node. The Datacenter firewall in [Galaxy Data Center Firewall](../../../../Compute/Galaxy/Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md) enforces independently. The NUT path proved that on 2026-07-25, and the monitoring relocation also required the `pve_svc_clients` IPSet member outside the main rule section. Test from the source host after adding a policy rather than assuming the gateway is the only gate.

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

The edge-01 restriction and Cloudflare Access change are documented in [Coolify Access Hardening - 2026-07-22](../../../Cloudflare/Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

The VLAN 73 collector policies, DNS finding, six Security-A policy deletions, and retained Wazuh port are documented in [Monitoring Relocation to monitor-01 - 2026-07-26](../../../../../Platforms/Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

The two 8090 policies, the 8090 additions to the NPM and break-glass entries, and the 8090 removal from docker-main are documented in [PeaNUT Relocation to monitor-01 - 2026-07-26](../../../../../Platforms/PeaNUT/Documentation/Change%20Records/PeaNUT%20Relocation%20to%20monitor-01%20-%202026-07-26.md).
