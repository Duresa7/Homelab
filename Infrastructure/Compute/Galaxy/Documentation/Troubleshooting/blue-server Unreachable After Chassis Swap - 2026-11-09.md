# blue-server Unreachable After Chassis Swap

**Created:** 2026-11-09  
**Last updated:** 2026-11-09

**Investigated:** 2026-11-09  
**Owner:** Galaxy / blue-server networking  
**Status:** Resolved

## Symptom

I moved Blue's boot NVMe from its ThinkCentre M910q into a ThinkCentre M920q ([chassis swap](../../../../Hardware/Documentation/Change%20Records/Blue%20Chassis%20Swap%20and%20Green%20Memory%20Upgrade%20-%202026-11-09.md)). The M920q powered on, but Blue never came back. Proxmox on Grey listed `blue-server offline`, `pvecm status` held at `Total votes: 4`, and Grey's neighbour entry stayed `192.168.70.12 dev vmbr0.70 INCOMPLETE`. Blue's CTs 100, 104, 107 and 108 stayed unreachable with it.

UniFi showed Bane Switch POE port 3 `up` at 1000 Mb/s full duplex, but no client on it. The `blue-server` client record, fixed IP `192.168.70.12`, was last seen at 7:14 AM, which was the old chassis.

On Blue's console, `vmbr0.70` held `192.168.70.12/24` and `vmbr0.71` held `192.168.71.12/24`, both `UP,LOWER_UP`. Pinging Grey and `1.1.1.1` from Blue failed:

```text
From 192.168.70.12 icmp_seq=1 Destination Host Unreachable
```

## Cause 1: nic0 is pinned to the old NIC's MAC address

Every Galaxy node runs PVE 9.2.26, whose installer writes a systemd link file that names the onboard NIC `nic0` by MAC address:

```text
/usr/local/lib/systemd/network/50-pmx-nic0.link
[Match]
MACAddress=<REDACTED_BLUE_M910Q_NIC_MAC>
Type=ether

[Link]
Name=nic0
```

`/etc/network/interfaces` builds the bridge on that name: `bridge-ports nic0`. The M920q's I219-LM has a different MAC, so the file no longer matched. The kernel log on the first two M920q boots shows the NIC stopping at its default name:

```text
e1000e 0000:00:1f.6 eno2: renamed from eth0
```

No `nic0` existed, so `vmbr0` had no physical port. The bridge still read `UP` because the four containers' `veth` interfaces are attached to it, which is why the VLAN interfaces looked healthy while nothing left the host.

## Fix 1

On Blue's console, in `/usr/local/lib/systemd/network/`, I pointed the existing pin at the new NIC and rebuilt the initramfs images:

```text
sed -i "s/^MAC.*/MACAddress=$(cat /sys/class/net/en*/address)/" 50-pmx-nic0.link
update-initramfs -u -k all
```

`sed` printed no error, so the `en*` pattern matched exactly one interface. `update-initramfs` regenerated the images for `7.0.14-28-pve` and the older kernels, each with `No /etc/kernel/proxmox-boot-uuids found, skipping ESP sync.`

The folder also holds `50-pmx-nic1.link`. Before rebooting I confirmed the bridge uses `nic0`: `grep -n bridge-ports /etc/network/interfaces` returned `7: bridge-ports nic0`. After the reboot the kernel log showed the pin applied:

```text
e1000e 0000:00:1f.6 eno2: renamed from eth0
e1000e 0000:00:1f.6 nic0: renamed from eno2
```

`ls /sys/class/net` listed `nic0`, `vmbr0`, `vmbr0.70`, `vmbr0.71` and `wlo1`, the M920q's unconfigured Wi-Fi.

## Cause 2: an IoT access port

Blue still did not answer. Bane port 3 now read `up: False`, and a new wired client had appeared on Jango Switch port 2 at 8:12:49 AM in the IoT network. That was Blue's new NIC, with its cable in a different port. Port 2 uses the `IoT` port profile: native VLAN 20 and `tagged_vlan_mgmt: block_all`. Blue's addresses are on tagged VLANs 70 and 71, so the switch dropped them.

Every Galaxy node port uses the `Proxmox-Trunk` profile: Bane Switch POE ports 2 to 5 and 14, and Jango Switch port 3, which was empty.

## Fix 2

The cable went back to Bane Switch POE port 3, `Proxmox-Trunk`. No UniFi configuration changed.

## Verification

- Blue booted at 8:19:21 AM with `nic0` renamed from `eno2`.
- UniFi showed the new client on Bane Switch POE port 3, IP `192.168.70.12`, VLAN 70, network MGMT-A.
- Grey's `pvesh get /nodes` listed `blue-server online` with 6 CPUs, and `pvecm status` read `Total votes: 5`, `Quorate: Yes`.
- `corosync-cfgtool -s` on Blue showed both links connected to nodes 1, 2, 4 and 5.
- `ethtool nic0` on Blue read `Speed: 1000Mb/s` and `Link detected: yes`.
- `pct list` showed CTs 100, 104, 107 and 108 running.
- From Blue, `https://192.168.70.10:8006/` returned `200`, and TCP 22 on Grey accepted a connection.

ICMP between Galaxy nodes is filtered. Red cannot ping Grey or Green either, so a failed node-to-node ping is not a test of reachability. Use TCP 8006 or 22 instead.

## Avoiding it next time

Before moving a node's drive into another chassis:

1. Read the new chassis's NIC MAC address, from a label or its firmware, and write it into `50-pmx-nic0.link` before the move. Otherwise, plan for a console session on first boot.
2. Plug the node into a `Proxmox-Trunk` port.

The same applies to replacing a node's motherboard or NIC.
