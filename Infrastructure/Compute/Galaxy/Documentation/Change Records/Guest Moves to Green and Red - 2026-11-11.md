# Guest Moves to Green and Red

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Change date:** 2026-11-11  
**Target:** VM 301 `HQ-DC01` and VM 200 `security-01` to `green-server`; VM 112 `hermes-01` to `red-server`

## Outcome

I moved three guests off `grey-server`, which carried every guest in the identity, security and assistant roles.

| VM | From | To | State after | Downtime |
|---|---|---|---|---|
| 112 `hermes-01` | Grey `ssd-lvm1` | Red `local-lvm` | stopped, as before | none, it was stopped |
| 301 `HQ-DC01` | Grey `ssd-lvm1` | Green `local-lvm` | running | 3:52 to 4:01 PM |
| 200 `security-01` | Grey `ssd-lvm1` | Green `local-lvm` | running | 4:04 to about 4:15 PM; dashboard at 4:17 PM |

`HQ-DC01` and `HQ-DC02` now sit on different nodes, so Active Directory survives the loss of either Grey or Green while both run. `security-01` and `splunk-siem` also sit on different nodes. I kept `splunk-siem`, `HQ-MGT01` and `HQ-WS001` on Grey: Splunk needs 6 vCPU, which is every core on Green or Red, and the other two are usually stopped, so moving them frees nothing.

| Node | Memory in use before | After |
|---|---|---|
| `grey-server` | 39.2 of 62.7 GiB | 27.0 of 62.7 GiB |
| `green-server` | 1.9 of 15.5 GiB | 12.5 of 15.5 GiB |
| `red-server` | 3.1 of 15.5 GiB | 3.1 of 15.5 GiB, `hermes-01` stopped |

## Checks before the moves

- Green and Red run PVE 9.2.26, the same as Grey, and both bridge `vmbr0` VLAN-aware with `bridge-vids 2-4094`.
- A passive capture on each node's `nic0` (`tcpdump -c 3 'vlan N'`, counting packets only) saw tagged traffic for VLANs 65, 72 and 80 on both Green and Red within seconds, so the switch passes all three to them.
- Green's `local-lvm` was empty, 141.2 GiB. Red's held 45 GiB of CT 842 `media-01`.
- None of the three VMs had a snapshot, an HA resource, a per-VM firewall file, an `args` line, a hookscript or SMBIOS overrides. `HQ-DC01`'s licence reads `Licensed`, channel `OEM:DM`; Grey exposes no MSDM table, so nothing ties the activation to Grey's firmware.
- `datacenter.cfg` sets no migration network, so the copies ran over MGMT-A.

## Change

Every VM uses `cpu: host`, and Grey is AMD while Green and Red are Intel, so these were offline moves: shut down, then `qm migrate <vmid> <node> --targetstorage local-lvm`. Each disk streamed its full virtual size over 1 GbE at about 116 MB/s and landed thin on the target.

| VM | Migration | Duration | Disk allocated on the target |
|---|---|---|---|
| `hermes-01` | 3:42 PM | 9 min 16 s | 9.20% of 60G |
| `HQ-DC01` | 3:52 PM | 7 min 29 s, with its EFI vars and TPM state | 45.12% of 48G |
| `security-01` | 4:04 PM | 9 min 53 s | 40.07% of 64G after `fstrim` released 33 GiB |

I started `HQ-DC02` at 3:43 PM so the domain had a controller while `HQ-DC01` was down. Before the shutdown it had replicated every naming context from `HQ-DC01` with no failures. I shut it down again at 4:03 PM once replication had converged.

Proxmox warned on Red that its thin volumes now total 160 GiB against a 141 GiB pool (`media-01` 100G plus `hermes-01` 60G). The allocated total is 35.76% of the pool.

## Verification

`HQ-DC01` on Green, from 4:01 PM:

- `Get-CimInstance Win32_Processor` reads `Intel(R) Core(TM) i5-8500T`, and the licence still reads `LicenseStatus=1`, channel `OEM:DM`.
- `w32tm /query /source` still reads `time.cloudflare.com,0x8`, and `netdom query fsmo` still names `HQ-DC01` for every role.
- NTDS, DNS, Netlogon, KDC, W32Time and DFSR running. `dcdiag /q` for Services, Advertising, FsmoCheck, NetLogons, SysVolCheck, Replications and KnowsOfRoleHolders printed nothing.
- Inbound replication from `HQ-DC02`: all five naming contexts, 0 failures, at 4:01 PM.
- Disk 0 healthy at 48 GiB, `Repair-Volume -Scan` `NoErrorsFound`, WinRE enabled, no storage errors since boot.
- Over SSH it answered on `192.168.65.10`, resolved `hq-dc02.ad.alphasecunited.com` and reached `192.168.65.1`.

On `HQ-DC02`, the Configuration, Schema and ForestDnsZones partitions each showed one failure from the window when `HQ-DC01` was off (error 1722, `The RPC server is unavailable`, 3:59 to 4:00 PM). Those partitions replicate only on change. `repadmin /syncall /A /e /d` returned `SyncAll terminated with no errors`, and all five then read 0 failures with a last success at 4:03:36 PM.

`security-01` on Green, from 4:15 PM:

- `/proc/cpuinfo` reads the i5-8500T. `/` is 62G with 29G used. No ext4 or I/O errors in `dmesg`, and `systemctl --failed` empty.
- `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard` and `filebeat` active, and 15 agents active, the same count as before.
- `hawser`, `cadvisor` and `wazuh-mcp-server` healthy. `SplunkForwarder` running with two connections to port 9997.
- The dashboard returned `503` until about 4:17 PM, then `302` to its login page. OpenSearch Dashboards took about three minutes to start on the i5.
- Prometheus on `monitor-01` reports `up` 1 for `192.168.72.2:9100` and `192.168.72.2:9101`.

`hermes-01` on Red: `qm config 112` shows both volumes on `local-lvm`, the NIC on VLAN 80 with the firewall on, and the VM stopped. I did not boot it.

The cluster readback after the last check placed VMs 200 and 301 on `green-server`, VM 112 on `red-server` and VM 302 stopped on Grey. Grey's `ssd-lvm1` was 8.74% used, Green's `local-lvm` 33.49% and Red's 35.76%.

I updated the [VM inventory](../../../../../Operations/Inventory/Galaxy/VMs.md), [Galaxy inventory](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md), [services](../../../../../Operations/Inventory/Galaxy/Services.md), [node record](../../../../Hardware/Nodes.md), the Galaxy, Wazuh, Hermes Agent and Active Directory READMEs, the UniFi [networks page](../../../../Network/UniFi/Configuration/network-vlan.md), and six diagrams (`galaxy-cluster`, `homelab-overview`, `lab-map`, `wazuh`, `ansible-automation`, `ssh-key-lifecycle`). The diagrams also had Green at 7.60 GiB with one module and an empty pool; it has had 15.46 GiB since 2026-11-09.

## Findings

- **Green is not on a UPS.** The [power record](../../../../Hardware/Power.md) puts `grey-server`, `blue-server`, `red-server`, the gateway, the switch and the ONT on `UPS-02`, and nothing of Green's. `HQ-DC01`, which holds every FSMO role and is the domain's time source, and `security-01` now go down with the first power cut, while Grey rides it out. `UPS-02` read 19% load on 2026-08-31.
- **Neither VM starts on its own.** `HQ-DC01` and `security-01` have no `onboot` setting, the same as on Grey, so a Green reboot leaves both off until started by hand.

## Open items

- Put `green-server` on `UPS-02`, or decide the two guests stay where an outage takes them down.
- Decide whether `HQ-DC01` and `security-01` get `onboot: 1`, and whether `HQ-DC02` runs permanently so the split DCs protect the domain.
