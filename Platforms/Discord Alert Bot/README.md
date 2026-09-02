# Discord Alert Bot

**Created:** 2026-09-02  
**Last updated:** 2026-09-02

I run a small Discord bot that turns Grafana alerts into messages in the `#bots` channel, posted by the **Anubis AS** bot user. It is the only contact point Grafana has. Before it existed, every one of the 15 alert rules on `monitor-01` evaluated into a receiver named `empty`, so nothing was ever delivered. Delivery was proven on 2026-09-02 with a firing and a resolved message; the ids are in the deployment record.

**Owner:** Homelab infrastructure monitoring

## How it works

1. A Grafana rule fires. The root notification policy routes it to the contact point `discord-bot`, a Grafana webhook receiver.
2. Grafana posts the alert payload to `http://alert-bot:8080/grafana` over the monitoring Compose network, with a shared secret as a bearer token. Nothing is published on the LAN.
3. The bot checks the bearer, builds one embed per alert, and posts it to channel `1495962372936826991` as the bot user. A resolved alert produces a green message the same way.
4. `GET /health` on the bot answers 200 only while its Discord session is ready. Prometheus probes it through blackbox, so a dead bot trips the rule "Internal service is unreachable" rather than silently swallowing every alert.

## Layout

| Item | Location |
| --- | --- |
| Bot source | [Source/alert_bot.py](Source/alert_bot.py), [Source/Dockerfile](Source/Dockerfile), [Source/requirements.txt](Source/requirements.txt) |
| Deployed copy | `/home/dkadi/monitoring/alert-bot/` on `monitor-01`, built by the monitoring Compose project as `homelab/alert-bot:1` |
| Compose service | `alert-bot` in [Prometheus Configuration/docker-compose.yml](../Prometheus/Configuration/docker-compose.yml) |
| Grafana contact point and policy | [contact-points.yaml](../Prometheus/Configuration/grafana/provisioning/alerting/contact-points.yaml) |
| Health probe | `http://alert-bot:8080/health` in the `blackbox` job of [prometheus.yml](../Prometheus/Configuration/prometheus-config/prometheus.yml) |
| Secrets | Untracked mode-0600 `.env` beside the Compose file, holding `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID` and `ALERT_BOT_SECRET`. Template at [.env.example](../Prometheus/Configuration/.env.example). Both secret values live in the password manager. |

The bot runs as an unprivileged user inside `python:3.13-slim` with `discord.py` 2.x and `aiohttp` 3.x. It needs no privileged Discord intents: posting requires only **Send Messages** and **Embed Links** in the channel.

## Operations

To change what a message looks like, edit `Source/alert_bot.py`, copy it to the deployed path, and run `docker compose up -d --build alert-bot` from `/home/dkadi/monitoring`. To rotate the shared secret, change it in the password manager and in `.env`, then recreate both `alert-bot` and `grafana`, because Grafana reads the value into its provisioning at start. To rotate the bot token, reset it in the Discord developer portal, update the password manager and `.env`, and recreate `alert-bot` alone.

The bot logs one line per posted message with the Discord message id, and one warning per rejected request. `docker logs alert-bot` is the first place to look when a message did not arrive.

## Records

- [Deployment record](Documentation/Change%20Records/Discord%20Alert%20Bot%20Deployment%20-%202026-09-02.md)
- [Grafana alert rules](../Prometheus/Documentation/Change%20Records/Grafana%20Alert%20Rules%20-%202026-09-01.md) and [the three added the next day](../Prometheus/Documentation/Change%20Records/Guest%20CPU%20and%20Load%20Alert%20Rules%20-%202026-09-02.md)
- [Prometheus platform](../Prometheus/README.md)
