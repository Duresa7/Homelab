# Andor-ParrotOS-PC Admin Access

**Created:** 2026-10-11  
**Last updated:** 2026-10-12

**Implementation date:** 2026-10-11  
**Status:** Complete  
**Affected systems:** four MAC-based and one IP-based UniFi firewall policy, the `AG-PAW` address group, one UniFi client alias, the Galaxy Datacenter firewall, `ssh-key-automation` on `ansible-01`, 15 authorized-key stores, and the SSH key in the desktop's `dkadi` account

On 2026-10-11 I gave Andor-ParrotOS-PC the same admin access as Jedi PC: its own SSH key on Jedi PC's 16 hosts, every UniFi grant that names Jedi PC, and Jedi PC's place in the Proxmox `pve_admins` set.

## The device

Andor-ParrotOS-PC is Parrot Security 7.4 on ObiPC's hardware, installed in place of ObiPC's Windows 11 domain build for a while. I treat it as a separate machine from ObiPC, and ObiPC's records and objects stay as they are. Its record is [Andor-ParrotOS-PC](../../../../Hardware/Workstations/Andor-ParrotOS-PC.md).

| Item | Value |
|---|---|
| OS | Parrot Security 7.4 (echo), installed 2026-10-11 |
| Hostname, account | `parrot`, `dkadi` (in `sudo`, password required) |
| Network | Secure, VLAN 50, wired, DHCP `192.168.50.102` |
| MAC | Withheld. It is the adapter UniFi already knew as `Obi PC`. |
| SSH Manager entry | `andor_parrot_os_pc` |

Before I changed anything I confirmed that the machine would not hand Jedi PC's access to another OS. The firmware's only internal boot entry is `Parrot`, no Windows Boot Manager remains, and the 500 GB drive holds an NTFS data partition with no EFI system partition. That holds only while Parrot is the installed OS. The MAC grants below follow the network adapter, not the OS, so they have to come off before ObiPC's Windows goes back on this hardware (see Open).

## What Jedi PC has, and what this needed

Jedi PC (`192.168.50.241`) is also on Secure, so the Secure-network policies already cover the desktop: `Allow Secure and Secure Client to WAC HTTPS`, `Allow Admin Networks to Identity RDP`, `Allow Secure to HQ-WS001 SSH`, `Allow Workstations to AD`, and the inbound `Docker -> Jedi PC`. I searched all 89 user-defined policies (the list returned 89 of 89) for Jedi PC's MAC, its address and the `AG-PAW` group. Six policies matched, and those six plus `pve_admins` are what I changed.

## What changed

### UniFi

For each policy I read it, changed only its source, and read it back. In every case the rest of the policy compared equal before and after.

| Object | Source before | Source after |
|---|---|---|
| `DMZ Allow List` | 4 MACs | 5 MACs |
| `Allow Devices to Personal-A` | 10 MACs | 11 MACs |
| `Device Access --> Proxmox` | 6 MACs | 7 MACs |
| `Jedi PC --> Unifi Console SSH` | 2 MACs (Jedi PC, Parrot OS-Mac) | 3 MACs |
| `Allow Secure to monitor-01 break-glass` | `192.168.50.241` | `192.168.50.241`, `192.168.50.102` |
| `AG-PAW` address group | `192.168.50.241` | `192.168.50.241`, `192.168.50.102` |

`AG-PAW` is the source of `Allow PAW to Windows Admin`, which opens `PG-Windows-Admin` (TCP 22, 3389, 5985 and 5986) to the identity servers. I did not edit that policy itself.

I also renamed the UniFi client from `Obi PC` to `Andor-ParrotOS-PC`, so the MAC lists read correctly in the controller. Its DHCP hostname still reports `Obipc`.

### Galaxy Datacenter firewall

I added `192.168.50.102 # Andor-ParrotOS-PC` to `pve_admins` in `/etc/pve/firewall/cluster.fw` on `grey-server`, directly after Jedi PC's line. The diff was that one line, and the file went from 52 lines to 53 (`f9e894e5…`). `pve-firewall compile` exited 0. All five nodes read the same digest and report `enabled/running`. `ipset test` finds `192.168.50.102` in the live `PVEFW-0-pve_admins-v4` set on all five, which holds six members. Grey-server showed `pending changes` for the first minute, then applied. I took no copy of the file: the change is one line, and the rollback below names it.

### SSH identity

I generated an ED25519 key on the desktop as `dkadi`, with the comment `andor-parrotos-pc` and no passphrase, like the Parrot OS-Mac key. Its fingerprint is `SHA256:EkErC2I8oBnZLf7PK2339LfRK9jCrbUXzAL49c8ZMRA`. On `ansible-01` I added `identities/andor-parrotos-pc.yml` (`ansible:ansible`, `0600`) with the same 16-host allowlist as `jedi-pc`.

The first run validated and audited (`missing` on the 15 reachable hosts), then the onboarding step failed before it touched any host. I had passed `ssh_target_group=ssh_key_missing`, which is not an inventory group, so the requested list was empty and the allowlist check refused it. The README's onboarding example has the same flaw. I reran onboarding with an explicit `ssh_target_hosts` list of the 15 reachable hosts.

`app-01` (`192.168.80.10`) is parked and returned `No route to host`, so it does not have the key. `ubuntu-dev` is not one of the 16, but Jedi PC's key is in its `ai-agent` account by hand, so on 2026-10-12 I added this key the same way (described in the next section). On `grey-server` the module failed again with `[Errno 1] Operation not permitted: '/etc/pve/priv/authorized_keys'`, the same post-write error recorded for Parrot OS-Mac. The follow-up audit reads `current_key: present` on all 15 reachable hosts, `grey-server` included. The run logs are `/home/ansible/andor-run.log` and `/home/ansible/andor-run2.log` on `ansible-01`. I deleted the two run scripts.

