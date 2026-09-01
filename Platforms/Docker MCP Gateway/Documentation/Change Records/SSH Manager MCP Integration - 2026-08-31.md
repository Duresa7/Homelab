# SSH Manager MCP Integration

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Outcome

I added SSH Manager MCP 3.8.5 to the Docker MCP Gateway on `docker-blue`. The gateway now launches the server on demand and exposes its 37 tools through the existing bearer-protected MCP endpoint at `http://192.168.40.39:8811/mcp`, alongside the UniFi Network server already there. The endpoint reports 42 tools in total, 5 from UniFi and 37 from SSH Manager.

Twelve of the eighteen configured servers answered at initial deployment. I closed the five Proxmox and `ubuntu-dev` blockers later the same day; all eighteen now answer as recorded in [SSH Manager Fleet Reach Completion](SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md).

## Source Selection

Upstream is [bvisible/mcp-ssh-manager](https://github.com/bvisible/mcp-ssh-manager). Its newest release is `v3.8.5`, published 2026-08-28, which fixes three command-injection advisories, one of which bypassed the server's own readonly mode. Tracking the newest release was the point of the change rather than a side effect of it.

The project publishes to npm only. It carries no Dockerfile, and nothing is published to ghcr.io or Docker Hub, so there was no image to pin the way I pinned the UniFi server. The gateway's catalog requires an `image:`, so I build one on `docker-blue` from [Dockerfile.ssh-manager](../../Configuration/Dockerfile.ssh-manager), tagged `homelab/mcp-ssh-manager:latest`. The Dockerfile installs `mcp-ssh-manager@latest`; this build resolved to 3.8.5, confirmed with `npm ls -g` inside the image.

The image carries `openssh-client` and `rsync` on top of `node:22-alpine`. `rsync` is not optional: `ssh_sync` calls `spawn(rsyncCommand, ...)` at `src/index.js:1101` and runs rsync as a local process rather than going through the pure-JS `ssh2` path. I omitted `sshpass` because no fleet entry uses password authentication.

## Implementation

1. I wrote [Dockerfile.ssh-manager](../../Configuration/Dockerfile.ssh-manager) and built `homelab/mcp-ssh-manager:latest` on `docker-blue`. The gateway starts managed containers with `--pull never`, so a locally built image is what it expects.
2. I added the [ssh-manager catalog entry](../../Configuration/catalogs/ssh-manager.yaml), generated from the live MCP configuration so the host, user, port, platform, ProxyJump, and description of all eighteen servers are versioned in this repository. Secret values were excluded at generation time and never entered the file.
3. I added `--catalog=ssh-manager.yaml` and `--servers=ssh-manager` to the gateway's Compose command. Both flags are string slices, so the new values append to the UniFi ones rather than replacing them. SSH Manager is not a Compose service; the gateway spawns it as a stdio container on demand.
4. I restricted the managed container's network to the eighteen server addresses on TCP 22 through `allowHosts`.
5. I loaded the ten configured sudo passwords into `/opt/docker/mcp-gateway/mcp-secrets.env`, owned by root with mode `0600`, and mapped each to its `SSH_SERVER_<NAME>_SUDO_PASSWORD` variable through the catalog's `secrets:` block. Eight servers have no sudo password configured and never escalate.
6. I applied the tracked [3.8.5 homelab patch](../../Configuration/patches/mcp-ssh-manager-3.8.5-homelab.patch). It lets remote MCP clients upload and download bounded inline content without access to the server container's filesystem, and replaces upstream's hostname-only SSH2 host check with a comparison against the received key's SHA-256 fingerprint.
7. I persisted SSH Manager state, including `known_hosts`, in the `ssh-manager-state` volume. Unknown keys and changed keys are refused. The OpenSSH client used by `ssh_sync` also has `StrictHostKeyChecking yes`.
8. I kept the server `longLived` because its `ssh_session_*` tools hold an interactive shell between calls. A Streamable HTTP client must close its gateway session when finished; the managed container is otherwise expected to stay up.
9. I recreated the gateway from its pinned 0.43.3 image.

### The private key could not be mounted

My first design bind-mounted the `ai-agent@ubuntu-dev` private key into the container read-only. The gateway refused to start the server:

```
Can't start ssh-manager: validate volume for ssh-manager: unsafe docker volume
"/opt/docker/mcp-gateway/keys/id_ed25519:/keys/id_ed25519:ro":
host path "/opt/docker/mcp-gateway/keys/id_ed25519" is blocked (credential file)
```

Gateway 0.43.3 blocks bind-mounting anything it recognises as a credential file. I did not work around the check by renaming the file. Instead I routed the key through the gateway's own secret store, which is the mechanism built for this: the key is base64-encoded onto a single line as `ssh-manager.private_key_b64`, passed in as `SSH_PRIVATE_KEY_B64`, and written to `/keys/id_ed25519` at mode `0600` by the image's entrypoint before it execs the server. The key is never in an image layer. Its source remains only in the root-owned secret file, while each managed container holds a mode-`0600` materialized copy until that container is removed. I removed the `/opt/docker/mcp-gateway/keys` directory that the abandoned design created.

The image writes an SSH client config setting `StrictHostKeyChecking yes` because the rsync-backed tools shell out to OpenSSH. The patched `ssh2` path computes the received key's SHA-256 fingerprint and compares it with every enrolled fingerprint for that host and port. Upstream 3.8.5 treated any hostname present in `known_hosts` as verified without comparing the presented key, then accepted unknown hosts by default. The image refuses both cases instead.

## Verification

- Compose validation passed and `docker-mcp-gateway` returned to healthy on the pinned 0.43.3 image. `/health` returned HTTP 200.
- The gateway log shows `Those servers are enabled: unifi-network, ssh-manager` and `> ssh-manager: (37 tools)`.
- An unauthenticated MCP initialization returned HTTP 401. An authenticated initialization returned HTTP 200 and established a session.
- `tools/list` through the endpoint returned 42 tools, 37 of them SSH.
- `ssh_list_servers` through the endpoint returned all 18 servers.
- `ssh_execute_sudo` against `docker_blue` returned `root`, which proves the injected key authenticated and the sudo password reached the container from the secret store.
- `ssh_execute` returned the expected hostname and account for `media_01` (`media-01`, `dkadi`), `ansible_01` (`ansible-01`, `ansible`), `edge_01` (`edge-01`, `dkadi`), and `monitor_01` (`monitor-01`, `dkadi`). `monitor_01` is reached through `ProxyJump=ansible_01`, so that path survives containerization.
- The built image contains the inline-transfer patch and the SSH2 key-mismatch check, its OpenSSH client configuration reports `StrictHostKeyChecking yes`, and the persistent known-hosts file held 52 enrolled key lines after verification.
- The pre-commit review found that the first inline-download implementation checked its size only after SFTP completed. I replaced that path with a capped stream that reads at most one byte beyond the 1 MiB limit, rebuilt the live 3.8.5 image, and restarted only the SSH Manager gateway. A fresh Executor session listed all 18 servers, returned a 17-byte inline file, and rejected a 1,048,577-byte file with `Inline download exceeds the 1048576-byte limit`. The remote test files were removed.
- The rebuilt image omits `sshpass`, which no configured fleet entry uses. Its package inventory still reports `mcp-ssh-manager@3.8.5`, and the image inspection found the bounded-download method present.
- The catalog's `allowHosts` set contains 18 unique `address:22` entries and matches all 18 configured server addresses with no missing or extra host.
- A direct gateway session uploaded the UTF-8 text `inline-transfer-ok` to a temporary file, downloaded the same content inline, removed the file, and closed with HTTP 204. No managed SSH Manager container or temporary file remained.
- `ssh_execute` against `red_server` failed with `Timed out while waiting for handshake`. A TCP 22 sweep from `docker-blue` across all eighteen addresses showed the five Proxmox nodes on `192.168.70.0/24` blocked and the other thirteen open, which locates the cause in the firewalls rather than in the key or the image.
- `ssh_execute` against `ubuntu_dev` failed with `All configured authentication methods failed`.
- The live MCP secret file is root-owned with mode `0600` and holds 14 entries. No secret value was written to this repository, and the temporary files used to move the key and the sudo passwords onto `docker-blue` were shredded.

No snapshot or backup was created. The deployment is reproducible from the versioned Compose file, Dockerfile, and catalog; secret values remain outside the repository. I retained no standalone command or API capture; the verification bullets above record the live results I observed.

## Open State

**The six reach blockers closed later on 2026-08-31.** I added a TCP 22 UniFi policy from `192.168.40.39` to the five node addresses, added that source to Proxmox `pve_admins`, authorized the gateway identity on `ubuntu-dev`, and enrolled `ubuntu-dev`'s three verified host keys. All six now pass through Executor. The complete implementation and verification are in [SSH Manager Fleet Reach Completion](SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md).

**The container holds a key that reaches root across the fleet.** This was a deliberate choice to match what the local server can do, taken with the tradeoff stated. The gateway already mounts the Docker socket, so it is root on `docker-blue`, and the bearer token now also fronts fleet-wide SSH with full read and write including sudo on ten hosts. Executor is connected through a personal encrypted credential and puts that same reach behind its `execute` tool. No Executor policy override currently requires approval for the imported tools.

The later [agent client cutover](../../../Executor/Documentation/Change%20Records/Agent%20Client%20Cutover%20-%202026-08-31.md) retained that no-approval behavior by request in Codex and Claude Code. This is the accepted current boundary rather than an undocumented pending decision.

**The image tracks `latest`, but the patch targets 3.8.5.** A rebuild can resolve a new upstream version. The patch should make the build fail if its source context no longer applies, but a clean apply does not prove the behaviour still matches the new release. Record the resolved version, rebase the patch when it changes, and repeat the transfer and host-key checks. This build is 3.8.5.
