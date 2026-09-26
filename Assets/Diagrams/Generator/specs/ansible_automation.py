#!/usr/bin/env python3
"""ansible-automation: the controller, its projects and the managed hosts, remade.

Controller and runtime: Platforms/Ansible/README.md (Current State) and the
2026-09-24 live readback (.scratch/reorg/live-facts.md section 7: Ansible 14.2.0,
ansible-core 2.21.2, Semaphore 2.18.27 with 3 projects and 23 templates; project
directories under /home/ansible). Template names: each project's
semaphore/task-templates.yml under Platforms/Ansible/Source/. Host groups: the four
inventory/hosts.yml files. Privilege model: Platforms/Ansible/Documentation/
Architecture.md, Source/host-access-baseline/README.md and Operations/Maintenance/
Fleet Access Model Verified and Credential Item Collapsed - 2026-09-07.md (ansible
holds NOPASSWD root on 11 of 11 guests; dkadi's sudo prompt takes root's password).
Superseded NOPASSWD templates and the retired db-13-dev inventory entry are not drawn."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ansible-automation.svg")
d = Diagram("ansible-automation", "Ansible automation on ansible-01: controller, projects, managed hosts",
            "Four project directories run by ansible-playbook; Semaphore fronts three of them with 23 templates; a run reaches a guest as the ansible account and a node as root",
            source="Platforms/Ansible/README.md and Documentation/Architecture.md, Platforms/Ansible/Source/*/ (semaphore/task-templates.yml, inventory/hosts.yml, README.md), Operations/Maintenance/Fleet Access Model Verified and Credential Item Collapsed - 2026-09-07.md",
            width=1640, card_w=200)

# --- row 0: the controller -----------------------------------------------------------
d.group("ctl", "ansible-01 · LXC 100 on blue-server · 192.168.40.36", badge="Personal-A VLAN 40 · execution account ansible", family="Internal", notes=[
    (None, "also in /home/ansible, deployed by ansible-playbook deploy.yml only: proxmox-pxe-provisioning (Platforms/Galaxy PXE) and wazuh-agent-deployment (Platforms/Wazuh)"),
])
d.card("ctl", "ans", "Ansible 14.2.0", sub1="ansible-core 2.21.2 · /opt/ansible-current on PATH", sub2="ansible-playbook from /home/ansible/<project>, C.utf8", logo="ansible")
d.card("ctl", "sem", "Semaphore 2.18.27", sub1="TCP 3000 · semaphore.alphasecunited.com through NPM", sub2="3 projects, 23 templates, 0 schedules (read 2026-09-24)", logo="semaphore")
d.card("ctl", "man", "Manifests and reconciler", sub1="semaphore/task-templates.yml in each project", sub2="reconcile_semaphore.py reports drift, --apply writes it", logo="glyph:YML")
d.card("ctl", "cred", "Credentials", sub1="ansible-key: the controller SSH key, one copy per project", sub2="passwords typed as secret survey variables, never argv", logo="glyph:KEY")

# --- rows 1 and 2: the projects -----------------------------------------------------------
d.group("ssh", "Server-SSH · /home/ansible/ssh-key-automation", badge="13 templates: Onboard + 4 per identity", family="Access", notes=[
    (None, "views Mac, Ansible Control, Jedi PC; ubuntu-dev templates are in the manifest only"),
])
d.card("ssh", "audit", "Audit", sub1="ssh-key-audit.yml, read-only", sub2="reports state, writes nothing", logo="glyph:1")
d.card("ssh", "onb", "Onboard", sub1="Onboard: New SSH Device", sub2="ssh-identity-onboard.yml", logo="glyph:2")
d.card("ssh", "stage", "Stage Replacement", sub1="ssh-key-stage.yml, additive", sub2="new key beside the current", logo="glyph:3")
d.card("ssh", "verify", "Verify Staged Key", sub1="ssh-key-verify.yml", sub2="both keys on every target", logo="glyph:4")
d.card("ssh", "retire", "Retire Old Key", sub1="ssh-key-retire.yml, 5 gates", sub2="survey phrase RETIRE <id>", logo="glyph:5")

d.group("fleet", "Fleet-Updates · /home/ansible/fleet-updates", badge="6 templates", family="Access", notes=[(None, "11 guests, no node; reboot when a host asks")])
d.card("fleet", "osu", "OS Update", sub1="os-update.yml · apt or dnf", sub2="fleet, dry run, one host", logo="glyph:apt")
d.card("fleet", "dcu", "Docker Compose", sub1="docker-compose-update.yml", sub2="20 projects on 6 hosts", logo="docker")

d.group("mon", "Monitoring-Exporters · /home/ansible/monitoring-exporters", badge="4 templates live, 8 in the manifest", family="Access", notes=[
    (None, "textfile collectors and WUD run by ansible-playbook until the manifest is reconciled"),
])
d.card("mon", "nex", "Node Exporter", sub1="node-exporter.yml", sub2="reconcile all, single host", logo="node-exporter")
d.card("mon", "cad", "cAdvisor", sub1="cadvisor.yml, 8 hosts", sub2="reconcile all, single host", logo="cadvisor")
d.card("mon", "txt", "Textfile Collectors", sub1="textfile-collectors.yml", sub2="6 hosts · CLI only", logo="node-exporter")
d.card("mon", "wud", "WUD", sub1="wud.yml · WUD", sub2="6 Compose hosts · CLI only", logo="glyph:WUD")

d.group("hab", "Host-Access-Baseline · /home/ansible/host-access-baseline", badge="manifest only: ansible-playbook", family="Identity", notes=[
    (None, "one host at a time, stop on first failure; visudo -cf before any sudoers file lands"),
])
d.card("hab", "aia", "AI Agent Account", sub1="ai-agent-account.yml", sub2="account + key on 10 guests", logo="glyph:ai")
d.card("hab", "sudo", "Sudo Policy", sub1="sudoers-rootpw.yml", sub2="Defaults rootpw, 11 guests", logo="glyph:su")
d.card("hab", "pw", "Account Passwords", sub1="account-passwords.yml", sub2="root and dkadi, proven by su", logo="glyph:pw")

# --- row 3: the managed hosts ---------------------------------------------------------
d.group("nodes", "Proxmox nodes", badge="as root · cluster key file · never package updates", family="Mgmt", cols=2)
d.card("nodes", "grey", "grey-server", sub1="192.168.70.10 · keys: writer", sub2="textfile, smartmon, nvme timers", logo="proxmox", node="grey")
d.card("nodes", "purple", "purple-server", sub1="192.168.70.11 · keys: verify", sub2="no other project targets it", logo="proxmox", node="purple")
d.card("nodes", "blue", "blue-server", sub1="192.168.70.12 · keys: verify", sub2="no other project targets it", logo="proxmox", node="blue")
d.card("nodes", "red", "red-server", sub1="192.168.70.13 · keys: verify", sub2="no other project targets it", logo="proxmox", node="red")
d.card("nodes", "green", "green-server", sub1="192.168.70.14 · keys: verify", sub2="no other project targets it", logo="proxmox", node="green")

d.group("guests", "Linux guests", badge="as ansible, key-only · all 11 in Server-SSH and OS Update", family="Servers", cols=4, notes=[
    (None, "ansible: NOPASSWD root for the unattended run · dkadi: sudo prompt takes root's password (Defaults rootpw) · ai-agent: no sudo · root: no SSH login"),
])
def guest(id, name, logo, node, s1, s2):
    d.card("guests", id, name, sub1=s1, sub2=s2, logo=logo, node=node)
guest("dmain", "docker-main", "docker", "grey", "Compose 7 · WUD · cAdvisor", "node_exporter · textfile")
guest("dnet", "docker-network", "nginx-proxy-manager", "blue", "Compose 2 · WUD · cAdvisor", "node_exporter · accounts")
guest("dblue", "docker-blue", "docker", "blue", "Compose 3 · WUD · cAdvisor", "node_exporter · accounts")
guest("media", "media-01", "jellyfin", "red", "Compose 1 · WUD · cAdvisor", "node_exporter · accounts")
guest("alpha", "alpha-prod-01", "teamspeak", "purple", "Compose 5 · WUD · cAdvisor", "node_exporter · accounts")
guest("mon01", "monitor-01", "grafana", "blue", "Compose 2 · WUD · cAdvisor", "node_exporter · accounts")
guest("app01", "app-01", "coolify", "purple", "cAdvisor · textfile · accounts", "Coolify owns its images")
guest("edge01", "edge-01", "caddy", "purple", "textfile · accounts", "exports on 9100 already")
guest("sec01", "security-01", "wazuh", "grey", "cAdvisor · textfile · accounts", "exports on 9100 already")
guest("splunk", "splunk-siem", "splunk", "grey", "node_exporter · textfile (dnf)", "accounts · Podman host")
guest("ans01", "ansible-01", "ansible", "blue", "node_exporter · accounts", "local connection")

d.row("ctl")
d.row("ssh", "fleet")
d.row("mon", "hab")
d.row("nodes", "guests")

d.edge("ctl", "nodes", "SSH as root, /etc/pve/priv/authorized_keys: grey writes, four verify", color="grey",
       from_side="left", to_side="top", x="left", label_x="left:+8", label_y="gap:2", label_anchor="start")
d.edge("ctl", "guests", "SSH as ansible, key-only, restricted key · sudo -n to root for the run", color="grey",
       from_side="right", to_side="top", x="right", label_x="right:-8", label_y="gap:2", label_anchor="end")

d.legend_family("Internal", "controller"); d.legend_family("Access", "project with Semaphore templates"); d.legend_family("Identity", "project run by ansible-playbook only")
d.legend_family("Mgmt", "Proxmox nodes"); d.legend_family("Servers", "Linux guests")
d.legend_edge("SSH from ansible-01", "solid", "grey")
d.legend_badge("guest's node", "grey")
d.footnote("Guest tags name the inventory groups that vary by host: Compose n is docker_compose_targets with n projects, WUD wud_targets, cAdvisor cadvisor_targets, node_exporter node_exporter_targets, textfile textfile_collector_targets, accounts ai_agent_targets plus the sudo and password plays.")
d.footnote("Live Semaphore (2026-09-24): Server-SSH 13, Fleet-Updates 6, Monitoring-Exporters 4. The manifests under Source/ define 41 templates in four projects; the 18 not yet reconciled run by ansible-playbook. The monitoring-exporters inventory still lists db-13-dev, retired 2026-08-14, which is not drawn.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
