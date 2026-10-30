# Phase 1 Build

**Created:** 2026-10-30  
**Last updated:** 2026-10-30

**Implementation date:** 2026-10-30  
**Status:** Complete  
**Affected systems:** UniFi (KUB-A, zone `AlphaSec-Kube`, `Proxmox-Trunk`), `green-server` (new VM 820 `ci-k3s-01`), `grey-server` (VM 103 `win11-dev`), SSH Manager on `docker-blue` and Dockhand's copy on `docker-main`, `ansible-01`, `monitor-01`, `security-01`

On 2026-10-30 I built the first phase of my self-hosted GitHub Actions runners: an isolated VLAN, a single-node k3s cluster on Green with the ARC controller installed, and `win11-dev` turned into a runner-only machine on the same VLAN. I connected no new repository. The design is in [Cross-Platform CI Research](../../../../Architecture/Cross-Platform%20CI%20Research%20-%202026-10-28.md).

Green carried no guest before this. Its memory errors traced to one SK Hynix module on 2026-10-28, and it runs on the 8 GB Micron module alone ([memory record](../../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md)). That is why the VM has 6 GiB rather than 8.

## 1. Network

I created KUB-A on VLAN 82 with its own zone, `AlphaSec-Kube`, eight firewall policies, and removed it from the `Proxmox-Trunk` exclusion list. The detail and the controller readback are in [KUB-A VLAN 82](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/KUB-A%20VLAN%2082%20-%202026-10-30.md).

## 2. VM 820 `ci-k3s-01`

I downloaded `ubuntu-26.04.1-live-server-amd64.iso` to Green's `local` storage. Its SHA-256 matched the `SHA256SUMS` file on `releases.ubuntu.com`. I created VM 820 to match `alpha-prod-01`'s layout: q35, OVMF with a 4 MiB EFI disk and no pre-enrolled keys, `cpu: host`, 4 cores, 6144 MiB with ballooning off, `virtio-scsi-single`, a 120 GiB `local-lvm` disk with `discard`, `iothread`, `ssd` and `cache=writeback`, `virtio` on `vmbr0` with `firewall=1` and `tag=82`, QEMU agent on, `onboot=1`. VMID 820 follows the VLAN; the Grey node will be 821.

The install used Ubuntu autoinstall from a CIDATA seed ISO built on Green with `genisoimage`. The [published template](../../Configuration/ci-k3s-01-autoinstall.yaml) selects `ubuntu-server-minimal` plus OpenSSH, sets the static address `192.168.82.10/24`, takes the whole disk as LVM, creates `dkadi` with a throwaway random password hash and `ubuntu-dev`'s key, and in `late-commands` creates `ansible` with the controller key behind its `from="192.168.40.36"` restriction, writes `/etc/sudoers.d/90-ansible` through `visudo -cf`, and writes `99-hardening.conf`. I added `autoinstall` to the GRUB kernel line from the Proxmox console with `qm sendkey`, so the installer did not stop for confirmation.

The first attempt stopped with `Malformed autoinstall in 'late-commands' section`. The line that wrote the ansible sudoers rule contained `NOPASSWD: ALL` as an unquoted YAML scalar, which YAML reads as a mapping, so that list item was not a string. I rewrote the late commands as one literal block, checked that every item parsed as a string, rebuilt the seed and restarted the VM. The second install ran from 1:08 PM to 1:14 PM and powered off as configured.

I then removed both CD drives' media, set the boot order to `scsi0`, deleted the seed ISO and its working directory from Green, and booted. `ci-k3s-01` answered SSH from `ubuntu-dev` on `192.168.82.10` as Ubuntu 26.04.1 LTS, kernel `7.0.0-42-generic`.

## 3. Linux baseline

I applied the [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md) from `ansible-01`, after adding `ci-k3s-01` to the `host-access-baseline`, `ssh-key-automation`, `monitoring-exporters`, `fleet-updates` and Wazuh inventories and to the three validators that pin their host sets.

