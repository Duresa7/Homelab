# SSH Manager Gateway Process Exhaustion

**Created:** 2026-09-02  
**Last updated:** 2026-09-03

**Superseded in part:** the conclusion that `--long-lived` shares one container across client sessions did not hold. The eight verification calls reused one Executor session. The gateway keeps one container per session in this version, which the [2026-09-03 troubleshooting record](../Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) shows from the log and the source. The diagnosis of the exhaustion and the cleanup below stand.

## Outcome

The SSH Manager gateway stopped answering tool calls on 2026-09-02 because it had used 251 of its 256 allowed processes and could no longer fork a managed server container. I restarted it with `--long-lived` so it keeps one SSH Manager server for its whole lifetime instead of starting one per client session. Three separate Executor sessions afterwards shared one managed container, and the gateway's refused-fork counter stayed at zero.

## Symptom

Every SSH Manager call through Executor returned `Internal tool error` with a correlation ID, including `ssh_list_servers`, which takes no arguments. Executor's own log showed only `McpInvocationError: MCP tool call failed`. The UniFi gateway on the same host answered normally, the SSH gateway's health endpoint at `192.168.40.39:8812/health` returned 200, and Compose reported the container healthy.

## Diagnosis

I read the gateway from inside CT 108 on `blue-server`, because the SSH Manager path I would normally use was the thing that was broken.

- `docker ps` showed 28 running `homelab/mcp-ssh-manager:latest` containers with generated names, created between 11:26 AM Eastern on 2026-09-01 and 5:22 AM Eastern on 2026-09-02. None had exited.
- `docker top` on `ssh-manager-mcp-gateway` showed 27 `docker run` child processes, one per managed container, each holding about nine PIDs. The container's cgroup read `pids.max 256` and `pids.current 251`.
- The cgroup's `pids.events` read `max 360`: the kernel had refused 360 forks against the limit. `memory.events` showed no memory pressure. The UniFi gateway's `pids.events` read `max 0`.
- The gateway log showed the last completed call at 5:22 AM Eastern, an `ssh_upload` that spawned the 27th child and finished in under a second. Every later call, from 5:28 AM onward, logged `Calling tool` and never logged a completion. The gateway wrote no error line for the failed fork.
- The gateway had been started at 11:26 AM Eastern on 2026-09-01. It took about eighteen hours of ordinary use to fill the limit.

The catalog entry carried `longLived: true`, and the integration record expected each Streamable HTTP client to close its session with `DELETE`. Executor opens a fresh MCP session for every `execute` call and never closes it, so each call left a managed container and its stdio bridge behind until the gateway was restarted. Without the gateway-level `--long-lived` flag, the catalog marker only kept a container alive for its own session; it did not share one across sessions.

## Changes

1. I copied the live `/opt/docker/mcp-gateway/docker-compose.yml` on the host before editing. The file holds only `${VAR}` references and secret file paths, no values. The copy is committed as [docker-blue-docker-compose-2026-09-02.yml](../../../../Backups/docker-blue-docker-compose-2026-09-02.yml) and the host copy is deleted.
2. I added `--long-lived` to the `ssh-manager-gateway` command, directly after the `--secrets` argument, in both the live Compose file and the versioned [Compose reference](../../Configuration/docker-compose.yml). The two files were identical before the edit and remain identical after it.
3. `docker compose config --quiet` passed. `docker compose up -d ssh-manager-gateway` recreated only the SSH Manager gateway. The UniFi gateway was not touched.

The recreation stopped the 27 stdio bridges, and Docker removed all 28 orphaned managed containers through `--rm`. The `ssh-manager-state` volume with the enrolled host keys was not affected. I took no snapshot.

## Verification

- Twenty seconds after the recreation, Compose reported `ssh-manager-mcp-gateway` as `Up (healthy)`, the cgroup read `pids.current 8`, and `docker ps -a` filtered on the SSH Manager image returned no containers.
- Three Executor `execute` calls, each opening its own MCP session, ran `ssh_list_servers`, `ssh_connection_status`, and `ssh_health_check` against `red_server`. `ssh_list_servers` returned the eighteen-entry catalog in 895 ms. `ssh_connection_status` returned a validation error for a missing `action` argument, which proves the server answered. `ssh_health_check` returned `overall_status: healthy` for `red_server` in 729 ms.
- After those three sessions the gateway held one `docker run` child, one managed container was running, `pids.current` read 16, and `pids.events` read `max 0`.
- The gateway log showed one `Running homelab/mcp-ssh-manager:latest` line for the first call and none for the later two.
- A second round of five fresh Executor sessions exercised the remaining tool types. `ssh_execute` on `media_01` returned `media-01`, `dkadi`, and the uptime with exit code 0. `ssh_execute_sudo` on `docker_blue` returned UID `0` and counted one managed SSH Manager container. `ssh_execute` on `grey_server` returned five cluster nodes and `Quorate: Yes`. `ssh_service_status` on `red_server` reported `pve-cluster` and `pveproxy` running and healthy.
- After both rounds the gateway still held one `docker run` child and one managed container, `pids.current` read 16, `pids.events` read `max 0`, and both gateway containers reported healthy.

No standalone transcript was retained. The counters and log lines above are the live readbacks observed during the change.

## What Changed for Operations

The managed SSH Manager container now lives as long as the gateway. The README's earlier instruction to look for containers left by interrupted clients no longer describes normal operation: one container is expected, and a second one is a fault. Restarting the gateway remains the way to reset the server's interactive `ssh_session_*` state.

## Related Records

- [SSH Manager MCP integration](SSH%20Manager%20MCP%20Integration%20-%202026-08-31.md)
- [SSH Manager fleet reach completion](SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md)
- [Executor integration separation](../../../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
