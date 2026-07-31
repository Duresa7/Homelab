# S05 Green Physical Rerun

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture window:** 2026-07-31T06:12:24+00:00 through 2026-07-31T12:41:27+00:00  
**Targets:** `ansible-01`, `grey-server`, Bane switch port 4, and `green-server`  
**Mechanisms:** SSH Manager, Galaxy PXE state and service logs, and UniFi Network controller readback  
**Working directory:** `/home/ansible/proxmox-pxe-provisioning` where applicable

## Preflight and Arm

On `ansible-01`, I confirmed `galaxy-pxe` and `tftpd-hpa` were active, `/health` returned `ok`, and Green's state was `disabled`. Grey reported cluster name `Galaxy`, four nodes, `Quorate: Yes`, and all three remote peers connected on Corosync links 0 and 1. UniFi returned Bane port 4 on `Server-Provision`.

After authorizing the physical rerun, I issued:

```bash
python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  --force \
  <GREEN_NODE_MAC> ready

python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  --json \
  <GREEN_NODE_MAC>
```

The readback returned `ready`, no attempt ID, and an update time of `2026-07-31T06:12:43+00:00`. The commands exited `0`.

## Original Installed-System Finding

Green next booted the local installation from the first physical run. I reached it remotely and confirmed 16 GB of installed RAM and Proxmox on `/dev/nvme0n1`. The retained first-boot log showed a connection failure to `192.168.40.36:8080` while the port still used native VLAN 5. This proved the first installer had finished and identified the missing pre-cutover callback path.

I previewed and created `Allow Server-Provision callbacks to Galaxy PXE`. UniFi read back enabled policy ID `6a6c927885e3cf84d3d7c033`, source network `Server-Provision`, destination `192.168.40.36`, protocol TCP, and destination port 8080. A direct callback request then passed from Green.

I set the UEFI BootNext entry to IPv4 PXE and restarted the M920q.

## Physical Installer Timeline

The Galaxy PXE service recorded:

```text
2026-07-31T12:19:19+00:00  installer_claimed
2026-07-31T12:20:49+00:00  answer_served
2026-07-31T12:20:49+00:00  bootstrap_fetched
2026-07-31T12:22:26+00:00  installer_succeeded
2026-07-31T12:27:25+00:00  first_boot_started
2026-07-31T12:41:03+00:00  network_ready
2026-07-31T12:41:26+00:00  cluster_joined
2026-07-31T12:41:27+00:00  complete
```

The state record used attempt ID `<PXE_ATTEMPT_ID>`. The schema 1.2 installer result reported:

```text
FQDN: green-server.galaxy
Boot mode: EFI
Filesystem: ext4
Boot disks: /dev/nvme0n1
Other disks: /dev/sda
Installer address: 192.168.5.18/24
```

The service log matched the state history. It served the UEFI boot assets and full ISO, accepted the answer request and bootstrap fetch, then received the installer-complete webhook from `192.168.5.18`.

## First-Boot Repair During the Rerun

The rerun initially stopped after `first_boot_started`. The cached script did not retry a refused callback connection while `galaxy-pxe` restarted, and its ICMP gate could fail even when the required SSH path worked.

I updated both callback fetches with bounded retries, removed the ICMP gates, made key-only SSH to Grey the required network proof, added bounded Corosync convergence polling, and added reason-coded failures. The full 21-test suite, Python compilation, Ansible syntax check, and rendered first-boot `bash -n` passed. I redeployed the service, replaced Green's cached first-boot script, and restarted the one-shot unit.

At `12:41:01 UTC`, Green refetched `/v1/bootstrap`, recorded a new `first_boot_started`, and fetched `/v1/join-key` from `192.168.70.14`. It then moved through `network_ready`, `cluster_joined`, and `complete` without another repair.

## Final Verification

I verified the following after `complete`:

- Galaxy reported five nodes and `Quorate: Yes`.
- Green and Grey each showed four remote peers connected on Corosync links 0 and 1.
- Green held `192.168.70.14/24` on MGMT-A and `192.168.71.14/24` on Cluster-Net.
- Required Proxmox, firewall, time, and node-exporter services were active.
- Root SSH accepted the approved keys and did not allow password authentication.
- `/dev/nvme0n1p3` was the Proxmox LVM physical volume.
- `/dev/sda` had no partition, filesystem, mount, LVM, ZFS, or Proxmox storage reference.
- UniFi returned Bane port 4 on `Proxmox-Trunk`, with VLANs 70 and 71 admitted and PoE off.
- UniFi returned both callback policies enabled: `6a6c927885e3cf84d3d71363` for Green on MGMT-A and `6a6c927885e3cf84d3d7c033` for `Server-Provision`.

The final state readback returned `phase: complete`, `started_at: 2026-07-31T12:19:19+00:00`, and `updated_at: 2026-07-31T12:41:27+00:00`. The command exited `0`.
