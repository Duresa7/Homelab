# Kasm Session Isolation

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Status:** Implemented and fully accepted 2026-07-28

## Outcome

Kasm sessions land in one of three sealed lanes, and the Kasm control plane sits on a management lane that reaches nothing else in the lab. Every session type I care about works: phishing links and pentest tooling on VLAN 74 behind Proton, malware with no Internet on VLAN 77, and artifact review on VLAN 79. I wrote this plan before execution, then I added the workspace recipes after validating the live network behavior.

This plan builds the plumbing only. Adding a workspace registry, pulling images, & creating workspaces are mine to do; the plan stops at leaving the networks, the firewall, & the session policy ready for them.

## Execution Result

I completed the storage, migration, control-plane move, session networks, Kasm group policy, firewall matrix, containment tests, documentation, and residue cleanup. The durable result is in [Kasm Session Isolation - 2026-07-28](../Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). I verified the Management Access VPN policy and its order, then closed the end-to-end check from a real remote client later the same day.

I skipped both backup steps during this implementation by choice: no `vzdump` archive and no pre-change VM snapshot. That applies to the migration and the NIC retag, not to running the lab. The snapshot-before-malware rule under Operating rules still stands.

Testing corrected two assumptions in this plan. A Docker network override also needs an explicit `dns` value, or Docker's embedded resolver can forward through the management host. The Proton route fails closed when the VPN stays enabled and its tunnel fails, but administratively disabling the VPN object causes normal WAN fallback. The change record and architecture record carry the final workspace recipes and operating rule.

## Decisions behind this plan

I made these calls on 2026-07-28 and treated them as settled during execution.

| Decision | Reason |
| --- | --- |
| Kasm containers only. No Windows VM, no KVM detonation guest | Kasm 1.19.0 CE builds Docker containers. Adding a second machine class doubles the work for a lab I want simple |
| `kasm-01` is expendable. The rest of the lab & the four-node cluster are not | This is the whole point of the design. Every rule below protects the lab from `kasm-01`, not `kasm-01` from the samples |
| Three lanes, not one | 74 needs internet for phishing links. 77 must have none. One lane can't be both |
| VLAN 77 gets no internet | A sample with internet can reach its operator, pull a second stage, & attack strangers from my exit address |
| VLAN 74 reaches 77. VLAN 77 can't reach 74 | I want to SSH from a tooling session into a target session. A target that gets owned shouldn't be able to turn around & hit my tooling |
| Control plane moves to a new VLAN 78 | `kasm-01` currently shares VLAN 80 with `app-01`, `supabase-01`, `splunk-siem`, & `security-01`. A container escape lands beside production today |
| Files move only through the Kasm browser window | Kasm's upload rides the HTTPS session, not the container's network, so an offline lane still receives files. A mounted share would give a live sample a filesystem path to a lab host |
| Upload on, download off for malware workspaces | The sample needs to get in. Nothing needs to come back out to my PC |
| INetSim is out of scope | It existed to feed fake DNS & HTTP to samples with no internet. It's now optional Phase 7, one container instead of an LXC |
| Lab guests go on the 850 EVO, not the boot NVMe | Snapshots & rollbacks hit this pool constantly. When it fills or fails I want the hypervisor's root filesystem on a different device |

Windows samples can't run in a Linux container at all, so this lab covers Linux samples, phishing pages, file inspection, & forensic triage. Windows work needs a VM & is a separate project.

## Verified state on 2026-07-28

I checked all of this live before writing the plan and used it as the execution baseline.

`kasm-01` is VM 122 on `grey-server`: 4 cores, 8192 MiB, 100 GiB on `ssd-lvm1`, one NIC `net0 virtio=<REDACTED_KASM_HOST_MAC>,bridge=vmbr0,firewall=1,tag=80`, static 192.168.80.30/24 set through cloud-init `ipconfig0`. Kasm 1.19.0 CE with all 8 service containers up 3 days. The `licenses` table is empty, so the 5-concurrent-session cap applies.

Two things differ from the [deployment record](../Deployment.md) state of 2026-07-25. The `images` table holds **zero workspace definitions**, & the three test workspace images are gone from Docker. Root filesystem use dropped from 26 GiB to 16 GiB of 96 GiB, & `docker images -a` returns only the 8 `kasmweb` service images. That makes this the cheapest moment to rearrange the networking, because there's nothing to break.

