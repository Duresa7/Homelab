# openipmi Masked on Four Lenovo Nodes

**Created:** 2026-09-02  
**Last updated:** 2026-09-02

**Change date:** 2026-09-02  
**Status:** Complete. `openipmi.service` is masked on `red-server`, `purple-server`, `green-server` and `blue-server`, and no longer appears in `systemctl --failed` on any of them.  
**Scope:** One systemd unit on four Proxmox nodes. No package was removed, no kernel module was touched, and `grey-server` was not changed because it never had the unit.

## Outcome

`openipmi.service` had failed on every boot of four of the five Galaxy nodes, on `red-server` since 2026-08-28 and on the others since their own last boots on 2026-08-01, 2026-08-09 and 2026-08-18. It sat in the failed list next to `nut-monitor`, which is disabled by choice, and made that list look like two problems where there was one. I masked it. The service is the Linux driver for IPMI, the out-of-band management interface a server board exposes through a baseboard management controller, and none of these boards has one.

## State before the change

| Node | Board | `/dev/ipmi*` | DMI type 38 records | `openipmi` |
| --- | --- | --- | --- | --- |
| red-server | Lenovo 10RRS0LN00 | none | 0 | installed, enabled, failed |
| purple-server | Lenovo 10RRS0LN00 | none | 0 | installed, enabled, failed |
| green-server | Lenovo 10RRS0LN00 | none | 0 | installed, enabled, failed |
| blue-server | Lenovo 10MUS08B00 | none | 0 | installed, enabled, failed |
| grey-server | MSI MS-7C91 | none | 0 | not installed |

Three checks say the same thing on each of the four. There is no IPMI character device. The DMI table, which a board with a management controller uses to advertise it, holds zero records of type 38. And the unit's only journal line is systemd reporting that the LSB init script failed to start, which is what the script does when it finds no device. Two IPMI kernel modules load anyway and are harmless without hardware.

`apt-cache rdepends --installed openipmi` names one dependent, `ipmitool`, which arrived with the node_exporter collector tooling. The same package ships `prometheus-node-exporter-ipmitool-sensor.timer`, which is equally inert on this hardware. `grey-server` never received the package, which is why it was clean.

## What I changed

On each of the four nodes, through the SSH Manager gateway as root:

```
systemctl disable --now openipmi.service
systemctl mask openipmi.service
systemctl reset-failed openipmi.service
```

Masking rather than uninstalling keeps `ipmitool` and the node_exporter package intact. systemd reported the unit as non-native and redirected the disable through `systemd-sysv-install`, then created the symlink `/etc/systemd/system/openipmi.service` to `/dev/null`. The change is reversed with `systemctl unmask openipmi.service`.

## Verification

Read back on each node immediately after, between 6:36:36 PM and 6:36:40 PM Eastern:

| Node | `is-enabled` | `is-active` | Unit symlink | `systemctl --failed` |
| --- | --- | --- | --- | --- |
| red-server | masked | inactive | `/dev/null` | `nut-monitor.service` only |
| purple-server | masked | inactive | `/dev/null` | empty |
| green-server | masked | inactive | `/dev/null` | empty |
| blue-server | masked | inactive | `/dev/null` | empty |

`ipmitool` remains installed on all four. `nut-monitor.service` on `red-server` is the unit disabled on purpose at the [PeaNUT deployment](../../Platforms/PeaNUT/Documentation/Change%20Records/UPS%20Dashboard%20Deployment%20-%202026-07-22.md), so neither Proxmox host shuts itself down on a UPS event; it is not part of this change.

## Left open

Nothing from this change. The hosts still carry `ipmitool` and its sensor timer for hardware they do not have; removing them would be tidier but touches the node_exporter package set that Ansible manages, so that belongs with the exporter project rather than here.
