# nic0 Offloads Disabled on Purple, Green and Red

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-15  
**Status:** Complete; confirmed after a reboot on all three nodes  
**Affected systems:** `purple-server`, `green-server` and `red-server`: `/etc/network/interfaces`, onboard Intel I219-LM `nic0` (`e1000e`)  
**Incident:** [Purple Server NIC Transmit Hang - 2026-10-14](../../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md)

On 2026-10-15 I turned off TCP segmentation offload (TSO), generic segmentation offload (GSO) and generic receive offload (GRO) on `nic0` on the three M920q nodes. The change is in each node's network configuration, so it is applied again at every boot. It is the community workaround for the I219 transmit hang that took Purple off the network on 2026-10-14. It is not a vendor fix, and it does not prove the hang cannot recur.

## Why these three nodes

Purple, Green and Red are the same M920q `10RRS0LN00` with BIOS `M1UKT45A`, an I219-LM (7) and NVM `0.5-4`, and all three had TSO, GSO and GRO on. Blue's M910q I219-LM (2) already has TSO forced off by its driver, and Grey uses Realtek NICs, so I left both unchanged. The [troubleshooting record](../Troubleshooting/e1000e%20Transmit%20Hang%20on%20purple-server%20-%202026-10-14.md#offload-workaround-and-open-work) links the community reports.

## What changed

Each node's `nic0` stanza gained one line:

```text
iface nic0 inet manual
	post-up /sbin/ethtool -K nic0 tso off gso off gro off
```

The indentation matches each file: a tab on Purple and Red, four spaces on Green. RX/TX checksumming and scatter-gather stay on. Before the edit, no node had a pending `/etc/network/interfaces.new`. Each node keeps its original file as `/root/interfaces.pre-offload-2026-10-15`, and `ifquery -a` parsed the new file with exit code 0.

## How it survives a reboot

At boot, `networking.service` runs ifupdown2's `start-networking start`, which brings up `vmbr0` and its bridge port `nic0` from this file and then runs each `post-up` line. `nic0` has no `auto` line of its own. ifupdown2 configures it as a dependency of `vmbr0`. On each node, a dry run of the boot path, `ifup -a -n -v`, printed `DRY-RUN: executing /sbin/ethtool -K nic0 tso off gso off gro off`.

Proxmox's network editor keeps lines it doesn't recognise, such as `post-up`, when it rewrites `/etc/network/interfaces`. `PVE/Network/Interfaces.pm` stores them as extra options and writes them back, so a later edit from the web interface should not drop this line.

## Applying it without a reboot

I ran `ifup nic0` on each node so ifupdown2 applied the new line itself, rather than running `ethtool` by hand. That exercises the configured line, not only the command. Changing these three flags does not reset an `e1000e` adapter.

| Node | Applied (EDT) | Kernel | TSO / GSO / GRO after | `carrier_changes` before → after | Corosync peer links connected | Gateway ping |
|---|---|---|---|---|---|---|
| `green-server` | 8:06:28 AM | `7.0.14-20-pve` | off / off / off | 2 → 2 | 8 of 8 | 3 of 3 |
| `red-server` | 8:06:43 AM | `7.0.14-20-pve` | off / off / off | 2 → 2 | 8 of 8 | 3 of 3 |
| `purple-server` | 8:06:58 AM | `7.0.14-22-pve` | off / off / off | 2 → 2 | 8 of 8 | 3 of 3 |

The unchanged `carrier_changes` counters show the link never dropped. The kernel logged no `e1000e`, `nic0` or link messages afterwards. "8 of 8" is four peers on both Corosync links. The gateway is `192.168.70.1`. I did Green first because it holds no guests.

On Purple, VM 121 `edge-01` and VM 401 `alpha-prod-01` stayed running. On `alpha-prod-01` the `minecraft` container was healthy, `playit-agent` was up and port 25565 accepted a loopback connection. VM 116 `app-01` was stopped, as it has been since it was parked on 2026-10-09.

## After-reboot verification

Later on 2026-10-15 I rebooted Green, Red and then Purple, one at a time, so the cluster never had fewer than four votes. Each reboot was a normal `systemctl reboot` scheduled through `systemd-run`. No node had `ethtool` run by hand after it booted.

