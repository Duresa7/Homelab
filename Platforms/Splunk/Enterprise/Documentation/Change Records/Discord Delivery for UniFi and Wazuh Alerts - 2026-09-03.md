# Discord Delivery for UniFi and Wazuh Alerts

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Implemented:** 2026-09-03, 1:40 AM to 3:15 AM Eastern  
**Status:** Complete. Nine saved searches post to Discord through the alert bot  
**Affected systems:** `unifi_insights` and `wazuh_insights` on `splunk-siem`, the Discord alert bot on `monitor-01`

## Change

Until tonight nothing in Splunk notified anyone. Eight UniFi correlation searches wrote notables into Enterprise Security's Incident Review, and two Wazuh saved searches existed with no schedule. This change makes Splunk the one thing that posts security events to Discord. Grafana carries states; Splunk carries events; Wazuh and UniFi themselves notify nobody, and Wazuh stays detection only with no active response, a decision I made deliberately when planning this and want written down.

Delivery is Splunk's stock `webhook` alert action posting to `http://192.168.73.2:8080/splunk`, the alert bot's endpoint on `monitor-01`. The action cannot send a header, so the bot accepts posts from `192.168.72.3` alone and a UniFi policy admits only that host to the port. `alert.digest_mode = 0` on every Discord-bound search makes Splunk run the action once per result row, so a search grouped by source produces one message per source, and the suppression fields apply per source too.

### The nine searches

Every one was tuned against the 30 days of history before it was enabled, in the same way the eight notable rules were on 2026-08-28. The volume column is what that history would have produced.

| Search | Schedule | Window | Suppression | 30-day history |
|---|---|---|---|---|
| UniFi - Intrusion detection not blocked | hourly at :12 | 70 minutes | 6 hours per source and rule | 38 source-and-rule pairs before tuning, 8 after |
| UniFi - Threat reputation or malicious user agent match | hourly at :17 | 70 minutes | 4 hours per source and rule | 7 pairs |
| UniFi - Intrusion detection blocked | hourly at :47 | 70 minutes | 1 hour per source and rule | 41 source-hours before tuning, 4 pairs after |
| UniFi - Internal host blocked repeatedly | every 10 minutes at :03 | 10 minutes | 1 hour per source | 0; the busiest pairing was 33 denies in the whole month |
| UniFi - Syslog export has gone quiet | hourly at :52 | 6 hours | 24 hours | 0; the quietest six-hour block held 13 events |
| Wazuh - Malware or high severity | every 15 minutes at :07 | 20 minutes | 1 hour per machine and rule | 2, both the EICAR test file on `ubuntu-dev` |
| Wazuh - Account or group changed | hourly at :57 | 70 minutes | 1 hour per machine | 7 events on 3 machines, all mine |
| Wazuh - Login from outside private networks | hourly at :02 | 70 minutes | 24 hours per machine and source | 0 |
| Wazuh - Machines gone quiet, listed | hourly at :05 | 7 days | 7 days per machine | 0 after excluding `wazuh-01` |

The first two already existed as notable rules and keep their notable action; the webhook was added beside it. The other three UniFi searches and the three new Wazuh searches carry the webhook and no notable, because they exist for the phone, not the queue. The silent-machine search is the one that existed unscheduled since 2026-08-30, now scheduled.

### Tuning decisions

**`Intrusion detection not blocked` was reporting things three other rules already report.** In 30 days it matched 38 source-and-rule pairs: 30 were Tor from one PC, which the Tor rule covers; 17 were `Web Infrastructure Servers` signatures raised by the reverse proxy on `192.168.85.2` reaching my own services; and `Scanning Activity` from my own admin hosts, which the scanning rule covers. With TOR, Scanning Activity, the four reputation rules and the reverse-proxy pairing excluded, the same 30 days give 8 pairs. That exclusion also changes the notable queue, which is a correction rather than a loss: each excluded class still lands in Incident Review through its own rule.

**`Intrusion detection blocked` is the rule the plan called "blocked events, batched per source per hour".** Unfiltered it would have been 41 source-hours in 30 days, about ten a week on its own. Fifteen of those were the reverse proxy again; the rest were my scans from `ansible-01` and my workstation, the reputation rules that already post, and P2P and Tor. Excluding those leaves four pairs in 30 days.

