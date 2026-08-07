# Galaxy Game-01 LXC Deployment

**Created:** 2026-08-07  
**Last updated:** 2026-08-07

**Implemented:** 2026-08-07  
**Owner:** Infrastructure / Compute / Galaxy  
**Status:** Complete. LXC 123 `game-01` running on `green-server`, baselined, on SERVERS-A VLAN 80.

I built a dedicated guest to host self-managed game servers. This record covers the guest: placement, specification, network and baseline. The platform that runs on it is [Game Servers](../../../../Platforms/Game%20Servers/README.md).

## Placement

`green-server` was empty. It joined the cluster on 2026-07-31 and carried no guests, and `free -h` reported 13 GiB of its 16 GiB available with `local-lvm` at 0.00 percent of 141 GiB.

I checked the alternatives before choosing it:

| Node | Available memory before this change | Why not |
|---|---|---|
| grey-server | 19 GiB of 62 GiB, 1.5 GiB swap already in use | A Minecraft heap pre-commits with `-Xms`, so it is real resident memory, not paper allocation. Adding 10 GiB to a node already swapping puts Coolify, Supabase, Wazuh and Splunk at risk. |
| purple-server | VM 122 holds 12 GiB of 15.46 GiB | No room. |
| blue-server | 5.68 GiB total since the 2026-07-31 module move | No room. |
| red-server | 12 GiB of 15 GiB free | Workable, but `media-01` spikes during transcodes and green was genuinely idle. |

Green's cost is single-thread speed. It is an i5-8500T that boosts to 3500 MHz against grey's Ryzen 7 3700X. Minecraft ticks on one thread per server, so chunk generation on a 231-mod pack is slower here than it would be on grey. I took the isolation over the clock speed.

## Preflight

`Proxmox-Trunk` is an exclusion list, and its four excluded networks are Management, IoT (20), Trusted (10) and Secure (50). SERVERS-A (VLAN 80) is not among them, so the trunk carries it. All five Proxmox nodes sit on ports using that profile: Bane Switch POE ports 2, 3, 4 and 14, and Jango Switch port 3.

I checked this first on purpose. The `edge-01` move on 2026-08-07 caused a three-minute outage because the trunk did not carry the VLAN and ARP failed at layer 2.

Green had no LXC template cached, so I downloaded the current one. The fleet standard is Debian 13, and the available build is now `13.6-1` rather than the `13.1-2` used for `monitor-01`:

```bash
pveam download local debian-13-standard_13.6-1_amd64.tar.zst
```

`pvesh get /cluster/nextid` returned 103. I took 123 instead, following the precedent set for `kasm-01`, which took the next ID in the 1xx sequence rather than the lowest free one.

## Creation

```bash
pct create 123 local:vztmpl/debian-13-standard_13.6-1_amd64.tar.zst \
  --hostname game-01 \
  --cores 6 --memory 12288 --swap 2048 \
  --rootfs local-lvm:80 \
  --net0 name=eth0,bridge=vmbr0,tag=80,firewall=1,ip=192.168.80.30/24,gw=192.168.80.1 \
  --nameserver 192.168.80.1 \
  --unprivileged 1 \
  --features nesting=1,keyctl=1 \
  --ostype debian \
  --onboot 1 \
  --start 1
```

`nesting=1,keyctl=1` are both required for Docker in an unprivileged container. High availability stays disabled: the rootfs is on node-local `local-lvm`, and enabling HA without a strict node-affinity rule is what stranded CT 107 and CT 108 on 2026-07-20.

Swap is 2 GiB as an OOM cushion only. A Java heap that pages is worse than one that fails, so if that swap is ever actively used the heap is too large.

## Address

`192.168.80.30` was silent to ICMP from `alpha-prod-01` before the build. It was not entirely unused history: `ansible-01` held three stale `known_hosts` entries for it at lines 76 to 78, so something occupied this address previously. I removed them with `ssh-keygen -R` and confirmed the key now offered matches the ed25519 host key generated when CT 123 was created.

