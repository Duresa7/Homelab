# app-01 Maintenance Silence

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

**Implemented:** 2026-10-11  
**Status:** Active until 11:59 PM on 2026-10-25, or until app-01 returns to service  
**Affected systems:** Grafana on `monitor-01`, the Discord alert bot, `app-01`

I silenced Grafana's notifications for `app-01` while the VM is stopped for maintenance. I stopped VM 116 on 2026-10-09 and set `onboot: 0` while deploying Minecraft on `alpha-prod-01` ([deployment record](../../../Minecraft/Documentation/Change%20Records/Deployment%20-%202026-10-09.md)). Both of its scrape targets, `192.168.80.10:9100` in `node` and `192.168.80.10:9101` in `cadvisor`, read `up 0` on 2026-10-11. The alert bot posted `CRITICAL: Host is down` 14 times between 1:26 PM on 2026-10-09 and 6:31 PM on 2026-10-11, once every four hours and five minutes under the root policy's four-hour `repeat_interval`.

## Why a silence

The downtime is planned and temporary. A silence mutes delivery and leaves the rules, the scrape targets and the dashboards alone, so the fleet table and the `node-app-01` board still show the host as down. It also expires on its own, so the alert returns if `app-01` is still down after the window rather than staying muted indefinitely. Removing the targets from `prometheus.yml` or pausing `homelab-host-down` would have hidden every other host's failures or needed a matching revert in the versioned configuration.

Silences live in Grafana's alertmanager state, not in the provisioning files, so nothing under [Configuration/](../../Configuration/) changed and no Grafana restart was needed.

## Before the change

Grafana held no silences. Its alertmanager listed one active alert carrying `app-01`: `Host is down` with `host="app-01"`, `instance="192.168.80.10:9100"`, `job="node"`. The cAdvisor target's `Metrics source stopped reporting` alert was not active, because `homelab-exporter-down` drops any target whose host's `node` target is down.

## Silences

I created both silences through `POST /api/alertmanager/grafana/api/v2/silences` at `http://192.168.73.2:3000`, authenticated as the Grafana administrator with the standard application account. The login was staged in a mode-0600 curl configuration file on `ubuntu-dev`, never placed in a command argument, and shredded afterwards.

| Silence ID | Matchers | Covers |
|---|---|---|
| `e36fd80f-eee8-4da5-b6fe-4ea71829013b` | `host="app-01"` | Every alert labelled `host="app-01"`, including `Host is down` and, if the host's cAdvisor target ever fails alone, `Metrics source stopped reporting` |
| `a09563d7-28cc-4010-91f9-d00df61ac0ed` | `alertname="VM or container is down"`, `name="app-01"` | `homelab-guest-down`, which labels the guest by Proxmox `name` and has no `host` label. It cleared two hours after the 2026-10-09 stop but would fire again if I start and stop the VM during the window |

Both run from 6:46:53 PM on 2026-10-11 to 11:59 PM on 2026-10-25, which is `2026-10-26T03:59:00Z`. The comment on each reads `Planned maintenance: app-01 (VM 116) parked since 2026-10-09 with onboot disabled. Expire this silence when app-01 returns to service.`

## Verification

Readback from `GET /api/alertmanager/grafana/api/v2/silences` listed both silences in state `active` with the matchers and end time above. `GET /api/alertmanager/grafana/api/v2/alerts` reported `Host is down` for `app-01` in state `suppressed`, `silencedBy` `e36fd80f-eee8-4da5-b6fe-4ea71829013b`. The unsilenced alert list still held the expected Updates alerts for eight hosts and `Filesystem is almost full` on `media-01` `/data`, so the silence muted only `app-01`.

The last `Host is down` message the bot posted was at 6:31:05 PM, sixteen minutes before the silence. The next repeat would have been due around 10:36 PM on 2026-10-11. I have not yet checked the bot's log past that time.

At 7:10 PM Eastern, Grafana's own metrics endpoint on `monitor-01` reported `grafana_alerting_silences{state="active"} 2`, both `app-01` targets still read `up 0`, and the alert bot's log held 66 lines since 6:46 PM with none mentioning `app-01`. That is consistent but not conclusive, because the next repeat was not due until about 10:36 PM.

## Open state

- When `app-01` returns to service, expire both silences rather than waiting out the window: `DELETE /api/alertmanager/grafana/api/v2/silence/<id>` with each ID above, or **Alerting > Silences > Expire** in Grafana. Then confirm `up{host="app-01"}` is 1 on both targets.
- If maintenance runs past 2026-10-25, the `Host is down` alert resumes on its next evaluation. Extend the window by creating a replacement silence with the same matchers.
- Confirm in `docker logs alert-bot` that no `Host is down` message for `app-01` was posted after 6:46 PM on 2026-10-11.
