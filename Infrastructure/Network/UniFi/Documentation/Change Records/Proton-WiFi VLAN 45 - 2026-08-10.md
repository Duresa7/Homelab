# Proton-WiFi VLAN 45

**Created:** 2026-08-11  
**Last updated:** 2026-08-11

## Date

I completed this change on 2026-08-10 between 9:58 PM and 10:36 PM.

## Scope

I built a wireless network whose traffic leaves through my ProtonVPN WireGuard client instead of the WAN. A device joining the `Proton-WiFi` SSID lands on VLAN 45, cannot reach any other network, cannot reach the other devices on the same SSID, and loses Internet access entirely if the tunnel drops.

Three objects make it work: the network, the SSID bound to it, and a traffic route that pins the network to the ProtonVPN interface. The route is the part that supplies the VPN egress. The first two on their own produce an isolated VLAN that still exits over the WAN.

I did not create a new VPN client, a new firewall zone, or any firewall policy.

## Starting State

The ProtonVPN client already existed and was enabled: WireGuard, `wg-US-GA-568.conf`, tunnel address `10.2.0.2/32`, in the `External` zone.

Two traffic routes already pointed at it:

- **KASM Lab Proton Egress**, enabled, kill switch on, targeting KASM-BROWSER (VLAN 74). This is the working precedent I copied. KASM-BROWSER sets DHCP DNS to Quad9 for the same reason I do below.
- **VPN - Proton**, disabled, kill switch on, targeting a single client by MAC (`<REDACTED_CLIENT_MAC>`, my MacBook Air on Trusted/VLAN 10). Because it was disabled, that target had no effect on anything.

VLAN 45 was free. Used IDs ran 5, 10, 20, 30, 40, 50, 60, 70 through 75, 77 through 80, 85, and 90.

## Actions

### S01: Create the network

I created `Proton-WiFi`, purpose `corporate`, `192.168.45.1/24`, VLAN 45, DHCP from `192.168.45.100` to `.199` on a 3600 second lease, UPnP off, network isolation on.

I set DHCP DNS manually to `9.9.9.9` and `149.112.112.112`. On automatic DNS the gateway resolves against the ISP even while the traffic itself is tunnelled, which publishes every lookup to the one party the tunnel exists to exclude. Pointing clients at a public resolver sends the queries down the tunnel with everything else. KASM-BROWSER was already configured this way.

The controller placed the network in the built-in `Internal` zone.

### S02: Create the SSID

I created the `Proton-WiFi` WLAN bound to network `6a7a85ffdee8c70a32df35b3`, on the default AP group across both bands, and left it disabled with a placeholder passphrase.

Two payloads were rejected before one was accepted. `security: wpa2-psk` returned `api.err.InvalidValue`; the controller wants `wpapsk` with `wpa_mode: wpa2`. The corrected payload then returned `api.err.ApGroupMissing`, because a WLAN will not create without an explicit `ap_group_ids` value.

### S03: Enable client isolation

I set `l2_isolation` on the WLAN, so two devices associated to the same SSID cannot address each other.

### S04: Retarget and enable the traffic route

I changed the target of **VPN - Proton** from the single client MAC to network `Proton-WiFi`, then enabled the route. Matching target stayed `INTERNET` and the kill switch stayed on.

### S05: Set the passphrase and enable the SSID

I replaced the placeholder passphrase with a real one, stored it in my password manager, and enabled the SSID. I also turned on WPA2/WPA3 transition mode, which requires PMF `optional`: WPA3 mandates protected management frames and WPA2 clients cannot negotiate them, so `required` locks out WPA2 devices and `disabled` breaks WPA3. Transition mode has exactly one valid PMF value.

## Decisions

- **I reused the disabled `VPN - Proton` route rather than creating a second one.** It already pointed at the ProtonVPN interface with the kill switch on, and its name still describes what it does. The client MAC it used to target is gone from the configuration, which costs nothing because the route was disabled.
- **I used the network isolation toggle rather than a dedicated firewall zone.** Isolation blocks VLAN 45 from every other network in one setting. The KASM zones exist to express deliberate relationships between lab networks, and VLAN 45 has no such relationships to express.
- **I left the SSID disabled until the route existed.** An enabled SSID with no traffic route is a network that looks private and is not, which is worse than one that is plainly unavailable.
- **I took no snapshot.** Every change here is a new object or a single reversible field.

## Resulting Configuration

`Proton-WiFi` is VLAN 45 at `192.168.45.1/24`, DHCP `.100` to `.199`, DNS `9.9.9.9` and `149.112.112.112`, network isolation on, in the `Internal` zone. The `Proton-WiFi` SSID is enabled on both bands with WPA2/WPA3 transition, PMF `optional`, and L2 isolation on. The `VPN - Proton` traffic route is enabled, targets the network, matches any Internet destination, exits through ProtonVPN, and has the kill switch on.

`KASM Lab Proton Egress` is unchanged and still targets VLAN 74 alone.

The controller added VLAN 45 to the `Proxmox-Trunk` exclusion list on its own, as it does for every new network. The list now holds Management, IoT (20), Trusted (10), Secure (50), and Proton-WiFi (45). I left it there because VLAN 45 is a wireless network with no reason to reach a hypervisor.

## Verification

Every row is a readback from the controller after the change, not the value I sent.

| Check | Observed result |
|---|---|
| Network `Proton-WiFi` | `vlan: 45`, `ip_subnet: 192.168.45.1/24`, `network_isolation_enabled: true` |
| DHCP DNS | `dhcpd_dns_1: 9.9.9.9`, `dhcpd_dns_2: 149.112.112.112`, `dhcpd_dns_enabled: true` |
| WLAN `Proton-WiFi` | `enabled: true`, `l2_isolation: true`, `networkconf_id` matches the network |
| WLAN security | `security: wpapsk`, `wpa3_support: true`, `wpa3_transition: true`, `pmf_mode: optional` |
| Route `VPN - Proton` | `enabled: true`, `target_devices: [{type: NETWORK, network_id: <Proton-WiFi>}]`, `matching_target: INTERNET`, `kill_switch_enabled: true` |
| Route interface | `network_id` resolves to the ProtonVPN client |
| ProtonVPN client | `enabled: true`, `wg-US-GA-568.conf`, `10.2.0.2/32` |
| VPN subsystem health | `ok` |
| `KASM Lab Proton Egress` | Unchanged, still `target_devices: [KASM-BROWSER]` |
| Live client | An iPad associated to `Proton-WiFi` and held `192.168.45.129`, inside the configured pool |
| `Proxmox-Trunk` exclusions | Five entries, including Proton-WiFi (45) |

Three writes in this change returned an error and had already committed: two as `'WriteVerificationResult' object has no attribute 'get'` and one as `cannot unpack non-iterable WriteVerificationResult object`. The fault is in the management tool's post-write verification step, after the controller accepted the write. This is why every row above is a fresh read rather than a returned value, and it is worth remembering the next time a write here appears to fail.

## Rollback

Disable the `Proton-WiFi` SSID, disable the `VPN - Proton` route, and delete the WLAN and the network. Restoring the route to its previous shape means setting its target back to the single client MAC and disabling it. Removing VLAN 45 from the `Proxmox-Trunk` exclusion list is not needed, because deleting the network removes the entry.

## Remaining Work

- Confirm the exit address from a client on the SSID. The controller can prove the route is configured and the tunnel is up, but not that a given client's packets left through it. The check is a request to an address-reporting site from a device on `Proton-WiFi`, which should return a Proton address in Georgia.
