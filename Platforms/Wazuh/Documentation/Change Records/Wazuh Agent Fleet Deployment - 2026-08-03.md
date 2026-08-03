# Wazuh Agent Fleet Deployment

**Created:** 2026-08-03  
**Last updated:** 2026-08-03  
**Change date:** 2026-08-03  
**Status:** Complete

## Scope

I added host-level Wazuh agents to `monitor-01`, `docker-network`, `docker-blue`, `alpha-prod-01`, `kasm-01`, `media-01`, `ansible-01`, `grey-server`, `purple-server`, `blue-server`, `red-server`, & `green-server`. I first scoped four Proxmox nodes, then added Green after the four-node deployment passed.

I also added missing SSH Manager records for `docker_blue`, `media_01`, `kasm_01`, & `green_server` in Codex. Claude already had the first three; I added Green to both managers. This record doesn't contain the private-key material referenced by either local manager.

## Starting State

- `security-01` ran manager, indexer, & dashboard package `4.14.6-1`; all three units were enabled and active.
- TCP 443, 1514, 1515, & 55000 listened on the expected addresses.
- `app-01` ID 004 & `edge-01` ID 005 were active. No requested target name had a stale manager identity.
- Four requested hosts could reach TCP 1514/1515. Seven timed out on both ports.
- The Wazuh `default` agent group monitored `/var/lib/docker/volumes/wordpress_wp_data/_data`, a path absent on every intended host I checked. IDs 004 & 005 both belonged to `edge`, although only ID 005 had `/etc/cloudflared`.

## Decisions

I pinned the new agents to `4.14.6-1` because the manager is `4.14.6-1`. The play disables the Wazuh APT source after installation & holds the package, so an unattended repository update can't move an agent ahead of the manager.

I stopped each host before package installation when either manager port failed. A running service with no enrollment path isn't a deployment result.

The live Galaxy cluster has five nodes. I first kept the requested hypervisor scope at Grey, Purple, Blue, & Red. After those four passed, I added Green to the same change. All five now share `default,proxmox`.

The existing LAB-MGMT catch-all block evaluated before the new `kasm-01` allow. I moved only those two policies within their LAB-MGMT-to-Observability pair, then proved TCP 1514 & 1515 from `kasm-01` before touching the Galaxy policy.

## Walkthrough

### Step 1: Verify the manager and every endpoint path

**Action:** I checked the live manager package, units, listeners, daemons, registrations, target packages, privilege paths, & TCP 1514/1515 reachability.

**Observed result:** The manager was healthy with only IDs 004 & 005 active. The seven blocked paths were `monitor-01`, `docker-network`, `kasm-01`, and the four requested Proxmox nodes.

**Verification:** Direct TCP probes returned `0` on the four reachable hosts and `124` on both ports for the seven blocked hosts.

**Evidence:** [S01 Live Preflight and Manager State](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S01%20Live%20Preflight%20and%20Manager%20State%20-%202026-08-03.md)

### Step 2: Register the missing SSH Manager hosts

**Action:** I added `docker_blue`, `media_01`, & `kasm_01` to Codex's TOML configuration. I verified Claude's `.env` already had one record for each & corrected its media host description from VM to LXC.

**Observed result:** Codex reloaded all three records without an MCP restart.

**Verification:** SSH Manager listed the three exact IPs & completed the read-only preflight on each.

**Evidence:** [S02 SSH Manager Registration](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S02%20SSH%20Manager%20Registration%20-%202026-08-03.md)

### Step 3: Build and run the bounded Ansible deployment

**Action:** I created `Platforms/Wazuh/Source/agent-deployment`, deployed it to `/home/ansible/wazuh-agent-deployment`, passed `ansible-playbook --syntax-check`, & limited the first live run to the four reachable hosts.

**Observed result:** The first run stopped before package installation because `dpkg_selections` can't clear a hold for a package APT hasn't indexed. I removed the unnecessary task and reran the same limit; all four hosts installed, enrolled, held, & started `4.14.6-1`.

