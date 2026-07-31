# S07 Deployment Residue Cleanup

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Step date:** 2026-07-31  
**System:** `ansible-01`

## Pre-delete gate

I resolved each candidate by its absolute path and confirmed both `galaxy-pxe.service` and `tftpd-hpa.service` were active. The retired `/etc/galaxy-pxe/cluster-password` file was already absent. The only current text match for `cluster-password` was the regression assertion that rejects the removed `--cluster-password` option.

I removed these superseded deployment artifacts:

- `/home/ansible/proxmox-pxe-provisioning/config/machines.json.bak.20260731_025627`
- `/home/ansible/proxmox-pxe-provisioning/tests/test_service.py.bak.20260731_025627`
- `/home/ansible/proxmox-pxe-provisioning/playbooks/deploy.yml.bak.20260731_025627`
- `/home/ansible/proxmox-pxe-provisioning/app/__pycache__/`
- `/home/ansible/proxmox-pxe-provisioning/tests/__pycache__/`
- `/usr/local/lib/galaxy-pxe/__pycache__/`
- `/home/ansible/.ansible/tmp/ansible-local-13451969swvbf/`

I retained the authoritative source tree, systemd services, prepared installer assets, TFTP loader, state database, join key, and reusable ISO and package caches.

I also removed the one-use `codex-green-askpass.cmd` and `galaxy-green-known-hosts` files from my Windows temporary directory. I deleted the ignored local Python bytecode caches under the PXE source tree after resolving their exact workspace paths.

## Verification

The post-delete check found every listed path absent. `galaxy-pxe.service` and `tftpd-hpa.service` both returned `active`, and `http://127.0.0.1:8080/health` returned `ok`.

I ran the deployed suite with `PYTHONDONTWRITEBYTECODE=1`. All 21 tests passed in 0.578 seconds, and neither source test directory recreated a `__pycache__` directory. The two Windows helpers and both local cache directories were absent after cleanup.
