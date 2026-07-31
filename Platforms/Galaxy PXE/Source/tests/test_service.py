import json
import io
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from galaxy_pxe import (  # noqa: E402
    MachineRegistry,
    build_server,
    find_mac_address,
    normalize_mac,
    render_answer,
    render_boot_script,
    render_first_boot,
    summarize_installer_result,
    stream_file_response,
    validate_runtime_inputs,
)


GREEN_MAC = "02:00:00:00:00:01"


def green_machine():
    return {
        "hostname": "green-server",
        "domain": "galaxy",
        "install_disk": "nvme0n1",
        "management_cidr": "192.168.70.14/24",
        "management_gateway": "192.168.70.1",
        "cluster_cidr": "192.168.71.14/24",
        "cluster_peer": "192.168.70.10",
        "cluster_peer_address": "192.168.71.10",
    }


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.machine_path = root / "machines.json"
        self.state_path = root / "state.json"
        self.machine_path.write_text(
            json.dumps({"machines": {GREEN_MAC: green_machine()}}),
            encoding="utf-8",
        )
        self.clock = mock.Mock(
            return_value=datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)
        )
        self.registry = MachineRegistry(
            self.machine_path,
            self.state_path,
            now=self.clock,
            id_factory=lambda: "attempt-1",
        )

    def test_new_machine_is_disabled_and_cannot_claim_installer(self):
        self.assertEqual(self.registry.status(GREEN_MAC), "disabled")
        self.assertFalse(self.registry.claim_install(GREEN_MAC))
        self.assertEqual(self.registry.status(GREEN_MAC), "disabled")

    def test_ready_machine_is_claimed_once_and_moves_to_installer_claimed(self):
        self.registry.set_state(GREEN_MAC, "ready")

        attempt = self.registry.claim_install(GREEN_MAC)

        self.assertEqual(attempt["attempt_id"], "attempt-1")
        self.assertEqual(attempt["phase"], "installer_claimed")
        self.assertEqual(self.registry.status(GREEN_MAC), "installer_claimed")
        self.assertIsNone(self.registry.claim_install(GREEN_MAC))

    def test_complete_machine_cannot_claim_installer(self):
        self.registry.set_state(GREEN_MAC, "complete")

        self.assertIsNone(self.registry.claim_install(GREEN_MAC))
        self.assertEqual(self.registry.status(GREEN_MAC), "complete")

    def test_unknown_machine_cannot_be_armed(self):
        with self.assertRaises(KeyError):
            self.registry.set_state("00:11:22:33:44:55", "ready")

    def test_registry_instances_share_a_filesystem_lock(self):
        second = MachineRegistry(self.machine_path, self.state_path)
        completed = threading.Event()

        def update_state():
            second.set_state(GREEN_MAC, "ready")
            completed.set()

        with self.registry.state_lock():
            worker = threading.Thread(target=update_state)
            worker.start()
            time.sleep(0.05)
            self.assertFalse(completed.is_set())

        worker.join(timeout=1)
        self.assertTrue(completed.is_set())
        self.assertEqual(self.registry.status(GREEN_MAC), "ready")

    def test_attempt_records_timestamped_phase_history(self):
        self.registry.set_state(GREEN_MAC, "ready")
        attempt = self.registry.claim_install(GREEN_MAC)

        self.registry.transition(
            GREEN_MAC,
            attempt["attempt_id"],
            "answer_served",
            {"fetch_schema": "1.0"},
        )

        record = self.registry.record(GREEN_MAC)
        self.assertEqual(record["phase"], "answer_served")
        self.assertEqual(record["attempt_id"], "attempt-1")
        self.assertEqual(
            [event["phase"] for event in record["history"]],
            ["installer_claimed", "answer_served"],
        )
        self.assertEqual(record["detail"]["fetch_schema"], "1.0")
        self.assertEqual(record["updated_at"], "2026-07-31T12:00:00+00:00")

    def test_wrong_attempt_cannot_advance_state(self):
        self.registry.set_state(GREEN_MAC, "ready")
        self.registry.claim_install(GREEN_MAC)

        with self.assertRaises(ValueError):
            self.registry.transition(
                GREEN_MAC, "older-attempt", "answer_served"
            )

    def test_active_attempt_requires_force_before_rearming(self):
        self.registry.set_state(GREEN_MAC, "ready")
        self.registry.claim_install(GREEN_MAC)

        with self.assertRaises(ValueError):
            self.registry.set_state(GREEN_MAC, "ready")

        self.registry.set_state(GREEN_MAC, "ready", force=True)
        self.assertEqual(self.registry.status(GREEN_MAC), "ready")

    def test_legacy_installing_state_is_read_without_losing_the_gate(self):
        self.state_path.write_text(
            json.dumps({GREEN_MAC: "installing"}), encoding="utf-8"
        )

        record = self.registry.record(GREEN_MAC)

        self.assertEqual(record["phase"], "installer_claimed")
        self.assertEqual(record["attempt_id"], "legacy")
        self.assertIsNone(self.registry.claim_install(GREEN_MAC))


