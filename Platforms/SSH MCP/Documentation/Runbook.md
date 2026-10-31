# SSH MCP Runbook

**Created:** 2026-10-31  
**Last updated:** 2026-10-31

The current state is on the [platform front page](../README.md). Every step below runs on `docker-blue` (`192.168.40.39`) as root unless it says otherwise.

## Routine Checks

```bash
cd /opt/docker/ssh-mcp
docker compose ps
docker compose logs --tail 50 ssh-mcp
curl -fsS http://192.168.40.39:8813/health        # {"healthy":true,"configured":true}
tail -n 5 data/ssh-mcp/audit.log
```

`configured: false` means the config did not load, and every tool call except `reload-config` is refused. A POST to `/` without the bearer token returns `401`.

From `ubuntu-dev`, with the bearer token injected from my password manager into `SSH_MCP_BEARER_TOKEN`:

```bash
node "Platforms/SSH MCP/Tests/fleet-smoke.mjs" "Platforms/SSH MCP/Configuration/config.toml"
PROFILES=monitor_01,hq_dc01 node "Platforms/SSH MCP/Tests/fleet-smoke.mjs" "Platforms/SSH MCP/Configuration/config.toml"
```

It runs `whoami` on every profile and `id -u` through `privileged-command` on every Linux profile that does not log in as root. Its exit status is the number of failing profiles. A host that is powered off fails with `EHOSTUNREACH`.

## Changing a Profile or Adding a Host

1. Edit [config.toml](../Configuration/config.toml). A Windows host's comment line ends in `(Windows OpenSSH)`, which the smoke test reads.
2. For a new host, add its keys to `/opt/docker/ssh-mcp/known_hosts` with `ssh-keyscan <ip>` and no `-t` filter, and confirm the fingerprints out of band. An operating system reinstall regenerates the keys, so replace that host's lines rather than appending.
3. A host that needs a sudo password gets `SSH_MCP_<PROFILE>_SUDO_PASSWORD` in `/opt/docker/ssh-mcp/ssh-mcp.env`, the profile name upper-cased with every other character turned into `_`. Write it from my password manager on the host; never put it in a command string.
4. Copy `Dockerfile`, `docker-compose.yml`, `config.toml`, `pin-host-keys.py` and `install-on-docker-blue.sh` to a mode-0700 stage directory and run `sh install-on-docker-blue.sh <stage>`. It rewrites the live config with pins and prints the profile, pin and sudo-password counts. It stops if any profile has no `known_hosts` entry.
5. Reload without a restart: `docker kill -s HUP ssh-mcp`. The log prints the profiles it added, removed and changed. A failed check changes nothing and the log says why. An env file change needs `docker compose up -d --force-recreate` instead, because the environment is read once.
6. Run the smoke test for the changed profiles.

## Updating ssh-mcp

1. Read the release notes from the running version forward. 2.x has removed flags and changed defaults inside the major version.
2. Change `SSH_MCP_VERSION` in the Dockerfile and the image tag in the Compose file together.
3. `docker compose build --pull && docker compose up -d`, detached if the call has a deadline.
4. Check health, `docker compose logs` for a clean start, and the full smoke test. Then update this platform's README.

## Rebuilding

Nothing here is backed up. To rebuild, install the tracked files, recreate `keys/id_ed25519` from `ubuntu-dev`'s `~/.ssh/id_ed25519`, which is the same `ai-agent@ubuntu-dev` key (UID 65532, mode 0400), recreate `ssh-mcp.env` with the bearer token and each sudo password, collect `known_hosts` with `ssh-keyscan` and confirm each fingerprint against the host, then run the install script. Its first run on 2026-10-31 copied the key, sudo passwords and `known_hosts` from the SSH Manager container, which no longer exists, so a rebuild cannot take that path. Executor's `ssh` app keeps working across a rebuild as long as the bearer token is unchanged.
