# Homelab TODO

**Created:** 2026-07-09  
**Last updated:** 2026-08-09

This file is my central backlog and index. It holds active priorities plus links to system backlogs; implementation steps stay in the owning system's TODO. I keep closed work in [Completed Work](COMPLETED.md).

## Inbox

None.

## Active Priorities

- [ ] Bring the fleet's human sudo policy in line with the [Linux host baseline](Guides/Linux-Host-Baseline.md), which I corrected on 2026-08-05 so that only unattended accounts carry `NOPASSWD`. A minority of hosts still hold the old policy, and one restores it from cloud-init on every boot. Order matters: provision the new `ai-agent` automation account first so unattended `sudo -n` keeps working, then remove the drop-ins, then stop cloud-init reapplying the change. I ran the preflight on 2026-08-05 and every affected host keeps working sudo afterward. The per-host detail sits with the hardening standard, which is not published. `db-13-dev` came off this list on 2026-08-08 as an approved single-account exception rather than as a conforming host.

- [ ] **Low priority.** Review the 23 diagrams under [Assets/Diagrams](Assets/Diagrams) and redraw the ones that no longer match the environment. Two are known: [prometheus.svg](Assets/Diagrams/prometheus.svg) still shows 51 targets against a live 52, and `agent-sandbox.png` illustrates the Agent Sandbox design I dropped on 2026-08-06 without ever building it. I did not audit the other 21. Excalidraw stores coordinates and colours as plain numbers in both the `.excalidraw` JSON and the exported SVG, so searching for a figure like `51` matches geometry as often as label text and proves nothing either way. Each diagram has to be opened. Every diagram is Excalidraw with its source beside the SVG, so a redraw edits the `.excalidraw` file and re-exports.

## Scheduled

None.

## System Backlogs

| Backlog | Open items |
|---|---|
| [Ansible](Platforms/Ansible/Documentation/TODO.md) | Register the `db-13-dev` identity in `ssh-key-automation`; tidy the duplicate entries in `/etc/pve/priv/authorized_keys`; watch the first real automatic reboot after the 2026-07-29 reconnect-race fix |
| [Galaxy](Infrastructure/Compute/Galaxy/Documentation/TODO.md) | Run Green's full offline memory test and watch its recovered daemons; watch Kasm thin-pool use and Purple drive wear; keep watching Blue's recurring `pvestatd` crashes, quiescent since 2026-07-22 with the cause still unestablished |
| [Galaxy PXE](Platforms/Galaxy%20PXE/README.md) | Physical deployment complete; keep the reusable one-use service ready for future Galaxy nodes |
| [Media Stack](Platforms/Media%20Stack/Documentation/TODO.md) | No open items; I dropped the backup-test, capacity-alert, & update-cadence items on 2026-07-25 |
| [Splunk Enterprise](Platforms/Splunk/Enterprise/Documentation/TODO.md) | Rocky host OS logs, Proxmox host logs, UniFi dashboards, & optional CIM normalization; internal HTTPS completed 2026-07-22 |
| [Splunk Enterprise Security](Platforms/Splunk/Enterprise%20Security/Documentation/TODO.md) | Post-install data readiness and CIM scoping |
| [NetBird](Platforms/Netbird/Documentation/TODO.md) | No open items after the 2026-07-12 descope |
| [Nginx Proxy Manager](Platforms/Nginx%20Proxy%20Manager/Documentation/TODO.md) | No open items; Kasm internal HTTPS completed 2026-07-28 |
| [Prometheus](Platforms/Prometheus/Documentation/TODO.md) | The repository no longer carries the inert Grafana WAL setting; the running container keeps it until the next recreate I initiate. Alert routing then rules; UniFi gateway metrics. Prometheus auto-start closed after it started four seconds after the controlled 2026-08-01 boot with `RestartCount=0` |
| [Wazuh](Platforms/Wazuh/Documentation/TODO.md) | Central stack upgraded to 4.14.7 on 2026-08-04, with 16 agents active after `db-13-dev` enrolled on 2026-08-08. Release the twelve agent holds one host at a time, then move `edge-01` off 4.14.5 and `docker-main` off 4.14.0 |
