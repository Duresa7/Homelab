# Galaxy Cluster PVE 9.2.11 Package Update

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

## What Changed

I refreshed the APT package indexes and ran a noninteractive `dist-upgrade` on all five Galaxy nodes in the order Green, Purple, Red, Blue, and Grey. I retained existing configuration files when `dpkg` encountered a locally modified conffile. No node or guest was rebooted or stopped.

The nodes moved from `pve-manager` 9.2.6 to 9.2.11. The update also installed Proxmox kernel `7.0.14-15-pve` and updated QEMU/KVM, `qemu-server`, `pve-container`, ZFS, Proxmox Backup clients, VM firmware, FRR, OpenSSL, Postfix, and the available Debian security packages. Grey installed 39 upgrades, Purple, Blue, and Red installed 55 each, and Green installed 56.

## Execution Result

Each node completed the package transaction. Purple, Red, Blue, and Grey wrote temporary output and exit-status files under `/var/tmp`; each recorded exit status 0. I removed those temporary files after verification.

Green's foreground upgrade outlived the Executor call and the call returned an internal gateway error. I did not retry the update. A follow-up process check showed the original `apt-get` and `dpkg` processes continuing through the Proxmox HA and initramfs triggers. After they exited, `dpkg --audit` returned no findings, `apt list --upgradable` returned no packages, and the installed package versions matched the other four nodes. I retained no complete terminal transcript for this maintenance.

## Verification

- All five nodes report `pve-manager/9.2.11`.
- All five nodes have `proxmox-kernel-7.0` version `7.0.14-15` installed and continue to run `7.0.14-8-pve`.
- `dpkg --audit` returned no incomplete package state on any node.
- `apt list --upgradable` returned no packages on any node after the index refresh and upgrade.
- `pve-cluster`, `corosync`, `pvedaemon`, `pveproxy`, `pvestatd`, `pve-ha-crm`, and `pve-ha-lrm` reported active on every node.
- At 10:38:46 AM EDT, `pvecm status` reported five nodes, five of five votes, quorum three, and `Quorate: Yes`.
- The cluster API listed Grey, Purple, Blue, Red, and Green online.
- `ha-manager status` reported quorum OK, fencing armed, Green as the active CRM master, and HA services `ct:107` and `ct:108` started on Blue.

## Still Open

All five nodes require a later rolling reboot to start kernel `7.0.14-15-pve`. Until then, package updates are complete but the running kernel remains `7.0.14-8-pve`.
