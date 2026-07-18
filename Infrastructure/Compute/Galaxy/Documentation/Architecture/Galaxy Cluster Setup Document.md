# Galaxy Cluster Setup Document

**Created:** 2026-05-30  
**Last updated:** 2026-07-17

**Author:** REDACTED_NAME_001
**Date:** 2026-05-30
**System:** Proxmox VE 9.2.2 (kernel 7.0.2-6-pve, Debian Trixie)

**Historical note:** This document records the May 2026 expansion from one node
to three nodes. It was updated on 2026-07-09 after live verification of the
current four-node cluster, including `red-server`, which was added on
2026-07-07. The detailed red node expansion is documented in
[`Galaxy Cluster Red Server Expansion - 2026-07-07.md`](../Change%20Records/Galaxy%20Cluster%20Red%20Server%20Expansion%20-%202026-07-07.md).
The redundant Cluster-Net Corosync link added on 2026-07-10 is documented in
[`Galaxy Cluster-Net Corosync Link Addition - 2026-07-10.md`](../Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md).

---

## 1. Overview

This document records the process I followed to bring my two new Proxmox nodes,
`purple-server` and `blue-server`, into my existing `grey-server` Proxmox cluster
named **Galaxy**. The end goal was a single management plane (one Datacenter view)
covering the original three nodes. As of 2026-07-09, **Galaxy** is a four-node
cluster after the later addition of `red-server`.

The cluster I built is a standard **PVE management cluster** (corosync + pmxcfs):
unified web UI and live/offline migration across the nodes. I did **not** configure
HA or shared storage as part of this work.

### Current node inventory

| Node | Management IP | Role | Corosync link0 | Corosync link1 |
|------|---------------|------|----------------|----------------|
| grey-server | 192.168.70.10 | Existing founder of the `Galaxy` cluster | 192.168.70.10 | 192.168.71.10 |
| purple-server | 192.168.70.11 | New node, joined | 192.168.70.11 | 192.168.71.11 |
| blue-server | 192.168.70.12 | New node, joined | 192.168.70.12 | 192.168.71.12 |
| red-server | 192.168.70.13 | Newest joined expansion node | 192.168.70.13 | 192.168.71.13 |

All four retain management on `192.168.70.0/24` through `vmbr0.70` and have a dedicated Cluster-Net interface on `192.168.71.0/24` through `vmbr0.71`.
Corosync transport is `knet` in passive mode over preferred `link0` on MGMT-A plus redundant `link1` on Cluster-Net.

---

## 2. Starting state

- `grey-server` already hosted a single-node cluster named **Galaxy**
  (corosync `config_version: 4`) and was running all of my production guests.
- `purple-server` and `blue-server` were fresh standalone installs, not part of
  any cluster, and both were empty of VMs and containers.
- All three nodes were on identical PVE versions (9.2.2).
- Current state verified on 2026-07-09: `red-server` is joined as the fourth
  voting node, and the cluster remains quorate.

---

## 3. Pre-flight checks

During the May expansion, I confirmed the cluster prerequisites on all three
nodes:

- **Version parity** — all nodes reported `pve-manager/9.2.2`.
- **Empty joiners** — `qm list` and `pct list` on both new nodes returned no
  guests. A node with existing VMs/CTs cannot join a cluster, so this mattered.
- **Time sync** — `timedatectl` showed `System clock synchronized: yes` on all
  nodes, all in `America/New_York`.
- **Unique hostnames** — `grey-server`, `purple-server`, `blue-server`.

For the July `red-server` expansion, the same checks were repeated before the
join: PVE version parity, no existing guests, active time sync, and a unique
hostname.

```bash
# Run on each node
pveversion | head -1
qm list; pct list
timedatectl | grep -E "synchronized|Time zone"
```

---

## 4. SSH key trust (joiners → founder)

I joined the nodes using the SSH-based method (see Section 7 for why), which
requires passwordless root SSH from each joining node to the founder. I appended
the root public key of `purple-server` and `blue-server` to grey's
`authorized_keys`. The same pattern was used later for `red-server`.

```bash
# On each joining node: grab the root public key
cat /root/.ssh/id_rsa.pub

# On grey-server: authorize joiner keys (idempotent)
grep -qF "root@purple-server" /root/.ssh/authorized_keys \
  || echo "<purple pubkey>" >> /root/.ssh/authorized_keys
grep -qF "root@blue-server" /root/.ssh/authorized_keys \
  || echo "<blue pubkey>" >> /root/.ssh/authorized_keys
grep -qF "root@red-server" /root/.ssh/authorized_keys \
  || echo "<red pubkey>" >> /root/.ssh/authorized_keys
```

I then verified passwordless SSH worked in the joiner → founder direction:

```bash
# On each joiner
ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes root@192.168.70.10 hostname
```

---

## 5. Firewall change (REQUIRED)

> **Warning — this was a blocker and required a security-config change.**

`grey-server` runs the Proxmox firewall (`pve-firewall`, enabled). My active rule
group is `zero_access`, which only permits SSH (port 22) from a short allowlist
and then drops everything else with `IN DROP -p tcp -dport 22`. The May joiners
(`.11` and `.12`) were not on that list, so their SSH to grey was silently dropped
and `pvecm add` could not proceed. The July `red-server` join required the same
allowlist treatment for `.13`.

Important detail: the `ssh_access` and `gui_access_grey` groups in `cluster.fw`
are invoked with a leading `|`, which means they are **disabled**. The group that
actually enforces SSH is `zero_access`. Editing `ssh_access` has no effect.

I backed up the config, then added the cluster node IPs to the **active**
`zero_access` group, immediately before its `DROP SSH` rule:

```bash
# On grey-server
cp /etc/pve/firewall/cluster.fw /root/cluster.fw.bak.$(date +%Y%m%d-%H%M%S)
```

Rules now present in `[group zero_access]` for cluster SSH:

```
IN ACCEPT -source 192.168.70.10 -p tcp -dport 22 -log nolog # grey-server (cluster SSH)
IN ACCEPT -source 192.168.70.11 -p tcp -dport 22 -log nolog # purple-server (cluster SSH)
IN ACCEPT -source 192.168.70.12 -p tcp -dport 22 -log nolog # blue-server (cluster SSH)
IN ACCEPT -source 192.168.70.13 -p tcp -dport 22 -log nolog # red-server (cluster SSH)
```

Applied and validated:

```bash
pve-firewall compile     # must report OK
pve-firewall restart
pve-firewall status      # enabled/running
```

> **Warning — shared firewall inheritance.** `cluster.fw` lives in `/etc/pve`,
> which is replicated cluster-wide. Once `purple-server` and `blue-server` joined,
> they inherited this same firewall and now enforce the `zero_access` allowlist.
> My management IPs were already in the allowlist, so administrative access was
> not interrupted, but this is the reason all four node IPs (including grey's own
> `.10`) need to remain in the group — the new nodes must accept SSH from grey for
> cluster operations and migrations.

Corosync traffic between members is auto-permitted by the PVE firewall once the
nodes are cluster members, so no manual UDP rules were needed.

---

## 6. Joining the nodes

I joined one node at a time and confirmed quorum between each step.

### purple-server

```bash
# On purple-server
pvecm add 192.168.70.10 --link0 192.168.70.11 --use_ssh
```

Successful output ended with `successfully added node 'purple-server' to cluster.`
I confirmed a 2-node quorate cluster on grey before continuing:

```bash
pvecm status   # Nodes: 2, Quorate: Yes
```

### blue-server

```bash
# On blue-server (after priming known_hosts for grey)
ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes root@192.168.70.10 hostname
pvecm add 192.168.70.10 --link0 192.168.70.12 --use_ssh
```

Output ended with `successfully added node 'blue-server' to cluster.`

### red-server

`red-server` was added later, on 2026-07-07, using the same SSH-based join
pattern after adding its root SSH key and firewall allowlist entry:

```bash
# On red-server
pvecm add 192.168.70.10 --link0 192.168.70.13 --use_ssh
```

Output ended with `successfully added node 'red-server' to cluster.`

---

## 7. Cluster authentication note (IMPORTANT)

> **Warning — authentication method.** My first attempts to join over the default
> API method failed. The API connection first rejected an incorrect fingerprint
> (grey uses a custom `pveproxy` certificate, so the relevant fingerprint is the
> one the API itself reports, not the node `pve-ssl.pem` fingerprint), and then
> stopped at `EOF while reading password` because the API join authenticates as
> `root@pam` and requires grey's actual root password.
>
> I avoided the password requirement entirely by using the **`--use_ssh`** flag,
> which performs the join over the SSH key trust established in Section 4 instead
> of the API. This is why the SSH key setup and the firewall rule were
> prerequisites for the join to succeed.

---

## 8. Removing stale node directories

`grey-server` had two phantom node folders under `/etc/pve/nodes/` left over from
an earlier install — `Grey-Server` (capitalized) and `REDACTED_NAME_003`. Both were empty of
guest configs and would otherwise appear as offline ghost nodes in the Datacenter
view. I confirmed they held no guest configs and removed them.

```bash
# On grey-server — confirm no guest configs first
find /etc/pve/nodes/Grey-Server/qemu-server /etc/pve/nodes/Grey-Server/lxc \
     /etc/pve/nodes/REDACTED_NAME_003/qemu-server /etc/pve/nodes/REDACTED_NAME_003/lxc -type f | wc -l   # expect 0

rm -rf /etc/pve/nodes/Grey-Server /etc/pve/nodes/REDACTED_NAME_003
```

After the May cleanup, `/etc/pve/nodes/` contained only `grey-server`,
`purple-server`, and `blue-server`. The current live cluster membership now also
includes `red-server`.

---

## 9. Verification

Current state confirmed from all four nodes via the SSH manager on 2026-07-10:

```bash
pvecm status
pvecm nodes
grep -E "name:|cluster_name:|config_version:" /etc/pve/corosync.conf
corosync-cfgtool -s
```

Results:

- **Cluster name:** Galaxy
- **Config version:** 8
- **Nodes:** 4 (`grey-server`, `purple-server`, `blue-server`, `red-server`)
- **Expected votes / Total votes:** 4 / 4
- **Quorum:** 3
- **Quorate:** Yes

Corosync links:

| Node ID | Votes | Node | Link 0 | Link 1 |
|---------|-------|------|--------|--------|
| 0x00000001 | 1 | grey-server | 192.168.70.10 | 192.168.71.10 |
| 0x00000002 | 1 | purple-server | 192.168.70.11 | 192.168.71.11 |
| 0x00000003 | 1 | blue-server | 192.168.70.12 | 192.168.71.12 |
| 0x00000004 | 1 | red-server | 192.168.70.13 | 192.168.71.13 |

Every node reported every peer connected on both links. The original management GUI endpoints on `192.168.70.10` through `.13` each returned HTTP 200 after the addition.

My existing production guests on `grey-server` (app-01, edge-01, alpha-prod-01,
docker-main) remained running throughout the join and were unaffected.

---

## 10. Backups created during this work

- `grey-server:/root/cluster.fw.bak.*` — firewall config prior to the
  `zero_access` change.
