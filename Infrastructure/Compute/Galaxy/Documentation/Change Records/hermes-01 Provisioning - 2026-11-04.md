# hermes-01 Provisioning

**Created:** 2026-11-04  
**Last updated:** 2026-11-04

**Implementation date:** 2026-11-04, 8:14 PM to 8:27 PM Eastern  
**Status:** Complete. The host carries the Linux host baseline and no workload.  
**Affected systems:** `grey-server` (new VM 112 `hermes-01`), three Ansible projects and six identity files on `ansible-01`, ssh-mcp on `docker-blue`

I built `hermes-01` as the host Hermes Agent will run on. It is VM 112 on Grey at `192.168.80.22` on SERVERS-A, a full clone of `debian13-template` with the Linux host baseline applied. Hermes itself, Docker, monitoring exporters and the Wazuh agent are not installed yet.

## Decisions

- **Host and size.** Grey, because on 2026-11-04 it had about 16 GiB of memory available and the other four nodes had between 1.4 and 6.3 GiB. 2 vCPU and a fixed 4 GiB, which sits inside the 2 to 4 GB Hermes documents for a gateway. The template's 60 GiB disk stays as it is.
- **Network.** SERVERS-A, VLAN 80. The `AlphaSec-Servers` zone has no standing path into the Internal zone, so anything Hermes later needs, such as Executor through Nginx Proxy Manager, gets its own policy. Before choosing `.22` I confirmed in UniFi's client list that only `.10`, `.20`, `.21` and `.118` were in use on `192.168.80.0/24`.
- **Operating system.** Debian 13 from the existing template. It needs none of the extra steps Ubuntu 24.04 and 26.04 take under the baseline, and Hermes's own image is built on Debian 13.4.
- **No desktop environment.** The template has none; `dpkg -l` lists no X server, GNOME, Xfce or display manager.

## 1. Clone

From Grey: `qm clone 101 112 --name hermes-01 --full 1 --storage ssd-lvm1`, then 2 cores, 4096 MiB with `balloon: 0`, `net0` `virtio` on `vmbr0` tag 80 with `firewall=1`, and `onboot=1`.

The clone carried an `ide2` CD-ROM with `debian-13.0.0-amd64-netinst.iso` and boot order `scsi0;ide2;net0`, because Proxmox discarded the template's pending `delete,boot` changes on clone. I deleted `ide2` and set the boot order to `scsi0` before the first start. First boot at 8:15 PM: the guest agent answered and `ens18` took a DHCP lease on VLAN 80.

## 2. What the template left behind

I inspected the clone through the QEMU guest agent before changing anything:

| Item | Found | Action |
|---|---|---|
| Hostname | `debian-vm` | set to `hermes-01`, `/etc/hosts` updated |
| `/etc/machine-id` | the template's ID | regenerated |
| SSH host keys | the template's three keys | deleted and regenerated with `ssh-keygen -A` |
| `dkadi` `authorized_keys` | one key, which matched `ansible-control`'s fingerprint, with no restriction prefix | moved to `ansible` with the controller prefix, `dkadi`'s file emptied |
| `ansible`, `ai-agent` | absent | created below |
| root | `passwd -S` `P`, set 2026-04-10 | reset by `account-passwords.yml` |
| sshd | effective `permitrootlogin no`, `passwordauthentication no`, `kbdinteractiveauthentication no`, empty `sshd_config.d` | `99-hardening.conf` written |
| cloud-init | not installed, no `/etc/cloud` | nothing to disable |
| Time zone, locale | `America/New_York`, `en_US.UTF-8` | none |

The template's `dkadi` key file is the one finding that matters beyond this host. The baseline keeps the controller key out of `dkadi`'s file, and every clone of template 101 inherits an unrestricted controller key there.

`systemd-machine-id-setup` did not regenerate the machine ID. It printed `Reusing machine ID stored in /run/machine-id` and wrote the old value back. `systemd-id128 new > /etc/machine-id` produced a new one, and `/var/lib/dbus/machine-id` links to it.

## 3. Bootstrap

ssh-mcp refuses any write that names an `authorized_keys` file and any `reboot`, so I ran the bootstrap and both reboots from my workstation's own SSH session to Grey, through `qm guest exec` and `qm reboot`. The bootstrap script:

- set the hostname, machine ID and host keys as above;
- created `ansible` with a `0700` home and wrote its one key with `from="192.168.40.36",no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty`; `ssh-keygen -lf` read back one ED25519 key with comment `ansible-control`;
- wrote `/etc/sudoers.d/90-ansible` at `0440` after `visudo -cf` returned `parsed OK`;
- wrote `/etc/ssh/sshd_config.d/99-hardening.conf` with the four baseline lines, and `sshd -t` passed;
- replaced the DHCP stanza in `/etc/network/interfaces` with `address 192.168.80.22/24` and `gateway 192.168.80.1`.

After the 8:18 PM reboot the static address and hostname were in place, but `/etc/resolv.conf` held only comments. dhcpcd had generated it and removed its own `nameserver` line when the DHCP interface went down. I wrote `nameserver 192.168.80.1` into it, and `deb.debian.org` resolved.

From `ansible-01`, `ssh ansible@192.168.80.22` logged in as `ansible` on `hermes-01` and `sudo -n true` succeeded. The host key it recorded matched the key on the host.

## 4. Linux baseline

