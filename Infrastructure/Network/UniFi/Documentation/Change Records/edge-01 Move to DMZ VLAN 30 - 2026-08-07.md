# edge-01 Move to DMZ VLAN 30

**Created:** 2026-08-07  
**Last updated:** 2026-08-07

## Date

I completed this change on 2026-08-07.

## Scope

I moved `edge-01` from DMZ-A (VLAN 90) to DMZ (VLAN 30), so one DMZ carries my edge host instead of two DMZs splitting the role. `edge-01` is VM 121 on `grey-server` and runs Caddy and the `edge-01` Cloudflare Tunnel, which is the only inbound path from the Internet to my services.

I did not change anything in Cloudflare. I did not move `app-01`. DMZ-A stays defined and empty through a soak period, and I delete it in a separate change.

## Starting State

I ran two DMZ networks, both in the `Dmz` firewall zone, so both carried identical policy:

- **DMZ (30)**, `192.168.30.0/24`, empty. My VLAN table called it "Internet-facing (legacy)" and pointed new edge hosts at DMZ-A.
- **DMZ-A (90)**, `192.168.90.0/24`, holding `edge-01` at `192.168.90.10`.

Before I started I confirmed DMZ (30) held nothing: no clients, no traffic in 90 minutes, no port forwards anywhere on the site, no firewall policy naming a `192.168.30.x` address, no WLAN mapped to it, and no port profile using it as a native network.

DHCP on DMZ (30) ran from `192.168.30.6` to `.254`, which would have placed a static `.10` inside the pool. DMZ-A ran from `.50` to `.100`, which is why `.10` was safe there.

One fact I did not have: the `Proxmox-Trunk` switch port profile excluded DMZ (30). No virtual machine could reach VLAN 30 on any hypervisor. That is the likely reason DMZ-A was created, and it is not recorded anywhere I looked before starting.

## Actions

### S01: Narrow the DMZ 30 DHCP pool

I changed DMZ (30) DHCP from `192.168.30.6 - .254` to `192.168.30.50 - .100`. The network had no clients, so nothing could be disturbed. The controller read back `firewall_zone_id` unchanged, confirming VLAN 30 stayed in the `Dmz` zone.

### S02: First cutover attempt, and the rollback

I copied `/etc/network/interfaces` on `edge-01`, rewrote its three `192.168.90.x` values to `192.168.30.x`, read the file back, then set `net0` from `tag=90` to `tag=30` and rebooted VM 121 at 2:17 PM.

The host came up at `192.168.30.10` with the correct default route, and Caddy started. `cloudflared` did not. Its journal recorded `lookup cfd-features.argotunnel.com on 1.1.1.1:53: dial udp 1.1.1.1:53: i/o timeout`, and systemd terminated it on a start timeout.

The cause was not DNS and not the firewall. `ping 192.168.30.1` returned `Destination Host Unreachable` from the host's own address, which is an ARP failure at layer 2. The gateway's `br30` interface showed `rx_packets=0` against `tx_packets=10734`, so it had never received a single frame on VLAN 30. A firewall drop still counts as received.

I restored the copied `interfaces` file, set `net0` back to `tag=90`, and rebooted. The tunnel returned healthy with 4 connections. Total outage was about 3 minutes across the two reboots.

I then found the cause: the `Proxmox-Trunk` port profile uses `forward: customize` with an exclusion list, and that list contained Management, IoT (20), Trusted (10), **DMZ (30)**, and Secure (50). `grey-server` sits on Bane Switch port 14, which carries that profile, so VLAN 30 frames never reached it.

### S03: Remove DMZ 30 from the trunk exclusion

I removed DMZ (30) from the `Proxmox-Trunk` exclusion list. The list now holds Management, IoT (20), Trusted (10), and Secure (50).

### S04: Prove VLAN 30 before touching the live interface

My first reachability test was invalid and I record it so the mistake is not repeated. I created `vmbr0.30` on `grey-server` and pinged the gateway from it. It failed, but `bridge vlan show dev vmbr0` showed the bridge's own local port carries only VLANs 1, 40, 70, and 71. The host's network stack can never receive VID 30 regardless of what the switch sends. The physical uplink `enp42s0` does carry VLANs 2 to 4094. A virtual machine's tap port is a different bridge port and receives its VID from Proxmox, so the test proved nothing about the path a guest would take.

I hot-added a second NIC to `edge-01` on VLAN 30 while it kept serving on VLAN 90, which risks no outage whatever the result:

- `ping -I ens19 192.168.30.1`: 3 packets sent, 3 received, 0% loss, average 0.419 ms.
- `dig @192.168.30.1 -b 192.168.30.200 cloudflare.com A`: `NOERROR`, 2 A records, query time 15 msec. This proves the gateway accepted a packet from a VLAN 30 source, recursed to the Internet, and answered, which is the exact path that failed in S02.
- The gateway's `br30` counter moved from 0 to 21 received packets and gained an ARP entry for the test address.

I removed the test NIC.

### S05: Second cutover

I repeated the `interfaces` rewrite and the `tag=30` change, keeping the MAC identical, and rebooted VM 121. `caddy` and `cloudflared` both came up active.

### S06: Repoint the dependents

- UniFi policy `Allow Monitor to DMZ monitoring`: destination address `192.168.90.10` to `192.168.30.10`. The controller preview showed the destination object also carried `port: 9100`, so I sent the port fields back unchanged rather than letting a partial object widen the rule to any port.
- `monitor-01`: Prometheus scrape target updated and reloaded with `SIGHUP`.
- `Platforms/Ansible/Source/fleet-updates/inventory/hosts.yml`: `ansible_host` for `edge-01`.
- The SSH Manager host entry for `edge_01`.

## Decisions

- I collapsed onto VLAN 30 rather than VLAN 90. Both networks were ordinary user-created networks with no delete protection, so either direction was available. Only `Internet 1`, `Internet 2`, and `Management` carry `attr_no_delete`.
- I kept the MAC identical. Both firewall policies that govern `edge-01`, `Allow edge-01 to app-01 Web` and `Allow DMZ to Wazuh - Security-A`, match it by MAC inside the `Dmz` zone. Because VLAN 30 and VLAN 90 share that zone, neither policy needed an edit.
- I narrowed the DHCP pool rather than adding a reservation, because a 249-address pool on an Internet-facing network earns nothing.
- I kept VLAN 90 defined through a soak period instead of deleting it in the same change.
- I took no snapshot. The change was two reversible values and I recorded both before touching them.

## Resulting Configuration

`edge-01` runs at `192.168.30.10/24` on VLAN 30, gateway `192.168.30.1`, as VM 121 on `grey-server` with `net0: virtio,bridge=vmbr0,firewall=1,tag=30`. DMZ (30) serves DHCP from `.50` to `.100`. DMZ-A (VLAN 90) is defined and empty.

Cloudflare is untouched. The tunnel's wildcard rule still points at `http://localhost:80` and its Coolify rule still points at `192.168.80.10:8000`, so no ingress rule, DNS record, or Access policy referenced the address that moved.

## Verification

| Check | Observed result |
|---|---|
| Address on `ens18` | `192.168.30.10/24` |
| Default route | via `192.168.30.1` |
| `caddy` and `cloudflared` | Both active |
| Cloudflare tunnel | Healthy, 4 connections |
| Caddy to Traefik across VLAN 30 to 80 | HTTP 404 from Traefik, which is the expected result for an unknown host |
| `coolify-a1.alphsec.com` from outside | HTTP 403 from Cloudflare Access, unauthenticated request refused as designed |
| Wazuh agent | Active, ESTABLISHED from `192.168.30.10` to `192.168.72.2:1514`, no re-registration needed |
| Prometheus target | `up` at `http://192.168.30.10:9100/metrics` |
| SSH Manager | Connects to `edge-01` at the new address |
| Clients on `192.168.90.0/24` | None |
| Proxmox cluster | 5 nodes, quorate, both Corosync links connected |

The Wazuh result closed the one dependency I could not read before the change. Reading the agent's registration state needs root on both the agent and the manager, which I did not have non-interactively, so I could not confirm in advance whether it was registered against a fixed address. It reconnected from the new address on its own.

## Rollback

Set `net0` back to `tag=90`, restore the `interfaces` file, and reboot VM 121. The pre-change file is committed at [Backups/edge-01-interfaces-2026-08-07](../../../../../Backups/edge-01-interfaces-2026-08-07) and I deleted the copy from the host after the change was verified. Restoring VLAN 90 to the `Proxmox-Trunk` exclusion list would also be needed to return the trunk to its earlier shape.

## Remaining Work

- Delete DMZ-A (VLAN 90), its honeypot at `192.168.90.2`, and its rows from the records after the soak period.
- `Block DMZ to Internal` at index 40000 and `Block DMZ to LAN` at index 40001 are identical: both block `Dmz ANY` to `Internal ANY`. One of them does nothing.
- DMZ (30) is not in the Threat Management network list, so `edge-01` is uninspected. It was uninspected on VLAN 90 as well, so this is not a regression, but the edge host is a reasonable candidate for coverage.
