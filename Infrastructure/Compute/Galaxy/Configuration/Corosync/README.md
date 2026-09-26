# Galaxy Corosync Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Galaxy's Corosync runs `knet` in passive link mode over two links. On 2026-09-24 the live `/etc/pve/corosync.conf` on `grey-server` was at `config_version: 9` with five nodes, SHA-256 `e2145ed72ca18789c100d2ce02cb0e7d24c8825fd8c6dda0a52d3fc150316525`, and `pvecm status` reported five expected and five total votes, quorate.

The tracked [corosync.conf](corosync.conf) is the four-node `config_version: 8` export from 2026-07-10, SHA-256 `b3d1ee784361141113c5ab6fbb02117e625daca6cf65f42d3d0080b7771fd22a`. It predates `green-server`, which joined as the fifth node on 2026-07-31. I have not captured the version 9 file into the repository yet.

## Live configuration (2026-09-24)

- Cluster: `Galaxy`
- Transport: `knet`, link mode `passive`
- Configuration version: `9`

| Node | Node ID | `link0` / MGMT-A | `link1` / Cluster-Net |
|---|---:|---|---|
| `grey-server` | 1 | `192.168.70.10` | `192.168.71.10` |
| `purple-server` | 2 | `192.168.70.11` | `192.168.71.11` |
| `blue-server` | 3 | `192.168.70.12` | `192.168.71.12` |
| `red-server` | 4 | `192.168.70.13` | `192.168.71.13` |
| `green-server` | not captured | `192.168.70.14` | `192.168.71.14` |

Node IDs 1 to 4 come from the version 8 export. I set no explicit link priorities, so Corosync prefers `link0` and `link1` carries the redundant path.

## Records

- [Cluster-Net Corosync Link Addition - 2026-07-10](../../Documentation/Change%20Records/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md): the four-node rollout of `link1` and the link-failure tests
- [Green Baseline and Monitoring - 2026-07-31](../../Documentation/Change%20Records/Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md): the fifth node
- [Cluster architecture](../../Documentation/Architecture/Cluster%20Architecture.md)
