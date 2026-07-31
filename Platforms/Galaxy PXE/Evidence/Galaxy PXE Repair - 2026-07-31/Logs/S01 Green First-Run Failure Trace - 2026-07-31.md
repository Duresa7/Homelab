# S01 Green First-Run Failure Trace

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Capture date:** 2026-07-31  
**Target:** `ansible-01` and `green-server`  
**Mechanism:** SSH Manager readback of the live PXE journal and state  
**Transcript boundary:** I retained the observed request times and sequence, not the complete original journal output or a target console capture.

## Observed Sequence

```text
03:38:18 UTC  Green requested /v1/boot.
03:38:18 UTC  The server sent boot.ipxe and began the installer asset path.
              Green fetched vmlinuz, initrd.img, and the complete PXE ISO.
03:39:46 UTC  Proxmox posted /v1/answer.
03:39:46 UTC  Proxmox fetched /v1/bootstrap.
Afterward      No first-boot request arrived.
After 40 min   The old record still read installing.
```

## Follow-Up Verification

- `192.168.70.14` did not answer.
- `pvecm status` remained four-node and quorate.
- `pvecm nodes` did not list `green-server`.

The source-side sequence proves delivery through the answer and bootstrap fetch. It does not prove the target-side installer step that stopped.

