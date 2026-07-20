# Splunk SIEM Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

I built a Rocky Linux VM for Splunk Enterprise, connected UniFi CEF events through SC4S and HEC, routed network data into `netops`, & installed Splunk Enterprise Security. The screenshots below stay with the original Splunk record and appear beside the steps they show.

## Current Status and Verified Versions

VM 109 `splunk-siem` runs Rocky Linux 10.2 on VLAN 72 at `192.168.72.3`. The current VM has 6 vCPU, 12 GiB memory, & a 150 GiB disk. Splunk Enterprise 10.4.0 receives SC4S events through HEC on 8088; SC4S 3.45.0 listens for CEF on TCP and UDP 1514.

## What You Need

- A Proxmox host with capacity for the VM.
- Rocky Linux 10.2 installation media.
- A Splunk Enterprise license and installation package.
- A UniFi console that can export System Logging/SIEM events.
- Network paths for Splunk Web, HEC, management, & CEF ingestion.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Create the VM

I created VM 109 with UEFI, q35, a host CPU type, guest agent, SSD emulation, discard, iothread, & Proxmox firewall enabled. I started with 4 vCPU and later raised it to 6 for the Enterprise Security setup.

![Splunk VM configuration](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/vm-config-1%20%281%29.png)

### Step 2: Install Rocky Linux

I installed Rocky Linux 10.2 without a desktop, set hostname `splunk-siem`, & configured the administrator account and network. The build later moved from its initial management address to `192.168.72.3` on Security-A.

![Rocky Linux network setup](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-06-28%20175948.png)

### Step 3: Update and Lock Down SSH

I ran the full package update, installed three Ed25519 public keys, set `PasswordAuthentication no` and `PermitRootLogin no`, validated `sshd`, & tested a second key session before closing the first.

### Step 4: Install Splunk Enterprise

I installed the Splunk 10.4.0 RPM under the dedicated `splunk` account and enabled its systemd-managed boot service. That service applies the required process, file, & Transparent Huge Pages settings.

```sh
sudo rpm -i /tmp/splunk-10.4.0-f798d4d49089.x86_64.rpm
sudo chown -R splunk:splunk /opt/splunk
sudo /opt/splunk/bin/splunk enable boot-start \
  -user splunk -systemd-managed 1 --accept-license
sudo systemctl start Splunkd
```

![Splunk Web login](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-06-29%20212751.png)

### Step 5: Create HEC and the Network Indexes

I created the bounded network indexes and an HEC input for SC4S, then checked the collector health endpoint on 8088.

![Splunk HEC configuration](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-06-30%20000305.png)

### Step 6: Deploy SC4S

I ran SC4S 3.45.0 in Podman under systemd, set the receive buffers, opened TCP and UDP 1514, & pointed its HEC output at Splunk. I checked the listeners, container health, HEC reachability, & SC4S logs before sending UniFi data.

![SC4S running](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-06-30%20133108.png)

### Step 7: Send UniFi CEF Events

I enabled Network, UniFi OS, & Protect categories in UniFi's System Logging/SIEM settings and sent them to `192.168.72.3:1514`. I generated a test event and found its parsed CEF fields in Splunk.

![First UniFi CEF event](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-06-30%20134033.png)

### Step 8: Route Network Data to netops

I updated the SC4S routing so new UniFi Network, OS, & Protect events landed in `netops`. I searched both `netops` and `main` over the same time window to confirm new CEF data stopped leaking into `main`.

![Final netops search](../Platforms/Splunk/Splunk%20Enterprise/Evidence/Screenshots/Screenshot%202026-07-01%20201953.png)

### Step 9: Install Enterprise Security

I uploaded the Enterprise Security package through Splunk Web. Its setup was CPU-bound at 4 vCPU, so I raised the VM to 6 vCPU and confirmed Enterprise Security loaded through Mission Control and its configuration page.

## What I Checked After Each Step

- Splunkd ran as `splunk` under systemd and returned the Web login page.
- HEC health returned HTTP 200 on 8088.
- SC4S listened on TCP and UDP 1514 and could reach HEC.
- A generated UniFi event arrived as parsed CEF.
- New UniFi events landed in `netops` and not `main`.
- Enterprise Security loaded after the VM received 6 vCPU.

## Troubleshooting and Recovery

If SC4S receives packets but Splunk has no events, check the HEC health endpoint, token assignment, SC4S destination, & container logs. If data reaches the wrong index, search by `_time`, `host`, and `sourcetype` before editing the routing file. Restore the last working SC4S environment and restart its systemd unit if a route change breaks ingestion.

## Known Limits

Enterprise Security installation is recorded, but its broader configuration backlog isn't complete. The historical build began on VLAN 70 and later moved to VLAN 72, so use the current address `192.168.72.3` when following the guide.

## Source Records

- [Splunk Enterprise build log](../Platforms/Splunk/Splunk%20Enterprise/Documentation/Build-Log.md)
- [VM specifications](../Platforms/Splunk/Splunk%20Enterprise/Documentation/VM-Specs.md)
- [UniFi CEF reference](../Platforms/Splunk/Splunk%20Enterprise/Documentation/UniFi-CEF-Reference.md)
- [Splunk Enterprise troubleshooting](../Platforms/Splunk/Splunk%20Enterprise/Documentation/Troubleshooting-Log.md)
- [Enterprise Security build log](../Platforms/Splunk/Splunk%20ES/Documentation/Build-Log.md)
