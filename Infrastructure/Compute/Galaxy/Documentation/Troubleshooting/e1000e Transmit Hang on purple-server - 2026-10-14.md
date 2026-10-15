# e1000e Transmit Hang on purple-server

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Investigated:** 2026-10-15; outage began 2026-10-14  
**Owner:** Galaxy / purple-server networking  
**Status:** Resolved, with preventive actions open

## Symptom and impact

At about 11:44:50 PM EDT on 2026-10-14, `purple-server` (`192.168.70.11`) and its running VMs 121 `edge-01` and 401 `alpha-prod-01` lost connectivity. Both Corosync links failed together, Purple lost quorum, and pmxcfs became read-only. The other four nodes stayed quorate. The Internet edge, Minecraft and both TeamSpeak paths were unavailable for about 54 minutes. After the reboot, Minecraft logins were separately most likely impaired from its 12:37 AM start at boot until external DNS recovered at 12:58:32 AM, despite working server-list pings. Nobody tried an authenticated join. The [incident report](../../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md) holds the full timeline and impact.

## Log signature and recognition

The first error was at 11:44:51 PM EDT:

```text
2026-10-14T23:44:51-04:00 purple-server kernel: e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang:
                                                  TDH                  <50>
                                                  TDT                  <82>
                                                  next_to_use          <82>
                                                  next_to_clean        <50>
                                                buffer_info[next_to_clean]:
                                                  time_stamp           <12e2a3af4>
                                                  next_to_watch        <51>
                                                  jiffies              <12e2a3f80>
                                                  next_to_watch.status <0>
                                                MAC Status             <80083>
                                                PHY Status             <796d>
                                                PHY 1000BASE-T Status  <3800>
                                                PHY Extended Status    <3000>
                                                PCI Status             <10>
```

The [verbatim journal capture](../../../../../Security/Incidents/Galaxy/Evidence/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14/Logs/S01%20Hang,%20Membership%20and%20Power-Key%20Recovery%20-%202026-10-15.md) includes both complete hang blocks, the Corosync event sequence and power-key messages.

I found 1,519 repeats at two-second intervals with TDH/TDT stuck at `50/82`, continuing into shutdown at 12:35:27 AM. There was no `NETDEV WATCHDOG`, transmit-timeout, `Reset adapter` or `NIC Link is Down` line. The PHY stayed at 1000 Mbps, and Bane Switch POE Port 2 showed no link-down. Its later client disconnections were idle timeouts. A live switch port therefore did not establish that Purple could transmit.

At 12:35:27 AM, 50 minutes 36 seconds after the first block, TDH `<50>`, TDT `<82>`, next_to_watch `<51>` and the stuck descriptor's time_stamp `<12e2a3af4>` were unchanged. Only `jiffies` advanced from `<12e2a3f80>` to `<12e589301>`. This directly supports the stuck-ring interpretation.

Grey also logged `Token has not been received in 3712 ms` at 11:44:53 PM and `Failed to receive the leave message. failed: 2` at 11:45:01 PM. Purple formed membership `2.2ca` with only member `2`; the other four nodes formed `1.2ca` with members `1 3 4 5` and stayed quorate. Grey recorded rejoin membership `1.2d3` at 12:36:43 AM.

For recurrence checks, I can inspect `journalctl -k -b` and the preceding boot for `Hardware Unit Hang`, check `ethtool nic0` for link state, and inspect `ethtool -S nic0` for errors, `tx_timeout_count` and `tx_restart_queue`. I need to compare those with Corosync peer logs and Prometheus host/guest reachability; a zero error counter alone did not rule out this hang.

## What I found and root cause

Purple uses an Intel Ethernet Connection (7) I219-LM `[8086:15bb]` rev 10, e1000e, NVM `0.5-4`, in a Lenovo M920q `10RRS0LN00` with BIOS `M1UKT45A` dated 2019-07-11. Its only wired NIC is `nic0`. The VLAN-aware `vmbr0`, management on `vmbr0.70` and Corosync link1 on `vmbr0.71` all use it. `wlo1` is down; the configured `nic1` device does not exist.

The transmit ring stopped and the driver never reset it. I infer that the NIC could no longer send frames despite the live PHY link. Load was under 1.5 Mbit/s TX and about 0.3 Mbit/s RX, with zero TX errors/drops, CPU about 50 °C and NVMe about 49 °C. I ruled out load, heat and the recurring pve-firewall `Can't lock /run/xtables.lock` noise. No specific trigger is established.

