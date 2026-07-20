# Network Segmentation TODO

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

I've already built the zones (`<YOUR_ORG_NAME>`-Access, `<YOUR_ORG_NAME>`-Security, `<YOUR_ORG_NAME>`-Cluster), the networks (Access-A/85, Security-A/72, Cluster-Net/71), and the Zone Matrix / firewall policies connecting them. Remaining work is below.

## Access-A Deployment

- [x] Deploy network-access / connectivity tooling onto Access-A: Nginx Proxy Manager 2.15.1 and NetBird 0.74.3 now run on LXC 107 `docker-network`
- [x] Assign a static IP from the reserved range: `192.168.85.2/24` (DHCP pool starts at `.6`)
- [x] Confirm reachability from both Internal and VPN. I verified internal DNS and application administration; I validated the VPN-client path into Access-A on 2026-07-12 via a NetBird routing peer (see the [change record](../../../../../Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md))
- [x] Add least-privilege outbound policies: TCP 80/443 and UDP 123 are allowed only from `192.168.85.2`, followed by an ordered block for all other `<YOUR_ORG_NAME>`-Access-to-External IPv4 traffic

The infrastructure implementation is recorded in [Galaxy Docker-Network LXC Deployment - 2026-07-10](../../../../Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md). Certificate, proxy-host, HTTPS login, and Compose restart validation are complete; I completed the first-peer enrollment and VPN-client path into Access-A on 2026-07-12 and recorded them in the NetBird [change record](../../../../../Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

I left the web and NTP destination addresses dynamic because Debian mirrors, container registries, certificate services, and NTP pools can rotate. Least privilege is enforced through the single-host source match, required ports only, ordered catch-all block, and logging rather than a brittle destination-IP list.

## Security-A Migration

- [x] Move the security/monitoring tooling (SIEM, detection, log/metrics tooling) to Security-A
- [x] Assign static IPs in the 192.168.72.2 – .5 reserved range (DHCP pool starts at .6): `security-01` = `192.168.72.2`, `splunk-siem` = `192.168.72.3`
- [x] Add narrow inbound firewall policies from every zone that needs to ship logs/metrics in, pointing at the new Security-A IPs (mirror the existing Wazuh-ports pattern)
- [x] Remove the old rules/references pointing at the previous MGMT-A (`<YOUR_PREVIOUS_MANAGEMENT_SUBNET>`) addresses once the migration is confirmed working

Completed 2026-07-12. The VM cutovers, replacement firewall paths, Security-A egress policy, Galaxy firewall changes, cleanup, rollback points, and verification are recorded in [Security-A Migration - 2026-07-12](../Change%20Records/Security-A%20Migration%20-%202026-07-12.md).

I updated the UniFi console SIEM/syslog destination to `192.168.72.3:1514` on 2026-07-12. A fresh CEF event was processed by SC4S, forwarded through HEC without drops, and indexed in Splunk's `netops` index. No additional Gateway-to-Security policy was required.

### Deferred follow-ups

- [x] Audit and reset the old Wazuh agents: I removed the disconnected `edge-01` and incorrect `wp-01` registrations and repointed/cleared `app-01` and `edge-01` so I can re-enroll them. `supabase-01` and `alpha-prod-01` have no agent installed; fresh enrollment is tracked in the [Wazuh TODO](../../../../../Platforms/Wazuh/Documentation/TODO.md).
- [x] Install and configure `node_exporter` on `purple-server`, `blue-server`, and `red-server`; all three targets report `UP`.
- [x] Reconcile stale Prometheus targets: corrected `security-01`, removed unavailable `app-01`/`supabase-01`, and verified exactly seven retained jobs `UP`.
- [ ] Review whether the retained Galaxy firewall accept for TCP 8006 from `192.168.70.0/24` can be narrowed in the MGMT-A lockdown change.

The three completed follow-ups are recorded in [Security Monitoring Baseline Cleanup - 2026-07-13](../../../../../Platforms/Prometheus/Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md).

## Next Bounded Change: MGMT-A Final Lockdown

I've resolved the allowed-set decision: MGMT-A may be reached from Trusted (VLAN 10), Secure (VLAN 50), the existing WireGuard VPN zone, and future NetBird traffic arriving from `<YOUR_ORG_NAME>`-Access through its routing peer. Next I implement and validate the final MGMT-A block policy; I kept it out of the Security-A migration's scope on purpose, and it stays a separate bounded change.

## Cluster-Net Corosync Link Addition

- [x] Confirm SSH is reachable on all four nodes (grey-server, purple-server, blue-server, red-server)
- [x] Verify each node's physical switch port uses the Proxmox-Trunk profile and carries Cluster-Net/71
- [x] Add a second interface per node on Cluster-Net: grey=192.168.71.10, purple=.11, blue=.12, red=.13
- [x] Add this as Corosync link1 alongside the existing link0 on MGMT-A; link0 was preserved
- [x] Verify cluster health after the change (`pvecm status` showed all 4 nodes, quorum intact, both links active)
- [x] Confirm GUI/SSH access via the original 192.168.70.10 – .13 addresses is unaffected

Completed 2026-07-10. The authoritative record, exact command transcripts, configuration exports, and step screenshots are in [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../../../../Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md).
