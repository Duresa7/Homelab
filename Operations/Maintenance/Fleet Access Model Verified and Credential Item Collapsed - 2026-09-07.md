# Fleet Access Model Verified and Credential Item Collapsed

**Created:** 2026-09-07  
**Last updated:** 2026-09-07

**Change date:** 2026-09-07  
**Status:** Complete. This closes the fleet access priority that opened on 2026-08-14  
**Scope:** A read-only verification of the sudo and SSH model on all eleven guests, the rewrite of the unpublished Linux Host Baseline Standard to match, and the deletion of two duplicate fields from the credential item every host account draws from. No host changed in this work; the host changes it verifies are in the two [NOPASSWD](NOPASSWD%20Drop-ins%20Removed%20on%20game-01%20-%202026-09-07.md) [records](NOPASSWD%20Drop-ins%20Removed%20on%20docker-network,%20monitor-01%20and%20media-01%20-%202026-09-07.md) from the same night

## Outcome

The model decided on 2026-08-15 is the live state on every guest, the standard now describes that state rather than the one it replaced, and the credential item holds each value once.

| Account | Sudo | How verified |
| --- | --- | --- |
| `dkadi` | `(ALL : ALL) ALL` from the `sudo` group, prompt takes root's password | `sudo -l -U dkadi` shows `rootpw` and no `NOPASSWD` on 11 of 11; a wrong password is refused with sudo checking root's password |
| `ai-agent` | none | `sudo -l -U ai-agent` reports not allowed on 11 of 11 |
| `ansible` | `NOPASSWD: ALL` | `sudo -n true` exits 0 on 11 of 11 |
| `root` | n/a | `passwd -S` reports `P` on 11 of 11; SSH login off on 11 of 11 since the [Coolify change](../../Platforms/Coolify/Documentation/Change%20Records/Non-Root%20Server%20Account%20and%20Root%20SSH%20Disabled%20-%202026-09-07.md) later the same night closed `app-01` |

## Verification

The per-host sweep was one `ssh_execute_sudo` per guest at 12:23 AM Eastern, run after the last drop-in came off `media-01`. Each host reported a count of `NOPASSWD` matches in `sudo -l -U` for `dkadi`, `ai-agent` and `ansible`, a count of `rootpw` in `dkadi`'s Defaults, and the contents of `/etc/sudoers.d`:

```text
host            dkadi  ai-agent  ansible  rootpw  drop-ins
alpha-prod-01   0      0         1        1       00-rootpw, 90-ansible
app-01          0      0         1        1       00-rootpw, 90-ansible
edge-01         0      0         1        1       00-rootpw, 90-ansible
security-01     0      0         1        1       00-rootpw, 90-ansible
splunk-siem     0      0         1        1       00-rootpw, 90-ansible
docker-blue     0      0         1        1       00-rootpw, 90-ansible
docker-network  0      0         1        1       00-rootpw, 90-ansible
monitor-01      0      0         1        1       00-rootpw, 90-ansible
media-01        0      0         1        1       00-rootpw, 90-ansible
game-01         0      0         1        1       00-rootpw, 90-ansible
ansible-01      0      0         1        1       00-rootpw, 90-ansible
```

The negative proof, a wrong password refused at `dkadi`'s prompt with the journal showing `auth could not identify password for [root]`, was run tonight on the four hosts that were `untestable` on 2026-08-20 and passed on all four. The other seven passed it on 2026-08-20 and nothing about their sudoers has changed since; the sweep confirms that. `ssh_execute_sudo` returned `root` on 11 of 11 and `ssh_execute` returned the login account on 11 of 11.

Key state is verified separately by `ssh-key-automation`, which now covers all seventeen Linux hosts and reads `present` for every identity on every host in its allowlist. That audit found `ansible-01`'s `dkadi` account had never received a key file, which is fixed and recorded in the [Ansible change record](../../Platforms/Ansible/Documentation/Change%20Records/SSH%20Identity%20Registration%20for%20green-server,%20monitor-01,%20game-01%20and%20ansible-01%20-%202026-09-07.md).

## The standard

The unpublished Linux Host Baseline Standard was rewritten from the verified state. What changed in it:

- **Root is not locked.** The old step 7, `passwd -l root`, is gone. Root carries a known password because `Defaults rootpw` makes it the sudo password, and a locked root plus that file locks every account out of sudo. The "no root on a VM" rule is now "no root **login**".
- **`ai-agent` has no sudo** on a three-account host. The 2026-08-15 wording said both human-facing accounts answer a prompt; the fleet never gave `ai-agent` a grant, agent work goes through the SSH Manager as `dkadi`, and I have written the standard to what is true. Granting it later is one group membership per host, because `rootpw` already governs the prompt.
- **A "What I accept" section** names the three things this model trades away: root's fleet password in plaintext in the SSH Manager's root-owned secret file on `docker-blue`, the 2026-08-14 transcript exposure of that value, redacted on 2026-08-20 and not rotated by decision on 2026-09-07, and my keys reaching root fleet-wide through the cluster key file and `ansible-01`.
- **The credential fields are named** with what each holds and which play or tool reads it, which the standard is the one file permitted to do.
- **The fleet table** above is in it, with the nodes, `docker-main` and `ubuntu-dev` listed as outside the model and why.
- The historical notes about the 2026-08-05 preflight and the 2026-08-14 check are gone; their outcomes are in the maintenance records and the root `TODO.md`.

The public [Linux Host Baseline](../../Guides/Linux-Host-Baseline.md) walkthrough was updated to match: its lock-root step is now a set-root-password-and-point-sudo-at-it step, and the expected root status is `P`.

## The credential item

The item held a `Sudo` section with two fields, both labelled `sudo password`, beside the fields the plays actually read. Before deleting anything I compared a SHA-256 of every field's value, computed inside a pipe and never printed, and got exactly the picture the 2026-08-20 records predicted: one `Sudo` field matched root's password byte for byte, the other matched the standard password byte for byte. Both duplicates are deleted, the section went with them, and every remaining field's hash is unchanged. The `console password` field also matches the standard password's value today; I left it, because it has a distinct meaning in the item and nothing reads either by that name.

Nothing that reads the item broke. `account-passwords.yml` and `ai-agent-account.yml` take their values from a staging file I build from the surviving fields, and the SSH Manager's entries were written from the surviving root field on 2026-08-20 and 2026-08-31.

## Closed by this work

- The fleet access priority in the root `TODO.md`, all sub-items.
- The superseded pre-2026-08-14 plan block below it, which was kept only until this rewrite landed.
