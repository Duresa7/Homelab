# Galaxy PXE Provisioning Service

**Created:** 2026-07-30  
**Last updated:** 2026-07-31

**Implementation date:** 2026-07-30  
**Repair date:** 2026-07-31  
**Status:** Complete; Green joined Galaxy at 2026-07-31 12:41:26 UTC  
**Primary owner:** `Platforms/Galaxy PXE`  
**Affected systems:** `ansible-01`; Ahsoka Gateway; Bane switch port 4; Galaxy Datacenter firewall; planned `green-server`

## Scope

I deployed a reusable UEFI PXE service on `ansible-01` for Galaxy Proxmox nodes. The first physical record installs Proxmox VE 9.2-1 on Green's `/dev/nvme0n1`, leaves `/dev/sda` out of the answer, applies the Red-derived network baseline, and joins Galaxy through Grey.

The first physical run downloaded the complete installer path and installed Proxmox, but its first-boot callback couldn't reach `ansible-01`. I kept Green out of the cluster, repaired the service, proved the disposable acceptance path, and reran the physical sequence. Green joined as Galaxy's fifth node and reached `complete` at 2026-07-31 12:41:27 UTC.

## Starting State

- The Lenovo M920q had UEFI PXE IPv4 enabled and reported MAC `<GREEN_NODE_MAC>`.
- Bane switch port 4 used the `Server-Provision` profile.
- `Server-Provision` provided native VLAN 5 on `192.168.5.0/24` and advertised `192.168.40.36` with filename `galaxy-ipxe.efi`.
- Galaxy had four quorate Proxmox VE 9.2.5 nodes.
- The Galaxy `pve_cluster` IP set and UniFi `OBJ-Proxmox-Nodes` already included planned address `192.168.70.14`.
- The original PXE service used a four-state gate and marked a node complete before it configured networking or joined Galaxy.

## Decisions

- I kept a MAC-specific, one-use installer gate. `ready` is the only operator state that allows an install claim.
- I replaced the flat state with a timestamped attempt record. Installer and first-boot callbacks now identify the exact attempt and follow an enforced order.
- I use Proxmox's post-installation webhook to record a successful installer result and the sanitized boot disk before first boot.
- I install the approved Galaxy root public keys through the answer file, then enforce key-only root SSH during first boot.
- I join through Grey with a dedicated key and `pvecm add --use_ssh`. The prior password/API path is not part of the runtime.
- I report `complete` only after networking, cluster membership, quorum, required services, SSH policy, and storage checks pass.
- I require both local VLAN addresses, a successful key-only SSH path to Grey, five cluster nodes, and four connected peers on each Corosync link before `complete`.
- I keep Bane port 4 on `Server-Provision` during installation and first boot. The port changes to `Proxmox-Trunk` only after Green is reachable on MGMT-A and visible in Galaxy.
- I added `nomodeset` to the automated installer entry as a Proxmox-documented framebuffer workaround. The first run did not retain enough target-side evidence to prove a framebuffer fault.

## Resulting Configuration

| Setting | Value |
|---|---|
| Provisioning network | `Server-Provision`, VLAN 5, `192.168.5.0/24` |
| Physical switch port | Bane port 4 |
| DHCP boot server | `192.168.40.36` |
| DHCP boot filename | `galaxy-ipxe.efi` |
| PXE MAC | `<GREEN_NODE_MAC>` |
| Hostname | `green-server.galaxy` |
| Install disk | `nvme0n1` |
| Disk excluded from installer and LVM | `sda` |
| MGMT-A | `192.168.70.14/24`, gateway `192.168.70.1` |
| Cluster-Net | `192.168.71.14/24` |
| Join peer | `192.168.70.10` |
| Join method | Dedicated SSH key with `pvecm add --use_ssh` |
| Final Green state | `complete` since 2026-07-31 12:41:27 UTC |

The service state sequence is:

```text
disabled -> ready -> installer_claimed -> answer_served
         -> bootstrap_fetched -> installer_succeeded
         -> first_boot_started -> network_ready -> cluster_joined -> complete
```

Any permitted active phase can record `failed`. Wrong attempt IDs and skipped transitions return an error instead of changing the record.

## Step 1: Deploy the Initial Service