VLAN 80 has no static band below its DHCP pool. The pool is `.6` to `.254`, and the existing hosts at `.10`, `.20` and `.118` are all in-guest statics inside it with no controller reservation. `.30` follows that existing pattern. Narrowing the pool the way DMZ 30 was narrowed would be the tidier fix, and it is not part of this change.

## Baseline

Applied per the Linux host baseline standard before the host carried a workload. The minimal Debian 13 template ships without `sudo`, so `/etc/sudoers.d` does not exist and the first pass failed at the drop-in write. Installing `sudo locales curl ca-certificates gnupg` first fixed it.

Verification, all against the running host:

| Check | Result |
|---|---|
| `id dkadi` | in `sudo` group |
| `sudo -n true` as `dkadi` | exit **1**, so no `NOPASSWD` drop-in |
| `sudo -n true` as `ansible` and `ai-agent` | exit 0 for both |
| `sudo -l -U dkadi` | `(ALL : ALL) ALL`, no `NOPASSWD` |
| `/etc/sudoers.d/` | `90-ansible` and `90-ai-agent` at 0440, both `parsed OK`, no `90-dkadi` |
| `sshd -T` | `permitrootlogin no`, `pubkeyauthentication yes`, `passwordauthentication no`, `kbdinteractiveauthentication no` |
| `passwd -S root` | `L` |
| Time and locale | `America/New_York`, clock synchronized, `LANG=en_US.UTF-8` |
| `/etc/cloud/cloud-init.disabled` | present |
| Controller access | `ssh ansible@192.168.80.30` from `ansible-01` succeeds by key and `sudo -n` returns 0 |

This host meets the standard as written. Four existing hosts still give `dkadi` passwordless sudo, and this is not one of them.

### Two deviations, both deliberate

**`dkadi` has two approved keys here, not three.** `ssh-key-automation` holds exactly two human identities, `jedi-pc` and `mac`, and I hold three public keys on record: `Jedi PC`, `mac-m3` and `ansible`. The third key in `dkadi`'s `authorized_keys` on the reference host `docker-network` is `SHA256:UtepyFu+HiAXaFy88mnPAS1kOYaknIGW5w3SuC2rjF8`, carries no comment, and matches no identity record anywhere. I did not copy a key I cannot attribute onto a new host. Identifying or retiring it is separate work.

**`ai-agent` exists with no SSH key.** The account, its password and its `NOPASSWD` drop-in are all in place, and `/home/ai-agent/.ssh/authorized_keys` exists at 0600 and is empty. No `ai-agent` key has been issued anywhere on the fleet, and minting one is an identity decision about which device owns it and what `from=` address it carries. With `PasswordAuthentication no`, the account cannot be reached over SSH until a key is added.

## Resulting state

| Setting | Value |
|---|---|
| CTID and hostname | 123, `game-01` |
| Node | `green-server` |
| OS | Debian GNU/Linux 13 (trixie), from template 13.6-1 |
| vCPU / Memory / Swap | 6 / 12288 MiB / 2048 MiB |
| rootfs | `local-lvm:vm-123-disk-0`, 80G |
| Network | `eth0` on `vmbr0`, VLAN 80, `192.168.80.30/24`, gateway `192.168.80.1`, firewall enabled |
| Unprivileged | yes |
| Features | `nesting=1,keyctl=1` |
| On boot | yes |
| High availability | disabled |

Green after the build: 8.2 GiB of 15 GiB available with the game server idle, swap `0B` used, `local-lvm` at 4.61 percent, guest rootfs 4.2 GB of 79 GB.

## Inventory drift found while working

`pvesh get /cluster/resources` returns no VMID 111, but `Operations/Inventory/Galaxy/VMs.md` still lists VM 111 `fedora-dev` as a stopped guest on grey. The guest no longer exists on the cluster. I have not edited that row, because confirming whether it was deleted deliberately is separate from this change.
