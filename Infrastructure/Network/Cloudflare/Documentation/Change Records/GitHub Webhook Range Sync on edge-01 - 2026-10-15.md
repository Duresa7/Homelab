# GitHub Webhook Range Sync on edge-01

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-15  
**Status:** Complete  
**Affected systems:** edge-01 (`github-webhook-ranges.timer`), the Cloudflare account API token `edge-01 GitHub Webhook Ranges`, the Zero Trust IP list `GitHub Webhooks`, Grafana alert rule `homelab-github-webhook-ranges-stale` on monitor-01  
**Earlier change:** [Coolify Webhook Bypass Limited to GitHub - 2026-10-15](Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md)

This morning I limited the Coolify webhook's Access bypass to the IP list `GitHub Webhooks`, which left me a list to maintain by hand. GitHub changes its `hooks` ranges a few times a year, and a delivery from a range the list lacks fails at Access with nothing but a red row on GitHub's Recent Deliveries page to say so. edge-01 now keeps the list in step with `api.github.com/meta` once a day, and Grafana tells me if that stops happening. I chose edge-01 over a Cloudflare Worker because it already runs the tunnel and a timer-driven collector of the same shape, and because a job on a host I monitor can raise the alert a Worker could not. All times are EDT.

## What changed

### The token

I created the account API token `edge-01 GitHub Webhook Ranges` in the Cloudflare dashboard under Manage account, Account API tokens, with one permission, **Zero Trust Edit** on the entire account, no client IP filter and no expiry. Zero Trust Edit is the permission that covers Gateway lists; Access permissions alone do not reach them. The token sees exactly one account, so the script discovers the account from `GET /accounts` and the env file holds nothing but the token.

The token is stored in the password manager as `Cloudflare Account API: edge-01 GitHub Webhook Ranges`. I moved it to edge-01 by piping the manager's CLI read over SSH into a `0600` staging file, then installing that file as root; the value never appeared in a command string, a transcript or this repository.

### On edge-01

| Path | Owner and mode | Purpose |
|---|---|---|
| `/usr/local/lib/github-webhook-ranges.py` | `root:root 0755` | The sync, Python 3.13 with the standard library only |
| `/etc/systemd/system/github-webhook-ranges.service` | `root:root 0644` | `Type=oneshot`, reads the env file, hardened like `edge-uptime.service` |
| `/etc/systemd/system/github-webhook-ranges.timer` | `root:root 0644` | `OnCalendar=*-*-* 06:20:00`, up to 10 minutes of random delay, `Persistent=true` |
| `/etc/cloudflare/github-webhook-ranges.env` | `root:root 0600`, directory `0750` | `CLOUDFLARE_API_TOKEN` only |
| `/var/lib/prometheus/node-exporter/github-webhook-ranges.prom` | written `0644` on every run | Five gauges for Prometheus |

The script, service and timer are versioned in [Scripts](../../Scripts/). A configurable version with its own tests and README is published as `automation/cloudflare-webhook-ranges` in the [tools-and-scripts](https://github.com/Duresa7/tools-and-scripts) repository; edge-01 runs the plain script here. Each run fetches the `hooks` key from `https://api.github.com/meta`, normalises every entry as a network, and refuses to continue if fewer than three come back, so an empty or broken answer can never empty the list. It then finds the list by name under `/gateway/lists?type=IP`, reads its items, and if the two sets differ sends one `PATCH` with the ranges to append and remove, then reads the list back and fails if it does not match. It never deletes the list and never touches the Access policy. A failed run exits non-zero, writes `github_webhook_ranges_last_run_ok 0`, and keeps the previous success timestamp so the alert below can age it.

### In Grafana

I added `homelab-github-webhook-ranges-stale`, title `GitHub webhook range sync has stopped`, to the Network group of the [provisioned alert rules](../../../../../Platforms/Prometheus/Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml). Its query is `time() - github_webhook_ranges_last_success_timestamp_seconds`, so the value the threshold sees is the age in seconds, and it fires at warning after 30 minutes above 172800, two days. `noDataState` is OK, because edge-01 being down already fires `Host is down`. It carries `category: network` and no `class`, so the Discord bot files it as infrastructure like the other 21 unclassed rules.

I wrote the file to `/home/dkadi/monitoring/grafana/provisioning/alerting/` on monitor-01 after checking the deployed copy matched the committed one at SHA-256 `4e8d4908…`, read back `4a507e1f…`, and reloaded through `POST /api/admin/provisioning/alerting/reload`, which answered `Alerting config reloaded`. I did not restart Grafana.

## Verification

- **First run, 9:39:27 AM.** `systemctl start github-webhook-ranges.service` exited 0 and the journal read `9 ranges, no change`. The metrics file showed `last_run_ok 1`, `count 9`, `changed 0`.
- **Add-back test, 9:39:43 AM.** I removed `143.55.64.0/20` from the list through the Cloudflare API and confirmed the list held 8 entries. The next run logged `adding ['143.55.64.0/20'] removing []`, and the metrics showed `count 9`, `changed 1`. The API read back all nine ranges in the list, and the Access policy `GitHub Webhook Bypass` still had the single `ip_list` include with decision `bypass`.
- **Timer.** `systemctl enable --now github-webhook-ranges.timer` created the `timers.target.wants` symlink; `list-timers` shows the next run at 6:23:29 AM on 2026-10-16.
- **Prometheus.** `github_webhook_ranges_last_success_timestamp_seconds{host="edge-01"}` returned `1792071583.656` from the existing node scrape, and `time() - …` evaluated to 20.66 seconds.
- **Grafana.** The provisioning API returned the rule with `provenance: file`, group `Network`, `for: 30m`, the expression above and threshold `172800`; 25 rules are provisioned. The rules endpoint reported the rule `inactive` with health `ok`.

The tokens on the GitHub side are unchanged: the Coolify GitHub App's redelivery earlier today already proved the delivery path, and the list's contents after the add-back are identical to what that test ran against.

## Rollback

`systemctl disable --now github-webhook-ranges.timer` stops the sync and leaves the list as it stands. Revoking the token in the dashboard does the same and makes the alert fire two days later. Removing the rule from the alert file and reloading drops the alert.

## Open

- [ ] Confirm the Security Insights finding on the Coolify webhook clears on its next scan; tracked in the [bypass record](Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md#open).