**Verification:** The corrected run exited `0`. The later idempotency run returned `changed=0`, `failed=0`, & `unreachable=0` on all four hosts.

**Evidence:** [S03 Reachable Host Deployment](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S03%20Reachable%20Host%20Deployment%20-%202026-08-03.md) & [package-hold troubleshooting record](../Troubleshooting/Package%20hold%20task%20failed%20before%20Wazuh%20agent%20installation%20-%202026-08-03.md)

### Step 4: Verify active identities and close the first-check-in race

**Action:** I checked the package, hold, enabled state, running state, local key, established session, & manager identity for all four deployed endpoints.

**Observed result:** IDs 006 through 008 were active immediately. ID 009 `ansible-01` first showed `Never connected`, then established its session 20 seconds after enrollment and became active without a repair.

**Verification:** I added a persistent TCP 1514 session wait to the play. Its second run changed zero hosts and passed every assertion.

**Evidence:** [S04 Active Agent and Idempotency Check](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S04%20Active%20Agent%20and%20Idempotency%20Check%20-%202026-08-03.md) & [first-check-in troubleshooting record](../Troubleshooting/Fresh%20edge-01%20identity%20initially%20showed%20never%20connected%20-%202026-07-13.md)

### Step 5: Correct the shared agent policies

**Action:** I replaced the stale default-group WordPress path with real-time `/etc/ssh` & `/etc/cron.d` coverage. I reduced `edge/agent.conf` to `/etc/cloudflared` and removed ID 004 from that group.

**Observed result:** Both fragments passed `verify-agent-conf`. The default group now covers generic Linux configuration paths, while only ID 005 receives the Cloudflare tunnel path.

**Verification:** Wazuh rebuilt `merged.mg`. The exact old WordPress volume path has zero matches under `/var/ossec/etc/shared`; all six agents remained active with established TCP 1514 sessions.

I checked Docker state on the active workload hosts as a separate removal check. No WordPress container, image, volume, or Compose project existed, so the stale shared policy and its rollback copy were the only WordPress-specific resources removed.

**Evidence:** [S05 Shared Agent Policy Correction](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S05%20Shared%20Agent%20Policy%20Correction%20-%202026-08-03.md)

### Step 6: Preview the blocked UniFi paths

**Action:** I captured the complete firewall state, then previewed four exact ALLOW policies with `confirm=false`.

**Observed result:** Each preview limits the source to one requested host or the four requested node IPs, the destination to `192.168.72.2`, & the ports to the existing `Wazuh Ports` object containing TCP 1514 and 1515.

**Verification:** All four previews returned `success=true` and `requires_confirmation=true`. No UniFi state changed.

**Evidence:** [S06 UniFi Wazuh Policy Previews](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S06%20UniFi%20Wazuh%20Policy%20Previews%20-%202026-08-03.md)

### Step 7: Give dkadi complete administrator access

**Action:** I compared `dkadi` with the default administrator across both authorization layers. The internal indexer user already carried backend role `admin`, which maps to `all_access`, but no Wazuh server RBAC rule matched `dkadi`. I backed up `rbac.db`, created rule ID 100 `wui_dkadi_admin`, & linked it to role ID 1 `administrator` through the Wazuh API.

**Observed result:** The administrator role now carries rules 1, 2, & 100. I didn't change the internal user's password, backend role, or indexer mapping.

**Verification:** A fresh `dkadi` authorization context resolved to `administrator`, exposed all 23 administrator policies, & returned HTTP `200` from the security configuration endpoint. Manager, indexer, & dashboard services remained healthy.

**Evidence:** [S07 dkadi Administrator Access](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S07%20dkadi%20Administrator%20Access%20-%202026-08-03.md)

### Step 8: Verify the dashboard and prepare the Proxmox group

