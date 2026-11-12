# e2b-01 Provisioning

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

**Implementation date:** 2026-11-11, 7:40 PM to 8:55 PM Eastern  
**Status:** Complete. The host carries the Linux host baseline, Docker, the Wazuh agent and the E2B Embed trial.  
**Affected systems:** `grey-server` (new VM 113 `e2b-01`), three Ansible projects and six identity files on `ansible-01`, ssh-mcp on `docker-blue`, the Wazuh manager on `security-01`

I built `e2b-01` as the single host for an [E2B Embed](../../../../../Platforms/E2B/README.md) trial: self-hosted Firecracker sandboxes that agents on my machines create, run code in and throw away. It is VM 113 on Grey at `192.168.80.30` on SERVERS-A, installed from the Ubuntu 26.04.1 server ISO with an autoinstall seed, then taken through the Linux host baseline from `ansible-01`. The E2B stack itself is in [Embed Trial Deployment](../../../../../Platforms/E2B/Documentation/Change%20Records/Embed%20Trial%20Deployment%20-%202026-11-11.md).

## Decisions

- **Its own VM.** Embed loads `nbd`, writes sysctl and modprobe files, adds an iptables mangle rule, reserves hugepages and creates `/fc-*` and `/orchestrator` on every start, and E2B says to give it a dedicated host. Destroying the VM undoes all of it.
- **Grey, nested.** Grey's `kvm_amd` reported `nested=1`, so a guest with `cpu: host` gets `/dev/kvm` for Firecracker.
- **Size.** 8 vCPU and a fixed 16 GiB with ballooning off, because Embed reserves hugepages out of guest memory. 120 GiB on Grey's NVMe `local-lvm` for template and snapshot reads. Before the build Grey had 34 GiB available.
- **Network.** SERVERS-A, VLAN 80. Untrusted code runs inside this VM, and the `AlphaSec-Servers` zone has no standing path into the Internal zone. Every Internal network already reaches SERVERS-A. `.30` was unused; `.10`, `.22` and `.118` are the other recorded hosts.
- **Operating system.** Ubuntu 26.04.1, the release `ubuntu-dev` runs. E2B wrote and tested its x86 guide on 24.04 and verified 26.04 on arm64. Embed's preflight passed on it unchanged (see the deployment record).
- **`onboot=0`.** The trial runs until the 2026-11-25 review. After a Grey reboot the VM stays off until I start it.

## 1. Media and VM

On Grey I downloaded `ubuntu-26.04.1-live-server-amd64.iso` into `local`, and `sha256sum -c` against Ubuntu's `SHA256SUMS` line returned `OK`.

[build-seed.sh](../../../../../Platforms/E2B/Scripts/build-seed.sh) rendered [e2b-01-autoinstall.yaml](../../../../../Platforms/E2B/Configuration/e2b-01-autoinstall.yaml) with the `ai-agent@ubuntu-dev` key, the `ansible-control` key from `ansible-01` and a throwaway `dkadi` hash, and wrote `e2b-01-seed.iso` on Grey. It printed `placeholders_left=0`. The seed installs `qemu-guest-agent`, `iptables`, `rsync`, `e2fsprogs`, `iproute2`, `python3-venv`, `nftables` and `locales`, creates `ansible` with the restricted controller key and `90-ansible`, and writes `99-hardening.conf`, as the CI-runner seed did.

At 7:45 PM:

```sh
qm create 113 --name e2b-01 --machine q35 --bios ovmf \
  --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=0 --cpu host --sockets 1 --cores 8 --numa 0 \
  --memory 16384 --balloon 0 --ostype l26 --agent 1 --scsihw virtio-scsi-single \
  --scsi0 local-lvm:120,discard=on,iothread=1,ssd=1,cache=writeback \
  --net0 virtio,bridge=vmbr0,firewall=1,tag=80 \
  --ide2 local:iso/ubuntu-26.04.1-live-server-amd64.iso,media=cdrom \
  --ide3 local:iso/e2b-01-seed.iso,media=cdrom \
  --boot "order=scsi0;ide2" --onboot 0 --vga std
```

I added `autoinstall` to the GRUB kernel line with `qm sendkey`, and the installer powered the VM off when it finished. I removed both CD drives' media, set the boot order to `scsi0`, deleted the seed ISO and `/root/e2b-01-seed` on Grey, and started it. The guest agent reported `192.168.80.30` on the first boot. `ens18` is named in netplan, so boot does not wait on a nonexistent `eth0`.

Inside the guest: Ubuntu 26.04.1 LTS, kernel `7.0.0-43-generic`, 8 CPUs, 15 GiB, and both `/dev/kvm` and `/dev/net/tun` present.

## 2. Linux baseline

I added `e2b-01` to the `host-access-baseline` and `ssh-key-automation` inventories and the `host-access-baseline` validator in the repository, copied them to `ansible-01`, and both validators passed there (`12 ai-agent hosts`; `6 identities, 18 supported hosts`). On `ansible-01` only, I added it to all six identity files' target lists and to `wazuh-agent-deployment`'s `wazuh_agent_targets`. It is not in `monitoring-exporters` or `fleet-updates` during the trial.

