#!/usr/bin/env python3
"""automation-flow: how one Ansible run reaches authorized keys (restyle of the
2026-07-28 Excalidraw diagram, content kept). Facts: Platforms/Ansible/Documentation/
Architecture.md (Request Path, Identity Separation), Platforms/Ansible/Source/
ssh-key-automation/README.md and inventory/hosts.yml. Four identities exist since
ubuntu-dev's registration on 2026-08-15, so the identity card names four files."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "automation-flow.svg")
d = Diagram("automation-flow", "How one Ansible run reaches authorized keys",
            "A run starts from a shell on ansible-01 or from a Semaphore template, loads one identity file, resolves its allowlist, and writes only that identity's key",
            source="Platforms/Ansible/Documentation/Architecture.md, Platforms/Ansible/Source/ssh-key-automation/README.md, Platforms/Ansible/Source/ssh-key-automation/inventory/hosts.yml",
            width=1640, gap=96)

d.group("launch", "Two ways to launch the same playbooks", badge="ansible-01 · 192.168.40.36", family="External")
d.card("launch", "shell", "Shell on ansible-01", sub1="ssh ansible-01, account ansible", sub2="ansible-playbook -e ssh_identity", logo="glyph:>_")
d.card("launch", "sem", "Semaphore 2.18.27", sub1="TCP 3000 · click-to-run", sub2="per-identity templates", logo="semaphore")

d.group("run", "One run, one identity", badge="/home/ansible/ssh-key-automation", family="Internal")
d.card("run", "proj", "Ansible project", sub1="playbooks: audit, onboard, stage,", sub2="verify, retire · validator first", logo="ansible")
d.card("run", "ident", "Selected identity file", sub1="identities/<id>.yml · public key, fingerprint", sub2="mac, ansible-control, jedi-pc, ubuntu-dev", logo="glyph:ID")
d.card("run", "allow", "Identity target allowlist", sub1="target_hosts, validated against the inventory", sub2="becomes ssh_identity_runtime_targets", logo="glyph:16")
d.card("run", "keys", "Keys on approved hosts", sub1="nodes: /etc/pve/priv/authorized_keys", sub2="guests: the identity's key store", logo="glyph:KEY")

d.row("launch", stretch=False)
d.row("run")

d.edge("shell", "proj", "runs Ansible", color="grey", label_seg=1, y="gap:0:-12")
d.edge("sem", "proj", "same playbooks, optional UI", color="purple", label_seg=1, t_off=60, y="gap:0:12")
d.edge("proj", "ident", "loads one", color="blue")
d.edge("ident", "allow", "its hosts only", color="blue")
d.edge("allow", "keys", "exact key match", color="blue")

d.legend_family("External", "launch path"); d.legend_family("Internal", "the run")
d.legend_edge("control", "solid", "grey"); d.legend_edge("Semaphore launches Ansible", "solid", "purple"); d.legend_edge("data the run carries", "solid", "blue")
d.footnote("The playbooks act on one selected identity at a time, so rotating one device never touches any other identity. Comparison and removal use the key algorithm plus the encoded public key, never the comment.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