### ubuntu-dev

`ssh-key-automation` does not manage `ubuntu-dev`. Its `ai-agent` `authorized_keys` held four keys, set by hand: `mac-air3-dkadi`, `jedi-pc`, `ansible-control` and `ai-agent@ubuntu-dev`. On 2026-10-12 I appended the desktop's public key there, after checking that it was one `ssh-ed25519` line with the `andor-parrotos-pc` comment. The file is now 482 bytes, still `0600`, and `ssh-keygen -lf` lists the new line with the fingerprint above. I scanned `ubuntu-dev`'s RSA, ECDSA and ED25519 host keys from the desktop and compared them with `ubuntu-dev`'s own `/etc/ssh/ssh_host_*_key.pub`. All three matched, so I added them to the desktop's `known_hosts`, which had no entry for `192.168.40.179` before. A key-only login from the desktop returned `ubuntu-dev as ai-agent`.

## Verification

I ran these from the desktop, using only the new key (`IdentitiesOnly`, `BatchMode`, no password).

- **SSH:** 15 of 15 logged in: `root` on the five Proxmox nodes and `docker-main`, and `dkadi` on `docker-network`, `alpha-prod-01`, `edge-01`, `security-01`, `splunk-siem`, `docker-blue`, `media-01`, `monitor-01` and `ansible-01`. These are the accounts Jedi PC's identity uses. Host keys were accepted on first use into the desktop's `known_hosts`.
- **TCP paths:** 44 of 44 open:
  - 22, 8006 and 3128 on all five nodes.
  - SSH to `docker-main`, `docker-blue`, `media-01`, `ansible-01`, `ubuntu-dev`, `edge-01`, `alpha-prod-01`, `security-01`, `splunk-siem`, `docker-network` and `monitor-01`.
  - Jellyfin 8096.
  - The break-glass ports 3000, 8090 and 9090 on `monitor-01`.
  - NPM 443.
  - 22, 3389 and 5985 on HQ-DC01, HQ-DC02 and HQ-MGT01.
  - WAC 443.
  - SSH to the Jango switch (`192.168.1.179`) and Anakin AP (`192.168.1.178`).
  - The gateway UI.
- **Baseline:** I did not probe before the change, so this is not a before-and-after comparison. The paths that depend on the new grants are now open.

## Open

- `app-01` lacks the key because the VM is parked. When it comes back, I run `ssh-identity-onboard.yml` for `andor-parrotos-pc` with `ssh_target_hosts` set to `["app-01"]`.
- ObiPC's records and objects stay: the SSH Manager entry `obipc`, the `OBIPC` computer object and its LAPS password in Active Directory, and the Action1 agent. ObiPC is a separate machine whose Windows install is off this hardware for now.
- Before ObiPC's Windows goes back on this hardware, work through [Before ObiPC's Windows returns](#before-obipcs-windows-returns).

## Before ObiPC's Windows returns

Andor-ParrotOS-PC and ObiPC share one Ethernet adapter, so they share one MAC. UniFi matches the four MAC-based policies against that adapter whatever OS is running. If Windows goes back on with these grants in place, ObiPC's end-user Windows gets Jedi PC's access: DMZ, Personal-A, Proxmox and the UniFi console's SSH. If it also takes `192.168.50.102`, the `AG-PAW` Windows admin ports, the `monitor-01` break-glass ports and Proxmox `pve_admins` follow it as well. Before reinstalling Windows, I complete each step and read it back:

1. **UniFi MAC lists.** Remove the adapter's MAC from `DMZ Allow List`, `Allow Devices to Personal-A`, `Device Access --> Proxmox` and `Jedi PC --> Unifi Console SSH`. Read each policy back and compare it with its state before the edit, as on 2026-10-11.
2. **UniFi addresses.** Remove `192.168.50.102` from the `AG-PAW` group and from `Allow Secure to monitor-01 break-glass`.
3. **Proxmox.** Delete the `192.168.50.102 # Andor-ParrotOS-PC` line from `pve_admins` in `/etc/pve/firewall/cluster.fw`, run `pve-firewall compile`, and confirm that `ipset test` no longer finds the address on any of the five nodes.
4. **UniFi client name.** Rename the client from `Andor-ParrotOS-PC` back to `Obi PC`.
5. **Andor-ParrotOS-PC itself.** Installing Windows destroys the `andor-parrotos-pc` private key, which lives only on the Parrot disk. If Parrot is not coming back, remove that key from the 15 key stores and from `ubuntu-dev`, as in the SSH line under Rollback, and remove the SSH Manager entry `andor_parrot_os_pc`. If Parrot is coming back, I can leave them.

`firewall.md` and `objects.md` under `Infrastructure/Network/UniFi/Configuration/`, and `Datacenter-Firewall.md` under Galaxy, change with steps 1 to 3.

## Rollback

- UniFi: remove the desktop's MAC from the four MAC lists, and remove `192.168.50.102` from `AG-PAW` and from the break-glass policy.
- Proxmox: delete the `192.168.50.102` line from `pve_admins`.
- SSH: remove the `andor-parrotos-pc` key from the 15 key stores, then delete `identities/andor-parrotos-pc.yml`. On `ubuntu-dev`, delete the `andor-parrotos-pc` line from `/home/ai-agent/.ssh/authorized_keys` by hand.
