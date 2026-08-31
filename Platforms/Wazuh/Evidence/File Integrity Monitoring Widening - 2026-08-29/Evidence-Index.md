# File Integrity Monitoring Widening Evidence

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

Supports [File Integrity Monitoring Widening - 2026-08-29](../../Documentation/Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md).

Step numbers run S01 to S21 across six evidence folders. This folder holds S11 to S15. All captures are headless, so no pointer appears in any of them.

| Step | Capture | What it shows |
|---:|---|---|
| 11 | [All agents active](Screenshots/S11-Wazuh-Endpoints-All-Agents-Active-2026-08-30.png) | The Endpoints page: 15 remote agents active, zero disconnected, pending or never connected, with the manager's own agent 000 making 16. Group membership is visible per agent. |
| 12 | [Endpoint groups](Screenshots/S12-Wazuh-Endpoint-Groups-2026-08-30.png) | The four groups this change configures: `default` with 14, `proxmox` with 5, `edge` with 1 and `workstation` with 1. |
| 13 | [Workstation group membership](Screenshots/S13-Wazuh-Workstation-Group-Membership-2026-08-30.png) | The `workstation` group holding only `ubuntu-dev`, agent 020, which is what makes it safe to give this group aggressive settings. |
| 14 | [Workstation agent configuration](Screenshots/S14-Wazuh-Workstation-Group-Agent-Config-2026-08-30.png) | The full `agent.conf` in Wazuh's editor: the watched directories, the `restrict` expressions on `/tmp` and `/var/tmp`, and the ignore list. This is the file the correction in the record produced. |
| 15 | [File Integrity Monitoring module](Screenshots/S15-Wazuh-File-Integrity-Monitoring-Module-2026-08-30.png) | Wazuh's own FIM view over 24 hours, taken after the correction and the purge. The busiest agent is now `grey-server` at 201 events, which is my own LVM work on `/etc/lvm`, and `ubuntu-dev` is second at 10. Before the correction `ubuntu-dev` alone produced 2,644, so this is the after state rather than the problem. |
