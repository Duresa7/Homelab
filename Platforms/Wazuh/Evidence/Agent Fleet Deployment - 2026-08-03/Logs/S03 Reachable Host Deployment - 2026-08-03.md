# S03 Reachable Host Deployment

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:41 through 02:43 EDT  
**Target:** `/home/ansible/wazuh-agent-deployment` on `ansible-01`  
**Mechanism:** SSH Manager MCP running Ansible Core 2.21.2

## First command

```bash
cd /home/ansible/wazuh-agent-deployment && ansible-playbook playbooks/deploy.yml --limit 'docker-blue:alpha-prod-01:media-01:ansible-01'
```

The first serial batch stopped before package installation:

```text
TASK [Permit an explicit Wazuh package version change]
Failed to find package 'wazuh-agent' to perform selection 'install'.

PLAY RECAP
alpha-prod-01 : ok=9 changed=4 unreachable=0 failed=1
docker-blue   : ok=9 changed=4 unreachable=0 failed=1
media-01      : ok=9 changed=4 unreachable=0 failed=1
```

The command exited `2`. The three hosts had the signing key, prerequisites, & enabled repository, but no `wazuh-agent` package, service, manager key, or identity.

## Correction

I removed the premature `dpkg_selections` task. The package install already uses `allow_change_held_packages: true`, so it doesn't need a package record before APT reads the new repository.

## Corrected command

```bash
cd /home/ansible/wazuh-agent-deployment && ansible-playbook playbooks/deploy.yml --syntax-check && ansible-playbook playbooks/deploy.yml --limit 'docker-blue:alpha-prod-01:media-01:ansible-01'
```

```text
playbook: playbooks/deploy.yml

PLAY RECAP
alpha-prod-01 : ok=17 changed=5 unreachable=0 failed=0 skipped=1
ansible-01    : ok=18 changed=9 unreachable=0 failed=0 skipped=0
docker-blue   : ok=17 changed=5 unreachable=0 failed=0 skipped=1
media-01      : ok=17 changed=5 unreachable=0 failed=0 skipped=1
```

The corrected command exited `0`. Each host installed `4.14.6-1`, disabled its Wazuh repository, held the package, enabled the service, & received a non-empty client key.

