#!/usr/bin/env python3
"""Validate the fleet-updates project structure without contacting any host.

Checks that the inventory parses, the two target groups exist and are
non-empty, every compose target carries a well-formed compose_projects list,
the referenced playbooks exist, and the Semaphore manifest points only at
playbooks that are present.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GROUPS = ("os_update_targets", "docker_compose_targets")
PLAYBOOKS = ("playbooks/os-update.yml", "playbooks/docker-compose-update.yml")
EXPECTED_OS_HOSTS = {
    "docker-main",
    "docker-network",
    "docker-blue",
    "media-01",
    "alpha-prod-01",
    "app-01",
    "edge-01",
    "security-01",
    "splunk-siem",
}
EXPECTED_COMPOSE_PROJECTS = {
    "docker-main": {
        "booklore": ("/opt/docker/booklore", ()),
        "forgejo": ("/opt/docker/forgejo", ()),
        "homelab-dashboard-aio": ("/opt/docker/homelab-dashboard-aio", ()),
        "immich": ("/opt/docker/immich-app", ()),
        "portainer": ("/opt/docker/portainer", ()),
    },
    "docker-network": {
        "netbird": ("/opt/docker/netbird", ()),
        "nginx-proxy-manager": ("/opt/docker/nginx-proxy-manager", ()),
        "portainer-edge-agent": ("/opt/docker/portainer-edge-agent", ()),
    },
    "docker-blue": {
        "portainer-edge-agent": ("/opt/docker/portainer-edge-agent", ()),
        "rustdesk": ("/opt/docker/rustdesk", ()),
    },
    "media-01": {
        "media-stack": ("/opt/media-stack", ("vpn",)),
        "portainer-edge-agent": ("/opt/docker/portainer-edge-agent", ()),
    },
    "alpha-prod-01": {
        "playit-agent": (
            "/home/<YOUR_ADMIN_USERNAME>/playit-agent",
            (),
        ),
        "portainer-edge-agent": ("/opt/docker/portainer-edge-agent", ()),
        "teamspeak": ("/home/<YOUR_ADMIN_USERNAME>/teamspeak", ()),
        "teamspeak-02": ("/home/<YOUR_ADMIN_USERNAME>/teamspeak-02", ()),
        "teamspeak-03": ("/home/<YOUR_ADMIN_USERNAME>/teamspeak-03", ()),
        "ts3-manager": ("/home/<YOUR_ADMIN_USERNAME>/ts3-manager", ()),
    },
}


def collect_hosts(group: dict) -> dict:
    """Merge host dicts from a group and all of its children."""
    hosts = dict(group.get("hosts") or {})
    for child in (group.get("children") or {}).values():
        hosts.update(collect_hosts(child or {}))
    return hosts


def main() -> int:
    errors: list[str] = []
    deployment_users: set[str] = set()

    inventory = yaml.safe_load((ROOT / "inventory" / "hosts.yml").read_text(encoding="utf-8"))
    children = inventory["all"]["children"]

    for group in REQUIRED_GROUPS:
        if group not in children:
            errors.append(f"inventory is missing required group {group}")
        elif not collect_hosts(children[group]):
            errors.append(f"group {group} has no hosts")

    compose_group = children.get("docker_compose_targets", {})
    os_hosts = collect_hosts(children.get("os_update_targets", {}))
    compose_hosts = collect_hosts(compose_group)

    if set(os_hosts) != EXPECTED_OS_HOSTS:
        errors.append(
            "OS-update host set differs from the approved nine-host fleet: "
            f"{sorted(os_hosts)}"
        )
    if set(compose_hosts) != set(EXPECTED_COMPOSE_PROJECTS):
        errors.append(
            "compose host set differs from the approved five-host fleet: "
            f"{sorted(compose_hosts)}"
        )
    if set(compose_hosts) - set(os_hosts):
        errors.append("every compose host must also be an OS-update host")
    for host, host_vars in os_hosts.items():
        if (host_vars or {}).get("ansible_user") != "ansible":
            errors.append(f"{host}: ansible_user must be ansible")

    for host, host_vars in collect_hosts(compose_group).items():
        projects = (host_vars or {}).get("compose_projects")
        if not isinstance(projects, list) or not projects:
            errors.append(f"{host}: compose_projects must be a non-empty list")
            continue
        expected_projects = EXPECTED_COMPOSE_PROJECTS.get(host, {})
        if len(projects) != len(expected_projects):
            errors.append(
                f"{host}: expected {len(expected_projects)} "
                f"compose projects, found {len(projects)}"
            )
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
            profiles = (entry or {}).get("profiles")
            if profiles is not None and (
                not isinstance(profiles, list)
                or not profiles
                or any(not isinstance(profile, str) or not profile for profile in profiles)
                or len(profiles) != len(set(profiles))
            ):
                errors.append(
                    f"{host}/{name}: profiles must be a non-empty list of unique strings"
                )
            expected = expected_projects.get(name)
            if expected is None:
                errors.append(f"{host}: unexpected compose project {name}")
                continue
            expected_src, expected_profiles = expected
            if "<YOUR_ADMIN_USERNAME>" in expected_src:
                expected_pattern = re.escape(expected_src).replace(
                    re.escape("<YOUR_ADMIN_USERNAME>"),
                    r"([^/]+)",
                )
                match = re.fullmatch(expected_pattern, src)
                if match:
                    deployment_users.add(match.group(1))
                else:
                    errors.append(
                        f"{host}/{name}: project_src does not match "
                        f"{expected_src}"
                    )
            elif src != expected_src:
                errors.append(
                    f"{host}/{name}: expected project_src {expected_src}, found {src}"
                )
            if tuple(profiles or ()) != expected_profiles:
                errors.append(
                    f"{host}/{name}: expected profiles {list(expected_profiles)}, "
                    f"found {profiles or []}"
                )
        missing_projects = set(expected_projects) - seen
        if missing_projects:
            errors.append(
                f"{host}: missing compose projects {sorted(missing_projects)}"
            )
    if len(deployment_users) > 1:
        errors.append(
            "deployment-owned compose paths use inconsistent usernames: "
            f"{sorted(deployment_users)}"
        )

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

    project_count = sum(
        len((host_vars or {}).get("compose_projects") or [])
        for host_vars in compose_hosts.values()
    )
    if project_count != 18:
        errors.append(f"expected 18 compose projects, found {project_count}")

    if errors:
        print("fleet-updates validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validation passed: {len(os_hosts)} OS-update hosts, "
        f"{len(compose_hosts)} compose hosts, {project_count} projects."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