| Node | Shutdown (EDT) | Booted | Kernel | Rejoined cluster | TSO / GSO / GRO after boot | Link |
|---|---|---|---|---|---|---|
| `green-server` | 8:30:01 AM | 8:30:52 AM | `7.0.14-20-pve` | 8:31:01 AM | off / off / off | 1000 Mb/s full duplex |
| `red-server` | 8:34:58 AM | 8:35:57 AM | `7.0.14-22-pve` | 8:36:33 AM | off / off / off | 1000 Mb/s full duplex |
| `purple-server` | 9:06:11 AM | 9:07:09 AM | `7.0.14-22-pve` | 9:07:47 AM | off / off / off | 1000 Mb/s full duplex |

On each node, `networking.service` finished within eight seconds of boot. Each node came back with RX/TX checksumming and scatter-gather still on, five quorate votes, all eight Corosync peer links connected, `pve-cluster`, `pvedaemon`, `pveproxy`, `pvestatd` and `corosync` active, no failed units, and no `Hardware Unit Hang` lines. Green and Red reached the gateway.

Green has no `7.0.14-22-pve` installed, so it booted the same kernel. Red booted the `7.0.14-22-pve` kernel it had been waiting for since the [2026-10-07 package updates](../../../../../Operations/Maintenance/OS%20Package%20Updates%20-%202026-10-07.md#open-state).

Red's only guest, CT 842 `media-01`, shut down cleanly at 8:35:13 AM and started again at 8:36:35 AM, so the media stack was down for about a minute and a half. All ten of its running containers came back, and `gluetun`, `jellyfin`, `hawser` and `cadvisor` reported healthy. The Docker boot race that hit Minecraft did not recur here. Every container's resolver file names the host's external server, and `jellyfin`, `sonarr`, `radarr`, `prowlarr`, `jellyseerr` and `qbittorrent` (through `gluetun`) all resolved an external name.

### Purple's guests

I had started `app-01` at 8:56 AM for the [Coolify webhook test](../../../../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/Coolify%20Webhook%20Bypass%20Limited%20to%20GitHub%20-%202026-10-15.md), and it was already stopped again by 9:06:08 AM. It is set not to start at boot, and I left it off after the reboot. Purple's shutdown stopped `edge-01` and `alpha-prod-01` between 9:06:17 and 9:06:30 AM. They started again at 9:07:47 and 9:07:50 AM.

- `edge-01`: `cloudflared` registered four tunnel connections between 9:08:06 and 9:08:09 AM, and Caddy was active.
- Minecraft: the [Docker DNS boot race](../../../../../Platforms/Minecraft/README.md#open-items) recurred. The container started at 9:08:12 AM, about four seconds before Alpha's `/etc/resolv.conf` was written at 9:08:16 AM, and its resolver file read `# NO EXTERNAL NAMESERVERS DEFINED`. I ran `docker restart minecraft` at 9:09:01 AM. It was healthy at 9:09:17 AM with `# ExtServers: [host(192.168.80.1)]`, and `sessionserver.mojang.com`, `api.minecraftservices.com` and `discovery.minecraftservices.com` resolved inside it.
- TeamSpeak: the boot-recovery script restarted `ts-valorant-02` and `ts-valorant-03` at 9:09:41 and 9:09:42 AM and `playit-agent` at 9:10:02 AM, and Playit reported its tunnels loaded.
- Checks at 9:10:46 to 9:10:53 AM: `teamspeak_public_up` was 1 for `ts02` and `ts03`. Prometheus `up` was 1 for Purple and `alpha-prod-01`, and every blackbox probe was 1. No alert was firing. TS3 Manager returned HTTP 200. Minecraft server-list pings on the LAN and through the Cloudflare SRV record and Playit both gave 26.3 / 777 / 0/20 with pong OK.

Grey could not ping Green after Green's reboot, and Green could not ping Grey. The reboot did not cause this. Grey gets no ping reply from Purple, Blue or Red either, Corosync traffic between the nodes was unaffected, and Green reached the gateway normally.

## Open

- Whether this prevents the hang will only show over time. If the hang returns, I will widen the line to every offload and record the recurrence against the incident.
- With GRO off, the CPU handles each received packet separately. I have not measured the cost.
- The NIC watchdog, the BIOS/ME check and out-of-band power control are still open in the [Galaxy TODO](../TODO.md#i219-transmit-hang-prevention).

## Rollback

On each node, delete the `post-up` line from the `nic0` stanza, or copy `/root/interfaces.pre-offload-2026-10-15` back over `/etc/network/interfaces` if nothing else has changed since. Then run `ethtool -K nic0 tso on gso on gro on` to restore the offloads without a reboot.
