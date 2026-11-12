# Post Once per State Change

**Created:** 2026-11-12  
**Last updated:** 2026-11-12  
**Implementation and verification:** 2026-11-12

The bot now posts a Grafana alert only when its status changes: once when it fires and once when it resolves. Before this, a host or VM that stayed down kept posting, because the bot forwarded every notification Grafana sent. The Splunk path is unchanged.

## Why it repeated

`docker logs alert-bot` for 2026-11-07 to 2026-11-12 showed two sources of repeats, both from Grafana's notification policy in [contact-points.yaml](../../../Prometheus/Configuration/grafana/provisioning/alerting/contact-points.yaml):

- **Group re-sends.** The root policy groups by `grafana_folder` and `alertname`, so every VM that is down shares one group. Grafana re-sends the whole group at the next `group_interval` (5 minutes) whenever any member joins or leaves. During the 2026-11-11 guest moves, `VM or container is down` posted 29 times between 1:08 PM and 6:05 PM: `(4)`, `(5)`, `(5)`, `(7)`, `(6)` and so on, each one the full list again. The updates route does the same at its 30-minute interval; `OS updates are waiting` posted two or three times on each of 2026-11-09, 11-10 and 11-11.
- **The repeat.** A group still firing after `repeat_interval` (4 hours on the root policy) is sent again unchanged.

Splunk was not part of it. Every Splunk search that posts here already suppresses repeats per machine or source, and `Wazuh - Machines gone quiet, listed` suppresses each machine for 604800 seconds.

## Change

[alert_bot.py](../../Source/alert_bot.py) keeps the last status it posted for each Grafana alert, keyed by the alert's `fingerprint`, and falls back to a hash of the labels if a payload has none. For each webhook it drops the alerts whose status matches what it last posted, builds embeds from the rest, and records them after Discord accepts the post. A batch with nothing changed gets a 200 response and the log line `dropped grafana batch of N alert(s): none changed status`, so Grafana does not retry it. Alerts that change together still arrive as one message, and four or more with the same name and status still condense into one embed.

A lock serialises the handler, so two batches arriving together cannot both post the same change. The memory is a JSON file at `STATE_FILE`, default `/tmp/alert-state.json` inside the container. It survives a container restart, and a rebuild starts it empty. A resolved entry is forgotten after seven days.

I left Grafana's policy alone. Its repeats still arrive and are now dropped at the bot, and if a post ever fails, Grafana's next send of that group retries it, because a failed post is never recorded.

Before deploying, I ran the handler on `ubuntu-dev` with Discord and aiohttp stubbed out, replaying the 2026-11-11 pattern:

| Step | Posted |
|---|---|
| `vm1` fires | 1, `CRITICAL: VM or container is down` |
| Group re-sent with `vm1` still firing and `vm2` new | 1, `vm2` only |
| The same group repeated | 0 |
| `vm1` resolved, `vm2` still firing | 1, `Resolved` for `vm1` only |
| The same batch again | 0 |
| `vm1` fires again | 1 |
| Five new alerts in one batch | 1 condensed embed, `(5)` |
| Module reloaded from the saved file | `vm2` firing counts as unchanged |

On `monitor-01` I copied the file to `/home/dkadi/monitoring/alert-bot/alert_bot.py`, SHA-256 `b3496f3f4ab0c1c180fff3e5ef74ecfb37f33a7a18214d4767f7dae069df335d` on both ends, and ran `docker compose up -d --build alert-bot` at 7:39 AM. Only the `alert-bot` container was recreated.

## Verification

| Check | Time | Result |
|---|---|---|
| Container | 7:39 AM | `Up 15 seconds (healthy)`, created 7:39:21 AM |
| Bot log | 7:39:35 AM | `discord ready as Anubis AS#9583`, `http listening on :8080` |
| Synthetic alert `Alert bot dedupe test`, fingerprint `dedupe-test-20261112`, posted to `/grafana` three times as firing and twice as resolved, bearer read from `.env` on the host | 7:39:57 to 7:40:06 AM | responses `posted 1`, `0`, `0`, then `1`, `0`. Two messages reached `#bots`, `INFO: Alert bot dedupe test` and `Resolved: Alert bot dedupe test`, and the log shows three `dropped grafana batch` lines |
| `/tmp/alert-state.json` in the container | 7:40 AM | present, owned `bot`, 74 bytes |

## Open items

- Publish the rebuilt image to Forgejo with Dockhand's push control, so `forgejo.alphasecunited.com/homelab-images/alert-bot:stable` in the registry matches what runs.
- Each genuine change still posts. `Disk is saturated` fired and resolved every night between 3:25 and 4:05 AM from 2026-11-08 to 2026-11-11, which is a threshold question for that rule, not a repeat.