I added the first Python service, registry, state command, Ansible deployment, systemd and TFTP templates, and tests on 2026-07-30. I used `proxmox-auto-install-assistant` to prepare the official Proxmox VE 9.2-1 ISO, built the embedded UEFI iPXE loader, and served the installer from `ansible-01`.

The ISO matched SHA256:

```text
4e88fe416df9b527624a175f24c9aa07c714d3332afb1ee3dbf3879573ef2c6c
```

The live health endpoint, complete TFTP loader transfer, generated answer validation, firewall compilation, and four-node cluster health passed before the first physical run.

The original evidence remains summarized in this record. I did not retain a complete terminal transcript for every 2026-07-30 command.

## Step 2: Observe the First Green Attempt

Green requested the UEFI loader and HTTP installer on 2026-07-31. The server recorded the boot request at `03:38:18 UTC`, then served `boot.ipxe`, `vmlinuz`, `initrd.img`, and the full PXE ISO. Proxmox posted its answer request and fetched the bootstrap at `03:39:46 UTC`.

The M920q did not return on `192.168.70.14`, did not call back from first boot, and did not join Galaxy. The old state remained `installing` for more than 40 minutes. Galaxy stayed quorate with four nodes.

The server-side evidence proves delivery through the installer answer and bootstrap fetch. It does not prove which target-side installer step stopped. The investigation is in [Green PXE Install Stalls Before Reboot](../Troubleshooting/Green%20PXE%20Install%20Stalls%20Before%20Reboot%20-%202026-07-31.md), with the retained boundary in [S01](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S01%20Green%20First-Run%20Failure%20Trace%20-%202026-07-31.md).

## Step 3: Repair the State and First-Boot Path

I split the application into registry, rendering, HTTP service, state command, and entry-point modules. I added an attempt ID, timestamps, phase history, ordered callbacks, a failure state, Proxmox's post-installation webhook, and boot-disk verification.

I replaced the unusable cluster credential path with a dedicated SSH key. The deployment authorizes its public half in Grey's `/root/.ssh/authorized_keys`; the private half stays root-readable on `ansible-01`. A batch SSH check from `ansible-01` to Grey passed.

The generated answer installs the approved Galaxy root public keys. First boot disables password SSH, requires key-only root access, changes networking, waits for Grey, joins with `--use_ssh`, and validates the final node before it can report `complete`. The LVM check requires `/dev/nvme0n1p3` and fails if `/dev/sda` appears as a physical volume.

The regression suite grew from 13 to 21 tests. It passed locally and on the exact uploaded project. Python compilation, Ansible syntax, rendered first-boot `bash -n`, and the official Proxmox answer validator passed. [S02](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S02%20Repair%20and%20Deployment%20Validation%20-%202026-07-31.md) records the check boundary.

## Step 4: Exercise the Disposable Acceptance Path

I created disposable VM 999 on Red with UEFI, a 32 GiB disk, MAC `02:00:00:00:09:99`, and VLAN 5. The first run emitted DHCP discovers but received no offer. After I admitted `Server-Provision` as a tagged network on `Proxmox-Trunk`, the next UEFI boot reached `ansible-01` and claimed an installer attempt.

The 7 GiB run failed while unpacking initramfs with `No space left on device` and could not mount `/mnt/pve-installer.squashfs`. I increased only the disposable VM to 12 GiB. That run reached the answer parser and exposed an invalid acceptance-only value: `poweroff` instead of Proxmox's `power-off`.

I corrected the value and reran the 12 GiB VM. Proxmox accepted the answer, wrote the 32 GiB disk, posted schema 1.2 results for exactly `/dev/sda`, and powered the VM off. The service recorded `installer_succeeded` at `05:50:08 UTC` with DHCP address `192.168.5.143/24`.

I verified the stopped VM name, destroyed VM 999, removed both logical volumes and temporary captures, confirmed the config and volumes were absent, and returned the acceptance identity to `disabled`. [S03](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S03%20Disposable%20Acceptance%20VM%20Constraint%20-%202026-07-31.md) records the blocked first test, three post-change runs, and the cleanup.

## Step 5: Deploy and Verify the Repaired Service

I deployed the repaired project to `ansible-01`. A later playbook run reported:

```text
ansible-01 : ok=30 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
```

Both services are enabled and active, `/health` returns `ok`, and the automated kernel line contains both `proxmox-start-auto-installer` and `nomodeset`. Before the physical rearm, Green and the synthetic acceptance identity both read `disabled`.

