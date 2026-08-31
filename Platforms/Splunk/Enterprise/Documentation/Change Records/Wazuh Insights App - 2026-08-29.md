# Wazuh Insights App

**Created:** 2026-08-29  
**Last updated:** 2026-08-31

## Date

I started this change on 2026-08-29 and finished it on 2026-08-30.

## Scope

I built `wazuh_insights`, a Splunk app that receives Wazuh alerts on port 9997, maps them onto the Common Information Model so Enterprise Security can use them, and presents one dashboard that answers what my machines are reporting. It mirrors the `unifi_insights` app I built on 2026-08-28 for the UniFi pipeline.

The forwarder that feeds it is in [Alert Forwarding to Splunk](../../../../Wazuh/Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md). The two Wazuh-side changes that decide what is worth forwarding are [File Integrity Monitoring Widening](../../../../Wazuh/Documentation/Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md) and [Malware Detection](../../../../Wazuh/Documentation/Change%20Records/Malware%20Detection%20-%202026-08-29.md).

The four together are written up as one followable path in [Wazuh Alerts in Splunk](../../../../../Guides/Wazuh-Alerts-in-Splunk.md), which is the guide a reader outside this lab would start from.

The app is committed at [Configuration/wazuh_insights](../../Configuration/wazuh_insights/) and installed at `/opt/splunk/etc/apps/wazuh_insights` on `splunk-siem`, running Splunk Enterprise 10.4.0 build `f798d4d49089` with Enterprise Security.

## What the dashboard is for

I did not want a dashboard of everything Wazuh can produce. The question I wanted answered was closer to: if something bad arrived on a machine, would this page show it. So the top strip is seven counts that should normally be zero or near it, and everything below exists to answer "why is that number not zero".

| Tile | What it counts | Window |
|---|---|---|
| Machines gone quiet | Agents seen in the last 7 days that have said nothing for 24 hours | 7 days |
| Malware found | A local known-bad hash match, or VirusTotal reporting detections | 24 hours |
| Off-network logins | Successful logins from an address outside RFC1918 | 24 hours |
| Watched files changed | File-integrity events across every agent | 24 hours |
| Scheduled task changes | Changes under cron and systemd unit directories | 7 days |
| Software added or removed | Package manager activity | 7 days |
| Listening port changes | A machine started or stopped listening on a port | 7 days |

Below them: alerts over time by machine, the VirusTotal lookup budget, alerts by machine, the most-changed watched files, a login table, and the whole stream newest first.

**Quiet agents cannot be derived from alert volume, and that shaped one tile.** A healthy machine with nothing to report sends nothing, so "no alerts" and "agent is down" look identical if you only count. The tile is therefore "seen in the last 7 days, silent for the last 24", which distinguishes a machine that stopped talking from one that was never enrolled.

**I checked every panel had data before building it.** The one exception is listening port changes, rules 533 and 534, which has no events yet. The netstat collector is configured and those rules only fire on a change, so an empty panel is the correct answer rather than a broken one.

## CIM mapping

`props.conf` for `[wazuh:alerts]` does the work: `KV_MODE = json`, `TRUNCATE = 32768`, and timestamps from `TIME_PREFIX = "timestamp":"` with `TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3N%z`. Aliases put `agent.name` on `dest`, `data.srcip` on `src` and `rule.description` on `signature`.

**Event classes key on `rule.groups{}`, not on rule IDs.** Rule IDs change between Wazuh releases and when a local rule overrides a stock one. Group names do not. The seven eventtypes in `eventtypes.conf` all match on groups for that reason.

Two mapping mistakes are worth recording because both were invisible until I looked at what Enterprise Security did with the result.

**`EVAL-object_category = "file"` was unconditional.** Enterprise Security tags an event into the Endpoint Filesystem data model when `object_category` is `file`, so an unconditional assignment put 905 of 925 non-file events into a filesystem model. The fix is a conditional:

```ini
EVAL-object_category = case(isnotnull('syscheck.path'), "file", isnotnull('data.package'), "package", 1==1, null())
EVAL-status = case(isnotnull('syscheck.path') OR isnotnull('data.package'), "success", 1==1, null())
```

After the change, the count of non-syscheck events carrying the `filesystem` tag is 0.

