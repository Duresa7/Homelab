# Purple Server NIC Transmit Hang - 2026-10-14

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident date | 2026-10-14 into 2026-10-15 |
| Report timezone | America/New_York (EDT) |
| Service | Galaxy Proxmox node `purple-server`, VM 121 `edge-01` and VM 401 `alpha-prod-01` |
| Node | `purple-server` (`192.168.70.11`), Corosync nodeid 2 in the five-node Galaxy cluster |
| Trigger | No specific trigger identified; first e1000e transmit hang at 11:44:51 PM |
| Duration | Full service outage about 54 minutes, October 14 at about 11:44:50 PM to October 15 at 12:39:03 AM; Purple absent from cluster membership for 51 minutes 42 seconds, 11:45:01 PM to 12:36:43 AM. Separately, Minecraft logins were most likely impaired after it started at 12:37 AM until DNS recovery at 12:58:32 AM |
| Recovery | Physical power-button shutdown and power-on; booted the already-installed `7.0.14-22-pve` kernel |
| Status | Resolved, with preventive actions open |
| Severity | SEV-2 - Service Outage |

## Summary

Purple's onboard Intel I219-LM NIC stopped processing its transmit ring at about 11:44:50 PM on October 14. The kernel logged `e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang:` every two seconds, but the driver never reset the adapter. Purple stayed powered and its Ethernet link stayed up while management, both Corosync links and the guest VLANs lost connectivity.

The outage took `edge-01`, the only Cloudflare Tunnel connector for Caddy ingress, and `alpha-prod-01`, which carries Minecraft and both public TeamSpeak servers, off the network. Minecraft and both TeamSpeak servers use Cloudflare DNS and SRV records to reach Playit relays and the Playit agent on `alpha-prod-01`, independently of the `edge-01` Cloudflare Tunnel. The other four Galaxy nodes stayed quorate. I pressed Purple's power button at 12:35:03 AM on October 15, let it shut down cleanly, and pressed it again to power on. The boot at 12:36:09 AM loaded `7.0.14-22-pve`, which had already been installed. The Playit agent loaded all three tunnels at 12:39:03 AM, ending the roughly 54-minute full outage. LAN and public protocol checks later confirmed Minecraft, TeamSpeak and TS3 Manager reachability. Minecraft also inherited an empty external DNS resolver list at boot. I restarted that container at 12:58:13 AM and verified DNS and health by 12:58:32 AM. Logins were most likely impaired between its 12:37 AM start at boot and that correction, despite working server-list pings; nobody tried an authenticated join. Reboot persistence remains open.

## Impact

| Area | Impact |
|------|--------|
| Purple management and cluster membership | `192.168.70.11` and both Corosync paths were unreachable. Purple formed a single-member, non-primary component, lost quorum and made pmxcfs read-only. The other four nodes remained quorate |
| Internet edge | VM 121 `edge-01` lost its network path, taking the only Cloudflare Tunnel connector and Caddy ingress offline. Caddy had no live applications behind it because `app-01` was parked |
| Minecraft and TeamSpeak | VM 401 `alpha-prod-01` lost Minecraft Java 26.3, `ts-valorant-02`, `ts-valorant-03`, TS3 Manager and their three Playit tunnels. The public game and voice path is Cloudflare DNS plus SRV to Playit, then the Playit agent on Alpha. Cloudflare kept answering the Minecraft CNAME `minecraft.alphasecunited.com` and SRV `_minecraft._tcp.minecraft.alphasecunited.com`, both pointing at the Playit allocation, and the TeamSpeak SRV names `_ts3._udp.ts02.alphasecunited.com` and `_ts3._udp.ts03.alphasecunited.com`, pointing at Playit relays. Player connections failed because the relays had no connected agent; the three tunnels loaded again at 12:39:03 AM. Of two players present around the failure, one had an unrelated anti-fly kick at 11:44:54 PM; the other timed out at 11:45:19 PM |
| Minecraft after the reboot | The server answered pings from 12:37:25 AM, but external authentication names did not resolve inside its container. With online authentication and secure profiles enabled, logins were most likely impaired from the 12:37 AM start at boot until 12:58:32 AM, about 21 minutes from container startup and extending 19 minutes 29 seconds beyond the full outage. This is an inference; nobody tried an authenticated join during that interval |
| Other Alpha workloads | teamspeak-monitor, cAdvisor and Hawser lost network access with the VM |
| Pre-existing downtime | VM 116 `app-01` was stopped and parked since 2026-10-09. Coolify and the applications behind Caddy were already offline; I do not count their existing downtime as new impact |
| Detection and recovery | Grafana alerted within six minutes. About 44 minutes passed between the first alert and my power-button press. Recovery required physical presence |
| Guest shutdown | pve-guests stopped both running VMs cleanly through qmshutdown before power-off; no forced guest power cut was needed |

