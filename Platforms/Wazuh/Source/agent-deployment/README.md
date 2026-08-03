# Wazuh Agent Deployment

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

I use this Ansible project to install one host-level Wazuh agent on each listed Linux endpoint. The play pins `wazuh-agent` to `4.14.6-1`, which matches the manager package on `security-01` at the 2026-08-03 deployment check.

The play stops before package installation when TCP `1514` or `1515` can't reach `192.168.72.2`. It installs from the Wazuh 4.x APT repository, enrolls with the exact inventory hostname, starts `wazuh-agent.service`, polls its active state for up to 60 seconds, confirms a non-empty `/var/ossec/etc/client.keys`, places the package on hold, & disables the repository.

All five Galaxy Proxmox nodes enroll into both `default` and `proxmox`. The manager-side `proxmox` group must exist before their first enrollment; I created and validated it on 2026-08-03. Other targets enroll into `default`.

Run the syntax check from this directory:

```bash
ansible-playbook playbooks/deploy.yml --syntax-check
```

Deploy a bounded host set with `--limit`. The 2026-08-03 change record names the approved scope & preserves the manager-side result.

```bash
ansible-playbook playbooks/deploy.yml --limit 'alpha-prod-01:ansible-01'
```

I completed all twelve inventory targets on 2026-08-03. A final run across the original last seven hosts returned `changed=0`, `failed=0`, & `unreachable=0` for every endpoint. The later Green-only rerun also returned `changed=0`. The manager reported all twelve new identities active as IDs `006` through `017`.
