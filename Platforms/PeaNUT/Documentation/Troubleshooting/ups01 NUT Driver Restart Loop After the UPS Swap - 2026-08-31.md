# ups01 NUT Driver Restart Loop After the UPS Swap

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Symptom

The Grafana overview showed one scrape target down, `192.168.70.13:3493`, labelled `red-server` / `ups01`. It was the only unhealthy target of 50. `red-server` itself was fine: node exporter on `192.168.70.13:9100` returned HTTP 200, and `pvecm status` listed all five nodes with quorum.

Underneath the dead target, `nut-driver@ups01.service` had been restarting every five seconds for three and a half days. In the 24 hours to 2026-08-31 it wrote 75,292 journal lines against 366 from every other unit on the host combined, and `NRestarts` had reached 12,014.

## Exact Error

From the Prometheus target:

```
server returned HTTP status 503 Service Unavailable
```

From `nut-driver@ups01` on `red-server`:

```
Network UPS Tools - Generic HID driver 0.52 (2.8.1)
USB communication driver (libusb 1.0) 0.46
libusb1: Could not open any HID devices: insufficient permissions on everything
No matching HID UPS found
Driver failed to start (exit status=1)
```

From `upsc`:

```
Error: Driver not connected
```

## Hypotheses

The driver message names permissions, so the first candidate was a udev regression: a package or kernel update dropping the rule that puts the APC HID device in group `nut`. The second was that no UPS was attached at all, in which case `usbhid-ups` prints the same line after finding nothing it can open.

## Tests

`lsusb` on `red-server` returned only the two xHCI root hubs and no device of any kind. That settled it, because `lsusb` reads `/sys` and lists devices regardless of permissions. A device that does not appear there is not attached.

The udev rule was intact anyway, which ruled the first hypothesis out on its own terms:

```
/lib/udev/rules.d/62-nut-usbups.rules
ATTR{idVendor}=="051d", ATTR{idProduct}=="0002", MODE="664", GROUP="nut"
```

I then checked all five Proxmox nodes for an APC device. Only `grey-server` had one, `051d:0002`, which is `UPS-02` serving `ups02`. The `UPS-01` data cable was plugged into nothing.

Prometheus put times on it. The last successful `ups01` scrape was 2026-08-28 at 9:08:00 AM, and `red-server`'s node exporter went down at 9:09:00 AM. The previous boot's journal ends at 9:20:18 AM and the current boot begins at 10:40:17 AM. So the UPS data and the host left together, and the host came back 90 minutes later without the cable.

`ups02` corroborates where the load went. It reads 19 percent load with 2,424 seconds of runtime, against the 17 percent and 2,895 seconds recorded on 2026-07-22. More load, less runtime.

## Root Cause

I moved `red-server` from `UPS-01` to `UPS-02` on 2026-08-28, powering the host down to do it. `UPS-02` is the unit the other nodes already sit on, and `grey-server` holds its USB data cable. `UPS-01`'s USB cable came off `red-server` during that work and was not plugged back into anything.

`red-server` still carried a `[ups01]` stanza in `/etc/nut/ups.conf` pinned to `vendorid 051d` / `productid 0002`. With no such device present, `usbhid-ups` exited 1, systemd restarted it five seconds later, and the loop ran until I stopped it. `upsd` stayed up serving a driver that never connected, which is why `prometheus-nut-exporter` answered 503 rather than refusing the connection.

Nothing was wrong with the monitoring. The target was accurately reporting that `UPS-01` had no data path.

## Corrective Action

`UPS-01` stays physically connected to its loads and stays unmonitored for now. Reattaching its data cable is deferred; the remaining work is in the root [TODO](../../../../TODO.md).

On `red-server`:

```
systemctl disable --now nut-driver@ups01.service
systemctl disable --now nut-server.service
```

Disabling was not sufficient by itself. Masking `nut-driver@ups01.service` is not either, and that is the finding worth carrying forward. `nut-driver-enumerator` rebuilds driver instances from `ups.conf` under an MD5-hashed instance name, so a run of it created `nut-driver@MD5_d351bf088d25fd0f4033e0e4ef12e42d.service`, described by systemd as "device driver for NUT device 'ups01'", and the loop resumed past the mask on the plain name.

