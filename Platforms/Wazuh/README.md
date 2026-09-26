# Wazuh

**Created:** 2026-07-13  
**Last updated:** 2026-09-25

I run Wazuh 4.14.7 as an all-in-one install (manager, indexer and dashboard) on VM 200 `security-01` at `192.168.72.2` on Security-A, VLAN 72. On 2026-09-24 `wazuh-control info` reported v4.14.7 and `agent_control -l` listed 15 agents plus the manager, all active. Every Proxmox node and every running Linux guest carries an agent except `splunk-siem`, which has none. `kali-pen` is stopped and not enrolled, and there are no Windows agents. Alerts forward to Splunk, and Wazuh MCP Server 4.3.0 gives Executor a read-only path to the manager and indexer.

**Owner:** Homelab security monitoring

| Item | Value |
|---|---|
| Host | VM 200 `security-01` on `grey-server`, Ubuntu 24.04.4 LTS, 4 vCPU, 10 GiB memory with an 8 GiB balloon floor, 100 GiB on `ssd-lvm1` (`qm config 200`, 2026-09-24) |
| Packages | `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard` 4.14.7-1 since the [2026-08-04 central upgrade](Documentation/Change%20Records/4.14.7%20Central%20Upgrade%20-%202026-08-04.md) |
| Agents | 15 active on 2026-09-24: IDs `004` to `011`, `013` to `017`, `020` (`ubuntu-dev`) and `021` (`docker-main`). 14 run 4.14.6-1 and `edge-01` runs 4.14.5-1, as last recorded on 2026-09-06; the per-host table is in the [configuration reference](Configuration/README.md#endpoint-installation-state) |
| Agent groups | `default` on every agent; `edge` on `edge-01`, `proxmox` on the five nodes, `workstation` on `ubuntu-dev` |
| Detection | File integrity monitoring per group ([widened 2026-08-29](Documentation/Change%20Records/File%20Integrity%20Monitoring%20Widening%20-%202026-08-29.md)), local rule 100200 against a weekly MalwareBazaar hash list, and the VirusTotal integration ([Malware Detection - 2026-08-29](Documentation/Change%20Records/Malware%20Detection%20-%202026-08-29.md)) |
| Splunk forwarding | A Universal Forwarder on `security-01` ships `/var/ossec/logs/alerts/alerts.json` to `splunk-siem` `192.168.72.3:9997`, index `wazuh`, 30-day retention ([Alert Forwarding to Splunk - 2026-08-29](Documentation/Change%20Records/Alert%20Forwarding%20to%20Splunk%20-%202026-08-29.md)); four Wazuh saved searches in Splunk post to Discord |
| MCP | Wazuh MCP Server 4.3.0 in Docker at `http://192.168.72.2:3000/mcp`, used by Executor on `docker-blue` ([MCP Server and Executor Integration - 2026-09-03](Documentation/Change%20Records/MCP%20Server%20and%20Executor%20Integration%20-%202026-09-03.md)) |

On 2026-09-11 the weekly hash refresh terminated the manager's processes. I restored the manager, and the refresh now restarts it through systemd. The [incident record](../../Security/Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md) holds the cause, verification and monitoring follow-up.

## Layout

- `Configuration/`: reference to the live endpoints, paths, agent state, agent group fragments, detection rules, the Splunk forwarder files and the MCP deployment.
- `Source/agent-deployment/`: idempotent Ansible deployment for the Linux fleet.
- `Scripts/`: the weekly known-bad hash list refresh and its systemd timer.
- `Documentation/Runbook.md`: health checks, enrollment, the MCP server, and recovery.
- `Documentation/Change Plans/`: the 4.14.7 upgrade plan, executed 2026-08-04.
- `Documentation/Change Records/`: dated endpoint and manager changes.
- `Documentation/Troubleshooting/`: issue index and one dated record per operational problem.
- `Documentation/TODO.md`: open Wazuh work.
- `Evidence/`: step-based verification transcripts for bounded changes.

## Dependencies

| Depends on | What for |
|---|---|
| Galaxy, `grey-server` | VM 200 compute and `ssd-lvm1` storage, VLAN tag 72, QEMU guest agent, VM firewall |
| UniFi | Gateway and DNS `192.168.72.1`; zone policies that allow agents to TCP 1514 and 1515, NPM `192.168.85.2` to the dashboard on 443, and the routed path from Executor on `docker-blue` to MCP on 3000. No WAN-inbound policy or port forward exists for Wazuh |
| Internet egress | Wazuh package repository (disabled on agents after install), abuse.ch MalwareBazaar for the weekly hash list, the VirusTotal API |
| `splunk-siem` | Receiving port 9997 for the forwarded alerts |
| Nginx Proxy Manager | `wazuh.alphasecunited.com` with the wildcard certificate |

## Service Endpoints

| Service | Endpoint | Use |
|---|---|---|
| Wazuh dashboard | `https://wazuh.alphasecunited.com/`; direct fallback `https://192.168.72.2/` | Human web interface through internal NPM |
| Wazuh API | `https://192.168.72.2:55000/` | Authenticated API |
| Wazuh MCP | `http://192.168.72.2:3000/mcp` | Bearer-authenticated, read-only MCP endpoint used by Executor on `docker-blue` |
| Agent events | `192.168.72.2:1514/tcp` | Enrolled agent traffic |
| Agent enrollment | `192.168.72.2:1515/tcp` | New agent registration |

NPM presents the Let's Encrypt wildcard certificate to internal dashboard clients and connects to Wazuh's existing HTTPS 443 listener. The direct dashboard still uses its current self-signed certificate. An HTTP `302` from the dashboard and HTTP `401` from the unauthenticated API root are expected healthy responses. The API and agent ports aren't published through NPM. See [Internal HTTPS Service Onboarding - 2026-07-22](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

## Agent History

Enrollment history is in [Endpoint Agent Removal - 2026-07-13](Documentation/Change%20Records/Endpoint%20Agent%20Removal%20-%202026-07-13.md), [Endpoint Re-enrollment - 2026-07-13](Documentation/Change%20Records/Endpoint%20Re-enrollment%20-%202026-07-13.md), [Agent Fleet Deployment - 2026-08-03](Documentation/Change%20Records/Agent%20Fleet%20Deployment%20-%202026-08-03.md) and [docker-main Agent Re-enrollment - 2026-09-06](Documentation/Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md). I removed the Kasm identity 012 on 2026-08-19, `debian-dev` identity 019 on 2026-08-14 and `game-01` identity 018 on 2026-09-12.

The Executor integration and its two narrowly scoped upstream compatibility patches are documented in [MCP Server and Executor Integration - 2026-09-03](Documentation/Change%20Records/MCP%20Server%20and%20Executor%20Integration%20-%202026-09-03.md).
