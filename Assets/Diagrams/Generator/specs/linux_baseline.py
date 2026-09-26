#!/usr/bin/env python3
"""linux-baseline: the layers a new VM or LXC passes through before it carries a
workload. Steps 1 to 6 and the checks: Guides/Linux-Host-Baseline.md
(2026-09-07). The fleet layer: Platforms/Wazuh/Configuration/README.md,
Platforms/Prometheus/README.md, Platforms/Ansible/README.md,
Guides/SSH-Key-Lifecycle.md, Platforms/Executor/README.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linux-baseline.svg")
d = Diagram("linux-baseline", "Linux host baseline: from fresh guest to workload-ready",
            "Six steps in three layers, each gated by a check; the host then joins the fleet before it carries anything",
            source="Guides/Linux-Host-Baseline.md, Guides/SSH-Key-Lifecycle.md, Platforms/Wazuh/Configuration/README.md, Platforms/Prometheus/README.md, Platforms/Ansible/README.md",
            width=1240, card_w=220)

d.group("fresh", "A new guest", badge="VM or LXC on Galaxy", family="External", notes=[
    (None, "What you bring: a hostname, address, gateway, DNS server and time zone; the administrative username, dkadi; three approved ED25519 public keys")])
d.card("fresh", "guest", "Fresh VM or LXC", sub1="Debian 13, Ubuntu 24.04 or Rocky 10", sub2="Proxmox console open, no workload yet", logo="debian", icons=["ubuntu", "rocky-linux", "proxmox"])

d.group("l1", "Layer 1 · patch and identity", badge="steps 1 to 3", family="Internal")
d.card("l1", "patch", "1 · Patch the host", sub1="apt update, apt upgrade -y", sub2="dnf upgrade -y on the RHEL family", logo="glyph:1")
d.card("l1", "admin", "2 · Administrative account", sub1="adduser dkadi, usermod -aG sudo", sub2="sudo asks for a password, no NOPASSWD", logo="glyph:2")
d.card("l1", "keys", "3 · Three public keys", sub1="~/.ssh 0700, authorized_keys 0600", sub2="one approved ED25519 key per line", logo="glyph:3")

d.group("l2", "Layer 2 · SSH and sudo", badge="steps 4 to 6", family="Access", notes=[
    (None, "root keeps a password and answers every sudo prompt, but cannot log in over SSH; a stolen key or a stolen login password alone is not root")])
d.card("l2", "sshd", "4 · Key-only SSH", sub1="sshd_config.d/99-hardening.conf", sub2="PermitRootLogin no, both password methods off", logo="glyph:4")
d.card("l2", "rootpw", "5 · Root password, Defaults rootpw", sub1="passwd root, proven with su - first", sub2="sudoers.d/00-rootpw 0440, since 2026-08-15", logo="glyph:5")
d.card("l2", "locale", "6 · Time and locale", sub1="America/New_York", sub2="en_US.UTF-8", logo="glyph:6")

d.group("l3", "Layer 3 · joins the fleet", badge="before the workload", family="Observability", cols=3, notes=[
    (None, "Only the unattended ansible account carries NOPASSWD; a human account never does. Every Linux guest ends up here")])
d.card("l3", "wazuh", "Wazuh agent 4.14.6-1", sub1="TCP 1514, 1515 to security-01", sub2="group default watches /etc/ssh, cron.d", logo="wazuh")
d.card("l3", "ne", "node_exporter :9100", sub1="node job on monitor-01, 17 hosts", sub2="rolled out from ansible-01", logo="node-exporter")
d.card("l3", "updates", "Fleet updates", sub1="ansible account, key-only, NOPASSWD", sub2="apt or dnf runs from Semaphore", logo="ansible", icons=["semaphore"])
d.card("l3", "lifecycle", "SSH key lifecycle", sub1="audit, stage, verify, retire playbooks", sub2="three approved keys stay the baseline", logo="glyph:KEY")
d.card("l3", "sshmgr", "SSH Manager MCP", sub1="docker-blue, connects as dkadi", sub2="its sudo entry answers the prompt", logo="glyph:SSH")

d.group("ready", "Workload-ready · what the checks must show", badge="reference build: docker-network CT 107", family="Servers", notes=[
    (None, "id dkadi lists sudo; sudo -n true exits 1, because a person at a keyboard is asked for a password"),
    (None, "sudo -l -U dkadi, run as root, lists rootpw among the Defaults and no NOPASSWD"),
    (None, "sshd -T: permitrootlogin no, pubkeyauthentication yes, passwordauthentication no, kbdinteractiveauthentication no"),
    (None, "ssh-keygen -lf authorized_keys prints exactly three fingerprints; passwd -S root reports P; a wrong password is refused at the sudo prompt"),
    (None, "timedatectl and locale report America/New_York and en_US.UTF-8")])

d.row("fresh"); d.row("l1"); d.row("l2"); d.row("l3"); d.row("ready")

d.edge("fresh", "l1", "the workload waits until the patch transaction exits 0", color="grey")
d.edge("l1", "l2", "dkadi is in sudo and exactly three fingerprints are present", color="grey")
d.edge("l2", "l3", "sshd -t passes, a second key-only session connects, su - proved root's password before 00-rootpw landed", color="grey")
d.edge("l3", "ready", "agent active on the manager, target UP in Prometheus, host in the fleet inventory", color="grey")

d.legend_family("External", "starting point"); d.legend_family("Internal", "layer 1: patch and identity"); d.legend_family("Access", "layer 2: SSH and sudo")
d.legend_family("Observability", "layer 3: fleet enrolment"); d.legend_family("Servers", "workload-ready")
d.legend_edge("gate to the next layer", "solid", "grey")
d.footnote("Until 2026-08-15 root was locked here; the current model gives root a password that the sudo prompt asks for, so the login password and the sudo password are different values. Windows hosts follow separate records.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