## Affected Assets

| Asset | Role and configuration | Observed state |
|-------|------------------------|----------------|
| `purple-server` | Lenovo ThinkCentre M920q `10RRS0LN00`, BIOS `M1UKT45A` dated 2019-07-11 | Running `7.0.14-20-pve` at failure; now `7.0.14-22-pve`, pve-manager 9.2.21 |
| `nic0`, PCI `0000:00:1f.6` | Intel Ethernet Connection (7) I219-LM `[8086:15bb]` rev 10, e1000e, NVM `0.5-4` | Purple's only wired NIC; transmit ring hung with physical link still up |
| `vmbr0` | VLAN-aware bridge with `bridge-ports nic0` | Management and every guest VLAN depend on the same NIC and cable |
| `vmbr0.70` and `vmbr0.71` | `192.168.70.11/24` on MGMT-A, Corosync link0; `192.168.71.11/24` on Cluster-Net, link1 | Both links failed together |
| Bane Switch POE, Port 2 | UniFi USW Pro Max 16 PoE, model `USPM16P` | No port link-down or alarm; switch uptime was 35 days |
| VM 121 `edge-01` | `192.168.30.10`, DMZ VLAN 30; Caddy 2.6.2 and cloudflared | Unreachable until the host and VM restarted |
| VM 401 `alpha-prod-01` | `192.168.80.118`, SERVERS-A VLAN 80; Minecraft, two TeamSpeak 3 servers, TS3 Manager, Playit agent, teamspeak-monitor, cAdvisor and Hawser | Unreachable until restart; Playit restored three tunnels at 12:39:03 AM. Minecraft external DNS recovered after a separate container restart, healthy at 12:58:32 AM |
| VM 116 `app-01` | Parked guest on Purple | Stopped before the incident and remained stopped |

`wlo1` is down and unused. The `iface nic1 inet manual` stanza in `/etc/network/interfaces` refers to no present device and provides no alternate path.

## Symptoms

- Purple, `edge-01` and `alpha-prod-01` node_exporters stopped answering; `https://ts3-manager.alphasecunited.com/` failed its blackbox probe.
- Purple logged both knet links down to every peer, token timeouts and quorum loss. pve-ha-lrm could not write its status file after pmxcfs became read-only.
- The NIC logged 1,519 `Detected Hardware Unit Hang` messages with TDH/TDT fixed at `50/82` through shutdown. It never logged `NETDEV WATCHDOG`, a transmit-timeout, `Reset adapter` or `NIC Link is Down`.
- UniFi kept the physical port up. Later wired-client disconnections were idle timeouts rather than link events.

## Timeline (EDT)

