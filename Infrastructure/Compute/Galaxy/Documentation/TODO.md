# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-08-01

This backlog contains the scheduled CT 105 deletion, Purple storage correction, the deferred `pvestatd` issue, & the accepted-risk cluster maintenance done during the earlier Kasm prep. The root [TODO](../../../../TODO.md) links here without copying detailed implementation steps.

## `green-server` PXE Expansion Complete

**Status:** Green joined Galaxy and reached PXE state `complete` at 2026-07-31 12:41:27 UTC  
**Change record:** [Galaxy PXE Provisioning Service](../../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)  
**Troubleshooting record:** [Green PXE Install Stalls Before Reboot](../../../../Platforms/Galaxy%20PXE/Documentation/Troubleshooting/Green%20PXE%20Install%20Stalls%20Before%20Reboot%20-%202026-07-31.md)

- [x] Build and validate the UEFI PXE service, Proxmox VE 9.2-1 assets, MAC-specific answer, and first-boot hook on `ansible-01`.
- [x] Add `192.168.70.14` to the Galaxy `pve_cluster` IP set and UniFi `OBJ-Proxmox-Nodes`.
- [x] Capture the first physical request through the installer answer and bootstrap fetch. Green did not reboot or join, and the old service could not identify the stopping phase.
- [x] Repair the lifecycle, installer webhook, SSH cluster join, root SSH baseline, storage checks, and failure telemetry. The deployed suite has 21 passing tests and the playbook reports `changed=0`.
- [x] Complete a disposable 12 GiB UEFI install through tagged VLAN 5. Proxmox reported only `/dev/sda` through the success webhook and powered the VM off.
- [x] Add and read back the UniFi callback policy from Green at `192.168.70.14` to `ansible-01` TCP 8080.
- [x] Add and read back the callback policy from `Server-Provision` to `ansible-01` TCP 8080.
- [x] Return Green to `disabled` after the repair.
- [x] Record that RAM capacity cannot be checked remotely, infer Secure Boot is off from the completed unsigned iPXE load, and rearm Green with `ready --force`.
- [x] Restart the M920q with UEFI PXE IPv4 first and complete the physical NVMe installation.
- [x] Verify `green-server` at `192.168.70.14`, Cluster-Net at `192.168.71.14`, five-vote quorum, both Corosync links, firewall state, node exporter, `local`, and `local-lvm`.
- [x] Prove the SATA disk was excluded from the installer and Proxmox storage.
- [x] Change Bane port 4 from `Server-Provision` to `Proxmox-Trunk` after MGMT-A reachability and cluster membership passed.
- [x] Apply the guarded subscription-popup script to all five nodes and add the same action to Galaxy PXE first boot.
- [x] Add Green to the Prometheus `node` job. All 49 targets and all 65 Grafana query assertions passed.
- [x] Capture Blue's completed extended SATA SMART result, reconcile its final blank-disk state, and roll the complete five-node hardware inventory forward. Blue's WDC passed at 23,215 power-on hours with all four critical counters at 0. Green's extended test failed with a read error, and I retained that result before wiping its unused SATA metadata.
- [x] Remove the stale deployment backups and bytecode caches from `ansible-01` after the reusable service passed all 21 tests. The legacy cluster-password file was already absent, and I retained the service, installer cache, assets, registry, state, and join-key machinery.
- [x] Remove Green's one-use first-boot script, log, and join-only SSH configuration. All three are gone, and replacing the join-only SSH config with the fleet standard also closed two parity gaps: Green now carries the same cipher restriction as the other four, and Grey's hand-maintained `authorized_keys` now holds Green's cluster root key. See [Galaxy Artifact Cleanup and Green SSH Parity](../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md).
- [x] Decide what to do about the empty `/etc/pve/priv/known_hosts` and per-node `ssh_known_hosts` files. I seeded them on 2026-08-01. There were three gaps, not one: the cluster store held a single line, the `/etc/ssh/ssh_known_hosts` symlink that reads it existed only on Grey, and every node's `/etc/hosts` carried nothing but its own entry. I wrote 15 key lines covering all five nodes under five name forms each, created the missing symlink on four nodes, and added peer host entries. All 20 ordered pairs verify by name and by IP under `StrictHostKeyChecking=yes`. See [Galaxy Cluster PVE 9.2.6 Upgrade and SSH Host Key Seeding](Change%20Records/Galaxy%20Cluster%20PVE%209.2.6%20Upgrade%20and%20SSH%20Host%20Key%20Seeding%20-%202026-08-01.md).
- [x] Reboot Green onto its installed kernel. Done 2026-08-01 as the first step of a five-node rolling upgrade. Green had been running the installer kernel `7.0.2-6-pve` with `7.0.14-8` unused on disk; all five nodes now run `7.0.14-8-pve` on `pve-manager/9.2.6` with nothing pending.
- [x] Decide the `*-server` to `*-node` rename. I cancelled it on 2026-07-31 and kept the current names. The [archived plan](../../../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Plans/Galaxy%20Cluster%20Node%20Rename%20Rolling%20Replacement%20Plan%20-%202026-07-31.md) records why: no shared storage means four of five nodes would need a backup and restore cycle to change a string.

