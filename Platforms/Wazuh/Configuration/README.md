# Wazuh Configuration Reference

**Created:** 2026-07-13  
**Last updated:** 2026-07-29

This reference records endpoints, paths, package versions, & current agent state.

## Manager

| Item | Value |
|---|---|
| Host | `security-01` / `wazuh-01` |
| Address | `192.168.72.2/24`, Security-A/VLAN 72 |
| Agent events | TCP 1514 |
| Enrollment | TCP 1515 |
| API | HTTPS 55000 |
| Dashboard | HTTPS 443 |
| Manager data/config root | `/var/ossec` (root:`wazuh`, mode 0750) |
| Indexer data | `/var/lib/wazuh-indexer` (`wazuh-indexer`, mode 0750) |
| Dashboard config | `/etc/wazuh-dashboard` (`wazuh-dashboard`, mode 0750) |

## Endpoint Installation State

| Host | Package | Manager identity | Address | Service state |
|---|---|---|---|---|
| `app-01` | 4.14.6-1 | ID `004`, `app-01` | `192.168.80.10` | Enabled/active; TCP 1514 established |
| `edge-01` | 4.14.5-1 | ID `005`, `edge-01` | `192.168.90.10` | Enabled/active; TCP 1514 established |

`app-01` and `edge-01` are the only intended Wazuh endpoints. The dashboard verifies IDs `004` and `005` active on manager node `node01`.

## Why the two agents sit at different versions

The two endpoints don't get their agent packages the same way, and the split isn't a missed upgrade. `app-01` has `/etc/apt/sources.list.d/wazuh.list`, so it tracks the Wazuh repository and fleet package maintenance moved it from 4.14.5-1 to 4.14.6-1 on 2026-07-29 along with everything else. `edge-01` has no Wazuh repository file at all. Its agent came from a downloaded package, so `apt-cache policy wazuh-agent` reports candidate 4.14.5-1 against installed 4.14.5-1, and no hold is set.

That means fleet maintenance reports edge-01 as fully patched and it is, for every package apt can see. The agent there will not move again until I either add the repository or install a newer package by hand. A 4.14.5 agent against a 4.14.6 manager is a supported pairing, so nothing is broken today; the part worth knowing is that no scheduled run will ever close the gap on its own.

I verified this on 2026-07-29 by reading the repository files, holds, and candidate versions on both hosts.
