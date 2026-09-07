# Integration Tool Calls Time Out at 60 Seconds

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Observed:** 2026-09-07, 2:05 to 2:09 AM Eastern, during the Coolify non-root change on `app-01`  
**Affects:** Every integration tool called from `execute`, on Executor 1.6.8. Seen through the SSH Manager gateway, but the cause is not in the gateway  
**Status:** Root cause found in Executor's bundle. Not configurable. Workaround in place, upstream change needed

## Symptom

Two `execute` runs that called `ssh_execute_sudo` with a remote `sleep 150` and a remote `sleep 80` failed. The first came back as `Internal tool error`, the second as `The operation timed out`. In both cases the remote command had already started, so I could not tell from the error how far it had run and had to read the host state back before continuing. Passing `timeout: 300000` to the SSH tool made no difference.

## What I measured

Timed `ssh_execute` calls against `docker_blue` from inside `execute`, each with `timeout: 120000` on the SSH tool:

| Remote command | Result | Wall time |
| --- | --- | --- |
| `sleep 45; echo slept45` | returned `slept45`, exit 0 | 45.2 s |
| `sleep 75; echo slept75` | `The operation timed out` | about 60 s |

The failure is an `execute` error, not a tool result. A timeout inside the SSH Manager or the gateway would have come back as `{ ok: false, error }` and my code would have returned it normally. The run itself was killed.

## Root cause

Executor calls every integration tool through the MCP TypeScript SDK's client, and passes no options:

```js
// /app/apps/host-selfhost/dist-server/serve.js, Executor 1.6.8, near line 306411
try: () => connection.client.callTool({ name: toolName, arguments: args }),
```

The SDK's request path applies `options?.timeout ?? DEFAULT_REQUEST_TIMEOUT_MSEC`, and `DEFAULT_REQUEST_TIMEOUT_MSEC = 60000`. So every tool call gets the SDK default of 60 seconds, the `Request timed out` error it raises is what surfaces as `The operation timed out`, and nothing downstream can extend it: the gateway, mcp-proxy and the SSH Manager all sit on the far side of that timer. The SSH tool's own `timeout` argument governs the SSH session on the far side and is irrelevant once the client has given up.

The SDK does offer `resetTimeoutOnProgress`, which would keep the timer alive while a server sends progress notifications, but Executor does not set it and the SSH Manager does not send progress.

Two things this is **not**:

- **Not `EXECUTOR_SANDBOX_TIMEOUT_MS`.** That variable exists in 1.6.8 and bounds the whole sandbox run. It is unset here, and it would not help: the per-call SDK timer fires first.
- **Not the Nginx Proxy Manager path.** The proxy host carries 3600-second read and send timeouts from the initial deployment.

The only Executor probe that sets its own timeout is the version-negotiation probe, which uses `PROBE_ANSWER_TIMEOUT_MS`. No release from 1.5.42 through 1.6.8 mentions tool call timeouts, and the open upstream issues about timeouts on 2026-09-07 concern elicitation waits and `tools.search`, not this.

## Workaround

**Keep a single tool call under about 55 seconds.** For anything longer, detach it on the remote host in its own session and poll:

```sh
setsid nohup sh -c '<long command>' > /tmp/<job>.log 2>&1 < /dev/null & echo $!
```

then read `/tmp/<job>.log` in a later call and remove it when done. `setsid` and the closed stdin are not decoration. A plain `nohup ... &` behind the SSH Manager was killed when the calling session ended: a 70-second test job left an empty log after its deadline had passed. The `setsid` form was tested the same morning: the launching call returned in 0.2 seconds, the job was still running 19 seconds later with its parent session gone, and a later call read the completed log. A `sleep` inside the remote command to wait for something is the pattern to stop using; wait between calls instead, and poll only after the job's deadline has passed, because an early `cat` reads an empty file and looks like a failure.

`ssh_session_send` does not avoid this. It runs through the same client call and the same timer.

## What would fix it

Executor passing a configurable timeout to `callTool`, for example an `EXECUTOR_MCP_TOOL_TIMEOUT_MS` environment variable beside the existing `EXECUTOR_SANDBOX_TIMEOUT_MS`, or setting `resetTimeoutOnProgress` and letting servers that report progress run longer. Either is an upstream change. Patching the bundle inside the image is not worth it: the deployment tracks `latest` and the patch would vanish at the next pull. Raising it upstream is recorded as a decision in the root `TODO.md`, because it means posting to a public tracker.
