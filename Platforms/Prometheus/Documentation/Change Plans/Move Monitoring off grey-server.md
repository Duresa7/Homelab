# Move Monitoring off grey-server

**Created:** 2026-07-26  
**Last updated:** 2026-07-29

**Status:** Complete on 2026-07-26  
**Target:** CT 104 `monitor-01`, Debian 13 LXC on `blue-server`, VLAN 73 `MONITOR-A`, 192.168.73.2  
**Owner:** Prometheus infrastructure monitoring  
**Affected systems:** `security-01`, `blue-server`, UniFi gateway, Proxmox cluster firewall, all four Proxmox nodes, `ansible-01`, Nginx Proxy Manager, and the final 46-target scrape set

This replaces the first draft of this plan, written earlier on 2026-07-26 and wrong in four ways: it said VM rather than LXC, `purple-server` or `red-server` rather than `blue-server`, 6 GiB rather than 2 GiB, and six firewall rules rather than twenty-three. The design review that corrected it is summarised under [Decisions](#decisions).

## Read This First

You are executing this, not designing it. The decisions below are settled; do not re-litigate them mid-run.

**Secrets.** Two secrets are handled here: the Grafana admin credential and a new Proxmox API token. Neither value may appear in a command line, a log, a file in this repository, a commit, or anything you print. Read the credential-retrieval skill before touching either. Pipe values, never echo them.

**Proxmox shows an API token secret exactly once.** If you create the token and lose the value, you cannot retrieve it. Delete the token and create it again. Store it in the same step that creates it, before doing anything else.

**Stop conditions.** Stop, report, and change nothing further if any of these happen:

- A firewall change is refused or blocked. Both a UniFi policy edit and an `/etc/pve` write were blocked earlier on 2026-07-26 and needed explicit operator permission. Phases 1 and 2 are additive precisely so that a block here leaves the running stack untouched.
- `promtool check config` fails.
- Any target is not `up` at the end of Phase 6. Do not proceed to cutover with a broken target set.
- The Grafana credential rotation in Phase 5 does not verify.
- Anything in Phase 8 would delete `cadvisor`, `node_exporter`, or a Wazuh component.

**Order matters more than speed.** Phases 1 through 6 add things and change nothing. The commit point is Phase 7. Before it, rollback is deleting CT 104 and removing the rules you added. After it, rollback means restoring rules and rebuilding from git.

## Execution State, 2026-07-26

I passed Phase 0 with 44 of 44 targets up. `blue-server` still reported CTID 104 free, the Debian 13 template cached, & about 140 GB free on `local-lvm`.

I created `MONITOR-A` as VLAN 73 at 192.168.73.1/24. DHCP serves 192.168.73.6 through 192.168.73.254, leaving the static `monitor-01` address at 192.168.73.2 outside the pool. UPnP & mDNS remain disabled.

Phase 1 is complete. `AlphaSec`-Monitor contains only `MONITOR-A`, and the network's `firewall_zone_id` matches that zone. All 12 additive UniFi policies are enabled, taking the user-defined policy count from 52 to 64. `/etc/pve/firewall/cluster.fw` now has 55 lines, five IP sets, both terminal `IN DROP` rules, both PeaNUT rules, the four old 192.168.72.2 entries, & the four planned 192.168.73.2 additions. `pve-firewall compile` passed, and TCP 22 plus 8006 remained active on all four nodes.

Phase 2 is complete. `pve-exporter@pve!monitor01` exists with privilege separation enabled & `PVEAuditor` on `/`. I stored its one-time secret and token ID outside this repository, then removed both staging files.

Phase 3 is complete. CT 104 runs Debian 13 on `blue-server` with two cores, 2 GiB memory, 1 GiB swap, a 16 GiB disk, & static address 192.168.73.2. The Linux host baseline passed: both administrative accounts have their approved keys and recovery passwords, SSH is key-only, root is locked, the locale is `en_US.UTF-8`, the timezone is `America/New_York`, & no package upgrades remain. Docker 29.6.2 and Compose 5.3.1 run inside the unprivileged LXC, and the controller reached the `ansible` account with its restricted key.

The first DNS check exposed two missing network details. UniFi had automatically excluded `MONITOR-A` from the shared `Proxmox-Trunk` profile, so VLAN 73 could not reach the gateway. I added only `MONITOR-A` to that profile and verified its network ID disappeared from the excluded set. DNS still needed the anticipated `Allow Monitor DNS to Gateway` policy on TCP and UDP 53. After both fixes, the guest reached 192.168.73.1, resolved public names, & resolved `jellyfin.alphasecunited.com` to 192.168.85.2.

Phase 4 is complete. The Ansible project now holds eight hosts in both exporter groups. The node exporter play installed version 1.9.0 on `monitor-01`, and the cAdvisor play started version 0.60.5 on port 9101. Both endpoints return HTTP 200.

Phase 5 is complete. Six containers run from `/home/dkadi/monitoring`, and the deployed files contain the real domain and administrator name rather than repository placeholders. I created `pve.yml` as a mode 0600 untracked file, removed every secret staging file, and verified `pve_up 1` for the cluster and all four nodes. The current Grafana image uses `/usr/share/grafana/bin/grafana cli` rather than the plan's removed `grafana-cli` executable. I used that supported path to rotate the saved credential through stdin, renamed the stored credential for the new host, verified the `dkadi` login, and confirmed the default `admin:admin` login fails. `promtool check config` passed.

Phase 6 passed. All 15 node exporters and all eight cAdvisor endpoints return HTTP 200 from `monitor-01`; Proxmox answers on 8006; both NUT servers accept TCP 3493 and return live UPS metrics; and both local web interfaces answer. The direct `https://192.168.85.2/` check returns curl code `000` because NPM rejects a TLS handshake without an SNI hostname, not because TCP 443 is blocked. A TCP probe reaches 443, and `https://jellyfin.alphasecunited.com/` returns HTTP 302 through the same address. The exact target assertion reports 46 of 46 up with no stale addresses. All 65 dashboard queries pass, with only the allowed container restart table empty.

The Phase 6 NPM handoff is complete. The operator changed proxy-host ID 18 for Grafana to `192.168.73.2:3000` & ID 19 for Prometheus to `192.168.73.2:9090`. A read-only database query confirmed both saved values. Both HTTPS names return HTTP 302, & both direct replacement endpoints return HTTP 200 from `docker-network`.

Phase 7 is complete. I reran the assertion at the commit point and got 46 of 46 targets up, then stopped the old five-container Compose project on `security-01`. cAdvisor remained the only running Docker container there; `node_exporter`, `wazuh-manager`, `wazuh-indexer`, & `wazuh-dashboard` remained active. I enabled only `UNIFI_POLICY_NETWORK_FIREWALL_POLICIES_DELETE` for the UniFi MCP, previewed and deleted the six superseded policies one at a time, and narrowed `Allow NPM to security-01 web UIs` to port 443. Each structural diff showed only the intended change. I replaced the four old 192.168.72.2 `cluster.fw` entries with the four 192.168.73.2 entries, compiled the result, and verified the same final SHA256 on all four nodes.

Phase 8 is complete. I proved the removal scope before deleting anything, then removed only `/home/dkadi/monitoring`, its two named volumes, and the five retired monitoring images from `security-01`. cAdvisor still returns HTTP 200, `node_exporter` is active, and the three Wazuh services plus the Wazuh HTTPS route remain healthy. The plan's expected six non-empty cAdvisor names was wrong after the wipe: only `cadvisor` remains because the five retired containers no longer exist.

The live UniFi policy count started at 52, not the 43 recorded in the firewall inventory. Nine Kasm policies account for the difference. The 12 planned additive policies brought the live count to 64, the required DNS policy brought it to 65, and the six deletions left 59. Editing the NPM policy did not change the count. Phase 9 corrected the inventory and recorded the complete result in [Monitoring Relocation to monitor-01 - 2026-07-26](../Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

## Why

Prometheus and Grafana run on `security-01`, a VM on `grey-server`. So do `app-01`, `docker-main`, and `splunk-siem`. Measured 2026-07-26:

```
grey-server      16 cpu   45.6 / 62.7 GiB used
blue-server       4 cpu    2.6 / 11.6 GiB used
purple-server     6 cpu    1.8 / 15.5 GiB used
red-server        6 cpu    3.0 / 15.5 GiB used
```

If `grey-server` fails, monitoring fails with most of what it monitors, at the moment I would most want to look at it. Purple's boot NVMe failed on 2026-07-25 and monitoring was unaffected, because monitoring isn't on Purple. Grey is a different outcome.

Second reason: `security-01` uses 8 of 12 GiB and nearly all of it is Wazuh's indexer. Prometheus and Grafana are minor tenants on a VM dominated by a memory-hungry neighbour.

## Decisions

| # | Decision | Reason |
|---|---|---|
| 1 | Docker Compose, reusing `Configuration/` unchanged | Debian 13 ships Prometheus 2.53.3 against the 3.10.0 in use, and has no package for Grafana, `prometheus-nut-exporter`, or cAdvisor. Native would mean a major downgrade, a third-party repo, two hand-built binaries, and a rewritten runbook |
| 2 | CT 104 `monitor-01`, Debian 13, unprivileged, `nesting=1,keyctl=1` | Matches CT 107 `docker-network` exactly, which runs Docker on this node today |
| 3 | 2 cores, 2048 MB memory, 1024 MB swap, 16G on `local-lvm` | Measured footprint is 371 MB RSS across all six containers and 5.5 GB of disk. `pct resize` grows the disk in seconds if it ever needs to |
| 4 | New VLAN 73 `MONITOR-A`, 192.168.73.0/24, new custom zone `AlphaSec`-Monitor | Dedicated zone so the collector does not inherit Security-A's permissions. VLAN 73 is free since the 2026-07-23 lab simplification |
| 5 | `--nameserver 192.168.73.1` | Split-horizon DNS is gateway-wide, verified against both `.72.1` and `.80.1`. A public resolver returns NXDOMAIN for internal names and silently kills all 19 blackbox probes and nothing else |
| 6 | Inbound: NPM plus break-glass from Jedi PC | Daily access through the proxy with the wildcard certificate. The direct rule exists because NPM runs on `docker-network`, on this same node, and because you need browser access before NPM is re-pointed |
| 7 | Fresh TSDB, retention stays 15d | Graphs restart empty and heal by 2026-08-10. Retention unchanged so no documentation numbers move |
| 8 | Grafana: bootstrap default, rotate immediately with the supported Grafana CLI | The 2026-07-22 incident was a bootstrap value left in the Compose file. Nothing goes in Compose this time. Grafana 13 uses `/usr/share/grafana/bin/grafana cli`; the old `grafana-cli` executable is gone |
| 9 | New `pve-exporter@pve!monitor01`, PVEAuditor on `/` | The existing credential is `local-dash@pve!readonly`, shared with `homelab-dashboard-aio` on `docker-main`. Revoking it breaks that app |
| 10 | Agent performs all firewall changes | Operator decision. Phases are ordered so a block is survivable |
| 11 | Additive first, roughly an hour of overlap, then cutover | The overlap exists only to prove the new path |
| 12 | Full wipe of the monitoring stack on `security-01` | Everything on that host is either in git or deliberately replaced |

## Facts Already Verified, 2026-07-26

Do not re-derive these. They were checked during the design review.

| Fact | Value |
|---|---|
| Prometheus TSDB size | 1.7 GB at 39,944 head series, 15d retention |
| Total RSS, six containers | 371 MB: prometheus 166, grafana 99, pve-exporter 53, cadvisor 34, blackbox 19, nut 1 |
| Images on `security-01` | 8 images, 2.15 GB |
| `blue-server` free memory | 8 GiB available of 11.6 |
| `blue-server` storage | `local-lvm` lvmthin, 140 GB available of 148 |
| Debian 13 LXC template | Already cached: `local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst` |
| Next free cluster ID | 104 |
| VLAN 73 trunking | `vmbr0` is VLAN-aware with `bridge-vids 2-4094`. UniFi initially excluded the newly created network from `Proxmox-Trunk`; I added only `MONITOR-A` to the profile during execution |
| Proxmox guest firewall | No per-guest `.fw` files exist and there is no `host.fw` on blue. CT 107 receives 443 with no rule permitting it, so guest ingress is not filtered. `monitor-01` needs no `cluster.fw` work for its own inbound |
| Existing PVE identity | `local-dash@pve` token `readonly`, `privsep=1`, ACL `/` role `PVEAuditor` propagate=1 |
| Stored credentials | No stored copy exists for the PVE credential. `pve.yml` on `security-01` is its only copy |

## Firewall Scope

Twenty-three changes across two systems that enforce independently. On 2026-07-25 a correct UniFi policy for NUT sat in place for a day while the path stayed blocked, because `cluster.fw` dropped it separately. Verify from the source host after every rule, not at the end.

### Twelve new UniFi policies

All egress policies take source zone `AlphaSec`-Monitor, source `IP 192.168.73.2`.

| # | Name | Destination | Ports |
|---|---|---|---|
| 1 | Allow Monitor to Personal-A monitoring | `Internal`, IPs 192.168.40.35, .36, .39, .42 | 9100, 9101 |
| 2 | Allow Monitor to A-Servers monitoring | `Org-Servers`, IPs 192.168.80.10, .118 | 9100, 9101 |
| 3 | Allow Monitor to A-Access monitoring | `Org-Access`, IP 192.168.85.2 | 9100, 9101, 443 |
| 4 | Allow Monitor to A-Security monitoring | `Org-Security`, IPs 192.168.72.2, .72.3 | 9100, 9101 |
| 5 | Allow Monitor to DMZ monitoring | `Dmz`, IP 192.168.90.10 | 9100 |
| 6 | Allow Monitor to Proxmox monitoring | `Org-Mgmt`, IPs 192.168.70.10 to .13 | 9100, 8006 |
| 7 | Allow Monitor to Proxmox NUT | `Org-Mgmt`, IPs 192.168.70.10, .70.13 | 3493 |
| 8 | Allow Monitor Web Egress | `External` | 80, 443 |
| 9 | Allow Monitor NTP Egress | `External` | 123 |
| 10 | Allow NPM to monitor-01 web UIs | source `Org-Access` IP 192.168.85.2, dest IP 192.168.73.2 | 3000, 9090 |
| 11 | Allow Secure to monitor-01 break-glass | source `Internal` IP 192.168.50.241, dest IP 192.168.73.2 | 3000, 9090 |
| 12 | Allow Automation to monitor-01 SSH | source `Internal` IP 192.168.40.36, dest IP 192.168.73.2 | 22 |

Policy 4 is the one that catches people. `security-01` and `splunk-siem` are scraped from inside their own zone today, so no policy exists. It becomes cross-zone. Miss it and two hosts go down.

Policy 12 is needed because `ansible-01` is on VLAN 40 and installs `node_exporter` and cAdvisor over SSH.

Enable automatic respond-policy generation on policies 1 through 7 and 10 through 12, matching how the eight existing cross-zone monitoring allows were created. Policies 8 and 9 are egress-trio members: create them with `create_allow_respond=false` and index order 10000 then 10001, matching the Security-A and Access-A trios.

Order-of-operations note: create the network and the zone first, or the policies have nothing to reference.

### Seven changes to existing UniFi policies, Phase 7 only

| Policy | Action |
|---|---|
| Allow Security to Personal-A monitoring | Delete |
| Allow Security to A-Servers monitoring | Delete |
| Allow Security to A-Access monitoring | Delete |
| Allow Security to Proxmox monitoring | Delete |
| Allow Security to DMZ monitoring | Delete |
| Allow Security to Proxmox NUT | Delete |
| Allow NPM to security-01 web UIs | Edit: remove ports 3000 and 9090, keep 443 for the Wazuh dashboard |

**Do not touch `Allow Security Workloads Web Egress` or `Allow Security Workloads NTP Egress`.** Both list `192.168.72.2` and `192.168.72.3`. `security-01` still needs web and NTP egress for Wazuh updates and for pulling the cAdvisor image, and `splunk-siem` needs them regardless. Removing `.72.2` there would break a host you are not migrating.

### Four `cluster.fw` changes

The file lives on pmxcfs at `/etc/pve/firewall/cluster.fw` and replicates to all four nodes on its own. Build a candidate outside `/etc/pve`, check it before installing, then run `pve-firewall compile`. New accepts must sit above the trailing `IN DROP` entries.

Phase 1, additive:

```
[IPSET pve_svc_clients]
192.168.73.2 # monitor-01 (PVE exporter / Proxmox API)

[group pve_mgmt]
IN ACCEPT -source 192.168.73.2 -p tcp -dport 9100 -log nolog # monitor-01 Prometheus node_exporter
IN ACCEPT -source 192.168.73.2 -dest 192.168.70.10 -p tcp -dport 3493 -log nolog # monitor-01 NUT exporter to Grey NUT
IN ACCEPT -source 192.168.73.2 -dest 192.168.70.13 -p tcp -dport 3493 -log nolog # monitor-01 NUT exporter to Red NUT
```

Phase 7, removal: the matching four `192.168.72.2` entries, being the `pve_svc_clients` IPSET member and the three `IN ACCEPT` lines. Leave the two `192.168.40.35` PeaNUT rules alone.

The `pve_svc_clients` IPSET line is the one that will be missed. It is not in the `[RULES]` section and it is how the PVE exporter reaches 8006. Without it the Proxmox job dies and takes all 21 guests and 10 storages with it, while the UniFi side looks perfectly correct.

## Phase 0. Preflight

```bash
# On blue-server
pvesh get /cluster/nextid                      # expect 104; if not, use what it returns and note it
pveam list local | grep debian-13              # expect the cached trixie template
pvesm status | grep local-lvm                  # expect active with room
```

Confirm the current stack is healthy before changing anything, so a later failure is attributable:

```bash
# On security-01
curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 assert_targets.py
```

**Pass:** 44 targets, all `up`. If not, fix that first. Do not migrate a broken target set.

## Phase 1. Network, zone, and firewall

1. Create network `MONITOR-A`, VLAN 73, 192.168.73.0/24, gateway 192.168.73.1. Enable DHCP from 192.168.73.6 through 192.168.73.254. Keep `monitor-01` static at 192.168.73.2 in its LXC network configuration. Leave UPnP and IGMP snooping off.
2. Create custom zone `AlphaSec`-Monitor containing only `MONITOR-A`.
3. Create the twelve policies above.
4. Make the four additive `cluster.fw` changes. Verify the candidate before installing: line count, that both `IN DROP` entries survive, that all five IPSETs survive, and that the file still contains the two PeaNUT rules. Then `pve-firewall compile`.

**Pass:** `pve-firewall compile` succeeds on the node you edited from, SSH and GUI listeners stay up, and the twelve policies are enabled. Nothing is verifiable end to end yet because `monitor-01` does not exist. That is expected.

## Phase 2. Proxmox API token

Create a dedicated identity. Do not reuse or revoke `local-dash@pve!readonly`.

```bash
# On grey-server
pveum user add pve-exporter@pve --comment "Prometheus PVE exporter on monitor-01"
pveum acl modify / --users pve-exporter@pve --roles PVEAuditor
pveum user token add pve-exporter@pve monitor01 --privsep 1
pveum acl modify / --tokens 'pve-exporter@pve!monitor01' --roles PVEAuditor
```

The token value is printed once. Capture it and write it straight into the credential store, with the token ID `pve-exporter@pve!monitor01` in a separate field. Do not print it, do not put it in a file yet, do not paste it into a commit.

**Pass:** `pveum user token list pve-exporter@pve` shows `monitor01`, and `pvesh get /access/acl` shows `pve-exporter@pve!monitor01` with role `PVEAuditor` on `/`.

## Phase 3. Build the LXC

```bash
# On blue-server
pct create 104 local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst \
  --hostname monitor-01 \
  --cores 2 --memory 2048 --swap 1024 \
  --rootfs local-lvm:16 \
  --net0 name=eth0,bridge=vmbr0,tag=73,firewall=1,ip=192.168.73.2/24,gw=192.168.73.1 \
  --nameserver 192.168.73.1 \
  --unprivileged 1 \
  --features nesting=1,keyctl=1 \
  --ostype debian \
  --onboot 1 \
  --start 1
```

The `qm set --delete cicustom` trap does not apply here. That is a VM-clone problem with template 9000, and this is an LXC built from a distribution template.

Then apply the [Linux Host Baseline Standard](../../../../Security/Hardening/Linux-Host-Baseline-Standard.md) before the host carries a workload: admin user, keys installed, key-only SSH, root locked.

Install Docker from Docker's own repository, matching the other Docker hosts.

**Pass, and check DNS explicitly because it fails silently:**

```bash
# Inside monitor-01
getent hosts jellyfin.alphasecunited.com     # MUST return 192.168.85.2
cat /etc/resolv.conf                          # MUST show 192.168.73.1, not 1.1.1.1
docker run --rm hello-world                   # proves web egress and nesting
timedatectl | grep -i synchronized            # proves NTP egress
```

If the internal name does not resolve, stop. Every blackbox probe depends on it and nothing else will look wrong.

If `hello-world` cannot pull, policy 8 is wrong. If time is not synchronised, policy 9 is wrong. If DNS fails while the resolver is correct, you may need an `AlphaSec`-Monitor to `Gateway` allow on 53; that was not needed for existing zones, so treat it as a finding worth recording rather than an expected step.

## Phase 4. Exporters through Ansible

Edit the repository copies first, then deploy to the controller.

1. Add `monitor-01` at 192.168.73.2 to both `node_exporter_targets` and `cadvisor_targets` in [inventory/hosts.yml](../../../Ansible/Source/monitoring-exporters/inventory/hosts.yml).
2. Add it to `EXPECTED_NODE_EXPORTER_HOSTS`, `EXPECTED_CADVISOR_HOSTS`, and `EXPECTED_IPS` in [tests/validate_project.py](../../../Ansible/Source/monitoring-exporters/tests/validate_project.py). The validator is strict on purpose; it will fail until you do.
3. Upload all three changed files to `/home/ansible/monitoring-exporters/` and run:

```bash
cd /home/ansible/monitoring-exporters
export LANG=C.utf8 LC_ALL=C.utf8
python3 tests/validate_project.py
ansible-playbook playbooks/node-exporter.yml -e target=monitor-01
ansible-playbook playbooks/cadvisor.yml -e target=monitor-01
```

Debian 13 carries `prometheus-node-exporter` 1.9.0-1+b4, so this takes the APT path and matches the fleet version with no binary install.

**Pass:** validator reports 8 node_exporter hosts and 8 cAdvisor hosts. `node-exporter.yml` asserts the running version. `cadvisor.yml` reports `named_containers` equal to the number Docker says are running, and fails on a mismatch.

## Phase 5. Stand up the stack

1. Copy `Configuration/` from this repository to `/home/<admin>/monitoring/` on `monitor-01`: `docker-compose.yml`, `prometheus.yml`, `blackbox.yml`, and the whole `grafana/` tree.
2. Substitute `alphasecunited.com` and `dkadi` in the copies. The versioned files carry placeholders; the deployed ones cannot.
3. Create `pve.yml` with the new token, mode 0600, owner the admin user. Write it with a heredoc fed from the credential store; never echo the value. Confirm afterwards that `pve.yml` is not tracked by git and never will be.
4. `docker compose up -d`.
5. Rotate the Grafana credential immediately:

```bash
docker exec -i grafana grafana-cli admin reset-admin-password --password-from-stdin
```

Feed it from the credential store's existing Grafana administrator entry, then rename that entry for the new host. Do not add any admin password variable to the Compose file. That is exactly what caused the 2026-07-22 incident.

**Pass:** six containers running, `curl -fsS http://127.0.0.1:9090/-/ready`, `curl -fsS http://127.0.0.1:3000/api/health` reporting `"database": "ok"`, `docker exec prometheus promtool check config /etc/prometheus/prometheus.yml` clean, and an authenticated Grafana API call succeeding with the rotated credential while the default one fails.

## Phase 6. Verify before committing to anything

This is the gate. Everything so far is reversible by deleting CT 104.

Reachability from `monitor-01`, every path, before trusting Prometheus:

```bash
for h in 192.168.40.35 192.168.40.36 192.168.40.39 192.168.40.42 \
         192.168.80.10 192.168.80.118 192.168.85.2 \
         192.168.72.2 192.168.72.3 192.168.90.10 \
         192.168.70.10 192.168.70.11 192.168.70.12 192.168.70.13; do
  printf "%-16s 9100=%s 9101=%s\n" "$h" \
    "$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://$h:9100/metrics)" \
    "$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://$h:9101/metrics)"
done
curl -s -o /dev/null -w '8006=%{http_code}\n' -m 5 -k https://192.168.70.10:8006/
for n in 192.168.70.10 192.168.70.13; do nc -z -w 4 $n 3493 && echo "3493 open $n"; done
curl -s -o /dev/null -w '443 via NPM=%{http_code}\n' -m 8 -k https://192.168.85.2/
```

Expect 200 on 9100 for all fourteen, 200 on 9101 for the eight cAdvisor hosts, non-zero on 8006, both NUT ports open, and NPM answering. A `000` anywhere is a firewall problem; fix the rule before continuing.

Then update the scrape config and both assertions in this repository:

- `prometheus.yml`: add `192.168.73.2:9100` with `role: monitoring` to the `node` job, add `192.168.73.2:9101` to `cadvisor`, and change the self-scrape's `host` label from `security-01` to `monitor-01`. Everything else is unchanged.
- `Tests/assert_targets.py`: add both new URLs, change the self-scrape host label, and keep `security-01`'s existing `node` and `cadvisor` entries. Expected total becomes **46**.

Deploy per the [runbook](../Runbook.md) target-change procedure, then:

```bash
curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 assert_targets.py
python3 assert_dashboard_queries.py ~/monitoring/grafana/dashboards/homelab-overview.json
```

**Pass, and this is the hard gate:** 46 targets, all `up`, and 65 dashboard queries with at most the container restart table empty. Anything less and you stop here with the old stack still running.

Hand off to the operator for the NPM re-point. They own that step.

## Phase 7. Cutover

Only after Phase 6 passed.

1. On `security-01`: `docker compose -f ~/monitoring/docker-compose.yml down`. This stops five containers. It does **not** stop `cadvisor`, which belongs to a separate project at `/opt/docker/cadvisor`. Confirm `cadvisor` is still running afterwards.
2. Delete the six superseded UniFi policies and edit `Allow NPM to security-01 web UIs` down to port 443.
3. Remove the four `192.168.72.2` entries from `cluster.fw`, same candidate-then-verify method as Phase 1. Leave the two PeaNUT rules.
4. Re-run the target assertion from `monitor-01`. Still 46, still all up. `security-01` must still appear twice, as a `node` target and a `cadvisor` target.

**Pass:** 46 up from `monitor-01`, `cadvisor` and `node_exporter` alive on `security-01`, Wazuh untouched and still reachable at `https://wazuh.<domain>`.

## Phase 8. Wipe security-01

```bash
cd ~/monitoring
docker compose down                       # already done in Phase 7, harmless to confirm
docker volume rm monitoring_prometheus_data monitoring_grafana_data
cd ~ && rm -rf ~/monitoring
docker image rm prom/prometheus:latest grafana/grafana:latest \
  prompve/prometheus-pve-exporter:latest prom/blackbox-exporter:v0.27.0 \
  hon95/prometheus-nut-exporter:1
```

Remove images by name. **Never run `docker image prune -a` here**, because it would take `ghcr.io/google/cadvisor:v0.60.5` with it.

This deletes the seven `.bak` files, `backups/grafana.db.bak.fleet-metrics-expansion-20260725`, and `pve.yml`. All of it is either in git or deliberately replaced. The grafana.db tarball is the last copy of the two dashboards deleted on 2026-07-26; that was a deliberate choice, not an accident.

**Pass, verify explicitly rather than assuming:**

```bash
test ! -d ~/monitoring && echo "config gone"
docker volume ls | grep -c monitoring_          # expect 0
docker ps --format '{{.Names}}'                 # expect cadvisor plus the Wazuh set, nothing else from this stack
systemctl is-active node_exporter               # expect active
curl -fsS http://127.0.0.1:9100/metrics | head -1
curl -fsS http://127.0.0.1:9101/metrics | grep -c 'name="'   # expect 1 after the wipe: cadvisor itself
```

## Phase 9. Documentation

Same task, per `CLAUDE.md`. First person, no emoji, ISO dates, written through the `no-ai-slop` and `rossmann-voice` skills.

**New:** a change record at `Documentation/Change Records/Monitoring Relocation to monitor-01 - 2026-07-26.md`, or the real completion date. It must carry the twenty-three firewall changes, the DNS finding, the `pve_svc_clients` finding, and the measured before-and-after target counts.

**Update:**

| File | Change |
|---|---|
| [Prometheus README](../../README.md) | Host, address, 46 targets, `monitor-01` in the job table, containers-on section retitled |
| [Runbook](../Runbook.md) | Every `security-01` reference for the monitoring stack, the new 46 and the rollback section, which currently names `.bak` files that no longer exist. Rollback becomes rebuild-from-git |
| [Platform TODO](../TODO.md) | Close this item |
| [UniFi firewall inventory](../../../../Infrastructure/Network/UniFi/Configuration/firewall.md) | Correct the stale 43-policy inventory to the 52-policy starting state, then record 59 after thirteen additions and six deletions. Note the DNS finding and NPM policy edit |
| [UniFi VLAN inventory](../../../../Infrastructure/Network/UniFi/Configuration/network-vlan.md) | Add VLAN 73 `MONITOR-A`, and note that 73 was previously part of the seven-VLAN Kasm lab range retired on 2026-07-23 |
| [UniFi zone inventory](../../../../Infrastructure/Network/UniFi/Configuration/zone.md) | Add custom zone `AlphaSec`-Monitor |
| [Kasm Lab Network Simplification](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md) | One line: VLAN 73 was reused for `MONITOR-A` on 2026-07-26, so a later reader does not think the lab VLAN returned |
| [Galaxy Data Center Firewall](../../../../Infrastructure/Compute/Galaxy/Configuration/Datacenter-Firewall.md) | The IPSET member swap and the three rule changes |
| [Operations inventory](../../../../Operations/Inventory/Galaxy/) | CT 104 in the LXC inventory, `security-01`'s workload list in `Services.md`, the new exporter rows |
| [monitoring-exporters README](../../../Ansible/Source/monitoring-exporters/README.md) | 8 hosts in both groups |
| [Root TODO](../../../../TODO.md) | Move to Recently Completed |
| `Mission Control/index.html` | New project or a new step, then `node harness.js` must pass |

Do not move the retired lab-range records into `Archive/`. That was considered and rejected on 2026-07-26: the simplification change record is the only account of why VLAN 73 is free, and the 2026-07-22 firewall audit already carries a superseded banner. Reverse pointers, not relocation.

Commit in several small commits rather than one, matching the pattern used through 2026-07-26. No AI author, preparer, reviewer, or co-author trailer anywhere.

## Rollback

**Before Phase 7.** Nothing is broken. `pct stop 104 && pct destroy 104`, delete the thirteen new policies, remove `MONITOR-A` from the `Proxmox-Trunk` tagged set, remove the four additive `cluster.fw` entries, revert the repository changes to `prometheus.yml`, `assert_targets.py`, and the Ansible inventory. The old stack never stopped.

**After Phase 7, before Phase 8.** Re-create the six deleted UniFi policies and restore port 3000 and 9090 on the NPM policy, re-add the four `192.168.72.2` `cluster.fw` entries, then `docker compose up -d` on `security-01`. The volumes and configs are still there, so this is minutes.

**After Phase 8.** The old stack is gone. Rebuild it from `Configuration/` in this repository, which is the same procedure Phase 5 used, so it is proven rather than theoretical. The TSDB and `grafana.db` are unrecoverable, which is acceptable because the new stack started empty by design.

Keep a `cluster.fw` backup on the node during the change. On 2026-07-26 I removed the temporary backup and candidate files after I requested cleanup; rollback now uses the four entries documented above.
