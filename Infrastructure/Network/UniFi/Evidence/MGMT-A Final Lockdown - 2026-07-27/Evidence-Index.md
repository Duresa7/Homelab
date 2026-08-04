# MGMT-A Final Lockdown Evidence Index

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

This folder contains the sanitized evidence for the 2026-07-27 MGMT-A lockdown. I omitted controller IDs, client MAC addresses, credentials, and secret values.

| Step | Evidence | Purpose |
|---|---|---|
| S01 | [Preflight](Logs/S01-Preflight.md) | Starting policies, allowed paths, and rollback captures |
| S02 | [UniFi changes](Logs/S02-UniFi-Changes.md) | The two reviewed controller changes |
| S03 | [Proxmox firewall](Logs/S03-Proxmox-Firewall.md) | The removed Termix exception and compile result |
| S04 | [Validation](Logs/S04-Validation.md) | Positive and negative connectivity results |
| S01/S03 | `Exports/cluster.fw.before-2026-07-27` and `Exports/cluster.fw.after-2026-07-27` | Exact Proxmox firewall files before and after the change |

The full UniFi rollback snapshots remain in the local UniFi skill state directory because they contain controller-specific identifiers and client details that do not belong in the public repository.
