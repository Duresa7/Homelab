# NetBird Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I deployed a self-hosted NetBird control plane, published it through Nginx Proxy Manager, enrolled the first peer, & built a routed path into VLAN 85. This guide follows those operations in the order I performed and checked them.

## Current Status and Verified Versions

NetBird v0.74.4 runs on CT 107 `docker-network` at `192.168.85.2`. The dashboard binds `127.0.0.1:8080`, the combined server binds `127.0.0.1:8081`, & STUN uses UDP 3478. The recorded routed peer uses overlay address `100.121.111.204` to advertise `192.168.85.0/24` with masquerade enabled.

## What You Need

- A Debian Docker host with TCP 80, 443, & UDP 3478 available.
- An internal DNS name such as `<YOUR_NETBIRD_DOMAIN>`.
- Nginx Proxy Manager on the same external Docker network.
- One client device for peer enrollment and route testing.
- Firewall access from the routing peer to the destination subnet.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Prepare CT 107 and Docker

I created CT 107 on VLAN 85, applied key-only SSH, installed Docker, & created `/opt/docker/netbird` plus the external `proxy` network. I checked Docker, DNS, NTP, & web egress before deploying NetBird.

![docker-network ready for NetBird](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S03-Docker-Network-SSH-HA-Ready-2026-07-10.jpg)

### Step 2: Run the Verified Installer

I downloaded the official v0.74.3 installer, verified SHA-256 `371ac85e4f56dc8e6d3abf14601f35d0d061b3712f2e60ce76f2e6832f3a1461`, selected the Nginx Proxy Manager integration, & kept the direct HTTP services on loopback. I later updated the running deployment to v0.74.4.

### Step 3: Correct Proxy Trust and Check Containers

I changed the generated trusted-proxy address to Nginx Proxy Manager's fixed `172.31.85.10/32`, recreated the NetBird containers, & checked the direct dashboard and identity-provider endpoints for HTTP 200.

### Step 4: Publish the Control Plane

I created the internal DNS record for `<YOUR_NETBIRD_DOMAIN>`, added the Nginx Proxy Manager host and advanced NetBird routes, assigned its certificate, & enabled Force SSL and HTTP/2.

![Authenticated NetBird dashboard](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S08-NetBird-Authenticated-Dashboard-2026-07-11.jpg)

### Step 5: Enroll the First Peer

I generated a peer setup key, installed the NetBird client on Debian, & joined it to the self-hosted management URL. The client reported connected before I created a network route.

![First Debian peer connected](../Platforms/Netbird/Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S01-First-Peer-Debian-Connected-2026-07-12.png)

### Step 6: Create the Resource and Policy

I added `192.168.85.0/24` as the routed resource, assigned the intended peer groups, & created the access policy for only those sources and destinations.

![NetBird resource details](../Platforms/Netbird/Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S07-Add-Resource-Details-2026-07-12.png)

![NetBird access policy](../Platforms/Netbird/Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S09-Resource-Access-Policy-2026-07-12.png)

### Step 7: Assign the Routing Peer

I selected the `docker-network` peer, enabled masquerade, & confirmed the completed network showed the resource, policy, and routing peer together.

![Routing peer with masquerade](../Platforms/Netbird/Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S11-Routing-Peer-Advanced-Masquerade-2026-07-12.png)

### Step 8: Prove the Tunnel Path

I checked the client's NetBird route, reached the VLAN address through the tunnel, sent the intended SNI name, & received HTTPS 200.

![HTTPS 200 through the NetBird tunnel](../Platforms/Netbird/Evidence/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12/Screenshots/S15-Debian-HTTPS-200-Through-Tunnel-2026-07-12.png)

## What I Checked After Each Step

- Both NetBird containers returned to running after recreation and restart.
- The direct dashboard and identity-provider probes returned HTTP 200.
- Nginx Proxy Manager resolved both containers over the `proxy` network.
- The HTTPS dashboard loaded and accepted the administrator login.
- The first peer reported connected.
- The client installed the route and received HTTPS 200 through it.

## Troubleshooting and Recovery

If the public name fails but loopback probes work, test DNS, Nginx configuration, container-name resolution, & the trusted-proxy address in that order. If the peer connects without reaching the resource, check its group, policy, routing peer, masquerade setting, destination firewall, & installed route. Preserve `netbird_data` when recreating containers.

## Known Limits

The route in this record covers `192.168.85.0/24`; it doesn't grant blanket access to other VLANs. The remaining optional hardening items were closed or declined in the 2026-07-12 follow-up record.

## Source Records

- [Deployment record](../Platforms/Netbird/Documentation/Deployment.md)
- [First peer and routed VPN path](../Platforms/Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md)
- [Operational follow-ups](../Platforms/Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [Runbook](../Platforms/Netbird/Documentation/Runbook.md)
