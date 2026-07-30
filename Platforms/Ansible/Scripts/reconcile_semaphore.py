#!/usr/bin/env python3
"""Reconcile Semaphore projects from versioned Ansible project manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
import sys
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import yaml


JsonObject = dict[str, Any]

TEMPLATE_COMPARE_FIELDS = (
    "name",
    "playbook",
    "arguments",
    "description",
    "inventory_id",
    "repository_id",
    "view_id",
    "app",
    "git_branch",
    "survey_vars",
    "type",
    "start_version",
    "autorun",
    "task_params",
    "vaults",
    "allow_override_args_in_task",
    "allow_override_branch_in_task",
    "allow_parallel_tasks",
    "suppress_success_alerts",
)
TEMPLATE_JSON_FIELDS = ("arguments", "survey_vars", "task_params", "vaults")


def load_manifest(path: Path) -> JsonObject:
    """Load and validate one Semaphore project manifest."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: manifest root must be a mapping")

    project = data.get("project")
    if not isinstance(project, dict) or not project.get("name"):
        raise ValueError(f"{path}: project.name is required")

    for section, required in (
        ("repository", ("name", "path")),
        ("inventory", ("name", "path", "credential")),
        ("environment", ("name", "variables")),
    ):
        value = project.get(section)
        if not isinstance(value, dict):
            raise ValueError(f"{path}: project.{section} must be a mapping")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(
                f"{path}: project.{section} is missing {', '.join(missing)}"
            )

    views = data.get("views")
    if not isinstance(views, list) or not views or views[0] != "All":
        raise ValueError(f"{path}: views must start with All")
    if len(views) != len(set(views)):
        raise ValueError(f"{path}: duplicate view name")

    templates = data.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ValueError(f"{path}: templates must be a non-empty list")

    template_names: set[str] = set()
    for template in templates:
        if not isinstance(template, dict):
            raise ValueError(f"{path}: every template must be a mapping")
        name = template.get("name")
        if not name:
            raise ValueError(f"{path}: every template needs a name")
        if name in template_names:
            raise ValueError(f"{path}: duplicate template name {name!r}")
        template_names.add(name)
        if template.get("view") not in views:
            raise ValueError(
                f"{path}: {name!r} references unknown view {template.get('view')!r}"
            )
        if not template.get("playbook"):
            raise ValueError(f"{path}: {name!r} needs a playbook")
        arguments = template.get("arguments", [])
        if not isinstance(arguments, list) or any(
            not isinstance(argument, str) for argument in arguments
        ):
            raise ValueError(f"{path}: {name!r} arguments must be a string list")

    return data


def environment_payload(project_id: int, environment: JsonObject) -> JsonObject:
    """Build the API payload for one variable group."""
    variables = environment.get("variables") or {}
    if not isinstance(variables, dict):
        raise ValueError("environment.variables must be a mapping")
    return {
        "project_id": project_id,
        "name": environment["name"],
        "password": None,
        "json": "{}",
        "env": json.dumps(variables, sort_keys=True, separators=(",", ":")),
        "secrets": [],
    }


def normalize_survey(survey: Iterable[JsonObject]) -> list[JsonObject]:
    """Remove empty optional survey fields that Semaphore omits on readback."""
    normalized: list[JsonObject] = []
    for variable in survey:
        item = {
            key: variable[key]
            for key in ("name", "title", "description", "type", "required", "values")
            if key in variable
        }
        if item.get("type") == "":
            item.pop("type")
        if item.get("values") == []:
            item.pop("values")
        normalized.append(item)
    return normalized


