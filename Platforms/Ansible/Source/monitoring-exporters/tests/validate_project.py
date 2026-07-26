#!/usr/bin/env python3
"""Validate the monitoring-exporters project structure without contacting a host.

Checks that the inventory parses, both target groups exist and hold exactly the
approved host sets, every host connects as the ansible account, the referenced
playbooks exist, and that hosts deliberately excluded from collection have not
crept back in.
"""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GROUPS = ("node_exporter_targets", "cadvisor_targets")
PLAYBOOKS = ("playbooks/node-exporter.yml", "playbooks/cadvisor.yml")

EXPECTED_NODE_EXPORTER_HOSTS = {
    "docker-main",
    "docker-network",
    "docker-blue",
    "media-01",
    "alpha-prod-01",
    "splunk-siem",
    "ansible-01",
    "monitor-01",
}
# All eight Docker hosts. The set was docker-main alone from 2026-07-25 to
# 2026-07-26, while cAdvisor v0.52.1 could not register containers under the
# containerd snapshotter; v0.60.5 handles it, so the storage driver no longer
# decides membership. The cadvisor_incompatible group went away with it.
EXPECTED_CADVISOR_HOSTS = {
    "docker-main",
    "docker-network",
    "docker-blue",
    "media-01",
    "alpha-prod-01",
    "app-01",
    "security-01",
    "monitor-01",
}

# Hosts that must never appear under node_exporter_targets, with the reason.
# Adding one of these would either collide with a working listener or point the
# automation at a hypervisor.
FORBIDDEN_NODE_EXPORTER_HOSTS = {
    "app-01": "runs its own manually installed node_exporter.service on 9100",
    "edge-01": "already exports on 9100 since the 2026-07-13 baseline",
    "security-01": "already exports on 9100 since the 2026-07-13 baseline",
    "grey-server": "hypervisor, out of scope for this automation",
    "purple-server": "hypervisor, out of scope for this automation",
    "blue-server": "hypervisor, out of scope for this automation",
    "red-server": "hypervisor, out of scope for this automation",
}

# Hosts that must never appear under cadvisor_targets, with the reason.
FORBIDDEN_CADVISOR_HOSTS = {
    "splunk-siem": "runs Podman, not Docker",
    "ansible-01": "runs no containers",
    "grey-server": "hypervisor, out of scope for this automation",
    "purple-server": "hypervisor, out of scope for this automation",
    "blue-server": "hypervisor, out of scope for this automation",
    "red-server": "hypervisor, out of scope for this automation",
}

EXPECTED_IPS = {
    "docker-main": "192.168.40.35",
    "docker-network": "192.168.85.2",
    "docker-blue": "192.168.40.39",
    "media-01": "192.168.40.42",
    "alpha-prod-01": "192.168.80.118",
    "app-01": "192.168.80.10",
    "security-01": "192.168.72.2",
    "splunk-siem": "192.168.72.3",
    "ansible-01": "192.168.40.36",
    "monitor-01": "192.168.73.2",
}


def collect_hosts(group: dict) -> dict:
    """Merge host dicts from a group and all of its children."""
    hosts = dict(group.get("hosts") or {})
    for child in (group.get("children") or {}).values():
        hosts.update(collect_hosts(child or {}))
    return hosts


def main() -> int:
    errors: list[str] = []

    inventory = yaml.safe_load((ROOT / "inventory" / "hosts.yml").read_text(encoding="utf-8"))
    children = inventory["all"]["children"]

    for group in REQUIRED_GROUPS:
        if group not in children:
            errors.append(f"inventory is missing required group {group}")
        elif not collect_hosts(children[group]):
            errors.append(f"group {group} has no hosts")

    node_hosts = collect_hosts(children.get("node_exporter_targets", {}))
    cadvisor_hosts = collect_hosts(children.get("cadvisor_targets", {}))

    if set(node_hosts) != EXPECTED_NODE_EXPORTER_HOSTS:
        errors.append(
            "node_exporter host set differs from the approved eight-host set: "
            f"{sorted(node_hosts)}"
        )
    if set(cadvisor_hosts) != EXPECTED_CADVISOR_HOSTS:
        errors.append(
            "cAdvisor host set differs from the approved eight Docker hosts: "
            f"{sorted(cadvisor_hosts)}"
        )
    if "cadvisor_incompatible" in children:
        errors.append(
            "cadvisor_incompatible is back in the inventory. It was removed on "
            "2026-07-26 when v0.60.5 made the storage driver irrelevant; if a "
            "host really is incompatible, record why rather than reviving the group"
        )

    for host, reason in FORBIDDEN_NODE_EXPORTER_HOSTS.items():
        if host in node_hosts:
            errors.append(f"{host} must not be a node_exporter target: {reason}")
    for host, reason in FORBIDDEN_CADVISOR_HOSTS.items():
        if host in cadvisor_hosts:
            errors.append(f"{host} must not be a cAdvisor target: {reason}")

    for group_name, hosts in (
        ("node_exporter_targets", node_hosts),
        ("cadvisor_targets", cadvisor_hosts),
    ):
        for host, host_vars in hosts.items():
            host_vars = host_vars or {}
            if host_vars.get("ansible_user") != "ansible":
                errors.append(f"{group_name}/{host}: ansible_user must be ansible")
            expected_ip = EXPECTED_IPS.get(host)
            if expected_ip and host_vars.get("ansible_host") != expected_ip:
                errors.append(
                    f"{group_name}/{host}: expected ansible_host {expected_ip}, "
                    f"found {host_vars.get('ansible_host')}"
                )

    # The controller manages itself, so it must not depend on its own key being
    # present in its own authorized_keys.
    controller = (node_hosts.get("ansible-01") or {})
    if controller and controller.get("ansible_connection") != "local":
        errors.append("ansible-01 must use ansible_connection: local")

    for playbook in PLAYBOOKS:
        if not (ROOT / playbook).is_file():
            errors.append(f"missing playbook {playbook}")

    if errors:
        print("monitoring-exporters validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validation passed: {len(node_hosts)} node_exporter hosts, "
        f"{len(cadvisor_hosts)} cAdvisor hosts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
