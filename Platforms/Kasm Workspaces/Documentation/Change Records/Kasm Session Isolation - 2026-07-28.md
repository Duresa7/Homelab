# Kasm Session Isolation

**Created:** 2026-07-28  
**Last updated:** 2026-07-31

**Implemented:** 2026-07-28  
**Owner:** Platforms / Kasm Workspaces  
**Status:** Implemented and fully accepted

## Result

I moved `kasm-01` (VM 122) from `grey-server` to `purple-server`, placed its control plane on LAB-MGMT VLAN 78 at `192.168.78.10`, and attached three session-only NICs for VLANs 74, 77, and 79. Docker macvlan networks now place disposable sessions directly in the selected UniFi zone.

The containment matrix passed with harmless test containers. VLAN 74 reaches the Internet through Proton and can initiate toward VLAN 77. VLANs 77 and 79 have no Internet or working resolver. The three session lanes cannot reach LAB-MGMT, the trusted LAN, Proxmox management, cluster networking, application servers, access services, observability services, or the gateway UI.

I did not create a VM snapshot or `vzdump` archive for this implementation. I chose a direct migration with no backup step. That decision covers this change only; the standing rule is still to snapshot before a malware session and roll back afterwards.

## Final Layout

| Layer | Final state |
| --- | --- |
| Proxmox node | `purple-server` |
| Guest storage | 150 GiB `scsi0` on `ssd-lvm2`, LVM-thin on Purple `/dev/sda` |
| Kasm control plane | LAB-MGMT VLAN 78, `192.168.78.10/24`, gateway `192.168.78.1` |
| Session lane 74 | `lab74`, `192.168.74.208/28`, parent `enp6s19` |
| Session lane 77 | `lab77`, `192.168.77.208/28`, parent `enp6s20` |
| Session lane 79 | `lab79`, `192.168.79.208/28`, parent `enp6s21` |
| Kasm version | 1.19.0 Community Edition |
| Session policy | `Lab Sessions` group, one-hour limit, upload enabled, download and clipboard disabled, no persistent profile |

VM 122 has four VirtIO NICs:

| NIC | VLAN | MAC | Proxmox firewall |
| --- | ---: | --- | --- |
| `net0` | 78 | `<REDACTED_KASM_HOST_MAC>` | enabled |
| `net1` | 74 | `<REDACTED_KASM_LANE_74_MAC>` | disabled |
| `net2` | 77 | `<REDACTED_KASM_LANE_77_MAC>` | disabled |
| `net3` | 79 | `<REDACTED_KASM_LANE_79_MAC>` | disabled |

I disabled the Proxmox firewall on the three macvlan parents because each session container uses its own MAC address. Enabling it would make the bridge filter discard valid session traffic.

## Step-Based Walkthrough

### Step 0: Create the Purple pool and migrate VM 122

I verified `/dev/sda`, created `ssd-lvm2`, restricted it to Purple, shut down VM 122, and ran the offline migration. The exact creation and migration commands are retained in the Storage and Migration section below. I did not retain the full action transcript. The observed migration ran for 15 minutes 25 seconds at an average of 117 MB/s.

I verified the final node, disk volumes, quorum, snapshot list, pool use, and SMART counters with [S00 Compute and Storage Final Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S00%20Compute%20and%20Storage%20Final%20Verification%20-%202026-07-28.md). I retained the exact [Proxmox storage stanza](../../../../Infrastructure/Compute/Galaxy/Configuration/Storage/ssd-lvm2.storage.cfg) and the unchanged [SMART capture](../../../../Infrastructure/Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt).

### Step 1: Move the control plane to LAB-MGMT

I created LAB-MGMT VLAN 78 and its custom zone, removed LAB-MGMT from the Proxmox trunk exclusion list, and changed VM 122 to `192.168.78.10/24`. The controller mutation payloads and guest file-write transcript were not retained. Tagged ARP initially failed because UniFi auto-excluded the new network. Removing only LAB-MGMT from that exclusion list fixed the path.

I verified the final network, DHCP state, critical management allow and catchall block order, and the five remaining trunk exclusions with [S01 UniFi Final State Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S01%20UniFi%20Final%20State%20Verification%20-%202026-07-28.md). S00 verifies VM 122's VLAN 78 NIC and static address.

### Step 2: Attach the session lanes

I attached VLAN NICs 74, 77, and 79, configured addressless guest parents, created the three Docker macvlan networks, and installed the persistent shim service. The configuration write transcript was not retained.