## `grey-server` Identity and Leftover Cleanup

**Status:** Complete 2026-08-01. FQDN, search domain, certificate CN, kernels, & agent leftovers all resolved  
**Change record:** [Galaxy Cluster PVE 9.2.6 Upgrade and SSH Host Key Seeding](Change%20Records/Galaxy%20Cluster%20PVE%209.2.6%20Upgrade%20and%20SSH%20Host%20Key%20Seeding%20-%202026-08-01.md)

- [x] Make Grey's FQDN match the other four. Its `/etc/hosts` line now reads `192.168.70.10 grey-server.galaxy grey-server grey-server.local`, so `hostname -f` returns `grey-server.galaxy`. The short hostname is unchanged, so pmxcfs and Corosync identity are untouched. All 20 SSH pairs still verify and every node resolves all five `.galaxy` names.
- [x] Trim Grey's accumulated kernels. `apt-get autoremove` cleared `proxmox-kernel-6.17.13-19-pve-signed` & `proxmox-kernel-7.0.2-6-pve-signed`, leaving five installed and nothing further autoremovable. `/boot` is 94 GB at 37 percent, so this was tidiness rather than pressure.
- [x] Regenerate Grey's TLS certificate. Its CN was `grey-server.Grey` against `<node>.galaxy` on the other four. The `/etc/hosts` fix did not change it: Proxmox builds the CN from the search domain in `/etc/resolv.conf`, and Grey's read `search Grey`. I set it with `pvesh set /nodes/grey-server/dns --search galaxy --dns1 192.168.70.1`, passing the existing nameserver so the call wouldn't drop it, then ran `pvecm updatecerts --force` and restarted `pveproxy`. The CN is now `grey-server.galaxy` with matching SANs, all five nodes agree, and a cross-node API call between members succeeds. Both forced runs left the seeded `known_hosts` file at 15 lines.
- [x] Remove `/root/.claude`, `/root/.claude.json`, & `/root/.codex` from Grey, 282 MB in total. Nothing referenced them: no cron entry, no systemd unit, no running process, and the newest file in either tree dated to 2026-06-11. Grey was the only node carrying them; the other four and `ansible-01` were already clean. Done 2026-08-01.

## `ai-bravo-02` Deletion Scheduled

**Status:** Stopped, autostart disabled, & archived 2026-07-25  
**Deletion date:** 2026-08-15  
**Archive record:** [ai-bravo-02 Archived Guest](../../../../Archive/Operations/Inventory/Galaxy/AI%20Bravo%2002%20Archived%20Guest%20-%202026-07-25.md)

- [ ] On 2026-08-15, confirm CT 105 is still stopped & `onboot` remains `0`.
- [ ] Read the archived guest record, TNIO platform tree, walkthrough, & diagrams before deleting the guest.
- [ ] Identify any guest backup retained outside this repository & record its location or record that no restorable backup exists.
- [ ] Capture the final `pct config 105` output without private values, then delete CT 105 & its `ssd-lvm1:vm-105-disk-0` root volume.
- [ ] Confirm guest ID 105 & hostname `ai-bravo-02` are absent from cluster resources, configuration, storage, DNS, DHCP, SSH Manager, local SSH state, & active automation.
- [ ] Update the archive record from stopped & archived to deleted & retired, with the observed deletion result.

## `purple-server` Boot NVMe Replaced

**Status:** Hardware issue closed 2026-07-25. A Toshiba THNSF5256GPUK cloned from the failing Samsung is Purple's boot device, health `PASSED`, and Galaxy is back to four of four votes.  
**Change record:** [Purple Boot NVMe Replacement](Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md)  
**Troubleshooting record:** [Purple NVMe Reliability Failure](Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md)

