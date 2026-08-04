# Galaxy Proxmox PXE Provisioning

**Created:** 2026-07-30  
**Last updated:** 2026-07-31

I use this project to install a registered Galaxy node from UEFI PXE, apply the normal Proxmox network baseline, and join the node to the Galaxy cluster. The physical machine registry names only the intended install disk. Green names `nvme0n1`, so its generated Proxmox answer does not list the SATA disk.

## Request Flow

1. UniFi gives the machine a VLAN 5 lease and points UEFI PXE at `192.168.40.36` and `galaxy-ipxe.efi`.
2. The embedded iPXE loader sends the machine MAC to the HTTP service on `ansible-01`.
3. A machine in `ready` atomically claims one attempt and moves to `installer_claimed`. Every other state exits iPXE and continues to the local disk.
4. Proxmox posts system information to `/v1/answer`. The service matches the registered MAC, records `answer_served`, and returns the machine-specific answer.
5. The answer uses Proxmox's post-installation webhook to report the successful boot disk. A disk mismatch records `failed`.
6. First boot reports its own milestones, changes from VLAN 5 to MGMT-A and Cluster-Net, fetches the dedicated join key, and joins Galaxy through Grey with `pvecm add --use_ssh`.
7. The service records `complete` only after Green verifies both local VLAN addresses, key-only SSH to Grey on MGMT-A, five-node cluster membership, both connected Corosync links, services, key-only root SSH, the expected NVMe LVM physical volume, and the absence of `/dev/sda` from LVM.

Every callback carries the attempt ID created by the one-use claim. A stale or wrong attempt cannot advance another run.

## Machine States

| State | Meaning |
|---|---|
| `disabled` | Exit to the local disk. This is the default for a new machine. |
| `ready` | Permit the next matching PXE request to claim one install. |
| `installer_claimed` | iPXE claimed the attempt. Another PXE request cannot reinstall the node. |
| `answer_served` | Proxmox received the generated answer. |
| `bootstrap_fetched` | The installer fetched the first-boot script. |
| `installer_succeeded` | Proxmox's post-installation webhook reported the expected boot disk. |
| `first_boot_started` | The installed node started the bootstrap script. |
| `network_ready` | MGMT-A and Cluster-Net are configured and Grey is reachable. |
| `cluster_joined` | Green joined Galaxy and passed the immediate cluster checks. |
| `complete` | Cluster, service, SSH, and storage checks passed. |
| `failed` | A callback or first-boot check recorded a failed attempt. |

The registry keeps the attempt ID, start and update timestamps, current detail, and chronological history under a filesystem lock.

## State Command

I inspect Green on `ansible-01` with:

```bash
sudo python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  --json \
  <REDACTED_NODE_MAC>
```

I authorize one install with:

```bash
sudo python3 /usr/local/lib/galaxy-pxe/state.py \
  --machines /etc/galaxy-pxe/machines.json \
  --state-file /var/lib/galaxy-pxe/state.json \
  <REDACTED_NODE_MAC> ready
```

Rearming an active, completed, or failed attempt requires the same command with `--force`. I use that flag only after deciding another NVMe erase is intended. Setting `disabled` makes later network boots exit without loading the installer.

## Deployment

The project is deployed at `/home/ansible/proxmox-pxe-provisioning`. I run:

```bash
cd /home/ansible/proxmox-pxe-provisioning
python3 -m unittest discover -s tests -v
sudo ansible-playbook playbooks/deploy.yml
```

The playbook installs:

| Path | Purpose |
|---|---|
| `/usr/local/lib/galaxy-pxe/` | HTTP service and state command |
| `/etc/galaxy-pxe/` | Machine registry, root hash, approved root public keys, and dedicated join key |
| `/var/lib/galaxy-pxe/state.json` | Runtime attempt state |
| `/srv/tftp/galaxy-ipxe.efi` | UEFI iPXE loader |
| `/srv/galaxy-pxe/` | Kernel, initrd, PXE ISO, and generated iPXE menu |
| `/var/cache/galaxy-pxe/` | Verified source ISO and assistant package |

`galaxy-pxe.service` listens on TCP 8080. `tftpd-hpa.service` listens on UDP 69. Both start at boot. The playbook refuses any target except `ansible-01`, verifies the three root-only runtime files, pins iPXE to commit `404588d5f7c84815dfbf6c34912467b86a4376f4`, and stays idempotent after deployment.

## Machine Registry

The live `config/machines.json` contains hardware MAC addresses, node addresses, and the exact install disk. Git ignores that file. I copy `config/machines.example.json` to `config/machines.json`, replace every `<YOUR_...>` value, and verify the disk name against `lsblk` before deployment.

The public example also contains a disposable acceptance identity at synthetic MAC `02:00:00:00:09:99`. It targets a VM disk named `sda`, powers off after the installer, and skips the physical-node first-boot routine. I completed a disposable install through tagged VLAN 5 on 2026-07-31, destroyed VM 999, and returned that identity to `disabled`.

## Verification

```bash
systemctl is-active galaxy-pxe tftpd-hpa
curl --fail http://127.0.0.1:8080/health
journalctl -u galaxy-pxe -u tftpd-hpa
```

The generated answer must pass:

```bash
proxmox-auto-install-assistant validate-answer /path/to/answer.toml
```

I also render the first-boot script and run `bash -n` against it before a physical attempt. The current suite has 21 tests covering the state lock, attempt IDs, callback order, installer result, install-disk isolation, SSH cluster join, root SSH baseline, acceptance VM behavior, asset streaming, and runtime input checks.

The custom iPXE loader is unsigned, so Secure Boot must be off. A 7 GiB acceptance VM exhausted the PXE initramfs before it could mount the installer. The same path completed with 12 GiB, so I require at least 12 GiB and prefer 16 GiB for a physical node. The generated automated kernel line includes `nomodeset` to avoid the documented installer framebuffer hang on affected hardware.

## Recovery

If an attempt stops, I inspect the full state record and the two service journals before I rearm it. A machine at `installer_succeeded` has written the target disk even if first boot never started. A machine at `failed` keeps the failing phase and detail. During an active Green recovery, `/var/log/galaxy-pxe-first-boot.log` holds the local bootstrap output after the installed system starts. I retain a sanitized evidence summary before removing that one-run log.

I leave Bane port 4 on `Server-Provision` until the first-boot state reaches at least `network_ready`. I change it to `Proxmox-Trunk` only after the node's management address is reachable and the node is visible in the cluster. UniFi policy `Allow Server-Provision callbacks to Galaxy PXE` permits the VLAN 5 callback before cutover. `Allow Proxmox Nodes to Galaxy PXE` uses `OBJ-Proxmox-Nodes` for the post-cutover TCP 8080 callback. I add a future node's management address to that object instead of creating another policy.