| Date | Time | Event |
|------|------|-------|
| 2026-10-14 | 11:44:49 PM | Last evidence of working traffic: a Minecraft player reconnected and logged in |
| 2026-10-14 | 11:44:51 PM | First e1000e hang. Purple logged Corosync knet links 0 and 1 down to hosts 1, 3, 4 and 5 |
| 2026-10-14 | 11:44:52 PM | Grey logged both links to host 2 down |
| 2026-10-14 | 11:44:53 PM | Purple and Grey both logged `Token has not been received in 3712 ms` |
| 2026-10-14 | 11:44:54 PM | One of the two players was kicked for an unrelated anti-fly reason |
| 2026-10-14 | 11:44:55 PM | Purple logged `A processor failed, forming new configuration: token timed out (4950ms)` |
| 2026-10-14 | 11:45:00 PM | On the 15-second Prometheus scrape, `up` dropped to 0 for Purple and both guests; the TS3 Manager blackbox probe failed |
| 2026-10-14 | 11:45:01 PM | Purple formed membership `2.2ca` with member `2`, logged `node lost quorum` and entered the non-primary component. pmxcfs became read-only; the other four nodes formed membership `1.2ca` with members `1 3 4 5` and stayed quorate. Grey logged `Failed to receive the leave message. failed: 2` |
| 2026-10-14 | 11:45:19 PM | The other Minecraft player disconnected with `Timed out` |
| 2026-10-14 | 11:46:19 PM | Minecraft was empty and paused |
| 2026-10-14 | 11:51:06 PM to 11:51:29 PM | Grafana delivered “Proxmox node or cluster is down”, “Internal service is unreachable” and three “Host is down” alerts through the Discord alert bot |
| 2026-10-14 | 11:56:03 PM | Two “VM or container is down” alerts followed |
| 2026-10-15 | 12:00:45 AM | UniFi recorded `alpha-prod-01` connected. This was a client-tracking artifact, not evidence of traffic recovery |
| 2026-10-15 | 12:05:28 AM | UniFi expired Purple on MGMT-A and `edge-01` on DMZ as wired clients on Bane Switch POE Port 2 |
| 2026-10-15 | 12:10:28 AM | UniFi expired `alpha-prod-01` on SERVERS-A. No physical link-down accompanied these idle timeouts |
| 2026-10-15 | 12:35:03 AM | I pressed the power button. systemd-logind logged `Power key pressed short.` then `Powering off...`; a clean shutdown began |
| 2026-10-15 | 12:35:14 AM to 12:35:20 AM | pve-guests stopped VM 121 by 12:35:14 AM and VM 401 by 12:35:18 AM through qmshutdown; `all VMs and CTs stopped` at 12:35:20 AM |
| 2026-10-15 | 12:35:27 AM | The last hang block retained TDH `<50>`, TDT `<82>`, next_to_watch `<51>` and time_stamp `<12e2a3af4>` from the first block; only `jiffies` advanced |
| 2026-10-15 | 12:36:09 AM | After I pressed the button again, wtmp recorded the boot onto `7.0.14-22-pve` |
| 2026-10-15 | 12:36:43 AM | Grey logged host 2 joined, membership `1.2d3` with all five members |
| 2026-10-15 | 12:36:45 AM | Corosync link1 was up and Purple's Prometheus `up` returned to 1 |
| 2026-10-15 | 12:36:47 AM to 12:36:51 AM | pve-guests started VM 121, then VM 401 |
| 2026-10-15 | 12:37:10.56 AM | The `minecraft` container started before the host resolver was ready; its resolver file had no external nameservers |
| 2026-10-15 | 12:37:14.98 AM | Alpha's `/etc/resolv.conf` was written, about 4.4 seconds after Minecraft started; the container retained the empty external resolver list |
| 2026-10-15 | 12:37:15 AM | `up` returned for `edge-01` and `alpha-prod-01` |
| 2026-10-15 | 12:37:25 AM | Minecraft logged `Done` and answered server-list pings, despite its external DNS failure |
| 2026-10-15 | 12:37:59 AM | The TS3 Manager blackbox probe began reporting HTTP 200 again |
| 2026-10-15 | 12:38:40 AM to 12:38:44 AM | Boot recovery restarted TeamSpeak at 12:38:40 AM; virtual server 1 was listening at 12:38:41 AM, and both `teamspeak_public_up` series were 1 from 12:38:44 AM |
| 2026-10-15 | 12:39:01 AM | Boot recovery restarted Playit after DNS answered |
| 2026-10-15 | 12:39:03 AM | Playit logged `playit connected; tunnels loaded`, with three tunnels; both TeamSpeak public probes had already recovered. Minecraft's public status path recovered, but its container still could not resolve authentication names |
| 2026-10-15 | 12:41:03 AM to 12:41:29 AM | All Grafana alerts resolved |
| 2026-10-15 | 12:43 AM to 12:45 AM | Post-recovery checks confirmed quorum, guest and workload state, NIC counters and monitoring recovery |
| 2026-10-15 | 12:51:21 AM to 12:54:31 AM | Credential-free LAN/public checks passed for Minecraft, TS-02, TS-03 and TS3 Manager |
| 2026-10-15 | 12:58:13 AM | With 0 of 20 players online, I ran `docker restart minecraft` to regenerate its resolver file |
| 2026-10-15 | 12:58:25 AM to 12:58:32 AM | Minecraft logged `Done (0.301s)` at 12:58:25 AM and was healthy at 12:58:32 AM; all three authentication service names resolved inside the container |
| 2026-10-15 | 12:59 AM | A repeated LAN server-list ping passed after the container restart, with 1.8 ms connect time and pong OK |
| 2026-10-15 | 12:59:56 AM | I verified the public Minecraft join route after the DNS correction: Cloudflare SRV via 1.1.1.1 to `<playit-relay>`, then a protocol-777 login handshake naming the SRV target and Login Start as unauthenticated `testuser`. The server's first login packet was `0x01` Encryption Request, requiring online authentication, with a 245 ms round trip. I closed the connection before authentication |

