# Immediate Service Fact Assertion Raced Wazuh Agent Startup

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

## Symptom

The first deployment batch installed `wazuh-agent` 4.14.6-1 on `monitor-01`, `docker-network`, & `kasm-01`. Each host had a non-empty client key and an established TCP 1514 session, but the final assertion failed:

```text
ansible_facts.services['wazuh-agent.service'].state == 'running'
```

The play exited `2`. Its recap showed one failed task on each host after 20 successful tasks.

## Failed Attempt

The play originally read `service_facts` once, immediately after the TCP 1514 session wait. That snapshot treated service discovery as a readiness check. It wasn't one.

## Hypotheses and Tests

I checked `wazuh-agent` through SSH Manager less than one minute after the failure. All three units were enabled & running. The enrollment keys and TCP sessions remained present, so no agent repair was required.

The later Proxmox deployment reproduced the timing boundary after I added a direct service poll. Grey, Purple, Blue, Red, & Green each failed one or two `systemctl is-active` attempts before returning `active`. Their eventual state matched the first three hosts.

## Root Cause

The agent can establish its event socket before systemd reports `wazuh-agent.service` active through the final verification path. The play waited for enrollment and the TCP session but didn't wait for the service state. An immediate `service_facts` assertion could therefore fail during a successful first start.

## Corrective Action

I added a bounded readiness task before `service_facts`:

```yaml
- name: Wait for the Wazuh agent service to become active
  ansible.builtin.command:
    argv:
      - systemctl
      - is-active
      - wazuh-agent
  register: wazuh_agent_active
  changed_when: false
  failed_when: false
  until:
    - wazuh_agent_active.rc == 0
    - wazuh_agent_active.stdout | trim == 'active'
  retries: 12
  delay: 5
```

The final assertion now checks the registered return code & exact `active` output. I kept `service_facts` for the separate enabled-state check.

## Verification

The corrected file had matching local & remote SHA-256 `8459a74cc11342bc975455c0b4e485b77311a8675d4386c270057cf910d5dc56` and passed `ansible-playbook --syntax-check`.

The rerun against `monitor-01`, `docker-network`, & `kasm-01` changed zero hosts and passed every assertion. Grey, Purple, Blue, Red, & Green then installed with zero failures. A final seven-host run and the later Green-only run returned `changed=0`, `failed=0`, & `unreachable=0` for every target.