**The malware macro counted VirusTotal's error messages as malware.** `wazuh_malware_found` matched the whole `virustotal` group, and the integration raises an alert for every outcome it has, including 87101 for a rate-limit refusal and 87103 for a file the service has never seen. Those are the integration reporting on itself. The tile read 2,941 when the true number was 2. Only 87105 carries `data.virustotal.malicious = 1`, so that field is what it keys on now:

```ini
[wazuh_malware_found]
definition = index=wazuh sourcetype=wazuh:alerts ("data.virustotal.malicious"=1 OR "rule.groups{}"=known_bad_hash OR "rule.groups{}"=trojan OR "rule.groups{}"=rootkit)
```

The general lesson is that a product's own operational messages sit in the same group as its findings, and a group match cannot tell them apart.

## Two things about Dashboard Studio

**A multiselect input broke the whole definition.** The first version rendered `Layout undefined is not defined` and no panels at all. The cause was an `input.multiselect` with a `prefix`/`suffix`/`delimiter` schema. A definition either parses or it does not, so one bad input takes the page down rather than that one control. I rebuilt on the shape already proven by `unifi_threat_center.xml`: `layout` keys `type`, `options`, `structure`, `globalInputs`, with `input.timerange` as the only global input.

**A panel can pin its own time window in SPL, and I nearly built something unnecessary to do it.** The quiet-agents tile has to look back 7 days regardless of what the picker says. I first moved it to a saved search, which did not render in a single-value panel. Then I read the job's messages and found Splunk had been saying so all along:

```text
INFO  Your timerange was substituted based on your search string
```

Writing `earliest=-7d latest=now` in the search string overrides the dispatch range the picker sets. The tile is a plain `ds.search` again. The saved searches stayed, because alerts attach to those and that is the next piece of work, but no panel depends on them.

**`_time` renders as a formatted timestamp only while it is still called `_time`.** `| table _time, ... | rename _time as Time` printed raw epochs. The tables now do `eval Time=strftime(_time,"%Y-%m-%d %H:%M:%S")` after sorting.

## Verification

**The dashboard renders with every panel populated.** The final capture shows all seven tiles, both charts, all four tables. Malware found reads 4, which is the EICAR test detected twice by two independent mechanisms, twice over.

**The receiving side works.** `[splunktcp://9997]` with `connection_host = ip`, and the forwarder holds an established connection to it. `index=wazuh` reached 5,750 events, from all 16 agents.

**Retention is set.** `frozenTimePeriodInSecs = 2592000` and `maxTotalDataSizeMB = 5120` on `[wazuh]`.

Captures are in [Evidence](../../Evidence/Wazuh%20Insights%20App%20-%202026-08-29/).

## What I removed from the index, and why

Twice I deleted events rather than waiting for them to age out. Both times the reason was the same: the configuration that produced them had been corrected, so the data was a record of a setting I no longer have.

| What | Splunk | Wazuh indexer |
|---|---|---|
| Scratch files under `/tmp` that the corrected FIM restrict no longer collects | 2,646 | 2,853 |
| Proxmox `/etc/pve` state files the new proxmox group ignores | 123 | 5,570 |
| Rootcheck trojan false positives on `/bin/chfn`, `/bin/chsh`, `/bin/passwd` | 471 | 22,190 |

`| delete` needs care in Splunk. The `search/jobs/export` endpoint accepts it and reports success without removing anything, and `admin` does not hold `can_delete` by default. Each purge was a blocking job submitted to `/services/search/jobs`, with `can_delete` granted immediately before and revoked immediately after. Every run reported `errors 0`.

One deletion went further than I meant. The `/tmp` purge took with it the single VirusTotal verdict that proved malware detection worked, because that test file had been written under `/tmp`. I re-ran the test in `~/Downloads` and got a better result than the one I lost, since the quota had recovered by then and both detection paths fired. That is in the malware record.

## Remaining work

- Alerting. The dashboard is a page you have to open. The backlog entry is in the [Enterprise Security TODO](../../../Enterprise%20Security/Documentation/TODO.md).
- A machine and severity filter on the dashboard, now that the base render is confirmed.
- Splunk's own internal indexes hold 22.1 GB against 99 MB of real UniFi data, noted in [Root Filesystem Expansion](Root%20Filesystem%20Expansion%20-%202026-08-29.md) and still untrimmed.
