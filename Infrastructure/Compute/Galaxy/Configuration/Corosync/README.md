# Galaxy Corosync Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

This directory holds the validated Corosync `knet` export for configuration version 8. Its SHA-256 is `b3d1ee784361141113c5ab6fbb02117e625daca6cf65f42d3d0080b7771fd22a`; the dated change record owns the implementation sequence.

The historical and current cluster overview is in the [Galaxy cluster setup document](../../Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md).

## Current Configuration

- Cluster: `Galaxy`
- Transport: `knet`
- Link mode: `passive`
- Configuration version: `8`
- Current reference: [corosync.conf](corosync.conf)
- SHA-256: `b3d1ee784361141113c5ab6fbb02117e625daca6cf65f42d3d0080b7771fd22a`

| Node | Node ID | `link0` / MGMT-A | `link1` / Cluster-Net |
|---|---:|---|---|
| `grey-server` | 1 | `192.168.70.10` | `192.168.71.10` |
| `purple-server` | 2 | `192.168.70.11` | `192.168.71.11` |
| `blue-server` | 3 | `192.168.70.12` | `192.168.71.12` |
| `red-server` | 4 | `192.168.70.13` | `192.168.71.13` |

I set no explicit link priorities. Corosync prefers lower-numbered `link0`; `link1` carries the redundant path. [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../../Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) records the four-node rollout & link-failure tests.
