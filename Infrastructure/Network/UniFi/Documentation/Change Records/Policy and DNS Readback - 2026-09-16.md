# Policy and DNS Readback

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Readback date:** 2026-09-16  
**Status:** Complete; documentation correction only, no controller change  
**Affected records:** [Firewall policies](../../Configuration/firewall.md), [Local DNS](../../Configuration/local-dns.md)

On 2026-09-16 I read the firewall policies and static DNS records back after the Portainer retirement. The retirement itself, which removed two Portainer Edge allow policies, TCP 9443 from `Allow NPM to docker-main web UIs` and the `portainer.alphasecunited.com` record, is in [Portainer Retirement](../../../../../Archive/Platforms/Portainer/Documentation/Change%20Records/Retirement%20-%202026-09-16.md). This record covers what the same readback found in the configuration views. I wrote it on 2026-09-25 from the paragraphs those views carried.

## Firewall

The controller returned 86 user-defined policies, 78 allows and eight blocks, with 85 enabled and no name or selector matching Portainer. `Allow NPM to docker-main web UIs` kept TCP 2283, 3000, 3001, 3002, 3003 and 6060.

Two live policies were missing from the policy table, so I added their rows without changing the controller:

- `Allow Automation to Identity SSH` admits `AG-Automation-Hosts` in Internal to `AG-Identity-Servers` in `AlphaSec-Identity` on TCP 22.
- `Allow Surface SSH replies to Automation` matches established and related IPv4 TCP replies only, from `192.168.10.211` source port 22 to `192.168.40.179` and `192.168.40.39`, all in Internal.

The second policy was created after the 2026-09-13 count of 85. That is why the total read 86 rather than the 85 that the two removals and two additions would give on their own.

## Local DNS

The controller held 29 static DNS records, 23 of them pointing at Nginx Proxy Manager on `192.168.85.2`, including the unchanged Dockhand record. The readback also returned `hq-mgt01.ad.alphasecunited.com` to `192.168.65.12`, which the DNS table had not carried since the 2026-09-12 [Windows Admin Center deployment](../../../../../Platforms/Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md). I added its row.

No separate export was retained for this readback.
