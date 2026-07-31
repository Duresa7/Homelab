# Galaxy Cluster Node Rename Rolling Replacement Plan

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Research date:** 2026-07-31  
**Status:** Research complete; execution not started  
**Scope:** Proxmox VE 9.2.5 cluster `Galaxy`

## Decision

I can't rename these five clustered nodes in place. The current Proxmox VE Administration Guide says each node must be installed with its final hostname & IP configuration because changing the hostname or IP after cluster creation isn't supported. `pmxcfs` also treats `nodes/<NAME>` as the owner boundary for node configuration, certificates, VM configuration, & LXC configuration; it can't rename a non-empty directory. Editing `/etc/hostname`, changing `name:` inside `corosync.conf`, or renaming `/etc/pve/nodes/<OLD_NAME>` would leave those ownership boundaries out of agreement. [Proxmox VE Administration Guide 9.2.3, Cluster Manager, pp. 109-110](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=132) [Proxmox VE Administration Guide 9.2.3, pmxcfs, pp. 136-138](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=159)

I will treat the work as five rolling node replacements. For each physical server I will evacuate its guests & node-local data, power it off, remove the old member with `pvecm delnode`, reinstall Proxmox VE with the final `*-node` hostname, then join it as a new member. Proxmox documents a fresh installation as the required path when the same server joins the same cluster after removal. [Proxmox VE Administration Guide 9.2.3, Remove a Cluster Node, pp. 114-117](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=137)

The official manual available on the research date is release 9.2.3, generated on 2026-07-03. The live nodes report `pve-manager/9.2.5`; I will confirm the installed `pvecm`, `ha-manager`, `qm`, `pct`, & `pvesr` help before execution. I won't substitute the manual separation procedure in section 5.6. Proxmox labels that procedure not recommended, while section 5.5 gives the reinstall path used here. [Proxmox VE Administration Guide 9.2.3, title page](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=1) [Proxmox VE Administration Guide 9.2.3, Separate a Node Without Reinstalling, pp. 117-118](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=140)

## Name & address mapping

I will retain the five management & Cluster-Net addresses. An address becomes reusable only after the old installation is powered off, removed from Corosync, & prevented from booting on the cluster network.

| Physical node | Old member | New member | Management / Corosync link 0 | Cluster-Net / Corosync link 1 |
| --- | --- | --- | --- | --- |
| Grey | `grey-server` | `grey-node` | `192.168.70.10/24` | `192.168.71.10/24` |
| Purple | `purple-server` | `purple-node` | `192.168.70.11/24` | `192.168.71.11/24` |
| Blue | `blue-server` | `blue-node` | `192.168.70.12/24` | `192.168.71.12/24` |
| Red | `red-server` | `red-node` | `192.168.70.13/24` | `192.168.71.13/24` |
| Green | `green-server` | `green-node` | `192.168.70.14/24` | `192.168.71.14/24` |

The join requires synchronized time, TCP 22 between members, UDP 5405 through 5412 for Corosync, the same Proxmox VE version, & unique final names. Galaxy uses two Corosync links, so each new member must join with both addresses rather than receiving link 1 as a later repair. [Proxmox VE Administration Guide 9.2.3, Cluster Requirements, pp. 109-110](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=132) [Proxmox VE Administration Guide 9.2.3, Adding Nodes with a Separated Cluster Network, p. 114](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=137)

## Execution order & known blockers

I will replace one member at a time in this order. The listed workload state comes from the current repository & remains a preflight hypothesis until a live check proves it immediately before each removal.

