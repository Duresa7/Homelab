# RustDesk

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

RustDesk is my self-hosted remote-desktop server. The two OSS server containers, `hbbs` (ID and rendezvous) and `hbbr` (relay), run on `docker-blue`, CT 108 at `192.168.40.39` in Personal-A, VLAN 40. [MeshCentral](../MeshCentral/README.md) runs on the same host as a pilot to replace it; RustDesk stays until that pilot passes.

## Current State

Read back on 2026-09-24.

| Item | Current value |
|---|---|
| Host | `docker-blue`, CT 108 on blue-server, `192.168.40.39`, VLAN 40 |
| Containers | `hbbs` and `hbbr`, both running, both created 12:19 AM EDT on 2026-07-29 |
| Image | `rustdesk/rustdesk-server:latest`, version 1.1.16 |
| Compose project | `/opt/docker/rustdesk` (directory listed on 2026-09-12) |
| Published ports | Not read back |
| Public exposure | No UniFi port forward; the lab has none |
| Directory login | None. The OSS server has no central permissions or directory login |

## Open Items

- Read back the published ports, the Compose file and the client list, then capture a redacted Compose copy under `Configuration/` with any secret replaced by a `<REDACTED_X>` marker.
- Decide between RustDesk and MeshCentral once the four MeshCentral tests in its README pass (logged-out console, Ctrl+Alt+Delete, UAC elevation, reconnect after reboot).

## Related

- [MeshCentral](../MeshCentral/README.md)
- [Access Paths](../../Architecture/Access-Paths.md)
- [Services inventory](../../Operations/Inventory/Galaxy/Services.md)
