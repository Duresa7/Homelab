# Class Styling, Condensed Embeds and Splunk Endpoint

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Implemented:** 2026-09-02, with corrections on 2026-09-03  
**Status:** Complete  
**Affected systems:** the `alert-bot` container in the monitoring Compose project on `monitor-01`, its UniFi reachability from `splunk-siem`

## Change

The bot posted one embed per Grafana alert, coloured by severity, and accepted nothing else. Three things changed so it can carry the second wave of alerts without becoming the noise it was meant to replace.

**Class styling.** Every Grafana rule now carries a `class` label and the bot reads it. Infrastructure alerts keep the severity colours. Security alerts are purple, `0x7048E8`, and titled `SECURITY …`. Update alerts are blue, `0x1C7ED6`, and titled `UPDATES …`. A resolved alert of any class is green. The point is that the channel is one channel, by choice, so the class has to be visible at a glance.

**Condensed embeds.** When one webhook carries four or more alerts with the same name and status, the bot posts one embed listing them by summary line, with the count in the title, rather than four or more separate embeds. Below four it still posts one per alert, because a list of two is worse than two messages. This is what turns "sixteen hosts have security updates" into one message.

**A Splunk endpoint.** `POST /splunk` accepts the payload Splunk's `webhook` alert action sends: `search_name`, `sid`, `app`, `results_link` and a `result` row. The saved searches are named `<Source> - <what happened>`, and the bot splits the name on the first ` - ` so the source goes in the footer and the rest becomes the title. It shows a fixed set of result fields when present: source and destination addresses and ports, rule and signature, action, count, the Wazuh agent, rule id, level and description, a watched file path, the machine and its last-seen time for the silent-agent search, and the user for a login. Splunk's action cannot send a header, so the endpoint is guarded by source address instead: any request not from `192.168.72.3` gets a 403. That is a fixed address on Security-A behind a UniFi policy that admits only that host to port 8080 on `monitor-01`, so the guard is the address plus the policy, not the address alone. Docker preserves the client address on a published port, which I checked before relying on it. `/grafana` still requires its bearer secret.

Port 8080 is now published on the host for that reason; before this it existed only on the Compose network. `SPLUNK_SOURCE_IP` is an environment variable in the Compose file with that one address as its value.

## Deployment

I copied `alert_bot.py` to `/home/dkadi/monitoring/alert-bot/` and rebuilt with `docker compose up -d --build alert-bot`, and replaced the Compose file so the port and the variable took effect. The bot reported healthy and its Discord session ready after each rebuild.

I proved the endpoint from three directions on 2026-09-02: a test payload sent from `splunk-siem` with `curl` was posted to Discord at 7:52 PM as `SECURITY Splunk delivery test`, message `1544857589014069351`, the same payload from `ubuntu-dev` at `192.168.40.179` got a 403, and from `monitor-01` itself over the loopback address it got a 403. The UniFi policy `Allow splunk-siem to alert bot` was created for the path; it is in [Monitoring Ports for What's Up Docker and the Alert Bot](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Monitoring%20Ports%20for%20What's%20Up%20Docker%20and%20the%20Alert%20Bot%20-%202026-09-02.md).

The first real Updates batch then failed for three and a half hours, because a silence link built from fifteen labels passed Discord's field limit, and the first real Splunk post failed because Splunk's results link used a bare hostname. Both are in [Discord Rejected Every Updates Batch](../Troubleshooting/Discord%20Rejected%20Every%20Updates%20Batch%20-%202026-09-03.md). The bot now measures every field, keeps the embed under 6000 characters, and validates URLs. The final build went live at 2:07 AM on 2026-09-03 with `alert_bot.py` at SHA-256 `aeb1bf62006191d29659170d044e909062551a432548291a28ecbeb808b8ed5c`, matching the repository.

## Verification

- `curl -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health` on `monitor-01` returns 200 and the log shows `discord ready as Anubis AS#9583`.
- The 403 path is proven from two addresses and the accept path from `splunk-siem`, above.
- The condensed embed works on real data: `UPDATES WARNING: Security updates are waiting (16)` at 8:27 PM on 2026-09-02, message `1544866468976398357`, is one message for sixteen hosts.
- `docker exec alert-bot sha256sum /app/alert_bot.py` matches the repository file.
- Delivery of the condensed Updates messages and of a real Splunk saved search are recorded in the [Prometheus](../../../Prometheus/Documentation/Change%20Records/Certificate,%20Drive%20Health%20and%20Update%20Alert%20Rules%20-%202026-09-02.md) and [Splunk](../../../Splunk/Enterprise/Documentation/Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md) records.

No snapshot or backup. The image rebuilds from the repository in under a minute.

## Remaining Work

The bot still only posts. A `/status` command is a separate project, as it was before.
