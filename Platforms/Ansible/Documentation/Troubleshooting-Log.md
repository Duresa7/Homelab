# Ansible Troubleshooting Log

**Created:** 2026-07-14  
**Last updated:** 2026-07-14

## 2026-07-14 — Initial audit reported false missing keys and unknown host fingerprints

The first full Mac audit connected to six targets, rejected seven targets whose host fingerprints were not yet trusted by `ansible-01`, and timed out against `edge-01` and `ws-dc-1-main`. The original parser also treated valid key lines as missing because its regular expression was too strict.

The parser was changed to compare the first two whitespace-separated fields—algorithm and encoded key material. Host fingerprints were read through authenticated SSH Manager sessions, independently scanned from the controller, and enrolled only where the SHA256 values matched. A first known-host update attempt failed because of incorrect `awk` escaping and made no successful change; the corrected update was then verified by fingerprint. Full details are in S03 evidence.

## 2026-07-14 — SSH Manager host-key helper could not negotiate with current OpenSSH

The helper returned a key-exchange compatibility error involving the newer `sntrup761` method. It was not used to accept keys automatically. Authenticated SSH Manager commands read each target's existing ED25519 host-key fingerprint, and controller-side `ssh-keyscan` results had to match before enrollment.

## 2026-07-14 — Several hosts remained unreachable from the controller

Final TCP probes and Ansible audits classified `supabase-01`, `ai-alpha-01`, `ai-bravo-02`, and `ws-dc-1-main` as unreachable. Direct SSH Manager checks also timed out. `ws-dc-2-secondary` and `obi-pc` timed out and remain deliberately unknown.

UniFi Traffic Flows recorded the controller's SSH attempts as allowed, including prior flows to `edge-01` and `ws-dc-1-main`. No UniFi firewall change was warranted. `edge-01` became reachable after its independently verified host key was enrolled. The other failures are endpoint availability, host firewall, or SSH-service issues to investigate when those machines are online.

## 2026-07-14 — Ansible failed when the locale was omitted

One final audit attempt exited 1 with `unsupported locale setting` because `runuser` did not preserve the expected locale. Re-running with `LANG=C.utf8` and `LC_ALL=C.utf8` succeeded. The runbook and Semaphore environment both set these variables explicitly.

## 2026-07-14 — Final transfer archive temporarily reset the project directory mode

A pre-commit syntax run warned that `/home/ansible/ssh-key-automation` was world-writable, so Ansible ignored the project's `ansible.cfg` and inventory. The Windows-created transfer archive had reapplied permissive directory metadata during extraction.

The deployed project directories were explicitly reset to mode 0755, ordinary files to 0644, and `tests/validate_project.py` to 0755. `stat` confirmed the root directory and key files, then the validator and all five syntax checks passed again without warnings. No playbook reached a managed host during this correction.

## 2026-07-14 — Semaphore CLI export/import limitations

The first export attempt omitted the required project ID or name and exited without creating a backup. A separate attempt to inspect JSON with `jq` failed because `jq` is not installed; Python was used for secret-safe structural inspection instead.

Semaphore's project backup contains key metadata but intentionally excludes the private key. Importing it as a new project would therefore create an empty SSH credential, so the CLI import path was not used as a substitute for authenticated UI/API configuration. The original project export remains the rollback reference.

## 2026-07-14 — Semaphore's first view remained an aggregate view

Renaming the original `All` view to `Onboarding` changed its label but did not make it a filtered view; it still displayed every template. The view was renamed back to `All`, a separate `Onboarding` view was created, and the two onboarding templates were reassigned to it.

Final UI counts were 18 in `All`, four in each identity view, and two in `Onboarding`. The obsolete `Distribute SSH Keys` template was removed after the replacement set was verified. No template was launched during configuration.

## 2026-07-14 — Upstream Ansible virtual environment initially lacked its venv package

Creating `/opt/ansible-14.2.0` initially stopped before any runtime switch because Debian did not have `python3.13-venv` installed. The missing package was installed, the versioned environment was recreated, and Ansible 14.2.0 with ansible-core 2.21.2 then installed successfully. Debian's Ansible packages were retained as a fallback.

The original venv stderr was not retained by the remote execution transcript; the failed step identified the absent `python3.13-venv` package and made no runtime switch. APT's retained history confirms the corrective command and successful install:

```text
Commandline: apt-get install -y python3.13-venv
Install: python3.13-venv:amd64 (3.13.5-2+deb13u3)
End-Date: 2026-07-15  02:09:56
```

The package installation also displayed the controller's pre-existing `en_US.UTF-8` locale warning. The exact Ansible error when the unsupported locale was inherited was `ERROR: Ansible could not initialize the preferred locale: unsupported locale setting`. Runtime and service verification used `LANG=C.utf8` and `LC_ALL=C.utf8`, matching the runbook and Semaphore service environment, and completed successfully.

During final verification, one validator command used the nonexistent `scripts/validate_project.py` path and exited 2 without changing state. Its exact error was `python3: can't open file '/home/ansible/ssh-key-automation/scripts/validate_project.py': [Errno 2] No such file or directory`. Re-running `python3 tests/validate_project.py` returned `Validation passed: 4 identities, 15 supported hosts, 2 unknown hosts, 18 Semaphore templates.`, followed by successful syntax checks of all five operator playbooks.
