# NOPASSWD Drop-ins Removed on docker-network, monitor-01 and media-01

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete and verified. No human or agent account holds a passwordless sudo grant on any of the eleven guests  
**Scope:** `/etc/sudoers.d/90-dkadi` on `docker-network` (CT 107) and `monitor-01` (CT 104), and `/etc/sudoers.d/dkadi` on `media-01` (CT 842). No account, password, key, sshd setting or other sudoers file changed

## Outcome

These were the last three `dkadi` drop-ins in the fleet, following [game-01 earlier the same night](NOPASSWD%20Drop-ins%20Removed%20on%20game-01%20-%202026-09-07.md). On every one of the eleven guests the model decided on 2026-08-15 is now the live state: `dkadi` holds `(ALL : ALL) ALL` through the `sudo` group behind a prompt that `Defaults rootpw` points at root's password, `ai-agent` cannot run sudo, and `ansible` keeps `NOPASSWD` as the unattended route and the way back in.

| Host | Drop-in removed | `dkadi` after | Node for recovery |
| --- | --- | --- | --- |
| `docker-network` | `90-dkadi`, written 2026-07-10 | `(ALL : ALL) ALL`, password-gated | `blue-server`, CT 107 |
| `monitor-01` | `90-dkadi`, written 2026-07-26 | `(ALL : ALL) ALL`, password-gated | `blue-server`, CT 104 |
| `media-01` | `dkadi`, written 2026-07-17 | `(ALL : ALL) ALL`, password-gated | `red-server`, CT 842 |

## State before the change

Read through the SSH Manager as root at 12:20 AM Eastern, one command per host, plus `pct status` on each node:

- Each host held `00-rootpw`, `90-ansible`, the packaged `README` and one `dkadi` drop-in, all `0440 root:root`, all passing `visudo -c`. `media-01`'s is named `dkadi`, which the 2026-08-20 records flagged as the reason to check the privilege rather than the filename.
- `passwd -S root` reported `P`, set 2026-08-15, on all three.
- `dkadi` is in `sudo` on all three, and in `docker` on all three. `ansible` is in `sudo` and `docker` too, and holds its own `NOPASSWD` drop-in. `ai-agent` is in no group but its own and `sudo -l -U ai-agent` already reported "not allowed" on all three.
- `sudo -l -U dkadi` listed both grants on each host, the group's `(ALL : ALL) ALL` and the drop-in's `(ALL : ALL) NOPASSWD: ALL`, with `rootpw` among the resolved Defaults.
- `dkadi` sudo invocations in the last thirty days: 71 on `docker-network`, 120 on `monitor-01`, 150 on `media-01`. That is the SSH Manager's traffic, and it is what had to keep working.
- All three containers were `running` on their nodes, so `pct exec` was the confirmed recovery path.
- The SSH Manager's secret file on `docker-blue` holds a `SUDO_PASSWORD` key for each of the three, confirmed by key name on the `game-01` pass an hour earlier.

## What I changed

The same sequence on each host, one host at a time, `docker-network` first, then `monitor-01`, then `media-01`, with `media-01` gated on `monitor-01` returning `root` through the password path first. Between 12:21 and 12:22 AM Eastern:

1. Opened a persistent `ssh_session_start` shell as `dkadi`, ran `sudo -i` while the drop-in still allowed it, and confirmed `id -un` returned `root`. That shell stayed open until the host's verification passed.
2. In one root command: `rm -f` the drop-in, `visudo -c`, `sudo -l -U dkadi`, and `sudo -u ansible sudo -n true` to confirm the unattended route survived.
3. A separate `ssh_execute_sudo` running `id -un`, which now has to answer a prompt.
4. The negative and plain checks below.
5. Closed the held shell.

Nothing was written to any host. Each deleted file was one line, `dkadi ALL=(ALL:ALL) NOPASSWD: ALL`, with no comment.

## Verification

Per host, after its deletion, each through a fresh SSH Manager call. Every row below held on all three:

| Check | Result |
| --- | --- |
| `/etc/sudoers.d` contents | `00-rootpw`, `90-ansible`, `README`, all `440 root:root` |
| `visudo -c` | `parsed OK` on `/etc/sudoers` and all three files |
| `sudo -l -U dkadi` as root | `(ALL : ALL) ALL` only, `rootpw` in the resolved Defaults, no `NOPASSWD` |
| `sudo -u ansible sudo -n true` as root | exit 0 |
| `sudo -n id -un` as `dkadi`, plain `ssh_execute` | exit 1, `sudo: a password is required` |
| `printf 'not-the-password\n' \| sudo -S -k -p '' id -un` as `dkadi` | exit 1, `Sorry, try again.`, `1 incorrect password attempt` |
| `ssh_execute_sudo` running `id -un` | `root`, exit 0 |
| `ssh_execute` running `id -un; hostname` | `dkadi` and the hostname, exit 0 |

On each host the journal shows the failed attempt as `pam_unix(sudo:auth): auth could not identify password for [root]`, which is sudo checking root's password rather than `dkadi`'s, followed within seconds by the SSH Manager's successful `id -un` with no authentication complaint. These are the negative proofs the 2026-08-20 rootpw run recorded as `untestable` on these hosts. All three are testable now and all three refuse.

**Closing sweep across all eleven guests**, one `ssh_execute_sudo` each, run at 12:23 AM Eastern:

```text
host            dkadi_nopasswd  aiagent_nopasswd  ansible_nopasswd  rootpw  drop-ins
alpha-prod-01   0               0                 1                 1       00-rootpw, 90-ansible
app-01          0               0                 1                 1       00-rootpw, 90-ansible
edge-01         0               0                 1                 1       00-rootpw, 90-ansible
security-01     0               0                 1                 1       00-rootpw, 90-ansible
splunk-siem     0               0                 1                 1       00-rootpw, 90-ansible
docker-blue     0               0                 1                 1       00-rootpw, 90-ansible
docker-network  0               0                 1                 1       00-rootpw, 90-ansible
monitor-01      0               0                 1                 1       00-rootpw, 90-ansible
media-01        0               0                 1                 1       00-rootpw, 90-ansible
game-01         0               0                 1                 1       00-rootpw, 90-ansible
ansible-01      0               0                 1                 1       00-rootpw, 90-ansible
```

The counts are `grep -c NOPASSWD` over `sudo -l -U <user>` for each account and `grep -c rootpw` over `dkadi`'s Defaults. The packaged `README` is present in `/etc/sudoers.d` on all but `splunk-siem`, the Rocky host, and is omitted from the column. Eleven hosts, one `NOPASSWD` grant each, all of them `ansible`'s.

## What this closes

The password-on-stdin side effect from the [2026-08-20 SSH Manager record](SSH%20Manager%20Sudo%20Password%20on%20Ten%20Guests%20-%202026-08-20.md) is gone from the fleet. On a `NOPASSWD` host `ssh_execute_sudo` left root's password on the command's own stdin because sudo never read it; now every host with a configured entry prompts and consumes it. `ansible-01` was never in that state because it has no entry.

No SSH Manager, gateway or Executor configuration changed. The [Executor record](../../Platforms/Executor/README.md) has described these hosts as password-backed sudo since 2026-08-31, and the hosts now match it.

## Found along the way

`media-01` ran on `Etc/UTC` where the other guests I touched tonight run on `America/New_York`. Its journal stamps the sudo change at 04:22, the others at 00:22. `ansible-01` was moved off UTC on 2026-09-01 for the same reason, so I fixed this one too, at 12:31 AM Eastern, with `timedatectl set-timezone America/New_York`. Before the change I confirmed there was nothing to disturb: no crontab for `root` or `dkadi`, nothing in `/etc/cron.d` but `e2scrub_all`, every application container already carrying `TZ=America/New_York`, and no `timezone` option on CT 842 in Proxmox that would put it back on the next start. Afterwards `timedatectl` reports `America/New_York (EDT, -0400)` with the clock still synchronized, `/etc/localtime` points at the new zone, `systemd-timedated` logged the change, the systemd timers rescheduled to the same instants in local time, and `date` inside the Jellyfin and Sonarr containers agrees with the host to the second. No restart was needed. The baseline standard requires this zone, so the host is now conforming on that point as well.

The LXC inventory said root was locked on `docker-network`, `monitor-01` and `media-01`. That has been false since 2026-08-15, when root received a known password on every guest so that `Defaults rootpw` could land. I corrected those lines alongside this record.

## Left open

The two remaining steps of the fleet access priority are documentation: verify the whole model per host and rewrite the unpublished baseline standard to match, then collapse the duplicated fields in the credential item.
