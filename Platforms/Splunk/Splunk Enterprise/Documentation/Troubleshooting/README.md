# Splunk SIEM Troubleshooting

**Created:** 2026-07-01  
**Last updated:** 2026-07-22

I record each Splunk and SC4S failure here with its cause, correction, & observed result. The [build log](../Build-Log.md) holds the deployment sequence.

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Where | Symptom | Root cause | Fix |
|:-:|---|---|---|---|
| <a id="1-rpm-install-failed-transaction-lock-permission-denied"></a>[1](RPM%20install%20failed%20transaction%20lock%20permission%20denied%20-%202026-07-01.md) | Step 5 | `rpm -i` → transaction lock permission denied | Ran without `sudo` | Re-ran with `sudo` |
| <a id="2-splunk-command-not-found-after-installing"></a>[2](splunk%20command%20not%20found%20after%20installing%20-%202026-07-01.md) | Step 5 | `splunk: command not found` | Install (#1) had failed; `/opt/splunk` was empty | Fixed once #1 succeeded |
| <a id="3-sc4s-unit-does-not-exist"></a>[3](SC4S%20unit%20does%20not%20exist%20-%202026-07-01.md) | Step 6 | `Failed to enable unit: sc4s.service does not exist` | Unit file never created | Created `/lib/systemd/system/sc4s.service` |
| <a id="4-sc4s-crash-loop-port-1514-already-in-use"></a>[4](SC4S%20crash-loop%20port%201514%20already%20in%20use%20-%202026-07-01.md) | Step 6 | SC4S crash-loop, `0.0.0.0:1514 Address in use` | `splunkd` already listening on 1514 (leftover TCP input) | Deleted the Splunk TCP input |
| <a id="5-search-returned-0-results-real-time-trap"></a>[5](Search%20returned%200%20results%20real-time%20trap%20-%202026-07-01.md) | Step 6 | Search returned 0 results | Time range was real-time | Switched to a historical range |
| <a id="6-unifi-test-event-missing-wrong-sourcetype"></a>[6](UniFi%20test%20event%20missing%20wrong%20sourcetype%20-%202026-07-01.md) | Step 6 | UniFi test event "missing" | Searched the wrong sourcetype | Searched `sourcetype=cef` instead |
| <a id="7-cef-header-fields-came-back-blank"></a>[7](CEF%20header%20fields%20came%20back%20blank%20-%202026-07-01.md) | Step 6 | CEF header fields blank | Guessed field names; SC4S already parses CEF | Used real field names |
| <a id="8-only-one-unifi-product-routed-to-netops"></a>[8](Only%20one%20UniFi%20product%20routed%20to%20netops%20-%202026-07-01.md) | Step 6 | Only `UniFi OS` routed to `netops` | UniFi sends 3 product strings; only 1 key defined | Added all 3 routing keys |