I rebooted the guest and verified the service enablement, parent NICs, shim addresses and routes, Docker networks, service containers, image set, and health endpoint with [S02 Guest and Kasm Final Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S02%20Guest%20and%20Kasm%20Final%20Verification%20-%202026-07-28.md).

### Step 3: Install and order the firewall matrix

I added the 38 LAB-MGMT and Kasm policies described below. The individual creation payloads were not retained. I verified the final policy count, critical definitions, narrow-allow order, stateful reverse block, and allowed and denied source paths with [S03 Firewall and Source-Path Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S03%20Firewall%20and%20Source-Path%20Verification%20-%202026-07-28.md). I then proved the lane matrix and every protected target from each session lane with [S06 Containment and Cleanup Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S06%20Containment%20and%20Cleanup%20Verification%20-%202026-07-28.md).

### Step 4: Correct DNS and verify Proton

I disabled VLAN 77's stale DHCP DNS option. I configured the KASM-BROWSER traffic route to use Proton with the kill switch enabled. The exact controller mutation payloads and first failure-injection transcript were not retained.

[S04 DNS and Proton Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S04%20DNS%20and%20Proton%20Verification%20-%202026-07-28.md) maps the current DHCP option, route target, kill switch, enabled Proton client, lane DNS, hostname egress, direct-IP egress, and failure test to the retained S01 and S06 transcripts. During implementation I replaced the enabled VPN's endpoint with `192.0.2.1:51820`; VLAN 74 lost Internet, the Kasm host kept ordinary WAN, and service returned after I restored the production endpoint.

### Step 5: Apply the Kasm session policy

I created `Lab Sessions`, assigned one administrator member, and set the seven required values. The mutation request was not retained. I verified the group, description, priority, member count, and values directly from the Kasm database with [S05 Lab Sessions Policy Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S05%20Lab%20Sessions%20Policy%20Verification%20-%202026-07-28.md).

### Step 6: Run acceptance and remove residue

I ran the harmless containment matrix, source-zone checks, Proton failure test, host pull test, and service checks. The initial Proton failure transcript was not retained. The exact final lane matrix is in S06. The host pull, host protected-target matrix, direct-IP egress checks, and cleanup are in [S06 Host and Direct-IP Acceptance Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S06%20Host%20and%20Direct-IP%20Acceptance%20Verification%20-%202026-07-28.md). S03 retains the final Personal-A and Trusted allows plus five denied source paths.

I removed all temporary containers, test images, temporary interfaces, test firewall policies, and temporary trunk admission. An independent review found eight older dangling Kasm image IDs. I pruned them, reclaimed 4.373 GB, then reran S02 and S06. The final state is eight service containers, eight tagged images, zero dangling images, no test container, and no lab-network endpoint.

### Step 7: Update records and local access

I updated the architecture, platform records, UniFi inventories, Galaxy storage configuration, complete dated guest inventories, TODOs, Mission Control, the stored dashboard URLs, and Jedi PC's SSH alias. [S07 Documentation and Local Access Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S07%20Documentation%20and%20Local%20Access%20Verification%20-%202026-07-28.md) retains the 1,080-check Mission Control pass, resolved SSH alias, 192 valid local links, and the reason I did not retain secret-store or authentication output.

### Step 8: Verify the 150 GiB disk expansion

I found VM 122's `scsi0` disk already expanded from 100 GiB to 150 GiB. The guest had also grown `/dev/sda1` to 149 GiB and its ext4 filesystem to 145 GiB, so I did not run `growpart`, `parted`, or `resize2fs`.

Kasm uses `/opt/kasm` and Docker uses `/var/lib/docker`; both resolve to `/dev/sda1`. The filesystem reported about 42 GiB available during verification. All eight Kasm containers were running, seven reported healthy as designed, and `/api/__healthcheck` returned `{"ok": true}`. I retained the exact checks in [S08 Kasm Disk Expansion Verification](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/S08%20Kasm%20Disk%20Expansion%20Verification%20-%202026-07-28.md).

## Storage and Migration

Before writing to the Samsung 850 EVO, I confirmed `/dev/sda` contained only GPT and PMBR signatures. SMART reported `PASSED`, zero reallocated sectors, zero CRC errors, zero uncorrectable errors, and `Wear_Leveling_Count` normalized 15 with raw value 1800.

I created `ssd-lvm2` with:

```text
pvesh create /nodes/purple-server/disks/lvmthin --name ssd-lvm2 --device /dev/sda --add_storage 1
pvesm set ssd-lvm2 --nodes purple-server --content images,rootdir
```

I shut down VM 122 and migrated it offline:

```text
qm migrate 122 purple-server --targetstorage ssd-lvm2
```

The migration completed in 15 minutes 25 seconds at an observed average of 117 MB/s. The VM's EFI, cloud-init, and 100 GiB root disks now reside on `ssd-lvm2`. Grey holds no VM 122 logical volume, and `hddpool-1` holds no backup archive.

Immediately after the migration, `ssd-lvm2` reported 239,185,920 KiB total and 26,382,206 KiB allocated, or 11.03 percent. The final evidence pass reported 26,501,799 KiB allocated, or 11.08 percent. The VM root thin volume reported 25.16 percent data use. SMART remained `PASSED`; the wear indicator was normalized 15 with raw value 1801, power-on hours rose from 45,241 to 45,242, and the three error counters remained zero.

## UniFi Changes

I created LAB-MGMT with VLAN 78, subnet `192.168.78.0/24`, gateway `192.168.78.1`, DHCP disabled, and UPnP disabled. I created the LAB-MGMT custom zone and verified that the network reads back with that zone assignment.

UniFi initially excluded every new network from the existing `Proxmox-Trunk` port profile. Tagged ARP requests left Purple but received no reply. I removed only LAB-MGMT from that exclusion list. The final exclusion set is Management, IoT, DMZ, Secure, and Trusted. VLANs 74, 77, 78, and 79 are admitted to Purple.

I retained the nine existing KASM baseline rules and added 38 policies for the control plane, lane separation, production containment, and outbound image pulls. The important ordering and state choices are:

- Trusted, Personal-A, and Management Access VPN may reach `192.168.78.10` on TCP 22 and 443. Catchall Internal and VPN blocks follow those narrow allows.
- LAB-MGMT may reach External for DNS and Kasm image pulls, but it cannot initiate toward Internal, the custom service zones, the gateway, or any session lane.
- KASM-BROWSER may initiate toward MALWARE-OFFLINE. The reverse block matches `NEW` and `INVALID` so return traffic from a connection started on VLAN 74 still works.
- Every session lane is explicitly blocked from LAB-MGMT, Internal, Servers, Management, Access, and Observability.
- EVIDENCE-QUARANTINE cannot be reached from either active lab lane and cannot initiate toward them.

I disabled the stale VLAN 77 DHCP DNS option. UniFi retains the old value as inactive configuration, but it no longer advertises it.

## Guest Network Configuration

The control-plane netplan uses `192.168.78.10/24`, gateway `192.168.78.1`, and resolver `9.9.9.9`. The three session interfaces have no host address and are marked optional.

Docker owns these networks:

```text
lab74  192.168.74.0/24  gateway 192.168.74.1  range 192.168.74.208/28
lab77  192.168.77.0/24  gateway 192.168.77.1  range 192.168.77.208/28
lab79  192.168.79.0/24  gateway 192.168.79.1  range 192.168.79.208/28
```

`kasm-lab-shims.service` creates host macvlan interfaces at `.201/32` and routes each `.208/28` session range through its shim. The unit starts after `network-online.target` and before Docker. A full guest reboot proved that the parent NICs, shims, routes, Docker networks, Kasm agent report, and all eight Kasm service containers return without manual action. Seven containers report Docker health `healthy`; `kasm_proxy` has no Docker health check and remains running. The API health endpoint returns `{"ok":true}`.

## Session Policy and Workspace Recipes

I created the Kasm group `Lab Sessions` with priority 100 and assigned the administrator account. Its effective settings are:

| Setting | Value |
| --- | --- |
| Upload | enabled |
| Download | disabled |
| Clipboard up | disabled |
| Clipboard down | disabled |
| Seamless clipboard | disabled |
| Session limit | 3,600 seconds |
| Persistent profile | disabled |

Each workspace needs both a network and an explicit resolver in its Docker Run Config Override:

```json
{"network":"lab74","dns":["9.9.9.9","149.112.112.112"]}
```

```json
{"network":"lab77","dns":["192.168.77.10"]}
```

```json
{"network":"lab79","dns":["192.168.79.10"]}
```

The persistent profile path stays empty. VLANs 77 and 79 deliberately point at unused in-lane addresses, so lookups fail locally. Using only `{"network":"lab77"}` is unsafe because Docker injects `127.0.0.11` and can forward queries through the host resolver on VLAN 78.

