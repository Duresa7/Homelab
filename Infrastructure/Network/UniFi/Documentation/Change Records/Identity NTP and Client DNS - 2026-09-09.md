# Identity NTP and client DNS

**Created:** 2026-09-09  
**Last updated:** 2026-09-09

I moved Allow Identity NTP Egress above Block Identity Other External Egress and changed DHCP DNS on Secure (VLAN 50) and Secure Client (VLAN 60) from automatic to 192.168.65.10 followed by 192.168.65.11. The original session reported both changes saved and verified after reload. I resumed the unfinished evidence capture at approximately 10:25 PM Eastern and independently read the saved settings through Chrome at https://unifi.duresakadi.com, Network 10.6.101, site default. I made no further configuration changes during this verification.

After reloading the zone page and selecting AlphaSec-Identity to External, I observed this order:

| Order | Policy | Action | Protocol / destination ports | Index |
|---|---|---|---|---|
| 1 | Allow Identity Web Egress | Allow | TCP 80,443 | 10000 |
| 2 | Allow Identity NTP Egress | Allow | UDP 123 | 10001 |
| 3 | Block Identity Other External Egress | Block | All | 10002 |

The NTP rule showed 34 hits. The pair also displays two built-in policies below the three custom policies. I left them unchanged.

| Network | DNS first | DNS second | Gateway | DHCP range |
|---|---|---|---|---|
| Secure, VLAN 50 | 192.168.65.10 | 192.168.65.11 | 192.168.50.1/24 | 192.168.50.6–192.168.50.254 |
| Secure Client, VLAN 60 | 192.168.65.10 | 192.168.65.11 | 192.168.60.1/24 | 192.168.60.6–192.168.60.254 |

Both network panels showed Auto DNS Server unchecked and the ordered DNS list above. This UI uses a list rather than numbered DNS Server 1 and DNS Server 2 fields. The prior session reported gateways, subnets and DHCP ranges unchanged; the resumed read matched those values. No network or policy was missing.

I retained the final-state screenshots below, cropped to the relevant settings so no cursor is visible. No screenshot of the original save actions was recovered; these captures show the saved state during the resumed verification.

- [Firewall order](../../Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/01-Firewall-Order.png)
- [Secure DNS](../../Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/02-Secure-DNS.png)
- [Secure Client DNS](../../Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/03-Secure-Client-DNS.png)

The requested controller changes and evidence capture are complete. I did not test DHCP renewal or DNS resolution on client devices, or time synchronization on the domain controllers.

## Time synchronisation after the reorder

I verified the domain side at approximately 11:25 PM Eastern, which the earlier capture had left untested. Before the reorder HQ-DC01 was running on its own CMOS clock; it now holds an external source, and the two downstream hosts follow it.

| Host | Time source | Stratum | Last successful sync |
|---|---|---|---|
| HQ-DC01 | time.cloudflare.com | 4 | 2026-09-09 11:22:33 PM |
| HQ-DC02 | HQ-DC01.ad.alphasecunited.com | 5 | 2026-09-09 11:22:43 PM |
| HQ-MGT01 | HQ-DC02.ad.alphasecunited.com | 6 | 2026-09-09 11:24:36 PM |

HQ-MGT01 first answered `The computer did not resync because no time data was available` on two attempts. That was the client still collecting samples, not a blocked path: `w32tm /stripchart` reached both domain controllers on UDP 123 throughout, and the System log recorded event 37, valid time data from HQ-DC02, at 11:24:19 PM. The next resync succeeded. Root dispersion was still wide at 21.8 s immediately after the chain came up and narrows as polls accumulate.

## Client DNS reachability

The DHCP change hands VLAN 50 and VLAN 60 the two domain controllers, which are in AlphaSec-Identity while both client networks are in Internal, so the path crosses a zone boundary. That path was already permitted before this change by `Allow Workstations to AD` at index 10000: source Internal matching the Secure and Secure Client networks, destination AlphaSec-Identity / AG-Domain-Controllers / PG-AD-Client, TCP and UDP, enabled. AG-Domain-Controllers holds 192.168.65.10 and 192.168.65.11, and PG-AD-Client holds 53, 88, 123, 135, 389, 445, 464, 636, 3268, 3269 and 49152-65535, so DNS and the rest of the domain-join port set are covered. No new policy was required.

I briefly created a narrower duplicate, `Allow Secure Clients to Identity DNS`, after reading a policy list that the controller had capped at 200 of roughly 351 entries and that therefore omitted the existing rule. I deleted it once I confirmed the overlap; the readback shows no policy of that name and no orphaned response rule, and `Allow Workstations to AD` is unchanged.

Both domain controllers accept DNS on any profile from any address: `DNS (TCP, Incoming)` and `DNS (UDP, Incoming)` are enabled with remote address Any, and both report NetworkCategory DomainAuthenticated. Jedi PC at 192.168.50.241 is the only client currently on either VLAN, and that address falls inside the Secure DHCP pool of 192.168.50.6 to 192.168.50.254, so it takes the new resolvers at its next lease renewal. I did not test resolution from a VLAN 50 or VLAN 60 host, because no host on either network is reachable through SSH Manager.
