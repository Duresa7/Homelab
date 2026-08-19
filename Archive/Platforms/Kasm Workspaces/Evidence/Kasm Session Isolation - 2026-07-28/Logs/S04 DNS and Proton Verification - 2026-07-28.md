# S04 DNS and Proton Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture date:** 2026-07-28  
**Targets:** UniFi VLAN 77 DHCP, `KASM Lab Proton Egress`, and the ProtonVPN client  
**Mechanism:** UniFi Network MCP and harmless containers on VM 122

## Final Controller State

I read the following final values from UniFi:

```text
MALWARE-OFFLINE VLAN: 77
MALWARE-OFFLINE DHCP DNS enabled: false
Traffic route: KASM Lab Proton Egress
Traffic route enabled: true
Traffic route matching target: INTERNET
Traffic route target network: KASM-BROWSER
Traffic route kill switch enabled: true
VPN client: ProtonVPN
VPN client enabled: true
VPN client type: wireguard-client
```

The complete structured requests and redacted controller results are retained in [S01 UniFi Final State Verification](S01%20UniFi%20Final%20State%20Verification%20-%202026-07-28.md).

## Lane Results

The exact commands and complete lane output are retained in [S06 Containment and Cleanup Verification](S06%20Containment%20and%20Cleanup%20Verification%20-%202026-07-28.md) and [S06 Host and Direct-IP Acceptance Verification](S06%20Host%20and%20Direct-IP%20Acceptance%20Verification%20-%202026-07-28.md).

```text
lab74 DNS: passed
lab74 HTTPS exit: 185.98.168.20
lab74 direct TCP to 1.1.1.1:443: open
lab77 DNS: failed
lab77 hostname HTTPS: failed
lab77 direct TCP to 1.1.1.1:443: blocked
lab79 DNS: failed
lab79 hostname HTTPS: failed
lab79 direct TCP to 1.1.1.1:443: blocked
```

The raw-IP checks prove that VLANs 77 and 79 lack Internet access independently of their failed resolvers.

## Failure Test

I temporarily replaced the enabled Proton client's endpoint with `192.0.2.1:51820`. VLAN 74 then lost Internet while the Kasm management host kept ordinary WAN access. I restored the production endpoint, and VLAN 74 returned through `185.98.168.20`.

I did not retain the endpoint mutation request or the first failure-injection transcript because the production WireGuard configuration contains secret material. S01 retains the final enabled client with its configuration redacted. S06 retains the restored Proton exit and final cleanup state.