A workspace with no override runs on `kasm_default_network` and gets ordinary control-plane egress. I will not publish a lab workspace without the matching network and DNS override.

## Containment Evidence

I ran the tests with a temporary Alpine-derived image that carried Bash, curl, and DNS tools. I removed the image and every test container after the matrix passed.

| Test | Observed result |
| --- | --- |
| VLAN 74 DNS | Resolved through the explicit public resolvers |
| VLAN 74 Internet | Proton exit `185.98.168.20` |
| Kasm host Internet | The home WAN address, not a Proton exit |
| VLAN 74 to VLAN 77 | Connection initiated successfully |
| VLAN 77 to VLAN 74 | Blocked |
| VLAN 74 or 77 to VLAN 79 | Blocked |
| VLAN 79 to VLAN 74 or 77 | Blocked |
| VLAN 77 and VLAN 79 DNS | Failed |
| VLAN 77 and VLAN 79 Internet | Blocked |
| VLAN 77 and VLAN 79 direct TCP to `1.1.1.1:443` | Blocked |
| Any session lane to LAB-MGMT or protected homelab targets | Blocked |
| Personal-A VLAN to Kasm HTTPS | HTTP 200 |
| Trusted VLAN to Kasm health endpoint | `{"ok":true}` |
| Secure VLAN to Kasm TCP 443 | Blocked |
| Servers, Management, Access, and Observability to Kasm TCP 443 | Blocked |
| Kasm administrator authentication | Returned a valid session token |
| Kasm host image pull | `hello-world` pulled successfully |

The Trusted test succeeded. The Management Access VPN allow rule precedes its catchall VPN block, and I closed that path from a real remote client on 2026-07-28: connected over the VPN, opened `https://192.168.78.10/`, and the UI loaded. I did not substitute a forged source address at any point.

Each lane failed TCP probes to:

```text
192.168.78.10:443
192.168.80.10:22
192.168.70.10:8006
192.168.70.11:8006
192.168.71.10:22
192.168.72.2:443
192.168.73.2:9090
192.168.1.1:443
192.168.10.1:443
```

The Kasm host itself can reach its own `192.168.78.10:443` listener. That is a local self-reference, not routed traffic, and it is required for the service. It failed toward the other eight protected addresses.

### Proton failure test

The `KASM Lab Proton Egress` traffic route remains enabled, targets only KASM-BROWSER, and has its kill switch enabled. With the VPN enabled and healthy, VLAN 74 used the Proton exit.

To test a real tunnel failure without saving a modified configuration, I temporarily changed the live endpoint to TEST-NET address `192.0.2.1:51820`. VLAN 74 then lost Internet while the Kasm host retained plain WAN access. I restored the production endpoint, and VLAN 74 returned to `185.98.168.20`.

Disabling the VPN object administratively makes UniFi fall back to the normal WAN even when the route has its kill switch selected. I therefore keep the VPN object enabled whenever a VLAN 74 session may run. The verified fail-closed condition is an enabled VPN with a failed tunnel.

## Access and Credentials

The web UI is `https://192.168.78.10/`, and SSH uses the same address. I updated the stored dashboard URLs to the new address outside this repository. I also changed Jedi PC's `Host kasm-01` entry to `192.168.78.10` and verified the resolved SSH configuration. No credential changed, and no secret was written to this repository or its evidence.

## Residue Check

I removed the temporary Alpine test image, `hello-world`, every throwaway container, all temporary firewall rules, the temporary VLAN 10 test interface on Purple, and the temporary trunk admission used for that path.

The independent residue review then found eight dangling, untagged Kasm image IDs from 2026-07-21 through 2026-07-23. No container referenced them. I ran `docker image prune -f`, reclaimed 4.373 GB, and verified eight tagged service images, eight running service containers, and zero dangling images.

UniFi has no policy whose name begins with `TEST `. VM 122 has no snapshot, and no backup archive was created.

## Follow-up later on 2026-07-28

Three things came out of reviewing the finished work.

