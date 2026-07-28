# S02 Guest and Kasm Final Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture timestamp:** 2026-07-28T14:40:55-04:00  
**Target:** `kasm-01`, VM 122  
**Mechanism:** SSH Manager MCP to `purple-server`, Proxmox QEMU guest agent, guest Bash, default working directory

## Exact command

```bash
qm guest exec 122 -- /bin/bash -lc 'date -Is; printf "shim_service_enabled="; systemctl is-enabled kasm-lab-shims.service; printf "shim_service_active="; systemctl is-active kasm-lab-shims.service; printf "docker_service_active="; systemctl is-active docker.service; echo "--- containers ---"; docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}" | sort; echo "--- images ---"; printf "all="; docker image ls -aq | sort -u | wc -l; printf "tagged="; docker image ls --format "{{.Repository}}:{{.Tag}}" | grep -vc "<none>"; printf "dangling="; docker image ls -qf dangling=true | wc -l; echo "--- lab addresses ---"; ip -br addr | grep -E "enp6s(19|20|21)|shim(74|77|79)"; echo "--- lab routes ---"; ip route show | grep -E "192\.168\.(74|77|79)\.208/28"; echo "--- docker networks ---"; for n in lab74 lab77 lab79; do docker network inspect "$n" --format "{{.Name}}|{{index .Options \"parent\"}}|{{(index .IPAM.Config 0).Subnet}}|{{(index .IPAM.Config 0).Gateway}}|{{(index .IPAM.Config 0).IPRange}}"; done; echo "--- API health ---"; curl -ksS https://127.0.0.1/api/__healthcheck'
```

## Complete guest-agent result

```json
{
  "exitcode": 0,
  "exited": 1,
  "out-data": "2026-07-28T14:40:55-04:00\nshim_service_enabled=enabled\nshim_service_active=active\ndocker_service_active=active\n--- containers ---\nkasm_agent|Up About an hour (healthy)|kasmweb/agent:1.19.0-rolling\nkasm_api|Up About an hour (healthy)|kasmweb/api:1.19.0-rolling\nkasm_db|Up About an hour (healthy)|kasmweb/postgres:1.19.0-rolling\nkasm_guac|Up About an hour (healthy)|kasmweb/kasm-guac:1.19.0-rolling\nkasm_manager|Up About an hour (healthy)|kasmweb/manager:1.19.0-rolling\nkasm_proxy|Up About an hour|kasmweb/proxy:1.19.0-rolling\nkasm_rdp_gateway|Up About an hour (healthy)|kasmweb/rdp-gateway:1.19.0-rolling\nkasm_rdp_https_gateway|Up About an hour (healthy)|kasmweb/rdp-https-gateway:1.19.0-rolling\n--- images ---\nall=8\ntagged=8\ndangling=0\n--- lab addresses ---\nenp6s19          UP             fe80::be24:11ff:fed7:e42e/64 \nenp6s20          UP             fe80::be24:11ff:fec5:ee3d/64 \nenp6s21          UP             fe80::be24:11ff:fe0f:771b/64 \nshim74@enp6s19   UP             192.168.74.201/32 fe80::fc56:22ff:fe3e:b654/64 \nshim77@enp6s20   UP             192.168.77.201/32 fe80::a412:d9ff:fe85:d481/64 \nshim79@enp6s21   UP             192.168.79.201/32 fe80::8c9c:cdff:fe6c:b531/64 \n--- lab routes ---\n192.168.74.208/28 dev shim74 scope link \n192.168.77.208/28 dev shim77 scope link \n192.168.79.208/28 dev shim79 scope link \n--- docker networks ---\nlab74|enp6s19|192.168.74.0/24|192.168.74.1|192.168.74.208/28\nlab77|enp6s20|192.168.77.0/24|192.168.77.1|192.168.77.208/28\nlab79|enp6s21|192.168.79.0/24|192.168.79.1|192.168.79.208/28\n--- API health ---\n{\"ok\": true}"
}
```

**Standard error:** empty  
**SSH Manager exit code:** 0  
**Structured result:** `success: true`

The command is the follow-up verification. It proves the persistent shim unit, Docker, eight Kasm services, clean image set, addressless parent NICs, shim routes, macvlan definitions, and API health in one capture.
