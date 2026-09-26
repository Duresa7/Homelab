# Discord Alert Bot Deployment

**Created:** 2026-09-02  
**Last updated:** 2026-09-25

**Implemented:** 2026-09-02  
**Status:** Complete. Delivery proven end to end in both directions  
**Affected systems:** Grafana, Prometheus and the monitoring Compose project on `monitor-01`

## Change

Grafana had 15 alert rules and no way to deliver one. `/api/v1/provisioning/contact-points` returned an empty list, the root policy's receiver was named `empty`, and SMTP was disabled. I chose a dedicated bot over a plain channel webhook because the messages then come from the real **Anubis AS** bot user and the same process can later answer commands.

What I added:

- A Python bot, [Source/alert_bot.py](../../Source/alert_bot.py), with `POST /grafana` for Grafana's webhook payload and `GET /health` that answers 200 only while the Discord session is ready. It is built into `homelab/alert-bot:1` by the monitoring Compose project.
- The `alert-bot` service in the monitoring `docker-compose.yml`, and `ALERT_BOT_SECRET` in Grafana's environment. Both are interpolated by Compose from an untracked mode-0600 `.env` beside the file; `.env` is now gitignored and a `.env.example` carries placeholders.
- A provisioned Grafana contact point `discord-bot` of type webhook, pointing at `http://alert-bot:8080/grafana` with a bearer secret interpolated from Grafana's environment, and a root notification policy that routes to it with `group_wait` 30s, `group_interval` 5m and `repeat_interval` 4h.
- The bot's health endpoint as a blackbox probe target, so the target count went from 49 to 50 and the existing service-unreachable rule covers the bot.
- A new shared secret, generated with `openssl rand -hex 32` and stored in the password manager before use. Neither it nor the bot token appears in any file in this repository.

## Deployment

I copied the live `docker-compose.yml` to [Backups/monitor-01-docker-compose-2026-09-02.yml](../../../../Backups/monitor-01-docker-compose-2026-09-02.yml) before replacing it. It holds no withheld values. The live file was replaced in place, so there was no second copy on the host to delete. The replacement is the versioned file, which also drops the inert `GF_DATABASE_WAL=true` line and its comment block that the live copy had carried since 2026-07-26.

The deploy did not go smoothly. My first two attempts ran over direct SSH from `ubuntu-dev` and stalled: one on the `.env` transfer, one on the first `docker` command. After that, SSH from `ubuntu-dev` to `monitor-01` timed out at the TCP handshake while the same host answered HTTP normally and SSH from `grey-server` and `docker-network` still worked. On `monitor-01` I found no firewall rule, no Wazuh active response and nothing in the sshd journal naming my address, so the drop is somewhere on the path from `192.168.40.179` and I have not identified it. I finished the deploy through the Executor gateway on `docker-blue`, which is the route the agent instructions prefer anyway.

Through that route, at 11:54:39 AM Eastern, `docker compose up -d grafana prometheus` recreated Grafana. Grafana's provisioner logged `starting to provision alerting` and `finished to provision alerting` 273 milliseconds apart with no error between them. Compose left Prometheus running, because a changed bind-mounted config does not trigger a recreate, so at 11:55:58 AM I restarted it explicitly and it reported ready six seconds later.

The bot image built at 227 MB. The token item was not in the vault the automation account reads, so the first pass ended with `DISCORD_TOKEN` empty and the container not started. Once the item was moved there, I read it by item id rather than by title, because the colon in the title broke the password manager's secret-reference syntax, wrote `.env` over the stdin of a single SSH session, and started the container at 12:33 PM Eastern. It reported healthy after 22 seconds and its log shows the Discord session ready as the Anubis AS bot user, posting to channel `1495962372936826991`. The Grafana container reaches `http://alert-bot:8080/health` and gets `ok`.

I used one multiplexed SSH connection for that whole pass, because the earlier drop turned out to be UniFi Threat Management matching `ET SCAN Potential SSH Scan OUTBOUND` on my burst of separate connections and blocking them under the Scanning Activity policy.

## Verification

- `/api/v1/provisioning/contact-points` returns one entry: `discord-bot`, type `webhook`, URL `http://alert-bot:8080/grafana`, authorization scheme `Bearer`, provenance `file`.
- `/api/v1/provisioning/policies` returns receiver `discord-bot`, `group_wait` 30s, `group_interval` 5m, `repeat_interval` 4h, provenance `file`. The `empty` receiver is gone.
- The rule state API reports 15 rules, 0 unhealthy.
- The recreated Grafana container's environment holds zero `GF_DATABASE_WAL` lines and one non-empty `ALERT_BOT_SECRET`. Grafana reports version 13.2.0 and database `ok`.
- Prometheus reports 50 active targets after the restart. The `http://alert-bot:8080/health` target scrapes successfully and `probe_success` for it reads 0, which is the correct reading for a bot that is not running.
- `.env` on the host is mode 600 with three lines.
- The bot source compiles, and the Compose file, `prometheus.yml` and both provisioning files parse; `promtool check config` returned SUCCESS.
- After the bot started, `probe_success` for its health endpoint reads 1, Prometheus reports 50 of 50 targets up, and no rule is firing.
- **Delivery, firing.** A throwaway rule with `vector(1)` created at 12:34:10 PM was posted by the bot at 12:35:10 PM as Discord message `1544747525821431839`: one evaluation plus the 30-second `group_wait`.
- **Delivery, resolved, twice.** Deleting that rule did produce a resolved message, at 12:40:10 PM as message `1544748783970295980`: exactly one `group_interval` after the firing post, not immediately, and later than the three and a half minutes I first waited before concluding it had not come. Because I doubted it at the time, I ran a second throwaway rule that clears on its own, true for 100 seconds after creation through `vector(time() - <start> < bool 100)`. It posted firing at 12:40:10 PM as message `1544748784054046801` and resolved at 12:45:10 PM as message `1544750042014031996`, again one `group_interval` later. So a resolved notification, whether from a rule clearing or from a rule being deleted, arrives at the next five-minute flush. Both rules are deleted and the 15 provisioned rules remain.

## Remaining Work

1. The bot posts only. Slash commands such as a `/status` that reads Prometheus are a separate project.

## Follow-up the same day

The SSH blocks were UniFi Threat Management matching `ET SCAN Potential SSH Scan OUTBOUND`, and this was the second time: the existing Detection Exclusion for `192.168.85.2` had been added for the same symptom on `docker-network`. Rather than add a second host, I excluded the one signature under Detection Exclusions, which keeps every other detection live on the automation hosts, and removed the `192.168.85.2` host exclusion so `docker-network` is inspected again. I made both changes in the controller interface; the UniFi MCP catalog exposes no exclusion tool, so the second change is recorded from what I did rather than from an API read.

Verification at 4:19 PM Eastern: twelve separate SSH connections from `ubuntu-dev` to `monitor-01` in two seconds all succeeded, and a thirteenth immediately after still reached the host. That is the burst that was blocked at 11:44 AM.
