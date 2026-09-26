# Physical Hardware

**Created:** 2026-07-22  
**Last updated:** 2026-09-25

Specifications and power for my physical equipment: five Galaxy nodes, two workstations, two UPS units and the drives. Guest and service inventories are under [Operations/Inventory](../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md).

| Record | Contents |
| --- | --- |
| [Galaxy node specifications](Nodes.md) | Five Proxmox nodes: processors, memory, graphics, storage, addresses and UPS assignments |
| [Component inventory](Components/README.md) | Individual components, slotted or spare, one folder per type, with raw `smartctl` captures for the drives |
| [Jedi PC](Workstations/Jedi%20PC.md) | Windows 11 Pro administration workstation on Secure, VLAN 50 |
| [ObiPC](Workstations/ObiPC.md) | Physical end-user workstation on the domain, joined 2026-09-11, rebuilt 2026-09-18 |
| [Power equipment](Power.md) | UPS models, inventory identifiers, connected loads and NUT monitoring |

## Dated records

| Date | Record |
| --- | --- |
| 2026-09-20 | [ObiPC Shutdown](Documentation/Change%20Records/ObiPC%20Shutdown%20-%202026-09-20.md) |
| 2026-07-31 | [Galaxy Green and Blue hardware changes](Documentation/Change%20Records/Galaxy%20Green%20and%20Blue%20Hardware%20Changes%20-%202026-07-31.md): RAM redistribution, added SATA HDDs, extended SMART tests |
| 2026-07-31 | [Lenovo M920q remote power options research](Documentation/Lenovo%20M920q%20Remote%20Power%20Options%20Research%20-%202026-07-31.md): Intel AMT, Wake-on-LAN, managed outlets |
| 2026-07-22 | [UPS installation and load assignment](Documentation/Change%20Records/APC%20Back-UPS%20Pro%20Installation%20and%20Load%20Assignment%20-%202026-07-22.md) |
| 2026-07-22 | [UPS monitoring options research](Documentation/UPS%20Monitoring%20Options%20Research%20-%202026-07-22.md): NUT, apcupsd, USB ownership, multi-node shutdown |

Two laptops on Trusted, VLAN 10, are enrolled in SSH Manager but have no hardware record yet: `surface_pro` (Surface Pro Model 1796, Ubuntu, 192.168.10.211) and `parrot` (Parrot OS, 192.168.10.176).
