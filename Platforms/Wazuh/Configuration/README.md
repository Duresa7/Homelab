# Wazuh Configuration Reference

**Created:** 2026-07-13  
**Last updated:** 2026-08-03

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
| `alpha-prod-01` | 4.14.6-1, held | ID `006`, `alpha-prod-01` | `192.168.80.118` | Enabled/active; TCP 1514 established |
| `docker-blue` | 4.14.6-1, held | ID `007`, `docker-blue` | `192.168.40.39` | Enabled/active; TCP 1514 established |
| `media-01` | 4.14.6-1, held | ID `008`, `media-01` | `192.168.40.42` | Enabled/active; TCP 1514 established |
| `ansible-01` | 4.14.6-1, held | ID `009`, `ansible-01` | `192.168.40.36` | Enabled/active; TCP 1514 established |
| `monitor-01` | 4.14.6-1, held | ID `010`, `monitor-01` | `192.168.73.2` | Enabled/active; TCP 1514 established |
| `docker-network` | 4.14.6-1, held | ID `011`, `docker-network` | `192.168.85.2` | Enabled/active; TCP 1514 established |
| `kasm-01` | 4.14.6-1, held | ID `012`, `kasm-01` | `192.168.78.10` | Enabled/active; TCP 1514 established |
| `grey-server` | 4.14.6-1, held | ID `013`, `grey-server` | `192.168.70.10` | Enabled/active; TCP 1514 established |
| `purple-server` | 4.14.6-1, held | ID `014`, `purple-server` | `192.168.70.11` | Enabled/active; TCP 1514 established |
| `blue-server` | 4.14.6-1, held | ID `015`, `blue-server` | `192.168.70.12` | Enabled/active; TCP 1514 established |
| `red-server` | 4.14.6-1, held | ID `016`, `red-server` | `192.168.70.13` | Enabled/active; TCP 1514 established |
| `green-server` | 4.14.6-1, held | ID `017`, `green-server` | `192.168.70.14` | Enabled/active; TCP 1514 established |

The manager and dashboard verified IDs `004` through `017` active and synchronized on 2026-08-03. Both interfaces reported zero disconnected, pending, or never-connected agents.

## Shared Agent Groups

| Group | Versioned fragment | Membership and purpose |
|---|---|---|
| `default` | [default-agent.conf](Agent%20Groups/default-agent.conf) | All agents; real-time `/etc/ssh` and `/etc/cron.d` monitoring |
| `edge` | [edge-agent.conf](Agent%20Groups/edge-agent.conf) | ID `005` only; adds real-time `/etc/cloudflared` monitoring |
| `proxmox` | No extra fragment | IDs `013` through `017`: Grey, Purple, Blue, Red, & Green; membership is `default,proxmox` |

I removed the former custom `/var/lib/docker/volumes/wordpress_wp_data/_data` entry and its rollback copy on 2026-08-03. The exact path has zero matches under the manager's shared configuration. Wazuh's package-owned generic audit signatures remain unchanged.

## Administrative Access

The internal indexer user `dkadi` has backend role `admin`, which the live `all_access` mapping grants full indexer access. Dashboard `run_as` is enabled. Wazuh server mapping rule ID 100, `wui_dkadi_admin`, matches `user_name: dkadi` and links to role ID 1, `administrator`.

I verified the complete path on 2026-08-03 with a fresh `dkadi` authorization context. The security configuration endpoint returned HTTP `200`, the effective role was `administrator`, & that role exposed all 23 administrator policies. The check did not reveal or change the user's password.

The manager-side `proxmox` group contains exactly five active members: Grey, Purple, Blue, Red, & Green. Its generated `agent.conf` passed `verify-agent-conf`. The dashboard returned `default, proxmox` on all five rows, so the nodes keep the common Linux policy and share one Proxmox identity.

## Why edge-01 sits at a different version

`edge-01` has no Wazuh repository file. Its agent came from a downloaded package, so `apt-cache policy wazuh-agent` reports candidate 4.14.5-1 against installed 4.14.5-1, and no hold is set. `app-01` reached 4.14.6-1 through the repository before this change. The twelve new agents are pinned and held at the manager's 4.14.6-1 version by the deployment play.

That means fleet maintenance reports edge-01 as fully patched and it is, for every package apt can see. The agent there will not move again until I either add the repository or install a newer package by hand. A 4.14.5 agent against a 4.14.6 manager is a supported pairing, so nothing is broken today; the part worth knowing is that no scheduled run will ever close the gap on its own.

I verified the existing version split on 2026-07-29 and the twelve new package holds on 2026-08-03.
