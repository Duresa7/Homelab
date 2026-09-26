#!/usr/bin/env python3
"""boot-model: the controller boot chain (restyle of the 2026-07-20 Excalidraw
diagram, content kept) extended with the two PXE services systemd also starts in
LXC 100. Facts: Platforms/Ansible/README.md (Live Deployment: boot behaviour),
Platforms/Ansible/Documentation/Architecture.md (Runtime and Boot Model),
Platforms/Ansible/Configuration/semaphore.service, Platforms/Galaxy PXE/README.md
and Source/README.md, Operations/Inventory/Galaxy/Services.md (ansible-01),
Platforms/Galaxy PXE/Documentation/Troubleshooting/First TFTP Request Fails After
Restart - 2026-09-12.md. ansible-01 has run on blue-server since 2026-09-12."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "boot-model.svg")
d = Diagram("boot-model", "Controller boot model: LXC 100 to Semaphore and the PXE services",
            "blue-server boots, Proxmox starts ansible-01 with onboot=1, systemd brings up three units, and every task resolves into /opt/ansible-current",
            source="Platforms/Ansible/README.md, Platforms/Ansible/Documentation/Architecture.md, Platforms/Ansible/Configuration/semaphore.service, Platforms/Galaxy PXE/README.md, Platforms/Galaxy PXE/Source/README.md, Operations/Inventory/Galaxy/Services.md",
            width=1400, gap=96)

d.group("boot", "Boot chain", badge="no operator step", family="Mgmt")
d.card("boot", "node", "blue-server boots", sub1="Proxmox VE 9.2.11 · 192.168.70.12", sub2="pct config 100: onboot: 1", logo="proxmox", node="blue")
d.card("boot", "lxc", "LXC 100 ansible-01 starts", sub1="192.168.40.36 · Personal-A VLAN 40", sub2="systemd inside the container", logo="glyph:LXC", node="blue")
d.card("boot", "sysd", "systemd starts three units", sub1="all enabled, active after every boot", sub2="Semaphore: Restart=on-failure, 5 s", logo="glyph:init")

d.group("svc", "Services inside ansible-01", badge="listeners", family="Internal")
d.card("svc", "sem", "semaphore.service", sub1="Semaphore 2.18.27 · TCP 3000", sub2="PATH /opt/ansible-current/bin first · C.utf8", logo="semaphore")
d.card("svc", "pxe", "galaxy-pxe.service", sub1="HTTP TCP 8080 · answers and callbacks", sub2="state /var/lib/galaxy-pxe/state.json", logo="glyph:PXE")
d.card("svc", "tftp", "tftpd-hpa.service", sub1="UDP 69 · root /srv/tftp", sub2="first request after a restart times out", logo="glyph:TFTP", warn=True)

d.group("use", "What they resolve into", badge="no daemon for direct runs", family="External")
d.card("use", "cur", "/opt/ansible-current", sub1="Ansible 14.2.0 · ansible-core 2.21.2", sub2="/usr/local/bin/ansible* link into it", logo="ansible")
d.card("use", "lane", "PXE lane · Server-Provision VLAN 5", sub1="UEFI PXE at 192.168.40.36, galaxy-ipxe.efi", sub2="one-use claim, answer per registered MAC", logo="glyph:5")
d.card("use", "join", "Cluster join through grey-server", sub1="first boot fetches the dedicated join key", sub2="pvecm add --use_ssh · scope: this join only", logo="proxmox", node="grey")

d.row("boot")
d.row("svc")
d.row("use")

d.edge("node", "lxc", "starts", color="grey")
d.edge("lxc", "sysd", "boots", color="grey")
d.edge("sysd", "sem", "", color="grey")
d.edge("sysd", "pxe", "", color="grey")
d.edge("sysd", "tftp", "", color="grey")
d.edge("sem", "cur", "tasks use", color="purple")
d.edge("pxe", "lane", "serves the answer, records state", color="blue")
d.edge("tftp", "lane", "hands out the loader", color="blue", t_off=110)
d.edge("lane", "join", "join key", color="teal")

d.legend_family("Mgmt", "Proxmox node and guest"); d.legend_family("Internal", "systemd units"); d.legend_family("External", "runtime and lane")
d.legend_edge("boot order", "solid", "grey"); d.legend_edge("Semaphore tasks", "solid", "purple"); d.legend_edge("PXE path", "solid", "blue"); d.legend_edge("first boot of a new node", "solid", "teal")
d.legend_badge("blue-server", "blue"); d.legend_badge("grey-server", "grey")
d.footnote("The web UI returns on its own after a controller or node reboot. Direct ansible-playbook runs need no service and work as soon as the LXC is up. The tftpd-hpa first-request timeout is open since 2026-09-12; the transfer succeeds on retry.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
