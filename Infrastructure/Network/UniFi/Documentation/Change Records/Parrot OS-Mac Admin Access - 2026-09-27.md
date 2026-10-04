# Parrot OS-Mac Admin Access

**Created:** 2026-09-27  
**Last updated:** 2026-10-03

**Implementation date:** 2026-09-27  
**Status:** Complete  
**Affected systems:** six UniFi firewall policies, the Galaxy Datacenter firewall, `ssh-key-automation` on `ansible-01`, 16 authorized-key stores, and the SSH key in the laptop's `dkadi` account

On 2026-09-27 I gave Parrot OS-Mac the same admin access as my MacBook Air M3 (`dkadi-mb-air3`, `192.168.10.27`), plus the UniFi console path Jedi PC has.

## The device

| Item | Value |
|---|---|
| Hardware | Apple MacBook Pro, `MacBookPro14,3` |
| OS | Parrot Security 7.3 (echo) |
| Hostname, account | `parrot`, `dkadi` (in `sudo`, password required) |
| Network | Trusted, VLAN 10, Wi-Fi on `The-Box` |
| MAC, address | Withheld (Broadcom Wi-Fi, OUI listed as Epigram), fixed IP `192.168.10.176` |
| SSH Manager entry | `parrot_os_mac` |

The fixed IP already existed. `Allow Trusted SSH replies to Admin Hosts` already listed `192.168.10.176`, so SSH Manager could already reach the laptop. The firewall inventory still called that policy `Allow Surface SSH replies to Automation`, with `192.168.10.211` as its only source and two destinations. The controller has the new name, the laptop as a second source, and `ansible-01` as a third destination. I have no record of that change, and I corrected the inventory row.

## What changed

### UniFi

I added the laptop to the same source lists that name the MacBook Air M3. For each policy I read it, updated only its source, and read it back. Action, index, protocol, destination, logging, schedule and the respond setting stayed the same.

| Policy | Source before | Source after |
|---|---|---|
| `Device Access --> Proxmox` | 5 MACs | 6 MACs |
| `Allow Devices to Personal-A` | 9 MACs | 10 MACs |
| `DMZ Allow List` | 3 MACs | 4 MACs |
| `Allow MacBook Air and Pixel to WAC HTTPS` | 2 MACs | 3 MACs |
| `Allow dkadi MacBook Air M3 to PeaNUT` | `192.168.10.27` | `192.168.10.27`, `192.168.10.176` |
| `Jedi PC --> Unifi Console SSH` | 1 MAC (Jedi PC) | 2 MACs |

The last one is Jedi PC's own grant to the Management network, where the switches and access point live. The MacBook does not have it. I added it because the request covered the network gear too. I kept both policy names as they were.

### Galaxy Datacenter firewall

I added `192.168.10.176 # Parrot OS-Mac` to `pve_admins` in `/etc/pve/firewall/cluster.fw` on `grey-server`. The diff was that one line, and the file went from 51 lines to 52. `pve-firewall compile` exited 0. All five nodes read the same file (`429f9b94…`), report `enabled/running`, and list the address in the live `PVEFW-0-pve_admins-v4` set. The pre-change file is [grey-server-pve-cluster.fw-2026-09-27](../../../../../Backups/grey-server-pve-cluster.fw-2026-09-27) (`46bf8b36…`); the host keeps no copy.

### SSH identity

I generated an ED25519 key on the laptop as `dkadi`, with the comment `parrot-os-mac` and no passphrase. Its fingerprint is `SHA256:BxT8jxsgZU9Kox38KItPkW8ZjfuaZ9mtr7079zCue/E`. On `ansible-01` I added `identities/parrot-os-mac.yml` (`ansible:ansible`, `0600`). Its 16-host allowlist is the same as the `mac` and `jedi-pc` lists. The validator passed with 5 identities.

