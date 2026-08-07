# Wazuh Configuration Reference

**Created:** 2026-07-13  
**Last updated:** 2026-08-07

I record endpoints, paths, package versions, & current agent state here. The [version-figure rule](../../../README.md#version-figures) applies to the dated observations below.

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
| `edge-01` | 4.14.5-1 | ID `005`, `edge-01` | `192.168.30.10` | Enabled/active; TCP 1514 established |
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

## Agent package state across the fleet

Observed 2026-08-04, after adding the `edge-01` source and correcting two holds:

| Host | Agent | Held | Wazuh source |
|---|---|---|---|
| `alpha-prod-01`, `media-01`, `docker-network`, `docker-blue`, `ansible-01`, `monitor-01` | 4.14.6-1 | yes | yes |
| `app-01` | 4.14.6-1 | yes, applied 2026-08-04 | yes |
| `edge-01` | 4.14.5-1 | yes, applied 2026-08-04 | yes, added 2026-08-04 |
| `docker-main` | 4.14.0-1 | no | no |
| `security-01` | manager 4.14.7-1 | n/a | yes |
| `splunk-siem` | none | n/a | no |

**The manager caps every agent.** `security-01` ran manager `4.14.6-1` while the repository carried only `4.14.7-1`, because Wazuh publishes one package per release line rather than a back catalogue. An agent must never be newer than its manager, which froze every agent version until the manager moved. I upgraded the central stack to `4.14.7-1` on 2026-08-04, so the cap is now above every agent and the holds can be released one host at a time.

That is what the holds are for. `app-01` had the source without a hold, and a simulated fleet run confirmed it would have installed `4.14.7-1` over its `4.14.6-1`, putting the agent ahead of the manager. Holding it was the fix. `edge-01` received the same hold when it received the source, so adding the source could not create the same exposure.

`edge-01` on 4.14.5-1 against a 4.14.7-1 manager is a supported pairing, so none of this describes an outage. `docker-main` on 4.14.0-1 is the widest gap and is [tracked as open work](../Documentation/TODO.md).
