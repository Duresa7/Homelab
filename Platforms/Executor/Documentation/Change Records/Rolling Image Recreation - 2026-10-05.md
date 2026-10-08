# Rolling Image Recreation

**Created:** 2026-10-05  
**Last updated:** 2026-10-07

**Implementation date:** 2026-10-05  
**Status:** Complete; [service incident closed](../../../../Security/Incidents/Executor/Rolling%20Image%20Lost%20Data%20Directory%20Access%20-%202026-10-05.md)  
**Affected systems:** `docker-blue` (CT 108), the `executor` Compose project, every MCP integration that answers through Executor

## What happened

The [2026-10-05 fleet update](../../../../Operations/Maintenance/Fleet%20Update%20-%202026-10-05.md) ran the `docker-compose-update.yml` play against `docker-blue` at 11:49 PM Eastern. The play pulled `ghcr.io/usefulsoftwareco/executor-selfhost:latest`, which resolved to the build published on 2026-09-18 (image ID `b9e001775d3e`, labelled 1.6.10, revision `3890d6f`). The container that had been running since 2026-09-19 was on the older build `c8dd83a5dba8` from 2026-08-30, whose label reads 1.6.7, even though the application reported 1.6.10 at the time. The 2026-09-19 recreation recorded in the README did not move the container onto the newer build; this one did.

The new container entered a restart loop. Its log ended in `EACCES: permission denied, open '/data/secret.key'` from `resolveSecretKey`. The 2026-08-30 image ran as root; the 2026-09-18 image runs as UID and GID 65532. The bind mount `/opt/docker/executor/data` was `root:root` mode 700, holding `auth-secret.key`, `data.db` and `secret.key`, so the unprivileged process could not even traverse the directory and treated the key as absent. The play's `--wait` gate reported `container executor is unhealthy` after three attempts and stopped that project; MeshCentral and RustDesk in the same run recreated normally.

While Executor was down, every tool call through it timed out, including the SSH Manager gateway. I fell back to direct SSH from `ubuntu-dev` to `ansible-01` and `docker-blue`, which the workstation's key already reaches, and did the diagnosis and the repair through Ansible's `become` on `docker-blue`.

## What I did

1. Read the container log and the image metadata to confirm the user change between the two builds.
2. Confirmed the directory state with `stat`: the directory and all three files were owned by UID 0.
3. Ran `chown -R 65532:65532 /opt/docker/executor/data` and `docker restart executor`.
4. Watched the container reach `healthy` within 20 seconds and answer `/mcp`.

I changed no file contents and generated no new key. The existing `secret.key` and `data.db` carried over, so the saved connections and their stored secrets were untouched.

## Verification

- `docker ps` shows `executor` as `Up (healthy)` with the data directory and its three files now `65532:65532`, modes unchanged (700 on the directory, 600 on the two keys, 644 on the database).
- `connections.list` through Executor returned the full saved connection inventory after the restart, and an SSH Manager call through the gateway completed.
- The first Executor call after the restart returned `MCP server "executor" session expired`; the client re-established its session on the next call. That is the expected effect of a server restart, not a fault.

## Repository changes

The Compose reference under `Configuration/` is unchanged: the image reference, the bind mount and the hardening options are the same. The ownership of the host-side data directory is now part of what the deployment needs, and the README's version row points here.
