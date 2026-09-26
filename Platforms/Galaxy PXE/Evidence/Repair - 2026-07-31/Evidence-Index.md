# Galaxy PXE Repair Evidence Index

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Evidence date:** 2026-07-31  
**Project:** Galaxy PXE provisioning repair

| Step | Artifact | Demonstrates |
|---|---|---|
| S01 | [Green First-Run Failure Trace](Logs/S01%20Green%20First-Run%20Failure%20Trace%20-%202026-07-31.md) | The physical machine fetched the installer, answer, and bootstrap, then produced no first-boot callback. |
| S02 | [Repair and Deployment Validation](Logs/S02%20Repair%20and%20Deployment%20Validation%20-%202026-07-31.md) | The repaired code, generated answer, first-boot script, and deployed project passed their checks. |
| S03 | [Disposable Acceptance VM Runs](Logs/S03%20Disposable%20Acceptance%20VM%20Constraint%20-%202026-07-31.md) | Tagged VLAN 5 reached the service; a 7 GiB memory failure and invalid answer value were corrected; the 12 GiB VM installed to `/dev/sda`, posted success, powered off, and was removed. |
| S04 | [Final Live Verification](Logs/S04%20Final%20Live%20Verification%20-%202026-07-31.md) | The live services, disabled states, join key, both Corosync links, callback policy, disposable VM cleanup, and idempotent deployment passed. |
| S05 | [Green Physical Rerun](Logs/S05%20Green%20Physical%20Rerun%20-%202026-07-31.md) | The original callback failure was identified, both callback paths were allowed, the M920q installed to NVMe, Green joined as the fifth node, both Corosync links passed, and Bane port 4 moved to `Proxmox-Trunk`. |
| S06 | [Firewall Group Consolidation](Logs/S06%20Firewall%20Group%20Consolidation%20-%202026-07-31.md) | The post-cutover policy moved from a Green-only selector to `OBJ-Proxmox-Nodes`; UniFi read back the group reference and Grey and Green still reached the PXE health endpoint. |
| S07 | [Deployment Residue Cleanup](Logs/S07%20Deployment%20Residue%20Cleanup%20-%202026-07-31.md) | Superseded backups and caches were removed after the live service and retained runtime paths passed verification. |

I retained no passwords, private keys, public key bodies, or generated password hashes in these artifacts.
