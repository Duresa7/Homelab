# Deployment and Verification

**Created:** 2026-09-12  
**Last updated:** 2026-09-12  
**Captured:** 2026-09-12, 11:37 PM to 11:48 PM EDT

Commands ran through the SSH Manager MCP against `docker_blue` (`192.168.40.39`), `blue_server` (`192.168.70.12`), `hq_mgt01` (`192.168.65.12`), `hq_dc01` (`192.168.65.10`), and `ansible_01` (`192.168.40.36`), and through the UniFi Network MCP against the controller. The host clock read `2026-09-12 11:48 PM EDT` at the final readback. Individual per-command timestamps were not captured; the window above is the session boundary.

## S01 Sizing preflight

`blue_server`, exit code 0:

```
               total        used        free      shared  buff/cache   available
Mem:            5811        3039         197          49        2924        2772
Swap:           8191        1876        6315
--- pct 108 ---
cores: 2
memory: 2048
onboot: 1
swap: 1024
--- alloc ---
100 memory: 1024
104 memory: 2048
107 memory: 2048
108 memory: 2048
```

`docker_blue`, exit code 0:

```
               total        used        free      shared  buff/cache   available
Mem:            2048         595         903           2         551        1452
Swap:           1024         370         653
--- containers ---
mcp-ssh-manager|Up 4 hours (healthy)
docker-mcp-gateway|Up 3 days (healthy)
mcp-unifi-network|Up 3 days (healthy)
executor|Up 3 days (healthy)
ssh-manager-mcp-gateway|Up 3 days (healthy)
portainer_edge_agent|Up 3 days
wud|Up 3 days (healthy)
cadvisor|Up 3 days (healthy)
hbbs|Up 3 days
hbbr|Up 3 days
--- disk ---
/dev/mapper/pve-vm--108--disk--0   15G  5.7G  8.3G  41% /
```

## S02 Host preflight

`docker_blue`, exit code 0. Nothing was listening on 80 or 443, and existing Compose projects live under `/opt/docker`:

```
--- listening 80/443 ---
none
--- compose ---
Docker Compose version v5.5.1
--- existing project labels ---
/opt/docker/executor
/opt/docker/rustdesk
```

## S03 Compose file, first attempt and repair

The first staging write used `printf '%s'`, which does not expand the escapes in its argument. `wc -l` returned `0 /tmp/mc-stage/docker-compose.yml` for a 738-byte file. I placed that file before noticing, and the `ls -la` below is that broken placement:

```
total 12
drwxr-xr-x 2 root root 4096 Sep 12 23:44 .
drwxr-xr-x 9 root root 4096 Sep 12 23:44 ..
-rw-r--r-- 1 root root  738 Sep 12 23:44 docker-compose.yml
```

The detached `docker compose pull` against it failed and pulled nothing:

```
go-yaml load error in scanner at L1.C93: mapping values are not allowed in this context
```

I restaged with `printf '%b'`, exit code 0:

```
27 /tmp/mc-stage/docker-compose.yml
services:
  meshcentral:
    image: ghcr.io/ylianst/meshcentral:latest
    container_name: meshcentral
```

Placed over the broken file with `sudo install -m 0644 -o root -g root`, exit code 0 with no output, staging directory removed in the same command. Validated before starting anything, exit code 0:

```
YAML VALID
```

The corrected file is 711 bytes. Verified against the tracked copy after the deployment, exit code 0:

```
3624c1a05e08eb3d08c6b0681c6376f1  /opt/docker/meshcentral/docker-compose.yml
711 /opt/docker/meshcentral/docker-compose.yml
```

The repository copy at `Platforms/MeshCentral/Configuration/docker-compose.yml` returns the same MD5 and the same byte count.

## S04 Pull and start

Run detached as `nohup sh -c 'docker compose pull && docker compose up -d'`, because an Executor integration tool call dies at 60 seconds. Polled result, exit code 0:

```
 Network meshcentral_default Created 
 Container meshcentral Creating 
 Container meshcentral Created 
 Container meshcentral Starting 
 Container meshcentral Started 
--- ps ---
meshcentral|ghcr.io/ylianst/meshcentral:latest|Up 20 seconds|80/tcp, 192.168.40.39:443->443/tcp
```

First-start log, exit code 0. The generated `cert` value was the upstream placeholder:

```
Generating code signing certificate...
Generating Intel AMT MPS certificate...
MeshCentral v1.2.5, Hybrid (LAN + WAN) mode, Production mode.
Code signed MeshService.exe.
MeshCentral Intel(R) AMT server running on myserver.mydomain.com:4433.
Server has no users, next new account will be site administrator.
MeshCentral HTTPS server running on myserver.mydomain.com:443.
--- local https ---
http_code=200
```

## S05 Certificate name corrected

`docker exec meshcentral sed -i 's/"cert": "myserver.mydomain.com"/"cert": "192.168.40.39"/' /opt/meshcentral/meshcentral-data/config.json` followed by `docker restart meshcentral`, exit code 0:

```
7:    "cert": "192.168.40.39",
restarted
```

## S06 Firewall baseline

`hq_mgt01`, exit code 0, before any firewall change:

```
mgt01_to_meshcentral_443=False
```

`obipc` could not be reached to establish the VLAN 60 baseline:

```
Failed to connect to obipc: connect EHOSTUNREACH 192.168.60.102:22
```

## S07 Policy creation

The first call was refused without creating anything:

```
Failed to execute tool: Invalid params for 'unifi_create_firewall_policy': unknown arguments {action, create_allow_respond, destination, enabled, index, ip_version, logging, name, protocol, schedule, source}. Valid arguments: [confirm, policy_data]
```

Resubmitted with the policy inside `policy_data` and `confirm: true`:

```
{
  "success": true,
  "message": "Firewall policy 'Allow Identity to MeshCentral' created successfully.",
  "policy_id": "6aa61ccb80977b56f62ce0bc",
  "details": {
    "action": "ALLOW",
    "create_allow_respond": true,
    "destination": {
      "ips": ["192.168.40.39"],
      "matching_target": "IP",
      "matching_target_type": "SPECIFIC",
      "port": "443",
      "port_matching_type": "SPECIFIC",
      "zone_id": "68b788c0e9f08f1e1b2a2288"
    },
    "enabled": true,
    "index": 10002,
    "ip_version": "IPV4",
    "logging": true,
    "name": "Allow Identity to MeshCentral",
    "protocol": "tcp",
    "schedule": { "mode": "ALWAYS" },
    "source": {
      "ips": ["192.168.65.12", "192.168.65.20"],
      "matching_target": "IP",
      "matching_target_type": "SPECIFIC",
      "port_matching_type": "ANY",
      "zone_id": "6a9eddbbf9e5db2485ad6613"
    }
  }
}
```

## S08 Verification

`hq_mgt01`, exit code 0, after the change:

```
mgt01_to_meshcentral_443=True
```

`hq_dc01`, exit code 0. Same zone, deliberately outside the policy, still refused:

```
dc01_to_meshcentral_443=False
```

`ansible_01`, exit code 0:

```
control_personal_a_443=open
```

`docker_blue`, exit code 0:

```
Up About a minute
MeshCentral Intel(R) AMT server running on 192.168.40.39:4433.
Server has no users, next new account will be site administrator.
MeshCentral HTTPS server running on 192.168.40.39:443.
local_https=200
subject=CN=192.168.40.39
```

Controller policy count after the change, read from the full 200-limit list rather than a filtered page:

```
total_count: 84, allows: 76, blocks: 8
matched name: Allow Identity to MeshCentral, enabled: true, action: ALLOW
```

## S09 Final state

`docker_blue`, exit code 0:

```
2026-09-12 11:48 PM EDT
--- container ---
ghcr.io/ylianst/meshcentral:latest running 2026-09-13T03:45:50.239577073Z
ghcr.io/ylianst/meshcentral@sha256:45873f56b1221cf4c33a65c6a9a8c2ae8b503bd4f605a19f8b1527fbb80a7b6c
--- version ---
MeshCentral v1.2.5, Hybrid (LAN + WAN) mode, Production mode.
--- key config ---
    "cert": "192.168.40.39",
    "port": 443,
    "redirPort": 80,
    "tlsOffload": false,
    "SelfUpdate": false,
    "WebRTC": false,
      "NewAccounts": true,
      "localSessionRecording": true,
--- volumes ---
meshcentral_meshcentral-backups
meshcentral_meshcentral-data
meshcentral_meshcentral-files
meshcentral_meshcentral-web
--- host mem ---
               total        used        free      shared  buff/cache   available
Mem:            2048         716          81           2        1252        1331
--- disk ---
/dev/mapper/pve-vm--108--disk--0   15G  6.7G  7.3G  48% /
```

The container start time is UTC as Docker reports it, and corresponds to 11:45 PM EDT on 2026-09-12.