Docker networks on the host: `bridge`, `host`, `kasm_default_network` at 172.18.0.0/16, `kasm_sidecar_network`, `none`. `ufw` is inactive, which doesn't matter because Docker writes its own nftables rules & the gateway is what enforces the lanes.

On the controller there are 14 zones & 25 networks. The three lab networks exist & each is bound to its own zone:

| VLAN | Network | Network ID | Zone | Zone ID |
| ---: | --- | --- | --- | --- |
| 74 | KASM-BROWSER 192.168.74.1/24 | `6a616a0d2d027bb055268248` | KASM-BROWSER | `6a616d942d027bb055268c60` |
| 77 | MALWARE-OFFLINE 192.168.77.1/24 | `6a616a0e2d027bb055268251` | MALWARE-OFFLINE | `6a616dbb2d027bb055268d8e` |
| 79 | EVIDENCE-QUARANTINE 192.168.79.1/24 | `6a616a0e2d027bb05526825c` | EVIDENCE-QUARANTINE | `6a616dc32d027bb055268e16` |

Nine `KASM` firewall policies survive & all nine are baseline: DHCP & NTP allows to the Gateway zone, a gateway block per lane, & an External block on 77 & 79. Not one of them blocks a lab zone toward Internal or the `AlphaSec` zones. That containment rests on the custom-zone default, & after the 2026-07-27 consolidation deleted 44 policies I want it tested rather than assumed.

Traffic route `KASM Lab Proton Egress` (`6a6170cc2d027bb055269a6c`) is enabled with the kill switch on, matching INTERNET, targeting the KASM-BROWSER network object. The older `VPN - Proton` route is disabled.

VLAN 77's DHCP still advertises DNS 192.168.77.10, an address with nothing on it since the [2026-07-23 teardown](../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md). VLAN 74 advertises 9.9.9.9 & 149.112.112.112. VLAN 79 advertises none. VLANs 75, 76, & 78 are free.

The UniFi MCP has no zone-matrix membership endpoint & no create-zone tool, so zone creation & network-to-zone binding are web console operations. Policy creation works through the MCP.

## Phase 0: Storage on the 850 EVO, then move to `purple-server`

Lab guests live on the Samsung 850 EVO at `/dev/sda`, & nothing Kasm-related touches the boot NVMe. The reason is failure-domain separation rather than endurance. Malware writes, snapshots, & rollbacks hammer this pool by design, & when a lab pool fills up, corrupts, or dies I want the hypervisor's root filesystem sitting untouched on a different device.

State on 2026-07-28: `sda` carries an empty GPT label with zero partitions & 232.9 GiB free, so there's nothing to preserve. `wipefs -n /dev/sda` reports only `gpt` & `PMBR` signatures. The relocation plan's note about a leftover 16 MiB partition is out of date.

I read both drives before committing to this:

| Metric | 850 EVO `sda` | Boot NVMe `nvme0n1` |
| --- | --- | --- |
| SMART health | PASSED | PASSED |
| Power-on hours | 45,240 | 23,225 |
| Host writes | 332 TB against a 75 TBW rating | 36.9 TB |
| Wear indicator | `Wear_Leveling_Count` normalized 15 of 100, raw 1800 average erase cycles | `Percentage Used` 30% |
| Reallocated sectors | 0 | not applicable |
| Uncorrectable & integrity errors | 0 | 0 |

The EVO has taken 4.4 times its rated writes and reports 15% of its wear budget left. It passes SMART with zero reallocated sectors and zero CRC errors, so it works today. A lab pool is the right load for a drive I don't fully trust because every byte on it is disposable. I chose to proceed without a `vzdump` archive.

- [x] Confirm `sda` is still empty with `lsblk -f` & `wipefs -n /dev/sda`. If anything other than `gpt` & `PMBR` appears, stop
- [x] Build the VG, the thin pool, & the storage entry in one call, the way the GUI does it:

```bash
pvesh create /nodes/purple-server/disks/lvmthin --name ssd-lvm2 --device /dev/sda --add_storage 1
```

- [x] Restrict it to the one node & set its content types: `pvesm set ssd-lvm2 --nodes purple-server --content images,rootdir`
- [x] Verify with `pvesm status`, `vgs`, & `lvs`. Expect `ssd-lvm2` active at roughly 232 GiB with 0% used

