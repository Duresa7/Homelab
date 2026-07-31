# Kasm Relocation to Purple

**Created:** 2026-07-25  
**Last updated:** 2026-07-31

**Status:** Superseded and implemented 2026-07-28

> [Kasm Session Isolation](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md) superseded this plan and was implemented on 2026-07-28. It built `ssd-lvm2`, moved VM 122 to Purple, dropped INetSim and KVM guests from scope, moved the control plane to VLAN 78, attached the three macvlan session lanes, and completed the containment gate. This record remains for the placement reasoning and cluster-trust tradeoff.

## Execution Result

The completed change is recorded in [Kasm Session Isolation - 2026-07-28](../../../../../Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Session%20Isolation%20-%202026-07-28.md). `kasm-01` now runs on `purple-server` from `ssd-lvm2`; the LAB-MGMT control plane and VLAN 74, 77, and 79 session networks survived a reboot and passed the harmless-container acceptance matrix.

I chose to proceed without a `vzdump` archive or VM snapshot, so neither rollback artifact was created. The live VM and final storage state were healthy after the migration.

## Outcome

Kasm and everything Kasm spawns runs on `purple-server`. Grey is back to production only. The lab VLANs 74, 77, and 79 reach their Kasm session networks, VLAN 77 stays offline with no INetSim, and the acceptance checks in the [Isolated Security Lab](../../../../../Architecture/Isolated-Security-Lab.md) passed before any real sample.

Out of scope: `kali-pen` (VM 106) stays on Grey. It predates Kasm and isn't part of this lab. I destroyed the unrelated Windows test VM 103 during the Active Directory decommission on 2026-07-27.

## Why Purple

Grey runs `app-01` at 24 GiB, `splunk-siem` at 12 GiB, `security-01` at 12 GiB, `alpha-prod-01` at 16 GiB, & `edge-01`. Kasm sessions & malware detonation don't belong on the same node as production. Purple carries zero guests today & has 15 GiB of RAM plus two unused disks, so it can take the whole lab.

I'm keeping Purple in the Galaxy cluster. That's a deliberate tradeoff & it costs me part of the isolation:

```text
purple# ssh 192.168.70.10 'hostname; id -un'
grey-server
root
```

Cluster members hold each other's root keys in `/etc/pve/priv/authorized_keys`, along with the cluster CA private key at `/etc/pve/priv/pve-root-ca.key`. Root on Purple is root on Grey. A sample that escapes its container, then escapes QEMU, reaches Grey regardless of which node it started on. I'm accepting that because the four-node console is worth more to me than closing a path that requires a QEMU vulnerability to walk.

What that buys me instead: the defense has to sit at the guest boundary, so Step 4 & Step 6 carry weight they wouldn't if Purple were standalone.

## Resource budget

Purple has 15 GiB usable & an Intel i5-8500T at 6 cores, 6 threads, 2.10 GHz.

| Guest | RAM | Note |
| --- | --- | --- |
| `kasm-01` | 8 GiB | 2 concurrent sessions. Kasm's 8 service containers idle at 2.1 GiB, & each default workspace requests 2768 MB |
| INetSim LXC | 1 GiB | Perl daemon, doesn't need more |
| One detonation VM | 4 GiB | One at a time |
| PVE | 1.5 GiB | Measured at 1 GiB with no guests running |
| **Total** | **14.5 of 15** | |

That fits with 500 MiB spare & no room for a second detonation guest. 32 GiB of DDR4 on the LGA1151 board would let me run a victim, a target, & a monitor at once. It's the cheapest upgrade available & it isn't a blocker.

| Pool | Device | Size | Holds |
| --- | --- | --- | --- |
| general guest thin pool | Samsung 850 EVO, `sda` | 232.9 GB | VM disks and LXC root volumes, including Kasm guests |
| `local-lvm` | Toshiba THNSF5256GPUK boot NVMe | 140.87 GiB, 0% used | INetSim LXC, spare |

I assigned the 850 EVO a permanent role as ordinary Proxmox guest storage on 2026-07-27. Kasm can use that pool, but the pool isn't dedicated to Kasm.

## Step 1: Audit the UniFi zone matrix

Read-only. Nothing else starts until this passes, because every later step assumes the lab zones are sealed.

- [ ] Confirm KASM-BROWSER, MALWARE-OFFLINE, & EVIDENCE-QUARANTINE each block toward Internal, `<YOUR_ORG_NAME>`-Servers, & `<YOUR_ORG_NAME>`-Mgmt
- [ ] Confirm `KASM Lab Proton Egress` still targets VLAN 74 only with the kill switch on
- [ ] Confirm the 9 surviving `KASM` policies match the [2026-07-23 simplification](../../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)

Custom zones default to Block All, but that change deleted 44 policies & I want the current matrix confirmed rather than assumed.

## Step 2: Build the general guest thin pool on the 850 EVO

`sda` currently holds one leftover 16 MiB partition & nothing else.

- [ ] Wipe `sda`, create the VG & thin pool
- [ ] Add it as PVE storage with `nodes purple-server` and enable VM image plus LXC root-directory content
- [ ] Confirm with `pvesm status` on Purple

