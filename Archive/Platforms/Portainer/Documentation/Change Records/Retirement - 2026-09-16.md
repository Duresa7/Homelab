# Retirement

**Created:** 2026-09-16  
**Last updated:** 2026-09-16

**Status:** Complete.  
**Execution:** 2026-09-16, 4:24 AM Eastern onward.

I retired Portainer after verifying Dockhand's independent connections to all seven Docker hosts. I removed the server and four Edge Agents, their data and images, network publication, dedicated credentials, and automation and monitoring entries. Dockhand now manages 42 projects, 64 running containers, and six stopped Hawser updater containers. Every remaining container retained its ID, start timestamp, and running state.

## Containers and data

I removed these five imported stacks through Dockhand's authenticated stack removal API with named-volume and stack-file removal enabled. Each imported definition contained only its Portainer service.

| Host | Stack | Container | Removed data volume |
|---|---|---|---|
| docker-main | portainer | portainer_ce | portainer_portainer_data |
| docker-blue | portainer-edge-agent | portainer_edge_agent | portainer-edge-agent_portainer_agent_data |
| docker-network | portainer-edge-agent | portainer_edge_agent | portainer-edge-agent_portainer_agent_data |
| media-01 | portainer-edge-agent | portainer_edge_agent | portainer-edge-agent_portainer_agent_data |
| alpha-prod-01 | portainer-edge-agent | portainer_edge_agent | portainer-edge-agent_portainer_agent_data |

I also removed the unused `portainer_data` volume on docker-main after checking it had no container consumers. I removed the five original deployment directories, the server image tag, and the three retained agent tags on each remote host: `latest`, `2.45.0`, and `2.39.1`. Compose removed the dedicated networks. The agents' host-root, Docker socket, and Docker volume-directory bind mounts were not deleted.

[Stack removals](../../Evidence/Retirement%20-%202026-09-16/Exports/Stack-Removals.json), [host cleanup](../../Evidence/Retirement%20-%202026-09-16/Exports/Host-Cleanup.json), and [host verification](../../Evidence/Retirement%20-%202026-09-16/Exports/Host-Verification.json) retain the results. No Portainer container, image tag, named volume, deployment directory, or imported stack remains on the seven connected hosts. Docker-main no longer accepts TCP connections on localhost ports 8000 or 9443.

I deleted the dedicated Portainer credential item and the three separately stored Edge Agent items for docker-blue, docker-network, and media-01. No separate alpha-prod-01 credential item was present. I left shared credentials and NPM's certificate credential in place.

## Network cleanup

I removed NPM proxy host 14 for `portainer.alphasecunited.com`, which forwarded to `https://192.168.40.35:9443`. The other 23 proxy host IDs remain present. Nginx configuration validation passed; shared certificate 1 remains in use. NPM retains its normal deleted database row, with no active proxy configuration.

The saved shared login was rejected by NPM. I completed the authorized proxy deletion through its normal HTTP API using a two-minute session issued by NPM's token model inside its container for the existing administrator. The session token stayed in process memory. I did not reset a password or change authentication configuration.

I removed these UniFi resources after live readback:

| Resource | Identifier | Result |
|---|---|---|
| Portainer A record | 6a60fd2b2d027bb05525a852 | Removed; 29 static records remain |
| Allow A-Servers to Portainer Edge | 69dde0a1a508864f48576830 | Removed |
| Allow docker-network to Portainer Edge | 6a68eb3f052792cd2140c9ad | Removed |
| Portainer Edge Agents port group | 69dde070a508864f485767bd | Removed after checking all 371 policies for references; 22 Network Lists remain |
| Allow NPM to docker-main web UIs | 6a60fd2c2d027bb05525a873 | Removed only destination TCP 9443; retained 2283, 3000, 3001, 3002, 3003, and 6060 |

The final controller readback has no Portainer DNS record, firewall policy, or port-group reference. Dockhand's DNS record and management paths remain active. Cloudflare had no exact public DNS record or Access application for `portainer.alphasecunited.com`, so I made no Cloudflare changes. [Network changes](../../Evidence/Retirement%20-%202026-09-16/Exports/Network-Changes.json) and [readback](../../Evidence/Retirement%20-%202026-09-16/Exports/Network-Verification.json) record the controller results.

## Maintenance and monitoring

I removed the five Portainer projects from the fleet-maintenance inventory and its expected-project validator, both in the workspace and on ansible-01. Both copies of the validator pass with 11 OS-update hosts, six Compose hosts, and 20 projects. Its initial run correctly rejected the old total of 25; I changed the expected count to 20. Both copies of `inventory/hosts.yml` carry the same 20 projects: docker-main 7, docker-network 2, docker-blue 3, media-01 1, alpha-prod-01 5, monitor-01 2.

I updated the maintenance README in the workspace. A later readback found the deployed copy still described the retired Portainer projects, so I synchronized `/home/ansible/fleet-updates/README.md` on ansible-01 and verified its SHA-256 matches the workspace copy. I also corrected the deployed inventory comments about the retired game-01 host and the five Proxmox nodes. Parsed YAML before and after is identical, and the deployed validator still passes with 11 OS-update hosts, six Compose hosts, and 20 projects.

I removed the Portainer HTTPS target from Prometheus, validated the candidate with promtool, and reloaded configuration without restarting the container. The target assertion passes: 57 expected targets are present and healthy, with no stale addresses and no Portainer target. I updated the Uptime service inventory and regenerated the Uptime, Services & Uptime, and Homelab Overview dashboards. Uptime now covers 28 service checks, including 22 internal HTTPS names; Services & Uptime covers 23 HTTP probes including the alert bot.

All 27 dashboards passed layout validation. The three changed dashboards passed their live PromQL checks: 116, 19, and 21 queries, with no errors or unexpected empty results. Grafana's provisioned resource records match the deployed panel definitions, and none mentions Portainer. The initial verification queried Grafana's legacy dashboard table, which is empty in this deployment; I verified the current resource table instead. No Grafana restart was needed.

## Final state and records

[Dockhand verification](../../Evidence/Retirement%20-%202026-09-16/Exports/Dockhand-Verification.json) confirms all seven environment tests pass and the five removed stacks are absent. Every remaining running container with a configured health check is healthy. TeamSpeak voice servers and other applications stayed running.

I archived the former platform records and guide, repaired their links, updated the current service and network inventories, and closed the retirement task. The deployed documentation website was not rebuilt as part of retirement; this repository carries the updated records.

I retained structured exports for container, stack, and network operations. NPM validation, credential deletion, maintenance validation, monitoring reload, and dashboard verification were observed during this session; no complete terminal transcript is retained for those steps. I created no snapshot or backup. The Prometheus candidate file was removed after validation and reload, and no temporary file was left on a host.
