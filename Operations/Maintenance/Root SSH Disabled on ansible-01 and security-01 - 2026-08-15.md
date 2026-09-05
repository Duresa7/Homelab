# Root SSH Disabled on ansible-01 and security-01

**Created:** 2026-08-15  
**Last updated:** 2026-08-15

**Change date:** 2026-08-15  
**Status:** Complete. Two deviations found on the way through are recorded below and left open  
**Scope:** `PermitRootLogin no` on `ansible-01` (LXC 100) and `security-01` (VM 200). `app-01` is excluded by decision and was verified untouched

## Outcome

Both hosts now report `permitrootlogin no` from `sshd -T`, and `ssh.service` is `active` on both. Root SSH is refused from my workstation with `Permission denied (publickey)`, while `ansible@ansible-01` and `dkadi@security-01` still open new sessions normally. Neither host had a single key in `/root/.ssh/authorized_keys` before the change, so the setting was granting nothing and closing it cost nothing.

The Linux Host Baseline Standard requires `PermitRootLogin no`. Three hosts ran `without-password`, which permits root to log in by key. Two of them are now closed. The third is `app-01`, and it stays open on purpose.

The change was not uneventful. `systemctl reload ssh` on `ansible-01` killed the daemon and put `ssh.service` into `failed`. The cause was not the one I expected, and the fix is a `restart` rather than a `reload`. That is written up below, because the same trap is waiting on every socket-activated host in the fleet.

## State before the change

| Host | `permitrootlogin` | Keys in `/root/.ssh/authorized_keys` | Where the setting lived |
| --- | --- | --- | --- |
| `ansible-01` | `without-password` | 0 | `PermitRootLogin prohibit-password` on line 33 of `/etc/ssh/sshd_config` |
| `security-01` | `without-password` | 0, and the file is 0 bytes | Nowhere. No drop-in or main-file directive, so sshd was applying its own default |
| `app-01` | `without-password` | 2 | Not inspected, out of scope |

`security-01` is the interesting one. Its `/etc/ssh/sshd_config.d/00-ansible-hardening.conf` sets three of the four hardened values and never mentions root, so the host was compliant by accident on everything except the one setting that matters here.

## What I changed

**`ansible-01`.** One line in the main file, because the host has an empty `/etc/ssh/sshd_config.d/` and keeps its directives in `/etc/ssh/sshd_config`:

```text
33c33
< PermitRootLogin prohibit-password
---
> PermitRootLogin no
```

**`security-01`.** Appended `PermitRootLogin no` to the existing `/etc/ssh/sshd_config.d/00-ansible-hardening.conf`, which is where the host already keeps its hardening, leaving:

```text
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
```

The `00-` prefix earns its place. `50-cloud-init.conf` on the same host sets `PasswordAuthentication yes`, and sshd takes the first value it obtains for a keyword, so the hardening file wins on every setting the two share. Putting the root directive anywhere later would have been a coin toss.

`sshd -t` exited `0` on both hosts before the service was touched. The `security-01` edit ran through a shell that restored the pre-change copy and re-tested if `sshd -t` had failed, so a bad file could not have survived to the restart. It did not fire.

I held a second session open on each host for the whole window and confirmed both were still alive afterwards.

## The reload that broke sshd on ansible-01

The ticket warned me to expect `Missing privilege separation directory: /run/sshd`, which is what an sshd reload did to `media-01` earlier the same day. I saw that string, assumed it was the same fault, and it was not.

```text
Aug 15 15:46:39 ansible-01 systemd[1]: Reloading ssh.service - OpenBSD Secure Shell server...
Aug 15 15:46:39 ansible-01 systemd[1]: Reloaded ssh.service - OpenBSD Secure Shell server.
Aug 15 15:46:39 ansible-01 sshd[134]: Received SIGHUP; restarting.
Aug 15 15:46:39 ansible-01 sshd[134]: fatal: Cannot bind any address.
Aug 15 15:46:39 ansible-01 systemd[1]: ssh.service: Main process exited, code=exited, status=255/EXCEPTION
Aug 15 15:46:39 ansible-01 systemd[1]: ssh.service: Failed with result 'exit-code'.
```

The fatal error is `Cannot bind any address`, at 11:46 AM Eastern. `ansible-01` runs `ssh.socket` with `ListenStream=22` and `Accept=no`, so systemd owns port 22 and hands the listening socket to `sshd -D` on start. On `SIGHUP` sshd re-executes itself, loses the passed file descriptor, tries to bind port 22 for itself, finds systemd already holding it, and exits.