**Action:** I signed into the internal dashboard as `dkadi` through the Codex in-app browser, opened the active endpoint table, & opened agent group management. I created manager group `proxmox` through `agent_groups` and set Grey, Purple, Blue, & Red to enroll into `default,proxmox` in the versioned Ansible inventory.

**Observed result:** The dashboard showed six active agents, zero disconnected, zero pending, & zero never connected. Its Groups page showed `default` with six agents, `edge` with one, & `proxmox` with zero.

**Verification:** The endpoint table named IDs 004 through 009 and matched their live addresses, versions, statuses, & current groups. The generated Proxmox group configuration passed `verify-agent-conf`. The updated playbook passed syntax check and still listed exactly eleven targets.

**Evidence:** [S08 Dashboard and Proxmox Group Verification](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S08%20Dashboard%20and%20Proxmox%20Group%20Verification%20-%202026-08-03.md)

### Step 9: Apply the approved paths and finish the fleet

**Action:** I applied each UniFi policy separately, captured before-and-after firewall snapshots, read the structural diff, & tested TCP 1514/1515 from its exact source. I moved the `kasm-01` allow ahead of the existing LAB-MGMT catch-all block after the first source test failed. I then deployed the remaining seven agents through `/home/ansible/wazuh-agent-deployment`.

**Observed result:** The four policy creates added IDs `6a7082b7e0ee2d5b4b149c26`, `6a7082eee0ee2d5b4b149cc5`, `6a708320e0ee2d5b4b149d1e`, & `6a70d24fe0ee2d5b4b154510`. The first three-host deployment exposed a service-readiness race: the event socket existed before `service_facts` reported the unit running. I added an explicit `systemctl is-active wazuh-agent` poll. Grey, Purple, Blue, & Red each required two service-poll retries before reporting `active`, which reproduced the timing boundary and verified the correction.

**Verification:** The final seven-host Ansible run exited `0` with `changed=0`, `failed=0`, & `unreachable=0`. Manager IDs 010 through 016 were active. `agent_groups` returned exactly four `proxmox` members, and each belonged to `default,proxmox`. The in-app dashboard reported 13 active agents, zero disconnected, zero pending, zero never connected, & `proxmox (4)` while signed in as `dkadi`.

**Evidence:** [S09 Firewall Application, Remaining Agent Deployment, and Final Verification](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S09%20Firewall%20Application%2C%20Remaining%20Agent%20Deployment%2C%20and%20Final%20Verification%20-%202026-08-03.md), [service-readiness troubleshooting record](../Troubleshooting/Immediate%20service%20fact%20assertion%20raced%20Wazuh%20agent%20startup%20-%202026-08-03.md), [endpoint page 1](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S09%20Wazuh%20Endpoints%20Page%201%20-%202026-08-03.png), [endpoint page 2](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S09%20Wazuh%20Endpoints%20Page%202%20-%202026-08-03.png), & [Proxmox group](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S09%20Wazuh%20Proxmox%20Group%20-%202026-08-03.png). The screenshots were captured through the page renderer and contain no mouse cursor.

### Step 10: Add Green to the completed fleet

**Action:** After I added Green to scope, I previewed and applied one update to the existing Galaxy Wazuh policy. The update added only `192.168.70.14` to its source list. I added `green_server` to both SSH managers, added `green-server` to the Ansible inventory with `default,proxmox`, & ran the bounded deployment.

**Observed result:** Green reached TCP 1514/1515, installed held agent `4.14.6-1`, enrolled as ID `017`, started, & established its event session. Its first play returned `ok=22`, `changed=9`, & `failed=0`.

**Verification:** The second Green run returned `changed=0`. The dashboard reported 14 active agents, zero disconnected, zero pending, zero never connected, & `proxmox (5)`. The filtered view showed Grey, Purple, Blue, Red, & Green active in `default` & `proxmox`.

