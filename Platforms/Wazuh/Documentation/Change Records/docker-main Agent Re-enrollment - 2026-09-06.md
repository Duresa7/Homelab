# docker-main Agent Re-enrollment

**Created:** 2026-09-06  
**Last updated:** 2026-09-06

**Implementation date:** 2026-09-06  
**Status:** Complete  
**Affected systems:** `docker-main` (CT 110), Wazuh manager on `security-01`, the `agent-deployment` Ansible project on `ansible-01`

## Why

The [2026-09-06 documentation audit](../../../../Operations/Maintenance/Documentation%20Staleness%20Audit%20-%202026-09-06.md) found that `docker-main`'s Wazuh agent had never reached the current manager. `wazuh-agent` 4.14.0-1 was installed and its service was active, but `/var/ossec/etc/ossec.conf` had not changed since 2025-11-05 and still named `192.168.40.227`, the address `security-01` held before the [Security-A migration](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md) moved it to `192.168.72.2` on 2026-07-12. The agent logged `Unable to connect to '[192.168.40.227]:1514/tcp'` every ten seconds, its `client.keys` held a key issued as ID `001` by the old manager, and `agent_control -l` on the current manager listed 15 remote agents with no `docker-main` among them. Every record since 2026-08-03 had tracked the host as "on 4.14.0" rather than as absent. The host was also missing from the `agent-deployment` inventory, which is why the fleet play never touched it.

## What I did

I worked as root on `docker-main` through the SSH Manager, and mirrored the end state the [deploy play](../../Source/agent-deployment/playbooks/deploy.yml) produces so the play would agree with the host afterwards.

1. Confirmed TCP 1514 and 1515 to `192.168.72.2` were reachable from the host, and that the manager's `auth` block has `use_password` set to `no`.
2. Stopped `wazuh-agent`, installed the Wazuh signing key to `/usr/share/keyrings/wazuh.gpg`, wrote `/etc/apt/sources.list.d/wazuh.list`, and installed `wazuh-agent=4.14.6-1` over 4.14.0-1. The upgrade kept the existing `ossec.conf`, so the old address survived it, as expected.
3. Changed the one `<address>` element from `192.168.40.227` to `192.168.72.2`. No other line in the file referenced the old address.
4. Emptied `client.keys` and ran `agent-auth -m 192.168.72.2 -p 1515 -A docker-main`. It returned `Valid key received`, and the file now holds one key for ID `021`.
5. Held the package with `apt-mark hold`, commented the repository line so it reads `#deb ...`, and started the agent.
6. Added `docker-main` to `inventory/hosts.yml` in the `agent-deployment` project on `ansible-01`, as `ansible_user: ansible`, and ran `ansible-playbook playbooks/deploy.yml --limit docker-main`. The `ansible` account on the host has a `NOPASSWD` drop-in, so `become` worked. The run reported `ok=15 changed=0 failed=0`, with the seven installation tasks skipped because the version already matched. The repository copy of the inventory carries the same entry.

I kept a copy of the pre-change `ossec.conf` only in this repository's `Backups/` folder; it holds no credential. I did not copy `client.keys` anywhere.

## Verification

- `wazuh-control info` on the host reports `WAZUH_VERSION="v4.14.6"`, `WAZUH_TYPE="agent"`.
- `ossec.log` after the restart shows agentd reloading on the manager's shared configuration, logcollector and modulesd starting, and no `Unable to connect` line since. The two `Could not open file /var/log/apache2/...` errors are the stock Debian template's Apache entries and predate this change.
- On the manager, `agent_control -l` lists `ID: 021, Name: docker-main, IP: any, Active`, and `agent_control -i 021` returns `Status: Active` with the host's kernel string `7.0.14-8-pve`, which is grey-server's kernel seen from inside the container, as expected for an LXC. The manager now lists 16 active remote agents and nothing disconnected or pending, and `agent_groups -s -i 021` places `docker-main` in `default`, which now has 15 members.
- `apt-mark showhold` on the host returns `wazuh-agent`, and `apt-cache policy` shows the installed and candidate version as 4.14.6-1 with the repository disabled.
- The idempotent play run above is the check that the host now matches what the fleet automation expects.

## What remains

The two logcollector entries for Apache logs that do not exist are cosmetic and shared with the other Debian agents. The host's agent is on 4.14.6-1 like the rest of the fleet, so the "move `docker-main` off 4.14.0" item in the [Wazuh TODO](../TODO.md) is closed by this change, and the remaining version item is `edge-01` on 4.14.5-1.
