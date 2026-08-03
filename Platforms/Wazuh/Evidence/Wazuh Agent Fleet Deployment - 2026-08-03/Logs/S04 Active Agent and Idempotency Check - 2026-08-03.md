# S04 Active Agent and Idempotency Check

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:43 through 02:45 EDT  
**Targets:** Wazuh manager & four deployed endpoints  
**Mechanism:** SSH Manager MCP; manager CLI through `ansible-01`; Ansible Core 2.21.2

## Manager result

```text
ID: 004, Name: app-01, IP: any, Active
ID: 005, Name: edge-01, IP: any, Active
ID: 006, Name: alpha-prod-01, IP: any, Active
ID: 007, Name: docker-blue, IP: any, Active
ID: 008, Name: media-01, IP: any, Active
ID: 009, Name: ansible-01, IP: any, Active
```

ID 009 first appeared as `Never connected`. At `2026-08-03T06:43:24+00:00`, its log recorded:

```text
wazuh-agentd: INFO: Trying to connect to server ([192.168.72.2]:1514/tcp).
wazuh-agentd: INFO: (4102): Connected to the server ([192.168.72.2]:1514/tcp).
wazuh-agentd: INFO: Agent is reloading due to shared configuration changes.
```

The manager log recorded its enrollment at `06:43:04`, so the first state sample landed inside a 20-second first-check-in interval. I added a persistent `1514/tcp` session wait to the playbook.

## Endpoint result

```text
docker-blue:    package=4.14.6-1 hold=hold enabled=enabled active=active sessions=1
alpha-prod-01:  package=4.14.6-1 hold=hold enabled=enabled active=active sessions=1
media-01:       package=4.14.6-1 hold=hold enabled=enabled active=active sessions=1
ansible-01:     package=4.14.6-1 hold=hold enabled=enabled active=active sessions=1
```

## Idempotency command

```bash
cd /home/ansible/wazuh-agent-deployment && ansible-playbook playbooks/deploy.yml --syntax-check && ansible-playbook playbooks/deploy.yml --limit 'docker-blue:alpha-prod-01:media-01:ansible-01'
```

```text
alpha-prod-01 : ok=14 changed=0 unreachable=0 failed=0 skipped=7
ansible-01    : ok=14 changed=0 unreachable=0 failed=0 skipped=7
docker-blue   : ok=14 changed=0 unreachable=0 failed=0 skipped=7
media-01      : ok=14 changed=0 unreachable=0 failed=0 skipped=7
```

The syntax check & idempotency run exited `0`.

