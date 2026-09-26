#!/usr/bin/env python3
"""ssh-key-lifecycle: one SSH identity from inventory to retirement, remade.

Identities and allowlists: Platforms/Ansible/Source/ssh-key-automation/README.md
(Change Boundaries) and the 2026-09-07 registration change record (16 hosts after
game-01's retirement on 2026-09-12). Playbooks and gates: Documentation/Runbook.md
and Architecture.md. Key stores per host: inventory/hosts.yml. Semaphore template
set: the 2026-09-24 live readback (.scratch/reorg/live-facts.md section 7): 13
Server-SSH templates covering Mac, Ansible Control and Jedi PC; the ubuntu-dev
templates exist only in semaphore/task-templates.yml. Nothing superseded is drawn:
no Windows targets, no game-01, no ssh_key_unknown hosts."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ssh-key-lifecycle.svg")
d = Diagram("ssh-key-lifecycle", "SSH key lifecycle: one identity from inventory to retirement",
            "Four registered identities, one file each; the ssh-key-automation project on ansible-01 audits, stages, verifies and retires keys one identity at a time",
            source="Platforms/Ansible/Source/ssh-key-automation/ (README.md, inventory/hosts.yml, semaphore/task-templates.yml), Platforms/Ansible/Documentation/Runbook.md, Platforms/Ansible/Documentation/Change Records/SSH Identity Registration for green-server, monitor-01, game-01 and ansible-01 - 2026-09-07.md",
            width=1640, gap=20)

# --- row 0: the identities ----------------------------------------------------------
d.group("ident", "Identities: one file per device under identities/", badge="4 identity files on ansible-01, not published", family="Access", notes=[
    (None, "each file: id, display_name, SHA256 fingerprint, current_public_key, target_hosts allowlist, rotation.replacement_public_key, rotation.operator_verified"),
])
d.card("ident", "mac", "Mac", sub1="identities/mac.yml", sub2="16 hosts: 5 nodes + 11 guests", logo="apple", badge="Semaphore + CLI")
d.card("ident", "actl", "Ansible Control", sub1="identities/ansible-control.yml", sub2="9 guests · ansible account key store", logo="ansible", badge="Semaphore + CLI")
d.card("ident", "jedi", "Jedi PC", sub1="identities/jedi-pc.yml", sub2="16 hosts: 5 nodes + 11 guests", logo="glyph:PC", badge="Semaphore + CLI")
d.card("ident", "udev", "Ubuntu Dev", sub1="identities/ubuntu-dev.yml", sub2="16 hosts: 5 nodes + 11 guests", logo="ubuntu", badge="CLI only")
d.card("ident", "new", "New device", sub1="_new-device-template.yml.example", sub2="invalid until edited, then Onboard", logo="glyph:+")

# --- row 1: the lifecycle ---------------------------------------------------------
d.group("life", "Lifecycle: playbooks and their Semaphore templates", badge="one identity per run · -e ssh_identity=<id> · validator first", family="Internal", notes=[
    (None, "Semaphore views Mac, Ansible Control and Jedi PC each hold Audit, Stage Replacement, Verify Staged Key and Retire Old Key; the Onboarding view holds Onboard: New SSH Device"),
])
d.card("life", "s1", "Inventory", sub1="ssh-keygen -lf, by fingerprint", sub2="the comment is only a label", logo="glyph:1")
d.card("life", "s2", "Audit", sub1="ssh-key-audit.yml, read-only", sub2="present, missing, unreachable", logo="glyph:2")
d.card("life", "s3", "Onboard or stage", sub1="ssh-identity-onboard.yml", sub2="ssh-key-stage.yml · additive", logo="glyph:3")
d.card("life", "s4", "Verify", sub1="ssh-key-verify.yml, both keys", sub2="owner-device login test", logo="glyph:4")
d.card("life", "s5", "Retire", sub1="ssh-key-retire.yml, fails closed", sub2="five gates, phrase RETIRE <id>", logo="glyph:5")
d.card("life", "s6", "Final audit and evidence", sub1="zero old-key matches, promote", sub2="evidence kept with the record", logo="glyph:6")

# --- row 2: the fleet that receives the keys -------------------------------------------
d.group("nodes", "Proxmox nodes: one shared key file", badge="/etc/pve/priv/authorized_keys · root", family="Mgmt", cols=2)
d.card("nodes", "grey", "grey-server", sub1="192.168.70.10 · writes the file", sub2="ssh_key_write_enabled: true", logo="proxmox", node="grey")
d.card("nodes", "purple", "purple-server", sub1="192.168.70.11 · verifies only", sub2="shared writer: grey-server", logo="proxmox", node="purple")
d.card("nodes", "blue", "blue-server", sub1="192.168.70.12 · verifies only", sub2="shared writer: grey-server", logo="proxmox", node="blue")
d.card("nodes", "red", "red-server", sub1="192.168.70.13 · verifies only", sub2="shared writer: grey-server", logo="proxmox", node="red")
d.card("nodes", "green", "green-server", sub1="192.168.70.14 · verifies only", sub2="shared writer: grey-server", logo="proxmox", node="green")

d.group("guests", "Linux guests: one key store each", badge="human keys: /home/dkadi/.ssh/authorized_keys · connect as ansible", family="Servers", cols=4)
def guest(id, name, ip, logo, node, store="dkadi key store", extra=""):
    d.card("guests", id, name, sub1=f"{ip} · {extra}" if extra else ip, sub2=store, logo=logo, node=node)
guest("dmain", "docker-main", "192.168.40.35", "docker", "grey", store="/root/.ssh/authorized_keys", extra="root login")
guest("dnet", "docker-network", "192.168.85.2", "nginx-proxy-manager", "blue")
guest("dblue", "docker-blue", "192.168.40.39", "docker", "blue")
guest("media", "media-01", "192.168.40.42", "jellyfin", "red")
guest("alpha", "alpha-prod-01", "192.168.80.118", "teamspeak", "purple")
guest("app01", "app-01", "192.168.80.10", "coolify", "purple")
guest("edge01", "edge-01", "192.168.30.10", "caddy", "purple")
guest("sec01", "security-01", "192.168.72.2", "wazuh", "grey")
guest("mon01", "monitor-01", "192.168.73.2", "grafana", "blue")
guest("splunk", "splunk-siem", "192.168.72.3", "splunk", "grey")
guest("ans01", "ansible-01", "192.168.40.36", "ansible", "blue", extra="local connection")

d.row("ident")
d.row("life")
d.row("nodes", "guests")

for a, b in (("s1", "s2"), ("s2", "s3"), ("s3", "s4"), ("s4", "s5"), ("s5", "s6")):
    d.edge(a, b, "", color="grey")
d.edge("ident", "life", "one identity file per run", color="blue", label_seg=0)
d.edge("life", "nodes", "SSH as root · grey writes, four verify", color="grey", label_seg=1)
d.edge("life", "guests", "SSH as ansible · root only for another account's file", color="grey", label_seg=1)
d.edge("ident", "guests", "owner-device login test to every assigned target", style="dashed", color="teal",
       from_side="right", to_side="top", x="right", t_off=300, label_x="right:-8", label_y="gap:0", label_anchor="end")

d.legend_family("Access", "identities"); d.legend_family("Internal", "lifecycle on ansible-01"); d.legend_family("Mgmt", "Proxmox nodes"); d.legend_family("Servers", "Linux guests")
d.legend_edge("Ansible run from ansible-01", "solid", "grey"); d.legend_edge("direct SSH from the owner device", "dashed", "teal")
for n in ("grey", "purple", "blue", "red", "green"): d.legend_badge(f"{n}-server", n)
d.footnote("Allowlist counts are each file's target_hosts after game-01's retirement on 2026-09-12; the identity files stay on the controller. ansible-control resolves to /home/ansible/.ssh/authorized_keys on its nine guests and reaches the nodes through the cluster file instead.")
d.footnote("Semaphore held 13 Server-SSH templates on 2026-09-24 (Onboard plus four per identity for Mac, Ansible Control and Jedi PC). The ubuntu-dev templates exist in semaphore/task-templates.yml and have not been reconciled into the UI, so that identity runs by ansible-playbook.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
