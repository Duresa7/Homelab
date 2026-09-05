# Sudo Pointed at the Root Password on Eleven Guests

**Created:** 2026-08-20  
**Last updated:** 2026-08-20

**Change date:** 2026-08-20  
**Status:** Complete and verified on all eleven guests  
**Scope:** `/etc/sudoers.d/00-rootpw` on the eleven Linux guests in the host access model. The five Proxmox nodes, `ubuntu-dev`, `docker-main` and `supabase-01` are outside the model and were not touched. No account password, no sshd setting and no existing sudoers file was changed

## Outcome

A sudo prompt on the eleven guests now asks for root's password rather than the invoking user's. That is what I wanted on 2026-08-15: one password to log in as `dkadi`, a different one at a sudo prompt. Stock sudo cannot do it: sudo authenticates the invoking user's own password, so on an unmodified host the two values are necessarily the same. `Defaults rootpw` is the only mechanism that separates them, and it works by pointing every prompt at **root's** password.

| Action | Password now typed |
| --- | --- |
| Log in as `dkadi` | the standard login password |
| Answer a sudo prompt as `dkadi` | root's password |

The work is a new play, `playbooks/sudoers-rootpw.yml`, in the [host-access-baseline](../../Platforms/Ansible/Source/host-access-baseline/README.md) Ansible project. It writes one file per host, four lines of comment and one line of policy, `0440 root:root`, moved into place only after `visudo -cf` accepts it at a temporary path.

`ansible` keeps its `NOPASSWD` grant on all eleven and was rechecked at the end of every host. It is the route that repairs a bad sudoers file, and a run that disturbed it would have failed rather than finished quietly.

## State before the change

Read through Ansible immediately before the run, on all eleven:

- `passwd -S root` reported `P` on every host, so no host was in the condition that makes this change dangerous.
- `visudo -c` passed on every host.
- **No `rootpw`, `targetpw` or `runaspw` existed anywhere on the fleet**, not in `/etc/sudoers` and not in any drop-in. This change introduces the setting rather than adjusting it.
- `/etc/sudoers.d/00-rootpw` did not exist on any host.

Who could reach root through sudo, and how:

| Hosts | `dkadi` | `ai-agent` | `ansible` |
| --- | --- | --- | --- |
| `edge-01`, `app-01`, `alpha-prod-01`, `ansible-01`, `splunk-siem`, `docker-blue`, `security-01` | authenticates | **not permitted** | `NOPASSWD` |
| `media-01`, `docker-network`, `monitor-01` | `NOPASSWD` | **not permitted** | `NOPASSWD` |
| `game-01` | `NOPASSWD` | `NOPASSWD` | `NOPASSWD` |

Two things in that table are worth stating plainly.

**`ai-agent` cannot use sudo at all on ten of the eleven.** The account exists everywhere and is in no administrative group anywhere, and only `game-01` carries a drop-in for it. So the row of the 2026-08-15 model that says `ai-agent` answers a sudo prompt with root's password describes an account that has nothing to answer a prompt about on ten hosts. Nothing here changed that, and nothing here should have. It is a real gap between the written model and the fleet, and it belongs to the verification step rather than to this one.

**The `dkadi` drop-in filenames are not consistent.** `media-01` calls it `/etc/sudoers.d/dkadi` where the other three use `90-dkadi`. A sweep that looks for the filename reports `media-01` as compliant when it is not, so the play detects the privilege by testing it instead.

## What I changed

One play, run from `ansible-01`, one host at a time, aborting the whole run on the first failure. Per host, in this order: parse the existing sudoers, confirm root reports a usable password, **prove root's password actually authenticates**, write the file, parse again, then prove what the prompt now accepts and refuses.

The proof before the write is the point of the whole design. A status letter from `passwd -S` only says a hash is present; it does not say the hash is the value I hold. Writing `Defaults rootpw` to a host where those differ removes sudo from every account on it at once, and the way back is the Proxmox console. So the play authenticates as root through `su` from the unprivileged `ansible` account before it writes anything, and a host that cannot prove it stops the run.

