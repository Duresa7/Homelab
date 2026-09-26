# SSH Manager Shared Server Cutover

**Created:** 2026-09-03  
**Last updated:** 2026-09-25

**Implementation date:** 2026-09-03  
**Status:** Complete; nightly restart timer added the same day  
**Affected systems:** `docker-blue`

## Outcome

The SSH Manager MCP server now runs as one persistent Compose service on `docker-blue` instead of a container the gateway starts per client session. `mcp-proxy` inside the image serves the stdio server over Streamable HTTP, and the gateway reaches it as a remote server. Containers can no longer accumulate, and the behaviour a local install gives is back: one process holds the SSH connection pool, interactive sessions, tunnels and history for every caller. Four parallel Executor calls left zero managed containers and the gateway at eight of its 256 processes. All eighteen hosts answer, and the privilege model is unchanged.

## Why

The gateway keeps a managed container per MCP client session and frees it only when the client closes that session, which Executor never does. `--long-lived` does not share one container across sessions; the [troubleshooting record](../Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md) has that diagnosis from the log and the 0.43.3 source. Restarting the gateway was the only remedy, and it costs every live session one failed call.

Four options were on the table. Dropping `longLived` gives a container per call that is removed on release; it stops the growth but adds one to two seconds per call and abandons `ssh_session_*`, tunnels and history, which is exactly the local behaviour I did not want to lose. A scheduled restart or a reaper keeps the speed and the leak. A larger process limit only delays exhaustion. Running the server myself and pointing the gateway at it over HTTP fixes the cause: there is one process, so there is nothing per-session to leak, and the server's own state is shared the way it is when run locally. I took the fourth.

## Changes

`mcp-ssh-manager` speaks stdio only, so the image now also carries [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) 0.12.0, which spawns the server once and serves it on `0.0.0.0:8080` at `/mcp` with `/status` for health. The MCP Python SDK is pinned to 1.29.1 beside it: mcp-proxy 0.12.0 declares only `mcp>=1.17.0`, but the 2.x line removed the `mcp.server.lowlevel.server.request_ctx` symbol it imports, so the first build resolved to 2.1.1 and the container crash-looped on an `ImportError`. A `mcp-proxy --help` smoke test in the build now turns that into a build failure. The entrypoint still accepts `--stdio` to run the bare server for a one-off local test.

The catalog entry changed from `type: server` with an image to `type: remote` at `http://ssh-manager:8080/mcp` over the project network, published on no host port. The gateway rejects a non-HTTPS remote, so its service sets `DOCKER_MCP_ALLOW_INSECURE_REMOTE_URLS=1`, and `--long-lived`, `--cpus`, `--memory` and `--secrets` came off its command because none applies to a remote server.

The eighteen server definitions moved out of the catalog into `ssh-manager-servers.env`. I first wrote here that the file is tracked; that was wrong, because `.gitignore` excludes `*.env`, so it exists only on the host and as a local copy under `Configuration/` (corrected 2026-09-25). The private key and ten sudo passwords moved from the gateway secret store into the root-owned `ssh-manager.env` at mode `0600`. Both are read by the new service through `env_file`. The key is written to a `/keys` tmpfs at mode `0600` at start rather than into the container filesystem. The `ssh-manager-state` volume is now declared `external` because the gateway created it unprefixed; it carries the enrolled host keys and the server's persisted local configuration unchanged. The service runs with `init`, all capabilities dropped, `no-new-privileges`, a 256-process limit, 512 MiB and one CPU.

I ran the [cutover script](../../Scripts/ssh-manager-shared-server-cutover.sh), which backs up the live Compose file and catalog, installs the staged files, derives the new env file from the old secret file, builds, waits on both health checks, confirms the gateway lists 37 tools, and restores everything on any failure. Its first run exited silently without rolling back: `[ $i -gt 30 ] && { ...; }` returns non-zero when the condition is false, and under `set -e` that ends the script. The waits use `if` now. The UniFi gateway was not touched and stayed up throughout.

## Verification

