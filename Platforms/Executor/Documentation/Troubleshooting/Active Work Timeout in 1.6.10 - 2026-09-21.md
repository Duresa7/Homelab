# Active Work Timeout in 1.6.10

**Created:** 2026-09-21  
**Last updated:** 2026-09-25

## Symptom

An integration tool call through Executor that runs past 60 seconds fails before the remote command finishes. On 2026-09-21 I checked whether that cap could be raised on `docker-blue` (`192.168.40.39`). Executor reports version 1.6.10 and is healthy. The 60-second integration timeout remains, but its implementation differs from the [1.6.8 investigation](Integration%20Tool%20Calls%20Time%20Out%20at%2060%20Seconds%20-%202026-09-07.md).

## Error

`ssh_execute` with `command: "sleep 65"` and `timeout: 90000` returned `Internal tool error [5cfe3c00]`, with no normal tool result and no elapsed-time value.

## What I checked

I read the running container's `/app/apps/host-selfhost/dist-server/serve.js` through SSH Manager. An initial `docker exec executor sh` failed with exit 127 because the image has no shell. Streaming `docker cp` into `tar` and Python succeeded without creating a host copy. I inspected these sections:

- Line 337627 sets `MCP_ACTIVE_WORK_TIMEOUT_MS = 60000`.
- Line 337812 calls `makeActiveWorkDeadline()` without an override for each MCP tool invocation.
- Line 337816 passes that deadline's abort signal to `connection.client.callTool`, together with `MCP_SDK_TIMEOUT_BACKSTOP_MS = 2147483647`. The SDK default no longer owns the 60-second limit.
- The active-work timer pauses during elicitation and resumes with its remaining budget. Ordinary SSH command execution consumes that budget.
- `EXECUTOR_SANDBOX_TIMEOUT_MS` configures a separate sandbox limit. It cannot extend the hard-coded integration deadline.

The live `ssh_execute` tool description accepts `timeout` in milliseconds, defaults to 120000, and caps it at 300000. Passing a larger SSH timeout cannot extend Executor's earlier deadline.

I called `ssh_execute` on `docker_blue` with `command: "sleep 65"` and `timeout: 90000` through Executor. The call failed with `Internal tool error [5cfe3c00]`; no normal tool result or elapsed-time value returned. This reproduces a failure for a command longer than the source-defined deadline, but the generic error alone does not identify its cause. A subsequent `true` command returned exit 0. I retained no separate terminal transcript for these checks.

## Root cause

Executor 1.6.10 hard-codes `MCP_ACTIVE_WORK_TIMEOUT_MS = 60000` and passes that deadline's abort signal to every MCP tool call. No environment variable or command flag overrides it, and the SSH tool's own `timeout` argument runs inside it.

## Rate limits and available changes

A timeout limits how long one command runs. A rate limit limits requests within a time window. In the installed bundle, `EXECUTOR_DISABLE_AUTH_RATE_LIMIT` controls authentication throttling; the API-key plugin's own rate limiter is disabled. Neither setting raises the integration command deadline. The sandbox-timeout and authentication-rate-limit environment overrides are both absent from the running container. I found no explicit timeout or rate-limit command flags in either gateway container's configured arguments. This inspection does not establish every downstream service's rate limits.

Raising the integration deadline to five minutes requires changing Executor's `MCP_ACTIVE_WORK_TIMEOUT_MS` to 300000 or adding a configurable value at that call site. The installed build exposes no setting for this. A maintained custom image or an upstream release is required; a one-off image patch would be lost on replacement. Any custom build still needs end-to-end validation against the gateway and SSH timeout layers.

I changed no running configuration and restarted no containers. Long operations can continue using the previously verified detach-and-poll workaround. Selection and deployment of a custom build remain open.
