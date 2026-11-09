# Blue Chassis Swap and Green Memory Upgrade

**Created:** 2026-11-09  
**Last updated:** 2026-11-09

**Implementation date:** 2026-11-09  
**Status:** Complete, with open items  
**Affected hardware:** `blue-server` and `green-server`

## Scope

I bought a second-hand Lenovo ThinkCentre M920q that came with an 8 GB SO-DIMM and an M.2 drive. I moved `blue-server` off its ThinkCentre M910q onto the M920q by moving Blue's drives across, and I put the 8 GB module in Green's empty slot. The M910q is now kept for spare parts.

Blue had been the weakest node: an i5-7500T with four cores. The M920q carries an i5-8500T with six, the same processor as Purple, Green and Red. Green had run on a single 8 GB module since I removed its faulty SK Hynix on 2026-10-28.

## Starting state

| Node | Chassis | CPU | Memory | Usable |
|---|---|---|---|---:|
| Blue | ThinkCentre M910q, BIOS `M1AKT35A`, I219-LM (2) | i5-7500T, 4 cores / 4 threads | Samsung 2 GB + SK Hynix 4 GB, 2133 MT/s | 5.68 GiB |
| Green | ThinkCentre M920q `10RRS0LN00`, BIOS `M1UKT45A` | i5-8500T, 6 / 6 | Micron 8 GB in `ChannelA-DIMM0`, `ChannelB-DIMM0` empty | 7.60 GiB |

Blue ran CTs 100 `ansible-01`, 104 `monitor-01`, 107 `docker-network` and 108 `docker-blue`. Green held no guests. The cluster was quorate with five votes.

## Step 1: Shut both nodes down

I shut each node down through the Proxmox API, `pvesh create /nodes/<node>/status --command shutdown`, Green first. Green's boot ended at 7:08:05 AM. On Blue, `pve-guests` began stopping its containers at 7:08:34 AM, the last `vzshutdown` ended at 7:08:49 AM, and the boot ended at 7:09:01 AM. With both down, `pvecm status` on Grey reported `Total votes: 3` and `Quorate: Yes`.

Blue's four containers are where Executor, ssh-mcp, the UniFi MCP gateway, Nginx Proxy Manager, Grafana alerting and Ansible run, so all of them were down from 7:08 AM.

## Step 2: Hardware changes

- **Green:** I installed the 8 GB module in `ChannelB-DIMM0`.
- **Blue:** I moved the Samsung MZVLW256HEHP-000L7 boot NVMe and the WDC WD5000LPVX-08V0TT5 HDD into the M920q, along with Blue's 2 GB and 4 GB modules.
- **M910q:** stripped of its drives and memory and kept for spare parts.
- **The M920q's M.2 drive** is not installed in either node. I have not recorded its model or capacity.

## Step 3: Green readback

Green booted at 7:22:23 AM and rejoined at four votes. `dmidecode -t 17` and Proxmox reported:

| Slot | Module | Rank | Speed |
|---|---|---|---|
| `ChannelA-DIMM0` | Micron `8ATF1G64HZ-2G6E1`, 8 GB | 1 | 2666 MT/s |
| `ChannelB-DIMM0` | Micron `8ATF1G64HZ-2G6E1`, 8 GB | 1 | 2666 MT/s |

Proxmox reports 15,830 MiB, 15.46 GiB, the same as Purple and Red. The new module is the same part as the one already in Green, so Green runs dual-channel again.

