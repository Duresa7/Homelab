# Final transfer archive temporarily reset the project directory mode

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

A pre-commit syntax run warned that `/home/ansible/ssh-key-automation` was world-writable, so Ansible ignored the project's `ansible.cfg` and inventory. The Windows-created transfer archive had reapplied permissive directory metadata during extraction.

I reset the deployed project directories to mode 0755, ordinary files to 0644, and `tests/validate_project.py` to 0755. `stat` confirmed the root directory and key files, then the validator and all five syntax checks passed again without warnings. No playbook reached a managed host during this correction.
