# Galaxy Green Node Rolling Replacement

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Implementation date:** Not implemented  
**Status:** Cancelled 2026-07-31; archived unexecuted  
**Replacement:** `green-server` to `green-node`, abandoned  
**Parent plan:** [Galaxy Cluster Node Rename Rolling Replacement Plan](../Change%20Plans/Galaxy%20Cluster%20Node%20Rename%20Rolling%20Replacement%20Plan%20-%202026-07-31.md)

## Cancellation

I cancelled the rename on 2026-07-31 and kept `green-server`. Only step 2 of the sequence below ever ran: I changed the PXE machine registry to `green-node`, ran the 21 tests, and deployed. I reverted that same day, so `/etc/galaxy-pxe/machines.json` reads `green-server` again with `nvme0n1` as the only install disk, both services are active, and `/health` returns `ok`. Green never rebooted, never left the cluster, and its PXE state file still holds the original `complete` record for attempt `60d0f991` with `fqdn: green-server.galaxy`.

Bane port 4 stayed on `Proxmox-Trunk` the whole time, so step 3 never happened and no switch configuration changed. The starting state below is a read-only preflight and remains an accurate 2026-07-31 snapshot of Green.

## Scope

I will use Green as the guest-free pilot for the five-node naming migration. This is a node replacement, not an in-place hostname edit. I will power off the old installation, remove `green-server` from Galaxy, reinstall the same physical M920q through the repaired PXE path with hostname `green-node`, and rejoin it at the existing management and Cluster-Net addresses.

The old installation must never boot on Galaxy after `pvecm delnode green-server`. If the replacement cannot join, the rollback is another fresh installation, not a hostname change on the removed system.

## Starting State

At 2026-07-31 10:36 EDT, Galaxy reported five expected votes, five total votes, quorum 3, and `Quorate`. `green-server` was online as node ID 5. All seven required Proxmox and HA services were active on Green.

The Green guest directories contained zero VM or LXC configuration files. Local `qm list` and `pct list` returned no guests. Galaxy had no replication jobs. Green's HA LRM was idle, and the only managed services were CT 107 and CT 108 on Blue under `pin-blue-local-storage`.

No storage definition, HA rule, backup job, replication job, mapping, SDN configuration, or ACL depended on `green-server`. The operational exact-name references were its Corosync member and a descriptive comment in `cluster.fw`. The HA manager-status cache also reported Green online, which is expected while the old member exists.

Green's Proxmox installation uses `/dev/nvme0n1`; `/dev/nvme0n1p3` is its only LVM PV. The separate Hitachi `/dev/sda` is blank, failed its extended SMART test, and is not an installation or storage target.

[S01](../../Evidence/Galaxy%20Green%20Node%20Rolling%20Replacement%20-%202026-07-31/Logs/S01%20Green%20Replacement%20Preflight%20-%202026-07-31.md) records the live gate.

## Execution Sequence

1. Finish the running Blue extended SMART test and commit the five-node hardware checkpoint.
2. Change Green's ignored PXE machine record from `green-server` to `green-node`, retain `nvme0n1` as the only install disk, run all tests, and deploy the idempotent project to `ansible-01`.
3. Preview the Bane port 4 change from `Proxmox-Trunk` to `Server-Provision`, obtain confirmation, apply it, and verify tagged VLANs 70 and 71 remain admitted.
4. Rearm Green's completed PXE identity with `ready --force`, set UEFI BootNext to its IPv4 PXE entry, and restart the old guest-free node.
5. Wait for the PXE service to record `installer_claimed`, then prove the old OS no longer answers on either Corosync address.
6. From a healthy remaining member, require four online votes and quorum, run `pvecm delnode green-server`, and verify the old name is absent from membership and `corosync.conf`.
7. Let the automatic installation write only `/dev/nvme0n1`, join as `green-node` with both Corosync links, and reach PXE state `complete`.
8. Return Bane port 4 to `Proxmox-Trunk`, verify the five-node acceptance gate, update active monitoring and automation labels, and remove only proven old-member residue.

## Stop Conditions

I will stop before the removal boundary if another Galaxy member becomes unhealthy, quorum or a Corosync link degrades, Green gains a guest, a new operational dependency appears, the PXE registry names the wrong disk, or the switch profile preview differs from the intended single-port change.

After `pvecm delnode`, I will keep workloads away from the replacement until five-node quorum, both links, local storage, services, certificates, SSH, node exporter, SMART metrics, and the exact-name residue scan all pass.

## Result

Cancelled. The read-only preflight passed, the PXE registry edit was reverted, and `green-server` remains online at node ID 5 with both Corosync links and zero guests. Galaxy reports five expected votes, five total votes, and `Quorate`.