class RenderingTests(unittest.TestCase):
    def test_normalize_mac_accepts_lenovo_firmware_format(self):
        self.assertEqual(normalize_mac("02-00-00-00-00-01"), GREEN_MAC)

    def test_find_mac_reads_official_proxmox_system_info_shape(self):
        payload = {
            "schema": {"version": "1.0"},
            "sysinfo": {
                "network_interfaces": [
                    {"link": "enp0s31f6", "mac": "02:00:00:00:00:01"}
                ]
            },
        }

        self.assertEqual(find_mac_address(payload, {GREEN_MAC}), GREEN_MAC)

    def test_ready_boot_script_chains_to_http_installer_assets(self):
        script = render_boot_script(
            "http://192.168.40.36:8080", should_install=True
        )

        self.assertIn("#!ipxe", script)
        self.assertIn(
            "chain --replace http://192.168.40.36:8080/assets/boot.ipxe",
            script,
        )

    def test_non_ready_boot_script_exits_to_local_boot(self):
        script = render_boot_script(
            "http://192.168.40.36:8080", should_install=False
        )

        self.assertIn("#!ipxe", script)
        self.assertIn("exit", script)
        self.assertNotIn("/assets/boot.ipxe", script)

    def test_answer_targets_only_nvme_and_pins_green_nic(self):
        answer = render_answer(
            GREEN_MAC,
            green_machine(),
            "$y$test-root-password-hash",
            "http://192.168.40.36:8080",
            "attempt-1",
            ["ssh-ed25519 AAAATEST jedi-pc"],
        )

        self.assertIn('fqdn = "green-server.galaxy"', answer)
        self.assertIn('root-password-hashed = "$y$test-root-password-hash"', answer)
        self.assertIn('disk-list = ["nvme0n1"]', answer)
        self.assertNotIn("sda", answer)
        self.assertIn('"02:00:00:00:00:01" = "nic0"', answer)
        self.assertIn('source = "from-dhcp"', answer)
        self.assertIn('ordering = "network-online"', answer)
        self.assertIn(
            'root-ssh-keys = ["ssh-ed25519 AAAATEST jedi-pc"]', answer
        )
        self.assertIn("reboot-on-error = true", answer)
        self.assertIn("[post-installation-webhook]", answer)
        self.assertIn(
            "/v1/installer-complete?"
            "mac=02%3A00%3A00%3A00%3A00%3A01&attempt=attempt-1",
            answer,
        )
        self.assertIn(
            'url = "http://192.168.40.36:8080/v1/bootstrap'
            "?mac=02%3A00%3A00%3A00%3A00%3A01&attempt=attempt-1\"",
            answer,
        )

    def test_acceptance_machine_powers_off_without_first_boot(self):
        machine = {
            "hostname": "pxe-acceptance",
            "domain": "galaxy",
            "install_disk": "sda",
            "acceptance_only": True,
        }

        answer = render_answer(
            "02:00:00:00:09:99",
            machine,
            "$y$test-root-password-hash",
            "http://192.168.40.36:8080",
            "attempt-acceptance",
            ["ssh-ed25519 AAAATEST test"],
        )

        self.assertIn('reboot-mode = "power-off"', answer)
        self.assertNotIn('reboot-mode = "poweroff"', answer)
        self.assertIn('disk-list = ["sda"]', answer)
        self.assertNotIn("[first-boot]", answer)

    def test_first_boot_configures_both_vlan_interfaces_and_cluster_join(self):
        script = render_first_boot(
            GREEN_MAC,
            green_machine(),
            "http://192.168.40.36:8080",
            "attempt-1",
        )

        self.assertIn("auto vmbr0.70", script)
        self.assertIn("address 192.168.70.14/24", script)
        self.assertIn("auto vmbr0.71", script)
        self.assertIn("address 192.168.71.14/24", script)
        self.assertIn("pvecm add 192.168.70.10", script)
        self.assertIn("--use_ssh", script)
        self.assertIn("--link0 address=192.168.70.14", script)
        self.assertIn("--link1 address=192.168.71.14", script)
        self.assertNotIn("--fingerprint", script)
        self.assertNotIn("expect <<", script)
        self.assertIn("/v1/join-key", script)
        self.assertIn("ssh -o BatchMode=yes", script)
        self.assertIn("PermitRootLogin prohibit-password", script)
        self.assertIn("sshd -t", script)
        self.assertIn("NoMoreNagging", script)
        self.assertIn("popup_source_unexpected", script)
        self.assertIn('if [ "${popup_changed}" -eq 1 ]', script)
        self.assertIn("systemctl restart pveproxy", script)
        self.assertIn("report_state first_boot_started", script)
        self.assertIn("report_state network_ready", script)
        self.assertIn("report_state cluster_joined", script)
        self.assertIn("report_state complete", script)
        self.assertNotIn("ping ", script)
        self.assertEqual(script.count("--retry-connrefused"), 2)
        self.assertEqual(script.count("--retry 30"), 2)
        self.assertIn("Grey did not accept the dedicated SSH join key.", script)
        self.assertIn('fail "join_ssh_unreachable"', script)
        self.assertIn('fail "cluster_not_converged"', script)
        self.assertIn('fail "sata_became_lvm_pv"', script)
        self.assertIn("BatchMode yes", script)
        self.assertIn("ConnectTimeout 5", script)
        self.assertIn("for attempt in $(seq 1 30); do", script)
        self.assertIn("cluster_ready=false", script)
        self.assertIn("Galaxy did not converge to five nodes", script)
        self.assertEqual(script.count("exit 1"), 1)
        self.assertLess(
            script.index("ssh -o BatchMode=yes"),
            script.index("report_state network_ready"),
        )
        self.assertLess(
            script.index("report_state network_ready"),
            script.index("pvecm add 192.168.70.10"),
        )
        self.assertIn(
            'ip -4 -o addr show dev vmbr0.70 | grep -Fq "inet 192.168.70.14/24"',
            script,
        )
        self.assertIn(
            'ip -4 -o addr show dev vmbr0.71 | grep -Fq "inet 192.168.71.14/24"',
            script,
        )
        self.assertIn('for link_id in 0 1; do', script)
        self.assertIn('grep -c "connected$"', script)
        self.assertIn('test "${connected_count}" -eq 4 || links_ready=false', script)
        self.assertLess(
            script.index("cluster_ready=false"),
            script.index("report_state cluster_joined"),
        )
        self.assertLess(
            script.index("report_state cluster_joined"),
            script.index("report_state complete"),
        )
        self.assertIn("pvecm status", script[: script.index("report_state complete")])
        self.assertNotIn("test-root-password", script)

    def test_installer_result_summary_keeps_boot_disk_without_serials(self):
        payload = {
            "$schema": {"version": "1.1"},
            "fqdn": "green-server.galaxy",
            "boot-info": {"mode": "efi", "secureboot": False},
            "filesystem": "ext4",
            "disks": [
                {
                    "path": "/dev/nvme0n1",
                    "size": 256060514304,
                    "is-bootdisk": True,
                    "udev-properties": {
                        "ID_MODEL": "SAMSUNG MZVLB256HAHQ",
                        "ID_SERIAL": "DO-NOT-RETAIN",
                    },
                },
                {
                    "path": "/dev/sda",
                    "size": 500107862016,
                    "is-bootdisk": False,
                },
            ],
            "network-interfaces": [
                {
                    "name": "nic0",
                    "mac": GREEN_MAC,
                    "address": "192.168.5.18/24",
                }
            ],
        }

        summary = summarize_installer_result(payload)

        self.assertEqual(summary["schema_version"], "1.1")
        self.assertEqual(summary["boot_disks"], ["/dev/nvme0n1"])
        self.assertEqual(summary["other_disks"], ["/dev/sda"])
        self.assertNotIn("DO-NOT-RETAIN", json.dumps(summary))


