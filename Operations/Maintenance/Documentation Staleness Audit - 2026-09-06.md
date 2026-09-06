# Documentation Staleness Audit

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-06  
**Status:** Complete; host-side follow-ups tracked in [TODO.md](../../TODO.md)  
**Affected systems:** All five Galaxy nodes, all 13 workload guests, the UniFi controller, and the living records that describe them

## Outcome

I read the live state of the cluster, every guest, and the UniFi controller back through Executor, then compared it line by line with the records that claim to describe them. The records were right about far more than they were wrong about: every VLAN, subnet, DHCP range, zone, firewall policy count, DNS record, Prometheus target, and Wazuh agent the records name is on the live system. What had drifted was concentrated in the living inventory files and in version figures that services had moved past. I corrected each in its owning file, archived the one platform that had no workload behind it, and left the hosts untouched.

Two findings matter beyond bookkeeping. `docker-main`'s Wazuh agent has been pointed at the manager's pre-migration address since before 2026-07-12 and has never connected to the current manager, so the records that tracked it as "on 4.14.0" were tracking a version that reports to nobody. And `kali-pen` was destroyed and rebuilt under a different VMID on 2026-08-26 without any record, so the VM inventory described a guest that had not existed for eleven days.

## Method

The read side was Executor's SSH Manager and UniFi gateways. On `grey-server` I read `pvesh get /cluster/resources`, `pveversion`, `pvecm status`, `ha-manager status`, `/etc/pve/storage.cfg`, `/etc/pve/firewall/cluster.fw`, `/etc/pve/ha/rules.cfg`, every `qemu-server/*.conf` and `lxc/*.conf` on the cluster, and the task index for create and destroy events. From each node I read the installed and running kernels, `pvesm status`, NUT state, and the root `authorized_keys` link. On each of the 13 guests I read the OS release, uptime, `docker ps` with images, OCI version labels, package versions for the Wazuh agent and node exporter, and the service's own version endpoint where one exists. On `monitor-01` I read the Prometheus targets API and the Grafana health endpoint; on `security-01` I ran `agent_control -l` and `agent_groups -l` through the configured sudo path.

From UniFi I listed the networks, zones, all 68 firewall policies, firewall groups, client groups, OON policies, WLANs, port profiles, traffic routes, static routes, port forwards, DNS records, adopted devices, and the controller version. The controller's login limiter returned `429` partway through, so the second half of the readback ran after a pause; nothing was written to the controller at any point.

Every command was read-only. The one thing I changed outside this repository is nothing.

## Findings and Corrections