## Findings

### The transmit ring stopped while the physical link stayed up

The first hang had TDH `<50>`, TDT `<82>`, next_to_use `<82>`, next_to_clean `<50>`, MAC Status `<80083>`, PHY Status `<796d>`, PHY 1000BASE-T Status `<3800>`, PHY Extended Status `<3000>` and PCI Status `<10>`. The message repeated every two seconds: 455 occurrences in the 11:00 PM hour and 1,064 in the midnight hour, 1,519 total. TDH/TDT never advanced from `50/82`. There was no adapter reset or link-down message, and the PHY continued to report a 1000 Mbps link.

I infer that the NIC stopped processing its transmit ring while the link stayed up, leaving the switch with a live port but no frames. The simultaneous Corosync and guest failures, persistent ring values and lack of a switch link event support that interpretation. The switch did not reboot: its uptime was 35 days.

The [verbatim journal capture](Evidence/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14/Logs/S01%20Hang,%20Membership%20and%20Power-Key%20Recovery%20-%202026-10-15.md) retains the complete first and last hang blocks, Corosync membership changes and power-key recovery. At 12:35:27 AM, 50 minutes 36 seconds after the first block, TDH `<50>`, TDT `<82>`, next_to_watch `<51>` and the stuck descriptor's time_stamp `<12e2a3af4>` were identical. Only `jiffies` advanced, from `<12e2a3f80>` to `<12e589301>`. That directly supports a stuck transmit ring.

Grey independently logged `Token has not been received in 3712 ms` at 11:44:53 PM and `Failed to receive the leave message. failed: 2` at 11:45:01 PM. Purple formed membership `2.2ca`; the other four nodes formed `1.2ca` and remained quorate. Grey recorded the five-node rejoin as membership `1.2d3` at 12:36:43 AM.

### Load, heat and firewall lock messages do not explain the failure

