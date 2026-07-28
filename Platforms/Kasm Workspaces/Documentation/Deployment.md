# Kasm Workspaces Deployment

**Created:** 2026-07-24  
**Last updated:** 2026-07-28

**Implemented:** 2026-07-24  
**Owner:** Platforms / Kasm Workspaces  
**Host:** `kasm-01`, VM 122 on `purple-server`, `192.168.78.10`  
**Status:** Complete. Kasm Workspaces 1.19.0 Community Edition and session isolation are verified except for one pending Management Access VPN client-path test.

## Current State on 2026-07-28

I moved VM 122 to `purple-server` and its 100 GiB disk to the `ssd-lvm2` thin pool on the Samsung 850 EVO. The control plane now uses LAB-MGMT VLAN 78 at `192.168.78.10/24`.

Three addressless guest NICs carry VLANs 74, 77, and 79. Docker macvlan networks `lab74`, `lab77`, and `lab79` place sessions into their matching UniFi zones. A persistent systemd unit creates the host shims before Docker. All eight Kasm containers, the three networks, their shim routes, the agent network report, the health endpoint, and administrator authentication survived a full reboot.

I created the `Lab Sessions` group with a 3,600-second session limit, upload enabled, and download, clipboard, seamless clipboard, and persistent profiles disabled. Every lab workspace needs a Docker Run Config Override that declares both its network and resolver. The completed layout, exact recipes, containment results, and Proton operating rule are in [Kasm Session Isolation](Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md).

I updated the existing `Host kasm-01` entry in Jedi PC's SSH configuration to `192.168.78.10` and confirmed `ssh -G kasm-01` resolves that address with user `<YOUR_ADMIN_USERNAME>`.

The original build history below records the 2026-07-24 deployment on Grey and VLAN 80. Those values explain the starting point and are not the current address or placement.

## Scope

I deployed the Kasm platform & nothing else. No lab VLAN NICs, no workspace images, no reverse proxy, no session policies. I wanted a working control plane on a baselined host before adding the isolation plumbing, because the previous build failed by doing all of it at once.

This replaces the lab I tore down on 2026-07-23. That teardown destroyed ten VMs and every Proxmox object the earlier version had created.

## Why Ubuntu 24.04 rather than Debian 13

My fleet template standard is Debian 13 (trixie), which Kasm doesn't support. Kasm 1.19.0 lists Ubuntu 22.04/24.04, Debian 11/12, Oracle Linux 8/9, RHEL 8/9, AlmaLinux 8/9, & Rocky Linux 8/9. Debian 13 appears on none of those lines.

So I cloned template 9000 `ubuntu-cloud-template`, which runs Ubuntu 24.04.4 LTS & already carries cloud-init plus a `tag=80` NIC. Guest OS confirmed after boot as `PRETTY_NAME="Ubuntu 24.04.4 LTS"`.

## VM specification

I full-cloned template 9000 to VMID 122 on `ssd-lvm1`, then set the hardware.

| Setting | Value | Reason |
| --- | --- | --- |
| VMID / name | 122 / `kasm-01` | 122 was free cluster-wide; follows the 1xx guest sequence after `edge-01` at 121 |
| Node | `grey-server` | 16 cores & 27 GiB RAM free at build time; holds the other VLAN 80 servers |
| vCPU | 4 | Kasm's floor is 2 cores. Each default session wants 2 more |
| Memory | 8 GiB | Kasm's floor is 4 GiB. Default workspaces request 2768 MB per session |
| Disk | 100 GiB on `ssd-lvm1` | Kasm's floor is 50 GiB SSD. Workspace images are large & pull on demand |
| Swap | 4 GiB file at `/mnt/Kasm.swap` | Kasm's docs say a host with ample RAM still hits stability problems without swap |
| NIC | `virtio`, `vmbr0`, `firewall=1`, `tag=80` | VLAN 80 SERVERS-A. `firewall=1` matches `app-01`; it's inert because no `122.fw` rules file exists |
| IPv4 | `192.168.80.30/24`, gateway `192.168.80.1` | Static, continuing the `.10`/`.20` pattern on VLAN 80. Confirmed unused by ping before allocation |
| DNS | `1.1.1.1`, `8.8.8.8` | Matches `app-01` on the same VLAN |
| Firmware | OVMF / q35, `virtio-scsi-single`, agent enabled, `onboot=1` | Inherited from the template |

`grey-server` ran `pve-manager/9.2.5/20242970da7fbcef` on kernel `7.0.14-6-pve` during the build.

### The cloud-init trap I had to clear first

