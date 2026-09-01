# Wazuh TODO

**Created:** 2026-07-13  
**Last updated:** 2026-09-01

## Fleet deployment status

I completed the [2026-08-03 fleet deployment](Change%20Records/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03.md) with 14 active remote agents, zero disconnected or pending agents, and all five Galaxy nodes active in `proxmox`. I described IDs `006` through `017` as held because the [deployment play](../Source/agent-deployment/playbooks/deploy.yml) installs exact package `4.14.6-1` and separately applies `dpkg_selections: hold` to its twelve targets. Existing IDs `004` and `005` are not in that inventory, so the empty `apt-mark showhold` results from `app-01` and `edge-01` on 2026-08-04 do not contradict the record. The final seven-host run and later Green-only run each changed zero hosts.

## Two host deviations found on 2026-08-15

Both turned up while I turned root SSH off on `security-01` and neither affects Wazuh itself. See [Root SSH Disabled on ansible-01 and security-01](../../../Operations/Maintenance/Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md).

- [ ] The guest answers to the hostname `wazuh-01`, but it is `security-01` in [VMs.md](../../../Operations/Inventory/Galaxy/VMs.md), in the Ansible inventory, and in the SSH Manager configuration. Every shell prompt and journal line from the host disagrees with the name every record uses. **Decided 2026-09-01: `security-01` is canonical**, because it is the Proxmox guest name and what all but a handful of records already say. `/etc/hostname` has to move to it; the name `wazuh-01` then survives only in dated records and captures, where it stays.

  Do not run `hostnamectl` as the whole job. Three things read the current name and one of them can take the stack down:

  - **The indexer's TLS identity, first, read-only.** A single-node Wazuh install usually names the node `node-1` with certificates to match, in which case the hostname is irrelevant to it. If this one took its `node.name` from the hostname instead, renaming breaks the security plugin's node check and the indexer will not start. Read `node.name`, `network.host` and `plugins.security.nodes_dn` out of `/etc/wazuh-indexer/opensearch.yml`, and the subject and SANs of the indexer certificate, before touching anything. Also read `opensearch.hosts` in `/etc/wazuh-dashboard/opensearch_dashboards.yml`.
  - **Agent 000.** The manager's own agent is registered as `wazuh-01` (`ID: 000, Name: wazuh-01 (server)`). Renaming the host does not re-register it, so decide whether agent 000 keeps the old name or gets re-registered, and expect a split in `agent.name` either way.
  - **The Splunk `host` field.** The forwarder's [inputs.conf](../Configuration/Splunk%20Forwarder/inputs.conf) sets no `host`, so it defaults to the OS hostname. After the rename, forwarded alerts arrive as `security-01` while the previous 30 days are `wazuh-01`. The `wazuh` index keeps 30 days, so it heals on its own, but check anything that keys on the manager's name first. Pinning `host = security-01` in the forwarder's `inputs.conf` ahead of the rename makes the change invisible to Splunk.

  Blocked on 2026-09-01: the SSH Manager MCP was disconnected, so none of the read-only preflight above has been run yet.
- [x] Fixed 2026-08-30: `timedatectl` now reports `Time zone: America/New_York (EDT, -0400)` with the system clock synchronized. This mattered more than a baseline tick once alerts started reaching Splunk, because the manager's timestamps are what the dashboard sorts on.

## Detection and forwarding, 2026-08-30

Four changes on 2026-08-29 into 2026-08-30 took this platform from an agent fleet that reported into its own dashboard to one whose alerts are searchable in Splunk with malware detection on top: [Alert Forwarding to Splunk](Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md), [File Integrity Monitoring Widening](Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md), [Malware Detection](Change%20Records/Malware%20Detection%20-%202026-08-29.md) and, on the Splunk side, [Wazuh Insights App](../../Splunk/Enterprise/Documentation/Change%20Records/Wazuh%20Insights%20App%20-%202026-08-29.md).

- [ ] Phase two of file-integrity monitoring. Only `workstation` and `edge` have real watches; the other 14 agents still carry `/etc/ssh` and `/etc/cron.d` from the `default` group.
- [ ] Alerting. Nothing in Wazuh or Splunk notifies me yet. The backlog entry is in the [Enterprise Security TODO](../../Splunk/Enterprise%20Security/Documentation/TODO.md).
- [ ] No automatic response. Nothing quarantines or deletes a file that matched a known-bad hash.
- [ ] `nut-driver@ups01.service` on `red-server` fails every 25 seconds, about 3,450 times a day, and was 575 of 914 fleet alerts, 62.9 per cent, on the day the feed opened. `openipmi.service` is failed on the same host. This belongs with [PeaNUT](../../PeaNUT/) rather than here.
- [ ] Rootcheck still reports "Files hidden inside directory '/tmp'" on `ubuntu-dev`, 36 events. Low volume, left alone.

## Agent versions are gated on the manager, not on the sources

- [x] Decision settled 2026-08-04: add the Wazuh APT source to `edge-01` so ordinary fleet package maintenance can carry its agent forward, matching `app-01`. I accept the third-party package source and signing key on the edge ingress host.
- [x] Implemented 2026-08-04: the source and signing key are on `edge-01`, and its agent is held at `4.14.5-1`. See [edge-01 Package Source and Fleet Agent Holds](Change%20Records/edge-01%20Package%20Source%20and%20Fleet%20Agent%20Holds%20-%202026-08-04.md).
- [x] Fixed 2026-08-04: `app-01` carried the source with **no hold**, so the next fleet run would have upgraded it past the manager. Held.
- [x] Upgraded the central stack to 4.14.7 on 2026-08-04. Indexer, manager, Filebeat integration, and dashboard, in that order, with no snapshot by choice. 15 agents active and zero disconnected before and after; cluster green at 400 primaries both times. See [Wazuh 4.14.7 Central Upgrade](Change%20Records/Wazuh%204.14.7%20Central%20Upgrade%20-%202026-08-04.md).
- [ ] Release the twelve agent holds, one host at a time. The manager is now newer than every agent, so this is unblocked. Releasing a hold makes that host eligible for `4.14.7-1` on the next fleet run.
- [ ] Move `edge-01` off `4.14.5-1` and `docker-main` off `4.14.0-1`, and give `docker-main` the package source it has never had.

Adding a source does **not** move an agent forward on its own, which is the thing I had wrong when I chose this option. The version an agent can reach is capped by the manager, and the repository only ever carries the current package for a release line. So a source plus a hold is the whole of what a target can safely have until the manager moves.

`edge-01` on `4.14.5-1` and `docker-main` on `4.14.0-1` against a `4.14.7-1` manager are supported pairings, so none of the above describes an outage.

The [configuration reference](../Configuration/README.md) carries the dated package observations and links the repository-wide version rule.