From `ansible-01`:

- One shell task: `apt-get full-upgrade` with `--force-confold` returned 0 and no reboot was required; `en_US.UTF-8` generated and set; time zone `America/New_York`; `update-alternatives --set sudo /usr/bin/sudo.ws`; homes `0700` with `DIR_MODE=0700` and `HOME_MODE 0700`. Four packages stayed upgradable afterwards (`python3-distro-info`, `python3-software-properties`, `snapd`, `software-properties-common`), held back by phasing.
- `ai-agent-account.yml`: `account=present keys=1 sshd_password_auth=no sshd_allowlist=none`.
- `account-passwords.yml`: `root=P root_auth=ok dkadi_auth=ok`.
- `sudoers-rootpw.yml`: `visudo=ok rootpw_in_force=ok rootpw_accepted=ok loginpw_refused=ok`.
- `ssh-identity-onboard.yml` for the six identities: `failed=0` each; `ubuntu-dev` and `ansible-control` reported `changed=0` because the autoinstall had already written those keys.
- `wazuh-agent-deployment` `deploy.yml` with `wazuh_agent_version=4.14.10-1`, the manager's `dpkg-query` version: `failed=0`. `agent_control -l` on `security-01` showed agent `022` `e2b-01` as `Pending`, then `Active`.

The three account playbooks read a mode-`0600` vars file staged from my password manager, which I shredded on `ansible-01` after the last play.

## 3. ssh-mcp

I added profile `e2b_01` to [config.toml](../../../../../Platforms/SSH%20MCP/Configuration/config.toml) as `dkadi` with the shared key. I took the host's three public keys from its own key files through the QEMU guest agent rather than `ssh-keyscan`, replaced the stale `192.168.80.30` lines in `/opt/docker/ssh-mcp/known_hosts`, and appended `SSH_MCP_E2B_01_SUDO_PASSWORD` to `ssh-mcp.env` from a `0600` file staged from my password manager and shredded after use. The install script reported `profiles: 26`, `pins: 26`, `sudo passwords: 12`, and I recreated the container through Ansible on `docker-blue`, outside ssh-mcp. `privileged-command` through `e2b_01` returned `0`, `root` and `e2b-01`.

## 4. Gateway intrusion prevention blocked SSH

After `ssh-keyscan -H 192.168.80.30` from `ansible-01`, every new SSH connection from `ansible-01` to `e2b-01` timed out, while `ubuntu-dev` connected and `ansible-01` still reached `alpha-prod-01` on the same VLAN. UniFi's traffic flows showed eight `blocked` SSH flows from `192.168.40.36` to `192.168.80.30`, policy `Scanning Activity`, category `EMERGING_SCAN`, type `INTRUSION_PREVENTION`. A multi-type `ssh-keyscan` opens one connection per key type, and with my own retries that crossed the signature's threshold. With no attempts for about ten minutes the block lapsed and the next connection succeeded.

Later in the build `ubuntu-dev` hit the same signature after several `scp` and `ssh` connections to `e2b-01` within a few minutes, so I moved the remaining host checks to ssh-mcp. Onboarding a new host goes better with one `ssh-keyscan -t ed25519`, host keys taken through the guest agent, and few separate connections. I left the IPS configuration unchanged.

## 5. Verification

[verify-baseline.sh](../../../../../Platforms/E2B/Scripts/verify-baseline.sh) through Ansible's `script` module:

| Check | Result |
|---|---|
| `dkadi` | in `sudo` |
| `ai-agent` | `not allowed to run sudo on e2b-01` |
| `ansible` | `sudo -n true` exit 0 |
| root, `ai-agent` | `passwd -S` `P` |
| sshd | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no` |
| sudoers.d | `00-rootpw` and `90-ansible`, both `0440` |
| Keys | `ansible`: `ansible-control`; `ai-agent`: `ai-agent@ubuntu-dev` |
| cloud-init | disabled |
| Time, locale | `America/New_York`, `NTPSynchronized=yes`, `LANG=en_US.UTF-8` |
| Homes | `dkadi`, `ai-agent`, `ansible` all `0700` |
| sudo | `/usr/bin/sudo.ws` |
| Services | `ssh`, `wazuh-agent`, `qemu-guest-agent`, `docker`, `e2b-nft-guard` all `active` |

On Grey afterwards: `qm list` showed `ubuntu-dev`, `splunk-siem` and `e2b-01` running; `free -g` read 44 GiB used of 62 with 18 GiB available; `local-lvm` was 52.30% used with 397,033,979 KiB available.

## Left open

- The 2026-11-25 trial review decides whether `e2b-01` stays. If it does, it gets `onboot=1`, a boot-time `docker compose up`, `monitoring-exporters` and `fleet-updates`.
- Starting every stopped Grey guest at once (26 GiB) would overcommit Grey with `e2b-01` running.
