# Managed SSH Manager Containers Accumulated Under long-lived

**Created:** 2026-09-03  
**Last updated:** 2026-09-25

**Observed:** 2026-09-03 1:51 PM to 2:27 PM Eastern  
**Status:** Resolved 2026-09-03 by the [shared server cutover](../Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md)

## Symptom

Thirty-six minutes after the SSH Manager gateway was restarted at the end of the [v2 compatibility rollback](../Change%20Records/v2%20Compatibility%20Rollback%20-%202026-09-03.md), `docker-blue` was running 22 `homelab/mcp-ssh-manager:latest` containers with generated names, all started by `ssh-manager-mcp-gateway`, which still runs the exact 0.43.3 image with `--long-lived`. The platform record said exactly one is the expected state and a second one is a fault. Another agent noticed the count during a routine host check while working on the Wazuh integration and handed it to me rather than repairing it mid-task.

The gateway's cgroup read `pids.current 192` against `pids.max 256`, each managed container holding about nine processes through its `docker run` bridge. The containers together used about 600 MiB. Every call still answered; at the observed rate the gateway had roughly eight sessions of headroom before it would stop forking, which is the failure recorded on 2026-09-02.

## Diagnosis

I correlated the gateway log with the container list, then read the gateway's source at tag `v0.43.3`.

**What the log showed.** Since the 1:51 PM restart, every client session whose first message was a tool call logged `Running homelab/mcp-ssh-manager:latest` on that call, and each `Running` line matched one new container to the millisecond. Sessions that initialized without calling a tool logged no `Running` line and started nothing. Later calls inside a session reused that session's container. No `Client disconnected` line appeared in the whole window.

Sessions arrived in two patterns. Bursts of three or four `Client initialized` lines within ten milliseconds, each followed by its own `Running`, matched the parallel calls the other agent was making. Single new sessions appeared after a failure: a call at 1:57:39 PM never logged a completion, Executor recorded `transportFailure: true` against it a minute later, and the next call at 1:59:04 PM arrived as a fresh session and started a fresh container. Between those events Executor reused idle sessions, which is why sequential calls minutes apart added nothing.

**What the source shows.** In `pkg/gateway/clientpool.go` the kept-client map is keyed by both server name and client session:

```go
type clientKey struct {
	serverName string
	session    *mcp.ServerSession
}
```

`longLived()` returns false when there is no session, and `AcquireClient` looks up `clientKey{serverConfig.Name, session}`. `--long-lived` therefore keeps one managed container per client session for that session's life. It never shares one across sessions. The only release path is `ReleaseClientsForSession`, called from a goroutine that blocks on `ss.Wait()` until the client closes its session. `pkg/gateway/transport.go` builds the streaming handler with `mcp.NewStreamableHTTPHandler(..., nil)`, so the SDK's `SessionTimeout` is zero and idle sessions are never closed by the gateway. The `main` branch keys the map the same way.

Executor never closes a session it opens. It reuses idle ones, opens more when calls run in parallel, and abandons one after a transport failure. Each abandoned or extra session leaves a managed container that only a gateway restart removes.

**What this means for the earlier records.** The 2026-09-02 [process-exhaustion record](../Change%20Records/SSH%20Manager%20Gateway%20Process%20Exhaustion%20-%202026-09-02.md) concluded that `--long-lived` shares one container across sessions because eight sequential calls produced one container. Those calls reused one Executor session, so the test measured Executor's reuse, not the gateway's pooling. The flag did change one thing: without it, the catalog's `longLived: true` alone behaves identically, so the flag was neither the cause nor the cure. Today's [v2 rollback](../Change%20Records/v2%20Compatibility%20Rollback%20-%202026-09-03.md) blamed the `latest` image for one container per session, but 0.43.3 does the same under parallel load. The rollback itself is harmless; the reason given for it does not hold, and the pin is no longer justified by that test.

**A second finding from the same read.** The catalog's `allowHosts` list is only enforced when the gateway runs with `--block-network`; without it `runToolContainer` skips the proxy path and attaches the managed container to `docker-mcp-gateway_default`, which is what the logged `docker run` arguments show. Neither gateway service passes that flag, so the egress limits the platform record described for both managed servers are declared but not applied. That is a separate item in the root TODO.

## Fix

At 2:27 PM I ran `docker compose restart ssh-manager-gateway` in `/opt/docker/mcp-gateway`, scheduled three seconds ahead from a detached shell so the SSH Manager call that issued it could return. Restarting stops every stdio bridge, and Docker removes the managed containers through `--rm`. The `ssh-manager-state` volume is untouched. I changed no Compose file, catalog, secret, or Executor connection, and took no snapshot.

The restart invalidates every session Executor still holds. The first call on each of those fails once with a transport error, after which Executor opens a new session. The next SSH Manager call from any other connected client takes that one failure.

## Verification

- At 2:28:05 PM the gateway reported `running`, `healthy`, restart count 0, and `http://192.168.40.39:8812/health` returned 200.
- `docker ps -a --filter label=docker-mcp-name=ssh-manager` listed one container, started by my verification session at 2:28:02 PM.
- The gateway cgroup read `pids.current 15` and `pids.events max 0`.
- The log showed the startup tool listing, then one `Client initialized` and one `Running` line for the verification call.

The count climbed again with the next parallel calls, because the restart is a reset and not a fix. Later the same afternoon I moved the server out of the gateway's control entirely: it runs as its own Compose service and the gateway reaches it over HTTP, so no per-session container exists to accumulate. That work and its verification are in the [shared server cutover](../Change%20Records/SSH%20Manager%20Shared%20Server%20Cutover%20-%202026-09-03.md).

## What I would do differently

Verify a session-sharing claim by counting `Client initialized` lines against `Running` lines, not by counting containers after a handful of calls from one client. And read the pool code before pinning an image on a behaviour difference: the two versions compared today behave the same.
