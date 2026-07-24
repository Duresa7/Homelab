# Galaxy Troubleshooting

**Created:** 2026-07-14  
**Last updated:** 2026-07-24

This is my chronological troubleshooting record for the Galaxy Proxmox cluster. Open follow-up work is tracked in the [Galaxy TODO](../TODO.md).

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Date investigated | Symptom | Current finding | Status |
|---:|---|---|---|---|
| <a id="1-recurring-pvestatd-failure-on-blue-server"></a>[1](Recurring%20pvestatd%20Failure%20on%20blue-server%20-%202026-07-13.md) | 2026-07-13 | Proxmox reported `blue-server` as `unknown` while its guests remained online | `pvestatd` repeatedly crashes and does not restart; the deeper cause is not yet proven | Known issue; deferred |
| <a id="2-gnome-wired-network-indicator-showed-a-question-mark-on-debian-dev"></a>[2](GNOME%20Wired%20Network%20Indicator%20Showed%20a%20Question%20Mark%20on%20debian-dev%20-%202026-07-15.md) | 2026-07-15 | GNOME showed a question mark for wired networking on `debian-dev` although internet access worked | `ens18` was owned by legacy ifupdown/dhcpcd and therefore appeared unmanaged to NetworkManager | Resolved |
| <a id="3-duplicate-1password-apt-repository-on-debian-dev"></a>[3](Duplicate%201Password%20APT%20Repository%20on%20debian-dev%20-%202026-07-15.md) | 2026-07-15 | `apt update` emitted repeated duplicate-target warnings for the 1Password repository | Equivalent legacy `.list` and maintained deb822 `.sources` entries were both active | Resolved |
| <a id="4-claude-desktop-keyring-and-kvm-access-on-debian-dev"></a>[4](Claude%20Desktop%20Keyring%20and%20KVM%20Access%20on%20debian-dev%20-%202026-07-15.md) | 2026-07-15 | Claude Desktop would not persist sign-in and Cowork could not use `/dev/kvm` on `debian-dev` | A fresh GNOME login activated the login keyring & `kvm` group membership; Claude now saves sign-in & Cowork can use `/dev/kvm` | Resolved |
| <a id="5-ha-local-storage-stranding-of-ct-107-and-ct-108-after-a-blue-server-shutdown"></a>[5](HA%20Local-Storage%20Stranding%20of%20CT%20107%20and%20CT%20108%20After%20a%20Blue-Server%20Shutdown%20-%202026-07-20.md) | 2026-07-20 | CT 107 `docker-network` & CT 108 `docker-blue` down and stuck in HA `error` on purple-server; couldn't migrate back to blue | HA relocated the configs off blue on a shutdown, but the guests' `local-lvm` disks stayed on blue, so no node could start them | Resolved |
| <a id="6-disabled-ha-daemons-on-grey-server"></a>[6](Disabled%20HA%20Daemons%20on%20grey-server%20-%202026-07-22.md) | 2026-07-22 | HA reported `grey-server` with `old timestamp - dead?`, `watchdog standby`, & a 2025-08-22 LRM timestamp | Grey's `pve-ha-lrm` & `pve-ha-crm` units were disabled and hadn't started during the current boot | Resolved |
| <a id="7-ssh-backup-helper-reported-missing-archives"></a>[7](SSH%20Backup%20Helper%20Reported%20Missing%20Archives%20-%202026-07-22.md) | 2026-07-22 | The backup helper reported four successful Proxmox configuration archives, but its inventory and the remote filesystems contained none | The success response did not match remote state; I replaced it with direct checksummed root-only archives | Mitigated; helper defect remains |
| <a id="8-purple-nvme-reliability-failure"></a>[8](Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md) | 2026-07-22 | Purple's boot log reported NVMe critical warning `0x04` after the Proxmox 9.2.5 canary reboot | The 256 GB boot NVMe reports overall health `FAILED` and 169% endurance used | Replacement underway; Purple offline since 2026-07-24 |