The name follows the fleet convention. `grey-server` carries `lvmthin: ssd-lvm1` on VG `ssd-lvm1` with `nodes grey-server`, so purple gets `ssd-lvm2` on VG `ssd-lvm2` with `nodes purple-server`.

- [x] No backup taken, by choice. `hddpool-1` could not have held one anyway: its content types are `images,rootdir`, and the only backup-capable storage on `grey-server` is `local`, at 70.67% used. The rollback path is a migration back to `ssd-lvm1`, not a restore
- [x] Shut down VM 122, then `qm migrate 122 purple-server --targetstorage ssd-lvm2`, offline. Nothing depends on `kasm-01`, so downtime is free & an offline move has fewer failure modes across different storage types
- [x] Boot & verify: all 8 containers healthy, `/api/__healthcheck` returns `{"ok": true}`, the admin credential authenticates. The guest was using 16 GiB of its 96 GiB filesystem on 2026-07-28, so expect a short copy
- [x] Confirm `qm config 122` now reports `ssd-lvm2:vm-122-disk-1` & `ssd-lvm2:vm-122-disk-0` for the EFI disk, & that `lvs` on the boot NVMe shows nothing belonging to VM 122
- [x] Record the EVO's `Reallocated_Sector_Ct` & `Wear_Leveling_Count` in the change record as the baseline to compare against later

Every phase after this one runs on `purple-server`. Use the `purple_server` SSH profile & `qm guest exec 122` there.

VLAN tags live in the guest's NIC config & the macvlan parents are guest interface names, so both survive a migration. `vmbr0` on `grey-server` & `purple-server` are each `bridge-vlan-aware yes` with `bridge-vids 2-4094`. If `kasm-01` ever moves again, none of the isolation work needs redoing. The reasoning for choosing purple, & the cluster tradeoff it carries, stays in [Kasm Relocation to Purple](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Plans/Kasm%20Relocation%20to%20Purple.md).

## Phase 1: Move the control plane to VLAN 78

- [x] Create network LAB-MGMT, VLAN 78, subnet 192.168.78.1/24, DHCP server disabled. `kasm-01` is the only host & it gets a static address, so there's no reason to answer DHCP in this lane
- [x] Create firewall zone LAB-MGMT in the web console & bind the LAB-MGMT network to it. Confirm the binding by reading the network's `firewall_zone_id` back
- [x] Create these policies. Name each with a `LABMGMT` prefix so they group the way the nine `KASM` policies do

| Action | Source | Destination | Ports |
| --- | --- | --- | --- |
| ALLOW | Internal zone, networks Trusted & Personal-A only | 192.168.78.10 | TCP 443, 22 |
| ALLOW | Vpn zone, network Management Access | 192.168.78.10 | TCP 443, 22 |
| BLOCK | LAB-MGMT | Internal | any |
| BLOCK | LAB-MGMT | `AlphaSec-Servers` | any |
| BLOCK | LAB-MGMT | `AlphaSec-Mgmt` | any |
| BLOCK | LAB-MGMT | `AlphaSec-Access` | any |
| BLOCK | LAB-MGMT | `AlphaSec-Observability` | any |
| BLOCK | LAB-MGMT | Gateway | any |
| BLOCK | LAB-MGMT | KASM-BROWSER, MALWARE-OFFLINE, EVIDENCE-QUARANTINE | any |

Both ALLOW rules target named networks rather than a whole zone. I verified on 2026-07-28 that Trusted (VLAN 10) & Personal-A (VLAN 40) both carry `firewall_zone_id 68b788c0e9f08f1e1b2a2288`, which is Internal, & that `Management Access` (10.6.0.0/24) sits in the Vpn zone `68b788c0e9f08f1e1b2a228b`. A zone-wide source would hand the Kasm login page to every other network in Internal, & I can't read full zone membership through the MCP to know what else is in there.

Blocking LAB-MGMT toward the three lab lanes does not break sessions. The Kasm agent reaches session containers over the macvlan shims built in Phase 2, which are on-link inside each lab subnet & never touch the gateway. That's counterintuitive enough to be worth stating before someone "fixes" it.

LAB-MGMT keeps plain internet through the External zone so Kasm can pull workspace images from Docker Hub. Set the guest's resolver to 9.9.9.9 so DNS leaves through External rather than needing a Gateway allow.

