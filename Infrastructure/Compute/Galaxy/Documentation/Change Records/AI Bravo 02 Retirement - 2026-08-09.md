# AI Bravo 02 Retirement

**Created:** 2026-08-09  
**Last updated:** 2026-08-09  
**Status:** Complete

## Outcome

I retired Galaxy LXC 105 `ai-bravo-02` early on 2026-08-09. I deleted the stopped guest and its 100 GiB `ssd-lvm1` root volume, removed the durable SSH Manager definition and generated documentation host page, and confirmed there was no matching live UniFi, automation, monitoring, Wazuh, or local SSH dependency. I preserved the final guest configuration and the TNIO/OpenClaw-backed source, tests, configuration, walkthrough, diagrams, and dated records in the archive.

## Starting State and Archive Gate

CT 105 was stopped on `grey-server` with `onboot: 0`. Its root volume was `ssd-lvm1:vm-105-disk-0,size=100G`; it was unprivileged and carried seven NVIDIA device mappings. I read the [retired guest record](../../../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md), the [TNIO platform archive](../../../../../Archive/Platforms/TNIO%20AI%20Bot/README.md), the [TNIO walkthrough](../../../../../Archive/Guides/TNIO-AI-Bot.md), the [OpenClaw walkthrough](../../../../../Archive/Guides/OpenClaw.md), and both archived diagram sources before deletion.

The archive contains the TNIO primary, remote, experimental, and legacy source snapshots; evaluation tests; runtime configuration; evidence; generated artifacts; product description; dated accuracy work; and the OpenClaw-backed inference records referenced by the deployed fixes. The diagrams remained readable from their Excalidraw sources. This preserved operational history is not a guest backup.

## Backup and Dependency Check

Proxmox held no CT snapshot, HA resource, replication job, configured backup, or matching backup file on `local` or `hddpool-1`. I found no retained external backup, so there is no restorable copy of the guest or its root filesystem.

UniFi held no client history for the hostname or address and no matching fixed address, DHCP reservation, local DNS record, firewall group or policy target, client group, content filter, ACL, on-off-network policy, or traffic route. The Ansible controller, monitoring host, and Wazuh manager held no active hostname or address reference. Local SSH configuration and known-host files held no entry.

## Deletion

I guarded the destructive command on all three expected conditions: the guest had to be stopped, `onboot` had to equal `0`, and the rootfs line had to exactly match `ssd-lvm1:vm-105-disk-0,size=100G`. I then ran:

```sh
pct destroy 105 --purge 1 --destroy-unreferenced-disks 1
```

Proxmox reported that it removed logical volume `vm-105-disk-0` and purged CT 105 from related configurations. The [redacted deletion evidence](../../Evidence/AI%20Bravo%2002%20Retirement%20-%202026-08-09/Logs/S01-CT-105-Deletion-2026-08-09.txt) records the guard, command, output, and post-deletion checks.

## External Cleanup

I removed the exact `ai_bravo_02` block from SSH Manager's durable environment file. The currently running manager process still exposes its startup-time cached copy until that process restarts, but the durable source is gone. There is no alias, group membership, active session, tunnel, or pooled connection for the retired server.

The documentation site had a generated host page and stale stopped-guest references even though its repository subtree is intentionally local-only. I removed CT 105 from the private fleet snapshot, removed the generated host page, changed the operations copy to a retirement retrospective, regenerated the host index at 16 active guests and two templates, rebuilt the site, synchronized it to `docker-main`, and recreated its container.

## Verification

- `pct status 105` failed because the configuration no longer exists.
- The cluster resource list, Proxmox configuration tree, and `ssd-lvm1` volume list contain no CT 105 entry.
- Galaxy remained quorate with five votes.
- `ssd-lvm1` allocation fell from 15.72 percent before deletion to 13.05 percent afterward.
- The live documentation container returned healthy, `/healthz` returned `ok`, the host index omitted `ai-bravo-02`, and the retired host route returned HTTP `404`.
- The active inventory and backlogs no longer describe CT 105 as stopped or scheduled for deletion.

## Recovery and Remaining Work

Deletion was intentional and no restorable backup exists. Recovery would require rebuilding a new guest from the archived source and records. No retirement work remains. Restarting the SSH Manager process will discard its harmless startup-time cached server definition.
