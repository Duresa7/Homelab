# Discord Alert Bot

**Created:** 2026-09-02  
**Last updated:** 2026-09-25

I run a small Discord bot that turns Grafana alerts and Splunk alerts into messages in the `#bots` channel, posted by the **Anubis AS** bot user. It is the only contact point Grafana has and the only place Splunk's security searches post. On 2026-09-24 Grafana's provisioning file on `monitor-01` held 24 alert rules and one contact point, the bot. Before the bot existed, every one of the 15 rules then defined evaluated into a receiver named `empty`, so nothing was delivered. Delivery was proven on 2026-09-02 with a firing and a resolved message, and the Splunk path on 2026-09-03 with a real saved search; the ids are in the records.

**Owner:** Homelab infrastructure monitoring

## How it works

1. A Grafana rule fires. The root notification policy routes it to the contact point `discord-bot`, a Grafana webhook receiver. Alerts labelled `class: updates` take a child route that groups them by rule name, waits 5 minutes, flushes every 30, and repeats once a year, so an update condition is announced once and resolved once.
2. Grafana posts the alert payload to `http://alert-bot:8080/grafana` over the monitoring Compose network, with a shared secret as a bearer token.
3. A Splunk saved search fires its `webhook` alert action, which posts one result row to `http://192.168.73.2:8080/splunk`. Splunk cannot send a header, so the bot accepts that endpoint from `192.168.72.3` only and answers 403 to anything else, and a UniFi policy admits only that host to the port.
4. The bot builds one embed per alert, or one condensed embed when four or more alerts share a name and status, and posts it as the bot user. Colour and title prefix follow the alert's class: infrastructure alerts are coloured by severity, security alerts are purple and titled `SECURITY`, update alerts are blue and titled `UPDATES`, and anything resolved is green.
5. `GET /health` answers 200 only while the Discord session is ready. Prometheus probes it through blackbox, so a dead bot trips the rule "Internal service is unreachable" rather than silently swallowing every alert.

## Layout

| Item | Location |
| --- | --- |
| Bot source | [Source/alert_bot.py](Source/alert_bot.py), [Source/Dockerfile](Source/Dockerfile), [Source/requirements.txt](Source/requirements.txt) |
| Deployed copy | `/home/dkadi/monitoring/alert-bot/` on `monitor-01`, built by the monitoring Compose project as `forgejo.alphasecunited.com/homelab-images/alert-bot:stable`; the running container was created on 2026-09-16 |
| Compose service | `alert-bot` in [Prometheus Configuration/docker-compose.yml](../Prometheus/Configuration/docker-compose.yml), port 8080 published on the host, `SPLUNK_SOURCE_IP=192.168.72.3` |
| Grafana contact point and policy | [contact-points.yaml](../Prometheus/Configuration/grafana/provisioning/alerting/contact-points.yaml) |
| Splunk senders | the nine searches carrying `action.webhook` in [unifi_insights](../Splunk/Enterprise/Configuration/unifi_insights/default/savedsearches.conf) and [wazuh_insights](../Splunk/Enterprise/Configuration/wazuh_insights/default/savedsearches.conf) |
| Health probe | `http://alert-bot:8080/health` in the `blackbox` job of [prometheus.yml](../Prometheus/Configuration/prometheus-config/prometheus.yml) |
| Secrets | Untracked mode-0600 `.env` beside the Compose file, holding `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID` and `ALERT_BOT_SECRET`. Template at [.env.example](../Prometheus/Configuration/.env.example). Both secret values live in the password manager. |

The bot runs as an unprivileged user inside `python:3.13-slim` with `discord.py` 2.x and `aiohttp` 3.x. It needs no privileged Discord intents: posting requires only **Send Messages** and **Embed Links** in the channel.

## Limits the bot enforces

Discord rejects a whole message when any embed field passes 1024 characters, the embed passes 6000, or a URL's host has no dot. I hit each of those on 2026-09-03, so the bot now drops a silence link that will not fit, trims a description until the embed fits, and only attaches a URL it can validate. A message with a missing link still arrives; a rejected message never does.

## Operations

To change what a message looks like, edit `Source/alert_bot.py`, copy it to the deployed path, and run `docker compose up -d --build alert-bot` from `/home/dkadi/monitoring`. Then publish the rebuilt image to Forgejo with Dockhand's push control, so the registry copy matches what runs. To rotate the shared secret, change it in the password manager and in `.env`, then recreate both `alert-bot` and `grafana`, because Grafana reads the value into its provisioning at start. To rotate the bot token, reset it in the Discord developer portal, update the password manager and `.env`, and recreate `alert-bot` alone. If `splunk-siem` ever changes address, change `SPLUNK_SOURCE_IP` in the Compose file and the UniFi policy `Allow splunk-siem to alert bot` together.

The bot logs one line per posted message with the Discord message id, one warning per rejected request, and a full traceback when Discord refuses an embed. `docker logs alert-bot` is the first place to look when a message did not arrive. Grafana retries a failed webhook at every `group_interval`, so a bot fault shows up there as the same batch failing on a schedule.

## Records

- [Deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-02.md)
- [Class styling, condensed embeds and the Splunk endpoint](Documentation/Change%20Records/Class%20Styling,%20Condensed%20Embeds%20and%20Splunk%20Endpoint%20-%202026-09-02.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Grafana alert rules](../Prometheus/Documentation/Change%20Records/Grafana%20Alert%20Rules%20-%202026-09-01.md), [the three added the next day](../Prometheus/Documentation/Change%20Records/Guest%20CPU%20and%20Load%20Alert%20Rules%20-%202026-09-02.md), and [the nine for certificates, drives and updates](../Prometheus/Documentation/Change%20Records/Certificate,%20Drive%20Health%20and%20Update%20Alert%20Rules%20-%202026-09-02.md)
- [Splunk delivery](../Splunk/Enterprise/Documentation/Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md)
- [Prometheus platform](../Prometheus/README.md)
