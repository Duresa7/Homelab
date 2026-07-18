#!/usr/bin/env python3
"""Validate inventory and SSH identity data without contacting any host."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IDENTITIES = {"mac", "ansible-control", "jedi-pc", "termix"}
PUBLICATION_NOTICE = ROOT / "identities" / "PUBLICATION-NOTICE.md"


def fingerprint(public_key: str) -> str:
    parts = public_key.split()
    if len(parts) < 2:
        raise ValueError("public key has fewer than two fields")
    raw = base64.b64decode(parts[1], validate=True)
    digest = base64.b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
    return f"SHA256:{digest}"


def collect_hosts(group: dict) -> set[str]:
    hosts = set((group.get("hosts") or {}).keys())
    for child in (group.get("children") or {}).values():
        hosts.update(collect_hosts(child or {}))
    return hosts


def main() -> int:
    errors: list[str] = []
    inventory = yaml.safe_load((ROOT / "inventory" / "hosts.yml").read_text(encoding="utf-8"))
    all_children = inventory["all"]["children"]
    supported = collect_hosts(all_children["ssh_key_supported"])
    unknown = collect_hosts(all_children["ssh_key_unknown"])

    if supported & unknown:
        errors.append(f"supported and unknown overlap: {sorted(supported & unknown)}")
    if "nas-family" in collect_hosts(inventory["all"]):
        errors.append("retired nas-family host is still present")

    identity_files = sorted((ROOT / "identities").glob("*.yml"))
    identities_omitted = PUBLICATION_NOTICE.is_file()
    identity_ids: set[str] = (
        set(REQUIRED_IDENTITIES) if identities_omitted else set()
    )
    key_materials: set[str] = set()
    if identities_omitted and identity_files:
        errors.append(
            "identity notice cannot coexist with live identity YAML files"
        )
    for path in identity_files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        identity = data.get("ssh_identity", {})
        identity_id = identity.get("id")
        if identity_id != path.stem:
            errors.append(f"{path.name}: id does not match filename")
        if identity_id in identity_ids:
            errors.append(f"{path.name}: duplicate identity id {identity_id}")
        identity_ids.add(identity_id)

        current_key = identity.get("current_public_key", "")
        try:
            actual_fingerprint = fingerprint(current_key)
        except (ValueError, base64.binascii.Error) as exc:
            errors.append(f"{path.name}: invalid current public key: {exc}")
            continue
        if actual_fingerprint != identity.get("fingerprint"):
            errors.append(f"{path.name}: fingerprint mismatch")

        material = " ".join(current_key.split()[:2])
        if material in key_materials:
            errors.append(f"{path.name}: duplicate current public-key material")
        key_materials.add(material)

        targets = identity.get("target_hosts")
        if not isinstance(targets, list) or not targets:
            errors.append(f"{path.name}: target_hosts must be a non-empty list")
        else:
            if len(targets) != len(set(targets)):
                errors.append(f"{path.name}: duplicate target host")
            extra_targets = set(targets) - supported
            if extra_targets:
                errors.append(f"{path.name}: unsupported targets {sorted(extra_targets)}")

        rotation = identity.get("rotation") or {}
        replacement = rotation.get("replacement_public_key", "")
        if replacement:
            try:
                replacement_material = " ".join(replacement.split()[:2])
                fingerprint(replacement)
                if replacement_material == material:
                    errors.append(f"{path.name}: replacement equals current key")
            except (ValueError, base64.binascii.Error) as exc:
                errors.append(f"{path.name}: invalid replacement public key: {exc}")
        elif rotation.get("operator_verified") is True:
            errors.append(f"{path.name}: operator_verified cannot be true without a replacement")

    missing_identities = REQUIRED_IDENTITIES - identity_ids
    if missing_identities and not identities_omitted:
        errors.append(
            f"missing required identities {sorted(missing_identities)}; "
            f"found {sorted(identity_ids)}"
        )

    semaphore = yaml.safe_load(
        (ROOT / "semaphore" / "task-templates.yml").read_text(encoding="utf-8")
    )
    declared_views = set(semaphore.get("views") or [])
    if not declared_views:
        errors.append("Semaphore manifest must declare at least one view")
    template_names: set[str] = set()
    for template in semaphore.get("templates", []):
        name = template.get("name", "")
        if not name or name in template_names:
            errors.append(f"Semaphore template name is empty or duplicated: {name!r}")
        template_names.add(name)
        playbook = ROOT / template.get("playbook", "")
        if not playbook.is_file():
            errors.append(f"{name}: missing playbook {template.get('playbook')}")
        if template.get("view") not in declared_views:
            errors.append(f"{name}: unknown Semaphore view {template.get('view')!r}")
        arguments = template.get("arguments", [])
        for argument in arguments:
            if isinstance(argument, str) and argument.startswith("ssh_identity="):
                selected_identity = argument.split("=", 1)[1]
                if selected_identity not in identity_ids:
                    errors.append(f"{name}: unknown identity {selected_identity}")
        if "Retire Old Key" in name:
            survey_variables = {
                item.get("name") for item in (template.get("survey") or [])
            }
            if "ssh_retire_confirmation" not in survey_variables:
                errors.append(f"{name}: retirement confirmation survey is missing")
        for survey in template.get("survey") or []:
            if not survey.get("name") or not survey.get("title"):
                errors.append(f"{name}: survey variables require name and title")
            if survey.get("type", "") not in {"", "int", "enum", "secret"}:
                errors.append(f"{name}: unsupported survey type {survey.get('type')!r}")
            if not isinstance(survey.get("required"), bool):
                errors.append(f"{name}: survey required flag must be boolean")
            if not isinstance(survey.get("values", []), list):
                errors.append(f"{name}: survey values must be a list")

    if errors:
        print("SSH key automation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if identities_omitted:
        print(
            "Validation passed without identity files: live identity "
            f"records are absent; {len(supported)} supported hosts, "
            f"{len(unknown)} unknown hosts, and {len(template_names)} "
            "Semaphore templates validated."
        )
    else:
        print(
            f"Validation passed: {len(identity_ids)} identities, "
            f"{len(supported)} supported hosts, {len(unknown)} unknown hosts, "
            f"{len(template_names)} Semaphore templates."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
