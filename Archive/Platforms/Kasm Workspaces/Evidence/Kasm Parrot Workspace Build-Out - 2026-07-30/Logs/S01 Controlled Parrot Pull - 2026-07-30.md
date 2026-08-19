# S01 Controlled Parrot Pull

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Capture time:** 2026-07-30 00:49 through 00:57 EDT  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP, Proxmox CLI, QEMU guest agent, Docker CLI

## Pull result

With `kasm_agent` stopped, I ran one explicit pull:

```text
docker pull kasmweb/parrotos-7-desktop:1.19.0-rolling-daily
```

Docker returned:

```text
Digest: sha256:8dc7c7821c3e69f6e7d4bbef0a55d84f6e4c784851fa729773b273d72dddd736
Status: Downloaded newer image for kasmweb/parrotos-7-desktop:1.19.0-rolling-daily
```

Image inspection returned:

```text
ID: sha256:8dc7c7821c3e69f6e7d4bbef0a55d84f6e4c784851fa729773b273d72dddd736
Size: 13,670,381,122 bytes
```

`docker system df -v` reported 40.92 GB unique for the expanded Parrot image. The guest filesystem rose from 116 GB to 154 GB used, which is consistent with the expanded figure rather than the image-inspection size.

## Storage result

```text
ssd-lvm2 before pull: 51.46 percent
ssd-lvm2 after pull: 67.44 percent
Thin-pool increase: 15.98 percentage points, about 36.45 GiB
Guest before pull: 77 GB available
Guest after pull: 39 GB available
```

The pool retained about 74 GiB of physical headroom. The pull process exited zero, and no second image pull ran.