Template 9000 carried `cicustom: user=local:snippets/ssh-harden.yaml`. In Proxmox, a `cicustom` `user=` entry replaces the generated user-data outright, so `ciuser`, `cipassword`, & `sshkeys` get ignored. That snippet contains four `sed` lines against `sshd_config` & a service restart. It creates no user & installs no keys.

Cloning as-is would have produced a VM with `PasswordAuthentication no`, no authorized keys, & no `<YOUR_ADMIN_USERNAME>` account. The only way in would have been the hypervisor console. I deleted `cicustom` & used native cloud-init instead, then applied the hardening over SSH afterward where I could verify the result.

## Host baseline

I applied the [Linux Host Baseline Standard](../../../Security/Hardening/Linux-Host-Baseline-Standard.md) before installing anything.

Cloud-init installed the four fleet public keys & created `<YOUR_ADMIN_USERNAME>` in `sudo`. I then patched the host, added `qemu-guest-agent`, wrote a validated `/etc/sudoers.d/90-<YOUR_ADMIN_USERNAME>` drop-in, wrote `/etc/ssh/sshd_config.d/99-hardening.conf`, locked root, & set timezone & locale.

The standard's text still lists three authorized keys. The live fleet carries four, & `app-01` plus `docker-network` both match that set exactly, so I installed four. The standard needs a correction; that's tracked separately.

### Verification checklist results

Every check ran over SSH from `ansible-01` after the sshd restart.

| Check | Result |
| --- | --- |
| `id <YOUR_ADMIN_USERNAME>` includes `sudo` | `uid=1000(<YOUR_ADMIN_USERNAME>)`, group `27(sudo)` |
| `sudo -n true` | Succeeds |
| `sshd -T` | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no` |
| `ssh-keygen -lf ~/.ssh/authorized_keys` | Four fingerprints, matching `app-01` |
| `passwd -S root` | `root L` (locked) |
| Console recovery password for `<YOUR_ADMIN_USERNAME>` | `<YOUR_ADMIN_USERNAME> P` (set, inherited from the template) |
| Timezone & locale | `America/New_York (EDT, -0400)`, `LANG=en_US.UTF-8` |
| Key-only SSH | Password attempt returns `Permission denied (publickey)` |
| `qemu-guest-agent` | `active` |

The four installed key fingerprints:

```text
SHA256:UtepyFu+HiAXaFy88mnPAS1kOYaknIGW5w3SuC2rjF8  (no comment)
SHA256:QyNF8ipQ5F/1KV69opH2QHuVVclpfNnZFGhDYZL38rM  mac-air3-<YOUR_ADMIN_USERNAME>
SHA256:7sgrdr0LDOx+QyFwDZSsOOV7PTrbqFtG9KkK0Rn6qc8  ansible-control
SHA256:pcjlugUJER60YblfoAOfzZYKHJ1pHVTeqGm7Vwquj/4  jedi-pc
```

## Kasm installation

I verified the download before running it as root. Kasm publishes a checksum at the tarball URL plus `.sha256sum`, & the file I pulled matched:

```text
1d2e41b0775c458beb0396143789f080c1c835498fb45a78b4e0794cde7a5b7c  kasm_release_1.19.0-latest.tar.gz
```

The tarball is 10,517,241 bytes & its `install.sh` reports `KASM_VERSION="1.19.0"`. Kasm's downloads page showed a truncated hash that didn't match the start of this digest; the published `.sha256sum` file is the value I trusted, & it agreed with what I computed on the host.

Commands, run on `kasm-01`:

```bash
cd /tmp
curl -O https://kasm-static-content.s3.amazonaws.com/kasm_release_1.19.0-latest.tar.gz
tar -xf kasm_release_1.19.0-latest.tar.gz
sudo bash kasm_release/install.sh --role all --accept-eula --swap-size 4096 --ignore-dep-failures
```

Flag choices: `--role all` puts every component on one host, which is what Community Edition's 5-session cap justifies. `--swap-size 4096` creates the swap file the docs ask for, since the Ubuntu cloud image ships with none. `--ignore-dep-failures` is what Kasm's own help text recommends for non-interactive installs that may hit missing optional dependencies such as rclone, WireGuard, v4l2loopback, or fuse. I accepted the EULA after confirming the instruction.

I did not pass `--default-images`, so no workspace images downloaded. The catalog is seeded & each image pulls the first time I launch it.

The installer pulled Docker 29.6.2 & containerd 2.2.6 from `download.docker.com`, confirmed TCP 443 & 3389 were free, created the 4 GiB swap file, & generated a self-signed certificate at `/opt/kasm/1.19.0/certs/kasm_nginx.*`. Install directory is `/opt/kasm/1.19.0`.

## Post-install verification

All eight containers reported healthy. `kasm_proxy` exposes no healthcheck, which is normal.

```text
kasm_agent              Up (healthy)
kasm_api                Up (healthy)
kasm_db                 Up (healthy)
kasm_guac               Up (healthy)
kasm_manager            Up (healthy)
kasm_proxy              Up
kasm_rdp_gateway        Up (healthy)
kasm_rdp_https_gateway  Up (healthy)
```

Service checks:

- `GET https://192.168.80.30/` returns HTTP 200.
- `GET https://192.168.80.30/api/__healthcheck` returns `{"ok": true}`.
- `POST /api/authenticate` as `admin@kasm.local` returns a session token, so the generated administrator credential works.
- Swap active: `/mnt/Kasm.swap`, 4 GiB, in `swapon --show`.
- Disk after install: 13 GiB used of 96 GiB.

