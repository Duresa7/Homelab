# Uptime Dashboard

**Created:** 2026-09-15  
**Last updated:** 2026-09-15

**Implemented:** 2026-09-15

I added [Uptime](https://grafana.alphasecunited.com/d/uptime) to the Homelab folder. I used the supplied status-page image as the layout reference: an overall status banner followed by one service per row, separate history bars, uptime percentage, and coverage. Grafana remains on its existing private access path. I changed no DNS, tunnel ingress, firewall, authentication, or alert delivery policy.

## Coverage

I display 29 checks:

- TeamSpeak ts02 and ts03, each measured through its public Playit UDP path.
- Cloudflare Tunnel connection health on edge-01.
- Caddy's local HTTP listener and Coolify's origin, measured separately from edge-01.
- All 23 monitored internal HTTPS names through NPM, including the newly added CLI Proxy API, Executor, MeshCentral, and NetBird probes.
- The Discord alert bot's existing health endpoint.

I verified app-01's live container inventory: it currently runs the Coolify platform and proxy, with no deployed application containers. I therefore show the connector and origins separately. An Access login response would not establish that Coolify's origin works, so I do not count it as application uptime. The TeamSpeak probes traverse the public relay from alpha-prod-01; I have no independent off-site probe. HTTP login and expected authorization responses establish reachability, not completion of an authenticated user workflow. I did not add the NPM administrative listener: the test from monitor-01 timed out on port 81. The application probes exercise NPM's actual HTTPS service path.

## State and percentages

| Display | Meaning |
|---|---|
| Green | Successful response; Cloudflare has at least four connections |
| Yellow | HTTP response above 2 seconds, TeamSpeak UDP response above 250 ms, or Cloudflare has one to three connections |
| Red | Probe failed, Cloudflare has zero connections, or cloudflared is stopped |
| Gray | Missing/stale observations, failed monitoring scrape, or unreadable connector metrics |

I reject HTTP observations older than 90 seconds and textfile collector timestamps older than 180 seconds. I remove relay labels with aggregation before returning TeamSpeak data to Grafana.

Each history bar shows the worst sampled state within its interval, including unknown time. I use Grafana's built-in [status history panel](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/status-history/) with gaps between bars and a maximum of 90 displayed points. No plugin or HTML panel is required.

The default view is 14 days against the existing 15-day Prometheus retention. I do not invent a 90-day history. New checks show gray before installation; existing checks reuse retained raw probe data. Uptime is successful one-minute observations divided by known observations over the selected range. A degraded response still counts as reachable. Coverage divides known observations by the selected duration, so unknown time cannot disappear behind a 100% uptime figure. I use [Prometheus range functions](https://prometheus.io/docs/prometheus/latest/querying/functions/) for these sampled calculations.

The target is 99.99%, displayed to four decimal places. Uptime below 99.9% is red, 99.9% through less than 99.99% is yellow, and at least 99.99% is green. This is a target comparison of sampled availability, not proof of uninterrupted service. One-minute probes can miss shorter failures. Uptime and Coverage have separate columns because a newly installed probe can have 100% observed uptime with almost no historical coverage.

## Deployment

I added `Tools/uptime.py` to the existing dashboard generator and rebuilt the JSON. The two existing reachability totals now derive 23 HTTPS names from the same inventory. The generated `uptime.json` has 120 data panels and three section rows. I added stable panel IDs.

I installed `Scripts/edge-uptime.py` as `/usr/local/lib/edge-uptime.py` on edge-01 with `edge-uptime.service` and `edge-uptime.timer`. The timer runs every minute. Its service has a read-only system filesystem, private temporary directory, and write access to the existing textfile directory. The collector reads loopback metrics and writes `/var/lib/prometheus/node-exporter/edge-uptime.prom` atomically. Only a connection count, two HTTP results, and the completion timestamp are exported.

The first SSH sudo invocation passed a multiline command without a shell wrapper and did not install the files. I corrected it to execute the installation and systemd steps inside `bash -c`; the timer then became active and all four metrics appeared. I later made an inactive/failed cloudflared service explicitly report zero connections and verified that behavior with fixtures.

The live Prometheus configuration differed from the tracked baseline only by one trailing blank line. I validated the staged file with `promtool check config`, wrote the four additional targets, and sent Prometheus SIGHUP. Its first validation preceded the new targets' first scrape, so the four new uptime percentages were empty. After their first observations, all 120 dashboard queries returned data.

I installed three generated dashboard files: Uptime, Homelab Overview, and Services & Uptime. Grafana loaded them through its existing provider interval without a restart. I read the new dashboard from Grafana's live SQLite unified storage in read-only mode: 27 dashboards, with `uptime` titled `Uptime` and 123 panel objects.

I removed the deployment archive, staged files, and Prometheus test fixtures after verification. The first fixture cleanup used the container's unprivileged default user and could not remove files copied into `/tmp`; repeating that bounded removal as container root succeeded.

I retained the observed results below rather than a full command transcript. I made no configuration backup or snapshot; the prior configuration and existing dashboard versions remain in git.

## Verification

| Check | Observed result |
|---|---|
| Offline layout check | 27 unique dashboard UIDs; no overlapping/out-of-bounds panels |
| Collector unit tests | 3 passed, including stopped connector, missing/malformed metrics, and atomic output |
| PromQL fault fixtures | 17 passed through `promtool test rules`, covering HTTP/UDP failure and latency, stale/missing observations, Cloudflare states, coverage, uptime, and a brief outage inside a history bar |
| Live target assertion | 58 expected targets present and healthy; 24 HTTP probes; retired addresses absent |
| Full dashboard query assertion | 1,466 queries across 27 dashboards; 1,445 returned data, 21 correctly empty, zero errors or unexpected empty results |
| Default 14-day Uptime queries | All 120 returned data; complete sequential pass took 4.32 seconds |
| Current service state | All 29 operational at verification |
| Edge collector | Four tunnel connections, both HTTP origins up, active timer |
| Grafana | 13.2.1; database health `ok`; Uptime present in provisioned storage |

## Remaining limits

I could not complete an authenticated browser appearance check with the available session. The CLI service account can read the alert-bot secret but has no Grafana login item; the separate interactive CLI account is signed out. The deployed dashboard and its queries are verified above. Longer retention, independent off-site probes, and authenticated application transactions remain outside this change.