| Record | What it said | What is live | Correction |
|---|---|---|---|
| [VMs](../Inventory/Galaxy/VMs.md) | `kali-pen` is VM 106: 4 vCPU, 5.86 GiB, 50G, no VLAN tag, Kali 2025.2 | VM 106 was destroyed at 10:42 EDT on 2026-08-26 and `kali-pen` recreated at 10:52 EDT as VM 102: 6 vCPU, 8 GiB, 100G on `local-lvm`, VLAN 40, Kali 2026.2, stopped | Replaced the table row and detail block; noted that VMID 102 is in use again after the `debian-dev` deletion |
| [VMs](../Inventory/Galaxy/VMs.md) | `ubuntu-dev` still awaits a restart for `balloon: 0` to take effect and sees 11.4 GiB | The guest has been up since 2026-08-19 and reports 15,408 MiB | Closed the note; recorded the OS as Ubuntu 26.04.1 LTS |
| [LXCs](../Inventory/Galaxy/LXCs.md) | `docker-blue` is 1 vCPU, 1 GiB, 0.5 GiB swap; the fleet totals 18 vCPUs, 38 GiB, 10 GiB swap | `docker-blue` is 2 vCPU, 2 GiB, 1 GiB swap, `onboot` set; the file was written 2026-09-01 12:51 EDT; totals are 19, 39, and 10.5 | Corrected the row, the detail table, and the totals |
| [LXCs](../Inventory/Galaxy/LXCs.md) | No mention | CT 110 carries `unused0: hddpool:subvol-110-disk-0`, a reference to a storage ID that is not defined | Recorded it; cleanup is a TODO item |
| [Services](../Inventory/Galaxy/Services.md) | `docker-main` is a Docker host with no agent row; the Wazuh TODO tracked it as "on 4.14.0" | `wazuh-agent` 4.14.0-1 is active but `ossec.conf` names `192.168.40.227` and the agent has never appeared on the manager | Added the row, corrected the Wazuh TODO, and opened a root TODO item |
| [Services](../Inventory/Galaxy/Services.md) | Wazuh table has 14 rows and a 2026-08-03 count | `agent_control -l` lists 15 active remote agents including `game-01` as `018` | Added the row and a 2026-09-06 count with the group totals |
| [Services](../Inventory/Galaxy/Services.md) | NetBird management 0.78.0 | 0.78.1 since 2026-09-04 | Corrected two rows and the [NetBird runbook](../../Platforms/Netbird/Documentation/Runbook.md) |
| [Services](../Inventory/Galaxy/Services.md) | Executor 1.6.7 | 1.6.8 by OCI label | Corrected two rows |
| [Services](../Inventory/Galaxy/Services.md) | `docker-blue` runs Docker 29.6.2, containerd 2.2.6, runc 1.3.6 | 29.8.0, 2.3.4, 1.5.1 | Corrected the runtime row and noted the fleet-wide engine versions |
| [Services](../Inventory/Galaxy/Services.md) | `ubuntu-dev` runs VS Code 1.133.0, GitHub CLI 2.97.0, Compose v5.4.0 | 1.136.1, 2.98.0, v5.5.0 | Corrected |
| [Services](../Inventory/Galaxy/Services.md) | Grafana has 15 provisioned alert rules | The provisioning file carries 24 rules and the Prometheus backlog says 24 | Corrected |
| [Services](../Inventory/Galaxy/Services.md) | `red-server` NUT `ups01` driver and server active | `nut-server` inactive, `[ups01]` commented out since 2026-08-31, `upsc -l` empty | Corrected the UPS telemetry table |
| [Services](../Inventory/Galaxy/Services.md) | `alpha-prod-01` runs TeamSpeak, TS3 Manager, Playit | Also the `teamspeak-monitor` reachability collector, documented under Teamspeak Hosting but absent here | Added |
| [Nodes](../../Infrastructure/Hardware/Nodes.md) | Storage last read 2026-08-09 and 2026-08-19 | `hddpool-1` at 82.46 percent, `ssd-lvm1` at 13.47 percent | Added the 2026-09-06 readback beneath the earlier ones |
| [Datacenter firewall](../../Infrastructure/Compute/Galaxy/Configuration/Datacenter-Firewall.md) | Five IPSets and eleven rules | The live file also defines `pve_ssh_manager` holding `192.168.40.39` and a TCP 22 accept for it, both written 2026-08-31 | Added the IPSet, the rule, and a history entry |
| [UniFi firewall](../../Infrastructure/Network/UniFi/Configuration/firewall.md) | Seven policies named with `AlphaSec` | The controller names them `AlphSec` or `A-Servers`; the 2026-07-27 correction renamed zones, not policies | Renamed the rows to match the controller |
| [UniFi objects](../../Infrastructure/Network/UniFi/Configuration/objects.md) and [VPN and port profiles](../../Infrastructure/Network/UniFi/Configuration/vpn-networks-port-profiles.md) | 15 firewall groups; `PG-Node-Exporter` is 9100 and 9101 in one file | 16 groups including `PG-Printing` on 631 and 9100; `PG-Node-Exporter` carries 9102 | Added the group and the port |
| [UniFi objects](../../Infrastructure/Network/UniFi/Configuration/objects.md) | 15 client groups | 17: an empty `IOT` and a one-member `IoT` exist again | Recorded; decision is a TODO item |
| [VPN and port profiles](../../Infrastructure/Network/UniFi/Configuration/vpn-networks-port-profiles.md) and [zones](../../Infrastructure/Network/UniFi/Configuration/zone.md) | `Game-Access` enabled; `One-Click VPN` is a network in the `Vpn` zone | `Game-Access` disabled; the controller returned four remote-user VPN networks and no `One-Click VPN` object | Corrected the status; kept the One-Click row marked as not returned, because the interface has not been checked |
| [Networks and VLANs](../../Infrastructure/Network/UniFi/Configuration/network-vlan.md) | The disabled WLAN is `AlphaSec-IoT` | The controller spells it `Alpha-Sec-IoT` | Corrected |
| [UniFi README](../../Infrastructure/Network/UniFi/README.md) and [UniFi guide](../../Guides/UniFi-Network.md) | Partial counts from 2026-08-19 and 2026-09-05 | Full 2026-09-06 readback | Replaced with the complete count |
| [Guides index](../../Guides/README.md), [Portainer guide](../../Guides/Portainer.md), [Prometheus guide](../../Guides/Prometheus.md) | Portainer 2.39.5 and agents 2.39.1; Prometheus 3.13.1 with 52 targets across six jobs | Portainer 2.45.0 throughout; Prometheus 3.14.0 with 57 targets across seven jobs | Rewrote the status paragraphs and index rows |
| [Infrastructure README](../../Infrastructure/README.md) | "four-node Galaxy cluster" | Five nodes since 2026-07-31 | Corrected |
| [Operations README](../README.md) | Lists a `Diagnostics/` folder | No such folder; SMART output lives under the hardware component records | Corrected |