The file carries a four-line comment above the policy line. A bare `Defaults rootpw` on its own is one unexplained line, and deleting it silently returns every sudo prompt on the host to the login password with nothing left to show that anything ever changed. The ticket specified the policy line only; the comment is mine, and it changes no behaviour.

Before touching a host I confirmed the out-of-band route to root on it, because that is the recovery path if this goes wrong:

| Route | Hosts |
| --- | --- |
| `pct exec` from the node | `ansible-01`, `monitor-01`, `docker-network`, `docker-blue`, `media-01`, `game-01` |
| `qm guest exec` from the node | `app-01`, `edge-01`, `security-01`, `alpha-prod-01` |
| **Proxmox console only** | `splunk-siem`, where `guest-exec` is disabled on VM 109 |

`splunk-siem` went last for that reason.

## The bug the first host caught

I ran the play against `docker-blue` alone before the rest. The file was written, `visudo -c` passed, root's password was accepted at a `dkadi` sudo prompt and the login password was refused. Then the last verification failed:

```text
fatal: [docker-blue]: FAILED! => {"assertion": "dkadi_sudo_list.rc == 0",
"evaluated_to": false, "msg": "docker-blue: sudo -l no longer reports a grant for dkadi."}
```

`sudo -l` authenticates too. Once `rootpw` is in force, a password-gated account running `sudo -l` is prompted before sudo will tell it anything, so the command I had written to confirm the grant could no longer run unattended. The change was correct; the check was written for the world as it existed before the change.

Feeding the password into `sudo -l` was the obvious repair and the wrong one: it makes a routine read depend on a credential. The play now reads the policy as root with `sudo -l -U dkadi`, which needs no authentication and reports the same thing:

```text
Matching Defaults entries for dkadi on docker-blue:
    env_reset, mail_badpass, secure_path=..., use_pty, rootpw

User dkadi may run the following commands on docker-blue:
    (ALL : ALL) ALL
```

That output is a better check than the one it replaced. It is sudo reporting the Defaults it actually resolved for that user on that host, so `rootpw` appearing there proves the setting is in force, where a file that exists and parses only proves a file that exists and parses. The play now asserts on it.

This is the argument for a single-host trial. The fault was in the verification rather than the change, so an eleven-host run would have applied the policy correctly everywhere and failed on the first host anyway.

**Practical consequence worth carrying forward:** `sudo -l` is no longer a way to find out where you stand on these hosts without a password. Use `sudo -l -U <user>` as root.

## Verification

Every claim below was read back after the run. The play's own assertions are listed first, then an independent pass that did not go through the play.

**The play's per-host result lines.** `failed=0` across all eleven:

```text
docker-blue:    root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
media-01:       root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=untestable
docker-network: root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=untestable
monitor-01:     root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=untestable
game-01:        root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=untestable
edge-01:        root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
app-01:         root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
alpha-prod-01:  root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
security-01:    root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
ansible-01:     root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
splunk-siem:    root=P root_auth=ok visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok
```

**`untestable` is honest rather than passing.** On the four hosts where `dkadi` still holds a `NOPASSWD` drop-in, sudo authenticates nothing, so the login password would be "accepted" there only in the sense that it was never read. The play detects the grant by testing it and reports the negative proof as untestable rather than recording a pass it did not earn. Those four become testable when ticket 17 removes the drop-ins.

**Both directions proved on the seven gated hosts.** Root's password gets `dkadi` to root through sudo; the login password does not. The password reaches sudo on stdin through `sudo -S`, so it never enters a command string, an argument list or a shell history, and pipelining means no file carrying it is written to the host either.

**An independent sweep afterwards,** not part of the play, on all eleven:

| Check | Result |
| --- | --- |
| `/etc/sudoers.d/00-rootpw` mode and owner | `440 root:root` on 11/11 |
| `Defaults rootpw` present exactly once | 11/11 |
| `visudo -c` | passes on 11/11 |
| `rootpw` among the Defaults sudo resolves for `dkadi` | 11/11 |
| `(ALL : ALL) ALL` grant still held by `dkadi` | 11/11 |
| `sudo -n true` as `ansible` | exits `0` on 11/11 |

**A second run reports no changes.** `docker-blue` was run again in full: `ok=19 changed=0`, every assertion passing. A `--check --diff` pass across all eleven afterwards reports `changed=0` on every host, so the file on disk already matches what the play would write.

**Privileged tooling behaves exactly as ticket 16 predicted.** `ssh_execute_sudo` through the SSH Manager still reaches root on `media-01`, where `dkadi` is `NOPASSWD`, and on `docker-blue` returns:

```text
sudo: a terminal is required to read the password; either use the -S option
      to read from standard input or configure an askpass helper
sudo: a password is required
```

That is the same failure `app-01` gave on 2026-08-15, before this change existed. This work did not create that gap and did not widen it: the SSH Manager has never had a password configured for any server, so it has always failed wherever `dkadi` had to authenticate. Ticket 16 closes it, and it has to close before ticket 17 removes the four remaining drop-ins, or privileged tooling loses every path at once.

## How the credentials were handled

Neither value entered a command string, an inventory, a playbook, a log or a repository file. Both were read out of the credential item into a JSON file written with mode `0600` in `tmpfs`, so the local copy never reached a disk. It moved to `ansible-01` over SFTP into a mode-`0700` directory, was confirmed mode `0600` there, and was consumed with `-e @file`. Every task that touches a password carries `no_log: true`.

Before the run I asserted, without reading or printing either value, that both came back non-empty and that they are **distinct from each other**. That assertion is load-bearing rather than decorative: if the two fields held the same value, the negative proof would pass for the wrong reason and I would have recorded a separation that does not exist. I also confirmed that the durable field and the duplicate it is scheduled to replace still hold the same value, which is what the last step of this effort relies on when it deletes the duplicate.

Both copies of the staging file are gone, removed with `shred -u -z`, and both staging directories are gone. Neither host keeps a credential from this work. Which fields these are stays in the unpublished Linux Host Baseline Standard, the one file permitted to describe where a host account's credentials come from.

## What this unblocks, and the warning that goes with it

Ticket 16 is next and is now the blocking step: the SSH Manager needs root's password in its `.env` so privileged tooling works on the seven gated hosts. Ticket 17 removes the four remaining `dkadi` drop-ins and the `ai-agent` one on `game-01`, and must not run until 16 is proven.

**Any guest that joins the model later arrives with root locked.** Anything cloned from `debian13-template` or `ubuntu-cloud-template` is in exactly the state that makes this file dangerous. The order is not optional: run `account-passwords.yml` against the new host first, confirm it reports `root=P` and `root_auth=ok`, and only then run `sudo-rootpw`. The play enforces this itself and will refuse the host, but the sequence is worth knowing before it refuses.

## Left open

**`ai-agent` still has no sudo grant on ten of the eleven hosts.** The account is in no administrative group and carries a drop-in only on `game-01`. Under the written model it should answer a sudo prompt with root's password like `dkadi` does; today it has nothing to answer. Deciding whether the model or the fleet is wrong belongs to ticket 07.

**The four `NOPASSWD` drop-ins are still in place** on `media-01`, `docker-network`, `monitor-01` and `game-01`, plus the `ai-agent` one on `game-01`. They are the deliberate safety net until ticket 16 proves privileged access still works, and they are the reason the negative proof reports `untestable` on those hosts.

**`splunk-siem` has no agent-based recovery route.** `guest-exec` is disabled on VM 109, so the Proxmox console is the only way in if sudo ever breaks there. That is not a consequence of this change, but it came up while planning it and is worth fixing or accepting deliberately.
