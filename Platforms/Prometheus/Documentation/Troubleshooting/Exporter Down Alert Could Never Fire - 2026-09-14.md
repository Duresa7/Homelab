# Exporter Down Alert Could Never Fire

**Created:** 2026-09-14  
**Last updated:** 2026-09-14

## Symptom and cause

While reviewing the dashboard restyle I re-read the 24 alert rules and checked each one's expression against the live Prometheus API. `homelab-exporter-down`, titled *Metrics source stopped reporting*, cannot fire. It has never been able to fire.

The rule paired this expression

```
up{job!="node"} == 0 unless on(host) (up{job="node"} == 0)
```

with a threshold condition of `gt 0.5`.

A PromQL comparison without `bool` is a filter, not a test. It drops the samples that fail and keeps the ones that pass **at their original value**. So `up == 0` returns the down target carrying the value `0`, not `1`. Grafana reduced that with `last()` and asked whether `0 > 0.5`. It never is.

```
$ curl -s -G --data-urlencode 'query=vector(0) == 0' .../api/v1/query
  -> 0
$ curl -s -G --data-urlencode 'query=vector(0) == bool 0' .../api/v1/query
  -> 1
```

Forcing a real target down through the rule's own expression confirms it end to end:

```
$ curl -s -G --data-urlencode \
    'query=(up{job="wud",host="docker-blue"} * 0) == 0 unless on(host) (up{job="node"} == 0)' ...
  {"host":"docker-blue","instance":"192.168.40.39:9102","job":"wud"}  value 0
```

Value `0`, threshold `> 0.5`, no alert.

This is the rule that covers a dead exporter on a live host: cAdvisor, What's Up Docker, blackbox, the Proxmox exporter, NUT. Its own description says the condition lasted three and a half days in August 2026. That is what it was written for and what it silently did not catch.

The three sibling availability rules are all written the other way round, with an unfiltered expression and `lt 0.5`: *Host is down* on `up{job="node"}`, *Internal service is unreachable* on `probe_success`, *Proxmox node or cluster is down* on `pve_up`. This rule was the only one of the four that filtered.

I checked the other 23 rules for the same trap. Only this one has it. *VM or container is down* looks similar and is correct: its `and` chain takes the left operand's value, which is the `1` from `max_over_time(...) == 1`, and multiplying by `pve_guest_info` keeps it at 1. I verified that by running the rule's expression against a guest forced to zero, and it returns 1.

## Correction

I rewrote the rule to the same shape as its three siblings, in the [versioned rule file](../../Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml):

| | Before | After |
|---|---|---|
| Expression | `up{job!="node"} == 0 unless on(host) (...)` | `up{job!="node"} unless on(host) (...)` |
| Evaluator | `gt 0.5` | `lt 0.5` |
| `noDataState` | `OK` | `NoData` |

Dropping the filter means the rule reports every non-node target's raw `up` value and the threshold picks the zeros. `noDataState` moves with it: an empty result no longer means "everything is healthy", it means Prometheus itself did not answer, which is worth an alert rather than an OK. The `unless on(host)` suppression, the 10-minute `for`, the labels, the annotations and the rule UID are unchanged.

I left a comment in the rule saying why the filter must not come back.

## Verification

Four behaviours checked against live Prometheus before deploying:

```
healthy now          37 series, every value 1, fires on 0
wud forced down      value 0 -> lt 0.5 -> fires
host also down       0 series matched, so Host is down still covers it alone
no host label        21 blackbox and proxmox targets retained
```

The old expression returned the down target at value 0 and the new one returns it at value 0 as well; what changed is that the evaluator now agrees with the data.

## Deployment

Alerting provisioning is not re-read on an interval the way dashboards are, so this needed a restart. No Grafana administrator credential is in the inventory this account can reach, so the authenticated reload endpoint was not an option and a restart was the available path, as it was for [issue 7](Installation%20ISO%20Triggered%20Filesystem%20Capacity%20Alert%20-%202026-09-11.md).

I captured the alerting state first, copied the rule file up and confirmed its hash on the host before replacing anything, then restarted Grafana at 2026-09-15 03:16 UTC.

| | Before | After |
|---|---|---|
| Rules scheduled | 24 | 24 |
| Evaluation failures | 0 | 0 |
| Instances alerting | 15 | 15 |
| Instances normal | 293 | 329 |
| Instances in error or nodata | 0 | 0 |

The 36 extra normal instances are the fix working. The old filtered expression returned nothing while the fleet was healthy, so the rule tracked almost no instances; the new one reports all 37 non-node targets and holds them normal until one goes to zero.

Verified after the restart: Grafana health `database: ok` on 13.2.1, the file hash inside the container matching the repository at `97c95ea75b80037185f31ddfca7825f7b7820cd0794e8904290ab8da186195b5`, 24 rules in the database with this one carrying the new expression and a `lt 0.5` evaluator, the root policy and the Updates child route unchanged and still pointing at `discord-bot`, and the bot answering `ok` to Grafana over the Compose network. The 26 dashboards were unaffected.

## Limits

I have not confirmed a missed notification. Prometheus keeps 15 days, the contact point only went live on 2026-09-02, and every match inside that window was a single-scrape blip well under the 10-minute `for`. The one interval long enough to have fired was a 24-hour NUT outage on red-server ending 2026-09-01, which predates delivery. Nothing is known to have been missed. The rule simply could not have caught it.