I proved SSH from my workstation, not only from the jump host:

```text
$ ssh kasm-01
kasm-01
Ubuntu 24.04.4 LTS
```

That connection used the `jedi-pc` Ed25519 identity at `SHA256:pcjlugUJER60YblfoAOfzZYKHJ1pHVTeqGm7Vwquj/4`. I added a `kasm-01` host entry to `~/.ssh/config` on Jedi PC pointing at `192.168.80.30` as `<YOUR_ADMIN_USERNAME>`.

## Credentials

The installer generated passwords for `admin@kasm.local`, `user@kasm.local`, the `kasmapp` database account, the manager token, and the service registration token. None of those values are recorded in this repository. I retained them outside the repository. Administrator password rotation and storage remain my responsibility.

## Cluster state during the build

Galaxy was quorate throughout. `purple-server` was offline for its planned boot NVMe replacement, which left 3 of 4 votes against an expected 3, so the cluster held quorum with no margin to spare. Corosync showed nodeid 2 `disconnected` on both `LINK ID 0` (`192.168.70.10`) & `LINK ID 1` (`192.168.71.10`), matching a powered-down node rather than a link fault. All work in this record happened on `grey-server`, so the offline node never touched it. The failed device is tracked in [Purple NVMe Reliability Failure](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md).

## State on 2026-07-25

I rechecked the host the morning after the build, from `grey-server` through `qm guest exec 122`, because I'd used it the night before.

All 8 containers were still up, uptime 18h 08m, `GET https://127.0.0.1/` returned 200, & `/api/__healthcheck` returned `{"ok": true}`. The RDP gateway reported `Active Sessions: {}`, so nothing was running. Memory sat at 2.1 GiB of 7.7 GiB. Swap was barely touched at 768 KiB of 4 GiB.

Disk moved from 13 GiB to 26 GiB of 96 GiB. That's three workspace images I pulled on 2026-07-24 by launching the workspaces to see how the product works:

```text
kasmweb/forensic-osint:1.19.0-rolling-daily   10.3GB
kasmweb/vs-code:1.19.0-rolling-daily           6.42GB
kasmweb/terminal:1.19.0-rolling-daily          4.83GB
```

These were test launches on VLAN 80 with no isolation in place, which is fine for a VS Code container & a terminal. I'm not running anything hostile until the lab NICs exist. The `forensic-osint` image is the one to be careful with, since OSINT work means live Internet from a session that currently egresses through SERVERS-A rather than through Proton on VLAN 74.

`kasm_rdp_gateway` shows `RestartCount: 2` & restarted at 2026-07-25 02:49 EDT while the other seven containers held 18 hours. Its current log is clean: health checks return `{'ok': True}` & it's registering `['proxy', 'kasm-01']` as expected. I'm noting the restart rather than acting on it. If it climbs past 2 without a session to explain it, that's a real fault to chase.

## Follow-up State

- I completed the VLAN 74, 77, and 79 NICs, macvlan networks, shim routes, and explicit UniFi containment rules on 2026-07-28.
- I completed the harmless-container acceptance matrix before allowing a live sample.
- Decide whether `kasm.<YOUR_BASE_DOMAIN>` goes through Nginx Proxy Manager at `192.168.85.2`, which would replace the self-signed certificate warning with the wildcard certificate.
- I disabled the stale VLAN 77 DHCP DNS option on 2026-07-28. UniFi retains `192.168.77.10` as an inactive value, so the network no longer advertises it.
- Register `kasm-01` in the SSH Manager inventory. The MCP exposes no add-server tool & I couldn't locate its inventory file, so this stays manual.