**Jedi PC could not reach the Kasm UI.** The two allow rules covered the Trusted and Personal-A networks, but Jedi PC sits at `192.168.50.241` on the Secure VLAN, and the containment matrix above recorded that lane as blocked. My own acceptance table proved the block and I read it as a pass. I added `LABMGMT Allow Jedi PC to kasm-01` for that single address on TCP 22 and 443. The controller assigned it index 10002, one place below the `LABMGMT Block Other Internal to LAB-MGMT` catchall at 10001, so the block would have matched first and the allow would never have fired. The update endpoint refuses to move an index, so I used the ordering API to place the two allows above the catchall, which renumbered them to 10000, 10001, and 10002. Verified from Jedi PC itself: `/api/__healthcheck` returns `{"ok": true}`, the UI returns HTTP 200, and TCP 22 opens. `ansible-01` on Personal-A still returns `{"ok": true}`, so the reorder cost nothing.

**`kasm-01` now runs `node_exporter` 1.9.0.** It binds `192.168.78.10:9100` alone rather than every interface, because this host carries macvlan shim addresses at `192.168.74.201`, `192.168.77.201`, and `192.168.79.201`, and a session container on any of those subnets reaches the shim without the gateway seeing the packet. Confirmed with `ss -lntp`: one listener on the control-plane address, and all three shim addresses plus loopback refuse the connection. The fleet playbook now takes the bind address as an inventory override, since a play-level variable outranks an inventory host variable and the first run ignored the override and bound 0.0.0.0.

`LABMGMT Allow monitor-01 to kasm-01 node_exporter` permits `192.168.73.2` to that one port. The scrape still failed until I narrowed `LABMGMT Block to AlphaSec-Observability` from all connection states to `NEW, INVALID`; blocking every state also dropped the replies to a scrape monitor-01 had started. `kasm-01` still cannot initiate toward `192.168.73.2` on 9090, 3000, or 22. Prometheus reports 47 targets, all up, and the repository's target assertion passes.

**The exporter needed a managed account, and that account is smaller than the fleet's.** The monitoring-exporters validator requires `ansible_user: ansible` on every host, and it failed my first attempt because I had pointed the inventory at `dkadi`. The check earned its keep, so I provisioned the standard account instead of relaxing it: user `ansible`, the controller's key carrying `from="192.168.40.36"` with pty and all forwarding disabled, and a mode-0440 `90-ansible` sudoers drop-in.

I then cut it below the fleet pattern. It holds no supplementary groups, so neither `sudo` nor `docker`, and its drop-in reads `ansible ALL=(root) NOPASSWD: ALL` rather than `(ALL:ALL)`. `docker` membership is root-equivalent by itself through a host bind mount, and the exporter play never touches Docker. What I could not do is allowlist commands: Ansible escalates through `sudo -u root /bin/sh -c '<token>; python3'` and feeds the module on stdin, so any grant that lets the play run is equivalent to root. The real constraints on this account are the source-address restriction on its key and the empty group list. The play runs clean afterwards and still reports `listen=192.168.78.10:9100`.

**Purple needed no node firewall.** I had recorded that item as outstanding. The Datacenter firewall is enabled and its `pve_mgmt` group already restricts TCP 22 and 8006 on every node to the four cluster addresses, three named admin devices, `ansible-01`, and two API consumers, with an explicit drop on both ports after them. There is no per-node `host.fw` because the rules are cluster-wide, which is tighter than the per-node file I had planned.

## Evidence

The exact final commands, structured requests, outputs, curated phase results, and storage baseline are indexed in [Evidence-Index.md](../../Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Evidence-Index.md).

## Rollback Points

- Phase 0 rollback is an offline migration back to `grey-server` and `ssd-lvm1`. No backup archive or snapshot exists.
- Phase 1 rollback restores net0 to VLAN 80 and `192.168.80.30/24`, then removes LAB-MGMT after its policies are removed.
- Phase 2 rollback removes the three Docker networks, the shim unit, and net1 through net3.
- Phase 3 rollback removes the 38 policies added for this change after the session containers stop.
- Phase 4 rollback re-enables the old VLAN 77 DHCP DNS value and removes the Kasm Proton route.
- Phase 5 rollback removes the `Lab Sessions` group after its member is reassigned.
- The 100 GiB to 150 GiB disk expansion has no in-place shrink rollback. Returning to 100 GiB requires a new smaller virtual disk and a filesystem-level migration because ext4 cannot shrink while mounted.

## Remaining Work

- Workspace catalog entries remain a separate task I will do. Each one needs the exact network and DNS override documented above before publication.

## Related Records

- [Execution plan](../Change%20Plans/Kasm%20Session%20Isolation.md)
- [Kasm deployment](../Deployment.md)
- [Isolated Security Lab](../../../../Architecture/Isolated-Security-Lab.md)
- [Kasm Workspaces](../../README.md)
