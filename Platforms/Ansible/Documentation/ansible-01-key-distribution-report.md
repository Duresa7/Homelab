# ansible-01 Key Distribution Report

**Created:** 2026-04-17  
**Last updated:** 2026-07-20

Generated: 2026-04-17  
Source node: proxmox_grey  
Source LXC: 100 (ansible-01)

> **Superseded:** This is a historical snapshot of the original hard-coded distribution playbook. The active implementation is [SSH Identity Automation](Change%20Records/SSH%20Identity%20Automation%20-%202026-07-14.md), with operating instructions in the [SSH Identity Automation Runbook](Runbook.md).

## Overview

I inventoried my `ansible-01` control node and documented the SSH key distribution playbook I run there. This snapshot captures the inventory and playbook exactly as they existed on 2026-04-17.

The playbook is configured to:

- target the `lxc` and `management` groups as `root` with privilege escalation enabled
- target the `VM` group as user `<YOUR_ADMIN_USERNAME>` without privilege escalation
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
| app-01 | 192.168.80.10 | `<YOUR_ADMIN_USERNAME>` |
| security-01 | 192.168.70.20 | `<YOUR_ADMIN_USERNAME>` |
| edge-01 | 192.168.90.10 | `<YOUR_ADMIN_USERNAME>` |
| db-13-test | 192.168.40.135 | `<YOUR_ADMIN_USERNAME>` |
| alpha-prod-01 | 192.168.80.118 | `<YOUR_ADMIN_USERNAME>` |

## Raw Inventory File

Path: `/home/ansible/ansible/inventory/hosts.ini`

```ini
[lxc]
docker-main ansible_host=192.168.40.35 ansible_user=root
docker-red ansible_host=192.168.40.30 ansible_user=root

[management]
grey-server ansible_host=192.168.70.10 ansible_user=root

[VM]
app-01 ansible_host=192.168.80.10 ansible_user=<YOUR_ADMIN_USERNAME>
security-01 ansible_host=192.168.70.20 ansible_user=<YOUR_ADMIN_USERNAME>
edge-01 ansible_host=192.168.90.10 ansible_user=<YOUR_ADMIN_USERNAME>
db-13-test ansible_host=192.168.40.135 ansible_user=<YOUR_ADMIN_USERNAME>
alpha-prod-01 ansible_host=192.168.80.118 ansible_user=<YOUR_ADMIN_USERNAME>
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
        - "<YOUR_ADMIN_KEY_ONE_PUBLIC_KEY>"
        - "<YOUR_ADMIN_KEY_TWO_PUBLIC_KEY>"
        - "<YOUR_ADMIN_KEY_THREE_PUBLIC_KEY>"

- hosts: VM
  become: no
  tasks:
    - name: Deploy authorized SSH keys
      authorized_key:
        user: <YOUR_ADMIN_USERNAME>
        key: "{{ item }}"
        state: present
      loop:
        - "<YOUR_ADMIN_KEY_ONE_PUBLIC_KEY>"
        - "<YOUR_ADMIN_KEY_TWO_PUBLIC_KEY>"
        - "<YOUR_ADMIN_KEY_THREE_PUBLIC_KEY>"
```

## Notes

- The inventory currently defines 9 managed hosts across 3 groups.
- The playbook deploys the same 3 SSH public keys to every configured host.
- For `lxc` and `management`, the keys are placed under `root`.
- For `VM`, the keys are placed under `<YOUR_ADMIN_USERNAME>`.
