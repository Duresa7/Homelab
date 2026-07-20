# Security-A Migration

**Created:** 2026-07-12  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-12  
**Status:** Complete  
**Primary owner:** UniFi network segmentation  
**Affected systems:** UniFi gateway, Galaxy Proxmox cluster firewall, VM 109 `splunk-siem`, VM 200 `security-01`, Ansible inventory, local SSH Manager

## Scope

Move the two security and monitoring guests from MGMT-A/VLAN 70 to Security-A/VLAN 72, replace their cross-zone policy paths, apply workload-specific external egress restrictions, remove obsolete MGMT-A references, and prove the services still operate. I ran the migration end to end and required zero new WAN-inbound exposure.

I pulled Wazuh agent repointing out of the active scope and recorded it as later work. During validation, live state also showed that three planned Proxmox `node_exporter` targets did not exist and three Prometheus targets were stale or offline; I deferred those baseline corrections rather than expanding this migration.

## Starting State

| Guest | Before | Workloads |
|---|---|---|
| VM 109 `splunk-siem` | `192.168.70.109/24`, VLAN 70 | Splunk Enterprise/ES, SC4S, HEC |
| VM 200 `security-01` / `wazuh-01` | `192.168.70.20/24`, VLAN 70 | Wazuh manager/indexer/dashboard, Prometheus, Grafana, PVE exporter |

The UniFi controller had Wazuh policies aimed at `192.168.70.20` and a MGMT-A-to-DMZ node-exporter policy. The Galaxy Datacenter firewall allowed TCP 9100 and 8006 from all of `192.168.70.0/24`. No port forward or WAN-facing policy targeted either guest.

My preflight confirmed both QEMU agents responded, both NICs were VirtIO on `vmbr0` with guest firewall enabled and VLAN tag 70, and neither proposed Security-A address was in use. I backed up network configuration and firewall files before changing anything.

## Decisions

- I assigned static addresses: `security-01` = `192.168.72.2/24`; `splunk-siem` = `192.168.72.3/24`; gateway and DNS = `192.168.72.1`.
- I cut over hard, one guest at a time, Splunk first. `security-01` could not start until Splunk passed service, port, UI, and egress validation.
- I preserved NIC model, MAC, bridge, and guest-firewall state; I changed only the VLAN tag and in-guest addressing.
- I permitted external TCP 80/443 and UDP 123 only from the two Security-A workload IPs, then blocked and logged all remaining `<YOUR_ORG_NAME>`-Security-to-External IPv4 traffic.
- I added only the inbound/cross-zone paths required for Wazuh and monitoring. No WAN-inbound policies or port forwards.
- I kept the existing Galaxy TCP 8006 accept from `192.168.70.0/24` for later review, but replaced the broad TCP 9100 accept with `192.168.72.2/32`.
- I recorded MGMT-A's future allowed set as Trusted/VLAN 10, Secure/VLAN 50, WireGuard VPN, and future NetBird traffic sourced from `<YOUR_ORG_NAME>`-Access. Final MGMT-A lockdown is a separate bounded change.

## Actions and Observed Results

### 1. Stage the replacement paths

I created seven enabled UniFi policies:

| Policy | Path |
|---|---|
| Allow `<YOUR_ORG_NAME>`-Servers to Wazuh - Security-A | `<YOUR_ORG_NAME>`-Servers → `192.168.72.2`, Wazuh Ports |
| Allow DMZ to Wazuh - Security-A | `edge-01` → `192.168.72.2`, Wazuh Ports |
| Allow Security to DMZ monitoring | `192.168.72.2` → `192.168.90.10:9100` |
| Allow Security to Proxmox monitoring | `192.168.72.2` → `192.168.70.10`–`.13`, TCP 9100/8006 |
| Allow Security Workloads Web Egress | `.72.2` and `.72.3` → External TCP 80/443 |
| Allow Security Workloads NTP Egress | `.72.2` and `.72.3` → External UDP 123 |
| Block `<YOUR_ORG_NAME>`-Security Other External Egress | remaining `<YOUR_ORG_NAME>`-Security → External IPv4 |

