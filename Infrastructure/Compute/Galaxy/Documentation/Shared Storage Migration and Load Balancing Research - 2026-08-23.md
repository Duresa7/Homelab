# Proxmox Shared Storage Migration and Load Balancing Research

**Created:** 2026-08-23  
**Last updated:** 2026-08-23

**Research date:** 2026-08-23  
**Platform observed:** Proxmox VE 9.2.6, kernel `7.0.14-8-pve`  
**Status:** Research complete; no implementation started

## Scope and evidence boundary

I researched two related questions: what shared storage would make Galaxy guests portable between nodes, and what Proxmox VE 9.2's new cluster load balancer can do with that portability. I compared the current five-node state with the Proxmox VE 9.2 release material, current 9.2.4 administration guide, command references, and storage documentation. Proxmox released 9.2 on 2026-05-21 and introduced the dynamic load balancer in that release ([Proxmox VE 9.2 release announcement](https://www.proxmox.com/en/about/company-details/press-releases/proxmox-virtual-environment-9-2)).

I also made a read-only live check of the cluster around 7:03 PM EDT on 2026-08-23. I made no storage, HA, guest, network, or CRS change. I did not retain a raw API transcript because it included certificate fingerprints that do not belong in this public repository. The tables below retain only the non-sensitive results needed for this decision.

## Conclusion

I should not enable automatic load balancing yet. Galaxy has no shared guest storage, every busy guest on Grey is outside the HA stack, and the only two HA resources are CT 107 and CT 108 under a strict rule that allows only Blue. The new balancer therefore has no useful migration candidate and cannot reduce Grey's current load.

The practical path is an external, non-Galaxy NFS datastore backed by redundant storage, on a storage path physically separate from Corosync if the intended result is HA. NFS is the simplest Proxmox-native pilot because it supports both VM images and LXC root directories, mounts through the Proxmox storage plugin, and is shared by definition ([Proxmox NFS backend](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_nfs)). A single NFS server can provide planned migration and steady-state placement, but it remains a storage single point of failure and cannot turn Galaxy into end-to-end HA.

I should first use a disposable VM and LXC to validate the datastore and migration path. The first production volumes to move should then be the 47 GiB of provisioned root storage for CT 107 and CT 108, because those are already HA-managed and their local disks caused the 2026-07-20 stranding incident. I should keep their strict Blue rule until the shared volumes, target-node mounts, restart migration, and controlled recovery have all passed. I should also set their per-resource `auto-rebalance` to off before giving them more than one eligible node because an LXC move is a stop, relocate, and start operation, not a live migration.

After storage works, selected QEMU VMs can become the automatic-balancing pilot. All current VMs use CPU type `host` on AMD Grey, while the other four nodes are Intel. I need a tested cluster-compatible virtual CPU model or a same-vendor placement rule before any cross-vendor live migration. Shared storage alone does not solve that requirement.

## Observed local state

### Cluster and CRS

| Item | Observed state on 2026-08-23 |
| --- | --- |
| Cluster | Five nodes, quorate |
| Proxmox version | `pve-manager/9.2.6` |
| Running kernel on Grey | `7.0.14-8-pve` |
| HA state | Healthy; fencing armed |
| HA resources | `ct:107` and `ct:108`, both started on `blue-server` |
| HA placement | Strict node-affinity rule `pin-blue-local-storage`, Blue only |
| `/etc/pve/datacenter.cfg` | Only `keyboard: en-us` |
| CRS scheduler | Documented default `basic` |
| Automatic rebalancing | Documented default off |
| Rebalance on start | Documented default off |

The HA configuration matches the [current LXC inventory](../../../../Operations/Inventory/Galaxy/LXCs.md) and the [local-storage stranding record](Troubleshooting/HA%20Local-Storage%20Stranding%20of%20CT%20107%20and%20CT%20108%20After%20a%20Blue-Server%20Shutdown%20-%202026-07-20.md). The strict rule is a containment control for node-local storage, not a failover design.

### Point-in-time node load

