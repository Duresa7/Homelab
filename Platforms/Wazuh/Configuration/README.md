# Wazuh Configuration Reference

**Created:** 2026-07-13  
**Last updated:** 2026-07-20

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
| `app-01` | 4.14.5-1 | ID `004`, `app-01` | `192.168.80.10` | Enabled/active; TCP 1514 established |
| `edge-01` | 4.14.5-1 | ID `005`, `edge-01` | `192.168.90.10` | Enabled/active; TCP 1514 established |

`app-01` and `edge-01` are the only intended Wazuh endpoints. The dashboard verifies IDs `004` and `005` active on manager node `node01`. Never commit or display `/var/ossec/etc/client.keys` contents.