I added `/32` accepts from `192.168.72.2` for TCP 9100 and 8006 to the Galaxy firewall. `pve-firewall compile` completed successfully.

### 2. Cut over `splunk-siem`

I backed up the NetworkManager connection under `/root/security-a-migration-20260712-213903`, changed the address to `192.168.72.3/24` with gateway/DNS `192.168.72.1`, and changed VM 109's Proxmox NIC tag from 70 to 72 without altering the VirtIO MAC, bridge, or firewall flag. The guest rebooted cleanly.

Post-reboot observations: `Splunkd`, `sc4s`, `sshd`, `qemu-guest-agent`, and `firewalld` were active; SC4S listened on TCP and UDP 1514; Splunk listened on 8000, 8088, and 8089; Splunk Web returned HTTP 303; HTTPS HEC health returned HTTP 200. Internal access to `https://192.168.72.3:8000` returned HTTP 303. The handoff's HTTP/200 check was superseded by this host's already-enabled HTTPS-only setting: plain HTTP reset the connection and HTTPS returned the expected unauthenticated login redirect. HTTP and HTTPS egress returned 200, NTP sources remained reachable and synchronized, and an external TCP/53 connection timed out.

### 3. Cut over `security-01`

I backed up netplan under `/root/security-a-migration-20260713-014435`, changed the address to `192.168.72.2/24` with gateway/DNS `192.168.72.1`, and changed VM 200's Proxmox NIC tag from 70 to 72 while preserving all other NIC fields. The guest rebooted cleanly.

Post-reboot observations: SSH, Docker, Wazuh manager, Wazuh indexer, and Wazuh dashboard were active. The Grafana, Prometheus, and PVE-exporter containers were up. Internal requests returned HTTP 302 from the Wazuh dashboard, Grafana, and Prometheus. HTTP and HTTPS egress returned 200, `systemd-timesyncd` reported an active upstream with seven packets received, and external TCP/53 timed out.

Monitoring-path tests from `security-01` returned HTTP 200 from `edge-01:9100`, `grey-server:9100`, and the Proxmox API on `grey-server:8006`. Prometheus reported `edge-01`, `grey-server`, and the PVE exporter UP.

### 4. Diagnose and correct the response path

I initially created the first replacement policies without automatic response policies and later updated them to request one. The forward policies showed the new flag, but the controller did not create the hidden reverse companions, so monitoring connections still timed out. Re-creating the four cross-zone policies with response generation enabled at creation materialized the return paths. I used a temporary single-port rule to isolate the behavior and removed it after the final combined rule passed.

This behavior and the MCP deletion limitation are recorded in the [UniFi troubleshooting log](../Troubleshooting-Log.md).

### 5. Remove obsolete state and update access inventories

I removed the three original MGMT-A policies, the four superseded forward-only policies, and the temporary response test policy. A fresh API listing returned 32 enabled custom policies and none of the removed names or IDs. I removed the old Galaxy TCP 9100 accept from `192.168.70.0/24` and retained the planned TCP 8006 management accept. `pve-firewall status` returned `enabled/running` after cleanup.

I updated the Ansible inventory to map `security-01` to `192.168.72.2` and `splunk-siem` to `192.168.72.3`; `ansible-inventory --graph` succeeded with an explicit UTF-8 locale. I added local SSH Manager entries for both new addresses using the existing approved key, and detailed health checks succeeded over direct SSH.

### 6. Close the UniFi SIEM export handoff

I changed the UniFi Activity Logging destination to `192.168.72.3:1514`. The authenticated controller UI showed SIEM Server enabled with that exact address and port and eight event-content categories selected.