- [ ] Snapshot VM 122 before touching the NIC. I skipped this step; no snapshot was created
- [x] `qm set 122 -net0 virtio=<REDACTED_KASM_HOST_MAC>,bridge=vmbr0,firewall=1,tag=78 -ipconfig0 ip=192.168.78.10/24,gw=192.168.78.1`
- [x] Edit `/etc/netplan/50-cloud-init.yaml` in the guest to the same address & apply it, so netplan & `ipconfig0` agree no matter which one wins at boot
- [x] Reboot & verify: all 8 containers healthy, `GET https://192.168.78.10/api/__healthcheck` returns `{"ok": true}`, the admin credential authenticates from the Trusted VLAN, & `docker pull hello-world` succeeds

Kasm records the server's hostname in its own database. If the agent shows offline in Admin after the address change, correct the recorded hostname under Infrastructure, then restart the stack with the scripts under `/opt/kasm/bin/`. Don't reinstall over it.

## Phase 2: Attach the lab NICs & build the session networks

- [x] Add three NICs with the Proxmox firewall off on each:

```bash
qm set 122 -net1 virtio,bridge=vmbr0,tag=74,firewall=0 -net2 virtio,bridge=vmbr0,tag=77,firewall=0 -net3 virtio,bridge=vmbr0,tag=79,firewall=0
```

`firewall=0` is not optional. With `firewall=1` Proxmox installs an ebtables filter that only passes the NIC's own MAC address. Every macvlan container gets its own MAC, so the guest firewall silently drops all session traffic & the symptom looks like a broken container rather than a filter.

- [x] In the guest, confirm the interface names with `ip -br link` & bring all three up with no address, `dhcp4: no` & `optional: true` in netplan. The live names are `enp6s19`, `enp6s20`, and `enp6s21`
- [x] Create one macvlan network per lane, with the container range outside each DHCP pool of `.100` to `.199`:

```bash
docker network create -d macvlan --subnet 192.168.74.0/24 --gateway 192.168.74.1 \
  --ip-range 192.168.74.208/28 -o parent=enp6s19 lab74
docker network create -d macvlan --subnet 192.168.77.0/24 --gateway 192.168.77.1 \
  --ip-range 192.168.77.208/28 -o parent=enp6s20 lab77
docker network create -d macvlan --subnet 192.168.79.0/24 --gateway 192.168.79.1 \
  --ip-range 192.168.79.208/28 -o parent=enp6s21 lab79
```

- [x] Build a shim per lane so the Kasm agent & proxy can reach session containers:

```bash
ip link add shim74 link enp6s19 type macvlan mode bridge
ip addr add 192.168.74.201/32 dev shim74
ip link set shim74 up
ip route add 192.168.74.208/28 dev shim74
```

Repeat with `shim77` on `enp6s20` at 192.168.77.201 & `shim79` on `enp6s21` at 192.168.79.201.

A Linux host can't reach its own macvlan children through the parent interface. Without the shim, a session starts, the container comes up healthy, & the connection then fails with the logs pointing at the container. Kasm's proxy container also needs this path, & it works through the same host route.

- [x] Persist the shims with a systemd oneshot unit ordered after `network-online.target` & before `docker.service`, then reboot once & confirm they come back
- [x] Verify each lane with a throwaway container, not a Kasm workspace:

```bash
docker run --rm --network lab74 alpine ip -4 addr show eth0
docker run --rm --network lab74 alpine ping -c2 192.168.74.1
ping -c2 <container address from the first command>
```

- [x] Confirm Kasm itself sees the new networks. The `servers` table carries a `docker_network_names` column that the agent reports upward, & the `images` table carries `restrict_to_network` & `restrict_network_names`, so the three names should appear as selectable networks in the admin UI once the agent checks in

### If a session comes up but won't connect

The container getting an address proves the lane works. A session that starts & then fails to display is a host-to-container reachability problem, not a Kasm problem, & the logs will point at the container & waste an afternoon. Work through these in order:

1. Confirm the shim route exists: `ip route get 192.168.74.208` should resolve through `shim74`, not through `enp6s19` or the default route
2. Confirm `firewall=0` on the lab NIC in `qm config 122`. The ebtables MAC filter is the single most likely cause & it produces exactly this symptom
3. Switch the driver to ipvlan, which shares the parent's MAC instead of giving each container its own: `-d ipvlan -o parent=enp6s19 -o ipvlan_mode=l2`. Addressing & the shim stay the same

