# Purple NVMe Reliability Failure

**Created:** 2026-07-22  
**Last updated:** 2026-07-25

**Investigated:** 2026-07-22  
**Resolved:** 2026-07-25  
**Owner:** Galaxy / `purple-server`  
**Status:** Resolved. I replaced the failed boot NVMe with a Toshiba THNSF5256GPUK on 2026-07-25, cloned from the failing drive with Clonezilla. The new device reports overall health `PASSED`, and Purple is back to a full four votes. The work is written up in [Purple Boot NVMe Replacement](../Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

## Symptom and impact

After I updated and rebooted guest-free `purple-server` as the Proxmox 9.2.5 canary, `smartd` reported NVMe critical warning `0x04`. A direct `smartctl -x /dev/nvme0` check returned `SMART overall-health self-assessment test result: FAILED!` and stated that the NVM subsystem reliability had degraded.

Purple remains online and casts one of Galaxy's four votes. Its Proxmox services and HA daemons are active, and its local thin pool holds no guest volume. I have not observed a media or data-integrity error. That does not make the device healthy. I will not place `kasm-agent-01`, `inetsim-01`, or another workload on Purple while this warning remains.

I also paused the remaining rolling node reboots. With Purple operating on a failed boot device, taking another node offline would leave only two dependable votes if Purple failed during that window. Galaxy requires three votes for quorum.

## Tests and finding

At `2026-07-22T21:49:04-04:00`, Purple reported:

- Samsung `MZVLB256HAHQ-000L7`, 256 GB
- SMART overall health `FAILED`
- NVMe critical warning `0x04`, reliability degraded
- `Percentage Used: 169%`
- 49,369 power-on hours and 105 TB written
- zero media and data-integrity errors
- 2,462 error-log entries for an invalid-field command
- 38 C controller temperature

The 169% endurance reading and reliability warning are the finding. The zero media-error count does not override the device's failed health assessment.

A dated `smartctl -a` capture from [2026-07-24](../../../../Hardware/Components/Drives/NVMe/smartctl-a_MZVLB256HAHQ_5659_2026-07-24.txt) is stored in the drive inventory and returns the same failed health state. The 2026-07-22 22:10 EDT recapture returned that state as well.

I compared the boot NVMe on Grey, Blue, and Red. Each reported overall health `PASSED`, critical warning `0x00`, and zero media/data-integrity errors. Their percentage-used readings were 2%, 9%, and 7%, respectively. The fault is isolated to Purple's boot NVMe rather than a cluster-wide smartmontools interpretation.

## Current containment

- I left Purple online for quorum and HA visibility.
- I kept Purple guest-free and did not create either planned Kasm workload there.
- I paused the remaining Proxmox package upgrades and reboots.
- I did not run a destructive NVMe test, reformat the device, or change Purple's storage.

## Risk acceptance

On 2026-07-23, I chose to place `kasm-agent-01` and `inetsim-01` on Purple despite the failed SMART result. I also allowed the one-node-at-a-time Proxmox maintenance to resume. This accepts loss of those two guests, interruption of their services, and the quorum exposure described above if Purple fails while another node is offline.

The acceptance does not change the hardware result. A fresh `smartctl -H -A /dev/nvme0` check still returned overall health `FAILED`, critical warning `0x04`, 169% endurance used, zero media errors, and 36 C. Replacement remains the required hardware correction.

## Short self-test, 2026-07-24

On 2026-07-24 I ran a SMART short self-test (`smartctl -t short /dev/nvme0`) on Purple's boot NVMe. It logged `Completed: failed segments` at 49,373 power-on hours (NSID 1, segment 2). That is the first self-test failure recorded on the device; the 2026-07-22 captures logged no self-test at all. Overall health still reads `FAILED`, critical warning `0x04`, endurance 169% used, and zero media/data-integrity errors. The full transcript is the capture linked above.

I ran the same short test on the other six physical drives in Galaxy the same day. Grey's Crucial CT1000P310SSD8 NVMe (2% used), Blue's Samsung MZVLW256HEHP-000L7 NVMe (9% used), Red's Samsung MZVLB256HAHQ-000L7 NVMe (7% used), Grey's Crucial BX500 SATA SSD, Grey's Toshiba DT01ACA200 HDD, and Red's Seagate ST1000LM035 HDD each completed without error and report overall health `PASSED`. The full sweep and per-drive transcripts are recorded in the [drive inventory](../../../../Hardware/Components/Drives/README.md). Purple remains the only failed device.

## Replacement window opened 2026-07-24

I took Purple offline on 2026-07-24 to replace the drive. `pvecm nodes` on Grey then listed three members (nodeids 1, 3, 4) & `pvesh get /cluster/resources` reported `purple-server offline`. Corosync showed nodeid 2 `disconnected` on `LINK ID 0` (`192.168.70.10`) and `LINK ID 1` (`192.168.71.10`), which matches a powered-down node rather than a broken link.

Galaxy stayed quorate at three total votes against expected votes of four, with quorum needing three. That left no spare vote: taking Grey, Blue, or Red offline during the window would have made the cluster inquorate. I deployed `kasm-01` on Grey during the same window, which added no node restarts.

The window closed on 2026-07-25 at `07:19:56 EDT`. `last` records Purple as powered off for 19 hours 33 minutes, from `2026-07-24 11:46:33 EDT`. The swap and clone took about an hour of that; the rest is the node sitting down between the shutdown and the refit. No guest was affected, since Purple carried none.

## Correction, 2026-07-25

I replaced the drive. The failing Samsung came out, a Toshiba THNSF5256GPUK (`****TALT`) cloned from it with Clonezilla went in, and Purple booted off the clone at `2026-07-25 07:19:56 EDT`. I cloned rather than reinstalled, so the node kept its identity and needed no `pvecm add`, no reissued certificates, and no HA reconfiguration. Cluster config version stayed at 8. I added a Samsung SSD 850 EVO 250 GB on SATA during the same window; it has no role yet.

The new device passes every check the correction called for. `smartctl -a /dev/nvme0` returns overall health `PASSED`, critical warning `0x00`, 30% endurance used, available spare 100%, 23,148 power-on hours, zero media and data-integrity errors, and zero error-log entries against the old drive's 2,462. A `smartctl -t short` run logged `Completed without error` at 23,148 hours, where the old drive had failed the same test at 49,373. The capture is stored at [smartctl-a_THNSF5256GPUK_TALT_2026-07-25.txt](../../../../Hardware/Components/Drives/NVMe/smartctl-a_THNSF5256GPUK_TALT_2026-07-25.txt).

The rest of the node checks out too. Purple runs `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve` with nothing pending from apt, both Corosync rings connected on `192.168.70.11` and `192.168.71.11`, all seven Proxmox and HA units active, `local` and `local-lvm` active with the cloned LVM layout intact, and `ha-manager status` reporting quorum OK with fencing armed. `pvecm status` reports Quorate Yes at four of four votes. The cold boot off the new drive logged no I/O error, controller reset, or filesystem repair. Full detail and evidence are in the [change record](../Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

## What I'm still watching

The Toshiba is a used spare, not a new drive: 30% endurance used, 23,148 power-on hours, 36.8 TB written. That buys years, not permanence. I'm watching its endurance counter along with media errors, controller resets, I/O errors, filesystem errors, and Corosync stability, the same signals I watched on the drive it replaced.

## Healthy canary state retained

The package update itself completed. Purple runs `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve`, has no packages pending, and reports the six checked Proxmox, HA, and Corosync services active. Galaxy remained quorate with four votes, quorum three, HA master on Red, and fencing armed.

The post-update verification captured the exact command, standard output, and exit code. That transcript lived in the Kasm deployment evidence, which I removed from the repository on 2026-07-23; a copy is retained in the cleanup backup outside the repository.

## Related records

- [Purple Boot NVMe Replacement (2026-07-25)](../Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md), the change record that closes this issue
- [Drive Inventory](../../../../Hardware/Components/Drives/README.md), which holds the retired Samsung and the new boot drive
- [Kasm lab network simplification (2026-07-23)](../../../../Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)

I removed the earlier Kasm preflight and deployment records from the repository on 2026-07-23 while rebuilding Kasm from scratch. The failed NVMe is a hardware issue independent of that work.
