# Upstream Ansible virtual environment initially lacked its venv package

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

Creating `/opt/ansible-14.2.0` initially stopped before any runtime switch because Debian did not have `python3.13-venv` installed. I installed the missing package, recreated the versioned environment, and Ansible 14.2.0 with ansible-core 2.21.2 then installed successfully. I kept Debian's Ansible packages as a fallback.

The failed step identified the absent `python3.13-venv` package and made no runtime switch. APT's retained history confirms the corrective command and successful install:

```text
Commandline: apt-get install -y python3.13-venv
Install: python3.13-venv:amd64 (3.13.5-2+deb13u3)
End-Date: 2026-07-15  02:09:56
```

The package installation also displayed the controller's pre-existing `en_US.UTF-8` locale warning. The exact Ansible error when the unsupported locale was inherited was `ERROR: Ansible could not initialize the preferred locale: unsupported locale setting`. Runtime and service verification used `LANG=C.utf8` and `LC_ALL=C.utf8`, matching the runbook and Semaphore service environment, and completed successfully.

During final verification, one validator command used the nonexistent `scripts/validate_project.py` path and exited 2 without changing state. Its exact error was `python3: can't open file '/home/ansible/ssh-key-automation/scripts/validate_project.py': [Errno 2] No such file or directory`. Re-running `python3 tests/validate_project.py` returned `Validation passed: 4 identities, 15 supported hosts, 2 unknown hosts, 18 Semaphore templates.`, followed by successful syntax checks of all five playbooks.