Before the hang, `nic0` carried under 1.5 Mbit/s TX and about 0.3 Mbit/s RX, with zero TX errors or drops. CPU package temperature was about 50 °C and NVMe temperature about 49 °C. These readings do not support load or heat as the cause. pve-firewall's `Can't lock /run/xtables.lock` had appeared 22 times since the October 6 boot; I ruled it out as unrelated background noise.

### HA had no armed recovery path

`ha-manager status` showed every LRM idle with watchdog standby. Purple had no HA resource, so its watchdog was not armed and nothing fenced or restarted the node. Its guest disks are on `local-lvm`; they could not have moved to another node even with HA enabled.

### This is the first recorded occurrence; a kernel regression is not established

Purple booted `7.0.14-20-pve` at 12:31 AM on 2026-10-06 after the October 5 dist-upgrade. The October 7 dist-upgrade at 7:50 AM installed `7.0.14-22-pve`, but Purple did not boot it until recovery. The hang occurred after about nine days on `7.0.14-20-pve`. Earlier kernels had run for more than 65 days on Purple without a recorded hang. One occurrence does not establish a regression in `7.0.14-20-pve`.

I found no other `Hardware Unit Hang` in Purple boots -2 through -5 or in boots 0 through -3 on Green, Red and Blue. Purple's retained journal reaches back to 2026-07-02. Green and Red still run `7.0.14-20-pve` on the same M920q `10RRS0LN00`, BIOS `M1UKT45A`, I219-LM (7) and NVM `0.5-4`, with TSO and GSO on, without a recorded hang. Blue is an M910q `10MUS08B00` with I219-LM (2), NVM `0.8-4`; its e1000e driver forces `tcp-segmentation-offload: off [fixed]`. Grey uses Realtek NICs.

### Offload changes are a candidate workaround

At the time of the hang, RX/TX checksumming, scatter-gather, TSO, GSO and GRO were on. Corrective action 3 later turned TSO, GSO and GRO off. EEE is `enabled - inactive`, the TX ring is 256, the kernel command line is only `quiet`, and PCIe ASPM uses the default policy.

I did not find a specific trigger. Community reports describe this e1000e/I219 hang over several years. Reports include an I219-LM in a Lenovo M920q and describe disabling offloads with `ethtool -K` to stop recurrence: [I219 hardware-unit-hang discussion](https://forum.proxmox.com/threads/intel-nic-e1000e-hardware-unit-hang.106001/post-713319), [M920q report](https://forum.proxmox.com/goto/post?id=745557). Results vary; some needed every offload disabled rather than only TSO/GSO, and settings need network-configuration persistence to survive a reboot: [offload workaround discussion](https://forum.proxmox.com/goto/post?id=391990). These are community reports, not a vendor fix or proof of Purple's trigger.

### Minecraft inherited an empty external resolver list at boot

The `minecraft` container started at 12:37:10.56 AM on October 15. Alpha's `/etc/resolv.conf` was written at 12:37:14.98 AM, about 4.4 seconds later. Docker generated the container resolver file with `# NO EXTERNAL NAMESERVERS DEFINED`. Inside the container, `sessionserver.mojang.com`, `api.minecraftservices.com` and `discovery.minecraftservices.com` failed to resolve while the host resolved all three. Minecraft logged repeated `java.net.UnknownHostException` warnings.

With `online-mode=true` and `enforce-secure-profile=true`, player authentication depends on those names. I infer that logins would most likely have failed from the 12:37 AM container start at boot until DNS recovery at 12:58:32 AM, even though the server answered pings from 12:37:25 AM. Nobody tried an authenticated join, so I have no observed authenticated login failure.

