# Wazuh Runbook

**Created:** 2026-07-13  
**Last updated:** 2026-09-25

## Manager Health

Use SSH Manager against `security_01`. Expected units are enabled/active and expected listeners are TCP 1514, 1515, 443, and 55000:

```bash
systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard
ss -lnt | grep -E ':(443|1514|1515|55000)[[:space:]]'
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1/
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1:55000/
```

Expected unauthenticated responses are dashboard `302` and API `401`.

List agents and check shared-policy synchronization:

```bash
sudo /var/ossec/bin/agent_control -l
sudo /var/ossec/bin/agent_groups -S -i <agent-id>
```

## Fresh Agent Enrollment

1. Confirm the host is intended for monitoring and its hostname is correct.
2. Confirm the endpoint can reach `192.168.72.2` on TCP 1514 and 1515 before changing its package state.
3. Add the exact inventory name, connection settings, and any required existing Wazuh groups under `Source/agent-deployment/inventory/hosts.yml`.
4. Run `ansible-playbook --syntax-check` and `--list-hosts` from the deployment project.
5. Limit the first live run to the intended host or a named batch with `--limit`.
6. Verify package version and hold, enabled and active service state, a non-empty client key, and an established TCP 1514 session.
7. Verify the manager reports the exact identity active and synchronized.

The play pins new agents to manager version 4.14.6-1, disables the Wazuh APT source after installation, and holds the package. It stops before package work when either manager port is unavailable. I used it for IDs `006` through `017` on 2026-08-03; the final seven-host and Green-only runs changed zero hosts.

Grey, Purple, Blue, Red, and Green set `WAZUH_AGENT_GROUP=default,proxmox`. Verify both groups after enrollment with `agent_groups -s -i <agent-id>`.

## MCP Server

The live project is `/opt/docker/wazuh-mcp-server` on `security-01`. It uses host networking because the Indexer listens only on `127.0.0.1:9200`; the MCP listener itself binds to `192.168.72.2:3000`.

Routine local checks:

```bash
cd /opt/docker/wazuh-mcp-server
docker compose ps
curl -fsS http://192.168.72.2:3000/health
curl -fsS http://192.168.72.2:3000/ready
sudo ./verify_mcp.py
```

`/ready` must report the Manager, Indexer, and MCP service healthy. `verify_mcp.py` performs a credential-safe protocol test, calls the Manager agent API plus Indexer alert and vulnerability queries, and closes its MCP session. It must report 41 tools and `write_tools_exposed=0` for the current 4.3.0 release. A POST to `/mcp` without a bearer credential must return `401`.

The optional `search_external_context` tool sends its caller-supplied query to You.com. Its API credential is in the protected live `.env`. A healthy Executor call returns `enabled: true` with search results. `SSL_CERT_FILE` must remain `/etc/ssl/certs/wazuh-combined-ca-bundle.pem`, which includes the base image's public roots and the two local Wazuh trust anchors.

Verify the Docker Blue route separately:

```bash
curl -fsS http://192.168.72.2:3000/health
```

For a rebuild or upstream refresh, install the versioned files first, then run:

```bash
cd /opt/docker/wazuh-mcp-server
docker compose config --quiet
docker compose build --pull
docker compose up -d --wait --wait-timeout 180
sudo ./verify_mcp.py
```

Do not replace `docker compose build --pull` with `docker compose pull`: the final image is built locally from a digest-pinned upstream base. Before moving beyond 4.3.0, dry-run both patch files against the new upstream source and confirm the local compatibility fixes are still required.

## Remove an Obsolete Agent

Stop the endpoint agent first, create rollback copies, remove the exact manager ID with `manage_agents -r`, and verify `agent_control -l`.

## Recovery

Bring the manager back in this order:

1. Verify VM 200 is running with VLAN tag 72 and address `192.168.72.2`.
2. Verify `wazuh-indexer`, then `wazuh-manager`, then `wazuh-dashboard` are active.
3. Verify TCP listeners 1514, 1515, 443 and 55000.
4. Verify the dashboard and API responses locally before testing from another zone.
5. List the manager's agents with `agent_control -l` and confirm the expected 15 are active.

Do not weaken a firewall policy to compensate for a failed local service. The 2026-09-11 manager outage and its restore are in the [incident record](../../../Security/Incidents/Wazuh/Manager%20Processes%20Terminated%20by%20Hash%20Refresh%20-%202026-09-11.md).

An endpoint agent has no rollback point. The 2026-07-13 clean removal deleted `/var/ossec` from `app-01` and `edge-01`, and restoring an old manager `client.keys` would reintroduce identities with no endpoint state behind them. Recover an endpoint by installing a current supported agent and enrolling a fresh exact-name identity against `192.168.72.2`, then verify it active.

A network-level rollback of VM 200 follows the [Security-A migration change record](../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md#rollback-points). It is not a routine agent recovery step.

## URLs

- Dashboard: `https://192.168.72.2/`
- API: `https://192.168.72.2:55000/`
- MCP: `http://192.168.72.2:3000/mcp`
