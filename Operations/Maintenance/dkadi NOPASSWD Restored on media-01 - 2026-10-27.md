# dkadi NOPASSWD Restored on media-01

**Created:** 2026-10-27  
**Last updated:** 2026-10-27

**Change date:** 2026-10-27  
**Status:** Complete and verified. `media-01` is now an exception to the Linux Host Baseline Standard's sudo model  
**Scope:** One new file, `/etc/sudoers.d/90-dkadi`, on `media-01`, and the removal of `media-01`'s stored sudo password from SSH Manager on `docker-blue` and Dockhand's copy on `docker-main`. No account, password, key, sshd setting or other sudoers file changed. No other guest was touched

## Outcome

`dkadi` runs sudo on `media-01` without a password prompt again. I removed this grant fleet-wide on 2026-09-07 (see [NOPASSWD Drop-ins Removed on game-01](../../Archive/Operations/Maintenance/NOPASSWD%20Drop-ins%20Removed%20on%20game-01%20-%202026-09-07.md) for the same change on `game-01`) and I am putting it back on this one host because I want prompt-free sudo there. The trade is the one the standard describes: a stolen `dkadi` key on `media-01` is now root on `media-01`.

| Account | Before | After |
| --- | --- | --- |
| `dkadi` | `(ALL : ALL) ALL` from the `sudo` group, `rootpw` in force | `(ALL : ALL) ALL` plus `(ALL : ALL) NOPASSWD: ALL` from `90-dkadi` |
| `ansible` | `(ALL : ALL) NOPASSWD: ALL` from `90-ansible` | unchanged |

`Defaults rootpw` stays in `00-rootpw`. It no longer affects `dkadi`, because sudo never prompts it, but it still governs any other account in the `sudo` group.

## State before the change

Read through the SSH Manager at about 11:45 PM Eastern:

- `id dkadi` showed groups `dkadi sudo docker`.
- `sudo -n true` as `dkadi` exited `1` with `sudo: a password is required`.
- `/etc/sudoers.d` held `00-rootpw` (`Defaults rootpw`), `90-ansible` (`ansible ALL=(ALL:ALL) NOPASSWD: ALL`) and the packaged `README`, all `0440 root:root`. `/etc/sudoers` carried the stock `%sudo ALL=(ALL:ALL) ALL`. `visudo -c` passed on every file.

This matched the `media-01` row of the baseline standard's fleet state table from 2026-09-07.

## What I changed

At 11:49 PM Eastern, in one root command through `ssh_execute_sudo`:

1. Wrote `dkadi ALL=(ALL:ALL) NOPASSWD: ALL` to a temporary file and validated it with `visudo -cf`, which reported `parsed OK`.
2. Installed it as `/etc/sudoers.d/90-dkadi`, `root:root`, mode `0440`, with `install`, and removed the temporary file.
3. Ran `visudo -c`. `/etc/sudoers`, `00-rootpw`, `90-ansible`, `90-dkadi` and `README` all reported `parsed OK`.

## Verification

- `ls -l /etc/sudoers.d/` listed `90-dkadi` at `-r--r----- root root`, 34 bytes.
- `sudo -l -U dkadi` listed `rootpw` among the Defaults and two grants: `(ALL : ALL) ALL` and `(ALL : ALL) NOPASSWD: ALL`.
- As `dkadi`, through a plain `ssh_execute` with no password supplied: `sudo -n true` exited `0` and `sudo -n id -un` returned `root`.
- `ssh_execute_sudo` with `id -un` still returned `root` with exit code 0, so the SSH Manager's configured sudo path keeps working.

## SSH Manager

With `NOPASSWD` in place, SSH Manager no longer needs a stored sudo password for `media_01`, so I took it out and let `ssh_execute_sudo` fall back to plain `sudo`. Between 11:51 and 11:53 PM Eastern:

1. Deleted the `SSH_SERVER_MEDIA_01_SUDO_PASSWORD` line from the live `/opt/docker/mcp-gateway/docker-compose.yml` and from the reference `/opt/docker/mcp-gateway/ssh-manager.env` on `docker-blue`, and from Dockhand's copy at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` on `docker-main`. The line sat in the middle of the entry, so no JSON comma needed changing. Both Compose files went from `8ca5a233…` (19,953 bytes) to `4d04ec07…` (19,887 bytes), still `0600 root`. `ssh-manager.env` went from 1,161 to 1,109 bytes and holds 10 sudo passwords. `grep -c` for the key returned `0` in all three files, and `docker compose config -q` passed.
2. Recreated only `ssh-manager` with `docker compose up -d --no-deps --no-build --pull never --force-recreate ssh-manager`, detached through `setsid nohup` so the recreate would not cut off the session running it. The log showed `Recreated` and `Started`, and `mcp-ssh-manager` reported `healthy`. I deleted the log afterwards.

Verification after the recreate:

- `env` inside `mcp-ssh-manager` holds 10 `SUDO_PASSWORD` keys and 0 for `MEDIA_01`. I counted key names only.
- `ssh_execute_sudo` with `id -un` on `media_01` issued `sudo id -un`, with no `-S` and no piped password, and returned `root` with exit code 0.
- `ssh_execute_sudo` on `docker_blue` still issued `sudo -S -k` and returned normally, so the other entries are unaffected.
- [ssh-manager.env.example](../../Platforms/Docker%20MCP%20Gateway/Configuration/ssh-manager.env.example) and the [Docker MCP Gateway README](../../Platforms/Docker%20MCP%20Gateway/README.md) no longer list `media-01` as password-backed.

Rollback: put `dkadi`'s sudo password back as `SSH_SERVER_MEDIA_01_SUDO_PASSWORD` in both Compose files and `ssh-manager.env`, recreate `ssh-manager`, then remove `/etc/sudoers.d/90-dkadi` on `media-01`. In that order, so SSH Manager never faces a prompt it cannot answer.

## Standard

The [Linux Host Baseline Standard](../../Security/Hardening/Linux-Host-Baseline-Standard.md) lists this as a named exception under Outside the model as of 2026-10-27, so `90-dkadi` on `media-01` is recorded state, not drift. The 2026-09-07 fleet state table is a dated snapshot and keeps its original row.
