# Galaxy Inventory Post-Staleness Audit Snapshot

**Created:** 2026-08-03  
**Last updated:** 2026-08-03  
**Snapshot date:** 2026-08-03

I captured this set after checking all five Proxmox nodes, the cluster guest list, and the living service records. Every node reports `pve-manager/9.2.6`, kernel `7.0.14-8-pve`, and its lowercase `.galaxy` FQDN. The cluster API returned 19 guest records, 12 running. The service snapshot maps 13 workload guests; VM 102's display name and guest hostname are both `debian-dev`.

Node hardware, QEMU allocation, and LXC allocation did not change during the audit, so this set reuses the latest verified configuration snapshots. The workload record is new.

| File | Contents |
| --- | --- |
| [Nodes Post-Green Expansion - 2026-07-31.md](Nodes%20Post-Green%20Expansion%20-%202026-07-31.md) | Five-node Proxmox hardware and physical-storage snapshot |
| [VMs Post-Parrot - 2026-07-30.md](VMs%20Post-Parrot%20-%202026-07-30.md) | QEMU VM and template configuration snapshot |
| [LXCs Post-Parrot - 2026-07-30.md](LXCs%20Post-Parrot%20-%202026-07-30.md) | LXC configuration snapshot |
| [Services Post-Staleness Audit - 2026-08-03.md](Services%20Post-Staleness%20Audit%20-%202026-08-03.md) | Complete current workload snapshot, including service versions, 49 Prometheus targets, 14 active Wazuh agents, media-path verification, and exporter coverage |