## Step 3: Move `kasm-01` to Purple

VM 122 is 100 GiB provisioned & 26 GiB used. The cluster link is 1 GbE.

- [ ] `vzdump` VM 122 to Grey's `hddpool-1` first. This is the rollback point
- [ ] Shut down VM 122
- [ ] `qm migrate 122 purple-server --targetstorage <pool>`, offline
- [ ] Boot & verify: 8 containers healthy, `GET https://192.168.80.30/` returns 200, `/api/__healthcheck` returns `{"ok": true}`, admin authenticates
- [ ] Confirm the three test images survived: `forensic-osint` 10.3 GB, `vs-code` 6.42 GB, `terminal` 4.83 GB

Offline rather than live. Nothing depends on `kasm-01`, so downtime is free & offline has fewer failure modes across differing storage.

## Step 4: Harden Purple & the detonation guest template

This is where the isolation actually lives now that Purple stays clustered.

- [ ] Enable the Proxmox node firewall on Purple, limiting TCP 8006 & 22 to the management VLAN
- [ ] Confirm Purple's host carries no IP on 74, 77, or 79. `vmbr0` is already `bridge-vlan-aware yes` with `bridge-vids 2-4094`, so guests get the tags without the host holding an address in any lab lane
- [ ] Keep `pve-qemu-kvm` current. Most published escapes are device-emulation bugs, so patch level matters more than any single config choice
- [ ] Build detonation guests with the device list stripped: no `qemu-guest-agent`, no USB passthrough, no audio, no SPICE, no serial, `virtio-scsi-single` & q35 only
- [ ] No shared folders & no clipboard passthrough on detonation guests
- [ ] Snapshot before each detonation, roll back after

## Step 5: Rebuild INetSim & fix the VLAN 77 resolver

VLAN 77's DHCP still hands out `192.168.77.10`, which was the INetSim host destroyed in the [2026-07-23 teardown](../../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md). Malware that gets silence plays dead & teaches me nothing, so this has to exist before the first sample.

- [ ] Create the INetSim LXC on Purple, 1 GiB, static `192.168.77.10/24` on VLAN 77
- [ ] Configure it to answer DNS for every name with its own address, & to serve HTTP, HTTPS, SMTP, FTP, & IRC
- [ ] Confirm the UniFi DHCP DNS entry on VLAN 77 now points at a host that exists
- [ ] Verify from a throwaway guest on 77 that a made-up hostname resolves & the fake HTTP response arrives

## Step 6: Attach the lab VLAN NICs

One VLAN at a time. VLAN 74 first, because Proton egress is the piece with a testable answer.

- [ ] Add `net1` to VM 122 with `tag=74`, static `192.168.74.10/24`, outside the `.100` to `.199` DHCP pool
- [ ] Create the Docker network on `kasm-01` bound to that interface & map one workspace to it
- [ ] Test with the `terminal` image: confirm the egress address is Proton's, & confirm it can't reach `192.168.80.10`, `192.168.70.10`, or `192.168.72.2`
- [ ] Repeat for 77 & 79 once 74 proves out

Confirm against the Kasm 1.19 networking documentation whether the agent expects a macvlan against the new interface or a bridge. I haven't verified which.

## Step 7: Acceptance before the first live sample

Every check in the [Isolated Security Lab acceptance boundary](../../../../../Architecture/Isolated-Security-Lab.md) runs with harmless test guests. No sample runs until all of them pass, & I record the results in the change record rather than here.

## Rollback points

| After | Rollback |
| --- | --- |
| Step 2 | Remove the storage entry & wipe `sda`. Nothing else has touched it |
| Step 3 | Restore the `vzdump` archive to Grey's `ssd-lvm1` & power on there. The archive stays until Step 7 passes |
| Step 5 | Stop the LXC & revert the VLAN 77 DHCP DNS entry |
| Step 6 | Remove `net1` from VM 122. Sessions fall back to VLAN 80, which is where they run today |

## Stop conditions

I stop & reassess if any of these happen:

- Step 1 finds a lab zone that doesn't block toward Internal, `<YOUR_ORG_NAME>`-Servers, or `<YOUR_ORG_NAME>`-Mgmt
- The migration in Step 3 fails verification & the `vzdump` restore is needed
- Purple's replacement NVMe reports a `Critical Warning` other than `0x00`, or `Percentage Used` climbs above its current 30%
- A Step 6 containment test shows a session reaching a production address
- Any acceptance check in Step 7 fails

## Related records

- [Kasm Workspaces deployment](../../../../../Platforms/Kasm%20Workspaces/Documentation/Deployment.md)
- [Isolated Security Lab](../../../../../Architecture/Isolated-Security-Lab.md)
- [Kasm lab network simplification (2026-07-23)](../../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [Kasm lab Proxmox teardown (2026-07-23)](../../../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md)
- [Purple NVMe reliability failure](../../../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Purple%20NVMe%20Reliability%20Failure%20-%202026-07-22.md)
