# Latency Rule Fired on Failed Probes

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

## Symptom and cause

On 2026-09-18 the Sonarr, Radarr and Prowlarr probes stopped completing. Grafana sent three warnings:

```text
WARNING: Internal service is responding slowly
https://sonarr.alphasecunited.com/ is taking 9.501s to respond.
```

`probe_success` was `0` for all three at the time. Nothing was responding slowly; three probes were failing outright, and the alert that arrived described the wrong condition. Its own description sent me looking at "DNS resolution, the proxy, or a backend that is alive but struggling" when the path was dead.

`homelab-service-slow` paired this expression

```text
probe_duration_seconds
```

with a `gt 5` evaluator and a 10 minute `for`, and had no liveness precondition. A probe that times out still reports a duration, and the duration it reports is its deadline: 9.5 seconds here, which is Prometheus' default 10 second `scrape_timeout` less blackbox_exporter's default 0.5 second `--timeout-offset`. Any hard probe failure therefore clears a 5 second threshold by definition, so this warning fires on every one of them.

`homelab-service-unreachable` already covers that condition properly, on `probe_success` with `lt 0.5` and a 5 minute `for`, at critical. The latency warning was duplicating a rule that was already correct, five minutes later, with text that misdirects.

This is not [issue 8](Exporter%20Down%20Alert%20Could%20Never%20Fire%20-%202026-09-14.md)'s trap. Both rules were internally consistent and both did what they said. The defect is that the latency rule never asked whether the measurement it was thresholding came from a probe that finished. It applies to all 23 blackbox targets, not only the three that exposed it.

## Correction

I gated the expression on a successful probe, in the [versioned rule file](../../Configuration/grafana/provisioning/alerting/alphasec-united-alerts.yaml):

| | Before | After |
|---|---|---|
| Expression | `probe_duration_seconds` | `probe_duration_seconds * probe_success` |
| Evaluator | `gt 5` | unchanged |
| `for` | 10m | unchanged |
| `noDataState` | NoData | unchanged |

Multiplying rather than filtering is deliberate. `and on(instance) (probe_success == 1)` produces the same alerting behaviour, but it drops a failing target out of the result, so the instance disappears from the rule while it is down. The product keeps all 23 targets in the rule at all times and leaves the test to the evaluator, which is the shape issue 8 settled on for the availability rules.

The product is written without `on(instance)` because both metrics carry the identical label set, `{instance, job}`. A plain product matches one to one and keeps both labels, so this rule's instance identity still matches its sibling's. Adding `on(instance)` would have dropped `job`.

I also rewrote the description, which is now only ever shown for a probe that completed, and left a comment in the rule saying why the multiplication must not be removed.

## Verification

Four checks against live Prometheus before deploying anything:

```text
gated expression, healthy       23 series, values identical to raw probe_duration_seconds
probe forced to fail            (duration 9.5, success 0) -> 0, cannot reach gt 5
same case through the old expr  9.5 -> clears gt 5, which is the defect
label set                       {instance, job} preserved by the plain product
```

Alerting provisioning is not re-read on an interval, so this needed a Grafana restart, as [issue 8](Exporter%20Down%20Alert%20Could%20Never%20Fire%20-%202026-09-14.md) did. I edited the deployed file in place and confirmed it hashed to the repository copy at `906f528ee67346bb65c157717af19410a9a56393121efd06dc4ef98dc07239e8` before restarting Grafana at 10:47 PM. The previous version of the file is in git, so no separate copy was taken.

| | Before | After restart | Settled 10:51 PM |
|---|---|---|---|
| Rules scheduled | 24 | 24 | 24 |
| Evaluation failures | 0 | 0 | 0 |
| Instances alerting | 16 | 16 | 16 |
| Instances normal | 343 | 366 | 343 |
| Instances in error or nodata | 0 | 0 | 0 |

The 23 extra normal instances immediately after the restart are the count of blackbox targets, and they aged out within four minutes. The product drops the `__name__` label the bare metric carried, so every instance of this rule took a new identity and the old ones lingered briefly alongside the new ones.

Grafana 13.2.2 returned `database: ok`, and no provisioning error appeared in its startup log. Read back through the provisioning API, the rule carries the new expression with its `gt 5` evaluator, 10 minute `for` and `NoData` unchanged, 24 rules are provisioned, and `homelab-service-unreachable` is still on `probe_success` with `lt 0.5` and its 5 minute `for`. Both blackbox rules track 23 instances and both are inactive.

## Probe targets stay at the service root

I considered moving the three Arr probes to `/ping`, which answers 200 with no redirect, and kept `/` instead.

The reason to move was that the failing probe followed an `http://` redirect to a port the monitoring VLAN cannot reach. That was a symptom of the [Arr proxy trust fault](../../../Media%20Stack/Documentation/Troubleshooting/Lost%20Proxy%20Trust%20Broke%20Arr%20HTTPS%20Redirects%20-%202026-09-18.md) and not a property of probing the root. With the redirect scheme corrected, the whole chain is one TCP connection on 443: `curl` reports `num_connects=1` and one redirect for each of the three, ending at 200.

The reason to stay is stronger. Probing the root is what caught that fault. `/ping` would have answered 200 throughout and the downgrade would have gone unnoticed. The job's stated purpose is to walk the path a person walks, and the login redirect is part of that path. I recorded the decision as a comment in the blackbox job in [prometheus.yml](../../Configuration/prometheus-config/prometheus.yml) so it is answered where it would next be asked, and reloaded Prometheus by SIGHUP at 10:50 PM. `promtool check config` passed, `prometheus_config_last_reload_successful` returned 1, the container was not restarted, and 57 active targets remain up with 23 probes passing.

## Limits

I have not observed the corrected rule suppress a live failure, because nothing has failed since it was deployed. The behaviour is established by running both expressions against a forced-failure case in live Prometheus, not by waiting for an outage.

Grafana's notification history was not examined, so I cannot say how many of the 4,278 firing notifications it has sent since 2026-09-02 were this rule duplicating a real unreachable alert.