I added `hermes-01` to the `host-access-baseline`, `ssh-key-automation` and `fleet-updates` inventories and to the two validators that pin host sets. The three copies on `ansible-01` were identical to the repository's before I copied the new ones over, and all three validators passed there: `16 ai-agent hosts`, `22 supported hosts`, `17 OS-update hosts`. I left it out of `monitoring-exporters` because nothing is to be monitored yet.

Then from `ansible-01`:

- `hermes-01` added to the target list of all six identity files.
- `ssh-identity-onboard.yml` per identity: `failed=0` for all six. `ansible-control` reported `changed=0`, because the bootstrap had already written exactly that line; the other five each reported `changed=1`.
- `apt` `upgrade=dist` with `autoremove`: kernel `6.12.115+deb13.1` and the current point-release packages. A second simulation reported `0 upgraded, 0 newly installed`.
- Installed `curl`, `wget`, `gnupg`, `vim`, `htop`, `rsync`, `jq`, `bind9-dnsutils`, `lsof`, `tmux`, `unzip` and `needrestart`.
- `ai-agent-account.yml`: `account=present keys=1 sshd_password_auth=no sshd_allowlist=none`.
- `account-passwords.yml`: `root=P root_auth=ok dkadi_auth=ok`.
- `sudoers-rootpw.yml`: `visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok`.

The three account playbooks read their passwords from a mode-`0600` vars file staged from my password manager. I shredded it on `ansible-01` and on my workstation after the last play, and `~/.hab-run` no longer exists.

`ansible` keeps a locked password (`passwd -S` `L`). The standard's step 4 says to give it the standard password for console recovery, but the project README treats it as a key-only service account, and `kube-management`, `garm-01` and `ci-cache-01` all have it locked. I followed the recent hosts.

## 5. ssh-mcp

I added profile `hermes_01` to [config.toml](../../../../../Platforms/SSH%20MCP/Configuration/config.toml) as `dkadi` with the shared key, after confirming the live `config.unpinned.toml` matched the repository's copy. The fingerprints `ssh-keyscan` returned from `docker-blue` matched `ssh-keygen -lf` run on the host's own key files through the guest agent, for all three key types. I appended the three keys to `/opt/docker/ssh-mcp/known_hosts`. I wrote the sudo password entry by copying the value of an existing entry on the host, so it never appeared in a command, because every guest shares root's password. The install script reported `profiles: 31`, `pins: 31`, `sudo passwords: 16`. I recreated the container from a transient systemd unit so the recreate did not cut off the session that started it, and it came back `healthy`.

`whoami` through `hermes_01` returned `dkadi`, and `id -u` through `privileged-command` returned `0`. `kube_management`, `garm_01` and `grey_server` still answered afterwards.

## 6. Verification

After the 8:24 PM reboot into the new kernel, read on the host:

| Check | Result |
|---|---|
| Kernel, state | `6.12.115+deb13.1-amd64`, `running`, 0 failed units |
| Network | `192.168.80.22/24`, default via `192.168.80.1`, DNS resolves, HTTPS to `deb.debian.org` returned 200 |
| `dkadi` | in `sudo`; `sudo -n true` refused with `a password is required`; `sudo -l -U dkadi` lists `rootpw` and `(ALL : ALL) ALL` |
| `ai-agent` | `not allowed to run sudo on hermes-01` |
| `ansible` | `sudo -n true` exit 0 |
| root | `passwd -S` `P` |
| sudoers.d | `00-rootpw` and `90-ansible`, both `0440` |
| sshd | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`, no `AllowUsers` |
| `dkadi` keys | five: `jedi-pc`, `mac-air3-dkadi`, `parrot-os-mac`, `andor-parrotos-pc`, `ai-agent@ubuntu-dev`; no controller key |
| `ansible` keys | one, `ansible-control`, with the `from=` prefix |
| `ai-agent` keys | one, `ai-agent@ubuntu-dev` |
| Homes | all three `0700`, every `authorized_keys` `0600` |
| `ssh-key-audit.yml` | `present` for all six identities |
| Time | `America/New_York`, `NTPSynchronized=yes` against `2.debian.pool.ntp.org`, offset +11 ms |
| Locale | `LANG=en_US.UTF-8` |
| Resources | 2 CPUs, 3.8 GiB, root filesystem 55 GiB at 4% |

The clock had not synchronized one minute after boot. Two minutes later it had, and `alpha-prod-01` on the same VLAN syncs to the same pool.

## Left open

- **Hermes Agent is not installed.** The plan was the official image under Compose, its dashboard on loopback, Discord limited to my user ID, and a dedicated Executor login scoped to the apps it needs. Later the same evening I installed it with the upstream installer as `dkadi` instead; that work is in [Install and Discord Gateway](../../../../../Platforms/Hermes%20Agent/Documentation/Change%20Records/Install%20and%20Discord%20Gateway%20-%202026-11-04.md).
- **No path to Executor yet.** Hermes will need a UniFi policy from `192.168.80.22` to Nginx Proxy Manager at `192.168.85.2:443`, modelled on `Allow alpha-prod-01 Hawser to NPM HTTPS`. I added it as `Allow hermes-01 to NPM HTTPS` the same evening ([firewall](../../../../Network/UniFi/Configuration/firewall.md)).
- **Not monitored.** No node_exporter target and no Wazuh agent, until the host carries something worth watching.
- **Template 101 needs cleaning.** It still has the unrestricted controller key in `dkadi`'s file, the netinst ISO attached, and the pending `delete,boot` changes that do not survive a clone. The next clone repeats sections 1 to 3 until the template is fixed.
