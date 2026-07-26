# PeaNUT UPS Dashboard

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I use PeaNUT as the browser interface for the two APC Back-UPS Pro BR1500MS2 units. NUT owns each USB connection on its physical Proxmox host; PeaNUT reads both TCP/3493 endpoints from one container on `docker-main`.

## Layout

| Component | Location | Role |
| --- | --- | --- |
| NUT `ups01` | `red-server` | Reads `UPS-01` through USB & publishes telemetry on `192.168.70.13:3493` |
| NUT `ups02` | `grey-server` | Reads `UPS-02` through USB & publishes telemetry on `192.168.70.10:3493` |
| PeaNUT 6.0.0 | `docker-main` | Displays both NUT endpoints at `https://peanut.<YOUR_BASE_DOMAIN>`; direct fallback `http://192.168.40.35:8090` |

The dashboard login is stored in 1Password. The versioned configuration contains no password, UPS serial number, or command-capable NUT account.

## Records

- [Deployment plan](Documentation/Change%20Plans/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md)
- [Deployment record](Documentation/Change%20Records/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md)
- [Evidence index](Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Evidence-Index.md)
- [UPS monitoring research](../../Infrastructure/Hardware/Documentation/UPS%20Monitoring%20Options%20Research%20-%202026-07-22.md)
- [Power equipment inventory](../../Infrastructure/Hardware/Power.md)
- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)

## Operations

I open `https://peanut.<YOUR_BASE_DOMAIN>` and use the dashboard login from 1Password. The container runs from `/opt/docker/peanut`; its `.env` stays mode `0600` and isn't versioned. NUT exposes telemetry only. `nut-monitor.service` is disabled on Red and Grey, so this deployment doesn't shut down either Proxmox host.