This is the first recorded hang in Purple's journal, retained back to 2026-07-02. A regression in `7.0.14-20-pve` is not established: it occurred once after about nine days, Green and Red run the same kernel and NIC without a hang, and earlier Purple kernels ran more than 65 days without one.

## Recovery and verification

I recovered the host with a short power-button press at 12:35:03 AM on 2026-10-15. logind began a clean shutdown; qmshutdown stopped VM 121 by 12:35:14 AM and VM 401 by 12:35:18 AM, with all guests stopped at 12:35:20 AM. I then pressed the button again to power on. wtmp records the boot at 12:36:09 AM onto the already-installed `7.0.14-22-pve`, replacing `7.0.14-20-pve`.

Purple rejoined at 12:36:43 AM, both guests' Prometheus `up` recovered at 12:37:15 AM, the TS3 Manager probe reported HTTP 200 from 12:37:59 AM, and Playit loaded three tunnels at 12:39:03 AM. At 12:43 AM to 12:45 AM EDT I verified quorum, all five LRMs reporting `idle` with watchdog standby and no HA resources, both VMs running, VM 116 still stopped, zero current-boot hang lines and a 1000 Mb/s full-duplex NIC with zero error, timeout or restart counters. The workload checks are in the incident's [validation](../../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md#validation). On October 15 from 12:51:21 AM to 12:54:31 AM EDT, credential-free checks passed for Minecraft LAN/public server-list pings, both TeamSpeak LAN/public `TS3INIT1` paths, both unauthenticated ServerQuery version endpoints, both file-transfer TCP ports and TS3 Manager LAN/public HTTP 200. Minecraft's friendly-hostname handshake reset matched the already-recorded Playit behavior. I did not test an authenticated Minecraft join or TeamSpeak `serverinfo`, which require an account or login.

Minecraft inherited an empty external resolver list at boot and could not resolve its authentication service names. At 12:58:13 AM, with 0/20 players online, I ran `docker restart minecraft`; it was healthy at 12:58:32 AM, all three service names resolved and the 12:59 AM LAN ping passed again. At 12:59:56 AM EDT, the public join-route check resolved the Cloudflare SRV through 1.1.1.1 to `<playit-relay>` and sent a protocol-777 login handshake naming the SRV target, followed by Login Start as unauthenticated `testuser`. The server first sent `0x01` Encryption Request in 245 ms, confirming the Playit path reaches online authentication after the DNS correction. I closed before authentication; an authenticated join remains untested. The incident records the secondary finding and correction; [Minecraft DNS persistence](../../../../../Platforms/Minecraft/README.md#open-items) remains open.

A physical shutdown and power-on is the recovery demonstrated here. I have not tested a NIC bounce. No HA resource was armed on Purple, the watchdog was in standby, and the local guest disks could not fail over. I have no provisioned AMT or other out-of-band power path recorded, so this recovery required physical presence.

## Candidate fix and open work

I have not changed the offloads. RX/TX checksumming, scatter-gather, TSO, GSO and GRO remain on. EEE is `enabled - inactive`, TX ring 256, kernel command line `quiet` and ASPM policy default.

The candidate workaround is a persistent line on the `nic0` stanza in `/etc/network/interfaces` on Purple, Green and Red:

```text
iface nic0 inet manual
    post-up /sbin/ethtool -K nic0 tso off gso off gro off
```

I still need to apply it and verify `ethtool -k nic0` after a reboot. I will widen it to every offload if the hang returns. Community reports describe success on I219 NICs, including a Lenovo M920q, but results vary and some required all offloads disabled: [I219 hang report](https://forum.proxmox.com/threads/intel-nic-e1000e-hardware-unit-hang.106001/post-713319), [M920q report](https://forum.proxmox.com/goto/post?id=745557), [offload workaround discussion](https://forum.proxmox.com/goto/post?id=391990). This is a community workaround, not a vendor fix. An `ethtool -K` change alone does not survive reboot.

Green and Red share Purple's M920q, BIOS, I219-LM (7) and NVM revision with TSO/GSO enabled. Blue's M910q uses I219-LM (2), NVM `0.8-4`, and has TSO forced off by the driver; Grey uses Realtek NICs. I found no other hang in the retained boots I checked. Firmware, remote recovery, a separate physical link1 NIC and recurrence monitoring are tracked in the [Galaxy TODO](../TODO.md#i219-transmit-hang-prevention).