- The build reported `mcp-ssh-manager@3.8.5`, MCP SDK 1.29.1 and a working `mcp-proxy`. The service became healthy in 6 seconds and the gateway 6 seconds after that.
- The gateway logged `37 tools listed in 47.8ms` against the remote server, against about a second when it had to start a container.
- `docker ps -a --filter label=docker-mcp-name=ssh-manager` returns nothing. No managed container exists at all now.
- Four Executor calls issued in parallel, the pattern that produced 22 containers earlier the same day, left the gateway at 8 of 256 processes and the server at 13 of 256. The server holds 82 MiB against its 512 MiB limit and the gateway 21 MiB.
- All eighteen hosts returned their own hostname and login account through `ssh_execute`. The five Proxmox nodes and `docker-main` answered as `root`, `ansible-01` as `ansible`, `ubuntu-dev` as `ai-agent`, the other ten as `dkadi`.
- `ssh_execute_sudo` returned UID `0` on the other twelve. Four of the five Proxmox nodes return `sudo: not found`, which is how they were before: they log in as root and carry no `sudo` binary, so the earlier records' claim that they reach root through root login rather than sudo still holds.
- The interactive session test is the one that could not pass before. `ssh_session_start` on `media_01` in one Executor call, then `ssh_session_send` in three later separate calls: the second call read back `pwd=/tmp` and `marker=shared-server-ok` from the `cd` and `export` issued in the first. `ssh_session_list` showed the session as ready between calls.
- `ssh_tunnel_create` opened a local forward from `monitor_01`, `ssh_tunnel_list` reported it active, and `ssh_tunnel_close` removed it. `ssh_history` returned the shared command log across calls. `ssh_health_check` on `red_server` returned `healthy`.
- A UniFi network list through the other gateway returned 22 networks, confirming that gateway was unaffected.
- The old `ssh-manager-secrets.env` is gone from the host. Before removing it I proved that the new file's key names map one to one and that the sorted values hash identically, so no credential was lost or changed. Neither file was ever read into a transcript.

## Cleanup

I removed the staging directory, the `pre-proxy-20260903` rollback image tag and the superseded secret file. The temporary test session and tunnel are closed, and `ssh_session_list` and `ssh_tunnel_list` are empty. No snapshot was taken and no backup was retained.

## Nightly Restart

A local install got a fresh server process whenever Claude Code was reopened, because the client told the server it was done. Executor never sends that signal, which is the root of today's problem, so the shared server would otherwise live until something restarted it. To keep the daily fresh start I installed a systemd timer and one-shot service on `docker-blue`, both versioned under [Configuration/systemd](../../Configuration/systemd/). The timer fires at 4 AM Eastern with an explicit time zone so daylight-saving changes do not move it, is `Persistent` so a missed run catches up at boot, and the service runs `docker compose restart ssh-manager` in the project directory. The gateway is not touched.

I ran the service once by hand at 5:56 PM Eastern to prove the behaviour. The container restarted in one second and came back healthy with restart count 0. The gateway stayed up, logged no error, and the next Executor call through it succeeded with no reconnect, because the bridge runs stateless and there was no session for the restart to invalidate. Zero managed containers before and after. The first scheduled run is 2026-09-04 at 4 AM Eastern. The first version of the unit carried a `%20` in its documentation URL, which systemd read as a specifier and warned about; it is escaped now and the units verify clean.

## Open State

`allowHosts` no longer applies: a remote server has no container to restrict, and the limit was never enforced for the managed one either because that needs `--block-network`. The SSH Manager server reaches any host it can route to, and I decided the same day to keep it that way. I want it able to reach any machine I add to it, so no Docker network rule follows this change.

Two upstream behaviours are worth watching. A gateway release that shares one managed server across independent Streamable HTTP sessions, or an Executor release that closes its MCP sessions, would make the old layout viable again, though neither would improve on this one. `mcp-proxy` and the MCP Python SDK are both pinned, so a future update of either needs the build smoke test to pass and a real session test afterwards.

## Related Records

- [Managed SSH Manager containers accumulated under long-lived](../Troubleshooting/Managed%20SSH%20Manager%20Containers%20Accumulated%20Under%20long-lived%20-%202026-09-03.md)
- [SSH Manager gateway process exhaustion](SSH%20Manager%20Gateway%20Process%20Exhaustion%20-%202026-09-02.md)
- [Docker MCP Gateway v2 compatibility rollback](v2%20Compatibility%20Rollback%20-%202026-09-03.md)
- [SSH Manager MCP integration](SSH%20Manager%20MCP%20Integration%20-%202026-08-31.md)
- [Executor integration separation](../../../Executor/Documentation/Change%20Records/MCP%20Integration%20Separation%20-%202026-08-31.md)
