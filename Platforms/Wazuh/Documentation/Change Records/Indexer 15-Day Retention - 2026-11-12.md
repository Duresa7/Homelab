# Indexer 15-Day Retention

**Created:** 2026-11-12  
**Last updated:** 2026-11-12

**Change date:** 2026-11-12  
**Target:** `wazuh-indexer` 4.14.10 on VM 200 `security-01`

## Outcome

The Wazuh indexer now deletes alert, archive, monitoring and statistics indices 15 days after each one is created. Before this it deleted nothing: every daily alert index since 2026-02-24 was still there, and the node was 270 shards short of the limit at which it stops creating indices. The first deletions ran at 7:31 AM, and by 7:35 AM the node held 89 shards and 84.9 MB of indices, down from 731 and 612.4 MB.

## Why

The disk was never the problem. The indices held 612.4 MB in all. The shard count was:

| Check at 7:06 AM | Result |
|---|---|
| `_plugins/_ism/policies` | `{"policies":[],"total_policies":0}`, no retention of any kind |
| Oldest index | `wazuh-alerts-4.x-2026.02.24`, created 2026-02-24T19:03:58Z. Creation dates match the index names, so an age condition works on them |
| Indices | 207 `wazuh-alerts-4.x-*` daily, 36 `wazuh-monitoring-*` and 36 `wazuh-statistics-*` weekly, 28 `wazuh-states-*`, 8 system indices |
| `_cluster/health` | `green`, 730 active shards |
| `cluster.max_shards_per_node` | 1000, the default |
| A daily alert index | 3 primary shards, 0 replicas, about 2.4 MB |

At three shards a day the node would have reached 1,000 shards around February 2027. From then on the indexer refuses to create a new index, so the dashboard and the vulnerability states stop updating. Splunk would have kept receiving alerts, because the Universal Forwarder reads `alerts.json` and not the indexer.

Fifteen days keeps the Wazuh dashboard useful for the last two weeks. The longer record is the `wazuh` index in Splunk, which keeps 30 days.

## Change

The policy is [wazuh-retention-15d.json](../../Configuration/Indexer/wazuh-retention-15d.json): a `hot` state that moves to `delete` at `min_index_age` 15 days, and an `ism_template` that attaches the policy to every new `wazuh-alerts-*`, `wazuh-archives-*`, `wazuh-monitoring-*` and `wazuh-statistics-*` index. The `wazuh-states-*` indices hold current inventory and vulnerability state, not history, so they are not covered.

I applied it with the indexer's admin certificate from `/etc/wazuh-indexer/certs`, so no password was involved:

```text
PUT /_plugins/_ism/policies/wazuh-retention-15d
{"_id":"wazuh-retention-15d","_version":1,"_primary_term":1,"_seq_no":0, ...}

POST /_plugins/_ism/add/wazuh-alerts-*,wazuh-monitoring-*,wazuh-statistics-*
{"policy_id":"wazuh-retention-15d"}
{"updated_indices":279,"failures":false,"failed_indices":[]}
```

ISM creates its own system indices with one replica, and a single node cannot place a replica, so the cluster went `yellow` twice:

- Creating the policy created `.opendistro-ism-config`. I set it to `number_of_replicas: 0` and `auto_expand_replicas: false`, `{"acknowledged":true}`, and the cluster read `green` three seconds later.
- ISM's first pass at about 7:21 AM created `.opendistro-ism-managed-index-history-2026.11.12-1` and `.opendistro-job-scheduler-lock`. I set both the same way, and set the persistent cluster setting `plugins.index_state_management.history.number_of_replicas: 0` so the history indices ISM rolls over later are created without a replica. The cluster read `green`, 733 shards, 0 unassigned, at 7:23 AM.

I left the alert index template at 3 shards. At 15 days the node holds about 45 alert shards, so the shard limit is no longer close.

## Verification

| Check | Time | Result |
|---|---|---|
| `_cluster/health` | 7:16 AM | `green`, 731 active shards, 0 unassigned |
| `_plugins/_ism/explain` on the oldest and newest alert index | 7:18 AM | both carry `policy_id: wazuh-retention-15d`, `enabled: true` |
| Index counts, polled every minute | 7:17 to 7:30 AM | 207 alert, 36 monitoring and 36 statistics indices, unchanged while ISM initialized the policy and then evaluated the transition |
| The same | 7:31, 7:32, 7:33 AM | 163/26/26, then 90/15/14, then 20/4/3 as the delete actions ran |
| The same | 7:34 AM | 15 alert, 2 monitoring, 2 statistics; 89 active shards |
| Oldest and newest remaining | 7:35 AM | `wazuh-alerts-4.x-2026.10.29` to `wazuh-alerts-4.x-2026.11.12` |
| `_cluster/health` and `_cat/allocation` | 7:35 AM | `green`, 89 active shards, 0 unassigned; 84.9 MB of indices |
| `_plugins/_ism/explain/wazuh-alerts-4.x-2026.11.12` | 7:35 AM | state `hot`, "Evaluating transition conditions", so today's index is managed and waiting out its 15 days |
| Services | 7:35 AM | `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `filebeat` and `SplunkForwarder` active; dashboard HTTP 302 to the login page |
| `alerts.json` | 7:35 AM | newest alert written that minute, so the manager kept writing throughout |

## Open items

- Confirm that the `ism_template` attaches the policy to new indices on its own: `wazuh-alerts-4.x-2026.11.13` is the first one created after the policy. `_plugins/_ism/explain/wazuh-alerts-4.x-2026.11.13` should name `wazuh-retention-15d`.
- The rotated alert files under `/var/ossec/logs/alerts/YYYY/Mon` are still kept forever: 156 MB since February. The forwarder reads only the live `alerts.json`, so those files can go after 15 days too. ssh-mcp refuses writes to `/etc/cron*` and `/etc/systemd`, so the schedule goes in through Ansible from `ansible-01`.
- `/var/log/wazuh-indexer` holds 427 daily `wazuh-cluster` logs, 540 MB, and nothing deletes them.