| Order | Replacement | Reason for position | Required workload action |
| --- | --- | --- | --- |
| 1 | `green-server` to `green-node` | Green is the pilot candidate because the PXE project assigned it no production guest. | Stop if `qm list`, `pct list`, either guest configuration directory, or local storage inspection finds a workload. |
| 2 | `purple-server` to `purple-node` | Purple has one bounded workload, Kasm VM 122, & one SATA LVM-thin pool restricted to the old node name. | Migrate or back up VM 122; preserve or copy its disks; change `ssd-lvm2` from `nodes purple-server` to `nodes purple-node` only after the physical VG is present. [Galaxy storage inventory](../../Configuration/Storage/README.md) |
| 3 | `red-server` to `red-node` | Red has CT 842 plus a host SATA bind mount at `/data`. | Back up the CT root file system & the bind-mounted data with separate mechanisms. `vzdump` does not include bind-mount contents. [Proxmox VE Administration Guide 9.2.3, LXC Bind Mount Points, pp. 306-308](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=329) |
| 4 | `blue-server` to `blue-node` | Blue carries monitor-01 plus CT 107 & CT 108. The latter two use node-local `local-lvm` & a strict node-affinity rule named `pin-blue-local-storage`. | Take restorable backups, remove the two services from HA without stopping them, migrate them through controlled downtime, then recreate the rule against `blue-node` only after their disks return to Blue. The 2026-07-20 incident proves their configs can't be placed on a node without the matching local volumes. [HA local-storage incident](../Troubleshooting/HA%20Local-Storage%20Stranding%20of%20CT%20107%20and%20CT%20108%20After%20a%20Blue-Server%20Shutdown%20-%202026-07-20.md) |
| 5 | `grey-server` to `grey-node` | Grey carries the largest guest set, multiple node-local storage pools, NUT service, & the Ansible/PXE LXC. Grey's AMD CPU also differs from the four Intel nodes. | Move every guest & node service first. Use offline VM migration or backup/restore between AMD & Intel, because Proxmox supports online VM migration only between CPUs from the same vendor. [Proxmox VE Administration Guide 9.2.3, Cluster Requirements, p. 110](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=133) |

Green must return as a five-node member before Purple starts. The same rule applies at every later boundary.

## Cluster-wide preparation

### Final names, installation targets, & capacity

I will create the final DNS and `/etc/hosts` names before the first installation, but I won't put a new node on an address while the old installation can still transmit. The PXE inventory must render the final `*-node` hostname, the retained `.70` & `.71` addresses, & the exact NVMe installation target for that physical server. A SATA data disk remains untouched only when the pre-install disk identity check proves that the installer target is the intended NVMe device.

Every guest needs a destination with enough CPU, memory, & real storage capacity. Proxmox shares `/etc/pve/storage.cfg` across the cluster, but an identically named local storage on two nodes contains physically different data. The `shared` flag doesn't copy a disk. The `nodes` property limits a storage definition to named members, so every old member reference must be replaced after its physical backend is proven on the new installation. [Proxmox VE Administration Guide 9.2.3, Storage Configuration, pp. 143-144](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=166)

### Backups & guest evacuation

Before removing a member, I need a successful backup for every guest & node-local data set that would be lost with its boot disk. I will test at least one restore path for the node's workload class before reaching `pvecm delnode`; a completed backup job without a readable archive isn't the acceptance check.

VMs on local disks can use storage migration. Running containers can't use ordinary live migration; `pct migrate <CTID> <TARGET> --restart --target-storage <MAPPING>` stops the container, copies its storage-backed volumes, & starts it on the target. Bind mounts & device mounts remain outside Proxmox storage, migration, snapshots, & `vzdump`; Red's `/data` needs its own copy & comparison. [Proxmox VE Administration Guide 9.2.3, Bulk Guest Migration, p. 76](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=99) [Proxmox VE Administration Guide 9.2.3, Container Migration, p. 319](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=342) [Proxmox VE Administration Guide 9.2.3, Container Backup, p. 441](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=464)

I will inspect `hostpci`, `usb`, `dev`, `mp`, `hookscript`, local ISO, local snippet, & local backup references in each guest configuration. A guest config moved away from a node doesn't prove that a passthrough device, host path, or snippet followed it.

### HA state & rules

I won't rely on node maintenance mode to solve Blue's strict local-storage rule. Maintenance mode asks HA to migrate managed services according to the active affinity rules; a strict rule with no other eligible node can leave a shutdown waiting for manual intervention. Manual maintenance also persists across a reboot until it is explicitly disabled. [Proxmox VE Administration Guide 9.2.3, Node Maintenance, pp. 431-432](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=454)

For CT 107 & CT 108 I will first capture `ha-manager config` & `ha-manager rules config`, take restorable backups, then use `ha-manager remove` before their planned restart migration. Proxmox documents that removing a resource from HA doesn't start or stop it; by default it also removes that resource from rules. After `blue-node` is rebuilt, its `local-lvm` is active, & both containers are restored there, I will recreate `pin-blue-local-storage` with `blue-node` as the strict member and re-add the two HA resources. [Proxmox VE Administration Guide 9.2.3, HA Management Tasks, p. 413](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=436) [Proxmox VE Administration Guide 9.2.3, Node Affinity Rules, pp. 423-425](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=446)

