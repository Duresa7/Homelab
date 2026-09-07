# PeaNUT UPS Dashboard

**Created:** 2026-07-22  
**Last updated:** 2026-09-07

I use PeaNUT as the browser interface for the APC Back-UPS units. NUT owns each USB connection on its physical Proxmox host; PeaNUT reads the TCP/3493 endpoints from one container on `monitor-01`.

**`UPS-01` is unmonitored as of 2026-08-31.** Its USB data cable came off `red-server` on 2026-08-28 when I moved that node onto `UPS-02`, and it is not plugged into any host. The unit still carries its loads. `UPS-02` feeds every Galaxy node and reports normally through `grey-server`, so the unit powering the cluster is still on the board. On 2026-09-07 I decided `UPS-01` stays unmonitored rather than reconnecting it; the diagnosis and the entries to re-enable if that ever changes are in [ups01 NUT Driver Restart Loop After the UPS Swap](Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md).

## Layout

| Component | Location | Role |
| --- | --- | --- |
| NUT `ups01` | `red-server` | Disabled 2026-08-31. Stanza commented out in `/etc/nut/ups.conf`, `nut-server` and the driver disabled, nothing listening on `192.168.70.13:3493` |
| NUT `ups02` | `grey-server` | Reads `UPS-02` through USB & publishes telemetry on `192.168.70.10:3493` |
| PeaNUT `latest`, currently 6.0.0 | `monitor-01` | Displays the enabled NUT endpoints at `https://peanut.alphasecunited.com`; direct fallback `http://192.168.73.2:8090`. The `192.168.70.13` entry is present with `DISABLED: true` |

The dashboard login is held outside this repository. The versioned configuration contains no password, UPS serial number, or command-capable NUT account.

## Records

- [Relocation record to monitor-01](Documentation/Change%20Records/PeaNUT%20Relocation%20to%20monitor-01%20-%202026-07-26.md)
- [Relocation plan to monitor-01](Documentation/Change%20Plans/PeaNUT%20Relocation%20to%20monitor-01%20-%202026-07-26.md) (completed)
- [Deployment plan](Documentation/Change%20Plans/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md)
- [Deployment record](Documentation/Change%20Records/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22.md)
- [Evidence index](Evidence/PeaNUT%20UPS%20Dashboard%20Deployment%20-%202026-07-22/Evidence-Index.md)
- [UPS monitoring research](../../Infrastructure/Hardware/Documentation/UPS%20Monitoring%20Options%20Research%20-%202026-07-22.md)
- [Power equipment inventory](../../Infrastructure/Hardware/Power.md)
- [Internal HTTPS onboarding](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)

## Operations

I open `https://peanut.alphasecunited.com` and use the stored dashboard login. The container runs as `brandawg93/peanut:latest` from `/opt/docker/peanut` on `monitor-01`; its `.env` stays mode `0600` and isn't versioned. NUT exposes telemetry only. `nut-monitor.service` is disabled on Red and Grey, so this deployment doesn't shut down either Proxmox host.

PeaNUT now shares `monitor-01` with Prometheus, Grafana, and `prometheus-nut-exporter`, so the dashboard and the metrics collector read the same two NUT endpoints from one host.
