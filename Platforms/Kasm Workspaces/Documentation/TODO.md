# Kasm Workspaces TODO

**Created:** 2026-07-29  
**Last updated:** 2026-08-01

This backlog holds Kasm-specific follow-up. The root [TODO](../../../TODO.md) links here; implementation detail stays in this file.

## Storage Recovery Before Workspace Expansion

**Status:** Parrot build complete; automated thin-pool alert open  
**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../../../Security/Incidents/Kasm%20Workspaces/Thin%20Pool%20Exhaustion%20-%202026-07-29.md)

- [x] Retain one local recovery snapshot. I removed both 2026-07-28 snapshots before the controlled Parrot pull, then created `baseline-parrot-2026-07-30` after the image, tiles, lanes, services, and storage passed. VM 122 has exactly one snapshot and no external guest backup.
- [x] Enable discard for VM 122 `scsi0`, complete a controlled reboot, run `fstrim`, & record the before-and-after thin-pool allocation. I enabled `discard=on` on 2026-07-29 without replacing the disk or changing either snapshot. `fstrim` submitted 72.7 GiB from `/`, while `ssd-lvm2` fell from 54.91 to 54.78 percent because the snapshots still reference most old blocks. Kasm returned with all health checks passing and the public route at HTTP `200`.
- [ ] Add monitoring that warns before `ssd-lvm2` reaches the existing 80 percent action threshold.
- [x] Recalculate the safe image-install gate from both guest free space and `ssd-lvm2` `data_percent`. I require the pool at or below 55 percent and at least 70 GB free in the guest before a new image, pull one name at a time, stop an unexpected queue before 70 percent, and keep 80 percent as the hard stop. The current 68.25 percent pool and 39 GB guest headroom fail the gate.
- [x] Retry Parrot under live pool monitoring. I pruned seven unused images, trimmed the guest, started at 51.46 percent pool use and 77 GB guest free, and pulled only Parrot. The verified image raised the pool to 67.44 percent and left 39 GB free.
- [x] Add Parrot Normal, VPN, and Full plus Debian Malware. All four lane tests passed on 2026-07-30, the API returned HTTP `200`, and [the change record](Change%20Records/Kasm%20Parrot%20Workspace%20Build-Out%20-%202026-07-30.md) holds the result.
- [x] Stop unattended rolling-image refreshes. I cleared the Docker Registry field on all Kasm image rows, restarted the agent, and observed no follow-on pull. Future image maintenance is manual and one image at a time.

## Session Limit Exemption Follow-Up

**Status:** Settings applied and verified; snapshot and reboot items open  
**Change record:** [Kasm Session Limit Exemption](Change%20Records/Kasm%20Session%20Limit%20Exemption%20-%202026-08-01.md)

- [ ] Replace `baseline-parrot-2026-07-30`. It predates the 2026-08-01 group-settings change, so a rollback reverts the exemption and restores the one-hour limit on my account. The documented practice is one baseline that contains the current settings, and replacing it needs the full lane and service checks plus the pool gate at or below 55 percent. The pool currently fails that gate.
- [x] Explain the VM 122 power cycle. Proxmox logged `qmshutdown` at 11:04:32 and `qmstart` at 11:05:35 on 2026-08-01. That was the PVE 9.2.5 to 9.2.6 fleet upgrade rebooting `purple-server` onto kernel `7.0.14-8-pve`, with `kasm-01` down 80 seconds. See [the upgrade record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster%20PVE%209.2.6%20Upgrade%20and%20SSH%20Host%20Key%20Seeding%20-%202026-08-01.md).
- [ ] Decide whether `idle_disconnect` `0` disables the timer. I set 525600 minutes on `Administrators` because nothing in `client_api.pyc` or `provider_manager.pyc` shows how the client reads zero, and the RDP path only multiplies it by 60. A tested zero would be cleaner than a year.
- [ ] Trim the `logs` table. It holds 1556 MB of a 1.75 GB database dump, which makes every backup of a config-only database mostly session logging.