The first run failed at the schema check before it touched any host. I had written the file through a single-quoted shell command, which turned `replacement_public_key: ''` into a null. The standalone validator missed this. I corrected the line and ran audit, onboard and audit again.

Onboarding added the key on the 11 guests. On `grey-server` the module failed with `[Errno 1] Operation not permitted: '/etc/pve/priv/authorized_keys'`, so the playbook exited 2, and the four other nodes skipped their verification because of that failure. The key had still been written. The cluster file went from 10 lines to 11 at 10:18. All five nodes read the same 4,287-byte file, which holds the Parrot key once and keeps its `0600 root:www-data` mode. The follow-up audit reports `current_key: present` on all 16 hosts. The error comes from a file operation after the write that the Proxmox cluster filesystem refuses. The playbook will report this again the next time it adds a key there. The three run logs are in `/home/ansible/parrot-*.log` on `ansible-01`.

I did not add Semaphore templates for this identity. The `ubuntu-dev` identity also has none live.

### Claude Code installed, then removed the same day

While setting up the laptop I installed Claude Code 2.1.283 for `dkadi` and registered Executor in it, so the laptop could drive SSH Manager and UniFi through an MCP client. On reflection that went past what the laptop is for: it is an admin endpoint, and the MCP client already runs elsewhere. I removed it the same day. I deleted `~/.local/bin` (the installer created it, and it held only the `claude` link), `~/.local/share/claude`, `~/.local/state/claude`, `~/.cache/claude`, `~/.cache/claude-cli-nodejs`, `~/.claude` and `~/.claude.json`. I also removed the three lines the installer had appended to `~/.bashrc`, which still passes `bash -n`. Everything I deleted had been created between 10:17 and 10:21 that day. It never signed in to Executor. `claude` no longer resolves in a new shell, and the SSH key still logs in to `grey-server`. `~/src/t1-revive/CLAUDE.md` belongs to a project on the laptop and was not touched.

## Verification

I ran all tests from the laptop.

- **SSH with the new key only** (`IdentitiesOnly`, `BatchMode`, no password): all 16 hosts logged in. The login was `root` (UID 0) on the five Proxmox nodes and `docker-main`, and `dkadi` on the other ten. These are the accounts the Mac identity uses.
- **TCP paths**: 35 of 35 open after the change. That covers 22, 8006 and 3128 on all five nodes; SSH to `docker-main`, `docker-blue`, `media-01`, `ansible-01` and `ubuntu-dev`; Jellyfin 8096; SSH to `edge-01`, `app-01`, `alpha-prod-01`, `security-01` and `splunk-siem`; PeaNUT 8090 and 3000 on `monitor-01`; NPM 443 and 22; WAC 443; RDP to HQ-DC01; SSH to the Jango switch and Anakin AP; and the gateway UI.
- **Baseline**: my first probe ran slowly and overlapped the UniFi edits, so it is not a clean before-picture. It did show all 15 Proxmox ports closed and SSH to all five Personal-A hosts closed. Both sets are open now.

## Left as it was

The rest of Jedi PC's access comes from being on Secure, VLAN 50, or in the `AG-PAW` address group. I did not give those grants to the laptop:

- `Allow PAW to Windows Admin`, which covers SSH, RDP and WinRM to the domain controllers and HQ-MGT01
- `Allow Workstations to AD` and `Allow Secure to HQ-WS001 SSH`
- `Allow Secure to monitor-01 break-glass`

The laptop already reaches `monitor-01` and RDP on the identity hosts through the Trusted-network policies. `Docker -> Jedi PC` is an inbound path to Jedi PC, not an access grant.

## Rollback

- UniFi: remove Parrot OS-Mac's MAC from the five MAC lists and `192.168.10.176` from the PeaNUT policy.
- Proxmox: delete the `192.168.10.176` line from `pve_admins`.
- SSH: remove the `parrot-os-mac` key material from the 16 key stores, then delete `identities/parrot-os-mac.yml`.