A 12 GiB `memtester` pass started on Green at 8:28:52 AM, locked across both modules. The result is in [Memory test](#memory-test).

## Step 4: Blue booted without a network

Blue's first boot in the M920q began at about 7:36 AM. It reached a login prompt but had no network: the switch port showed link and no client registered on it. Proxmox pins the name `nic0` to the old NIC's MAC address, so the M920q's I219-LM came up as `eno2`, and `vmbr0` had no physical port. Once that was fixed, the cable sat for one boot in a port carrying the IoT VLAN. The diagnosis, the fix and the verification are in [blue-server Unreachable After Chassis Swap](../../../Compute/Galaxy/Documentation/Troubleshooting/blue-server%20Unreachable%20After%20Chassis%20Swap%20-%202026-11-09.md).

Blue came up on its network at 8:19:21 AM on Bane Switch POE port 3. Blue's containers were down for about 71 minutes in total.

## Step 5: Blue readback

| Check | Result |
|---|---|
| Chassis | `dmidecode` reports LENOVO ThinkCentre M920q, product `10RRS0LN00`, BIOS `M1UKT45A` dated 07/11/2019 |
| CPU | Intel Core i5-8500T @ 2.10GHz, 6 cores / 6 threads |
| Memory | Samsung `M471A5644EB0-CPB` 2 GB in `ChannelA-DIMM0` and SK Hynix `HMA851S6AFR6N-UH` 4 GB in `ChannelB-DIMM0`, both 2133 MT/s; Proxmox reports 5,761 MiB, 5.63 GiB |
| Storage | `nvme0n1` Samsung MZVLW256HEHP-000L7, 238.5 GiB; `sda` WDC WD5000LPVX-08V0TT5, 465.8 GiB |
| NIC | Intel I219-LM (7) `[8086:15bb]` at `00:1f.6`, driver `e1000e`, named `nic0`, 1000 Mb/s, link detected |
| Wireless | Intel Cannon Lake CNVi Wi-Fi at `00:14.3`, `wlo1`, unconfigured |
| Addresses | `vmbr0.70` `192.168.70.12/24`, `vmbr0.71` `192.168.71.12/24` |
| Cluster | `pvecm status` `Total votes: 5`, `Quorate: Yes`; `corosync-cfgtool -s` shows both links connected to all four peers |
| Guests | CTs 100, 104, 107 and 108 running, all `onboot: 1` |
| Services | On `docker-blue`: `executor-v2`, `ssh-mcp`, `mcp-unifi-network` and `docker-mcp-gateway` healthy. `https://executor.alphasecunited.com/mcp` answered `401`, the expected response without a token |

Usable memory dropped from 5.68 GiB to 5.63 GiB on the same two modules. The M920q firmware reserves more than the M910q did.

The M920q's hardware clock was 4 hours 5 seconds behind. chronyd logged `System clock wrong by 14404.838827 seconds` and stepped the clock at 8:17:14 AM. The boot at 8:19:21 AM started with the correct time, so the hardware clock now holds it. The new chassis's journal entries before 8:17 AM read 4 hours early.

## Step 6: nic0 offloads on Blue

Blue's new NIC is the I219-LM whose transmit hang took Purple off the network on 2026-10-14, and `ethtool -k nic0` read TSO, GSO and GRO all `on`. The M910q's I219-LM (2) had TSO forced off by its driver, which is why Blue never carried the workaround.

I copied Blue's `/etc/network/interfaces` to [`Backups/blue-server-interfaces-2026-11-09`](../../../../Backups/blue-server-interfaces-2026-11-09) and added the same line Purple, Green and Red carry:

```text
iface nic0 inet manual
	post-up /sbin/ethtool -K nic0 tso off gso off gro off
```

I applied it live with `/sbin/ethtool -K nic0 tso off gso off gro off`, exit 0. Afterwards `ethtool -k nic0` read `tcp-segmentation-offload: off`, `generic-segmentation-offload: off` and `generic-receive-offload: off`. `ifquery nic0` returned the new stanza, and the link stayed at 1000 Mb/s. Corosync stayed at five votes, and Blue reached Grey on TCP 8006 (`200`) and 22. The backup was copied straight off the host, so no copy remains on Blue. I have not yet rebooted Blue to confirm the line holds across a boot.

## Step 7: UniFi client record

UniFi kept the `blue-server` client record, with its fixed IP `192.168.70.12`, on the M910q's MAC address. The M920q's NIC registered as a new, unnamed client. Through the controller's API I renamed the old record `blue-server-old-chassis` with `use_fixedip` off. On the new record I set the name `blue-server`, `use_fixedip` on, `fixed_ip` `192.168.70.12` and network MGMT-A. Both writes returned `rc: ok`. The readback showed the new record with that name and reservation on MGMT-A, last seen on Bane Switch POE port 3. Blue's address is static on the node, so the reservation documents it rather than assigning it. The `blue.alphasecunited.com` A record in [local DNS](../../../Network/UniFi/Configuration/local-dns.md) still points at `192.168.70.12` and needed no change.

## Memory test

Pending. The `memtester 12G 1` run on Green started at 8:28:52 AM and writes to `/root/memtester-2026-11-09.log`.

## Result

| Node | CPU | Cores / threads | Usable memory |
|---|---|---|---:|
| Blue | i5-8500T | 6 / 6 | 5.63 GiB |
| Green | i5-8500T | 6 / 6 | 15.46 GiB |

Galaxy now has 32 physical cores, 40 hardware threads and 114.73 GiB of usable memory. Four of the five nodes are M920q systems on BIOS `M1UKT45A`, and Grey is the only one that is not.

## Open items

- I need two 8 GB DDR4 SO-DIMMs for Blue. It is the only node under 15 GiB.
- I still need the spare M.2 drive's model and capacity, and a SMART read before it holds anything.
- `blue-server` still has `/usr/local/lib/systemd/network/50-pmx-nic1.link` and an `iface nic1 inet manual` stanza that match no interface on the M920q. They are harmless and I left them.
- Reboot Blue at its next maintenance window and confirm `ethtool -k nic0` still reads TSO, GSO and GRO off.
- The Galaxy cluster and homelab overview diagrams still show Blue as an i5-7500T with 5.68 GiB and Green at 7.60 GiB.

Follow-up is tracked in the [Galaxy TODO](../../../Compute/Galaxy/Documentation/TODO.md#blue-chassis-swap-follow-ups).