At `2026-07-12 22:40:27 EDT`, SC4S recorded one 317-byte CEF source event and processed it through `vendor_product_by_source` and `p_cef_kv`. Its HEC destination showed zero dropped and zero queued events. Splunk's `per_index_thruput` metric then recorded one `netops` event at `22:40:43` with an average age of 0.720 seconds. The `netops` hot bucket created its raw-data and `.tsidx` files at the same `22:40:27` event timestamp. This proves the controller-originated CEF path from UniFi through SC4S/HEC into Splunk; no additional Gateway-to-Security policy was required.

## Resulting Configuration

| Item | Result |
|---|---|
| VM 109 | VLAN 72, `192.168.72.3/24`, gateway/DNS `.72.1` |
| VM 200 | VLAN 72, `192.168.72.2/24`, gateway/DNS `.72.1` |
| UniFi custom policies | 32 enabled; seven Security-A policies active; old and temporary policies absent |
| Galaxy firewall | `.72.2/32` allowed to TCP 9100/8006; broad VLAN 70 TCP 9100 removed; VLAN 70 TCP 8006 retained |
| WAN exposure | No new port forwards; the only listed port forward remained the disabled Valheim entry |
| SSH Manager | `security_01` and `splunk_siem` resolve directly to their VLAN 72 addresses |
| Ansible | Living inventory updated and graph validation passed |
| UniFi SIEM export | `192.168.72.3:1514`; fresh CEF event verified through SC4S/HEC into `netops` |

## Verification

| Check | Observed result |
|---|---|
| Proxmox NIC state | VM 109 and VM 200 show `tag=72`, original MACs, `vmbr0`, `firewall=1` |
| Guest addressing | QEMU guest agent and SSH both report `.72.3` and `.72.2`, default route via `.72.1` |
| Splunk/SC4S | Services active; 1514 TCP/UDP, 8000, 8088, 8089 listening; HEC HTTPS health 200 |
| Wazuh/monitoring services | Wazuh units active; Grafana, Prometheus, PVE exporter containers up |
| Internal UIs | Wazuh 302; Grafana 302; Prometheus 302; Splunk 303 |
| DMZ/Proxmox paths | `edge-01:9100`, `grey-server:9100`, and `grey-server:8006` returned 200 |
| Egress policy | HTTP and HTTPS 200; both guests showed live NTP sources/synchronization; external TCP/53 timed out; the catch-all policies have controller logging enabled |
| Firewall cleanup | Old UniFi policies and old Galaxy TCP 9100 subnet accept absent |
| Proxmox firewall | `Status: enabled/running` |
| WAN inbound | No Security-A port forward or external-to-Security allow created |
| UniFi feed | SC4S CEF source processed one fresh event at 22:40:27; Splunk indexed one `netops` event at 22:40:43 |

## Rollback Points

- VM 109 NetworkManager backup: `/root/security-a-migration-20260712-213903`.
- VM 200 netplan backup: `/root/security-a-migration-20260713-014435`.
- Galaxy firewall backups: `/root/cluster.fw.bak.security-a-20260712-213729` and `/root/cluster.fw.bak.security-a-cleanup-20260712-215806`.
- Ansible inventory backup: `/home/ansible/ansible/inventory/hosts.ini.bak.security-a-20260712-215740`.
- A guest rollback consists of restoring its saved in-guest configuration, retagging its NIC to VLAN 70 with the original MAC/bridge/firewall fields, and restoring the relevant old UniFi/Galaxy rules before reboot and verification.

## Deferred Follow-Ups

- Audit/repoint/enroll the intended Wazuh agents. The manager showed only `edge-01` and `wp-01` active at cutover time; I deferred the agent work.
- Install/configure `node_exporter` on `purple-server`, `blue-server`, and `red-server`, then add their targets if desired.
- Remove or correct stale Prometheus targets for `app-01`, old `security-01` address `192.168.70.20`, and offline `supabase-01`.
- Review the retained Galaxy TCP 8006 accept from `192.168.70.0/24` during MGMT-A lockdown.

No availability or security incident occurred. The EFI variable pseudo-filesystem on `security-01` reported 88% used in the generic health check, but the root filesystem was 29% used and all workload validation passed.