The dedicated join key authenticated to Grey in batch mode. Grey reported cluster name `Galaxy`, four nodes, and `Quorate: Yes`. Green is not a cluster member. [S04](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S04%20Final%20Live%20Verification%20-%202026-07-31.md) records the final readback.

## Step 6: Close the Post-Cutover Paths

An independent review found that Green would lose its callback path after changing from VLAN 5 to MGMT-A. I previewed and, after confirmation, created UniFi policy `Allow Galaxy PXE callbacks to ansible-01`. The initial IPv4 policy allowed only `192.168.70.14` in `AlphaSec`-Mgmt to reach `192.168.40.36` in `Internal` on TCP 8080. I read back policy ID `6a6c36cc85e3cf84d3d71363` with the same selectors.

The installed system also needed to call back while Bane port 4 still used native VLAN 5. I previewed and, after confirmation, created `Allow Server-Provision callbacks to Galaxy PXE`. The enabled IPv4 policy allows the `Server-Provision` network to reach only `192.168.40.36` on TCP 8080. I read back policy ID `6a6c927885e3cf84d3d7c033` with the same selectors.

The same review found that running `corosync-cfgtool -s` without checking its output could still report `complete` with a broken second link. I added Grey's Cluster-Net address `192.168.71.10`, local address checks for `vmbr0.70` and `vmbr0.71`, an exact key-only SSH check to Grey on MGMT-A, an exact five-node check, and a per-link requirement for four connected peers.

## Verification

- 21 local tests passed.
- The same 21 tests passed from `/home/ansible/proxmox-pxe-provisioning`.
- All five Python modules compiled.
- `ansible-playbook --syntax-check playbooks/deploy.yml` passed.
- The rendered first-boot script passed `bash -n`.
- The official Proxmox assistant accepted the generated answer.
- A 12 GiB disposable UEFI VM completed the automatic disk install, reported only `/dev/sda`, and powered off.
- UniFi read back both confirmed callback policies to `ansible-01:8080`; the post-cutover source is reusable group `OBJ-Proxmox-Nodes`.
- First boot now rejects a missing local VLAN address, a failed key-only SSH connection to Grey, a node count other than five, or fewer than four connected peers on either Corosync link.
- The deployed playbook reached `changed=0`, `failed=0`, and `unreachable=0`.
- `galaxy-pxe` and `tftpd-hpa` are enabled and active.
- The dedicated key reached Grey without a password prompt.
- The physical M920q installed to `/dev/nvme0n1`; the installer reported `/dev/sda` only as an untouched other disk.
- Green reached `complete` after all five nodes appeared and each Corosync link showed four connected remote peers.
- Green's required services are active, root SSH is key-only, and the LVM physical volume is `/dev/nvme0n1p3`.
- Bane port 4 now uses `Proxmox-Trunk` with VLANs 70 and 71 admitted and PoE off.

These checks prove the repaired server lifecycle, generated artifacts, VLAN 5 PXE path, physical NVMe install, MGMT-A cutover, and unattended cluster join on the M920q.

## Rollback

Before another physical attempt, I can leave Green `disabled`, stop and disable `galaxy-pxe.service` and `tftpd-hpa.service`, and remove only the documented runtime paths on `ansible-01`. I can remove the dedicated public key line from Grey after matching its exact key.

I remove `192.168.70.14` from the Galaxy `pve_cluster` IP set and UniFi `OBJ-Proxmox-Nodes` only if I abandon Green. Those entries are required once the node joins.

## Step 7: Arm the Physical Rerun

I repeated the live preflight immediately before arming Green. Both PXE services were active, `/health` returned `ok`, Galaxy was four-node and quorate, both existing Corosync links had all three remote peers connected, and Bane port 4 still used `Server-Provision`.

The repository does not contain Green's installed RAM capacity. Secure Boot was already off during the first run because the unsigned custom iPXE loader executed. I recorded the RAM uncertainty and proceeded after authorizing the real rerun.

At `2026-07-31T06:12:43+00:00`, I changed Green from `disabled` to `ready` with `--force` and read back a new record with no attempt ID. [S05](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S05%20Green%20Physical%20Rerun%20-%202026-07-31.md) records the preflight and arm result.

## Step 8: Prove the First Install and Start the Rerun