- [x] Choose whether the failed device blocks Kasm placement. Moot after the 2026-07-23 teardown removed the Kasm guests from Purple.
- [x] Take Purple offline for the NVMe replacement. Done 2026-07-24. Corosync showed nodeid 2 `disconnected` on both links, consistent with a powered-down node.
- [x] Avoid taking Grey, Blue, or Red offline until Purple rejoins. Held for the whole 19-hour-33-minute window; Purple rejoined at `07:19:56 EDT` on 2026-07-25 and the cluster is back to four votes.
- [x] Reassess the remaining rolling reboot order after the failed-device risk is removed or explicitly accepted.
- [x] After replacement, verify storage, Proxmox VE 9.2.5, kernel, bridges, Corosync, HA, and a controlled reboot. The cold boot off the cloned drive is the reboot check: `local` and `local-lvm` active, `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve` with nothing pending, both rings connected, all seven units active, fencing armed.
- [ ] Watch the Toshiba's endurance counter along with media errors, filesystem errors, controller resets, and cluster stability. It's a used spare at 30% endurance used and 23,148 power-on hours, not a new drive, so plan its own replacement rather than treating this as permanent.
- [x] Keep the Samsung SSD 850 EVO 250 GB installed permanently and use it as ordinary Proxmox storage for VM disks and LXC root volumes. I made that role decision on 2026-07-27.
- [x] Create `ssd-lvm2` as LVM-thin on the Samsung 850 EVO, restrict it to `purple-server`, enable VM image and LXC root-directory content, and verify it with a real guest disk. I completed this on 2026-07-28 by migrating Kasm VM 122 onto the pool. The pool was active at 11.03 percent allocated after the move, the guest booted, all eight Kasm services ran, seven Docker health checks reported healthy, and the API health endpoint passed. The unchanged [SMART capture](../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt) reports zero reallocated, CRC, and uncorrectable errors.
- [ ] Monitor `ssd-lvm2` below the Kasm hard stop. A catalog-wide rolling-image refresh filled the pool on 2026-07-29, paused VM 122 with `io-error`, & caused Kasm's NPM route to return `502`. I enabled `discard=on`, removed both old snapshots, pruned unused Docker layers, disabled automatic workspace-image pulls, and installed Parrot by itself. The final readback was 68.25 percent with `baseline-parrot-2026-07-30` as the only snapshot. The [incident record](../../../../Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md) holds the timeline. Keep 80 percent as the hard stop and add an alert below it. Autoextend can't help because the volume group has 124 MB unallocated.
- [ ] Watch the 850 EVO's wear counters now that it carries a guest. It has absorbed 332 TB of host writes against a 75 TBW rating, and `Wear_Leveling_Count` normalized sits at 15 of 100 with raw 1801 average erase cycles. The baseline to compare against is that same 2026-07-28 capture. A non-zero `Reallocated_Sector_Ct`, a non-zero `CRC_Error_Count`, or a normalized wear value below 10 means move the pool rather than keep writing to it. Nothing irreplaceable lives there: the lab guest is rebuildable from the Kasm deployment record.

## Cluster Maintenance Done During Kasm Prep

**Status:** Complete. All four nodes run Proxmox VE 9.2.5. I removed the preflight change record from the repository on 2026-07-23 while rebuilding Kasm from scratch; a copy is in the cleanup backup outside the repository.

- [x] Capture and verify root-only Proxmox configuration archives on Grey, Purple, Blue, and Red.
- [x] Record that I waived the guest-backup target and accepted that the node-local configuration archives cannot restore guest disks.
- [x] Update guest-free Purple to Proxmox VE 9.2.5 and verify quorum, HA, services, storage, networking, and package state after reboot.
- [x] Resume and finish the one-node-at-a-time updates. Red, Grey, and Blue reached Proxmox VE 9.2.5 on 2026-07-23 after I accepted the Purple risk.

## `blue-server` Recurring `pvestatd` Crashes

**Status:** Deferred known issue  
**Priority:** Schedule with a maintenance window  
**Troubleshooting record:** [Recurring `pvestatd` failure on `blue-server`](Troubleshooting/Recurring%20pvestatd%20Failure%20on%20blue-server%20-%202026-07-13.md)

- [ ] Recheck service, cluster, kernel, & package state before recovery; retain the failure window and a core dump if one becomes available.
- [ ] Record the current Lenovo BIOS settings, confirm the M910q update and rollback procedure, & update BIOS from `M1AKT35A` during a maintenance window.
- [ ] Run an extended offline memory test after the firmware review; record per-pass results and any failing address or module information.
- [ ] If memory passes, run a fixed-duration CPU test plus storage health & integrity checks, then compare the results with the other Galaxy nodes.
- [ ] Restore `pvestatd`, verify node and resource status from a peer, & monitor for another crash beyond the prior failure window.
- [ ] After finding the root cause, decide whether a systemd restart policy should cover a later daemon crash.

A manual restart isn't resolution. Previous restarts restored status, then `pvestatd` failed again.
