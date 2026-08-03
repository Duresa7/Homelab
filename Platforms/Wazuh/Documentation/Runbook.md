# Wazuh Runbook

**Created:** 2026-07-13  
**Last updated:** 2026-08-03

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
3. Add the exact inventory name, connection settings, & any required existing Wazuh groups under `Source/agent-deployment/inventory/hosts.yml`.
4. Run `ansible-playbook --syntax-check` and `--list-hosts` from the deployment project.
5. Limit the first live run to the intended host or approved batch.
6. Verify package version and hold, enabled and active service state, a non-empty client key, and an established TCP 1514 session.
7. Verify the manager reports the exact identity active and synchronized.

The play pins new agents to manager version 4.14.6-1, disables the Wazuh APT source after installation, and holds the package. It stops before package work when either manager port is unavailable. I used it for IDs `006` through `017` on 2026-08-03; the final seven-host and Green-only runs changed zero hosts.

Grey, Purple, Blue, Red, & Green set `WAZUH_AGENT_GROUP=default,proxmox`. Verify both groups after enrollment with `agent_groups -s -i <agent-id>`.

## Remove an Obsolete Agent

Stop the endpoint agent first, create rollback copies, remove the exact manager ID with `manage_agents -r`, & verify `agent_control -l`.

## URLs

- Dashboard: `https://192.168.72.2/`
- API: `https://192.168.72.2:55000/`
