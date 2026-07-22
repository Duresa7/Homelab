# UPS Monitoring Options Research

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

## Decision Context

The design needs to monitor two APC USB UPS units, display load and runtime, and leave a safe path for later shutdown of several physical nodes. This record compares the available designs; it doesn't record a deployment or hardware test.

## Recommended Architecture

I should run Network UPS Tools on the two Proxmox hosts that hold the USB cables. `red-server` should run the NUT driver, `upsd`, & a local primary `upsmon` for `UPS-01`. `grey-server` should do the same for `UPS-02`; `blue-server` should run a secondary `upsmon` that reads Grey over TCP/3493 because Blue shares that UPS.

This matches NUT's documented primary/secondary design. NUT says one computer owns the USB connection, runs the driver and data server, & acts as the primary; the other computers powered by the same UPS are secondaries. The driver & `upsd` run on the system with the communication link, while remote clients query `upsd` over the network. [`upsmon` handles the operating-system shutdown](https://networkupstools.org/docs/user-manual.chunked/ar01s02.html), and [`upsd` uses TCP/3493 by default](https://networkupstools.org/historic/v2.8.5/docs/man/upsd.conf.html).

## Documented capabilities

### NUT

NUT is built for mixed vendors & one-to-many monitoring. Its driver normalizes the readings, `upsd` publishes them, and clients use the same network protocol whether they run locally or on another host. The project documents simultaneous shutdown of multiple computers powered by one UPS as a core use case. [The NUT overview describes that layered design](https://github.com/networkupstools/nut), while the [`upsmon` manual defines primary and secondary shutdown ordering](https://networkupstools.org/historic/v2.8.5/docs/man/upsmon.html).

NUT is the better base for this setup because it gives both APC units one protocol, supports a primary on each USB host, & lets Blue subscribe to Grey without USB passthrough. It also leaves read-only telemetry available to a dashboard, Home Assistant, or Prometheus without giving those tools authority to shut down a Proxmox host.

### apcupsd

`apcupsd` can read APC UPS units over USB, publish status to network clients, shut down multiple computers, & serve its older CGI status pages. Debian's documentation includes APC USB devices and even covers distinguishing two same-vendor USB units by serial number. [Debian documents the APC USB setup](https://wiki.debian.org/apcupsd), and the [apcupsd files page lists 3.14.14 from 2016-05-31 as the latest stable release](https://sourceforge.net/projects/apcupsd/files/).

It still works for a simple APC-only installation, so it isn't a fake option. The tradeoff is project age and a narrower product focus. NUT's own release notes say the last apcupsd release was 3.14.14 in May 2016 and describe `apcupsd-ups` as a limited compatibility bridge that relays only the readings apcupsd exposes. [NUT records those limits in its 2.8.1 release notes](https://networkupstools.org/historic/v2.8.1/docs/release-notes.pdf).

## Community Practice

The common Proxmox pattern is NUT or apcupsd on the physical host that owns the USB cable, then a network client on every other physical machine powered by that UPS. In one Proxmox forum answer, the recommended design is NUT server on the PVE host & a network client in the other system; the same answer notes that shutting down the PVE host already shuts down its guests. [That discussion also states that one USB device can't be owned by both a host and VM](https://forum.proxmox.com/threads/can-i-share-usb-connected-ups-with-proxmox-and-a-windows-vm.111384/). Recent community examples repeat the NUT server/client pattern, including [one APC USB node with two other Proxmox nodes as NUT clients](https://www.reddit.com/r/Proxmox/comments/1u2xji5/), [NUT installed directly on the Proxmox USB host](https://www.reddit.com/r/Proxmox/comments/1u12pov/), & [an older three-node account with one server/client pair and two clients](https://www.reddit.com/r/Proxmox/comments/151wpvl/).

Some users pass the UPS into an LXC or Home Assistant guest. That arrangement is real, but the Proxmox forum records raw USB device paths changing after reboot and users working around cgroup, bind-mount, & device-permission details. One participant runs apcupsd on the host specifically so it can shut down guests and the host during an extended outage. [The USB passthrough thread records both the failure mode and the host-based choice](https://forum.proxmox.com/threads/usb-passthrough-to-lxc-problem.145087/). A guest can be useful when its only job is displaying data; it shouldn't be the sole owner of the USB link that protects its hypervisor.

## Interfaces people deploy

### NUT Web GUI

[NUT Web GUI](https://github.com/SuperioOne/nut_webgui) refreshes UPS variables, supports multiple NUT server connections, provides a JSON API & OpenMetrics endpoint, and ships as a Docker image on port 9000. Those features cover the two independent NUT servers without adding an InfluxDB dependency or a separate metrics exporter.

I can run one NUT Web GUI container on `docker-main` and configure two read-only connections, one to Red and one to Grey. That gives one screen for `battery.charge`, `battery.runtime`, `ups.load`, input voltage, status, & every other variable the BR1500MS2 firmware and selected NUT driver expose. The dashboard can't invent a reading that the UPS doesn't report.

### PeaNUT

[PeaNUT](https://github.com/Brandawg93/PeaNUT) is the more feature-heavy dashboard. It supports multiple UPS devices, commands, a JSON API, Prometheus output, direct InfluxDB v2 export, & Docker deployment on port 8080. Its repository showed 1,500 GitHub stars & release 6.0.0 on 2026-07-22.

PeaNUT makes sense if I want its layout editor, InfluxDB history, or Homepage and Glance widgets. For a first screen that only needs live load, battery, & runtime from Red and Grey, NUT Web GUI has fewer moving parts and explicitly documents multiple NUT server connections.

### Home Assistant

Home Assistant has an official NUT integration. It requires an existing NUT server, polls once every 60 seconds by default, displays status, supports notifications, & can expose UPS commands when the supplied NUT account has command privileges. [The Home Assistant documentation lists those capabilities and says the integration appears in 4.2% of active Home Assistant installations](https://www.home-assistant.io/integrations/nut).

Home Assistant fits when UPS alerts should join its existing notification flows. It doesn't replace NUT on Red or Grey, and its documented 60-second polling interval is slower than a continuously refreshed local status page.

### Prometheus & Grafana

Prometheus plus Grafana is the common choice for history rather than a quick live page. The Prometheus project lists a NUT exporter in its community exporter catalog, and [HON95's exporter](https://github.com/HON95/prometheus-nut-exporter) converts a NUT TCP endpoint into Prometheus metrics. It adds an exporter, a scrape job, stored time series, & a Grafana dashboard.

This homelab already runs Prometheus & Grafana on `security-01`, so historical load and runtime graphs are a logical second phase. I don't need that stack to answer today's question. NUT Web GUI can show both UPS units without first designing retention, alerts, & Grafana panels.

## Shutdown pattern for this homelab

The safe layout follows the electrical feeds, not cluster membership:

| UPS | USB owner and NUT primary | NUT secondary systems | Loads without an operating-system client |
| --- | --- | --- | --- |
| `UPS-01` | `red-server` | Jedi PC, if I later want it to shut down automatically | None recorded |
| `UPS-02` | `grey-server` | `blue-server` | Ahsoka Gateway, Bane Switch POE, Verizon ONT |

Grey should stay up long enough for Blue to receive the critical event and stop. NUT's primary/secondary logic waits for secondaries to disconnect, bounded by `HOSTSYNC`, before the primary finishes its own shutdown. [The `upsmon` manual explains that ordering and warns that secondaries must finish before the primary cuts UPS output](https://networkupstools.org/historic/v2.8.5/docs/man/upsmon.html).

The network path matters. `UPS-02` already powers the ONT, UCG-Fiber, & USW-Pro-Max-16-PoE, so Grey can continue reaching Blue while that UPS has battery. `UPS-01` protects Red & Jedi PC, but their NUT traffic depends on the network core supplied by `UPS-02`; shutdown thresholds must leave enough runtime on both units for that dependency.

I shouldn't script one cluster-wide shutdown call. Proxmox staff state that the API requires a shutdown request for each node and that guest boot order is local rather than cluster-wide. [The Proxmox forum answer documents both limits](https://forum.proxmox.com/threads/ish-shutdown-all-nodes-via-api.121594/). Independent `upsmon` clients on each protected node avoid making one custom API script responsible for every host.

## Recommendation

I should deploy in two stages:

1. Install NUT directly on `red-server` and `grey-server`, detect each BR1500MS2, confirm the values returned by `upsc`, & publish read-only access to the required management addresses on TCP/3493.
2. Run NUT Web GUI on `docker-main` with two read-only NUT accounts, one for Red and one for Grey. This gives a browser interface now without passing either UPS into LXC 110.

Automatic shutdown should be a later, controlled change. That phase should add a local primary `upsmon` on Red and Grey, a secondary on Blue, an optional Jedi PC client, firewall rules limited to the client addresses, & a timed pull-the-plug test that proves guest shutdown, secondary ordering, host poweroff, restored-power behavior, and HA behavior. The existing local-storage HA history makes that test part of the implementation, not an assumption.

If I want long-term graphs after live viewing works, I should expose OpenMetrics from NUT Web GUI or add a NUT exporter to the existing `security-01` Prometheus stack. PeaNUT or Home Assistant remains an interface choice; neither changes where the USB driver and Proxmox shutdown authority belong.

## Evidence Quality

Capability claims rest on NUT, Home Assistant, Prometheus, GitHub project repositories, Debian, and Proxmox staff answers. Reddit and non-staff Proxmox posts show community patterns only. Stars, comments, and anecdotes don't establish installation counts.