**Evidence:** [S10 Green Node Enrollment and Final Fleet Verification](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Logs/S10%20Green%20Node%20Enrollment%20and%20Final%20Fleet%20Verification%20-%202026-08-03.md), [endpoint page 1](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S10%20Wazuh%20Endpoints%20Page%201%20with%20Green%20-%202026-08-03.png), [endpoint page 2](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S10%20Wazuh%20Endpoints%20Page%202%20with%20Green%20-%202026-08-03.png), & [five-node Proxmox group](../../Evidence/Wazuh%20Agent%20Fleet%20Deployment%20-%202026-08-03/Screenshots/S10%20Wazuh%20Proxmox%20Group%20with%20Green%20-%202026-08-03.png). The screenshots were captured through the page renderer and contain no mouse cursor.

## Resulting Configuration

| Host | Manager ID | Agent | State |
|---|---:|---:|---|
| `app-01` | 004 | 4.14.6-1 | active; existing |
| `edge-01` | 005 | 4.14.5-1 | active; existing |
| `alpha-prod-01` | 006 | 4.14.6-1 | active; held |
| `docker-blue` | 007 | 4.14.6-1 | active; held |
| `media-01` | 008 | 4.14.6-1 | active; held |
| `ansible-01` | 009 | 4.14.6-1 | active; held |
| `monitor-01` | 010 | 4.14.6-1 | active; held |
| `docker-network` | 011 | 4.14.6-1 | active; held |
| `kasm-01` | 012 | 4.14.6-1 | active; held |
| `grey-server` | 013 | 4.14.6-1 | active; held; `default,proxmox` |
| `purple-server` | 014 | 4.14.6-1 | active; held; `default,proxmox` |
| `blue-server` | 015 | 4.14.6-1 | active; held; `default,proxmox` |
| `red-server` | 016 | 4.14.6-1 | active; held; `default,proxmox` |
| `green-server` | 017 | 4.14.6-1 | active; held; `default,proxmox` |

The manager has 14 active remote agents. IDs 006 through 017 run held package `4.14.6-1`; ID 004 runs `4.14.6-1`, and ID 005 remains on `4.14.5-1`.

`dkadi` has indexer `all_access` through backend role `admin` and Wazuh server role `administrator` through mapping rule ID 100.

The manager's `proxmox` group contains IDs 013 through 017. All five retain the common `default` policy and gain the shared Proxmox identity.

## Rollback

- The twelve new endpoints can be stopped, disabled, purged, & removed from the manager by exact ID 006 through 017. `/var/ossec` must be resolved and confirmed as a local directory before removing retained client state.
- The previous edge group configuration remains at `/var/ossec/etc/shared/edge/agent.conf.pre-fleet-20260803T0648Z` on `security-01`. The previous default file contained an unused WordPress path; I deleted that rollback copy at the owner's direction. The versioned [default agent configuration](../../Configuration/Agent%20Groups/default-agent.conf) is the current recovery source.
- Each created firewall rule has a pre-change snapshot. The Galaxy create uses `C:/Users/dures/.local/state/unifi-mcp/skills/firewall-snapshots/firewall_20260803T173904Z.json`; the `kasm-01` ordering rollback uses `firewall_20260803T173806Z.json`. A Green-only rollback removes `192.168.70.14` from policy ID `6a70d24fe0ee2d5b4b154510`. A complete rollback removes policy IDs `6a7082b7e0ee2d5b4b149c26`, `6a7082eee0ee2d5b4b149cc5`, `6a708320e0ee2d5b4b149d1e`, & `6a70d24fe0ee2d5b4b154510`, then restores the LAB-MGMT pair ordering from the pre-reorder snapshot.
- The narrow `dkadi` access rollback is to unlink and delete Wazuh server rule ID 100. The emergency database backup is `/var/ossec/api/configuration/security/rbac.db.pre-dkadi-admin-20260803T114102Z`.

## Remaining Work

1. Decide whether `edge-01` should receive the Wazuh APT repository or remain on deliberate manual upgrades.
