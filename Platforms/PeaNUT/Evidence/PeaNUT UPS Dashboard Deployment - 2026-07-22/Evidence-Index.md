# PeaNUT UPS Dashboard Deployment Evidence Index

**Created:** 2026-07-22  
**Last updated:** 2026-08-01

| Step | Artifact | Demonstrates |
| --- | --- | --- |
| Step 3 | [Red NUT package installation](Logs/S03-NUT-Package-Install-red-server.txt) | Debian installed NUT 2.8.1-5 and its dependencies on Red |
| Step 3 | [Grey NUT package installation](Logs/S03-NUT-Package-Install-grey-server.txt) | Debian installed NUT 2.8.1-5 and its dependencies on Grey |
| Step 3 | [Red NUT first configure attempt](Logs/S03-NUT-Configure-red-server.txt) | The udev reload and service restart run that exited 3 on Red before the USB permission fix landed |
| Step 3 | [NUT configuration corrections](Logs/S03-NUT-Configuration-Corrections.txt) | Red's SSH deploy failure, both USB permission failures, exact corrections, and validated results |
| Step 4 | [Galaxy firewall compilation](Logs/S04-Proxmox-Firewall.txt) | Both destination-specific TCP/3493 rules compiled and the firewall stayed active |
| Step 5 | [Initial PeaNUT deployment](Logs/S05-Dashboard-Deploy.txt) | The pinned image pulled and started; the first health check timed out |
| Step 6 | [Red NUT verification](Logs/S06-NUT-Verification-red-server.txt) | `ups01`, its listener, services, and live telemetry passed |
| Step 6 | [Grey NUT verification](Logs/S06-NUT-Verification-grey-server.txt) | `ups02`, its listener, services, and live telemetry passed |
| Step 6 | [Red guest continuity](Logs/S06-Guest-Continuity-red-server.txt) | The running Red guest uptime predated the deployment and no running guest restarted |
| Step 6 | [Grey guest continuity](Logs/S06-Guest-Continuity-grey-server.txt) | All six running Grey guest uptimes predated the deployment and no running guest restarted |
| Step 6 | [PeaNUT and workload verification](Logs/S06-Dashboard-Verification.txt) | PeaNUT was healthy, both NUT endpoints were reachable from its container, and existing containers remained running |
| Step 6 | [Authenticated PeaNUT dashboard](Screenshots/S06-PeaNUT-Dashboard-After.png) | PeaNUT's device table displayed `ups01` and `ups02` online with live charge and load values |
