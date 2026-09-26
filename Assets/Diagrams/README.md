# Diagrams

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

Eighteen architecture diagrams, each a self-contained SVG that GitHub renders inline. They are generated, not drawn: the specs, the library and the logo set live in [Generator](Generator/README.md), and one command rebuilds every file here. Each diagram carries a "State as of" date in its corner and a footer naming the records it was drawn from. The Excalidraw sources of the earlier hand-drawn set are in `Archive/Assets/Diagrams/`.

| File | What it shows | Embedded in |
|---|---|---|
| `homelab-overview.svg` | The whole lab: internet edge, UniFi zones, the five Galaxy nodes and their 18 guests, and the security, monitoring, identity and access flows | [README](../../README.md), [Access Paths](../../Architecture/Access-Paths.md), [External Service Ingress](../../Architecture/External-Service-Ingress.md) |
| `unifi-network.svg` | The sixteen routed networks and twelve firewall zones on the Ahsoka gateway | [UniFi guide](../../Guides/UniFi-Network.md), [UniFi README](../../Infrastructure/Network/UniFi/README.md) |
| `galaxy-cluster.svg` | Five Proxmox VE nodes with their hardware, storage pools, guests, both Corosync rings and the UPS | [Cluster Architecture](../../Infrastructure/Compute/Galaxy/Documentation/Architecture/Cluster%20Architecture.md), [Galaxy guide](../../Guides/Galaxy-Proxmox-Cluster.md) |
| `lab-map.svg` | Where each guide lands: hosts grouped by what they do, with the guide that covers each group | [Guides index](../../Guides/README.md) |
| `prometheus.svg` | Prometheus and Grafana on monitor-01: seven scrape jobs, 57 targets, 24 Grafana rules to Discord | [Prometheus guide](../../Guides/Prometheus.md) |
| `wazuh.svg` | The Wazuh manager on security-01, the fifteen agents by group, the forwarder to Splunk and the MCP path | [Wazuh guide](../../Guides/Wazuh.md) |
| `linux-baseline.svg` | The three layers every Linux guest passes through before it carries a workload | [Linux Host Baseline guide](../../Guides/Linux-Host-Baseline.md) |
| `ssh-key-lifecycle.svg` | One SSH identity from inventory to retirement across the nodes and guests | [SSH Key Lifecycle guide](../../Guides/SSH-Key-Lifecycle.md) |
| `ansible-automation.svg` | ansible-01: the four project directories, the Semaphore templates and the managed hosts | [Ansible guide](../../Guides/Ansible-SSH-Identity-Automation.md) |
| `automation-flow.svg` | How one Ansible run reaches authorized keys | [Ansible architecture](../../Platforms/Ansible/Documentation/Architecture.md) |
| `key-rotation.svg` | The five-state key rotation machine and its removal gate | [Ansible architecture](../../Platforms/Ansible/Documentation/Architecture.md) |
| `boot-model.svg` | The controller boot chain from blue-server to Semaphore and the PXE services | [Ansible architecture](../../Platforms/Ansible/Documentation/Architecture.md) |
| `media-stack.svg` | The media stack on media-01: request path, acquisition through Gluetun, and the HDD layout | [Media Stack guide](../../Guides/Media-Stack.md), [Media Stack architecture](../../Platforms/Media%20Stack/Documentation/Architecture.md) |
| `splunk.svg` | Splunk Enterprise and Enterprise Security on splunk-siem: inputs, apps, indexes and the alert path | [Splunk guide](../../Guides/Splunk.md) |
| `netbird.svg` | The NetBird control plane on docker-network and the routed path into Access-A | [NetBird guide](../../Guides/NetBird.md) |
| `nginx-proxy-manager.svg` | Internal HTTPS for 24 names: certificate path, local DNS, proxied backends and firewall allows | [Nginx Proxy Manager guide](../../Guides/Nginx-Proxy-Manager.md) |
| `immich-migration.svg` | The 2026-05-28 storage migration from the WD Red Plus to the Toshiba | [Immich storage migration guide](../../Guides/Immich-Storage-Migration.md) |
| `incident-response.svg` | The six steps from scope to close | [Security Incident Response guide](../../Guides/Security-Incident-Response.md) |

## Rebuilding

```bash
cd Assets/Diagrams/Generator
python3 build.py            # normalises the logos, regenerates every SVG in Assets/Diagrams/, validates
PNG=1 python3 build.py      # the same, plus a 2x PNG beside each SVG for viewers without SVG support
python3 build.py --check    # validation only
```

`build.py --check` parses every SVG, requires `width`, `height` and `viewBox`, and rejects scripts, `foreignObject`, external references, em dashes, and MAC- or email-like strings, so a withheld value cannot ride in through a spec. The PNG render uses headless Chrome and is optional; nothing in this folder depends on it.
