#!/usr/bin/env python3
"""Validate the fleet-updates project structure without contacting any host.

Checks that the inventory parses, the two target groups exist and are
non-empty, every compose target carries a well-formed compose_projects list,
the referenced playbooks exist, and the Semaphore manifest points only at
playbooks that are present.
"""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GROUPS = ("os_update_targets", "docker_compose_targets")
PLAYBOOKS = ("playbooks/os-update.yml", "playbooks/docker-compose-update.yml")


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

    compose_group = children.get("docker_compose_targets", {})
    for host, host_vars in collect_hosts(compose_group).items():
        projects = (host_vars or {}).get("compose_projects")
        if not isinstance(projects, list) or not projects:
            errors.append(f"{host}: compose_projects must be a non-empty list")
            continue
        seen: set[str] = set()
        for entry in projects:
            name = (entry or {}).get("name")
            src = (entry or {}).get("project_src")
            if not name or not src:
                errors.append(f"{host}: every compose project needs name and project_src")
                continue
            if name in seen:
                errors.append(f"{host}: duplicate compose project name {name}")
            seen.add(name)

    for playbook in PLAYBOOKS:
        if not (ROOT / playbook).is_file():
            errors.append(f"missing playbook {playbook}")

    semaphore_path = ROOT / "semaphore" / "task-templates.yml"
    if semaphore_path.is_file():
        semaphore = yaml.safe_load(semaphore_path.read_text(encoding="utf-8"))
        declared_views = set(semaphore.get("views") or [])
        template_names: set[str] = set()
        for template in semaphore.get("templates", []):
            name = template.get("name", "")
            if not name or name in template_names:
                errors.append(f"Semaphore template name is empty or duplicated: {name!r}")
            template_names.add(name)
            if not (ROOT / template.get("playbook", "")).is_file():
                errors.append(f"{name}: missing playbook {template.get('playbook')}")
            if template.get("view") not in declared_views:
                errors.append(f"{name}: unknown Semaphore view {template.get('view')!r}")
    else:
        errors.append("Semaphore manifest semaphore/task-templates.yml is missing")

    if errors:
        print("fleet-updates validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    os_hosts = collect_hosts(children["os_update_targets"])
    compose_hosts = collect_hosts(children["docker_compose_targets"])
    print(
        f"Validation passed: {len(os_hosts)} OS-update hosts, "
        f"{len(compose_hosts)} compose hosts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
