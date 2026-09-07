# Galaxy TODO

**Created:** 2026-07-14  
**Last updated:** 2026-09-07

This backlog retains completed Green recovery and Purple storage work. Its open items are the root SSH setting on Purple and Blue, and the scope of the PXE join key. The root [TODO](../../../../TODO.md) links here without copying detailed implementation steps.

## Scope of the `galaxy-pxe-join` Key

**Status:** Open, found 2026-08-15 while repairing Grey's root key file  
**Troubleshooting record:** [Broken Node Shell and Standalone authorized_keys on grey-server](Troubleshooting/Broken%20Node%20Shell%20and%20Standalone%20authorized_keys%20on%20grey-server%20-%202026-08-15.md)

- [ ] Decide whether `galaxy-pxe-join` stays trusted for root on all five nodes or is re-scoped to `grey-server` alone. On 2026-07-31 that key was trusted on Grey only, and [Galaxy Artifact Cleanup and Green SSH Parity](../../../../Operations/Maintenance/Galaxy%20Artifact%20Cleanup%20and%20Green%20SSH%20Parity%20-%202026-07-31.md) records the standalone `authorized_keys` on Grey as the mechanism that kept it that way, calling a widening to five nodes a downgrade. The key was already in `/etc/pve/priv/authorized_keys` before the 2026-08-15 repair, so it reached all five nodes while the file that was supposed to scope it had stopped doing so. Symlinking Grey's file on 2026-08-15 removed that mechanism for good. Its private half is what lets a newly installed node run `pvecm add --use_ssh`, and `cluster_peer: 192.168.70.10` in the PXE registry means only Grey needs to accept it. Re-scoping it means holding it outside the cluster-backed file, which is the arrangement that just caused a silent divergence, so the decision is which of the two costs to carry.

## Root SSH Setting Split Across the Nodes

**Status:** Open, found 2026-08-15 while resetting the node root passwords  
**Change record:** [Node Root Password Reset](Change%20Records/Node%20Root%20Password%20Reset%20-%202026-08-15.md)

- [x] 2026-09-07: `purple-server` and `blue-server` moved from `PermitRootLogin yes` to `prohibit-password`, so all five nodes resolve `without-password`. One line each, `sshd -t` clean, restart clean, fresh root login proven. [PermitRootLogin Aligned on purple-server and blue-server](Change%20Records/PermitRootLogin%20Aligned%20on%20purple-server%20and%20blue-server%20-%202026-09-07.md).

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

## `purple-server` Boot NVMe Replaced

**Status:** Hardware issue closed 2026-07-25. A Toshiba THNSF5256GPUK cloned from the failing Samsung is Purple's boot device, health `PASSED`, and Galaxy is back to four of four votes.  
**Change record:** [Purple Boot NVMe Replacement](Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md)  
**Troubleshooting record:** [Purple NVMe Reliability Failure](Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md)

- [x] Take Purple offline for the NVMe replacement. Done 2026-07-24. Corosync showed nodeid 2 `disconnected` on both links, consistent with a powered-down node.
- [x] Avoid taking Grey, Blue, or Red offline until Purple rejoins. Held for the whole 19-hour-33-minute window; Purple rejoined at `07:19:56 EDT` on 2026-07-25 and the cluster is back to four votes.
- [x] Reassess the remaining rolling reboot order after the failed-device risk is removed or explicitly accepted.
- [x] After replacement, verify storage, Proxmox VE 9.2.5, kernel, bridges, Corosync, HA, and a controlled reboot. The cold boot off the cloned drive is the reboot check: `local` and `local-lvm` active, `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve` with nothing pending, both rings connected, all seven units active, fencing armed.
- [x] Keep the Samsung SSD 850 EVO 250 GB installed permanently and use it as ordinary Proxmox storage for VM disks and LXC root volumes. I made that role decision on 2026-07-27.
- [x] Create `ssd-lvm2` as LVM-thin on the Samsung 850 EVO, restrict it to `purple-server`, enable VM image and LXC root-directory content, and verify it with a real guest disk. I completed this on 2026-07-28. The pool returned to 0.00 percent used after I retired its first workload on 2026-08-19. The unchanged [SMART capture](../../../Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt) reports zero reallocated, CRC, and uncorrectable errors.

## `green-server` Cross-Process Faults and Status Loss

**Status:** Closed 2026-08-09 after service recovery and a controlled reboot. I am not running the offline Memtest86+ pass the record names as its next conclusive step, so Green's hardware cause stays unproven rather than ruled out  
**Troubleshooting record:** [Status Unknown and Cross-Process Faults](Troubleshooting/Status%20Unknown%20and%20Cross-Process%20Faults%20on%20green-server%20-%202026-08-09.md)

- [x] Confirm the `unknown` status with a cluster-side pass/fail loop. `pvestatd` had aborted and stayed failed because its unit has `Restart=no`.
- [x] Separate the status symptom from the broader host fault. The same boot recorded 37 faults across Python, PHP, Perl, and `pve-firewall`; the other four matching nodes recorded none.
- [x] Verify package files, storage health, OOM state, machine-check reporting, Corosync, quorum, and the unaffected Proxmox services. None exposed a package, disk, or cluster-network cause.
- [x] Run a bounded online memory test without stopping CT 123. Two locked 1 GiB passes completed with exit status 0, no new kernel fault, no swap pressure, and no guest interruption.
- [x] Compile the firewall, restart `pvestatd` and `pve-firewall`, and verify the original cluster-status loop changed from `unknown` to `online`.
- [x] Reboot Green normally and verify CT 123 returned, all status and firewall daemons stayed active, and a 12-sample burn-in kept the new boot at zero faults.
