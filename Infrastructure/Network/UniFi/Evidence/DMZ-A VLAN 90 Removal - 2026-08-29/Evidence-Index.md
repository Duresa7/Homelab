# DMZ-A VLAN 90 Removal Evidence

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

Supports [DMZ-A VLAN 90 Removal - 2026-08-29](../../Documentation/Change%20Records/DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md).

Step numbers run S01 to S21 across six evidence folders, because these six jobs were one sitting and I want them walkable in order. This folder holds S01 to S03. All captures are headless, so no pointer appears in any of them.

| Step | Capture | What it shows |
|---:|---|---|
| 1 | [Networks before removal](Screenshots/S01-UniFi-Networks-Before-DMZ-A-Removal-2026-08-29.png) | The Networks table with DMZ-A present, the starting state I deleted from. |
| 2 | [Networks after removal](Screenshots/S02-UniFi-Networks-After-DMZ-A-Removal-2026-08-29.png) | The same table with DMZ-A gone and DMZ (30) still present. 15 routed LANs of 22 objects. |
| 3 | [Honeypot table](Screenshots/S03-UniFi-Honeypot-Table-Without-VLAN-90-2026-08-29.png) | CyberSecure listing three honeypots, none on `192.168.90.0/24`. Deleting the network took its honeypot with it. The same page shows Threat Management inspecting six networks, with DMZ (30) absent, which is the finding the record raises. I closed it on 2026-08-30 in [DMZ Added to Threat Management](../../Documentation/Change%20Records/DMZ%20Added%20to%20Threat%20Management%20-%202026-08-30.md), so this capture is the before state for that change too. |
