# Non-Root Server Account and Root SSH Disabled

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete and verified. Coolify manages `app-01` as `coolify`, root holds no SSH key, and `PermitRootLogin no` is in force  
**Scope:** `app-01` host accounts, sudoers and sshd, plus the `user` column of Coolify's `localhost` server record. No Coolify container was restarted, no deployed application was touched, and no key was generated or replaced

## Outcome

Coolify 4.3.17 manages the host it runs on by connecting to it over SSH from its own container, and until tonight it did that as `root`. That was the reason `app-01` was the one guest left running `PermitRootLogin without-password`, and the reason it logged more root logins than any host in the fleet: 73 in the seven days before the change, every one from the container network with Coolify's `localhost` key. Coolify now connects as a dedicated `coolify` account with passwordless sudo, which is the shape the baseline already gives `ansible`, and root cannot log in over SSH at all.

| Item | Before | After |
| --- | --- | --- |
| Coolify `localhost` server user | `root` | `coolify` |
| Key Coolify presents | `localhost's key`, ED25519 `SHA256:sP/veKfc…` | the same key, unchanged |
| `/root/.ssh/authorized_keys` | that key, plus an uncommented `SHA256:rmcpwm…` from 2026-03-13 | file removed |
| `PermitRootLogin` | `prohibit-password` | `no` |
| `/data/coolify` owner | uid `9999`, no matching host account | `coolify`, uid `9999` |

## What Coolify requires

Coolify's [non-root user documentation](https://coolify.io/docs/knowledge-base/server/non-root-user) asks for an account with a key and `NOPASSWD: ALL` sudo, and says plainly that the account still has root-level access. It marks the feature experimental. The [newer documentation](https://next.coolify.io/docs/core/infrastructure/servers/non-root-user) adds the exact steps: `useradd --create-home --user-group --shell /bin/bash`, a `0700` `.ssh` directory with a `0600` `authorized_keys`, a `0440` sudoers drop-in, `su - <user> -c 'sudo -n whoami'` returning `root`, and `chown -R <user>:<user> /data/coolify`.

Two things in that recipe needed thought for the server Coolify itself runs on.

**The uid.** The Coolify container runs as `www-data`, uid `9999`, and everything under `/data/coolify` on the host is owned by uid `9999` with no host account behind it. The documented recursive `chown` would have handed those files to a different uid and broken the container's own writes. Creating `coolify` **as uid and gid 9999** makes the container's user and the SSH user the same identity, so the ownership was already right and the `chown` became unnecessary. I checked both ids were unused on the host before creating them.

**The key.** The documentation has you generate a new key in the dashboard. Coolify already held a key for this server, `localhost's key`, and its private half was already in the container's key store. Reusing it meant no dashboard step, no new key to validate, and nothing to remove from Coolify afterwards. The [GitHub issue](https://github.com/coollabsio/coolify/issues/4245) about the localhost server rejecting a non-root key on an old beta did not reproduce on 4.3.17; the connection was proven from inside the container before the server record changed.

## State before the change

Read through the SSH Manager as `dkadi` with sudo, between 1:58 and 2:04 AM Eastern:

- `sshd -T`: `permitrootlogin without-password`, `passwordauthentication no`, no `AllowUsers`. `ssh.socket` inactive, `ssh.service` active, so a restart hands over cleanly.
- `/root/.ssh/authorized_keys`: three lines, one blank. The ED25519 key commented `coolify`, fingerprint `SHA256:sP/veKfc…`, which is Coolify's `localhost's key`. And the uncommented ED25519 `SHA256:rmcpwm…` written 2026-03-13, not one of the four keys in Coolify's `private_keys` table.
- Root logins accepted in the last seven days: 73, all `SHA256:sP/veKfc…`, all from `10.0.1.5` or `10.0.1.6`, which is the Coolify Compose network. Nothing else logs in as root.
- Coolify's `servers` table: `localhost` at `host.docker.internal` as `root` with key `0`, and a second row `apps-02` at `192.168.80.11` as `root` with key `2`, `is_reachable false`, and the address does not answer a ping. That row is not touched here; see below.
- No account `coolify`, no uid or gid `9999` on the host. `dkadi` in `docker`; `ansible` with its `NOPASSWD` drop-in; `00-rootpw` in place.
- `/data/coolify` and every subdirectory `9999:root` or `9999:9999`, mode `700`.
- All six Coolify containers and cAdvisor `healthy`.

## What I changed

At 2:04 AM Eastern, in one root command with `set -e`:

1. `groupadd --gid 9999 coolify`, `useradd --uid 9999 --gid 9999 --create-home --shell /bin/bash coolify`, `passwd -l coolify`. A locked password: this is an unattended key-only account like `ansible`.
2. `usermod -aG docker coolify`, so Docker is reachable with or without the sudo prefix Coolify adds for non-root servers.
3. `/home/coolify/.ssh` at `0700`, and `authorized_keys` at `0600` holding one line, the `coolify`-commented key copied from root's file.
4. `/etc/sudoers.d/90-coolify` holding `coolify ALL=(ALL:ALL) NOPASSWD: ALL`, validated with `visudo -cf` at a temporary path and installed `0440 root:root`. `visudo -c` passed on the whole configuration afterwards.
5. `su - coolify -c 'sudo -n whoami'` returned `root`.

Then, from inside the Coolify container, using Coolify's own copy of the `localhost` key: `ssh coolify@host.docker.internal` returned `coolify`, `sudo -n docker ps` listed the containers, and `/data/coolify/applications` tested writable. That is the proof the server record could be switched.

At 2:07 AM Eastern: `update servers set "user"='coolify' where id=0 and "user"='root'`, through `psql` in the `coolify-db` container. Then I killed the container's `ssh` ControlMaster and removed its mux socket so the next Coolify command could not ride the connection it had already opened as root. Coolify's scheduled server check reconnected at 2:07:43 AM as `coolify`, and the host showed one `sshd-session: coolify@notty` and no root session.

At 2:10 AM Eastern: removed `/root/.ssh/authorized_keys`, changed line 33 of `/etc/ssh/sshd_config` from `PermitRootLogin prohibit-password` to `PermitRootLogin no`, `sshd -t`, `systemctl restart ssh`.

A first attempt at the `psql` update failed on shell quoting and changed nothing, which I confirmed by reading the row back before retrying with dollar-quoting. Two of the SSH Manager calls timed out on remote `sleep` waits that were longer than the gateway allows; each time I read the state back before continuing rather than assuming what had run.

## Verification

At 2:10 and 2:11 AM Eastern, after the sshd restart:

| Check | Result |
| --- | --- |
| `sshd -T` | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no` |
| `/root/.ssh/` | empty directory |
| Fresh SSH Manager connection as `dkadi` | `dkadi`, `app-01` |
| From the container, `ssh coolify@host.docker.internal` with Coolify's key | `coolify`, then `sudo -n docker ps -q \| wc -l` returned 7 |
| From the container, `ssh root@host.docker.internal` with the same key | `Permission denied (publickey)` |
| Live sshd sessions | one `coolify@notty`, one `dkadi@notty`, none for root |
| Coolify `servers` row `0` | `localhost`, `host.docker.internal`, `coolify`, key `0` |
| Containers | all six Coolify containers and cAdvisor still `Up` and `healthy`, none restarted |
| Coolify panel `/api/health` | HTTP 200 |
| `docker logs coolify` since the change | no error, exception or permission denied |

Coolify holds one multiplexed connection open and reuses it, so the journal shows one `Accepted publickey for coolify` at reconnection rather than a login per command. That is the same pattern the 73 root logins followed; they were reconnections, not commands.

## Found along the way

**`apps-02` is a stale server record.** Coolify still lists a second server at `192.168.80.11` as `root` with the `apps-01-key`, marked unreachable, and nothing at that address answers. No host by that name exists in the Galaxy inventory. It is a Coolify housekeeping decision, recorded in the root `TODO.md`, and until it is removed Coolify will keep failing a check against it.

**The `wp-01` key claim does not hold.** The root `TODO.md` said Coolify stored a private key commented `dkadi@wp-01`. Searching the `private_keys` table's key columns for `wp-01` returns nothing on 4.3.17. Whatever carried that comment is gone or was never a stored key, and the item is closed as not found.

**The orphaned root key is gone with the file.** `SHA256:rmcpwm…` was never identified. It is no longer authorised anywhere on `app-01`.

## What this closes

`app-01` was the last guest outside the "no root login" rule of the [Linux host baseline](../../../../Guides/Linux-Host-Baseline.md). All eleven guests now run `PermitRootLogin no`. The exception noted in the unpublished standard and in the [fleet verification record](../../../../Operations/Maintenance/Fleet%20Access%20Model%20Verified%20and%20Credential%20Item%20Collapsed%20-%202026-09-07.md) is removed.
