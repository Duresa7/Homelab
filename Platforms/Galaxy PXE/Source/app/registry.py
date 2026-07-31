import json
import os
import tempfile
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


OPERATOR_STATES = {"disabled", "ready"}
ATTEMPT_PHASES = {
    "installer_claimed",
    "answer_served",
    "bootstrap_fetched",
    "installer_succeeded",
    "first_boot_started",
    "network_ready",
    "cluster_joined",
}
TERMINAL_STATES = {"complete", "failed"}
VALID_STATES = OPERATOR_STATES | ATTEMPT_PHASES | TERMINAL_STATES

ALLOWED_TRANSITIONS = {
    "installer_claimed": {"answer_served", "failed"},
    "answer_served": {"bootstrap_fetched", "installer_succeeded", "failed"},
    "bootstrap_fetched": {
        "installer_succeeded",
        "first_boot_started",
        "failed",
    },
    "installer_succeeded": {"first_boot_started", "failed"},
    "first_boot_started": {"network_ready", "failed"},
    "network_ready": {"cluster_joined", "failed"},
    "cluster_joined": {"complete", "failed"},
}


def utc_now():
    return datetime.now(timezone.utc)


class MachineRegistry:
    def __init__(
        self,
        machine_path,
        state_path,
        *,
        now=utc_now,
        id_factory=None,
    ):
        self.machine_path = Path(machine_path)
        self.state_path = Path(state_path)
        self._thread_lock = threading.Lock()
        self.lock_path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        self._now = now
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        machine_data = json.loads(self.machine_path.read_text(encoding="utf-8"))
        self.machines = {
            self._normalize_mac(mac): machine
            for mac, machine in machine_data["machines"].items()
        }

    @staticmethod
    def _normalize_mac(value):
        from rendering import normalize_mac

        return normalize_mac(value)

    def _timestamp(self):
        return self._now().astimezone(timezone.utc).isoformat(timespec="seconds")

    def _read_states(self):
        if not self.state_path.exists():
            return {}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write_states(self, states):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".state-", dir=self.state_path.parent, text=True
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(states, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.state_path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    @contextmanager
    def state_lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            with self.lock_path.open("a+b") as handle:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0, os.SEEK_END)
                    if handle.tell() == 0:
                        handle.write(b"\0")
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    handle.seek(0)
                    if os.name == "nt":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _coerce_record(self, value):
        if isinstance(value, dict):
            return value
        if value == "installing":
            return {
                "phase": "installer_claimed",
                "attempt_id": "legacy",
                "started_at": None,
                "updated_at": None,
                "detail": {"migrated_from": "installing"},
                "history": [],
            }
        phase = value if value in VALID_STATES else "disabled"
        return {
            "phase": phase,
            "attempt_id": None,
            "started_at": None,
            "updated_at": None,
            "detail": {},
            "history": [],
        }

    def _record_from_states(self, states, mac):
        return self._coerce_record(states.get(mac, "disabled"))

    def machine(self, mac):
        normalized = self._normalize_mac(mac)
        if normalized not in self.machines:
            raise KeyError(normalized)
        return self.machines[normalized]

    def record(self, mac):
        normalized = self._normalize_mac(mac)
        if normalized not in self.machines:
            raise KeyError(normalized)
        with self.state_lock():
            return self._record_from_states(self._read_states(), normalized)

    def status(self, mac):
        return self.record(mac)["phase"]

    def set_state(self, mac, state, *, force=False):
        normalized = self._normalize_mac(mac)
        if normalized not in self.machines:
            raise KeyError(normalized)
        if state not in VALID_STATES:
            raise ValueError(f"invalid state: {state}")
        with self.state_lock():
            states = self._read_states()
            current = self._record_from_states(states, normalized)
            if (
                state == "ready"
                and current["phase"] in ATTEMPT_PHASES | TERMINAL_STATES
                and not force
            ):
                raise ValueError(
                    "rearming an active or finished machine requires force"
                )
            timestamp = self._timestamp()
            states[normalized] = {
                "phase": state,
                "attempt_id": None,
                "started_at": None,
                "updated_at": timestamp,
                "detail": {},
                "history": [{"phase": state, "at": timestamp}],
            }
            self._write_states(states)

    def claim_install(self, mac):
        normalized = self._normalize_mac(mac)
        if normalized not in self.machines:
            return None
        with self.state_lock():
            states = self._read_states()
            current = self._record_from_states(states, normalized)
            if current["phase"] != "ready":
                return None
            timestamp = self._timestamp()
            record = {
                "phase": "installer_claimed",
                "attempt_id": self._id_factory(),
                "started_at": timestamp,
                "updated_at": timestamp,
                "detail": {},
                "history": [{"phase": "installer_claimed", "at": timestamp}],
            }
            states[normalized] = record
            self._write_states(states)
            return record

    def transition(self, mac, attempt_id, phase, detail=None):
        normalized = self._normalize_mac(mac)
        if normalized not in self.machines:
            raise KeyError(normalized)
        if phase not in ATTEMPT_PHASES | TERMINAL_STATES:
            raise ValueError(f"invalid attempt phase: {phase}")
        with self.state_lock():
            states = self._read_states()
            record = self._record_from_states(states, normalized)
            if record.get("attempt_id") != attempt_id:
                raise ValueError("attempt identifier does not match")
            current_phase = record["phase"]
            if current_phase == phase:
                return record
            if phase not in ALLOWED_TRANSITIONS.get(current_phase, set()):
                raise ValueError(
                    f"cannot transition from {current_phase} to {phase}"
                )
            timestamp = self._timestamp()
            event = {"phase": phase, "at": timestamp}
            if detail:
                event["detail"] = detail
                record.setdefault("detail", {}).update(detail)
            record["phase"] = phase
            record["updated_at"] = timestamp
            record.setdefault("history", []).append(event)
            states[normalized] = record
            self._write_states(states)
            return record