What actually stops it is removing the device from the configuration. I commented out the `[ups01]` stanza in `/etc/nut/ups.conf`, left the original lines in place behind `#` with restore instructions above them, and restarted `nut-driver-enumerator.service` to reconcile. It removed `/etc/systemd/system/nut-driver.target.wants/` entirely. I then unmasked `nut-driver@ups01.service`, because the configuration is the control point and a leftover mask would only confuse the restore.

The pre-edit copy of `ups.conf` is at [Backups/red-server-nut-ups.conf-2026-08-31](../../../../Backups/red-server-nut-ups.conf-2026-08-31) and the copy on the host is deleted. It holds no withheld values.

On `monitor-01`, I commented out the `192.168.70.13:3493` target in the Prometheus `nut` job and restarted the container, because this deployment does not run `--web.enable-lifecycle` and `POST /-/reload` returns 403. `promtool check config` passed before the restart. The versioned copy at [Configuration/prometheus-config/prometheus.yml](../../../Prometheus/Configuration/prometheus-config/prometheus.yml) now matches the live file byte for byte, `28e936f310c29814c7da1fce5d905f50`. Syncing it also corrected a stale comment on the live host that said the `cadvisor` job covers eight Docker hosts where it covers nine.

For PeaNUT I set `DISABLED: true` on the `192.168.70.13` entry in `/opt/docker/peanut/config/settings.yml` rather than deleting it. That field is PeaNUT's own mechanism, it survives the application rewriting the file, and the restore is one word. That file holds the dashboard password, so I edited it in place and made no copy of it.

## Verification

| Check | Result |
| --- | --- |
| Prometheus active targets | 49 of 49 up, 0 down |
| `nut` job | `ups02` / `grey-server` / `192.168.70.10:3493` up |
| `nut_battery_charge` | returns for `ups02`, where the exporter normalises 100 percent to `1` |
| `prometheus_config_last_reload_successful` | `1` |
| `red-server` journal | 1 line in 90 seconds, against 75,292 in the previous 24 hours |
| Last `nut-driver` line of any kind | 2026-08-31 11:00:33 PM, when I stopped the hashed instance |
| `nut-driver@*` instances on `red-server` | none, and `nut-driver.target.wants/` no longer exists |
| TCP 3493 on `red-server` | nothing listening |
| `red-server` node exporter | HTTP 200 on `192.168.70.13:9100` |
| PeaNUT container | `Up (healthy)`, HTTP 307 to its login on `192.168.73.2:8090` |
| PeaNUT blackbox probe | `probe_success = 1` for `https://peanut.alphasecunited.com/` |
| `cadvisor` targets | 9, matching the corrected comment |

I did not log in to the PeaNUT web interface to confirm the tile is gone. The credential is held outside this repository and the configuration change plus a healthy container and a passing probe are what I verified.

## Still Open

`UPS-01` runs unmonitored. Nothing reads its charge, load, or runtime, and nothing will alert if it goes to battery or its battery fails. That is an accepted state, not a fixed one.

Nothing alerted. Prometheus loads zero rule groups and knows no Alertmanager, so a target sat down for three and a half days and the Grafana panel was the only signal. Whether Grafana holds its own rules created through the web interface I did not establish, because that needs the admin credential. Either way it is a separate gap from this record's subject and is not addressed here; it is in the root [TODO](../../../../TODO.md).

`openipmi.service` is failed on `red-server`, unrelated to NUT and untouched. `nut-monitor.service` is also failed on both `red-server` and `grey-server`, which predates this work: it has been disabled since the [deployment](../Change%20Records/UPS%20Dashboard%20Deployment%20-%202026-07-22.md) on purpose, so neither node shuts itself down on a UPS event.

## Related

- [Power equipment inventory](../../../../Infrastructure/Hardware/Power.md)
- [PeaNUT deployment record](../Change%20Records/UPS%20Dashboard%20Deployment%20-%202026-07-22.md)
- [PeaNUT relocation to monitor-01](../Change%20Records/Relocation%20to%20monitor-01%20-%202026-07-26.md)