This is the same Docker boot race recorded in [Collector DNS Failure After a Boot Race](../../../Platforms/Teamspeak%20Hosting/Documentation/Change%20Records/Collector%20DNS%20Failure%20After%20a%20Boot%20Race%20-%202026-08-27.md). The [TeamSpeak boot-recovery script](../../../Platforms/Teamspeak%20Hosting/README.md#boot-recovery) waits for DNS and restarted TeamSpeak at 12:38:40 AM and Playit at 12:39:01 AM; Playit loaded three tunnels at 12:39:03 AM. Minecraft was deployed on 2026-10-09 without pinned `dns:` and without a place in that script. `ts3-manager` also inherited an empty external resolver list, but its query connections use IP addresses, so I found no effect there.

## Root Cause

Purple's onboard Intel I219-LM stopped processing its transmit ring, an e1000e “Hardware Unit Hang”, at about 11:44:50 PM. The driver never reset the adapter. Purple stayed powered and its link stayed up, but it could not send any frames. The logs establish the failure mode; they do not identify the specific trigger inside the NIC or driver.

## Contributing Factors

1. **One physical NIC.** Management, both Corosync links and every guest VLAN share `nic0` and its cable. The second Corosync link gave no protection against this NIC fault.
2. **No automatic or remote recovery.** Purple had no armed HA resource, no host-side connectivity check that bounces the NIC, and no out-of-band power control. The M920q has Intel AMT hardware, with an AMT SOL controller at `00:16.3`, but I have no record of provisioning it and treat it as unprovisioned.
3. **Offloads enabled.** RX/TX checksumming, scatter-gather, TSO, GSO and GRO were on, matching the configuration associated with the hang in the community reports. Their causal role on Purple remains unproven.

## Corrective Action

### 1. Power-cycle Purple

I recovered Purple by powering it off and on. At 12:35:03 AM I pressed the power button once; logind began a clean shutdown and pve-guests stopped both running VMs before power-off. I pressed the button again to power on, and wtmp records the boot at 12:36:09 AM. That boot also moved Purple from `7.0.14-20-pve` to the already-installed `7.0.14-22-pve` kernel. The power cycle changed no offloads, firmware, network configuration or recovery controls.

### 2. Restart Minecraft to restore external DNS

At 12:58:13 AM EDT on 2026-10-15, with 0 of 20 players online, I ran `docker restart minecraft`. It logged `Done (0.301s)` at 12:58:25 AM and was healthy at 12:58:32 AM. Its regenerated resolver file reads `# ExtServers: [host(192.168.80.1)]`, and all three Mojang/Minecraft service names resolve inside the container. At 12:59 AM a LAN server-list ping again gave 26.3 / 777 / 0/20, pong OK, with 1.8 ms connect time.

The restart corrected the current container state. Corrective action 4 later removed the race.

### 3. Disable `nic0` offloads on Purple, Green and Red

At about 8:06 AM EDT on 2026-10-15, I added `post-up /sbin/ethtool -K nic0 tso off gso off gro off` to the `nic0` stanza in `/etc/network/interfaces` on all three M920q nodes. I then ran `ifup nic0` on each, so the configured line applied the change. TSO, GSO and GRO read off on every node. No link dropped, all Corosync links stayed connected, and Purple's guests kept running. ifupdown2 runs the line at every boot. Green, Red and Purple all came back with the offloads off when I rebooted them one at a time later that morning, and Red booted `7.0.14-22-pve`. This is the community workaround, not a proven fix. [Change record](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md).

### 4. Pin Minecraft's DNS server

Purple's 9:06 AM verification reboot reproduced the Minecraft DNS boot race, and I restarted the container again at 9:09:01 AM. At 9:19:01 AM, with 0 of 20 players online, I recreated it with `dns: [192.168.80.1]` in its Compose definition, so Docker no longer takes its DNS server from Alpha's resolver file at start. It was healthy at 9:19:18 AM, its resolver file reads `# Overrides: [nameservers]`, and all three authentication names resolve. I have not yet confirmed it across a reboot of `alpha-prod-01`. [Change record](../../../Platforms/Minecraft/Documentation/Change%20Records/Pinned%20DNS%20Resolver%20-%202026-10-15.md).

## Validation

I checked the recovered state on 2026-10-15 from 12:43 AM to 12:45 AM EDT.

| Check | Observed result |
|-------|-----------------|
| Cluster | Quorum OK with all five LRMs reporting `idle` with watchdog standby; no HA resources |
| Guests | VM 121 and VM 401 running; VM 116 stopped |
| Kernel and NIC | `7.0.14-22-pve`, pve-manager 9.2.21; zero hang lines in the current boot; `nic0` at 1000 Mb/s full duplex |
| NIC counters | Zero RX/TX errors, CRC errors, `tx_timeout_count` and `tx_restart_queue` |
| Prometheus | `up` restored for Purple, `edge-01` and `alpha-prod-01`; TS3 Manager blackbox probe up |
| Alpha workloads | `minecraft` healthy, `hawser` healthy, `ts3-manager`, `ts-valorant-02`, `ts-valorant-03`, `playit-agent`, `cadvisor` healthy and `teamspeak-monitor` all Up |
| Public game and voice paths | Playit connected and loaded three tunnels at 12:39:03 AM |
| Cloudflare connector | `edge_uptime_connections` was 4 before the outage on October 14 at 11:39 PM and 11:43 PM, and after on October 15 at 12:39 AM and 12:43 AM. There are no samples during the outage |
| Alerting | All Grafana alerts resolved from 12:41:03 AM to 12:41:29 AM |

Playit's 12:39:01 AM `Network unreachable` messages targeted IPv6 and were expected noise; they do not indicate a separate fault.

I checked the following LAN and public paths on 2026-10-15 EDT without credentials.

| Path | Result and evidence | Time (EDT) |
|------|---------------------|------------|
| Minecraft LAN | Working. Server-list ping to `192.168.80.118:25565` gave version 26.3, protocol 777, 0/20 players, MOTD `AlphaSec United Minecraft`, pong OK. The repeat after the container restart gave the same response and 1.8 ms connect time | 12:51:21 AM; repeated at 12:59 AM |
| Minecraft public | Working. `_minecraft._tcp.minecraft.alphasecunited.com` gave the same SRV answer from 1.1.1.1, 8.8.8.8 and the default resolver. Two pings to `<playit-relay>` with the SRV target in the handshake gave 26.3 / 777 / 0/20, the same MOTD, about 125 ms and pong OK. Sending `minecraft.alphasecunited.com` in the handshake reset the connection, matching the known [Playit hostname behavior](../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md#connection-verification), not a new fault | 12:51:29 AM and 12:51:50 AM |
| Minecraft public join route | Reached authentication after the DNS correction. I resolved `_minecraft._tcp.minecraft.alphasecunited.com` through 1.1.1.1 to `<playit-relay>`, connected and sent a protocol-777 handshake naming the SRV target with next state login, followed by Login Start as unauthenticated `testuser`. The first login packet was `0x01` Encryption Request, requiring online authentication, with a 245 ms round trip. I closed the connection before authentication. This verifies the Cloudflare SRV to Playit to server join route reaches authentication, matching the earlier [SRV login transport verification](../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md#connection-verification); an authenticated join remains untested | 12:59:56 AM |
| TS-02 LAN | Working. UDP 9988 gave a valid `TS3INIT1` reply in 1.5 ms; unauthenticated ServerQuery 10012 `version` gave 3.13.8 Linux; file transfer TCP 30034 accepted connections. The log showed virtual server 1 listening at 12:38:41 AM and the ID revocation list downloaded | 12:51:21 AM to 12:52:22 AM |
| TS-02 public | Working. `_ts3._udp.ts02.alphasecunited.com` SRV from three resolvers led to `<playit-relay>`, which gave `TS3INIT1` in 40 to 44 ms. Prometheus `teamspeak_public_up` had been 1 continuously since 12:38:44 AM | 12:52 AM |
| TS-03 LAN | Working. UDP 9989 gave `TS3INIT1` in 1.0 ms; unauthenticated ServerQuery 10013 `version` gave 3.13.8; file transfer TCP 30035 accepted connections | 12:51:21 AM to 12:52:22 AM |
| TS-03 public | Working. `_ts3._udp.ts03.alphasecunited.com` SRV led to `<playit-relay>`, which gave `TS3INIT1` in 43 to 44 ms. `teamspeak_public_up` had been 1 since 12:38:44 AM | 12:52 AM |
| TS3 Manager | Working. HTTP 200 at `http://192.168.80.118:9000` and `https://ts3-manager.alphasecunited.com`; the blackbox probe had reported 200 from 12:37:59 AM onward | 12:54:31 AM |

I did not test an authenticated Minecraft join, which needs a real account, or TeamSpeak `serverinfo`, which needs a login. Protocol reachability is verified; authenticated use remains untested.

## Closure Status and Open Items

**Resolved:** Purple rejoined the cluster at 12:36:43 AM on 2026-10-15; public protocol reachability recovered by 12:39:03 AM, ending the roughly 54-minute full outage. LAN/public checks passed for Minecraft, TS-02, TS-03 and TS3 Manager. Minecraft logins were separately most likely impaired after it started at 12:37 AM until DNS recovery at 12:58:32 AM. The service outage and current DNS failure are closed, with preventive actions open. I have not tested an authenticated Minecraft join or TeamSpeak `serverinfo`.

The persistent offload change is applied on Purple, Green and Red and held through a reboot on each. I still need to add the NIC watchdog, check M920q BIOS/ME updates, establish recovery without physical presence, consider a separate physical Corosync link1 path, and watch Green and Red for the same signature. The actionable checklist is in the [Galaxy TODO](../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md#i219-transmit-hang-prevention).

Purple's verification reboot at 9:06 AM on 2026-10-15 reproduced the Minecraft DNS boot race. I pinned Minecraft's DNS server at 9:19 AM, which closes that item; confirming it across Alpha's next reboot is recorded in the [Minecraft backlog](../../../Platforms/Minecraft/README.md#open-items).

## Related Records

- [Evidence index](Evidence/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14/Evidence-Index.md)
- [Technical troubleshooting record](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/e1000e%20Transmit%20Hang%20on%20purple-server%20-%202026-10-14.md)
- [Minecraft DNS publication](../../../Platforms/Minecraft/Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md)
- [TeamSpeak public paths](../../../Platforms/Teamspeak%20Hosting/README.md#port-and-name-map)
- [Galaxy TODO](../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md#i219-transmit-hang-prevention)
- [Galaxy inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
