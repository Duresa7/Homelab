# Wazuh TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-29

## Agent Enrollment

I have no pending enrollments. I freshly installed and enrolled `app-01` and `edge-01` on 2026-07-13 as active IDs `004` and `005`; they are the only intended Wazuh endpoints. Their old `edge-01` and incorrect `wp-01` registrations remain retired.

## Decide how edge-01 gets agent updates

`edge-01` has no Wazuh apt repository, so its agent is stuck at 4.14.5-1 while `app-01` tracks the repository and moved to 4.14.6-1 on 2026-07-29. Nothing is broken, since a 4.14.5 agent against a 4.14.6 manager is supported, but no scheduled run will ever close that gap. I found this on 2026-07-29 while reviewing the fleet maintenance records.

Two ways to settle it. Add the repository to `edge-01` so fleet package maintenance carries the agent forward, which also means a third-party source and its signing key on the edge ingress host. Or leave it off and treat agent upgrades there as a deliberate act, which needs a reminder because nothing will surface the drift on its own.

Either way the version claims in the [configuration reference](../Configuration/README.md) need a reread whenever the manager moves.
