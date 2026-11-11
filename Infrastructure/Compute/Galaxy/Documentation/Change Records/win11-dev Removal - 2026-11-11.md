# win11-dev Removal

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Change date:** 2026-11-11  
**Target:** VM 103 `win11-dev` on `grey-server`, and the records and configuration that pointed at it

## Outcome

I deleted VM 103 `win11-dev`, the standalone Windows 11 Pro 25H2 workstation I [built on 2026-09-21](win11-dev%20Completion%20-%202026-09-21.md) and [moved to Grey on 2026-09-23](win11-dev%20Grey%20Migration%20-%202026-09-23.md). Its disks are gone and there is no backup, so this cannot be undone.

## Before

`qm config 103` on Grey read: 4 cores, 8 GiB fixed, OVMF with Secure Boot keys, `scsi0` 120G on `local-lvm:vm-103-disk-1` (30.61% allocated, about 36.7 GiB), `efidisk0` and `tpmstate0` on `local-lvm`, one NIC on VLAN 40, `onboot: 1`. It was stopped, after a `qmshutdown` by `root@pam` at 1:03 PM that day. It had no snapshots, no HA resource, no backup or replication job and no per-VM firewall file. Wazuh held no agent for it.

What still pointed at it:

| Where | What | Action |
|---|---|---|
| UniFi | Client `win11-dev` with a fixed IP of `192.168.40.117` on Personal-A | Forget sent twice; the reservation is still there |
| ssh-mcp on `docker-blue` | Profile `win11_dev` | Removed |
| Hermes `homelab-ops` skill | `win11_dev` in the personal-PC row of the profile map | Removed from the tracked copy |
| GitHub `Duresa7/app-portal` | Self-hosted runner `windows-x64-1`, offline, and the repository variable `WINDOWS_RUNNER=windows-x64-1` | Left in place |
| Diagrams | Cards on `galaxy-cluster`, `homelab-overview` and `lab-map` | Removed and rebuilt |

## Change

On `grey-server`:

```text
qm destroy 103 --purge 1 --destroy-unreferenced-disks 1
  Logical volume "vm-103-disk-1" successfully removed.
  Logical volume "vm-103-disk-0" successfully removed.
  Logical volume "vm-103-disk-2" successfully removed.
purging VM 103 from related configurations..
```

`qm status 103` then answered `Configuration file 'nodes/grey-server/qemu-server/103.conf' does not exist`, no `vm-103-` LV remained, and `local-lvm` read 48.87% used with 425,583,802 KiB available. It was 53.49% used when I read it earlier that afternoon. The cluster now holds 18 guests, 12 of them VMs.

On `docker-blue` I removed the `win11_dev` block from `/opt/docker/ssh-mcp/config.unpinned.toml` and the live `/opt/docker/ssh-mcp/config/config.toml` with `remove-profile.py`. The script refuses to write unless the result parses and every other profile and setting comes out identical. Both files dropped from 26 profiles to 25 and kept their owner and mode, 0 and `644` for the unpinned copy, 65532 and `600` for the live one. `docker kill -s HUP ssh-mcp` logged `Profiles: removed win11_dev.`, and `list-connections` returned 25 profiles. `ssh-mcp.env` held no entry for it. I made the same removal in the [tracked config](../../../../../Platforms/SSH%20MCP/Configuration/config.toml).

In UniFi I matched the client by name, confirmed it was the one holding the reservation (`use_fixedip` true, `fixed_ip` `192.168.40.117`, network Personal-A, no local DNS record), and ran `unifi_forget_client` on it. The controller answered `forgotten successfully`, but a readback 10 minutes later still listed the client with `use_fixedip` true and `fixed_ip` `192.168.40.117`. A second forget gave the same answer and the same readback. `unifi_set_client_ip_settings` with `use_fixedip` false failed with `api.err.IdInvalid`. The client's `_id` is a UUID, which that legacy endpoint may not accept. The reservation names a MAC that no longer exists, so nothing can take the address, but it keeps `192.168.40.117` reserved.

I removed the `win11_dev` profile from the [tracked Hermes skill](../../../../../Platforms/Hermes%20Agent/Configuration/skills/homelab-ops/SKILL.md). `hermes-01` was stopped, so the live copy in `~/.hermes/skills/homelab-ops/SKILL.md` still lists it.

I removed the win11-dev cards from the three diagram specs and the win11-dev clause from the `galaxy-cluster` footnote, rebuilt those three diagrams and the `homelab-overview` PNG, and `build.py --check` passed all three. Grey's card on `lab-map` already read 10 guests, which is now correct.

## Not changed

The app-portal CI job "Install and verify on Windows" runs on `${{ vars.WINDOWS_RUNNER || 'windows-latest' }}`, and `WINDOWS_RUNNER` is still `windows-x64-1`. That job only runs on a `v*` tag or a dispatch with Windows ticked; the last CI run, on 2026-11-07, skipped it and passed. Until the variable changes, a Windows-enabled run will wait for a runner that no longer exists.

## Open items

- Forget the `win11-dev` client in the UniFi Network UI, which removes the `192.168.40.117` reservation the API could not.
- I still need to delete the `WINDOWS_RUNNER` variable on `Duresa7/app-portal` (or point it at another runner) and remove the offline `windows-x64-1` registration.
- Copy the tracked `homelab-ops` skill to `hermes-01` the next time it runs.
