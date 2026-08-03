# S02 Rollback and Verification

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../../Kasm-Workspaces-Incident-Report-2026-07-29-Thin-Pool-Exhaustion.md)

**Capture time:** 2026-07-29 22:42 through 22:56 EDT  
**Targets:** `purple-server`, VM 122 `kasm-01`, Kasm NPM hostname  
**Mechanism:** SSH Manager MCP and local PowerShell

## Step 1: Stop and roll back VM 122

I issued:

```bash
qm stop 122
qm status 122
```

Both commands returned exit code `0`; the status read:

```text
status: stopped
```

I then issued:

```bash
qm rollback 122 baseline-tiles-2026-07-28
```

The command returned exit code `0`:

```text
Logical volume "vm-122-disk-1" successfully removed.
WARNING: You have not turned on protection against thin pools running out of space.
WARNING: Set activation/thin_pool_autoextend_threshold below 100 to trigger automatic extension of thin pools before they get full.
Logical volume "vm-122-disk-1" created.
WARNING: Sum of all thin volume sizes (<550.02 GiB) exceeds the size of thin pool ssd-lvm2/ssd-lvm2 and the size of whole volume group (232.88 GiB).
Logical volume ssd-lvm2/vm-122-disk-1 changed.
Logical volume "vm-122-disk-0" successfully removed.
WARNING: You have not turned on protection against thin pools running out of space.
WARNING: Set activation/thin_pool_autoextend_threshold below 100 to trigger automatic extension of thin pools before they get full.
Logical volume "vm-122-disk-0" created.
WARNING: Sum of all thin volume sizes (<550.02 GiB) exceeds the size of thin pool ssd-lvm2/ssd-lvm2 and the size of whole volume group (232.88 GiB).
Logical volume ssd-lvm2/vm-122-disk-0 changed.
```

The immediate storage readback showed:

```text
ssd-lvm2        228.11 52.51 2.40 ssd-lvm2 twi-aotz--
vm-122-disk-1   200.00 58.82      ssd-lvm2 Vwi-a-tz--
```

## Step 2: Start the guest and allow database recovery

I issued:

```bash
qm start 122
qm guest cmd 122 ping
```

Both commands returned exit code `0`. Proxmox generated the cloud-init ISO, and the guest agent answered.

PostgreSQL reported:

```text
< 2026-07-30 02:50:03.369 UTC     1  00000 2026-07-30 02:45:52 UTC 6a6abae0.1:>LOG:  database system is ready to accept connections
```

The service containers recovered through their existing restart policies. I didn't restart a container manually.

## Step 3: Verify Kasm, storage, and NPM

The final container command was:

```bash
qm guest exec 122 -- /usr/bin/docker ps --format '{{.Names}}|{{.Status}}'
```

It returned guest exit code `0`:

```text
kasm_proxy|Up About a minute
kasm_agent|Up About a minute (healthy)
kasm_guac|Up About a minute (healthy)
kasm_api|Up About a minute (healthy)
kasm_manager|Up About a minute (healthy)
kasm_rdp_https_gateway|Up 23 seconds (healthy)
kasm_rdp_gateway|Up 30 seconds (healthy)
kasm_db|Up 8 minutes (healthy)
```

The local API request returned:

```text
{"ok":true}
```

The final thin-pool and guest filesystem readbacks were:

```text
ssd-lvm2        228.11 54.74 2.59 ssd-lvm2 twi-aotz--
vm-122-disk-1   200.00 59.90      ssd-lvm2 Vwi-aotz--

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       193G  121G   73G  63% /
```

At 2026-07-29 22:56:13 EDT, I issued both NPM requests from Jedi PC. The PowerShell command exited `0`:

```text
root=200|0.031507
health=200|0.031085
```