When Green started its old local installation, I inspected it remotely. The machine had 16 GB of installed memory and Proxmox on `/dev/nvme0n1`. The retained first-boot log showed that the initial install had finished, but the system could not reach `192.168.40.36:8080` from VLAN 5. That finding replaced the earlier unproven framebuffer and memory hypotheses with a specific callback-policy failure.

I created the VLAN 5 callback policy, confirmed the callback with `curl`, set UEFI BootNext to the IPv4 PXE entry, and restarted Green. The service claimed the physical attempt at `12:19:19 UTC`, served the answer and bootstrap at `12:20:49 UTC`, and accepted the Proxmox installer-complete webhook at `12:22:26 UTC`. The schema 1.2 result named `/dev/nvme0n1` as the only boot disk and `/dev/sda` as an other disk.

## Step 9: Repair the First-Boot Retry Path

The rerun reached `first_boot_started` at `12:27:25 UTC`, then stopped before `network_ready`. The callback began too soon after `galaxy-pxe` started, and the old script used ICMP as a gate even though the required SSH path worked.

I changed both callback fetches to retry connection refusal, removed the ICMP gates, made the Grey SSH check the network proof, polled Corosync convergence, and added reason-coded failure reporting. Two independent reviews agreed with that control flow. The 21 tests, Python compilation, Ansible syntax check, and rendered `bash -n` passed again. I redeployed the service, replaced Green's cached first-boot script with the repaired version, and restarted the one-shot unit.

## Step 10: Complete the Physical Provisioning Run

Green refetched its bootstrap at `12:41:01 UTC`, recorded `network_ready` at `12:41:03 UTC`, joined Galaxy at `12:41:26 UTC`, and reached `complete` at `12:41:27 UTC`. Galaxy then reported five nodes and quorum. Green and Grey each showed four remote peers connected on Corosync links 0 and 1.

I confirmed the required Green services were active, root SSH accepted keys and rejected password authentication, `/dev/nvme0n1p3` was the only Proxmox LVM physical volume, and `/dev/sda` had no partition, filesystem, mount, LVM, ZFS, or Proxmox storage reference. I then confirmed Bane port 4 on `Proxmox-Trunk`, with VLANs 70 and 71 admitted and PoE off.

## Step 11: Consolidate the Post-Cutover Firewall Selector

I replaced the Green-only source on policy `6a6c36cc85e3cf84d3d71363` with existing address group `OBJ-Proxmox-Nodes`, group ID `6a67a1eb052792cd214090f1`. The group held all five Galaxy management addresses from `192.168.70.10` through `192.168.70.14`. I renamed the policy `Allow Proxmox Nodes to Galaxy PXE` and kept the destination limited to `192.168.40.36:8080` over IPv4 TCP.

The update preview showed only the source selector changing from the Green address to the existing group. After applying it, UniFi read back `matching_target_type: OBJECT` and the expected group ID. Grey and Green each received `ok` from the PXE `/health` endpoint. The provisioning rule still uses the `Server-Provision` network object, so no duplicate address group or firewall policy was required. [S06](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S06%20Firewall%20Group%20Consolidation%20-%202026-07-31.md) records the change and verification.

## Step 12: Remove Superseded Deployment Residue

I checked the exact cleanup candidates on `ansible-01` after the repaired deployment reached an idempotent result. The legacy `/etc/galaxy-pxe/cluster-password` file was already absent. The only remaining text reference to that filename was a negative regression assertion that rejects the retired command-line option.

I removed three timestamped deployment backups, the source and deployed Python bytecode caches, one abandoned Ansible temporary cache, and the two local Windows helper files used for Green's one-time SSH path. I kept the PXE source, services, prepared installer assets, ISO and package caches, state database, join key, and TFTP loader. Both services remained active, `/health` returned `ok`, and all 21 remote tests passed with bytecode generation disabled. [S07](../../Evidence/Galaxy%20PXE%20Repair%20-%202026-07-31/Logs/S07%20Deployment%20Residue%20Cleanup%20-%202026-07-31.md) records the exact boundary and post-delete verification.

## Remaining Work

The PXE deployment is complete. The separate Galaxy hardware and baseline work tracks the extended SMART tests, Green disk wipe, hardware inventory, monitoring target, subscription-popup automation, and the planned rolling node-name replacements.
