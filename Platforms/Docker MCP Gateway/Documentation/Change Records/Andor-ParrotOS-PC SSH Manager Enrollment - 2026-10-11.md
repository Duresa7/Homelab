# Andor-ParrotOS-PC SSH Manager Enrollment

**Created:** 2026-10-11  
**Last updated:** 2026-10-12

**Implementation date:** 2026-10-11  
**Status:** Complete  
**Affected systems:** `mcp-ssh-manager` on `docker-blue`, Dockhand's imported definition on `docker-main`, and the `dkadi` account on Andor-ParrotOS-PC

On 2026-10-11 I added Andor-ParrotOS-PC to SSH Manager as `andor_parrot_os_pc`. The server list went from 24 entries to 25. The desktop runs Parrot on ObiPC's hardware for now, and I treat it as a separate machine from ObiPC: [Andor-ParrotOS-PC](../../../../Infrastructure/Hardware/Workstations/Andor-ParrotOS-PC.md). Its admin access and own SSH key are in [Andor-ParrotOS-PC Admin Access](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Andor-ParrotOS-PC%20Admin%20Access%20-%202026-10-11.md).

## The device

| Item | Value |
|---|---|
| OS | Parrot Security 7.4 (echo) |
| Hostname, account | `parrot`, `dkadi` (in `sudo`, password required) |
| Network | Wired on `eno1`, `192.168.50.102/24`, Secure VLAN 50 |
| SSH | `ssh` service enabled, password and key authentication both accepted. Key-only since 2026-10-12: [Andor-ParrotOS-PC SSH Lockdown](../../../../Infrastructure/Hardware/Documentation/Change%20Records/Andor-ParrotOS-PC%20SSH%20Lockdown%20-%202026-10-12.md) |
| SSH Manager entry | `andor_parrot_os_pc`, key authentication, password-backed sudo |

The `dkadi` password is the standard one, kept in my password manager. I used it once, from `ubuntu-dev`, to install the key. An askpass helper read it from the password manager's command-line tool, so it never appeared in a command line or in any output.

## What changed

1. **Key on the PC.** `dkadi` had no `~/.ssh/authorized_keys`. I created it with SSH Manager's public key (the ED25519 key at `/keys/id_ed25519` in the container) as its only line, with `~/.ssh` at `700` and the file at `600`. A key-only login (`BatchMode`, `IdentitiesOnly`) from `ubuntu-dev` then returned `parrot`.
2. **Server definition.** I added seven non-secret settings after the `win11_dev` block in the live `/opt/docker/mcp-gateway/docker-compose.yml`: host `192.168.50.102`, user `dkadi`, mode `unrestricted`, port `22`, key path `/keys/id_ed25519`, platform `linux`, and a description. `docker compose config -q` passed. Before the edit, the live file and Dockhand's copy at `/opt/docker/dockhand/stacks/imported/docker_blue/docker-mcp-gateway/compose.yaml` both hashed `fae49383…`. I ran the same edit on both, and both now hash `367d9049…` (19,385 bytes before, 19,879 after, still `0600 root`).
3. **Host keys.** I scanned all three host key types (RSA, ECDSA, ED25519) from `docker-blue` and appended them to `/state/ssh/known_hosts` in the container. The fingerprints match an independent scan from `ubuntu-dev`. The file now holds three lines for `192.168.50.102`.
4. **Recreate.** I recreated only `ssh-manager`, with pulls and builds disabled, detached so the recreate would not cut off the SSH session running it. The log shows `Recreated` and `Started`.

No firewall policy changed: `nc -z` from inside the container reached `192.168.50.102:22` before I made any change.

## Sudo password

The `dkadi` sudo password is the same standard password, so I added it later the same evening. Before configuring it, I piped it from the password manager's command-line tool into `sudo -S -k` over a key login from `ubuntu-dev`. `id -un` returned `root`.

The other ten sudo passwords are written into the live Compose file itself, with a reference copy in `ssh-manager.env`. I followed the same layout:

1. On `ubuntu-dev`, a short script read the password from the password manager's command-line tool on stdin. It wrote two `0600` files: one with the JSON-quoted Compose line, one with the env line. It printed only whether the value contained characters that need quoting, and it contained none. I copied the files with `scp` to `/tmp` on `docker-blue` and `docker-main`, set them to `0600`, and shredded the local copies.
2. I inserted the line `SSH_SERVER_ANDOR_PARROT_OS_PC_SUDO_PASSWORD` after the entry's `USER` line in both Compose files with `sed ... r <file>`. On `docker-blue` I also appended the env line to `ssh-manager.env`, which now holds 11 sudo passwords (1,161 bytes, `0600 root`). Both Compose files hash `8ca5a233…` (19,953 bytes, `0600 root`), and `docker compose config -q` passed. I shredded the staging files on both hosts.
3. I recreated `ssh-manager` again with the same detached command. It was healthy from 8:58 PM Eastern.

`ssh_execute_sudo` on `andor_parrot_os_pc` then returned `root` and `parrot`. SSH Manager now reaches root on this host. I read the inserted line back only as its key name, with the value redacted.

## Verification

- `ssh_list_servers` returns 25 entries, including `andor_parrot_os_pc`.
- `ssh_execute` on `andor_parrot_os_pc` returned `parrot`, `dkadi`, `Parrot Security 7.4 (echo)` and exit code 0.
- `mcp-ssh-manager` reports `healthy`, started at 8:43 PM Eastern.
- I deleted the staging script and recreate log from `/tmp` on `docker-blue` and `docker-main`, and the askpass helper and its temporary known-hosts file from `ubuntu-dev`. No copy of the Compose file was kept. The edit is seven lines and a comma, and the rollback below reverses it.

During the same check, `parrot_os_mac` returned `EHOSTUNREACH` for `192.168.10.176:22`. That laptop is off the network. Nothing in this change touches it.

## Open

- The `obipc` entry stays, pointing at `192.168.60.102`. It does not answer while Parrot is on the hardware, and it is for when ObiPC's Windows comes back.

## Rollback

- Delete the eight `SSH_SERVER_ANDOR_PARROT_OS_PC_*` lines from both Compose files and the sudo line from `ssh-manager.env`, along with the comma added after `SSH_SERVER_WIN11_DEV_DESCRIPTION`, then recreate `ssh-manager`.
- Remove the three `192.168.50.102` lines from `/state/ssh/known_hosts`.
- Remove the SSH Manager key line from `/home/dkadi/.ssh/authorized_keys` on the PC.
