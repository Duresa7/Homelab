# Webhook action script not found after a stray REST POST

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Observed:** 2026-09-03, 1:54 AM to 2:03 AM Eastern  
**Status:** Resolved

## Symptom

The first saved search to trigger the new `webhook` alert action, a manual dispatch of `Wazuh - Malware or high severity` with `trigger_actions=1` at 2:02 AM, produced two result rows and no HTTP request to the alert bot. `splunkd.log` had, for each row:

```text
WARN  sendmodalert - action=webhook - Unable to find alert action script for action="webhook" in app="search"
ERROR sendmodalert - Error in 'sendalert' command: Alert action script for action "webhook" not found.
```

The script exists at `/opt/splunk/etc/apps/alert_webhook/bin/webhook.py`, mode `r-xr-xr-x`, owned by `splunk`. The message says Splunk was looking in the `search` app instead.

## Cause

Eight minutes earlier, at 1:54 AM, I had checked that the webhook action was present with:

```sh
curl -sk -u "$CRED" https://127.0.0.1:8089/services/alerts/alert_actions/webhook -d output_mode=json
```

`-d` makes curl send a POST, and a POST to an alert action's endpoint is an edit. Splunk wrote the edit to the calling context, which for `/services/` is the `search` app, and created `/opt/splunk/etc/apps/search/local/alert_actions.conf` containing exactly `[webhook]` and nothing else. `btool alert_actions list webhook --debug` then showed that file as the owner of the stanza header. Splunk resolves the alert action's script relative to the app that owns its stanza, so it looked for `search/bin/webhook.py`, which does not exist.

The listing I got back looked right, which is why I did not notice: the response to a POST is the resulting object, and the object was unchanged apart from where its header now lived.

## Fix

At 2:03 AM I printed the file to confirm it held only the stanza header, removed it, and reloaded alert actions:

```sh
rm /opt/splunk/etc/apps/search/local/alert_actions.conf
curl -sk -u "$CRED" -X POST https://127.0.0.1:8089/services/alerts/alert_actions/_reload
```

`btool` no longer lists any `search/local` line for the stanza, and the REST entry for `webhook` reports its app as `alert_webhook` again.

## Verification

The next dispatch with actions enabled, `Wazuh - Account or group changed` at 2:06 AM, ran `webhook.py` in `app="wazuh_insights"` and the bot logged a `POST /splunk` from `192.168.72.3`. That request then failed on a Discord validation the bot did not check, which is [the bot's own record](../../../../Discord%20Alert%20Bot/Documentation/Troubleshooting/Discord%20Rejected%20Every%20Updates%20Batch%20-%202026-09-03.md); the Splunk side of the path was proven by that request.

## What I would do differently

Read with `-G`, or put `output_mode=json` in the query string. Every other read in this session did, and the one that did not changed the server.
