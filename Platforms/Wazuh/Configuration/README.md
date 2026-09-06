# Wazuh Configuration Reference

**Created:** 2026-07-13  
**Last updated:** 2026-09-03

I record endpoints, paths, package versions, & current agent state here. The [version-figure rule](../../../README.md#version-figures) applies to the dated observations below.

## Manager

| Item | Value |
|---|---|
| Host | `security-01` |
| Address | `192.168.72.2/24`, Security-A/VLAN 72 |
| Agent events | TCP 1514 |
| Enrollment | TCP 1515 |
| API | HTTPS 55000 |
| Dashboard | HTTPS 443 |
| Manager data/config root | `/var/ossec` (root:`wazuh`, mode 0750) |
| Indexer data | `/var/lib/wazuh-indexer` (`wazuh-indexer`, mode 0750) |
| Dashboard config | `/etc/wazuh-dashboard` (`wazuh-dashboard`, mode 0750) |

## MCP Server

| Item | Value |
|---|---|
| Host | `security-01` |
| Upstream version | Wazuh MCP Server 4.3.0 |
| Image | `wazuh-mcp-server-local:4.3.0-compat` |
| Pinned base | `ghcr.io/gensecaihq/wazuh-mcp-server:4.3.0@sha256:4b3dc5e031f79d113cdb1f14ba03620499461f0d9c713e8e34cd3a047d7319d8` |
| MCP endpoint | `http://192.168.72.2:3000/mcp` |
| Health / readiness | `http://192.168.72.2:3000/health`, `http://192.168.72.2:3000/ready` |
| Live project | `/opt/docker/wazuh-mcp-server` |
| Versioned project | [MCP Server](MCP%20Server/) |
| Executor integration | `wazuh-mcp-server`, user connection `localWazuh` |
| Manager identity | `wazuh-mcp-api`, built-in `readonly` role |
| Indexer identity | `wazuh-mcp-indexer`, custom `wazuh_mcp_readonly` role |
| MCP scope | `wazuh:read`; the 14 write tools are not exposed |

The Indexer role can read only `wazuh-alerts-*` and `wazuh-states-vulnerabilities-*`. Its cluster permissions are `cluster_composite_ops_ro` and the single `cluster:monitor/health` action needed by the MCP readiness check.

The local image applies two patches to the pinned upstream image. The Indexer client clears Python 3.13's extra `VERIFY_X509_STRICT` flag because Wazuh's generated root CA omits a `keyUsage` extension; certificate-chain and hostname verification remain enabled. The bearer middleware also accepts the configured high-entropy API key directly while retaining its read-only scope, because upstream's token-exchange JWT expires after 24 hours and Executor needs a durable static credential.

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
| `grey-server` | 4.14.6-1, held | ID `013`, `grey-server` | `192.168.70.10` | Enabled/active; TCP 1514 established |
| `purple-server` | 4.14.6-1, held | ID `014`, `purple-server` | `192.168.70.11` | Enabled/active; TCP 1514 established |
| `blue-server` | 4.14.6-1, held | ID `015`, `blue-server` | `192.168.70.12` | Enabled/active; TCP 1514 established |
| `red-server` | 4.14.6-1, held | ID `016`, `red-server` | `192.168.70.13` | Enabled/active; TCP 1514 established |
| `green-server` | 4.14.6-1, held | ID `017`, `green-server` | `192.168.70.14` | Enabled/active; TCP 1514 established |
| `game-01` | 4.14.6-1, held | ID `018`, `game-01` | `192.168.80.30` | Enabled/active; TCP 1514 established |
| `ubuntu-dev` | 4.14.6-1 | ID `020`, `ubuntu-dev` | `192.168.40.179` | Enabled/active, verified locally 2026-08-14: `wazuh-modulesd`, `wazuh-logcollector`, `wazuh-syscheckd`, `wazuh-agentd`, and `wazuh-execd` all running |

The manager and dashboard verified IDs `004` through `017` active and synchronized on 2026-08-03. Both interfaces reported zero disconnected, pending, or never-connected agents.

`game-01` enrolled on 2026-08-07 with the game server platform and was missing from this table until 2026-08-08. `debian-dev` enrolled on 2026-08-08 under the manager identity `db-13-dev`. `agent_control -l` on that date listed the manager plus IDs `004` through `019`, all Active, so the table and the manager now agree at sixteen endpoint agents.

I removed Kasm identity 012 through `manage_agents` on 2026-08-19 after destroying VM 122. `agent_control -l` returned no ID 012 or `kasm-01` match afterward.

## Shared Agent Groups

All four groups carry a versioned fragment as of 2026-08-30. The two that were empty were given one in [File Integrity Monitoring Widening](../Documentation/Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md), and `default` and `workstation` were both corrected in it.

| Group | Versioned fragment | Membership and purpose |
|---|---|---|
| `default` | [default-agent.conf](Agent%20Groups/default-agent.conf) | All 16 agents. Real-time `/etc/ssh` and `/etc/cron.d`. Since 2026-08-30 it also turns off rootcheck's trojan check fleet-wide, which produced over 22,000 alerts on `/bin/chfn`, `/bin/chsh` and `/bin/passwd` and no true positives, and ignores `/dev/.lxc` |
| `edge` | [edge-agent.conf](Agent%20Groups/edge-agent.conf) | ID `005` only. `/etc/cloudflared`, `/etc/caddy`, `/tmp`, `/var/tmp`, `/usr/local/bin`, `/home/dkadi/.ssh` and `/etc/systemd/system` |
| `proxmox` | [proxmox-agent.conf](Agent%20Groups/proxmox-agent.conf) | IDs `013` through `017`: Grey, Purple, Blue, Red and Green; membership is `default,proxmox`. Added 2026-08-30 and adds no watches, only ignores: `/etc/pve` is pmxcfs, and its status files were reporting 533 changes each. Configuration under `/etc/pve` stays watched |
| `workstation` | [workstation-agent.conf](Agent%20Groups/workstation-agent.conf) | ID `020`, `ubuntu-dev`; membership is `default,workstation`. Created 2026-08-08 for `debian-dev` (ID `019`, enrolled as `db-13-dev`) so the one machine I sit at is separable from the servers in a dashboard filter; `ubuntu-dev` took over the role and the group membership on 2026-08-13. `debian-dev` was decommissioned on 2026-08-14, and its agent `019` was removed from the manager the same day via `manage_agents`; `agent_control -l` no longer lists it. Given real file-integrity coverage on 2026-08-30: Downloads, `/usr/local/bin`, `/opt`, `~/.ssh` and both systemd unit directories in realtime, with `/tmp` and `/var/tmp` restricted by filename to payload-shaped files |

I removed the former custom `/var/lib/docker/volumes/wordpress_wp_data/_data` entry and its rollback copy on 2026-08-03. The exact path has zero matches under the manager's shared configuration. Wazuh's package-owned generic audit signatures remain unchanged.

## Detection content

| Item | Versioned at | Purpose |
|---|---|---|
| Local rules | [Rules/local_rules.xml](Rules/local_rules.xml) | Rule 100200, level 12, matches a file's SHA-256 against the `known-bad-hashes` CDB list on rules 554 and 550 |
| Hash list refresh | [Scripts](../Scripts/) | A systemd timer at Sunday 04:30 that rebuilds `etc/lists/known-bad-hashes` from MalwareBazaar, re-pins the EICAR hash, refuses a list shorter than 2 entries, and restarts the manager so analysisd recompiles it |
| Splunk forwarder | [Splunk Forwarder](Splunk%20Forwarder/) | `inputs.conf` and `outputs.conf` shipping `/var/ossec/logs/alerts/alerts.json` to `192.168.72.3:9997` |

The VirusTotal integration lives in the manager's `ossec.conf` and is not versioned here, because the stanza is mostly its API key.


## Administrative Access

The internal indexer user `dkadi` has backend role `admin`, which the live `all_access` mapping grants full indexer access. Dashboard `run_as` is enabled. Wazuh server mapping rule ID 100, `wui_dkadi_admin`, matches `user_name: dkadi` and links to role ID 1, `administrator`.

I verified the complete path on 2026-08-03 with a fresh `dkadi` authorization context. The security configuration endpoint returned HTTP `200`, the effective role was `administrator`, & that role exposed all 23 administrator policies. I checked the live state again on 2026-09-03: the running Indexer Security API returned backend role `admin` for `dkadi`, its live `all_access` mapping still matched that backend role, dashboard `run_as` remained enabled, & Wazuh's RBAC database still linked rule 100 to the 23-policy `administrator` role. The manager, indexer, & dashboard were all enabled and running, and the Indexer cluster was green with no unassigned shards. Neither check revealed or changed the user's password.

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
