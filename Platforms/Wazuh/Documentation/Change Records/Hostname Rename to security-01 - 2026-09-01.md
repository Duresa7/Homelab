# Hostname Rename to security-01

**Created:** 2026-09-01  
**Last updated:** 2026-09-01

## Date

I did this on 2026-09-01, between about 5:45 PM and 6:30 PM Eastern.

## Scope

VM 200's Proxmox guest name has been `security-01` since it was built, but its `/etc/hostname` said `wazuh-01`, so every shell prompt, journal line and Wazuh agent name disagreed with the name every record uses. I moved the operating system hostname to `security-01` and rebooted the guest.

This closes the first of the two deviations found on 2026-08-15 and recorded in [Root SSH Disabled on ansible-01 and security-01](../../../../Operations/Maintenance/Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md). The decision that `security-01` is canonical was taken on 2026-09-01 and is in the [platform TODO](../TODO.md).

The host is the Wazuh 4.14.7 manager, indexer and dashboard at `192.168.72.2` on Security-A/VLAN 72. It also carries the Splunk Universal Forwarder, `node_exporter` and cAdvisor.

I took no snapshot. The preflight below is what replaced one.

## Preflight, read-only

The platform TODO named three things that read the current hostname, one of which could have taken the indexer down. I read all three before touching anything.

**The indexer does not derive anything from the hostname.** Out of `/etc/wazuh-indexer/opensearch.yml`:

```yaml
network.host: "127.0.0.1"
node.name: "node-1"
cluster.name: "wazuh-cluster"
plugins.security.nodes_dn:
- "CN=indexer,OU=Wazuh,O=Wazuh,L=California,C=US"
```

The node certificate matches, and its only SAN is a loopback address:

```console
subject=C = US, L = California, O = Wazuh, OU = Wazuh, CN = wazuh-indexer
X509v3 Subject Alternative Name:
    IP Address:127.0.0.1
```

So the security plugin's node check keys on `CN=indexer`, not on the machine name, and the rename could not break it. The dashboard reaches the indexer at `https://127.0.0.1:9200` and Filebeat at `127.0.0.1:9200`, both loopback. The manager's cluster stanza uses a static `<node_name>node01</node_name>`.

**Agent 000 is dynamic.** `ossec.conf` carries no `<agent_name>` and `client.keys` has no `000` row, so the manager reads its own agent name from the operating system hostname at runtime. That settled the TODO's open question: no re-registration was needed, and in fact `agent_control -l` reported the new name before the reboot, immediately after `hostnamectl` ran.

**Splunk defaults its `host` field to the hostname.** The forwarder's `inputs.conf` set no `host`, so forwarded alerts would have split at the rename. `server.conf` also carried `serverName = wazuh-01`.

Nothing else on the host held the old name. `grep -rn 'wazuh-01'` across `/var/ossec/etc/`, `/etc/filebeat/`, `/etc/wazuh-indexer/`, `/etc/wazuh-dashboard/` and `/opt/splunkforwarder/etc/system/local/` returned only `server.conf`.

The DNS record `wazuh.alphasecunited.com` points at Nginx Proxy Manager on `192.168.85.2`, and all 15 remote agents address the manager as `192.168.72.2`, so neither depends on the guest's own name.

## What I changed

Four things, in this order. The two Splunk edits went first so that the `host` field never split.

```ini
# /opt/splunkforwarder/etc/system/local/inputs.conf
[monitor:///var/ossec/logs/alerts/alerts.json]
index = wazuh
sourcetype = wazuh:alerts
host = security-01
disabled = 0
```

```ini
# /opt/splunkforwarder/etc/system/local/server.conf
[general]
serverName = security-01
```

```console
# hostnamectl set-hostname security-01
# grep 127.0.1.1 /etc/hosts
127.0.1.1 security-01
```

Then a full reboot, chosen over a rolling service restart so that nothing anywhere was left holding the cached old name.

## The sudo chain mistake

My first attempt at these edits partly failed, and it is worth recording why. `ssh_execute_sudo` prepends `sudo -S -k -p ''` to the command string it is given, which elevates only the **first** command in a `&&` chain. Everything after the first `&&` ran as `dkadi`.

