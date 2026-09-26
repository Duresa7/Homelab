# Wazuh TODO

**Created:** 2026-07-13  
**Last updated:** 2026-09-25

## Manager process health

- [x] 2026-09-11: Correct the hash refresh to restart through systemd, so manager processes survive the refresh service exiting. I ran the actual refresh and verified process ownership and both agent listeners afterward. [Incident record](../../../Security/Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md).
- [ ] Add a manager API or process/listener health check. The manager unit remained active while its daemons were stopped from September 6 to September 11; service-state monitoring alone missed the outage.

## Coverage and host hygiene

- [ ] Decide whether `splunk-siem` gets an agent. On 2026-09-24 it was the only running Linux guest without one (Rocky 10.2); `kali-pen` is stopped and not enrolled either.
- [ ] Check `security-01` for `/var/ossec/etc/client.keys.bak.security-monitoring-cleanup-20260713`, the pre-reset copy of the agent registry from the 2026-07-13 removal. It is not a valid rollback point, and a copy taken before an edit does not stay on the host, so remove it if it is still there.

## Fleet deployment status

I completed the [2026-08-03 fleet deployment](Change%20Records/Agent%20Fleet%20Deployment%20-%202026-08-03.md) with 14 active remote agents, zero disconnected or pending agents, and all five Galaxy nodes active in `proxmox`. I described IDs `006` through `017` as held because the [deployment play](../Source/agent-deployment/playbooks/deploy.yml) installs exact package `4.14.6-1` and separately applies `dpkg_selections: hold` to its twelve targets. Existing IDs `004` and `005` are not in that inventory, so the empty `apt-mark showhold` results from `app-01` and `edge-01` on 2026-08-04 do not contradict the record. The final seven-host run and later Green-only run each changed zero hosts.

## Host deviation found on 2026-08-15

This turned up while I turned root SSH off on `security-01` and doesn't affect Wazuh itself. See [Root SSH Disabled on ansible-01 and security-01](../../../Operations/Maintenance/Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md).

- [x] Fixed 2026-08-30: `timedatectl` now reports `Time zone: America/New_York (EDT, -0400)` with the system clock synchronized. This mattered more than a baseline tick once alerts started reaching Splunk, because the manager's timestamps are what the dashboard sorts on.

## Detection and forwarding, 2026-08-30

Four changes on 2026-08-29 into 2026-08-30 took this platform from an agent fleet that reported into its own dashboard to one whose alerts are searchable in Splunk with malware detection on top: [Alert Forwarding to Splunk](Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md), [File Integrity Monitoring Widening](Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md), [Malware Detection](Change%20Records/Malware%20Detection%20-%202026-08-29.md) and, on the Splunk side, [Wazuh Insights App](../../Splunk/Enterprise/Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).

- [ ] Phase two of file-integrity monitoring. Only `workstation` and `edge` have real watches; the other 13 agents, including `docker-main` since 2026-09-06, still carry `/etc/ssh` and `/etc/cron.d` from the `default` group.
- [x] 2026-09-03: Alerting. Splunk posts four Wazuh searches to Discord: malware or level 12 and above, account and group changes, logins from outside private networks, and a machine silent for 24 hours. Wazuh itself still notifies nobody, by design; Splunk is the one emitter. See [Discord Delivery for UniFi and Wazuh Alerts](../../Splunk/Enterprise/Documentation/Change%20Records/Discord%20Delivery%20for%20UniFi%20and%20Wazuh%20Alerts%20-%202026-09-03.md).
- [ ] No automatic response, and that is a decision as of 2026-09-02 rather than a gap: I considered active response while planning the alerts and chose to keep Wazuh as detection only. Nothing quarantines or deletes a file that matched a known-bad hash. Revisit only if a detection ever arrives that a human could not have acted on in time.
- [x] 2026-08-31: `nut-driver@ups01.service` on `red-server` failed every 25 seconds, about 3,450 times a day, and was 575 of 914 fleet alerts, 62.9 per cent, on the day the feed opened. I commented out the `[ups01]` stanza while UPS-01's data cable is disconnected, and no `nut-driver@*` instance remains on `red-server`. See [ups01 NUT Driver Restart Loop After the UPS Swap](../../PeaNUT/Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md).
- [ ] `openipmi.service` is failed on `red-server`, which also raises Wazuh alerts.
- [ ] Rootcheck still reports "Files hidden inside directory '/tmp'" on `ubuntu-dev`, 36 events. Low volume, left alone.

## Agent versions are gated on the manager, not on the sources

- [x] Decision settled 2026-08-04: add the Wazuh APT source to `edge-01` so ordinary fleet package maintenance can carry its agent forward, matching `app-01`. I accept the third-party package source and signing key on the edge ingress host.
- [x] Implemented 2026-08-04: the source and signing key are on `edge-01`, and its agent is held at `4.14.5-1`. See [edge-01 Package Source and Fleet Agent Holds](Change%20Records/edge-01%20Package%20Source%20and%20Fleet%20Agent%20Holds%20-%202026-08-04.md).
- [x] Fixed 2026-08-04: `app-01` carried the source with **no hold**, so the next fleet run would have upgraded it past the manager. Held.
- [x] Upgraded the central stack to 4.14.7 on 2026-08-04. Indexer, manager, Filebeat integration, and dashboard, in that order, with no snapshot by choice. 15 agents active and zero disconnected before and after; cluster green at 400 primaries both times. See [Wazuh 4.14.7 Central Upgrade](Change%20Records/4.14.7%20Central%20Upgrade%20-%202026-08-04.md).
- [ ] Release the twelve agent holds, one host at a time. The manager is now newer than every agent, so this is unblocked. Releasing a hold makes that host eligible for `4.14.7-1` on the next fleet run.
- [ ] Move `edge-01` off `4.14.5-1`. It is the last agent below the fleet's 4.14.6-1.
- [x] 2026-09-06: `docker-main` re-enrolled as agent `021`, on 4.14.6-1, held, with the source disabled, and now in the `agent-deployment` inventory. The audit that morning had found its agent was not an old version reporting in but not reporting at all: `ossec.conf`, unchanged since 2025-11-05, pointed at `192.168.40.227`, the manager's address before the Security-A migration, and the manager had never listed the host. The fleet stands at 16 active remote agents. See [docker-main Agent Re-enrollment](Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md).

Adding a source does **not** move an agent forward on its own, which is the thing I had wrong when I chose this option. The version an agent can reach is capped by the manager, and the repository only ever carries the current package for a release line. So a source plus a hold is the whole of what a target can safely have until the manager moves.

`edge-01` on `4.14.5-1` against a `4.14.7-1` manager is a supported pairing, so nothing above describes an outage. `docker-main`'s disconnected agent was the one outage here, and it closed on 2026-09-06.

The [configuration reference](../Configuration/README.md) carries the dated package observations and links the repository-wide version rule.
