# ansible-01 Key Distribution Report

**Created:** 2026-04-17  
**Last updated:** 2026-07-17

Generated: 2026-04-17
Source node: proxmox_grey

> **Superseded:** This is a historical snapshot of the original hard-coded distribution playbook. The active implementation is [SSH Identity Automation](Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md), with operating instructions in the [SSH Identity Automation Runbook](Runbook.md).
Source LXC: 100 (ansible-01)

## Overview

This report combines the current Ansible inventory and the SSH key distribution playbook found on `ansible-01`.

The playbook is configured to:

- target the `lxc` and `management` groups as `root` with privilege escalation enabled
- target the `VM` group as user `REDACTED_USER_001` without privilege escalation
- deploy three SSH public keys to the configured hosts

## Inventory Summary

### Group: lxc

| Host | IP | User |
| --- | --- | --- |
| docker-main | 192.168.40.35 | root |
| docker-red | 192.168.40.30 | root |

### Group: management

| Host | IP | User |
| --- | --- | --- |
| grey-server | 192.168.70.10 | root |

### Group: VM

| Host | IP | User |
| --- | --- | --- |
| app-01 | 192.168.80.10 | REDACTED_USER_001 |
| security-01 | 192.168.70.20 | REDACTED_USER_001 |
| edge-01 | 192.168.90.10 | REDACTED_USER_001 |
| db-13-test | 192.168.40.135 | REDACTED_USER_001 |
| alpha-prod-01 | 192.168.80.118 | REDACTED_USER_001 |

## Raw Inventory File

Path: `/home/ansible/ansible/inventory/hosts.ini`

```ini
[lxc]
docker-main ansible_host=192.168.40.35 ansible_user=root
docker-red ansible_host=192.168.40.30 ansible_user=root

[management]
grey-server ansible_host=192.168.70.10 ansible_user=root

[VM]
app-01 ansible_host=192.168.80.10 ansible_user=REDACTED_USER_001
security-01 ansible_host=192.168.70.20 ansible_user=REDACTED_USER_001
edge-01 ansible_host=192.168.90.10 ansible_user=REDACTED_USER_001
db-13-test ansible_host=192.168.40.135 ansible_user=REDACTED_USER_001
alpha-prod-01 ansible_host=192.168.80.118 ansible_user=REDACTED_USER_001
```

## Raw Playbook File

Path: `/home/ansible/ansible/playbooks/distribute_keys.yml`

```yaml
---
- hosts: lxc,management
  become: yes
  tasks:
    - name: Deploy authorized SSH keys
      authorized_key:
        user: root
        key: "{{ item }}"
        state: present
      loop:
        - "REDACTED_SSH_PUBLIC_KEY_002
        - "REDACTED_SSH_PUBLIC_KEY_006
        - "REDACTED_SSH_PUBLIC_KEY_004

- hosts: VM
  become: no
  tasks:
    - name: Deploy authorized SSH keys
      authorized_key:
        user: REDACTED_USER_001
        key: "{{ item }}"
        state: present
      loop:
        - "REDACTED_SSH_PUBLIC_KEY_002
        - "REDACTED_SSH_PUBLIC_KEY_006
        - "REDACTED_SSH_PUBLIC_KEY_004
```

## Notes

- The inventory currently defines 9 managed hosts across 3 groups.
- The playbook deploys the same 3 SSH public keys to every configured host.
- For `lxc` and `management`, the keys are placed under `root`.
- For `VM`, the keys are placed under `REDACTED_USER_001`.
