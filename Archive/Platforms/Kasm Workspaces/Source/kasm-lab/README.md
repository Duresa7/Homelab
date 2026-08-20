# Proxmox Kasm Lab Scripts

**Created:** 2026-08-20  
**Last updated:** 2026-08-20

These are the retired Proxmox-side Kasm lab maintenance scripts captured from
`grey-server:/usr/local/lib/kasm-lab` on 2026-08-20. They had no systemd unit,
cron entry, process, or external caller when I found them after the platform
decommission. I preserved the source here before deleting the live directory.

The scripts are historical source and must not be deployed. They implement the
capacity gate, evidence-disk retention, and orphaned dynamic-guest cleanup that
supported the abandoned autoscaling design. `orphan_sweeper.py` expects Kasm API
settings from an external environment file; this archive contains field names
only and no stored value.

| File | SHA256 |
| --- | --- |
| `capacity_guard.py` | `d862dc01ecf6bacb27708526307f8f91da9f4d4eda9afce4ecd92cf148c8f0fa` |
| `evidence_retention.py` | `3ca84aac4a1a87a4c5b5ae6a4b2af37b489904a4a3b913c88660f763ab9ced6f` |
| `orphan_sweeper.py` | `288e04735c3dbca8cf24e51c275ba9c653595e5c044a34ef2da98f3878642418` |

All three files compiled with Python 3 before archival. A publication-policy
scan found no credential value, private key, MAC address, encoded secret, or IP
address in the source.
