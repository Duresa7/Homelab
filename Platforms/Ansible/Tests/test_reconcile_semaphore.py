#!/usr/bin/env python3
"""Unit tests for the Semaphore manifest reconciler."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "Scripts" / "reconcile_semaphore.py"


def load_module():
    spec = importlib.util.spec_from_file_location("reconcile_semaphore", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReconcileSemaphoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_load_manifest_rejects_duplicate_template_names(self) -> None:
        content = """\
project:
  name: Example
  repository: {name: repo, path: /srv/repo}
  inventory: {name: hosts, path: /srv/repo/hosts.yml, credential: key}
  environment: {name: locale, variables: {LANG: C.utf8}}
views: [All, Work]
templates:
  - {name: Duplicate, view: Work, playbook: first.yml, arguments: []}
  - {name: Duplicate, view: Work, playbook: second.yml, arguments: []}
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate template"):
                self.module.load_manifest(path)

    def test_environment_payload_serializes_variables_deterministically(self) -> None:
        environment = {
            "name": "C UTF-8",
            "variables": {"LC_ALL": "C.utf8", "LANG": "C.utf8"},
        }
        payload = self.module.environment_payload(7, environment)
        self.assertEqual(payload["project_id"], 7)
        self.assertEqual(payload["name"], "C UTF-8")
        self.assertEqual(
            payload["env"],
            '{"LANG":"C.utf8","LC_ALL":"C.utf8"}',
        )
        self.assertEqual(payload["json"], "{}")
        self.assertIsNone(payload["password"])

    def test_template_payload_maps_manifest_names_to_live_ids(self) -> None:
        template = {
            "name": "OS Update: Whole Fleet (dry run)",
            "view": "OS Updates",
            "playbook": "playbooks/os-update.yml",
            "arguments": ["--check"],
        }
        payload = self.module.template_payload(
            project_id=4,
            template=template,
            repository_id=11,
            inventory_id=12,
            environment_id=13,
            view_id=14,
        )
        self.assertEqual(payload["project_id"], 4)
        self.assertEqual(payload["repository_id"], 11)
        self.assertEqual(payload["inventory_id"], 12)
        self.assertEqual(payload["environment_ids"], [13])
        self.assertEqual(payload["view_id"], 14)
        self.assertEqual(payload["arguments"], json.dumps(["--check"]))
        self.assertEqual(payload["app"], "ansible")
        self.assertEqual(payload["survey_vars"], [])

    def test_resource_diff_compares_json_fields_semantically(self) -> None:
        current = {
            "name": "Example",
            "arguments": '["--check"]',
            "survey_vars": None,
            "allow_parallel_tasks": None,
        }
        desired = {
            "name": "Example",
            "arguments": '["--check"]',
            "survey_vars": [],
            "allow_parallel_tasks": False,
        }
        self.assertFalse(
            self.module.resource_changed(
                current,
                desired,
                fields=(
                    "name",
                    "arguments",
                    "survey_vars",
                    "allow_parallel_tasks",
                ),
                json_fields=("arguments", "survey_vars"),
            )
        )

    def test_template_diff_covers_previously_omitted_fields(self) -> None:
        template = {
            "name": "Example",
            "view": "All",
            "playbook": "playbooks/example.yml",
            "arguments": [],
            "description": "Desired description",
        }
        desired = self.module.template_payload(
            project_id=1,
            template=template,
            repository_id=2,
            inventory_id=3,
            environment_id=4,
            view_id=5,
        )
        changed_values = {
            "description": "Stale description",
            "git_branch": "stale-branch",
            "type": "build",
            "start_version": "1.0.0",
            "autorun": True,
            "task_params": '{"stale":true}',
            "vaults": '[{"id":99}]',
        }
        for field, changed_value in changed_values.items():
            with self.subTest(field=field):
                current = {
                    **desired,
                    "task_params": json.dumps(desired["task_params"]),
                    "vaults": json.dumps(desired["vaults"]),
                    field: changed_value,
                }
                self.assertTrue(
                    self.module.resource_changed(
                        current,
                        desired,
                        fields=self.module.TEMPLATE_COMPARE_FIELDS,
                        json_fields=self.module.TEMPLATE_JSON_FIELDS,
                    )
                )

    def test_pruning_is_opt_in(self) -> None:
        with patch.object(
            self.module.sys,
            "argv",
            ["reconcile_semaphore.py", "--token-file", "token", "manifest.yml"],
        ):
            self.assertFalse(self.module.parse_args().prune)

        with patch.object(
            self.module.sys,
            "argv",
            [
                "reconcile_semaphore.py",
                "--token-file",
                "token",
                "--prune",
                "manifest.yml",
            ],
        ):
            self.assertTrue(self.module.parse_args().prune)

    def test_unmanaged_detection_uses_ids_not_names(self) -> None:
        reconciler = self.module.Reconciler(
            client=None,
            apply=False,
            private_key=None,
            credential_login="ansible",
            refresh_credential=False,
            prune=False,
        )
        reconciler.report_unmanaged(
            "project",
            [
                {"id": 1, "name": "Duplicate"},
                {"id": 2, "name": "Duplicate"},
            ],
            {1},
        )
        self.assertEqual(
            reconciler.actions,
            ["unmanaged project Duplicate (id 2) retained"],
        )

    def test_reconcile_all_reports_unmanaged_projects(self) -> None:
        class ProjectClient:
            def get(self, path):
                if path != "/projects":
                    raise AssertionError(path)
                return [
                    {"id": 1, "name": "Managed"},
                    {"id": 2, "name": "Manual"},
                ]

        class ProjectReconciler(self.module.Reconciler):
            def reconcile(self, manifest):
                return 1

        reconciler = ProjectReconciler(
            client=ProjectClient(),
            apply=False,
            private_key=None,
            credential_login="ansible",
            refresh_credential=False,
            prune=False,
        )
        reconciler.reconcile_all([{"project": {"name": "Managed"}}])
        self.assertEqual(
            reconciler.actions,
            ["unmanaged project Manual (id 2) retained"],
        )


if __name__ == "__main__":
    unittest.main()