| Node | Memory use | CPU use | Relevant capacity context |
| --- | ---: | ---: | --- |
| `grey-server` | about 79% | about 26% | 62.72 GiB RAM; all seven current VMs and two LXCs are assigned here |
| `blue-server` | about 42% | about 6% | 5.68 GiB RAM; CT 104, CT 107, and CT 108 have 5 GiB configured between them |
| `green-server` | about 30% | about 5% | 15.46 GiB RAM; CT 123 has 12 GiB configured |
| `red-server` | about 21% | about 4% | 15.46 GiB RAM; CT 842 has 4 GiB configured |
| `purple-server` | about 12% | about 2% | 15.46 GiB RAM; no current guest |

This is one observation, not a utilization baseline. The [guest resource tuning record](Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md) used 14.8 days of Prometheus history and remains the better source for workload headroom. The point-in-time check does show why the question matters: Grey carries the load while Purple is empty, but those Grey guests are not eligible for the HA balancer.

### Storage

The live `/etc/pve/storage.cfg` contains no shared storage. It defines the ordinary per-node `local` and `local-lvm` entries, plus Grey-only `ssd-lvm1` and `hddpool-1`, and Purple-only `ssd-lvm2`. The [node storage inventory](../../../Hardware/Nodes.md#cluster-storage) records the current capacities and explains that a cluster-wide storage definition does not make local contents common between nodes.

| Storage | Backing | Scope | Shared guest storage |
| --- | --- | --- | --- |
| `local` | Per-node directory | Each node's own filesystem | No |
| `local-lvm` | Per-node LVM-thin | Each node's own thin pool | No |
| `ssd-lvm1` | Grey 1.82 TiB SATA SSD | Grey only | No |
| `hddpool-1` | Grey single 1.82 TiB HDD ZFS pool | Grey only; about 80% used in the last inventory | No |
| `ssd-lvm2` | Purple 232.89 GiB SATA SSD | Purple only; empty | No |

Proxmox distributes `storage.cfg` to every node, but its documentation says local entries with the same storage ID can have physically different contents. The `shared` property only labels storage that is already shared and does not make local data accessible elsewhere ([storage configuration and common properties](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#_storage_configuration)). LVM-thin itself cannot be shared between nodes ([LVM-thin backend](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_lvmthin)).

### Network

Galaxy has MGMT-A on `vmbr0.70` and Corosync Cluster-Net on `vmbr0.71`. Both are VLAN interfaces on the Proxmox trunk in the current [Galaxy network reference](../Configuration/network.md). No separate physical storage or migration fabric is documented, and the live `datacenter.cfg` has no migration-network setting.

Proxmox defaults migration traffic to the cluster-communication network when no migration network is set and calls that arrangement suboptimal because bulk migration can disrupt latency-sensitive cluster traffic. It supports a dedicated CIDR through the cluster-wide `migration` setting ([migration network](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#pvecm_migration_network)). The Corosync guidance is stronger: storage should not share the Corosync network except as a low-priority fallback on a redundant design ([Corosync network requirements](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#pvecm_cluster_network_requirements)).

### Guest portability constraints

| Guests | Current constraint | Result before remediation |
| --- | --- | --- |
| VMs 105, 106, 109, 116, 121, 200, and 401 | All guest volumes are local to Grey; all VMs use CPU type `host`; VMs 106 and 109 also have node-local ISO attachments recorded | Not safe for automatic cross-vendor live movement |
| CT 107 and CT 108 | HA-managed but roots are on Blue `local-lvm`; strict Blue-only rule | No failover target and no balancing target |
| CT 100, CT 104, and CT 123 | Managed local root volumes and no node-local data/device dependency recorded | Storage-portable after root migration, but any later LXC balancing causes a restart |
| CT 110 | Root on Grey `local-lvm`; `/data` on Grey `hddpool-1` | Grey-bound until both volumes and their capacity are portable |
| CT 842 | Root on Red `local-lvm`; Red HDD bind mount; Intel render device and TUN device | Red-bound; exclude from automatic movement |
| Templates 101 and 9000 | Local to Grey and not running | Useful to move for cluster-wide provisioning, but not load-balancer candidates |

The details come from the living [VM inventory](../../../../Operations/Inventory/Galaxy/VMs.md) and [LXC inventory](../../../../Operations/Inventory/Galaxy/LXCs.md). Proxmox treats bind and device mounts as unmanaged by its storage subsystem, and their contents are not included in `vzdump` ([container mount points](https://pve.proxmox.com/pve-docs/chapter-pct.html#_storage_backed_mount_points)).

## Documented Proxmox VE 9.2 behavior

### Scheduler modes and scheduling points

The Cluster Resource Scheduler selects placements for HA resources. Its mode changes the usage data behind that choice ([CRS scheduling modes](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#_crs_scheduling_mode)).

| Mode | Input | Default |
| --- | --- | --- |
| `basic` | Number of active guests on each node | Yes |
| `static` | Configured CPU and memory quotas for active guests | No |
| `dynamic` | Average actual CPU and memory use plus configured quotas | No |

Recovery after a node failure and placement changes caused by HA rule edits are always scheduling points. Rebalance on start is a separate opt-in action. The guide labels static/dynamic rebalance-on-start behavior as technology preview; that warning appears in the rebalance-on-start section, not as a label on the entire automatic load-balancer section ([CRS scheduling points](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#ha_manager_crs_scheduling_points)).

### Automatic load balancing

The automatic balancer is a separate global switch and requires `static` or `dynamic` scheduler mode. Its node-load calculation includes all active guests, including guests outside HA, but only started HA resources are migration candidates. It moves candidates sequentially and obeys node and resource affinity rules. Proxmox documents automatic migration of non-HA guests as future work ([CRS load balancer](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#_crs_load_balancer), [`pve-ha-manager` node-usage construction](https://git.proxmox.com/?p=pve-ha-manager.git;a=blob;f=src/PVE/HA/Manager.pm;hb=c73364c19d5317e6df5bb1c1b727d080a5e897ef#l435), and [migration-candidate selection](https://git.proxmox.com/?p=pve-ha-manager.git;a=blob;f=src/PVE/HA/Manager.pm;hb=c73364c19d5317e6df5bb1c1b727d080a5e897ef#l138)).

| Setting | 9.2 default | Meaning |
| --- | ---: | --- |
| Global `ha-auto-rebalance` | `0` | Automatic balancing disabled |
| Per-resource `auto-rebalance` | `1` | Resource is eligible once global balancing is enabled |
| Imbalance threshold | 30% | Imbalance must exceed this value |
| Hold duration | 3 HA rounds | Threshold must persist for this many rounds; an HA round is about 10 seconds |
| Minimum improvement | 10% | Predicted relative imbalance reduction required before a move |
| Method | `bruteforce` | Migration-scoring method; `topsis` is the alternative |
| Rebalance on start | `0` | Starting an HA resource does not trigger best-node relocation by default |

The exact schema and defaults are in [`datacenter.cfg(5)`](https://pve.proxmox.com/pve-docs/datacenter.cfg.5.html). A per-resource opt-out matters here: once the global switch is enabled, an existing HA resource is eligible by default unless I set `auto-rebalance=0` or leave it without an allowed target.

The score uses CPU and memory. The documented inputs do not include storage latency, storage queue depth, network throughput, service criticality, NUMA topology, or recovery priority. I therefore cannot treat a lower CRS imbalance score as proof that an I/O-heavy guest such as Splunk or Wazuh belongs on shared NFS.

### Migration and shared storage

Shared storage is an HA requirement in Proxmox's own checklist, along with at least three nodes, hardware redundancy, and reliable fencing. If a dependency exists only on some nodes, the guide says to restrict the HA resource to that subset with a strict node-affinity rule ([HA requirements](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#_requirements)).

Shared storage is not required for every planned VM migration. Proxmox can copy local VM disks over the network during an online migration if other requirements are met. Shared storage removes that disk-copy phase because source and target already see the same image, which makes live migration much faster ([storage overview](https://pve.proxmox.com/pve-docs/chapter-pvesm.html)). A failed source node cannot supply its local disk, so local-disk live-copy support does not provide HA recovery.

Running LXCs cannot live-migrate. Proxmox restart migration shuts the container down, copies or relocates its volumes, and starts it on the target. With shared storage there is no root-volume copy, but the stop and start remain ([container migration](https://pve.proxmox.com/pve-docs/chapter-pct.html#pct_migration)). That makes repeated automatic movement inappropriate for network-control and relay containers until I have measured their reconnect behavior.

VM live migration also has a CPU boundary. Proxmox says CPUs from different vendors might work depending on the selected VM CPU model, but the result is not guaranteed. Its CPU guide says `host` exposes the source CPU's exact flags and recommends the lowest compatible virtual QEMU CPU type for mixed Intel/AMD live migration ([VM CPU type](https://pve.proxmox.com/pve-docs/chapter-qm.html#_cpu_type) and [live-migration requirements](https://pve.proxmox.com/pve-docs/chapter-qm.html#_requirements)).

## Shared-storage option analysis

### External NFS

NFS is the best first implementation for Galaxy. The Proxmox NFS plugin supports both `images` and `rootdir`, marks the datastore shared, mounts it without an `/etc/fstab` entry, tests server availability, and can enumerate exports ([NFS backend](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_nfs)). It fits a small mixed-hardware cluster better than building a distributed storage system from the current node disks.

The external storage host must be outside Galaxy if its purpose is to survive a Galaxy node failure. Exporting Grey's `hddpool-1` as NFS would make planned movement possible while Grey is healthy, but Grey would remain both a compute concentration and the storage failure domain. Its single-disk pool was also about 80% used at the last inventory. I do not recommend that as HA storage.

NFS does not provide native Proxmox storage snapshots. VM snapshots and clones on NFS use `qcow2`, and Proxmox warns that internal `qcow2` snapshot creation or deletion on network storage can block a running VM and take a long time for large disks. Containers do not gain that `qcow2` snapshot path ([storage feature table and snapshot warning](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#_storage_types)). The current no-snapshot policy means this is not a lost feature, but I should not adopt NFS with an assumption that cheap snapshots will become the recovery plan.

### iSCSI with shared LVM

iSCSI with thick LVM can provide shared block storage for VMs and containers. Proxmox implements cluster-wide locking when LVM is marked shared, and Proxmox VE 9 offers VM snapshot volume chains as a technology-preview feature. The design is more complex than NFS and commonly needs multipathing; direct `iscsidirect` is VM-only ([iSCSI and LVM backends](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_open_iscsi)). I would evaluate it only if the selected storage appliance has a stronger iSCSI implementation than NFS and I can build redundant paths.

### In-cluster Ceph

I do not recommend Ceph on Galaxy's current hardware. Proxmox recommends at least three preferably identical servers, at least 8 GiB of memory per OSD for good performance, at least 10 Gbps used exclusively for Ceph, physical separation from Corosync, and at least 12 OSDs evenly distributed across at least three nodes ([healthy Ceph cluster recommendations](https://pve.proxmox.com/pve-docs/chapter-pveceph.html#_recommendations_for_a_healthy_ceph_cluster) and [OSD guidance](https://pve.proxmox.com/pve-docs/chapter-pveceph.html#pve_ceph_osd_create)).

Galaxy has heterogeneous node and disk capacities, Blue has only 5.68 GiB of usable RAM, Green's only spare HDD failed its extended test, the other non-boot disks already have local roles, and the cluster does not have 12 eligible OSDs or a documented 10 Gbps exclusive physical network. Adding Ceph now would consume the capacity the balancer is supposed to recover and would put storage recovery traffic on an unsuitable fabric.

### ZFS replication

Proxmox storage replication is an alternative for local ZFS, not shared storage. It incrementally copies snapshots to another node, can reduce later migration time, and can participate in HA, but it is asynchronous and can lose changes between the last sync and a source-node failure. It supports only local `zfspool` storage and requires the same storage ID at the target ([storage replication](https://pve.proxmox.com/pve-docs/chapter-pvesr.html)). Galaxy currently has one local ZFS pool on Grey and no matching target pool, so this is not an immediate path.

## Analysis and inference for Galaxy

### Why the current balancer is inert

The balancer can only select running, movable HA resources. Galaxy's non-HA Grey guests contribute to Grey's node-load score, but the balancer cannot select them for migration. CT 107 and CT 108 are HA resources, but their strict rule leaves no target besides their current node. Changing from `basic` to `dynamic` or enabling global automatic balancing today would therefore add decision machinery without adding a legal move.

### Why shared storage is necessary but insufficient

Shared storage fixes disk visibility and removes disk-copy time from VM migration. It does not fix these other limits:

- All current QEMU VMs expose AMD Grey's `host` CPU flags while every other node is Intel.
- Blue and Green have little configured-memory headroom, and Galaxy does not have enough spare non-Grey RAM to absorb every Grey workload at its configured maximum after a Grey failure.
- CT 110 and CT 842 have node-local data or device dependencies outside their root volumes.
- LXC balancing is restart migration and creates service interruption.
- The CRS score does not account for shared-storage I/O or network saturation.
- A single NAS moves the single point of failure from one Proxmox node to the storage appliance.

Galaxy can support selective HA and selective load distribution after storage work. It cannot claim N+1 capacity for every current Grey guest without target-node memory upgrades, workload reductions, or a narrower protected set.

### Workload eligibility

I would divide the current guests into three sets.

| Set | Guests | Initial policy |
| --- | --- | --- |
| Existing HA gap | CT 107, CT 108 | Move roots to shared storage; validate recovery; keep automatic rebalancing off initially |
| Potential QEMU balancing pilot | VM 116, VM 121, VM 401 | Move all volumes, adopt a compatible CPU model, test migration, then add one at a time to HA |
| Manual or node-bound initially | VM 105, VM 106, VM 109, VM 200; CT 100, CT 104, CT 110, CT 123, CT 842 | Keep outside automatic movement until capacity, I/O, service criticality, restart behavior, and local dependencies are resolved |

The QEMU pilot list is a portability shortlist, not a criticality decision. VM 121 is ingress infrastructure, VM 116 carries applications, and VM 401 carries production voice/game services. I need an explicit recovery objective and a maintenance test for each before enrollment. Splunk and Wazuh should remain manual until NFS latency under indexing load is measured because the CRS will not score that bottleneck.

## Recommended path

1. Build a dedicated external storage appliance with mirrored SSD capacity, UPS coverage, and a storage network that does not share Corosync's physical path. If the appliance itself is not redundant, describe the result as planned mobility and load distribution, not full HA.
2. Add one NFS datastore through the Proxmox storage plugin for `images,rootdir`. Do not set `shared=1` on an existing local storage and do not use an ordinary directory entry to disguise a mount.
3. Validate the datastore from every intended node with a disposable VM and LXC before moving a production volume.
4. Move CT 107 and CT 108 roots first, but keep `pin-blue-local-storage` in place until mount, restart-migration, and recovery tests pass. Rename the rule when its reason is no longer local storage.
5. Set `auto-rebalance=0` on CT 107 and CT 108 before expanding their allowed nodes. Shared storage should first solve failover; it should not cause routine restart migrations of the network control plane.
6. Select one small QEMU production pilot. Move every attached disk to NFS, remove or move local ISO attachments, adopt a tested compatible virtual CPU model, and prove offline and online movement between the intended AMD and Intel targets.
7. Add only that VM to HA under a strict eligible-node rule. Prove start, migrate, relocate, maintenance mode, and controlled recovery before adding another resource.
8. Use `static` CRS first with global automatic balancing off. This improves recovery placement from the current guest-count-only default without authorizing background migrations.
9. After the shared storage and HA tests have a stable observation window, enable automatic balancing for selected QEMU resources only. Evaluate `dynamic` mode after Prometheus history confirms that the actual-use signal is useful and storage latency remains within the accepted bound.

## Prerequisites

### Storage appliance

- Usable capacity sized from actual allocated bytes, current working sets, and growth, not only the guests' thin-provisioned virtual sizes.
- Mirrored or otherwise redundant media with health monitoring and tested replacement behavior.
- UPS coverage and an intentional boot order relative to Proxmox nodes.
- NFS export restricted to the storage network and the five node addresses.
- Monitoring for capacity, latency, server reachability, filesystem health, and NFS errors.
- A documented answer for whether the storage controller or appliance is a tolerated single point of failure.

### Network

- One address per node in a dedicated storage/migration CIDR.
- A physical path separate from both Corosync links for the HA design. A new VLAN on the existing trunk is acceptable only as a bounded pilot after applying bandwidth limits and monitoring Corosync latency.
- Measured throughput, latency, packet loss, MTU consistency, and simultaneous read/write behavior from all five nodes.
- A cluster-wide secure migration network setting after the new path passes. Storage migration remains encrypted, and the current default has no dedicated network.

### Guest portability

- Every VM disk, EFI disk, TPM state disk, cloud-init disk, and required ISO either on shared storage or detached.
- No unmanaged host path, device passthrough, hook script, or node-only mapping on a guest declared portable.
- A virtual CPU model supported across AMD Grey and the intended Intel targets, followed by a cold restart and live-migration test.
- The same bridges and VLANs available on every allowed node.
- A strict eligible-node rule that excludes nodes without enough RAM, CPU, network, or device capacity.

### Recovery and capacity

- A selected protected workload set whose configured maximums fit on the remaining eligible nodes with host and storage headroom.
- Per-workload recovery time and recovery point objectives.
- A temporary rollback copy or retained source volume during each move when capacity permits, removed after the new volume and service pass. The workspace keeps no standing backups, so I must start with reconstructable workloads or explicitly accept rebuild-only recovery where a temporary independent copy is impossible.
- Acknowledgement that shared storage is not a backup and that one corrupted, deleted, or full datastore can affect every guest on it. Proxmox warns that a full thin or sparse datastore can return guest I/O errors and corrupt filesystems ([thin-provisioning capacity warning](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#_thin_provisioning)).

## Migration approach

### Phase 1: prove the platform

1. Record the NFS appliance, export, storage network, redundancy, and monitoring design before adding it to Proxmox.
2. Add the NFS storage with a new storage ID and `images,rootdir` content.
3. Confirm it is active from every intended node and that all nodes resolve the same export to the same data.
4. Test sustained and random I/O, latency, sparse allocation, discard behavior, and a controlled server/network interruption. Confirm how guests and Proxmox tasks behave when NFS pauses and returns.
5. Create a disposable small VM and LXC. Move them across each eligible node, including one AMD-to-Intel QEMU path, and remove them after the test.

### Phase 2: close the existing HA storage gap

1. Confirm CT 107 and CT 108 have no unrecorded bind mount, device mount, local hook script, or node-only dependency.
2. Set per-resource automatic rebalancing off.
3. Move one root volume at a time during a maintenance window, leaving the other network service running.
4. Verify the container starts on Blue from the shared root and that NetBird, Nginx Proxy Manager, RustDesk, monitoring, routing, and external reachability return.
5. Keep the Blue-only rule until the same container passes a restart migration to one target node and back.
6. Expand the strict rule to tested nodes only, then perform a controlled HA recovery test. Do not test both containers simultaneously.
7. Remove the old local volume only after the shared copy and rollback path are no longer needed.

### Phase 3: make selected VMs portable

1. Choose one VM from 116, 121, or 401 based on accepted impact and rebuildability.
2. Move all of its volumes to NFS while leaving no local ISO or auxiliary volume attached.
3. Replace CPU type `host` with the lowest compatible virtual model established from the 9.2 cluster CPU flag view and live node checks.
4. Restart and test the workload on Grey, then cold-migrate it to an Intel node.
5. Test a live migration between the exact allowed node pair while watching application sessions, conntrack behavior, storage latency, migration throughput, and Corosync health.
6. Add the VM to HA with a strict target set and `auto-rebalance=0`. Test HA recovery before allowing automatic movement.

### Phase 4: stage the 9.2 scheduler

1. Change CRS from `basic` to `static` with global auto rebalancing still off.
2. Observe HA status, node scores, recovery placement in controlled tests, and Prometheus node/storage history.
3. Enable `auto-rebalance` for the single QEMU pilot while every other HA resource remains opted out.
4. Enable global automatic balancing with conservative values. The documented 30% threshold, three-round hold, 10% improvement margin, and `bruteforce` method are reference defaults, not proof that they fit Galaxy.
5. Allow one automatic move, validate it end to end, and stop the trial if there is repeat movement, service impact, NFS latency, migration saturation, or Corosync jitter.
6. Evaluate `dynamic` only after the static pilot is stable. Add one resource at a time rather than enrolling the cluster as a batch.

## Risks and stop conditions

| Risk | Consequence | Control or stop condition |
| --- | --- | --- |
| Single NFS appliance | All shared guests lose storage together | Use redundant storage and power; do not claim HA if the controller remains singular |
| Storage and Corosync share a physical link | Migration or guest I/O can cause latency and quorum loss | Separate the physical path; stop on Corosync jitter, retransmits, or link saturation |
| Cross-vendor `host` CPU migration | QEMU can stop or the guest can fail | Adopt and test a compatible virtual CPU model before HA enrollment |
| Insufficient failover RAM | HA selects a target that cannot safely carry the workload | Use strict capacity-based node rules and reserve headroom |
| Automatic LXC relocate | Network or application interruption | Keep LXC `auto-rebalance=0`; measure restart and reconnect time |
| Unmanaged bind/device dependency | Guest starts without data or hardware, or cannot migrate | Keep CT 110 and CT 842 node-bound until every dependency is redesigned |
| CRS ignores storage/network pressure | CPU/memory balance worsens I/O or network contention | Exclude I/O-heavy guests until storage telemetry and thresholds exist |
| NFS fills | Guest I/O errors and possible filesystem corruption | Capacity alerts, growth reserve, and a tested emergency response |
| No standing backup | Migration or shared-storage fault can become permanent loss | Retain a temporary rollback copy where possible and start with reconstructable guests |
| Automatic migration churn | Repeated moves create risk without useful improvement | Never set both threshold and improvement margin to zero; stop on repeat movement |

## Open validation items

- [ ] Identify the proposed external NFS appliance, controller redundancy, usable media, UPS assignment, and failure domain.
- [ ] Measure each Proxmox node's physical NIC count, link speed, driver, switch path, and ability to add a separate storage interface.
- [ ] Decide whether the first goal is planned mobility, automatic steady-state balancing, node-failure HA, or all three. The storage design differs for each.
- [ ] Capture actual allocated and written bytes per guest volume plus 30-day growth before sizing the datastore.
- [ ] Build an N+1 memory and CPU placement matrix for the selected protected workloads. Blue and Green should not be treated as general failover targets in their current allocations.
- [ ] Select and test the lowest compatible QEMU CPU model across the Ryzen 7 3700X, i5-7500T, and i5-8500T nodes.
- [ ] Confirm VMs 106 and 109 no longer require their recorded local ISO attachments before declaring them portable.
- [ ] Confirm CT 107 and CT 108 have no live dependency absent from the inventory and measure full service recovery after restart migration.
- [ ] Define acceptable downtime for each LXC before any automatic-rebalance decision.
- [ ] Benchmark NFS with Splunk and Wazuh-like I/O before considering VM 109 or VM 200.
- [ ] Decide which QEMU VM is the first production balancing pilot and document its recovery objective.
- [ ] Confirm current `pve-ha-manager` package behavior and changelog on 9.2.6 immediately before enabling the feature. The current online guide used for this report identifies itself as version 9.2.4.
- [ ] Decide how I will obtain a temporary verified recovery copy for each production volume move under the current no-standing-backup policy.