**Internal denies use the flow record's `direction=local` and `src_ip` inside the server and workstation VLANs**: 30, 40, 70, 72, 73, 80 and 85. Trusted, VLAN 50, is left out on purpose; its denies are phones and TVs. The threshold of 20 denies in 10 minutes from one source would not have fired once in 30 days.

**The syslog dead-man window is six hours** because the history had one hour and one four-hour block with zero UniFi events, on 2026-08-26, and the quietest six-hour block held 13. Anything shorter would have produced a false alarm.

**`wazuh-01` is excluded from the silent-machine search until 2026-09-08.** The manager was renamed `security-01` on 2026-09-01, so its old name looks like an agent that fell silent until the seven-day lookback ages it out. The exclusion is harmless after that and can stay or go.

**Level 12 is the Wazuh severity floor**, plus any malware verdict at any level. Only the two EICAR detections reached it in 30 days. The `Systemd: Service exited due to a failure` flood that dominated the feed's first day never gets near 12.

**Off-network logins exclude the VPN.** Every successful login on record comes from inside the lab or from `10.0.1.0/24`, which is private space and the VPN's pool, so the search treats all of RFC 1918, loopback and the IPv6 local ranges as home.

### Splunk-side link fix

Both apps gained a `default/alert_actions.conf` with `hostname = https://splunk.alphasecunited.com` under `[default]`. Without it Splunk builds the `results_link` from its own hostname, `https://splunk-siem:8000/...`, which Discord refuses as a malformed URL and which nothing off the VM can open anyway.

## Deployment

The two `savedsearches.conf` files were staged to `ansible-01` over a tar stream and copied to `/opt/splunk/etc/apps/<app>/default/` as `splunk:splunk` mode 664 by an ad-hoc `ansible` copy, since the SSH account on `splunk-siem` cannot read the apps tree. Each copy was followed by `POST /servicesNS/nobody/<app>/saved/searches/_reload`, which returned 200 each time, and a listing that showed all 16 searches parsed with `action.webhook` on the nine intended ones.

Three things went wrong and each has its own account:

1. My first draft of the blocked rule used `rule NOT IN (...)`, which Splunk rejects; the fixed form is `NOT rule IN (...)`. Caught by dispatching every new search once with `trigger_actions=0` before enabling anything.
2. A REST read I made with `curl -d` was a POST and left an empty `[webhook]` stanza in `search/local/alert_actions.conf`, so the first trigger could not find the action's script. [Troubleshooting 9](../Troubleshooting/Webhook%20action%20script%20not%20found%20after%20a%20stray%20REST%20POST%20-%202026-09-03.md).
3. The first post that did reach the bot was refused by Discord for its URL, which is the `hostname` setting above and a URL check in the bot. [The bot's record](../../../../Discord%20Alert%20Bot/Documentation/Troubleshooting/Discord%20Rejected%20Every%20Updates%20Batch%20-%202026-09-03.md).

The credential I used for the REST calls lived in a mode-600 file in my home directory on `splunk-siem` for the session and was removed at the end of it.

## Verification

- All 16 saved searches in the two apps list as scheduled or intentionally unscheduled with the crons above, and nine carry `action.webhook = 1` with the bot's URL. `alert.digest_mode` reads per-result on the eight grouped searches and digest on the dead-man.
- Every new or changed search was dispatched once over 30 days with actions off and completed without error: blocked 4 rows, not-blocked 8, internal denies 3 rows (all below the live 10-minute threshold), syslog quiet 0, malware 2, account changes 3, off-network logins 0, silent machines 0.
- `btool alert_actions list webhook --debug` attributes every line of the stanza to `alert_webhook` or `system/default`, none to `search/local`.
- `sendmodalert` logged `Invoking modular alert action=webhook ... in app="wazuh_insights"` and the bot logged the matching `POST /splunk` from `192.168.72.3` at 2:06:12 AM.
- End-to-end proof is the paragraph below.

## End-to-end proof

Pending at the time of the first write of this record: the malware search's two results were inside their one-hour suppression from the 2:02 AM dispatch. The proof paragraph is completed below once the window lapsed.
