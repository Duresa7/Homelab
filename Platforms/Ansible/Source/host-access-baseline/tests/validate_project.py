#!/usr/bin/env python3
"""Validate the host-access-baseline project structure without contacting any host.

Checks that the inventory parses, the three target groups hold exactly the
approved host sets, every host connects as `ansible`, only ansible-01 uses a
local connection, the referenced playbooks exist, the sudoers playbook writes
through visudo validation, the ai-agent key carries no restriction options, the
account-password play carries no credential and converges rather than skipping,
and the Semaphore manifest points only at playbooks that are present.
"""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GROUPS = ("ai_agent_targets", "ai_agent_key_only", "dkadi_nopasswd_targets")
PLAYBOOKS = (
    "playbooks/ai-agent-account.yml",
    "playbooks/sudoers-nopasswd.yml",
    "playbooks/account-passwords.yml",
)

EXPECTED_AI_AGENT_TARGETS = {
    "media-01",
    "docker-network",
    "monitor-01",
    "edge-01",
    "app-01",
    "alpha-prod-01",
    # The effort spec calls this host wazuh-01. The inventory name matches
    # every other Ansible project and the SSH manager.
    "security-01",
    "splunk-siem",
    "docker-blue",
    "ansible-01",
}
# The account and its sudoers drop-in already exist here; only the key file is
# written. Its authorized_keys was 0 bytes, which is why the account was
# unreachable.
EXPECTED_KEY_ONLY = {"game-01"}
EXPECTED_DKADI_NOPASSWD = {
    "edge-01",
    "app-01",
    "alpha-prod-01",
    "security-01",
    "splunk-siem",
    "docker-blue",
}
# Deliberately outside the model. ubuntu-dev is the single-account workstation,
# docker-main stays root-login only, supabase-01 is powered off, and the
# Proxmox nodes are ssh-key-automation's cluster file rather than POSIX
# accounts.
EXCLUDED_HOSTS = {
    "ubuntu-dev",
    "docker-main",
    "supabase-01",
    "grey-server",
    "purple-server",
    "blue-server",
    "red-server",
    "green-server",
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

    ai_agent_hosts = collect_hosts(children.get("ai_agent_targets", {}))
    key_only_hosts = collect_hosts(children.get("ai_agent_key_only", {}))
    dkadi_hosts = collect_hosts(children.get("dkadi_nopasswd_targets", {}))

    if set(ai_agent_hosts) != EXPECTED_AI_AGENT_TARGETS:
        errors.append(
            "ai-agent target set differs from the approved eleven-host list: "
            f"{sorted(ai_agent_hosts)}"
        )
    if set(key_only_hosts) != EXPECTED_KEY_ONLY:
        errors.append(f"key-only set must be exactly {sorted(EXPECTED_KEY_ONLY)}")
    if set(dkadi_hosts) != EXPECTED_DKADI_NOPASSWD:
        errors.append(
            "dkadi NOPASSWD set differs from the approved six-host list: "
            f"{sorted(dkadi_hosts)}"
        )

    # A host in both would have its account created and then treated as
    # pre-existing, so the playbook asserts against it too.
    overlap = set(ai_agent_hosts) & set(key_only_hosts)
    if overlap:
        errors.append(f"hosts in both ai-agent groups: {sorted(overlap)}")

    # Every dkadi target must be a host this project already reaches.
    stray_dkadi = set(dkadi_hosts) - set(ai_agent_hosts) - set(key_only_hosts)
    if stray_dkadi:
        errors.append(f"dkadi targets absent from the ai-agent groups: {sorted(stray_dkadi)}")

    for host in EXCLUDED_HOSTS & (set(ai_agent_hosts) | set(key_only_hosts) | set(dkadi_hosts)):
        errors.append(f"{host} is excluded by decision but appears in a target group")

    for host, host_vars in {**ai_agent_hosts, **key_only_hosts}.items():
        host_vars = host_vars or {}
        if host_vars.get("ansible_user") != "ansible":
            errors.append(f"{host}: ansible_user must be ansible")
        connection = host_vars.get("ansible_connection")
        if host == "ansible-01" and connection != "local":
            errors.append("ansible-01 must use the guarded local connection")
        elif host != "ansible-01" and connection == "local":
            errors.append(f"{host}: only ansible-01 may use a local connection")

    for playbook in PLAYBOOKS:
        if not (ROOT / playbook).is_file():
            errors.append(f"missing playbook {playbook}")

    account_text = (ROOT / "playbooks" / "ai-agent-account.yml").read_text(encoding="utf-8")
    if "exclusive: true" not in account_text:
        errors.append("the ai-agent key must be installed exclusively")
    if 'mode: "0600"' not in account_text:
        errors.append("the ai-agent authorized_keys file must be mode 0600")
    if 'mode: "0700"' not in account_text:
        errors.append("the ai-agent .ssh directory must be mode 0700")
    if "no_log: true" not in account_text:
        errors.append("the account task must suppress the console password from logs")
    if "update_password: on_create" not in account_text:
        errors.append("the password must only ever be set at account creation")
    # This repository is public and publishes no key material. The playbook
    # must load the key from the gitignored vars file, never carry a literal.
    account_play = yaml.safe_load(account_text)[0]
    if (account_play.get("vars") or {}).get("ai_agent_public_key"):
        errors.append(
            "ai_agent_public_key must not be hardcoded in the playbook; "
            "it loads from the gitignored vars/ai-agent-key.yml"
        )

    key_example = ROOT / "vars" / "ai-agent-key.yml.example"
    key_notice = ROOT / "vars" / "PUBLICATION-NOTICE.md"
    if not key_example.is_file():
        errors.append("missing vars/ai-agent-key.yml.example")
    if not key_notice.is_file():
        errors.append("missing vars/PUBLICATION-NOTICE.md")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    if "vars/ai-agent-key.yml" not in gitignore:
        errors.append("vars/ai-agent-key.yml must be gitignored")

    # The example is published, so it must stay a placeholder. Any real base64
    # key data reaching it is a publication-policy failure.
    if key_example.is_file():
        example_text = key_example.read_text(encoding="utf-8")
        example_key = (yaml.safe_load(example_text) or {}).get("ai_agent_public_key", "")
        example_fields = " ".join(example_key.split()).split()
        if "REPLACE_WITH_PUBLIC_KEY_DATA" not in example_key:
            errors.append(
                "vars/ai-agent-key.yml.example must hold a placeholder, not a real key"
            )
        if len(example_fields) != 3 or example_fields[0] not in {"ssh-ed25519", "ssh-rsa"}:
            errors.append(
                "the example key must be a bare `type data comment` line; "
                "an options prefix means the key carries restrictions"
            )

    # Only the gitignored Linux Host Baseline Standard is allowed to name the
    # password manager or the credential item each account draws from. This
    # project is published, so it points at that standard instead. Assembled at
    # runtime so this file does not match itself.
    withheld_names = ("1" + "Password", "Linux Server" + " Standard")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        for name in withheld_names:
            if name in body:
                errors.append(
                    f"{path.relative_to(ROOT)}: names the password manager or the "
                    "credential item, which only the baseline standard may do"
                )

    # Belt and braces: no published file in this project may carry key data.
    # The markers are assembled at runtime so this file does not match itself.
    markers = ("AAAAB3NzaC1" + "yc2E", "AAAAC3NzaC1" + "lZDI1NTE5")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name == "ai-agent-key.yml":
            continue
        if ".git" in path.parts:
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        if any(marker in body for marker in markers):
            errors.append(
                f"{path.relative_to(ROOT)}: carries public key material, "
                "which this repository does not publish"
            )

    passwords_text = (ROOT / "playbooks" / "account-passwords.yml").read_text(encoding="utf-8")
    if "update_password: always" not in passwords_text:
        errors.append(
            "the account-password play must use update_password: always; "
            "on_create would skip every host that already has a password and "
            "leave the drift between the two sudo password fields in place"
        )
    if "no_log: true" not in passwords_text:
        errors.append("the account-password tasks must suppress passwords from logs")
    if "any_errors_fatal: true" not in passwords_text:
        errors.append("the account-password play must abort on the first host that fails")
    # This play writes to /etc/shadow on all eleven. Both values are supplied at
    # run time; a literal reaching this public repository is a publication
    # failure, and a default that is not empty would set a password nobody
    # chose.
    passwords_play = yaml.safe_load(passwords_text)[0]
    passwords_vars = passwords_play.get("vars") or {}
    for name in ("root_password", "dkadi_password"):
        if name not in passwords_vars:
            errors.append(f"the account-password play must declare {name}")
        elif passwords_vars[name] != "":
            errors.append(
                f"{name} must default to an empty string and be supplied at run "
                "time; this repository publishes no credential"
            )
    if "$6$" in passwords_text:
        errors.append("playbooks/account-passwords.yml carries a password hash")
    # An empty value hashes to a valid crypt string, so the play has to refuse
    # to run rather than set an empty root password on eleven hosts.
    if "root_password | length > 0" not in passwords_text:
        errors.append("the account-password play must refuse to run without both credentials")

    # Unquoted, YAML reads this as a boolean and Ansible hands sudo the string
    # True, which is not a command, so the check fails for a reason that has
    # nothing to do with the grant it is testing.
    for playbook in PLAYBOOKS:
        if "argv: [sudo, -n, true]" in (ROOT / playbook).read_text(encoding="utf-8"):
            errors.append(f"{playbook}: quote the argument to sudo -n; bare true is a boolean")

    sudoers_text = (ROOT / "playbooks" / "sudoers-nopasswd.yml").read_text(encoding="utf-8")
    if sudoers_text.count("validate: visudo -cf %s") != 2:
        errors.append("both sudoers drop-ins must be written through visudo validation")
    if 'mode: "0440"' not in sudoers_text:
        errors.append("sudoers drop-ins must be mode 0440")
    if "any_errors_fatal: true" not in sudoers_text:
        errors.append("the sudoers play must abort on the first host that fails")

    semaphore_path = ROOT / "semaphore" / "task-templates.yml"
    if semaphore_path.is_file():
        semaphore = yaml.safe_load(semaphore_path.read_text(encoding="utf-8"))
        declared_views = set(semaphore.get("views") or [])
        if not declared_views:
            errors.append("Semaphore manifest must declare at least one view")
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
            for survey in template.get("survey") or []:
                if not survey.get("name") or not survey.get("title"):
                    errors.append(f"{name}: survey variables require name and title")
                if survey.get("type", "") not in {"", "int", "enum", "secret"}:
                    errors.append(f"{name}: unsupported survey type {survey.get('type')!r}")
                if not isinstance(survey.get("required"), bool):
                    errors.append(f"{name}: survey required flag must be boolean")
                # Every password survey is a secret field. A plain one would
                # show the value in the Semaphore UI and store it in the task
                # log.
                if str(survey.get("name", "")).endswith("_password") and survey.get("type") != "secret":
                    errors.append(
                        f"{name}: the {survey.get('name')} survey must be a secret"
                    )
    else:
        errors.append("Semaphore manifest semaphore/task-templates.yml is missing")
        template_names = set()

    if errors:
        print("host-access-baseline validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validation passed: {len(ai_agent_hosts)} ai-agent hosts, "
        f"{len(key_only_hosts)} key-only host, {len(dkadi_hosts)} dkadi hosts, "
        f"{len(template_names)} Semaphore templates."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
