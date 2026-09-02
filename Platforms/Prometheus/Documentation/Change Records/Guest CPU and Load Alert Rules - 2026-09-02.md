# Guest, CPU and Load Alert Rules

**Created:** 2026-09-02  
**Last updated:** 2026-09-02

**Implemented:** 2026-09-02  
**Status:** Rules complete; notification destination open  
**Affected systems:** Grafana 13.2.0 on `monitor-01`

## Change

I added three rules to the file introduced in [Grafana Alert Rules - 2026-09-01](Grafana%20Alert%20Rules%20-%202026-09-01.md), bringing it to 15. That first set answered three of the questions I had asked of it, "is a machine down", "is a service unreachable" and "is a UPS on battery", but it could not name a guest that had stopped and it had no CPU rule at all.

| Rule | Group | Fires when | For |
| --- | --- | --- | --- |
| VM or container is down | Availability | a guest reported running at any point in the last two hours is now reported stopped | 5m |
| CPU is pinned | Capacity | `pve_cpu_usage_ratio` above 0.9 for any guest or node | 15m |
| Host is overloaded | Capacity | 15-minute load average above 2 per core on a hypervisor | 15m |

**Naming the guest.** The 2026-09-01 set scoped Proxmox alerting to nodes and quorum on purpose, because `qemu/101`, `qemu/102` and `qemu/9000` are stopped deliberately and a plain `pve_up == 0` rule would have fired three false alarms on load. The new rule reads "was up within the last two hours and is down now", which separates a crash from a guest I stopped myself, and joins `pve_guest_info` on `id` so the alert carries `name` and `node`. `pve_guest_info` has one series per guest, 16 of 16 on 2026-09-02, so the join drops nothing. The cost is that a guest I stop deliberately fires once and clears itself two hours later. I looked at `pve_onboot_status` as the cleaner filter and rejected it: the exporter reads guest configuration only from the node it is pointed at, so it returned 5 series, all on `grey-server`, for 16 guests.

**CPU from Proxmox, not node_exporter.** `pve_cpu_usage_ratio` is Proxmox's own figure and is already relative to the cores a guest holds, so one rule covers all 16 guests and 5 nodes without a per-host core count and without anything to deduplicate. Guests get their name joined in; nodes pass through under their `id` with `or`. The busiest series on 2026-09-02 was `media-01` at 0.575.

**Load average is hypervisor-only for a reason.** lxcfs does not virtualise `/proc/loadavg`. On 2026-09-02 `ansible-01`, `docker-main` and `grey-server` all read 2.06, and `docker-blue`, `monitor-01` and `blue-server` all read 0.25: the guests report their host's number. Unfiltered, one overloaded node would alert three times. The highest per-core figure that day was `red-server` at 0.367 against a threshold of 2.

**Memory is unchanged.** The existing rule already covers it at 92% for 15 minutes across the 18 node_exporter hosts. I did not add a Proxmox-side memory rule: 13 of the 16 guests run node_exporter and a second rule would report each of them twice.

## Deployment

I validated the three expressions against the live Prometheus API before writing them into the file: the guest rule returned 0 series with 13 guests counted as up in the window, the CPU rule returned 21 series, and the load rule returned 5. I copied the file to `/home/dkadi/monitoring/grafana/provisioning/alerting/homelab-alerts.yaml` and called the authenticated `POST /api/admin/provisioning/alerting/reload`, which returned HTTP 200 at 5:28:36 AM Eastern. Grafana logged `finished to provision alerting` 133 milliseconds later with no error between the two lines. No container was restarted.

## Verification

- YAML parsing found four groups and 15 unique rule UIDs; the Availability group holds 5, Capacity 6, Network 1, Power and hardware 3.
- `/api/v1/provisioning/alert-rules` returned 15 rules, every one with provenance `file`, and the three new UIDs `homelab-guest-down`, `homelab-cpu-pinned` and `homelab-load-overloaded` present.
- The rule state API reported 15 rules, 0 unhealthy and 0 firing. All three new rules read `state=inactive`, `health=ok`.
- The deployed file and the repository file share SHA-256 `e6285bfa101e4beda65dfa3e79668ca45fc32376450f6efbf4b8a9a55f5c7d34`.

I created no snapshot or backup. The previous version of the file is the parent commit.

## Remaining Work

Unchanged from the first record: no contact point exists, the root notification policy's receiver is `empty`, and SMTP is disabled, so a firing rule is visible inside Grafana and nowhere else. A Discord webhook is the agreed next step and is tracked in the [Prometheus backlog](../TODO.md).