class FileResponse:
    command = "GET"

    def __init__(self):
        self.status = None
        self.headers = {}
        self.wfile = io.BytesIO()

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass


class RuntimeTests(unittest.TestCase):
    def test_http_lifecycle_reaches_complete_only_after_cluster_join(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            machine_path = root / "machines.json"
            state_path = root / "state.json"
            asset_dir = root / "assets"
            root_hash = root / "root.hash"
            root_ssh_keys = root / "root-ssh-keys"
            join_key = root / "join-key"
            asset_dir.mkdir()
            machine_path.write_text(
                json.dumps({"machines": {GREEN_MAC: green_machine()}}),
                encoding="utf-8",
            )
            root_hash.write_text("$6$test", encoding="utf-8")
            root_ssh_keys.write_text(
                "ssh-ed25519 AAAATEST test\n", encoding="utf-8"
            )
            join_key.write_text("private-test-key\n", encoding="utf-8")
            args = SimpleNamespace(
                listen="127.0.0.1",
                port=0,
                base_url="http://placeholder",
                machines=str(machine_path),
                state=str(state_path),
                assets=str(asset_dir),
                root_hash=str(root_hash),
                root_ssh_keys=str(root_ssh_keys),
                join_key=str(join_key),
            )
            server = build_server(args)
            base_url = f"http://127.0.0.1:{server.server_port}"
            server.base_url = base_url
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            server.registry.set_state(GREEN_MAC, "ready")

            boot = urlopen(
                f"{base_url}/v1/boot?mac={GREEN_MAC}", timeout=2
            ).read().decode()
            self.assertIn("/assets/boot.ipxe", boot)

            payload = {
                "schema": {"version": "1.0"},
                "sysinfo": {
                    "dmi": {"system": {"product": "ThinkCentre M920q"}},
                    "network_interfaces": [{"link": "nic0", "mac": GREEN_MAC}],
                },
            }
            answer = urlopen(
                Request(
                    f"{base_url}/v1/answer",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=2,
            ).read().decode()
            attempt_id = server.registry.record(GREEN_MAC)["attempt_id"]
            self.assertIn(f"attempt={attempt_id}", answer)
            self.assertEqual(server.registry.status(GREEN_MAC), "answer_served")

            urlopen(
                f"{base_url}/v1/bootstrap?mac={GREEN_MAC}&attempt={attempt_id}",
                timeout=2,
            )
            self.assertEqual(
                server.registry.status(GREEN_MAC), "bootstrap_fetched"
            )

            installer_result = {
                "$schema": {"version": "1.1"},
                "fqdn": "green-server.galaxy",
                "filesystem": "ext4",
                "disks": [
                    {
                        "size": 256060514304,
                        "is-bootdisk": True,
                        "udev-properties": {"DEVNAME": "/dev/nvme0n1"},
                    },
                    {
                        "size": 500107862016,
                        "udev-properties": {"DEVNAME": "/dev/sda"},
                    },
                ],
            }
            response = urlopen(
                Request(
                    f"{base_url}/v1/installer-complete?"
                    f"mac={GREEN_MAC}&attempt={attempt_id}",
                    data=json.dumps(installer_result).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=2,
            )
            self.assertEqual(response.status, 204)
            self.assertEqual(
                server.registry.status(GREEN_MAC), "installer_succeeded"
            )

            response = urlopen(
                Request(
                    f"{base_url}/v1/state/first_boot_started?"
                    f"mac={GREEN_MAC}&attempt={attempt_id}",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=2,
            )
            self.assertEqual(response.status, 204)
            recovered_bootstrap = urlopen(
                f"{base_url}/v1/bootstrap?"
                f"mac={GREEN_MAC}&attempt={attempt_id}",
                timeout=2,
            ).read().decode()
            self.assertIn("report_state first_boot_started", recovered_bootstrap)
            self.assertEqual(
                server.registry.status(GREEN_MAC), "first_boot_started"
            )

            for phase in (
                "network_ready",
                "cluster_joined",
                "complete",
            ):
                response = urlopen(
                    Request(
                        f"{base_url}/v1/state/{phase}?"
                        f"mac={GREEN_MAC}&attempt={attempt_id}",
                        data=b"{}",
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )
                self.assertEqual(response.status, 204)

            self.assertEqual(server.registry.status(GREEN_MAC), "complete")
            second_boot = urlopen(
                f"{base_url}/v1/boot?mac={GREEN_MAC}", timeout=2
            ).read().decode()
            self.assertNotIn("/assets/boot.ipxe", second_boot)

    def test_deployment_prepares_ssh_join_and_nomodeset_installer(self):
        playbook = (PROJECT_ROOT / "playbooks" / "deploy.yml").read_text(
            encoding="utf-8"
        )
        unit = (
            PROJECT_ROOT / "templates" / "galaxy-pxe.service.j2"
        ).read_text(encoding="utf-8")

        self.assertIn("cluster-join-key", playbook)
        self.assertIn("grey-server", playbook)
        self.assertIn("/root/.ssh/authorized_keys", playbook)
        self.assertIn("nomodeset", playbook)
        self.assertIn("--root-ssh-keys", unit)
        self.assertIn("--join-key", unit)
        self.assertNotIn("--cluster-password", unit)

    def test_asset_response_streams_without_path_read_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            asset = Path(temp_dir) / "large.iso"
            content = b"x" * (2 * 1024 * 1024 + 17)
            asset.write_bytes(content)
            response = FileResponse()

            with mock.patch.object(
                Path, "read_bytes", side_effect=AssertionError("bulk read")
            ):
                stream_file_response(
                    response, asset, "application/octet-stream", chunk_size=65536
                )

            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Length"], str(len(content)))
            self.assertEqual(response.wfile.getvalue(), content)

    def test_runtime_input_validation_rejects_empty_credentials(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root_hash = root / "root.hash"
            root_ssh_keys = root / "root-ssh-keys"
            join_key = root / "cluster-join-key"
            root_hash.write_text("$6$test", encoding="utf-8")
            root_ssh_keys.write_text("ssh-ed25519 AAAATEST test\n", encoding="utf-8")
            join_key.write_bytes(b"")

            with self.assertRaises(ValueError):
                validate_runtime_inputs(root_hash, root_ssh_keys, join_key)


if __name__ == "__main__":
    unittest.main()