All other HA rules must lose the old member before it is deleted. Proxmox leaves deleted node names in HA rules, so cleanup isn't optional. [Proxmox VE Administration Guide 9.2.3, Cleanup After Node Removal, p. 117](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=140)

### Replication, jobs, ACLs, & node-scoped configuration

No replication job can name the member being removed. Proxmox warns that migration can reverse a replication job toward the retiring node, so I will run `pvesr list` before guest movement and again after the last migration. Any affected job must finish removal with `pvesr delete <JOB_ID>` before the node is deleted. [Proxmox VE Administration Guide 9.2.3, Remove a Cluster Node Prerequisites, p. 115](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=138)

I will scan the active cluster configuration for the exact old name without reading `/etc/pve/priv` secrets:

```bash
OLD_NODE=green-server

grep -R -nF -- "$OLD_NODE" \
  /etc/pve/corosync.conf \
  /etc/pve/storage.cfg \
  /etc/pve/ha \
  /etc/pve/firewall \
  /etc/pve/jobs.cfg \
  /etc/pve/replication.cfg \
  /etc/pve/mapping \
  /etc/pve/sdn 2>/dev/null

pveum acl list | grep -F -- "$OLD_NODE" || true
```

The review includes storage `nodes` restrictions, HA rules, backup-job node selectors, PCI/USB/resource mappings, SDN node lists, ACL paths such as `/nodes/<NAME>`, node firewall files, & comments used by operators. Historical records keep their event-time hostnames. Living configuration, monitoring labels, Ansible/PXE inventory, SSH Manager aliases, DNS, diagrams, & current inventories move to `*-node` after the matching live change passes.

### Certificates & SSH identity

The join replaces the new installation's node certificate with one signed by the Galaxy cluster CA. That browser session ending during the join is expected. I won't copy the old automatically generated `pve-ssl.pem`, `pve-ssl.key`, or cluster CA key onto the new installation. [Proxmox VE Administration Guide 9.2.3, Join Node to Cluster, pp. 112-113](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=135) [Proxmox VE Administration Guide 9.2.3, Certificate Management, pp. 77-78](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=100)

Custom `pveproxy-ssl.pem` & `pveproxy-ssl.key` files are node-specific because `/etc/pve/local` points at `/etc/pve/nodes/<NODENAME>`. A certificate issued for `grey-server` may not contain `grey-node`; I will inspect it with `pvenode cert info` & reissue or upload a certificate for the new name instead of copying an invalid name forward. [Proxmox VE Administration Guide 9.2.3, Certificates for API & Web GUI, p. 77](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=100)

The removed member's SSH public key & fingerprint remain in cluster files. After the new node is accepted, I will remove the old public key from `/etc/pve/priv/authorized_keys` only when its exact fingerprint isn't shared with automation or another node. If the reused IP produces an SSH host-key error after the join, Proxmox directs me to run `pvecm updatecerts` once on the re-added node. [Proxmox VE Administration Guide 9.2.3, Cleanup After Node Removal, p. 117](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=140)

## Per-node procedure

### Step 1: Capture the live preflight

I will run these checks from the retiring member & one healthy peer. The output becomes step evidence for the later change record.

```bash
pveversion -v
hostnamectl --static
pvecm status
pvecm nodes
corosync-cfgtool -s
ha-manager status
ha-manager config
ha-manager rules list
pvesr list
pvesr status
pvesm status
qm list
pct list
pvenode cert info
```

I will also list both guest owner directories under `/etc/pve/nodes/<OLD_NODE>/`, inspect every attached volume with `pvesm path`, inventory node services & mount points, & search the node-scoped references listed above. If `pvecm status` includes a QDevice flag, I will stop because the official removal procedure requires removing the QDevice first. [Proxmox VE Administration Guide 9.2.3, Remove a Cluster Node, p. 115](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=138)

### Step 2: Evacuate workloads & remove node references

I will migrate or restore guests onto named target storages, then verify the service from its client path. A running process or a moved `.conf` file alone isn't enough. Local volumes, bind data, VLAN reachability, DNS, health endpoints, & monitoring must agree on the new temporary owner.

