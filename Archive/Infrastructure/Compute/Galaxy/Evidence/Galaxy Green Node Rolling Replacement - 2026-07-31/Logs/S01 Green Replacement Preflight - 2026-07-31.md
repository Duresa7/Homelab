# S01 Green Replacement Preflight

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Captured:** 2026-07-31 10:36 EDT  
**Observed from:** `grey-server` and key-only SSH to Green

## Membership and quorum

```text
Config Version: 9
Expected votes: 5
Total votes: 5
Quorum: 3
Flags: Quorate
Node ID 5: green-server
```

No QDevice was present.

## Workload and cluster dependencies

```text
Green VM and LXC configuration files: 0
Green qm list: no guests
Green pct list: no guests
Replication jobs: 0
HA status: quorum OK
Green HA LRM: idle
HA services: ct:107 and ct:108 on blue-server
HA rules: pin-blue-local-storage
```

The exact-name scan found `green-server` in `corosync.conf`, the current HA manager-status cache, and the Green address comment in `cluster.fw`. It found no Green selector in `storage.cfg`, HA rules, backup jobs, replication configuration, resource mappings, or SDN configuration.

## Green storage and services

```text
local: active
local-lvm: active
LVM PV: /dev/nvme0n1p3 in pve
/dev/nvme0n1: 238.5 GiB Samsung MZVLB256HAHQ-000L7
/dev/sda: 298.1 GiB Hitachi HTS723232A7A364
Required Proxmox and HA services active: 7 of 7
```

`/dev/sda` had no mount and no LVM or ZFS role. Its failed extended SMART result and blank metadata state are recorded under the hardware change. Green remained the correct guest-free pilot.
