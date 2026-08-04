# Wazuh TODO

**Created:** 2026-07-13  
**Last updated:** 2026-08-04

## Fleet deployment status

I completed the [2026-08-03 fleet deployment](Change%20Records/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03.md) with 14 active remote agents, zero disconnected or pending agents, and all five Galaxy nodes active in `proxmox`. I described IDs `006` through `017` as held because the [deployment play](../Source/agent-deployment/playbooks/deploy.yml) installs exact package `4.14.6-1` and separately applies `dpkg_selections: hold` to its twelve targets. Existing IDs `004` and `005` are not in that inventory, so the empty `apt-mark showhold` results from `app-01` and `edge-01` on 2026-08-04 do not contradict the record. The final seven-host run and later Green-only run each changed zero hosts.

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
