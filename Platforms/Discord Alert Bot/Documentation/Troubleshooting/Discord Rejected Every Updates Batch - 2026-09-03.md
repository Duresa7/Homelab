# Discord Rejected Every Updates Batch

**Created:** 2026-09-03  
**Last updated:** 2026-09-03

**Observed:** 2026-09-02 10:27 PM to 2026-09-03 1:57 AM Eastern  
**Status:** Resolved 2026-09-03

## Symptom

The bot's log showed the same stack every 30 minutes, eight times, each ending in:

```text
discord.errors.HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body
```

Each was Grafana's webhook for the Updates group, delivered to `POST /grafana` from the Grafana container and answered with a 500 when `channel.send` raised. Grafana treats a 5xx as undelivered and retried at every `group_interval`, so the same batch failed eight times and nothing from the Updates class reached Discord in those three and a half hours. The infrastructure rules were unaffected, because none fired.

A second variant appeared at 2:06 AM on the new `/splunk` endpoint, once the first was fixed:

```text
400 Bad Request (error code: 50035): Invalid Form Body
In embeds.0.url: Not a well formed URL.
```

## Cause

Two limits in Discord's embed validation, neither of which the bot checked.

**An embed field value may not pass 1024 characters.** The bot adds a `Silence` field whose value is a markdown link to Grafana's silence URL. Grafana builds that URL with one matcher per label on the alert. The Updates rules are the first whose metrics carry many labels: a `wud_containers` series has fifteen, including the image name, tag, result tag, error message and watcher, and the URL-encoded link ran well past 1024 characters. The single-alert embed and the condensed embed both added the field without measuring it.

**An embed URL must be well formed, and Discord's definition needs a dot in the host.** Splunk builds the `results_link` in its webhook payload from its own server name, which was `https://splunk-siem:8000/...`. The bot passed it straight through as the embed's title link.

## Fix

In [alert_bot.py](../../Source/alert_bot.py):

- `add_silence_field` builds the link and adds the field only when the value fits in 1024 characters. A message without a silence link is still a message.
- `fit_embed` brings the embed under Discord's 6000-character total: it cuts the description once to the room the title, fields and footer leave, and if those alone pass the limit it drops the description and then the fields. Every embed passes through it. The first version of this function trimmed in a loop, and a code review the same morning found that the loop could never finish once the description was down to a single ellipsis while the fields still exceeded the limit, which would have hung the event loop and with it every endpoint on the bot. It was rewritten without the loop, checked against five constructed cases, and redeployed at 4:00 AM.
- `safe_url` accepts a URL only if it is `http` or `https` and its host contains a dot, and every embed URL goes through it.

On the Splunk side, both `unifi_insights` and `wazuh_insights` now carry a `default/alert_actions.conf` setting `hostname = https://splunk.alphasecunited.com`, which is the name the reverse proxy publishes Splunk Web on. The link in a Discord message now opens.

The bot was rebuilt on `monitor-01` at 2:01 AM with the size limits and again at 2:07 AM with the URL check. Both builds reported healthy within ten seconds and the Discord session ready. After the review fix the deployed `alert_bot.py` has SHA-256 `c299838035dfd8534fc091a252ca89e28335a3a9b3d4df0ed0f9ef9c7771ab67`, matching the repository.

## Verification

The Updates batch that had failed eight times was accepted at Grafana's next retry after the 2:01 AM rebuild: two `UPDATES INFO: Container image has an update` messages at 2:27:43 AM, ids `1544957045353226292` and `1544957047005782107`, each with six fields and no silence link. The channel's message history read through the bot's own token confirms them, and confirms that the other two Updates groups had already landed the previous evening before the image group first fired: the condensed 16-host security-updates message at 8:27 PM and the OS-updates message at 8:57 PM. The failure was confined to the one group whose metric carries fifteen labels. The Splunk path was proven with a real saved search once its suppression window lapsed; both results are in the [Splunk delivery record](../../../Splunk/Enterprise/Documentation/Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md).

## What I would do differently

Test the first rule of a new class with the widest-labelled metric it will ever read, not the narrowest. The class styling had been proven with a `vector(1)` rule carrying two labels.
