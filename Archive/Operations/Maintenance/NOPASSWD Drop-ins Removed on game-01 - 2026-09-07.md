# NOPASSWD Drop-ins Removed on game-01

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete and verified. `game-01` now matches the sudo model on the other seven password-gated guests  
**Scope:** `/etc/sudoers.d/90-dkadi` and `/etc/sudoers.d/90-ai-agent` on `game-01`, LXC 123 on `green-server`. No account, password, key, sshd setting or other sudoers file changed. `docker-network`, `monitor-01` and `media-01` still hold their `dkadi` drop-ins and were not touched

## Outcome

A sudo prompt on `game-01` is live for the first time since 2026-08-11. `dkadi` keeps its grant through the `sudo` group, and under `Defaults rootpw` the prompt asks for root's password and refuses everything else. `ai-agent` has no sudo on the host at all, which is what it has on the other ten guests. `ansible` keeps `NOPASSWD`, unchanged.

| Account | Before | After |
| --- | --- | --- |
| `dkadi` | `(ALL : ALL) ALL` from the `sudo` group plus `(ALL : ALL) NOPASSWD: ALL` from `90-dkadi` | `(ALL : ALL) ALL`, password-gated, `rootpw` in force |
| `ai-agent` | `(ALL : ALL) NOPASSWD: ALL` from `90-ai-agent` | not allowed to run sudo |
| `ansible` | `(ALL : ALL) NOPASSWD: ALL` from `90-ansible` | unchanged |

This closes the `game-01` part of the fleet access priority's next step and the policy question left open in [Vanilla Keep Inventory and Host Sudo Policy](../../Platforms/Game%20Servers/Documentation/Change%20Records/Vanilla%20Keep%20Inventory%20and%20Host%20Sudo%20Policy%20-%202026-08-11.md): the host is no longer an exception, and the drop-in I added there on 2026-08-11 is gone.

## State before the change

Read through the SSH Manager at 12:14 AM Eastern, all in one command as root:

- `/etc/sudoers.d` held `00-rootpw`, `90-ai-agent`, `90-ansible`, `90-dkadi` and the packaged `README`, every one `0440 root:root`, and `visudo -c` passed on all of them.
- `passwd -S root` reported `P`, set 2026-08-15, so root's password was usable and the host was not in the condition that makes `Defaults rootpw` dangerous.
- `dkadi` is in `sudo`, so it holds a grant with or without the drop-in. `ai-agent` and `ansible` are in no administrative group, so each account's sudo came from its drop-in and nothing else.
- `sudo -l -U dkadi` listed both grants, `(ALL : ALL) ALL` and `(ALL : ALL) NOPASSWD: ALL`, with `rootpw` among its resolved Defaults. `sudo -l -U ai-agent` and `sudo -l -U ansible` each listed one `NOPASSWD` grant.
- `ai-agent` had used sudo on this host as recently as 2026-09-04, twice, both `docker exec` calls into the Pelican Panel container during the [service login password standardization](../../../Operations/Maintenance/Service%20Login%20Password%20Standardization%20-%202026-09-04.md). Nine key logins as `ai-agent` in the last thirty days; 134 sudo invocations by `dkadi` in the same window, which is the SSH Manager's normal traffic.
- On `green-server`, `pct status 123` reported `running` and the container is unprivileged, so `pct exec 123` from the node was the confirmed way back in if sudo broke.
- On `docker-blue`, the SSH Manager's root-owned secret file holds ten `SUDO_PASSWORD` keys, one of them `SSH_SERVER_GAME_01_SUDO_PASSWORD`. I read only the key names, never a value.

## What I changed

Through the SSH Manager, in this order, between 12:15 and 12:16 AM Eastern:

1. Opened a persistent `ssh_session_start` shell on `game_01` as `dkadi` and ran `sudo -i`, which the drop-in still allowed. `id -un` in that session returned `root`. That shell stayed open until the verification below had passed, so a bad result could be repaired from it without touching the node.
2. Removed `/etc/sudoers.d/90-dkadi` with `rm -f`, ran `visudo -c`, and read `sudo -l -U dkadi` back in the same root command. The parse passed on every remaining file and the policy showed the single `(ALL : ALL) ALL` grant with `rootpw` still among its Defaults.
3. Ran `ssh_execute_sudo` with `id -un` against `game_01` as a separate call. It returned `root` with exit code 0. This is the call that had to keep working: with the drop-in gone, sudo now prompts, and the SSH Manager answers from its configured entry.
4. Removed `/etc/sudoers.d/90-ai-agent` the same way, ran `visudo -c`, and read both policies back.
5. Closed the held root session.

Nothing was written to the host. Two files were deleted, each a one-line grant with no comment, and both are reproduced in full in the table above.

## Verification

Run at 12:16 AM Eastern, after both deletions, each through a fresh SSH Manager call rather than the held session.

| Check | Result |
| --- | --- |
| `/etc/sudoers.d` contents | `00-rootpw`, `90-ansible`, `README`, all `440 root:root` |
| `visudo -c` | `parsed OK` on `/etc/sudoers` and all three remaining files |
| `sudo -l -U dkadi` as root | `(ALL : ALL) ALL` only; `rootpw` in the resolved Defaults; no `NOPASSWD` |
| `sudo -l -U ai-agent` as root | `User ai-agent is not allowed to run sudo on game-01.` |
| `sudo -u ansible sudo -n true` as root | exit 0, so the unattended route is intact |
| `sudo -u ai-agent sudo -n true` as root | exit 1 |
| `sudo -n id -un` as `dkadi`, plain `ssh_execute` | exit 1, `sudo: a password is required` |
| `printf 'not-the-password\n' \| sudo -S -k -p '' id -un` as `dkadi` | exit 1, `Sorry, try again.` and `1 incorrect password attempt` |
| `ssh_execute_sudo` running `id -un` on `game_01` | `root`, exit 0 |
| `ssh_execute` running `id -un; hostname` on `game_01` | `dkadi`, `game-01`, exit 0 |

The wrong-password test is the negative proof the 2026-08-20 rootpw run had to record as `untestable` on this host, because `NOPASSWD` authenticated nothing. It is testable now and it fails the way it should. The journal agrees: the failed attempt logged `pam_unix(sudo:auth): auth could not identify password for [root]`, which is sudo checking root's password rather than `dkadi`'s, and the successful `id -un` from the SSH Manager logged one second later with no authentication complaint.

## The SSH Manager path, and what changed underneath it

The SSH Manager reaches `game-01` as `dkadi`. Its `ssh_execute_sudo` tool now builds the elevated call as `sudo -S -k -p '' <command>` with the configured password on stdin. On 2026-08-20 the concern was that on a `NOPASSWD` host sudo never reads that stdin, so the password was left on the command's own stdin, where anything that reads stdin could print it. That was true of `game-01` until this change and is not true now: sudo consumes the line to answer the prompt, and the command gets an empty stdin. The same exposure still applies on `docker-network`, `monitor-01` and `media-01` until their drop-ins come off.

No SSH Manager, gateway or Executor configuration changed. The `game_01` sudo entry that makes this work has been in the secret file on `docker-blue` since the [fleet reach completion](../../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Fleet%20Reach%20Completion%20-%202026-08-31.md) on 2026-08-31, and the [Executor record](../../../Platforms/Executor/README.md) already described this host as password-backed sudo. The description was ahead of the host, and the host now matches it.

## Left open

- `docker-network`, `monitor-01` and `media-01` still carry `dkadi` drop-ins. Each has a `SUDO_PASSWORD` entry in the SSH Manager and each was proven on the password path on 2026-08-20, so the same procedure applies. `media-01` names its file `dkadi` rather than `90-dkadi`.
- `ai-agent` on `game-01` can log in by key and cannot escalate. The 2026-09-04 Pelican work that used its sudo would go through `dkadi` and the SSH Manager next time. If unattended work on this host ever needs root, it belongs to `ansible`, not to a new `ai-agent` drop-in.
- The fleet-wide verification and the baseline standard rewrite in the root [TODO](../../../TODO.md) still stand.
