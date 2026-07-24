# Purple NVMe Reliability Failure

**Created:** 2026-07-22  
**Last updated:** 2026-07-24

**Investigated:** 2026-07-22  
**Owner:** Galaxy / `purple-server`  
**Status:** Open; failed device retained. Purple is guest-free again after the 2026-07-23 Kasm teardown removed `kasm-agent-01` and `inetsim-01`.

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

## Required correction and verification

I still need to replace Purple's NVMe. A replacement must pass its full SMART health check before I recreate local storage or call the hardware issue resolved. I will then verify the installed Proxmox package set, kernel, bridges, storage, Corosync membership, HA heartbeat, and a controlled reboot.

Until replacement, I will watch for an increase from zero media errors, NVMe controller resets, I/O errors, filesystem errors, or Corosync instability. Any of those findings stops new placement and returns the issue to a hard blocker.

## Healthy canary state retained

The package update itself completed. Purple runs `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve`, has no packages pending, and reports the six checked Proxmox, HA, and Corosync services active. Galaxy remained quorate with four votes, quorum three, HA master on Red, and fencing armed.

The post-update verification captured the exact command, standard output, and exit code. That transcript lived in the Kasm deployment evidence, which I removed from the repository on 2026-07-23; a copy is retained in the cleanup backup outside the repository.

## Related records

- [Kasm lab network simplification (2026-07-23)](../../../../Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)

I removed the earlier Kasm preflight and deployment records from the repository on 2026-07-23 while rebuilding Kasm from scratch. The failed NVMe is a hardware issue independent of that work.