If all three fail, stop rather than improvise. The documented fallback is to leave sessions on `kasm_default_network` & put the host's own NIC on the single lane that matters most, which trades three lanes for one but keeps the lab sealed from the rest of the network. Record which of the three steps failed & what it did, because that's the finding worth keeping.

## Phase 3: Lane-to-lane firewall policy

Keep the nine existing `KASM` policies. Add these, prefixed the same way:

| Action | Source | Destination | Reason |
| --- | --- | --- | --- |
| ALLOW | KASM-BROWSER | MALWARE-OFFLINE | Tooling reaches targets. This is the pentest path |
| BLOCK | MALWARE-OFFLINE | KASM-BROWSER | An owned target can't reach back into tooling |
| BLOCK | KASM-BROWSER | EVIDENCE-QUARANTINE | Review artifacts stay out of reach of tooling |
| BLOCK | MALWARE-OFFLINE | EVIDENCE-QUARANTINE | Same, from the lane that holds live samples |
| BLOCK | each lab zone | LAB-MGMT | A session can't attack the control plane over the network |
| BLOCK | each lab zone | Internal, `AlphaSec-Servers`, `AlphaSec-Mgmt`, `AlphaSec-Access`, `AlphaSec-Observability` | Written explicitly instead of trusting the zone-matrix default |

EVIDENCE-QUARANTINE gets reached through the Kasm web UI, never from another lane.

## Phase 4: Fix the VLAN 77 resolver & confirm the Proton route

- [x] Turn off the DHCP DNS entry on VLAN 77. It advertises 192.168.77.10, which has held nothing since 2026-07-23. With no resolver advertised, a sample's lookups fail instead of hanging on a dead server. Phase 7 puts a responder back at that address if I want richer behaviour later
- [x] Confirm `KASM Lab Proton Egress` still targets only the KASM-BROWSER network & the kill switch stays enabled. Do not add MALWARE-OFFLINE to it
- [x] Leave VLAN 74's 9.9.9.9 & 149.112.112.112 alone. Those queries leave through Proton with everything else

## Phase 5: Session policy in Kasm

No workspace installs in this phase. Settings only.

- [x] On the group that will own lab sessions: uploads enabled, downloads disabled, clipboard restricted, & a session time limit set
- [x] Record the recipe for later. The final override declares both the network and resolver, for example `{"network":"lab77","dns":["192.168.77.10"]}`, and the persistent profile path stays empty

A workspace with no override runs on `kasm_default_network`, which NATs out `net0` on the management lane with plain internet. That's the failure mode to watch for, & it fails quietly because the session works fine.

Out of scope & mine to do: adding a workspace registry, pulling images, creating workspaces.

## Phase 6: Containment test, & nothing runs before it passes

Run every probe from a throwaway `alpine` container on each lane. Use this exact form, because `/dev/tcp` needs the port after a slash:

```bash
timeout 3 bash -c 'echo > /dev/tcp/192.168.80.10/22' && echo OPEN || echo blocked
```

A space in place of that second slash makes every probe fail, which reads as a clean pass & is nothing of the sort. I made that mistake while gathering state for this plan.

| From | Expected |
| --- | --- |
| `lab74` container | `curl -s ifconfig.me` returns a Proton exit address. Keep the VPN object enabled and force its tunnel to fail; the same request times out. A `lab77` container's port is reachable |
| `lab77` container | No route to 1.1.1.1, no DNS, & the `lab74` container is unreachable |
| `lab79` container | No internet & nothing else reachable |
| every lab container | 192.168.78.10:443, 192.168.80.10:22, 192.168.70.10:8006, 192.168.70.11:8006, 192.168.71.10:22, 192.168.72.2:443, 192.168.73.2:9090, 192.168.1.1:443, & 192.168.10.1:443 all fail |
| `kasm-01` on VLAN 78 | `docker pull hello-world` works. Every remote address in the row above fails. Its own `192.168.78.10:443` listener remains open by design. The UI loads from the Trusted VLAN & over the VPN |

Record the results in a change record with the commands & their output. A pass here is what earns the right to run a sample.

Every check passed. The container matrix, the Trusted path, the service-zone blocks, and the cleanup all held, and I closed the last one, the end-to-end Management Access VPN client path to `https://192.168.78.10/`, from a real remote client on 2026-07-28.

