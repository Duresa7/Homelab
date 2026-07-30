# S02 Registry Control and Tiles

**Created:** 2026-07-30  
**Last updated:** 2026-07-30

**Capture time:** 2026-07-30 00:58 through 01:03 EDT  
**Target:** `kasm-01`, VM 122  
**Mechanism:** SSH Manager MCP, QEMU guest agent, Docker CLI, Kasm PostgreSQL

## Registry-pull control

Before the change, the Kasm database held:

```text
https://index.docker.io/v1/ | 27 rows
https://kcr.kasmweb.com/v1/ | 4 rows
```

I set `docker_registry=NULL` on all 31 rows and updated the Parrot source with the verified local digest. The transaction returned:

```text
UPDATE 31
UPDATE 1
COMMIT
<null> | 31
```

After restarting `kasm_agent`, it reported healthy and logged no `Pulling docker image` line. `ssd-lvm2` stayed flat.

## Workspace rows

The completed readback was:

```text
Debian - Malware | lab77 | DNS 192.168.77.10 | Malware - VLAN 77 | Lab Sessions
Parrot OS - Full | default network | Full Access - VLAN 78 | All Users
Parrot OS - Normal | lab75 | Quad9 | Normal - VLAN 75 | Lab Sessions
Parrot OS - VPN | lab74 | Quad9 | VPN - VLAN 74 | Lab Sessions
```

Every row was enabled and available, used 2,902,458,368 memory bytes, had no persistent profile, and had a null Docker Registry. The Parrot rows preserved `{"hostname":"kasm"}`.

The obsolete names `Parrot OS 7` and `Debian - Target` both returned a count of zero.

## Service readback

I restarted `kasm_api` and `kasm_manager` to refresh their workspace cache. All seven defined Docker health checks returned healthy; `kasm_proxy` remained running without a health check. The local root and health endpoint returned HTTP `200`, and the agent logged no image pull.