After the last guest moves, the retiring node must satisfy all of these checks:

- `qm list` & `pct list` show no owned guest.
- `/etc/pve/nodes/<OLD_NODE>/qemu-server/` & `/etc/pve/nodes/<OLD_NODE>/lxc/` contain no guest configuration.
- `pvesr list` contains no source or target reference to the old member.
- `ha-manager status` contains no service on the old member and no `error`, `recovery`, `fence`, or active migration state.
- `ha-manager rules list`, storage restrictions, jobs, mappings, SDN, firewall, & ACLs contain no operational dependency on the old member.
- Every host bind mount, node-local dataset, custom certificate, service configuration, & required SSH public key has a checked copy or a rebuild path.

### Step 3: Power off & remove the old member

I will shut down the retiring node, confirm it no longer answers on either Corosync address, then disable or disconnect its switch port so the old installation can't boot on the Galaxy networks. This is the rollback boundary.

From a remaining healthy node:

```bash
pvecm status
pvecm nodes
pvecm delnode <OLD_NODE>
pvecm status
pvecm nodes
grep -nF -- '<OLD_NODE>' /etc/pve/corosync.conf || true
```

Before `pvecm delnode`, all four remaining members must be online & Galaxy must be quorate. The manual requires the retiring node powered off before deletion and warns that starting its old configuration on the same network can break the cluster. `CS_ERR_NOT_EXIST` from Corosync while deleting an already offline node doesn't by itself mean deletion failed; the deciding checks are `pvecm nodes`, `pvecm status`, & `corosync.conf`. [Proxmox VE Administration Guide 9.2.3, Remove the Cluster Node, p. 116](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=139)

### Step 4: Reinstall with the final name & rejoin

I will update the PXE mapping for the same physical MAC to the final hostname, confirm the NVMe target, enable the switch port on the provisioning profile, & start the installation. The joining node must have no guest configuration because the join overwrites `/etc/pve` & inherits Galaxy's storage configuration. [Proxmox VE Administration Guide 9.2.3, Adding Nodes, p. 112](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=135)

The equivalent manual join shape is:

```bash
pvecm add <HEALTHY_GALAXY_MANAGEMENT_IP> \
  --link0 <THIS_NODE_192.168.70_ADDRESS> \
  --link1 <THIS_NODE_192.168.71_ADDRESS>
```

The Galaxy PXE first-boot automation may issue the join instead. Either path must end with the same two-link Corosync member, cluster-signed node certificate, & five-vote membership.

### Step 5: Restore node services & workloads

I will apply the current Galaxy host baseline, confirm APT sources & installed versions, restore node exporter, NUT where applicable, storage definitions, custom certificate handling, & any hardware mapping. A local storage restriction receives the new name only after `pvesm status` & the backend tool (`lvs`, `zpool status`, or the applicable filesystem check) prove the intended physical storage.

Guests return only after the storage gate passes. Blue's two containers return before `pin-blue-local-storage` is recreated against `blue-node`; Red's CT 842 doesn't start until `/data` is mounted, its content comparison passes, & the bind-mount source path exists.

### Step 6: Remove old member residue

Proxmox intentionally leaves `/etc/pve/nodes/<OLD_NODE>` after deletion. I will first copy any needed configuration, prove both guest directories empty, prove the current shell isn't on the old member, & prove `pvecm nodes` doesn't list it. Only then will I remove that exact old node directory. [Proxmox VE Administration Guide 9.2.3, Cleanup After Node Removal, p. 117](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=140)

I will then remove stale HA-rule references, the unused old SSH public key, old storage node selectors, old node ACL paths, backup-job selectors, mappings, DNS record, monitoring label, PXE/Ansible inventory entry, & SSH Manager alias. I will run a final exact-name search across the active configuration. Historical evidence & dated records keep the name that existed when the event occurred.

## Quorum constraints

Proxmox assigns one vote to each node & requires a majority for writes. Galaxy starts each replacement at five expected votes with quorum 3. While one old member is powered off but not deleted, four votes remain out of five; after `pvecm delnode`, the cluster has four expected votes and still requires three. The new join returns Galaxy to five votes. [Proxmox VE Administration Guide 9.2.3, Quorum, pp. 118-119](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=141)