## Operating rules

Snapshot VM 122 before a malware session & roll back to it afterwards. That's what makes "the Kasm host is expendable" a fact rather than a sentence. Without it, every sample leaves behind whatever it left behind & the host quietly stops being trustworthy. Take a fresh snapshot whenever I finish changing workspaces or settings, so a rollback costs me only the session I just ran.

Untrusted workspaces stay disposable: no saved profile, a session time limit, & the container destroyed at the end.

I chose not to serialise sessions, so a sample can run while another workspace is open. A container escape reaches every session on the host through the shared kernel, whatever the gateway does to their routed lanes. If I ever want that closed, the fix is running one session at a time, not another firewall rule.

## Phase 7, optional & later: fake services on VLAN 77

Run a DNS & HTTP responder as a container on the `lab77` network at 192.168.77.10, then re-enable the VLAN 77 DHCP DNS entry that already points there. One `docker run` on a host that gets rolled back anyway, instead of a separate LXC to maintain. Do this when resolution failures stop telling me enough about a sample.

## Rollback

| After | Rollback |
| --- | --- |
| Phase 0 | Shut down VM 122 and migrate it back to `grey-server` with target storage `ssd-lvm1`. No backup archive exists |
| Phase 1 | Set `net0` back to `tag=80` with 192.168.80.30, restore the matching netplan, and delete the LAB-MGMT policies, network, and zone. No pre-change snapshot exists |
| Phase 2 | `qm set 122 -delete net1 -delete net2 -delete net3`, `docker network rm lab74 lab77 lab79`, remove the systemd unit. Sessions fall back to `kasm_default_network` |
| Phase 3 | Delete the added policies. The nine baseline `KASM` policies are untouched |
| Phase 4 | Re-enable the VLAN 77 DHCP DNS entry with 192.168.77.10 |

## Stop conditions

Stop & reassess if any of these happen:

- `sda` shows any signature other than `gpt` & `PMBR` before the wipe, which would mean something lives there that I don't know about
- The 850 EVO reports a non-zero `Reallocated_Sector_Ct`, a non-zero `CRC_Error_Count`, or `Wear_Leveling_Count` normalized below 10. At 15 today it has little margin, & a change in any of those three is the signal to move the pool rather than keep writing to it
- VM 122 fails verification after the migration and needs a restore that does not exist
- A Phase 6 probe shows a lab container reaching a homelab address
- A `lab74` container shows an exit address that isn't Proton's, or keeps Internet while the VPN object remains enabled and its tunnel fails
- The Kasm agent doesn't re-register after the Phase 1 address change & the recorded-hostname correction
- Session containers get addresses but no traffic passes, which points at `firewall=1` on a lab NIC or a missing shim route
- Any change to the nine existing `KASM` policies becomes necessary to make something work

## Documentation on completion

- Change record under `Platforms/Kasm Workspaces/Documentation/Change Records/` with the Phase 6 output as evidence
- Update [Isolated Security Lab](../../../../Architecture/Isolated-Security-Lab.md): containers only, VLAN 78 control plane, VLAN 77 offline with no INetSim, & the lane-to-lane rules
- Update the UniFi inventories under `Infrastructure/Network/UniFi/Configuration/` for the new network, zone, & policies
- Update [Kasm Relocation to Purple](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Plans/Kasm%20Relocation%20to%20Purple.md) so its INetSim & NIC steps point here
- Update the root [TODO](../../../../TODO.md) entry, the [Galaxy backlog](../../../../Infrastructure/Compute/Galaxy/Documentation/TODO.md) item for the 850 EVO, & the [deployment record](../Deployment.md) state section
- Roll the `Operations/Inventory/Galaxy/` guest inventory forward, since VM 122 changes node, storage, & address
- Record the new `ssd-lvm2` storage entry in the Galaxy configuration exports, & file the SMART baseline for `sda` under `Operations/Diagnostics/`

## Related records

- [Kasm Workspaces deployment](../Deployment.md)
- [Kasm Relocation to Purple](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Plans/Kasm%20Relocation%20to%20Purple.md)
- [Isolated Security Lab](../../../../Architecture/Isolated-Security-Lab.md)
- [Kasm lab network simplification (2026-07-23)](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [Zone and object consolidation (2026-07-27)](../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md)
