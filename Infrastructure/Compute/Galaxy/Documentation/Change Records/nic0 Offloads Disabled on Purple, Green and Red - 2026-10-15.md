# nic0 Offloads Disabled on Purple, Green and Red

**Created:** 2026-10-15  
**Last updated:** 2026-10-15

**Implementation date:** 2026-10-15  
**Status:** Applied; the after-reboot check is open  
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

## Open

- I have not rebooted any node since the change. The final check is `ethtool -k nic0` reading TSO, GSO and GRO off after each node's next boot. Red is already due a reboot for kernel `7.0.14-22-pve`.
- Whether this prevents the hang will only show over time. If the hang returns, I will widen the line to every offload and record the recurrence against the incident.
- With GRO off, the CPU handles each received packet separately. I have not measured the cost.
- The NIC watchdog, the BIOS/ME check and out-of-band power control are still open in the [Galaxy TODO](../TODO.md#i219-transmit-hang-prevention).

## Rollback

On each node, delete the `post-up` line from the `nic0` stanza, or copy `/root/interfaces.pre-offload-2026-10-15` back over `/etc/network/interfaces` if nothing else has changed since. Then run `ethtool -K nic0 tso on gso on gro on` to restore the offloads without a reboot.
