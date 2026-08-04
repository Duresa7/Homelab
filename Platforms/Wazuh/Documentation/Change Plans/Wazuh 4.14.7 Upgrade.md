# Wazuh 4.14.7 Upgrade

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

**Target:** Upgrade the all-in-one Wazuh stack on `security-01` from `4.14.6-1` to `4.14.7-1`  
**Execution status:** Preflight complete 2026-08-04; executing  
**Execution owner:** David Kadi

This is a change plan for a future maintenance window I will run. None of its commands ran while I wrote it, and writing this plan changed no live system.

## Component order

The required order is:

1. Prepare the upgrade and confirm the preflight facts still hold.
2. Upgrade `wazuh-indexer` and complete every indexer post-upgrade action.
3. Stop and assess the indexer result before continuing.
4. Upgrade `wazuh-manager`, then the Wazuh Filebeat module, template, package, and pipelines.
5. Upgrade `wazuh-dashboard`.
6. Verify all central components at the same patch level before releasing any agent hold.

This order comes from Wazuh's [central-component upgrade procedure](https://documentation.wazuh.com/current/upgrade-guide/upgrading-central-components.html). For an all-in-one installation, it stops Filebeat and the dashboard, completes the indexer and its post-upgrade actions, upgrades the manager and Filebeat, upgrades the dashboard, and names agent upgrades only after the central work. Wazuh's [compatibility rule](https://documentation.wazuh.com/current/upgrade-guide/index.html) requires identical versions, including patch level, across the central components and requires the manager to be at least as new as every agent.

Wazuh does not state a one-sentence causal rationale for the order. Its [architecture description](https://documentation.wazuh.com/current/getting-started/architecture.html) says the manager analyzes agent data, Filebeat sends the result to the indexer, and the dashboard queries the indexer and manager API. Treating that data flow as the reason behind the documented order is an inference. The order itself is not inferred.

<a id="prerequisites"></a>

## Step 1 - Prerequisites

### Step 1.1 - There is no rollback, and that is accepted

| Requirement | Answer |
|---|---|
| Restorable source for VM 200 | None |
| Wazuh index snapshot | None |

I decided on 2026-08-04 not to take a backup or a snapshot for this. If the upgrade fails badly, Wazuh gets rebuilt and the agent history is lost. Nineteen guests run on this cluster and none of them has a restore point, so this is the standing condition rather than a gap specific to this change.

Wazuh's own procedure recommends an index snapshot before upgrading. Taking one needs a registered snapshot repository, which does not exist here, so this plan proceeds without it.

That makes the ordering below the only real protection: one component at a time, verified before the next, with a hard stop after the indexer.

### Step 1.2 - Resolve every execution-blocking open question

Eight of the nine [open questions](#open-questions) were resolved by preflight measurement on 2026-08-04. The ninth, a rollback, does not exist and is accepted. Question 9 applies only if a plugin list reports `outdated`.

Every answer above came from measuring the host or from plain apt behaviour. None rests on a guessed flag, plugin name, credential workflow, or configuration value.

### Step 1.3 - Preserve the agent version gate

Keep all twelve ticketed agent holds in place through the complete central-component upgrade. The ticketed starting versions are ten agents on `4.14.6-1`, `edge-01` on `4.14.5-1`, and `docker-main` on `4.14.0-1`. Wazuh guarantees compatibility when the manager is the same version or newer than an agent, so all three older versions are compatible with manager `4.14.7`.

Do not release a hold while manager `4.14.6-1` is installed. The repository offers agent `4.14.7-1`, and releasing a hold early would recreate the agent-newer-than-manager condition that the holds prevent.

Verification: record the hostnames, installed versions, and held state immediately before the window. Releasing holds happens only after all three central components report `4.14.7-1`.

### Step 1.4 - Capture the baseline

Run the repository's existing health checks on `security-01`:

```bash
apt list --installed wazuh-indexer
apt list --installed wazuh-manager
apt list --installed wazuh-dashboard
systemctl is-active wazuh-indexer wazuh-manager wazuh-dashboard
sudo /var/ossec/bin/agent_control -l
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1/
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1:55000/
```

Expected baseline:

- All three central packages report `4.14.6-1`.
- All three services report `active`.
- The manager reports 15 active remote agents, measured 2026-08-04, against the 14 recorded on 2026-08-03.
- The dashboard returns HTTP `302` and the unauthenticated API root returns HTTP `401`.

Questions 3 through 5 are already answered from the 2026-08-04 preflight. Do not continue when the live baseline differs from the plan.

### Step 1.5 - Confirm the package candidate and maintenance inputs

Run Wazuh's documented `apt-get update`, then use the answer approved under Question 2 to prove that each unversioned install command will select exactly `4.14.7-1` and Filebeat-OSS `7.10.2-2`. Do not add `-y`, `--only-upgrade`, a version pin, a conffile force flag, or another option that is absent from the reviewed sources.

```bash
apt-get update
```

Export all dashboard saved objects through **Dashboard management > Dashboards Management > Saved objects** if there are any worth keeping. There is no index snapshot, per Step 1.1. Indexer authentication uses the admin certificate from Question 6.

Verification: the candidate proof names the exact package versions. Any mismatch stops the window before a service is stopped.

## Step 2 - Prepare the indexer upgrade

### Step 2.1 - Stop Filebeat and the dashboard

```bash
systemctl stop filebeat
systemctl stop wazuh-dashboard
systemctl is-active filebeat wazuh-dashboard
```

Expected result: both services print `inactive`. `systemctl is-active` returns a nonzero exit code for this expected stopped state.

This begins the visible monitoring gap. The dashboard will remain unavailable until Step 5.

### Step 2.2 - Save the live indexer security configuration

```bash
/usr/share/wazuh-indexer/bin/indexer-security-init.sh --options "-backup /etc/wazuh-indexer/opensearch-security -icl -nhnv"
```

Expected result: the script connects to the one-node indexer, reports a healthy cluster state, stores all security configuration types under `/etc/wazuh-indexer/opensearch-security`, and returns no failure.

### Step 2.3 - Quiesce the single-node indexer path

Authenticate with the admin certificate rather than a password. Nothing sensitive reaches the command line, which also means these commands can be run non-interactively.

The shard-allocation setting exists so a multi-node cluster does not shuffle shards during a rolling restart. This indexer is a single node with nothing to relocate, so it is harmless but not load-bearing here. The flush is the step that matters: it commits in-memory data to disk before the service stops.

```bash
CERT="--cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem"

curl -s $CERT -k -X PUT "https://127.0.0.1:9200/_cluster/settings"   -H 'Content-Type: application/json'   -d '{"persistent":{"cluster.routing.allocation.enable":"primaries"}}'

curl -s $CERT -k -X POST "https://127.0.0.1:9200/_flush"
systemctl stop wazuh-manager
systemctl is-active wazuh-manager
```

Expected result:

- The allocation update returns `"acknowledged": true` and `"enable": "primaries"`.
- The flush result reports `"failed": 0`. Do not copy Wazuh's example shard total into the acceptance result because the live total may differ.
- `wazuh-manager` prints `inactive`; the nonzero `systemctl is-active` exit code is expected.

No agent can report to the manager after this stop. The dashboard and Filebeat are already stopped, so the monitoring interface and newly indexed events remain unavailable until later steps restore them.

## Step 3 - Upgrade and assess the indexer

### Step 3.1 - Upgrade `wazuh-indexer`

```bash
systemctl stop wazuh-indexer
cp /etc/wazuh-indexer/jvm.options /etc/wazuh-indexer/jvm.options.old
apt-get install wazuh-indexer
systemctl daemon-reload
systemctl enable wazuh-indexer
systemctl start wazuh-indexer
```

When `apt-get` prompts about `/etc/wazuh-indexer/jvm.options`, choose the updated package file as Wazuh instructs. Reapply only the local JVM differences captured and approved under Question 5. Do not copy the old file wholesale over the new version.

Immediate verification:

```bash
apt list --installed wazuh-indexer
systemctl is-active wazuh-indexer
```

Expected result: package `wazuh-indexer` is `4.14.7-1` and the service prints `active`.

### Step 3.2 - Complete the indexer post-upgrade actions

```bash
/usr/share/wazuh-indexer/bin/indexer-security-init.sh

curl -k -u <YOUR_WAZUH_INDEXER_USERNAME> https://192.168.72.2:9200/_cat/nodes?v

curl -X PUT "https://192.168.72.2:9200/_cluster/settings" -u <YOUR_WAZUH_INDEXER_USERNAME> -k -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}
'

curl -k -u <YOUR_WAZUH_INDEXER_USERNAME> https://192.168.72.2:9200/_cat/nodes?v
```

Expected result:

- `indexer-security-init.sh` updates all ten expected security configuration types and ends `Done with success`.
- The node query returns the one upgraded indexer node.
- The allocation update returns `"acknowledged": true` and `"enable": "all"`.
- The second node query still returns the one upgraded node after allocation is restored.

### Step 3.3 - Stop and assess before touching the manager package

```bash
apt list --installed wazuh-indexer
systemctl is-active wazuh-indexer
curl -k -u <YOUR_WAZUH_INDEXER_USERNAME> https://192.168.72.2:9200/_cat/nodes?v
curl -k -u <YOUR_WAZUH_INDEXER_USERNAME> https://192.168.72.2:9200/_cluster/health?pretty
/usr/share/wazuh-indexer/bin/opensearch-plugin list
```

Continue only when all of these are true:

- `wazuh-indexer` is `4.14.7-1` and its service is active.
- The one indexer node is present.
- Cluster health is `green`, `timed_out` is `false`, node and data-node counts are both one, and unassigned shards are zero.
- Shard allocation is back at `all`.
- Security initialization ended `Done with success`.
- No indexer plugin is labeled `outdated`.

**Stop and assess here.** Manager, Filebeat, and dashboard are intentionally stopped at this gate, so their reachability and agent counts are not valid indexer acceptance checks. If any indexer condition fails, do not install the manager or dashboard package. There is no rollback, so investigate rather than pressing on, and do not add another component mismatch.

## Step 4 - Upgrade the manager and Filebeat

### Step 4.1 - Upgrade `wazuh-manager`

```bash
apt-get install wazuh-manager
systemctl daemon-reload
systemctl enable wazuh-manager
systemctl start wazuh-manager
```

Wazuh says a modified `/var/ossec/etc/ossec.conf` will not be replaced by the package. Do not add the CDB-list migration, which applies to upgrades from 4.12 or earlier. Do not add the vulnerability-detection and indexer-connector migration, which applies to upgrades from 4.7 or earlier. Resolve any `database_output` use under Question 4 before running this step because Wazuh 4.14.7 removes that deprecated configuration and `wazuh-dbd`.

Immediate verification:

```bash
apt list --installed wazuh-manager
systemctl is-active wazuh-manager
/var/ossec/bin/wazuh-control info -v
/var/ossec/bin/wazuh-control status
```

Expected result: `wazuh-manager` is `4.14.7-1`, the service prints `active`, `wazuh-control info -v` returns `v4.14.7`, and the required manager daemons report running. Do not require `wazuh-dbd` in 4.14.7.

### Step 4.2 - Update the Wazuh Filebeat integration

```bash
curl -s https://packages.wazuh.com/4.x/filebeat/wazuh-filebeat-0.5.tar.gz | sudo tar -xvz -C /usr/share/filebeat/module
curl -so /etc/filebeat/wazuh-template.json https://raw.githubusercontent.com/wazuh/wazuh/v4.14.7/extensions/elasticsearch/7.x/wazuh-template.json
chmod go+r /etc/filebeat/wazuh-template.json
cp /etc/filebeat/filebeat.yml /etc/filebeat/filebeat.yml.old
apt-get install filebeat
cp /etc/filebeat/filebeat.yml.old /etc/filebeat/filebeat.yml
systemctl daemon-reload
systemctl enable filebeat
systemctl start filebeat
filebeat setup --pipelines
filebeat setup --index-management -E output.logstash.enabled=false
```

The restored `filebeat.yml` must be the configuration captured and reviewed under Question 3. Do not assume the current file matches a default.

Verification:

```bash
apt list --installed filebeat
systemctl is-active filebeat
filebeat test output
sudo /var/ossec/bin/agent_control -l
```

Expected result:

- Filebeat is the Wazuh-supported Filebeat-OSS 7.10.2 package, published for this release as `7.10.2-2`.
- The service prints `active`.
- `filebeat test output` reaches the indexer and ends with its documented connection checks as `OK` and compatibility version `7.10.2`.
- The manager returns all 14 remote agents active and zero disconnected before the dashboard package step begins.

If agent status has not recovered, stop and assess. Do not treat the manager package as accepted solely because systemd says it is active.

## Step 5 - Upgrade the dashboard

### Step 5.1 - Upgrade `wazuh-dashboard`

```bash
cp /etc/wazuh-dashboard/opensearch_dashboards.yml /etc/wazuh-dashboard/opensearch_dashboards.yml.old
apt-get install wazuh-dashboard
systemctl daemon-reload
systemctl enable wazuh-dashboard
systemctl start wazuh-dashboard
```

When `apt-get` prompts about `/etc/wazuh-dashboard/opensearch_dashboards.yml`, choose the updated package file as Wazuh instructs. Reapply only the reviewed local differences from Question 5, including the existing `server.ssl.key` and `server.ssl.certificate` values. Do not add the `uiSettings.overrides.defaultRoute` migration, which Wazuh limits to upgrades from 4.7 and earlier.

Import the saved objects exported in Step 1.5 through **Dashboard management > Dashboard Management > Saved objects**.

### Step 5.2 - Verify the dashboard component

```bash
apt list --installed wazuh-dashboard
systemctl is-active wazuh-dashboard
sudo -u wazuh-dashboard /usr/share/wazuh-dashboard/bin/opensearch-dashboards-plugin list
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1/
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1:55000/
```

Expected result:

- `wazuh-dashboard` is `4.14.7-1` and the service prints `active`.
- No dashboard plugin is labeled `outdated`.
- The local dashboard returns HTTP `302` and the unauthenticated API root returns HTTP `401`.
- `https://wazuh.alphasecunited.com/` loads the Wazuh application through the existing internal route.

If a plugin is `outdated`, stop. Do not substitute a name into Wazuh's generic remove and install examples until Question 9 has a plugin-specific answer.

## Step 6 - Final acceptance and agent hold release

### Step 6.1 - Prove the central stack is complete

```bash
apt list --installed wazuh-indexer
apt list --installed wazuh-manager
apt list --installed wazuh-dashboard
systemctl is-active wazuh-indexer wazuh-manager filebeat wazuh-dashboard
sudo /var/ossec/bin/agent_control -l
```

In the Wazuh dashboard **Server management > Dev Tools** console, run:

```text
GET /agents/summary
GET /manager/status
```

The central upgrade is accepted only when:

- `wazuh-indexer`, `wazuh-manager`, and `wazuh-dashboard` are all exactly `4.14.7-1`.
- `wazuh-indexer`, `wazuh-manager`, `filebeat`, and `wazuh-dashboard` are all active.
- Manager status reports every required daemon running.
- The dashboard is reachable at `https://wazuh.alphasecunited.com/` and the direct local check returns HTTP `302`.
- The agent summary returns `active: 14` and `disconnected: 0`, matching the 2026-08-03 baseline.
- No indexer or dashboard plugin is labeled `outdated`.

Record the observed result for every line. A command being issued is not acceptance.

### Step 6.2 - Disable unattended central-component updates

After, and only after, Step 6.1 passes, apply Wazuh's recommended APT-source disablement:

```bash
sed -i "s/^deb /#deb /" /etc/apt/sources.list.d/wazuh.list
apt update
```

Verification: the source file has no active line beginning `deb `, `apt update` succeeds, all four services remain active, and the agent summary remains 14 active and zero disconnected.

### Step 6.3 - Release agent holds one host at a time

Do not release any agent hold until Step 6.1 passes. Use the approved roster and commands from Question 8. For each of the twelve hosts, finish the following gate before moving to the next host:

1. Record the hostname, starting agent version, source state, and held state.
2. Release only that host's hold with the approved command.
3. Upgrade only that host to the manager-compatible target.
4. Verify the installed package version, `wazuh-agent` active state, established TCP 1514 session, and active synchronized manager identity.
5. Stop if any check fails. Do not release the next hold.

Releasing any hold before the manager reaches `4.14.7-1` re-creates the overshoot that the holds prevent. Releasing the twelve together removes the one-host failure boundary required by this plan.

## Expected monitoring gap

The gap begins when Step 2.1 stops Filebeat and the dashboard. Agent reporting becomes unavailable when Step 2.3 stops the manager. The dashboard remains intentionally unavailable until Step 5 starts and verifies it, and Filebeat does not send new manager output while it is stopped.

Wazuh documents a default agent reconnection interval of 60 seconds, a default agent buffer of 5,000 events, and a default manager disconnected threshold of 15 minutes. The repository does not establish this fleet's actual queue settings, event rates, or threshold. Do not promise lossless buffering or a fixed outage length. The expected gap is the observed interval between the documented service stops and successful Step 6.1 verification. A quiet or unreachable dashboard inside that interval is expected; failure to recover 14 active and zero disconnected afterward is not.

## Open questions

Eight of the nine were resolved by preflight measurement on 2026-08-04. What each turned out to be:

| # | Question | Resolution |
|---:|---|---|
| 1 | Restorable rollback | **None, accepted.** See Step 1.1. |
| 2 | Pinning to `4.14.7-1` | Plain apt does this: `apt-get install wazuh-indexer=4.14.7-1`. Wazuh documents unversioned commands, but an explicit version is ordinary apt behaviour and does not need vendor blessing. |
| 3 | Filebeat package and customization | **Already `filebeat 7.10.2-2`**, the version Wazuh requires, so no Filebeat upgrade is needed. `/etc/filebeat/filebeat.yml` is 985 bytes dated Feb 24 and gets preserved. |
| 4 | Does the config use `database_output`? | **No.** `grep -c database_output /var/ossec/etc/ossec.conf` returns `0`, so 4.14.7 removing it and `wazuh-dbd` changes nothing here. |
| 5 | Which settings are custom? | Indexer JVM heap is `-Xms1024m -Xmx1024m`, tuned down for this VM and **must survive the upgrade**. Indexer plugins are the standard bundled OpenSearch set. Preserve `/etc/wazuh-indexer/`, `/etc/filebeat/filebeat.yml`, and `/var/ossec/etc/ossec.conf`. |
| 6 | How to supply authenticated indexer checks | **Admin certificate, not a password.** `/etc/wazuh-indexer/certs/admin.pem` and `admin-key.pem` exist, and `curl --cert ... --key ...` authenticates to the indexer API with no credential on the command line and nothing to redact. Verified 2026-08-04: cluster `green`, 1 node, 400 active primary shards, 0 unassigned. |
| 7 | How long can the manager be stopped? | The manager's `<remote>` carries `queue_size 131072`, and agents buffer locally as well. A package restart is seconds. Not a concern at this fleet size. |
| 8 | Hold-release roster | Not a blocker for this plan. Releasing holds happens after the manager is upgraded, one host at a time, and is tracked separately. |
| 9 | Plugin marked `outdated` | Only the bundled OpenSearch plugins are installed, and the Wazuh packages carry them. Handle it if the preflight reports one; do not pre-fill a name. |

Headroom confirmed the same day: `/` has 68 GiB free of 97 GiB, 27 percent used.

## Sources

- [Wazuh upgrade guide and component compatibility](https://documentation.wazuh.com/current/upgrade-guide/index.html)
- [Wazuh central-component upgrade procedure](https://documentation.wazuh.com/current/upgrade-guide/upgrading-central-components.html)
- [Wazuh package list](https://documentation.wazuh.com/current/installation-guide/packages-list.html)
- [Wazuh 4.14.7 release notes](https://documentation.wazuh.com/current/release-notes/release-4-14-7.html)
- [Wazuh architecture and component data flow](https://documentation.wazuh.com/current/getting-started/architecture.html)
- [Wazuh agent-manager compatibility](https://documentation.wazuh.com/current/installation-guide/wazuh-agent/index.html)
- [Wazuh indexer API health check](https://documentation.wazuh.com/current/user-manual/indexer-api/getting-started.html)
- [Wazuh server API use cases](https://documentation.wazuh.com/current/user-manual/api/use-cases.html)
- [Wazuh manager process and version checks](https://documentation.wazuh.com/current/user-manual/reference/tools/wazuh-control.html)
- [Wazuh dashboard and Filebeat troubleshooting](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/troubleshooting.html)
- [Wazuh agent connection settings](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/client.html)
- [Wazuh agent queue behavior](https://documentation.wazuh.com/current/user-manual/agent/agent-management/antiflooding.html)
- [Wazuh agent connection states](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/agent-life-cycle.html)

## Command provenance

| Commands | Source |
|---|---|
| Component package installs, service stops and starts, indexer security backup and restore, allocation changes, flush, node queries, Filebeat module and template work, pipeline setup, plugin lists, saved-object workflow, and APT-source disablement | [Wazuh central-component upgrade procedure](https://documentation.wazuh.com/current/upgrade-guide/upgrading-central-components.html) |
| Published Debian package names and release artifacts | [Wazuh package list](https://documentation.wazuh.com/current/installation-guide/packages-list.html) |
| `apt list --installed` final package checks | [Wazuh central-component upgrade procedure](https://documentation.wazuh.com/current/upgrade-guide/upgrading-central-components.html#next-steps) |
| Indexer cluster-health query and expected fields | [Wazuh indexer API health check](https://documentation.wazuh.com/current/user-manual/indexer-api/getting-started.html) |
| `wazuh-control` version and process checks | [Wazuh manager process and version checks](https://documentation.wazuh.com/current/user-manual/reference/tools/wazuh-control.html) |
| `filebeat test output` | [Wazuh dashboard and Filebeat troubleshooting](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/troubleshooting.html) |
| Dev Tools `/agents/summary` and `/manager/status` queries | [Wazuh server API use cases](https://documentation.wazuh.com/current/user-manual/api/use-cases.html) |
| `systemctl is-active`, `agent_control -l`, and the local dashboard and API `curl` checks | [Repository Wazuh runbook](../Runbook.md) |