The visible result was a set of contradictory errors: `sed -i` on a root-owned file appeared to succeed while the `grep` verifying it returned `Permission denied`. What actually happened is that the `sed` was first in its chain and the `grep` was not. The `/etc/hosts` edit was second in its chain and did not run at all, so for a few minutes the host had `hostnamectl` set to `security-01` while `/etc/hosts` still said `127.0.1.1 wazuh-01`.

I caught it before the reboot by re-reading actual state rather than trusting the exit codes, and fixed it by wrapping the whole script in `bash -c '...'` so that sudo applies to the entire thing. Every privileged command after that point used that form.

A hostname that does not resolve in `/etc/hosts` is the classic cause of multi-second `sudo` and service-start stalls, so rebooting in that intermediate state would have been the wrong move.

## Verification

Captured before the reboot, as the baseline:

```console
== agent total ==   16
== agent active ==  16
== agent 000 ==     ID: 000, Name: security-01 (server), IP: 127.0.0.1, Active/Local
== units ==         wazuh-indexer wazuh-manager filebeat wazuh-dashboard SplunkForwarder node_exporter docker
                    active active active active active active active
== fwd conn ==      1
```

After the reboot, from a login shell on the guest:

```console
== prompt identity ==
dkadi@security-01
== hostnamectl ==
security-01
security-01
== hosts ==
127.0.1.1 security-01
== uptime ==
up 6 minutes
== system state ==
running
== units ==
active
active
active
active
active
active
active
```

`systemctl is-system-running` returning `running` rather than `degraded` is the part that matters: no unit failed to start under the new name.

The agent census after the reboot matches the baseline exactly:

```console
total=16
active=16
disconnected=0
   ID: 000, Name: security-01 (server), IP: 127.0.0.1, Active/Local
fwd_sessions=1
```

Service endpoints, checked over the network from `ubuntu-dev`:

| Check | Result |
|---|---|
| `https://192.168.72.2/` | `302` |
| `https://192.168.72.2:55000/` | `401` |
| `https://wazuh.alphasecunited.com/` | `302` |
| `192.168.72.2:1514` | open |
| `192.168.72.2:1515` | open |

The `302` and `401` are the documented healthy responses for the dashboard and the unauthenticated API root.

Proxmox reports the guest as `status: running` with `name: security-01`, so the guest name and the operating system name now agree.

## Cleanup

I copied `/etc/hosts` and the forwarder's `inputs.conf` on the host before editing them, to `/root/*.pre-rename`. Both are gone from the host as of this record. Neither is committed to `Backups/`: the pre-change `inputs.conf` is already the tracked reference under [Configuration/Splunk Forwarder/](../../Configuration/Splunk%20Forwarder/), where git holds its previous version, and the one line that changed in `/etc/hosts` is quoted above in full. The `server.conf` copy never got made, because it was the command that fell victim to the sudo chain problem; the only line that changed there is quoted above as well.

## What remains open

**The SSH Manager gateway's exec path stalled for about 25 minutes after the reboot, then recovered on its own.** From the reboot until about 6:35 PM, `ssh_health_check` against `security_01` returned `overall_status: healthy` and read live CPU, memory and disk, while both `ssh_execute` and `ssh_execute_sudo` hung until the caller timed out. TCP 22 was open from `docker-blue`, where the gateway runs, and a direct `ssh` from `ubuntu-dev` connected and ran commands throughout, so it was neither the guest nor the network. A stale pooled connection on the gateway side that outlived the guest's reboot is the fit. I completed the verification over direct SSH while it was stalled, and `ssh_execute` against `security_01` returned `security-01` normally afterward with no intervention.

This is worth knowing rather than fixing: the gateway's health check can report a host healthy while its exec path is still stale, so a health check alone does not prove the gateway can run a command. It is not specific to Wazuh, and I have not seen it on a host I did not reboot.

**Agent 000's history is split in Splunk and in the Wazuh indexer.** Events before this change carry `agent.name` of `wazuh-01` and events after carry `security-01`. The `wazuh` index keeps 30 days, so the Splunk side heals by 2026-10-01. The Wazuh indexer keeps its own history longer. Nothing keys on the manager's own agent name today, so I left both alone rather than rewriting history.

The second deviation from 2026-08-15, the timezone, was already fixed on 2026-08-30.
