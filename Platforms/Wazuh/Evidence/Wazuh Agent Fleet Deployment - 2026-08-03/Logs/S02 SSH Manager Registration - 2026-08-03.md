# S02 SSH Manager Registration

**Created:** 2026-08-03  
**Last updated:** 2026-08-03

**Captured:** 2026-08-03 02:32 EDT  
**Targets:** the two local SSH manager configurations on my workstation, one TOML & one `.env`  
**Mechanism:** Local PowerShell inspection; `apply_patch`; SSH Manager discovery

## Action

I added the three hosts absent from the TOML manager. The `.env` manager already carried all three server records, so I corrected only its `media_01` description from VM 842 to LXC 842.

```text
docker_blue=1
media_01=1
kasm_01=1
DOCKER_BLUE=1
MEDIA_01=1
KASM_01=1
```

The live SSH Manager list then returned:

```text
docker_blue  192.168.40.39  dkadi  key  Debian 13 Docker host (CT 108 on blue-server)
media_01     192.168.40.42  dkadi  key  Media stack Docker host (LXC 842 on red-server)
kasm_01      192.168.78.10  dkadi  key  Kasm Workspaces control plane (Ubuntu 24.04 VM 122 on purple-server), LAB-MGMT VLAN 78
```

No password, private key, token, or concealed credential field entered either file or this transcript.

