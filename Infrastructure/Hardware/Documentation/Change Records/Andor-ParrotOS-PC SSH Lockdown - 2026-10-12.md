# Andor-ParrotOS-PC SSH Lockdown

**Created:** 2026-10-12  
**Last updated:** 2026-10-12

**Implementation date:** 2026-10-12  
**Status:** Complete  
**Affected systems:** [Andor-ParrotOS-PC](../../Workstations/Andor-ParrotOS-PC.md): `sshd` and `dkadi`'s `authorized_keys`

On 2026-10-12 I made SSH into Andor-ParrotOS-PC key-only. I installed my standard keys for `dkadi` and applied the `sshd` settings from my Linux host baseline. Root SSH is off, password and keyboard-interactive logins are refused, and the SSH Manager still connects and reaches root.

## Starting state

- `sshd -T` read `permitrootlogin prohibit-password`, `pubkeyauthentication yes`, `passwordauthentication yes`, `kbdinteractiveauthentication no`. `/etc/ssh/sshd_config.d/` was empty, and the main `sshd_config` sets only `KbdInteractiveAuthentication no` of these four.
- `ssh.service` is enabled and `ssh.socket` is disabled, so the daemon owns port 22 itself.
- `dkadi`'s `authorized_keys` held one key, `ai-agent@ubuntu-dev`, which is the SSH Manager's key.
- The SSH Manager entry `andor_parrot_os_pc` already authenticates with a key (`/keys/id_ed25519`) and has no login password, only the sudo password. It needed no change.

## What changed

1. **Standard keys.** The standard set is the one in `dkadi`'s `authorized_keys` on `docker-blue`: `mac-air3-dkadi`, `jedi-pc`, `ai-agent@ubuntu-dev`, `parrot-os-mac` and `andor-parrotos-pc`. I copied the three missing human keys from that file by comment, matching exactly one line per comment, and staged them on the PC. Before appending, I checked their fingerprints against the `ssh-key-automation` identities on `ansible-01`. The desktop's own `andor-parrotos-pc` key is not needed on itself. The file is now `0600 dkadi:dkadi`, 381 bytes, four keys:

   | Comment | Fingerprint |
   |---|---|
   | `ai-agent@ubuntu-dev` | `SHA256:2L4jdmX39LDiG3Zd+m9SX1qLlm0oVt5lOO8IqDkfDx4` |
   | `mac-air3-dkadi` | `SHA256:QyNF8ipQ5F/1KV69opH2QHuVVclpfNnZFGhDYZL38rM` |
   | `jedi-pc` | `SHA256:pcjlugUJER60YblfoAOfzZYKHJ1pHVTeqGm7Vwquj/4` |
   | `parrot-os-mac` | `SHA256:BxT8jxsgZU9Kox38KItPkW8ZjfuaZ9mtr7079zCue/E` |

2. **`sshd`.** I wrote `/etc/ssh/sshd_config.d/99-hardening.conf`, `0644 root:root`, 102 bytes:

   ```text
   PermitRootLogin no
   PubkeyAuthentication yes
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   ```

   `sshd -t` passed. I restarted `ssh.service` at 1:20 PM Eastern, and it came back `active`.

I did not register the PC in `ssh-key-automation`. That inventory connects to guests as the `ansible` account, which this desktop does not have. Parrot OS-Mac and Jedi PC are not in it either. The keys here are maintained by hand.

## Verification

- `sshd -T` after the restart: `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`.
- From `ubuntu-dev`, a password-only attempt as `dkadi` returned `Permission denied (publickey).` A key attempt as `root` returned the same.
- From `ubuntu-dev`, a key-only login as `dkadi` returned `parrot as dkadi`.
- Through the SSH Manager, in new sessions after the restart: `ssh_execute` returned `parrot as dkadi`, and `ssh_execute_sudo` returned `root`.

## Open

- `sudo` on this desktop still checks `dkadi`'s own password. The guests' `Defaults rootpw` model is not applied here.
- `X11Forwarding yes` remains from Parrot's default `sshd_config`. The baseline does not set it.

## Rollback

Delete `/etc/ssh/sshd_config.d/99-hardening.conf` and restart `ssh.service`. To remove the keys, delete the `mac-air3-dkadi`, `jedi-pc` and `parrot-os-mac` lines from `/home/dkadi/.ssh/authorized_keys`. Keep the `ai-agent@ubuntu-dev` line, because the SSH Manager depends on it. A local console login does not go through `sshd`, so it still works if a key is lost.
