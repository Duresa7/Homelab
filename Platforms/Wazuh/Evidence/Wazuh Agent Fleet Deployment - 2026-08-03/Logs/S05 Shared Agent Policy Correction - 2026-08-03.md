# S05 Shared Agent Policy Correction

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:45 through 03:03 EDT  
**Target:** `security-01:/var/ossec/etc/shared`  
**Mechanism:** SSH Manager MCP through `ansible-01`; Wazuh `verify-agent-conf`

## Starting state

The default group applied this path to all six agents:

```text
/var/lib/docker/volumes/wordpress_wp_data/_data
```

Privileged path checks returned it absent on both `app-01` & `edge-01`. The `edge` group covered IDs 004 and 005 even though `/etc/cloudflared` existed only on `edge-01`.

## Validation & change

I staged the replacement fragments in `/tmp/wazuh-default-agent.conf` & `/tmp/wazuh-edge-agent.conf`. Both returned:

```text
verify-agent-conf: OK
```

I initially saved the live files as:

```text
/var/ossec/etc/shared/default/agent.conf.pre-fleet-20260803T0648Z
/var/ossec/etc/shared/edge/agent.conf.pre-fleet-20260803T0648Z
```

I installed the validated files as `wazuh:wazuh` mode `0660`, removed ID 004 from `edge`, & ran the all-group validator.

```text
Agent '004' removed from edge.
verify-agent-conf: Verifying [etc/shared/default/agent.conf]
verify-agent-conf: OK
verify-agent-conf: Verifying [etc/shared/edge/agent.conf]
verify-agent-conf: OK
central-policy-update-ok
```

At the owner's direction, I resolved and deleted only `/var/ossec/etc/shared/default/agent.conf.pre-fleet-20260803T0648Z` because it retained the unused WordPress path. I left the edge backup because it contains no WordPress configuration. Wazuh regenerated `default/merged.mg`, and the exact custom path has zero matches under `/var/ossec/etc/shared`. The package-owned generic WordPress audit signature remains unchanged.

I also checked Docker resources on `docker-main`, `app-01`, `alpha-prod-01`, `docker-network`, `docker-blue`, `media-01`, `monitor-01`, `kasm-01`, & `security-01`. None had a WordPress container, image, volume, or Compose project. `edge-01` had no Docker installation. There was no deployed WordPress workload or data left to remove.

The default group now monitors `/etc/ssh` & `/etc/cron.d` in real time on Linux. The edge group adds only `/etc/cloudflared`, & only ID 005 belongs to it. At 02:57 EDT, IDs 004 through 009 all reported active and synchronized. All six agents retained one established `1514/tcp` session and zero `ERROR` or `CRITICAL` matches in the final 120 local log lines checked.