| Step | Result |
|---|---|
| Patch | `apt-get full-upgrade`, then zero upgradable packages and no reboot required |
| Locale and time | The minimized image had not generated `en_US.UTF-8` and left the time zone at UTC. I generated the locale and set `America/New_York` |
| `ai-agent` | `ai-agent-account.yml`: `account=present keys=1 sshd_password_auth=no sshd_allowlist=none` |
| Passwords | `account-passwords.yml`: `root=P root_auth=ok`, `dkadi_auth=ok` |
| Sudo | `sudoers-rootpw.yml`: `visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok`, after the sudo change below |
| Keys | `ssh-identity-onboard.yml` added Jedi PC, Mac, Parrot OS-Mac and Andor-ParrotOS-PC to `dkadi`; `ubuntu-dev` and `ansible-control` were already present |
| Home directories | Ubuntu creates them `0750`. I set `/home/dkadi`, `/home/ai-agent` and `/home/ansible` to `0700` like the rest of the fleet, and `DIR_MODE` and `HOME_MODE` to `0700` |
| cloud-init | `/etc/cloud/cloud-init.disabled` present |
| Node exporter | `node-exporter.yml`: binary 1.9.0 on `:9100`; `textfile-collectors.yml` also applied |
| Wazuh | `deploy.yml --limit ci-k3s-01 -e wazuh_agent_version=4.14.8-1`, agent ID 022, `Active` on the manager |

The two passwords went from my password manager into a `0600` JSON file on `ansible-01` through stdin, never into a command line. The first staging attempt wrote an empty root value because the secret reference used a section name containing parentheses, which the CLI rejects. I shredded that file before any play read it and staged again by field ID. I shredded the file after the last play.

**Ubuntu 26.04 ships `sudo-rs` as `sudo`.** The first `sudoers-rootpw.yml` run wrote `00-rootpw` and then failed its readback: `sudo -l -U dkadi` listed `(ALL : ALL) ALL` but no `rootpw` among the Defaults. The classic `sudo.ws` 1.9.17p2 is installed beside it, and the baseline's `rootpw` model has only been proven against classic sudo. I switched the alternative with `update-alternatives --set sudo /usr/bin/sudo.ws`. `sudo -l -U dkadi` then listed `rootpw`, and a second play run passed every check. `ansible` kept `NOPASSWD` throughout.

The wazuh playbook still pins agent `4.14.6-1`, while the manager and the fleet run `4.14.8-1`. I passed the matching version on the command line and left the pin as it is.

The verification checklist from the standard all passed: `sudo -n true` as `dkadi` exits 1 with `a password is required`, `sudo -l -U ai-agent` reports `not allowed to run sudo`, `ansible` passes `sudo -n true`, `passwd -S root` and `ai-agent` show `P`, and `sshd -T` reports `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no`.

## 4. SSH Manager

`ci-k3s-01`'s `dkadi` key set matches `docker-network`'s, which SSH Manager already reaches, so no extra key was needed. On `docker-blue` I added eight `SSH_SERVER_CI_K3S_01_*` settings after the Andor-ParrotOS-PC block in the live Compose file, appended the sudo line to `ssh-manager.env` (11 entries, 1,162 bytes, `0600 root`), scanned the RSA, ECDSA and ED25519 host keys into `/state/ssh/known_hosts`, passed `docker compose config -q`, and recreated `ssh-manager` detached. I made the same insertion in Dockhand's copy on `docker-main`. Both files hashed `bc56b647…` at 20,372 bytes. The sudo value travelled as a `0600` staging file through `ansible-01`, and I shredded every copy.

`ssh_list_servers` returned 26 entries. `ssh_execute` on `ci_k3s_01` returned `dkadi`, and `ssh_execute_sudo` returned `root`.

## 5. k3s and ARC

| Item | Version | Source |
|---|---|---|
| k3s | v1.36.5+k3s1 | the `stable` channel on 2026-10-30; `get.k3s.io` with `INSTALL_K3S_VERSION` |
| Helm | v4.3.1 | `get.helm.sh` tarball, checked against its `.sha256sum` |
| ARC controller | chart 0.15.1 | `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller` |

I kept the k3s defaults, so Traefik and ServiceLB run. The node reported `Ready`, `control-plane`, containerd `2.3.4-k3s1.36`. `/etc/rancher/k3s/k3s.yaml` is `0600 root`, so `kubectl` and `helm` run through sudo on the node. ARC went in as Helm release `arc` in `arc-systems`, created the four `actions.github.com` CRDs, and its controller pod was `Running`. At 1:33 PM every pod was `Running` or `Completed`, the node used 1,430 MiB and 8.4 GiB of its disk, and Green had 2,364 MiB available.

## 6. `win11-dev`

`win11-dev` is now a runner-only machine. Before the change I confirmed SSH as `dkadi`, a local administrator, and that App Portal's `windows-x64-1` runner was installed under `C:\actions-runner\app-portal`, running as LocalSystem. Windows reported a retail licence with `LicenseStatus 1`, so the open activation item was already done.