def template_payload(
    *,
    project_id: int,
    template: JsonObject,
    repository_id: int,
    inventory_id: int,
    environment_id: int,
    view_id: int,
) -> JsonObject:
    """Build the API payload for one Ansible task template."""
    return {
        "project_id": project_id,
        "inventory_id": inventory_id,
        "repository_id": repository_id,
        "environment_ids": [environment_id],
        "view_id": view_id,
        "name": template["name"],
        "playbook": template["playbook"],
        "arguments": json.dumps(
            template.get("arguments") or [],
            separators=(",", ":"),
        ),
        "description": template.get("description", ""),
        "allow_override_args_in_task": False,
        "allow_override_branch_in_task": False,
        "allow_parallel_tasks": False,
        "suppress_success_alerts": False,
        "app": "ansible",
        "git_branch": "",
        "survey_vars": normalize_survey(template.get("survey") or []),
        "type": "",
        "start_version": "",
        "autorun": False,
        "task_params": {},
        "vaults": [],
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def resource_changed(
    current: JsonObject,
    desired: JsonObject,
    *,
    fields: Iterable[str],
    json_fields: Iterable[str] = (),
) -> bool:
    """Return whether selected API fields differ."""
    json_field_set = set(json_fields)
    for field in fields:
        current_value = current.get(field)
        desired_value = desired.get(field)
        if field in json_field_set:
            current_value = _json_value(current_value)
            desired_value = _json_value(desired_value)
        if current_value is None and isinstance(desired_value, bool):
            current_value = False
        if current_value is None and isinstance(desired_value, list):
            current_value = []
        if current_value is None and isinstance(desired_value, dict):
            current_value = {}
        if current_value is None and desired_value == "":
            current_value = ""
        if current_value != desired_value:
            return True
    return False


def read_private_file(path: Path, label: str) -> str:
    """Read a private file after rejecting group or other access."""
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError(f"{label} must not be group- or world-accessible: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{label} is empty: {path}")
    return value


class SemaphoreClient:
    """Small authenticated client for the Semaphore v2.18 API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
        *,
        query: JsonObject | None = None,
    ) -> Any:
        url = f"{self.base_url}/api{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        body = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                content = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(
                f"Semaphore API {method} {path} returned HTTP {exc.code}: {detail}"
            ) from exc
        if not content:
            return None
        return json.loads(content)

    def get(self, path: str, *, query: JsonObject | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, payload: JsonObject) -> Any:
        return self.request("POST", path, payload)

    def put(self, path: str, payload: JsonObject) -> Any:
        return self.request("PUT", path, payload)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def expire_current_token(self) -> None:
        self.delete(f"/user/tokens/{quote(self.token, safe='')}")


class Reconciler:
    """Apply one or more versioned project manifests."""

    def __init__(
        self,
        client: SemaphoreClient,
        *,
        apply: bool,
        private_key: str | None,
        credential_login: str,
        refresh_credential: bool,
        prune: bool,
    ):
        self.client = client
        self.apply = apply
        self.private_key = private_key
        self.credential_login = credential_login
        self.refresh_credential = refresh_credential
        self.prune = prune
        self.actions: list[str] = []

    def action(self, verb: str, kind: str, name: str) -> None:
        prefix = "" if self.apply else "would "
        self.actions.append(f"{prefix}{verb} {kind} {name}")

    @staticmethod
    def named(items: Iterable[JsonObject], name: str) -> JsonObject | None:
        return next((item for item in items if item.get("name") == name), None)

    def report_unmanaged(
        self,
        kind: str,
        items: Iterable[JsonObject],
        managed_ids: set[int],
        *,
        name_field: str = "name",
        ignored_ids: set[int] | None = None,
    ) -> None:
        ignored = ignored_ids or set()
        for item in items:
            item_id = int(item["id"])
            if item_id in managed_ids or item_id in ignored:
                continue
            name = str(item.get(name_field, item["id"]))
            self.actions.append(
                f"unmanaged {kind} {name} (id {item_id}) retained"
            )

    def reconcile_all(self, manifests: list[JsonObject]) -> None:
        """Reconcile every supplied manifest and report extra live projects."""
        names = [manifest["project"]["name"] for manifest in manifests]
        if len(names) != len(set(names)):
            raise ValueError("duplicate project name across manifests")

        managed_project_ids: set[int] = set()
        for manifest in manifests:
            project_id = self.reconcile(manifest)
            if project_id >= 0:
                managed_project_ids.add(project_id)
        self.report_unmanaged(
            "project",
            self.client.get("/projects"),
            managed_project_ids,
        )

    def reconcile(self, manifest: JsonObject) -> int:
        project_spec = manifest["project"]
        project_name = project_spec["name"]
        projects = self.client.get("/projects")
        project = self.named(projects, project_name)
        if project is None:
            self.action("create", "project", project_name)
            if not self.apply:
                self.actions.append(
                    f"would populate project {project_name} with "
                    f"{len(manifest['templates'])} templates"
                )
                return -1
            project = self.client.post(
                "/projects",
                {
                    "name": project_name,
                    "alert": False,
                    "max_parallel_tasks": 0,
                    "type": "",
                },
            )

        project_id = int(project["id"])
        key_id = self.ensure_key(project_id, project_spec["inventory"]["credential"])
        repository_id = self.ensure_repository(project_id, project_spec, key_id)
        inventory_id = self.ensure_inventory(
            project_id,
            project_spec,
            key_id,
        )
        environment_id = self.ensure_environment(project_id, project_spec)
        view_ids = self.ensure_views(project_id, manifest["views"])
        self.ensure_templates(
            project_id,
            manifest["templates"],
            repository_id=repository_id,
            inventory_id=inventory_id,
            environment_id=environment_id,
            view_ids=view_ids,
        )
        if self.prune:
            self.prune_views(project_id, set(view_ids.values()))
        return project_id

    def ensure_key(self, project_id: int, name: str) -> int:
        keys = self.client.get(
            f"/project/{project_id}/keys",
            query={"sort": "name", "order": "asc"},
        )
        key = self.named(keys, name)
        system_key_ids = {
            int(item["id"])
            for item in keys
            if item.get("name") == "None" and item.get("type") == "none"
        }
        self.report_unmanaged(
            "credential",
            keys,
            {int(key["id"])} if key is not None else set(),
            ignored_ids=system_key_ids,
        )
        if key is None:
            self.action("create", "credential", name)
            if not self.apply:
                return -1
            if self.private_key is None:
                raise ValueError(f"private key is required to create credential {name}")
            key = self.client.post(
                f"/project/{project_id}/keys",
                {
                    "name": name,
                    "type": "ssh",
                    "project_id": project_id,
                    "override_secret": True,
                    "ssh": {
                        "login": self.credential_login,
                        "passphrase": "",
                        "private_key": self.private_key,
                    },
                },
            )
        elif self.refresh_credential:
            self.action("refresh", "credential", name)
            if self.apply:
                if self.private_key is None:
                    raise ValueError(
                        f"private key is required to refresh credential {name}"
                    )
                self.client.put(
                    f"/project/{project_id}/keys/{key['id']}",
                    {
                        "id": key["id"],
                        "name": name,
                        "type": "ssh",
                        "project_id": project_id,
                        "override_secret": True,
                        "ssh": {
                            "login": self.credential_login,
                            "passphrase": "",
                            "private_key": self.private_key,
                        },
                    },
                )
        return int(key["id"])

    def ensure_repository(
        self,
        project_id: int,
        project_spec: JsonObject,
        key_id: int,
    ) -> int:
        spec = project_spec["repository"]
        desired = {
            "project_id": project_id,
            "name": spec["name"],
            "git_url": spec["path"],
            "git_branch": "",
            "ssh_key_id": key_id,
        }
        return self.ensure_named_resource(
            project_id=project_id,
            kind="repository",
            collection="repositories",
            desired=desired,
            fields=("name", "git_url", "git_branch", "ssh_key_id"),
        )

    def ensure_inventory(
        self,
        project_id: int,
        project_spec: JsonObject,
        key_id: int,
    ) -> int:
        spec = project_spec["inventory"]
        desired = {
            "project_id": project_id,
            "name": spec["name"],
            "inventory": spec["path"],
            "ssh_key_id": key_id,
            "become_key_id": None,
            "repository_id": None,
            "type": "file",
        }
        return self.ensure_named_resource(
            project_id=project_id,
            kind="inventory",
            collection="inventory",
            desired=desired,
            fields=(
                "name",
                "inventory",
                "ssh_key_id",
                "become_key_id",
                "repository_id",
                "type",
            ),
        )

    def ensure_environment(self, project_id: int, project_spec: JsonObject) -> int:
        spec = project_spec["environment"]
        desired = environment_payload(project_id, spec)
        return self.ensure_named_resource(
            project_id=project_id,
            kind="environment",
            collection="environment",
            desired=desired,
            fields=("name", "json", "env"),
            json_fields=("json", "env"),
        )

    def ensure_named_resource(
        self,
        *,
        project_id: int,
        kind: str,
        collection: str,
        desired: JsonObject,
        fields: Iterable[str],
        json_fields: Iterable[str] = (),
    ) -> int:
        """Create or update one named project resource and report extras."""
        name = str(desired["name"])
        items = self.client.get(
            f"/project/{project_id}/{collection}",
            query={"sort": "name", "order": "asc"},
        )
        current = self.named(items, name)
        self.report_unmanaged(
            kind,
            items,
            {int(current["id"])} if current is not None else set(),
        )
        if current is None:
            self.action("create", kind, name)
            if not self.apply:
                return -1
            current = self.client.post(
                f"/project/{project_id}/{collection}",
                desired,
            )
        elif resource_changed(
            current,
            desired,
            fields=fields,
            json_fields=json_fields,
        ):
            self.action("update", kind, name)
            if self.apply:
                self.client.put(
                    f"/project/{project_id}/{collection}/{current['id']}",
                    {**desired, "id": current["id"]},
                )
        return int(current["id"])

    def ensure_views(self, project_id: int, names: list[str]) -> dict[str, int]:
        items = self.client.get(f"/project/{project_id}/views")
        by_title = {item["title"]: item for item in items}
        result: dict[str, int] = {}
        managed_ids: set[int] = set()
        for position, name in enumerate(names):
            current = by_title.get(name)
            if current is None:
                if name == "All":
                    raise RuntimeError(f"project {project_id} is missing its All view")
                self.action("create", "view", name)
                if not self.apply:
                    result[name] = -1
                    continue
                current = self.client.post(
                    f"/project/{project_id}/views",
                    {
                        "project_id": project_id,
                        "title": name,
                        "position": position,
                    },
                )
            elif int(current.get("position", -1)) != position:
                self.action("reorder", "view", name)
                if self.apply:
                    self.client.put(
                        f"/project/{project_id}/views/{current['id']}",
                        {
                            "id": current["id"],
                            "project_id": project_id,
                            "title": name,
                            "position": position,
                        },
                    )
            result[name] = int(current["id"])
            managed_ids.add(int(current["id"]))
        if not self.prune:
            self.report_unmanaged(
                "view",
                items,
                managed_ids,
                name_field="title",
            )
        return result

    def ensure_templates(
        self,
        project_id: int,
        templates: list[JsonObject],
        *,
        repository_id: int,
        inventory_id: int,
        environment_id: int,
        view_ids: dict[str, int],
    ) -> None:
        items = self.client.get(
            f"/project/{project_id}/templates",
            query={"sort": "name", "order": "asc"},
        )
        by_name = {item["name"]: item for item in items}
        managed_ids: set[int] = set()
        for template in templates:
            name = template["name"]
            desired = template_payload(
                project_id=project_id,
                template=template,
                repository_id=repository_id,
                inventory_id=inventory_id,
                environment_id=environment_id,
                view_id=view_ids[template["view"]],
            )
            current = by_name.get(name)
            if current is None:
                self.action("create", "template", name)
                if self.apply:
                    self.client.post(
                        f"/project/{project_id}/templates",
                        desired,
                    )
            else:
                managed_ids.add(int(current["id"]))
            if current is not None and (
                resource_changed(
                    current,
                    desired,
                    fields=TEMPLATE_COMPARE_FIELDS,
                    json_fields=TEMPLATE_JSON_FIELDS,
                )
                or sorted(current.get("environment_ids") or []) != [environment_id]
            ):
                self.action("update", "template", name)
                if self.apply:
                    self.client.put(
                        f"/project/{project_id}/templates/{current['id']}",
                        {**desired, "id": current["id"]},
                    )

        if self.prune:
            for current in items:
                if int(current["id"]) not in managed_ids:
                    self.action("delete", "template", current["name"])
                    if self.apply:
                        self.client.delete(
                            f"/project/{project_id}/templates/{current['id']}"
                        )
        else:
            self.report_unmanaged("template", items, managed_ids)

    def prune_views(self, project_id: int, managed_ids: set[int]) -> None:
        items = self.client.get(f"/project/{project_id}/views")
        for item in items:
            if int(item["id"]) not in managed_ids:
                self.action("delete", "view", item["title"])
                if self.apply:
                    self.client.delete(
                        f"/project/{project_id}/views/{item['id']}"
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile Semaphore project objects from Ansible project manifests. "
            "The default mode reports drift without writing."
        )
    )
    parser.add_argument(
        "manifests",
        type=Path,
        nargs="+",
        help="One or more semaphore/task-templates.yml files",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:3000",
        help="Semaphore base URL",
    )
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--private-key-file", type=Path)
    parser.add_argument("--credential-login", default="ansible")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply drift. Without this flag the command is read-only.",
    )
    parser.add_argument(
        "--refresh-credential",
        action="store_true",
        help="Replace existing managed SSH credentials with --private-key-file.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete templates and views that are absent from the manifests.",
    )
    parser.add_argument(
        "--expire-token",
        action="store_true",
        help="Expire the API token after reconciliation, including after a failure.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = read_private_file(args.token_file, "API token file")
    private_key = None
    if args.private_key_file:
        private_key = read_private_file(args.private_key_file, "private key file")

    manifests = [load_manifest(path) for path in args.manifests]
    client = SemaphoreClient(args.base_url, token)
    reconciler = Reconciler(
        client,
        apply=args.apply,
        private_key=private_key,
        credential_login=args.credential_login,
        refresh_credential=args.refresh_credential,
        prune=args.prune,
    )
    exit_code = 0
    try:
        reconciler.reconcile_all(manifests)
        for action in reconciler.actions:
            print(action)
        mode = "applied" if args.apply else "detected"
        print(
            f"Semaphore reconciliation {mode}: "
            f"{len(manifests)} projects, {len(reconciler.actions)} actions."
        )
    except Exception as exc:
        print(f"Semaphore reconciliation failed: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        if args.expire_token:
            try:
                client.expire_current_token()
                print("Temporary API token expired.")
            except Exception as exc:
                print(f"API token expiration failed: {exc}", file=sys.stderr)
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
