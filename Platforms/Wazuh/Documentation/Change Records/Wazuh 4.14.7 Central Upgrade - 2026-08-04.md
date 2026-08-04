# Wazuh 4.14.7 Central Upgrade

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Change date:** 2026-08-04  
**Target:** `security-01`, VM 200 on `grey-server`  
**Plan:** [Wazuh 4.14.7 Upgrade](../Change%20Plans/Wazuh%204.14.7%20Upgrade.md)  
**Status:** Complete

## What I did and why

I took the all-in-one Wazuh stack from 4.14.6-1 to 4.14.7-1: indexer, then manager and the Filebeat integration, then dashboard. The manager caps every agent version in the fleet, so `edge-01` on 4.14.5-1 and `docker-main` on 4.14.0-1 could not move until this did.

I ran it without a snapshot or backup, deliberately. That left the component ordering and a stop-and-assess gate after the indexer as the only protection, so I checked each component before starting the next.

## Before and after

| | Before | After |
|---|---|---|
| `wazuh-indexer` | 4.14.6-1 | 4.14.7-1 |
| `wazuh-manager` | 4.14.6-1 | 4.14.7-1 |
| `wazuh-dashboard` | 4.14.6-1 | 4.14.7-1 |
| `filebeat` | 7.10.2-2 | 7.10.2-2, unchanged |
| Services active | 4 of 4 | 4 of 4 |
| Agents | 15 active, 0 disconnected | 15 active, 0 disconnected |
| Cluster | green, 400 primaries, 0 unassigned | green, 400 primaries, 0 unassigned |
| Dashboard, API | HTTP 302, 401 | HTTP 302, 401 |

`wazuh-control info` reports `WAZUH_VERSION="v4.14.7"`. The manager log holds zero `ERROR` or `CRITICAL` lines since the upgrade, and the vulnerability scanner module started normally.

## Sequence

I copied `/etc/wazuh-indexer`, `/var/ossec/etc/ossec.conf`, and `/etc/filebeat/filebeat.yml` to `/root/pre-4.14.7/` first. Config files only, not a guest backup.

Filebeat and the dashboard came down, the indexer security configuration was written out to `/etc/wazuh-indexer/opensearch-security`, shard allocation dropped to `primaries`, and a flush committed 399 of 399 shards with zero failures before the manager stopped.

The indexer package went on with `--force-confold`, came back **green in ten seconds** with the same 400 primary shards and zero unassigned, and shard allocation returned to its default. Zero plugins reported `outdated` across 17. That was the stop-and-assess gate and it passed cleanly, so I continued rather than leaving the manager and dashboard down.

The manager package followed, then the Wazuh Filebeat module 0.5 and the v4.14.7 alerts template. `filebeat test output` passed every check to the indexer over TLSv1.2. The dashboard package went last and returned HTTP 302 within ten seconds of starting.

## Two things worth knowing next time

**Authenticate to the indexer with the admin certificate, not a password.** `/etc/wazuh-indexer/certs/admin.pem` and `admin-key.pem` are already there, so `curl --cert ... --key ...` does every API check with no credential on a command line and nothing to redact afterwards. The plan originally called for an interactive password prompt, which cannot run unattended and puts a secret one shell-history line away.

**Keeping the existing config files was the right call, and the vendor's advice would have broken the dashboard.** Wazuh's procedure says to take the packaged configuration file and reapply local differences. The packaged `opensearch_dashboards.yml` points `server.ssl.key` and `server.ssl.certificate` at `dashboard-key.pem` and `dashboard.pem`. This installation's certificates are named `wazuh-dashboard-key.pem` and `wazuh-dashboard.pem`, and those are the only ones present, so adopting the packaged file wholesale would have left the dashboard unable to start.

Two config differences are still worth adopting deliberately, and I have not:

- `/etc/wazuh-indexer/jvm.options.dpkg-dist` changes a JVM flag guard from `20:` to `20-:`, so `--add-modules=jdk.incubator.vector` applies to Java 20 **and later** rather than to Java 20 alone. Its heap values are `1g`, which is the same as the `1024m` already set, so nothing about memory changes.
- The packaged dashboard configuration adds `opensearch_security.cookie.ttl`, `session.ttl`, and `session.keepalive` at 900000 ms, giving sessions a fifteen-minute expiry. The live file keeps `opensearch_security.cookie.secure: true`, which the packaged file drops, so any adoption has to keep that line.

## Note on the tooling

Ansible on `ansible-01` drove the first half. Its five-minute load average reached 17.71 under repeated fleet-wide runs, which made SSH handshakes time out mid-upgrade. I finished the dashboard through the Proxmox guest agent with `qm guest exec 200` from `grey-server`, which needs neither SSH nor a password. The container was never faulty; it was saturated by my own runs.

## What remains

The twelve agent holds are still in place and can now be released, one host at a time, because the manager is newer than every agent. `edge-01` on 4.14.5-1 and `docker-main` on 4.14.0-1 are the two worth moving. `docker-main` also needs the package source it has never had.