1. **Runner account.** I generated a 32-character password, stored it in my password manager as a new item, and created local user `gh-runner` in Administrators with a non-expiring password. Through `secedit` I granted it `SeServiceLogonRight` and added it to `SeDenyInteractiveLogonRight` and `SeDenyRemoteInteractiveLogonRight`. I changed the runner service to log on as `.\gh-runner` through `Win32_Service.Change`, which returned 0, and restarted it. The password reached the VM as a file in `dkadi`'s profile that the script deleted on read.
2. **Readback.** The service ran as `.\gh-runner`, the listener process belonged to `WIN11-DEV\gh-runner`, and the runner log recorded `Listening for Jobs` at 1:28 PM.
3. **RDP.** I enabled Remote Desktop with Network Level Authentication and limited the three inbound Remote Desktop firewall rules to `192.168.50.241`.
4. **Network move.** A one-time SYSTEM task disabled DHCP and set `192.168.82.11/24`, gateway and DNS `192.168.82.1`. I started it and changed VM 103's `net0` from `tag=40` to `tag=82` with the MAC unchanged at 1:28 PM. `win11-dev` answered SSH on `192.168.82.11` within a minute, resolved `github.com`, and reached it on 443. I set the network profile to Private and removed the task and its script.
5. **Cleanup.** I turned off the UniFi DHCP reservation that held `192.168.40.117` for this VM.
6. **SSH Manager.** I changed `win11_dev`'s host to `192.168.82.11` and its description, which still said Green, in both Compose files (`a14eea96…`, 20,364 bytes), added the three host keys for the new address, and recreated `ssh-manager`. The ED25519, RSA and ECDSA fingerprints matched the ones `ubuntu-dev` already held for `192.168.40.117`.

The runner retried two broker requests at 1:28 and 1:29 PM while the network moved and then recovered. The GitHub API reported `windows-x64-1` `online` and idle.

## 7. Monitoring

I added `192.168.82.10:9100` to the `node` job, uploaded the candidate to `monitor-01`, passed `promtool check config`, wrote it into place and sent `HUP`. `assert_targets.py` reported `node|ci-k3s-01|up`. It also reported `app-01` down, which is the VM I stopped on 2026-10-09.

I added `ci-k3s-01` to the dashboard inventory with `apt=True` and no systemd panels, since the binary node exporter runs without the systemd collector. The layout check passed for 28 dashboards. The query check ran 1,513 queries: `ci-k3s-01` returned all 55, and the 60 empty results all belonged to the stopped `app-01`. I deployed the dashboards to `monitor-01`.

## 8. Isolation check

From `ci-k3s-01` at about 1:31 PM:

| Destination | Result |
|---|---|
| `github.com:443`, `deb.debian.org:80` | open |
| `192.168.82.1:53` gateway DNS | open |
| `192.168.72.2:1514` Wazuh | open |
| `1.1.1.1:53`, `1.1.1.1:22` | blocked |
| `192.168.72.3:514` Splunk | blocked |
| `192.168.40.36:22` `ansible-01` | blocked |
| `192.168.80.118:22` `alpha-prod-01` | blocked |
| `192.168.70.10:8006` Grey | blocked |
| `192.168.65.10:389` HQ-DC01 | blocked |
| `192.168.82.11:22` `win11-dev` | open, same subnet |

Traffic between `ci-k3s-01` and `win11-dev` stays on VLAN 82 and never reaches the gateway, so the zone policies do not separate them.

## Left in place

- `ubuntu-26.04.1-live-server-amd64.iso` stays on Green's `local` storage for the Grey node.
- No configuration file copies were taken; every edit was an insertion or a line replacement that the rollback reverses.

## Open

- No runner scale set exists and no new repository is wired. The README lists the next steps.
- The dashboard builder counts 21 blackbox probes while `prometheus.yml` holds 22, so a rebuild changes "Services reachable" from 22 to 21 on two boards. That predates this work. I left both boards at their committed state.
- The Wazuh deployment playbook's `4.14.6-1` pin is behind the fleet's `4.14.8-1`.

## Rollback

- VM 820: `qm stop 820 && qm destroy 820 --purge` on Green, then remove `ci-k3s-01` from the five inventories, three validators, the Prometheus `node` job, `assert_targets.py`, the dashboard inventory, the six identity allowlists on `ansible-01`, and the SSH Manager entry. The Wazuh agent ID 022 is removed with `manage_agents -r 022` on `security-01`.
- `win11-dev`: set `net0` back to `tag=40`, return the adapter to DHCP, restore the reservation, change the runner service back to LocalSystem, and remove `gh-runner`.
- KUB-A: the rollback in the UniFi record.