## What Matched

The 22 network objects, 15 routed LANs, subnets, gateway addresses, DHCP ranges, 11 zones, 68 policies with their 61 to seven split, 29 DNS records, four OON policies, one traffic route, five port profiles, five WLANs with three enabled, zero port forwards, and zero static routes all matched their records. All five nodes run `pve-manager/9.2.11` on kernel `7.0.14-8-pve` with `7.0.14-15-pve` installed, quorum is five of five, the HA rule pins CT 107 and CT 108 to `blue-server`, and the ten-key root file is the shared symlink on every node. Prometheus reported 57 of 57 targets up across node, cAdvisor, WUD, blackbox, NUT, Proxmox, and self-scrape jobs. Grafana is 13.2.1 and Prometheus 3.14.0. The version figures for Immich 3.1.0, BookLore v2.3.1, Forgejo 16.0.3, Portainer 2.45.0, CLI Proxy API v7.2.149, Ollama 0.33.3 with `qwen3.5:2b`, Open WebUI 0.11.3, Nginx Proxy Manager 2.15.1, NetBird dashboard v2.92.0, Docker MCP Gateway v0.43.3, SSH Manager 3.8.5 behind mcp-proxy 0.12.0, Jellyfin 10.11.11, Seerr 3.4.1, Coolify 4.3.17, Traefik v3.7, Pelican Panel v1.0.0-beta38, Playit 1.0.10 in the container and 1.0.9 as the native package, Semaphore 2.18.27, ansible-core 2.21.2, the Wazuh 4.14.7 central stack, Wazuh MCP 4.3.0, and the 4.14.6 agent fleet with `edge-01` on 4.14.5 were all as recorded. The Caddyfile on `edge-01` matches the versioned copy byte for byte in its uncommented lines.

## What I Could Not Verify

- **Cloudflare.** The Executor Cloudflare connection exposes a single tool, documentation search, so I could not read zones, DNS records, or the tunnel. The [Cloudflare records](../../Infrastructure/Network/Cloudflare/README.md) keep their 2026-08-09 verification date and a TODO item asks how they get verified next.
- **Splunk version.** `splunk version` needs root on `splunk-siem`, and the SSH Manager's configured `dkadi` login there has no sudo password entry. `Splunkd.service` and `sc4s.service` are both active and the root filesystem is at 36 percent, so the platform is up; the 10.4.0 figure stays on its own verification date.
- **Semaphore template count.** The API answers `pong` without authentication and the template list does not, so the 23-template figure was not re-read.
- **Grafana rule count from the running instance.** The API requires a session. I used the provisioning file, which is what the running instance loads.
- **One-Click VPN.** Not returned as a network object. Whether the feature is still configured needs a look at the interface.
- **`kali-pen`'s address.** The VM was stopped, so no guest address could be read.

## Archive

I moved `Platforms/Windows Servers/README.md` to `Archive/Platforms/Windows Servers/README.md`, beside the private plan, change record, and evidence that have lived there since 2026-07-27. The platform had no workload since that date and its README was already a retirement notice. The `.gitignore` rules moved with it so the README stays published and everything beside it stays private, and the four records that linked the old path now link the new one. No other platform qualified: every remaining folder under `Platforms/` maps to a container, service, or systemd unit that was running on 2026-09-06, and `Galaxy PXE`'s `galaxy-pxe.service` is active on `ansible-01` by design.

## Host-Side Follow-Ups

I changed nothing on a host or the controller. These need a decision and are in the root TODO:

- Re-enroll `docker-main`'s Wazuh agent against `192.168.72.2`.
- Remove the `unused0` line from CT 110 or confirm it is wanted.
- Remove or keep the five container-less directories under `/opt/docker` on `docker-main`.
- Decide whether `docker-blue` keeps both `pve_admins` and `pve_ssh_manager` in the Datacenter firewall.
- Decide whether the `IOT` and `IoT` client groups stay on the controller.
- Give Executor a Cloudflare connection that can read the account, or verify the Cloudflare records by hand.