I won't operate at the mathematical minimum. All four remaining members must be online before deletion, and all five must be online after rejoin before the next replacement begins. If a second member disappears, a Corosync link fails across the remaining cluster, or `pmxcfs` becomes read-only, I stop. I will not use `pvecm expected 1`; the manual presents that command only as a workaround in the nonrecommended separation path, not as part of a healthy five-node rolling replacement. [Proxmox VE Administration Guide 9.2.3, Separate a Node Without Reinstalling, p. 118](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf#page=141)

## Acceptance gate after each replacement

I will not begin the next node until every row passes.

| Check | Required result |
| --- | --- |
| Membership | `pvecm status` reports `Quorate: Yes`, 5 expected votes, 5 total votes, quorum 3; `pvecm nodes` contains the new name once & the old name zero times. |
| Corosync | `corosync-cfgtool -s` shows every peer connected on link 0 & link 1; `corosync.conf` has the new name with the retained `.70` & `.71` addresses. |
| Cluster services | `pve-cluster`, `corosync`, `pvedaemon`, `pveproxy`, `pvestatd`, `pve-ha-lrm`, & `pve-ha-crm` are active on the new member. |
| HA | `ha-manager status` says `quorum OK`; all LRMs have current timestamps; no resource is in `error`, `recovery`, or `fence`; no rule contains the old name. |
| Storage | Every expected pool is active on the correct member; local volumes are present; no `nodes` property contains the old name; no local pool is falsely marked shared. |
| Guests | The planned guest set runs on its accepted owner; storage, network, application health, & monitoring checks pass; no guest config remains under the old node directory. |
| Replication | `pvesr list` & `pvesr status` contain no old member or failed job. |
| Certificates & SSH | `pvenode cert info` matches the new name; TCP 8006 returns the expected GUI/API response; SSH succeeds using the new host key from another member & the management workstation. |
| Monitoring | The new `host="<COLOR>-node"` target is up; the old label is absent from active targets; node, SMART, & NVMe metrics match the installed hardware. |
| Residue | Active Proxmox, PXE, Ansible, Prometheus, DNS, SSH Manager, UniFi alias, current inventory, & diagram configuration contains the new name. Only dated history retains the old name. |

## Rollback & stop conditions

| Phase | Stop condition | Recovery path |
| --- | --- | --- |
| Before workload evacuation | Backup can't be read, target capacity is short, a bind mount or passthrough dependency has no destination, HA isn't idle, or another node is unhealthy. | Leave membership unchanged. Repair the failed prerequisite & repeat the preflight. |
| Workloads moved, old member still joined | Any guest or service fails its client-path validation. | Keep the old member joined. Move or restore the affected guest to a known working member; move it back only when its original storage is still intact & the migration path is supported. |
| Old member powered off, before `pvecm delnode` | Remaining cluster doesn't show four online votes, quorum, & healthy Corosync links. | Keep the switch port disabled while diagnosing. If the old installation is unchanged & still a cluster member, reconnect and boot it only after confirming no duplicate guest can start. |
| After `pvecm delnode` | Old name remains in membership, Corosync configuration is inconsistent, or quorum changes unexpectedly. | Do not boot the old installation. Repair the remaining cluster from a healthy member; preserve the powered-off disk for evidence. |
| New installation can't join | Hostname, time, TCP 22, UDP 5405-5412, link address, certificate, or version check fails. | Keep the new node guest-free. Correct or reinstall it. If I abandon the rename, the supported rollback is another fresh installation with the old `*-server` name followed by a normal join. |
| New member joins but acceptance fails | One link is down, storage is missing, HA is unhealthy, certificate names are wrong, or monitoring remains absent. | Leave workloads on their accepted staging nodes. Remove the empty failed member through the same powered-off `pvecm delnode` procedure if another reinstall is required. Do not start the next color. |
| Workload restore fails after join | Application, disk, bind data, VLAN, or health check differs from the captured state. | Keep the source backup & staging copy. Restore to a healthy joined node or repeat the restore; don't delete the last known-good data copy. |

`pvecm delnode` is the point after which the old installation must never boot on Galaxy again. A rollback of the naming decision after that command is another fresh installation, not a hostname edit.

## Sources

- [Proxmox VE Administration Guide, release 9.2.3, generated 2026-07-03](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf)
- [Proxmox VE Cluster File System reference](https://pve.proxmox.com/pve-docs/chapter-pmxcfs.html)