The privilege separation message was a second-order symptom, not the cause. `ssh.service` declares `RuntimeDirectory=sshd`, so systemd deleted `/run/sshd` when the unit died. Every `sshd -T` I ran after that failed on the missing directory and told me nothing about why the daemon was gone.

`systemctl restart ssh` fixed it in one step, because systemd recreates the runtime directory before `ExecStart` and hands over the socket cleanly:

```text
is-active=active
socket=active
drwxr-xr-x 2 root root 40 Aug 15 15:47 /run/sshd
permitrootlogin no
128905 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
```

Connectivity never dropped. `ssh.socket` stayed `active` throughout, my held session survived, and a fresh connection opened while the service was still marked `failed`. The exposure was about one minute either way, and both guests sit on `grey-server`, so `pct exec 100` and `qm terminal 200` were the recovery path if it had gone further.

**The lesson, for the next host:** on a socket-activated sshd, use `systemctl restart ssh`, not `reload`. I used `restart` on `security-01` and it started cleanly with no failure at all:

```text
Aug 15 15:47:59 wazuh-01 systemd[1]: Stopped ssh.service - OpenBSD Secure Shell server.
Aug 15 15:47:59 wazuh-01 systemd[1]: Starting ssh.service - OpenBSD Secure Shell server...
Aug 15 15:47:59 wazuh-01 sshd[375811]: Server listening on 0.0.0.0 port 22.
Aug 15 15:47:59 wazuh-01 sshd[375811]: Server listening on :: port 22.
Aug 15 15:47:59 wazuh-01 systemd[1]: Started ssh.service - OpenBSD Secure Shell server.
```

## Verification

Effective configuration on both hosts, read back with `sshd -T` after the restart:

```text
permitrootlogin no
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
active
```

That is all four values from step 6 of the baseline standard, on both hosts, plus `systemctl is-active ssh`.

Login behaviour, tested from `ubuntu-dev`:

| Test | Result |
| --- | --- |
| `ssh root@192.168.40.36` | `root@192.168.40.36: Permission denied (publickey).` |
| `ssh root@192.168.72.2` | `root@192.168.72.2: Permission denied (publickey).` |
| `ssh ansible@192.168.40.36` | `NEW_SESSION_OK as ansible@ansible-01` |
| `ssh dkadi@192.168.72.2` | `NEW_SESSION_OK as dkadi@wazuh-01` |

The held session on each host answered after the restart, `ansible-01` reporting `up 2 weeks, 30 minutes`, so nothing was dropped.

`app-01` was read through Ansible before and after and is unchanged: `permitrootlogin without-password`, `keycount=2`, `ssh=active`.

## app-01 stays as it is

Coolify 4.3.2 manages the host it runs on over root SSH. `app-01` logged 735 root logins in the 30 days to 2026-08-15 against 70 for `dkadi`, and the `coolify` key in root's `authorized_keys` is the public half of Coolify's own private key on that host. Turning root SSH off there stops the platform. Moving Coolify onto a non-root user is already an item in the root [TODO.md](../../TODO.md), and this change deliberately does not touch it.

## Backups

The pre-change copy of each edited file is in the repository's `Backups/` folder, and both are free of withheld values, so neither needed redaction:

- `Backups/ansible-01-sshd_config-2026-08-15`
- `Backups/security-01-sshd-00-ansible-hardening-2026-08-15.conf`

I also made a rollback copy on each host for the duration of the edit, at `/etc/ssh/sshd_config.pre-rootlogin-2026-08-15` on `ansible-01` and `/root/00-ansible-hardening.conf.pre-rootlogin-2026-08-15` on `security-01`. Both were deleted once the change was verified, and `ls` confirms neither path exists. The hosts keep nothing.

## Left open

One deviation turned up outside this change and was not fixed here.

**Both hosts run `Etc/UTC`.** Step 8 of the baseline standard requires `America/New_York` so timestamps compare across hosts without conversion. `timedatectl` reports `Time zone: Etc/UTC (UTC, +0000)` on `ansible-01` and on `security-01`. Every journal timestamp quoted in this record is UTC because of it.

It didn't affect the change and was recorded in the Wazuh and Ansible platform TODO lists.
