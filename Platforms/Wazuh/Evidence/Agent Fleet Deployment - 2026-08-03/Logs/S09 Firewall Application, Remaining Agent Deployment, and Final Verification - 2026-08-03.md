# S09 Firewall Application, Remaining Agent Deployment, and Final Verification

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 07:59 through 13:52 EDT  
**Targets:** UniFi site `default`; `/home/ansible/wazuh-agent-deployment` on `ansible-01`; Wazuh manager `security-01`; internal Wazuh dashboard  
**Mechanism:** UniFi Network MCP, SSH Manager MCP, Ansible Core 2.21.2, Wazuh CLI, & in-app browser

## Firewall application

I created one policy at a time. Each cycle used a complete pre-change snapshot, the previously approved preview, `confirm=true`, a complete post-change snapshot, a key-aware policy diff, & source-host TCP tests.

| Policy | Policy ID | Pre-change snapshot | Diff & source test |
|---|---|---|---|
| `Allow monitor-01 to Wazuh - Security-A` | `6a7082b7e0ee2d5b4b149c26` | `firewall_20260803T115927Z.json` | One policy added; no removal or edit; 1514 & 1515 open |
| `Allow docker-network to Wazuh - Security-A` | `6a7082eee0ee2d5b4b149cc5` | `firewall_20260803T120028Z.json` | One policy added; no removal or edit; 1514 & 1515 open |
| `Allow kasm-01 to Wazuh - Security-A` | `6a708320e0ee2d5b4b149d1e` | `firewall_20260803T120120Z.json` | One policy added; no removal or edit; first 1514 test blocked |
| `Allow Galaxy nodes to Wazuh - Security-A` | `6a70d24fe0ee2d5b4b154510` | `firewall_20260803T173904Z.json` | One policy added; no removal or edit; both ports open from four nodes |

The snapshots live under `C:/Users/dures/.local/state/unifi-mcp/skills/firewall-snapshots/`. The matching post-change snapshots are `firewall_20260803T120002Z.json`, `firewall_20260803T120056Z.json`, `firewall_20260803T120145Z.json`, & `firewall_20260803T173937Z.json`.

The new `kasm-01` allow received index 10001 behind `LABMGMT Block to AlphaSec-Observability` at index 10000. I stopped before the Galaxy mutation. The ordering preview preserved both integration-policy UUIDs and swapped only their positions:

```text
beforeSystemDefined before:
19d7dbd2-f36a-4598-81c8-c85b2ecf6548
a9fa1289-c005-4d87-9241-ea9b82b4456a

beforeSystemDefined after:
a9fa1289-c005-4d87-9241-ea9b82b4456a
19d7dbd2-f36a-4598-81c8-c85b2ecf6548
```

The reorder used pre-change `firewall_20260803T173806Z.json` & post-change `firewall_20260803T173833Z.json`. The structural diff showed no added or removed policy. It changed only the two intended indexes: the exact `kasm-01` allow moved to 10000, & the catch-all block moved to 10001. Both ports then opened from `kasm-01`.

The final source checks returned:

```text
monitor-01       1514 open  1515 open
docker-network   1514 open  1515 open
kasm-01          1514 open  1515 open
grey-server      1514 open  1515 open
purple-server    1514 open  1515 open
blue-server      1514 open  1515 open
red-server       1514 open  1515 open
```

Green `192.168.70.14` isn't present in the Galaxy policy.

## Remaining agent deployment

I ran the bounded seven-host play:

```bash
cd /home/ansible/wazuh-agent-deployment && ansible-playbook playbooks/deploy.yml --limit 'monitor-01:docker-network:kasm-01:grey-server:purple-server:blue-server:red-server'
```

The first serial batch installed & enrolled `monitor-01`, `docker-network`, & `kasm-01`, then failed the immediate `service_facts` state assertion:

```text
monitor-01      ok=20 changed=9 unreachable=0 failed=1
docker-network  ok=20 changed=9 unreachable=0 failed=1
kasm-01         ok=20 changed=8 unreachable=0 failed=1
```

SSH Manager reported all three units running less than one minute later. I replaced the immediate state assertion with a 12-attempt, five-second `systemctl is-active wazuh-agent` poll, uploaded SHA-256 `8459a74cc11342bc975455c0b4e485b77311a8675d4386c270057cf910d5dc56`, & passed `ansible-playbook --syntax-check`.

The three-host rerun changed nothing:

```text
docker-network  ok=15 changed=0 unreachable=0 failed=0 skipped=7
kasm-01         ok=15 changed=0 unreachable=0 failed=0 skipped=7
monitor-01      ok=15 changed=0 unreachable=0 failed=0 skipped=7
```

The four-node command completed after Grey, Purple, & Blue ran as the first serial batch and Red ran as the second:

```bash
ansible-playbook playbooks/deploy.yml --limit 'grey-server:purple-server:blue-server:red-server'
```

```text
blue-server    ok=22 changed=9 unreachable=0 failed=0
grey-server    ok=22 changed=9 unreachable=0 failed=0
purple-server  ok=22 changed=9 unreachable=0 failed=0
red-server     ok=22 changed=9 unreachable=0 failed=0
```

Grey, Purple, Blue, & Red needed service-poll retries before `systemctl is-active` returned `active`. The final seven-host idempotency command exited `0`; every host reported `changed=0`, `failed=0`, & `unreachable=0`.

## Manager and group verification

`agent_control -l` returned all 13 remote agents active:

```text
004 app-01          Active
005 edge-01         Active
006 alpha-prod-01   Active
007 docker-blue     Active
008 media-01        Active
009 ansible-01      Active
010 monitor-01      Active
011 docker-network  Active
012 kasm-01         Active
013 grey-server     Active
014 purple-server   Active
015 blue-server     Active
016 red-server      Active
```

`agent_groups -l -g proxmox` returned exactly four agents: IDs 013, 014, 015, & 016. Four separate `agent_groups -s -i <ID>` checks returned `default, proxmox` for Grey, Purple, Blue, & Red.

## Dashboard verification

I signed into the internal dashboard as `dkadi`. The password wasn't printed, retained in this record, or left in a temporary file.

The Endpoints page reported:

```text
Active: 13
Disconnected: 0
Pending: 0
Never connected: 0
default: 13
proxmox: 4
edge: 1
```

Page 1 showed IDs 004 through 013. Page 2 showed IDs 014 through 016. Filtering on `proxmox (4)` returned Grey, Purple, Blue, & Red as active version 4.14.6 members of `default` & `proxmox`. The page-rendered screenshots contain no mouse cursor.
