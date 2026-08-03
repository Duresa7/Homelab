# Galaxy HA Local-Storage Stranding Evidence

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

**Capture window:** 2026-07-20, 16:30-17:15 EDT  
**Mechanism:** Proxmox web UI screenshots plus `journalctl`, `ha-manager`, `pct`, `lvs`, & `/var/log/pve/tasks` transcripts pulled over SSH from the Galaxy nodes

This set backs the [incident report](../Galaxy-HA-Local-Storage-Stranding-Incident-2026-07-20.md). The four screenshots are a before/after pair around the recovery; the four logs are the verbatim host output the report quotes.

## Screenshots

**S01:** CT 107 `docker-network` on purple-server, Status `stopped`, HA State `error`, `No network information`; the task pane below shows the `HA 107/108 Migrate` exit-255 failures and the `no such logical volume` start failures. This is the stranded state before recovery.

![CT 107 stopped and in HA error on purple-server](Screenshots/S01-CT107-Stopped-HA-Error-Purple-2026-07-20.png)

**S02:** Cluster log detail, 16:37-16:38 & 17:03, showing `hamigrate:107`/`hastart:108` ending with `command 'ha-manager ...' failed: exit code 255` and the `vzstart:107` recovery task starting on blue-server.

![Cluster log HA migrate exit 255 and recovery vzstart on blue](Screenshots/S02-Cluster-Log-HAMigrate-Exit255-2026-07-20.png)

**S03:** Server view after recovery, 107 & 108 back under blue-server, with `CT 108 - Start` and `CT 107 - Start` tasks reporting OK at 17:03. This is the recovered state.

![Both containers recovered on blue-server](Screenshots/S03-Both-CTs-Recovered-Blue-2026-07-20.png)

**S04:** Cluster log detail, 16:31-16:39, showing the full `pve-ha-lrm` cascade: `vzstart:107`/`vzstart:108` failing with `no such logical volume pve/vm-107-disk-0` and `vzmigrate` returning `migration aborted`.

![Cluster log no-such-logical-volume and migration-aborted cascade](Screenshots/S04-Cluster-Log-NoSuchLV-Cascade-2026-07-20.png)

## Logs

| File | What it shows |
|------|---------------|
| [blue-shutdown-conditional-policy-journal-2026-07-20.txt](Logs/blue-shutdown-conditional-policy-journal-2026-07-20.txt) | blue's shutdown at 16:30 with the LRM logging `shutdown policy 'conditional'`, the `ct:107`/`ct:108` stop, and the `last` reboot/shutdown history |
| [purple-ha-recovery-attempt-failures-2026-07-20.txt](Logs/purple-ha-recovery-attempt-failures-2026-07-20.txt) | The `hamigrate`/`hastart` tasks refusing the services with `in error state, must be disabled and fixed first`, plus a representative `vzstart` `no such logical volume` |
| [purple-vzmigrate-aborted-2026-07-20.txt](Logs/purple-vzmigrate-aborted-2026-07-20.txt) | The HA-driven `vzmigrate` of 107 & 108 to red-server aborting, including the `stale volume copy on red-server` note |
| [post-recovery-verification-2026-07-20.txt](Logs/post-recovery-verification-2026-07-20.txt) | The 17:15 good-state snapshot: HA status, the `pin-blue-local-storage` rule, `pct list`, active disks, config locations, and the `TASK OK` recovery starts |
