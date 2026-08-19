# S06 Host and Direct-IP Acceptance Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture timestamp:** 2026-07-28T15:09:02-04:00  
**Target:** `kasm-01`, VM 122  
**Mechanism:** SSH Manager MCP to `purple-server`, Proxmox QEMU guest agent, base64 transport, guest Bash

I ran the missing management-host and direct-IP acceptance checks. The payload removed its temporary containers and images through both an exit trap and an explicit cleanup.

## Exact Decoded Command Payload

```bash
set -u
cleanup() {
  docker rm -f kasm-verify-74 kasm-verify-77 kasm-verify-79 >/dev/null 2>&1 || true
  docker image rm -f kasm-isolation-check:2026-07-28 alpine:3.22 hello-world:latest >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup
echo "timestamp=$(date -Is)"
echo '--- management host image pull ---'
docker pull hello-world:latest
echo '--- management host protected targets ---'
probe_host() {
  target="$1"; port="$2"; label="$3"
  output=$(timeout 3 bash -c "echo > /dev/tcp/${target}/${port}" 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then state=OPEN; else state=BLOCKED; fi
  printf '%s=%s|rc=%s|%s\n' "$label" "$state" "$rc" "$output"
}
probe_host 192.168.78.10 443 host_to_self_443
probe_host 192.168.80.10 22 host_to_192.168.80.10_22
probe_host 192.168.70.10 8006 host_to_192.168.70.10_8006
probe_host 192.168.70.11 8006 host_to_192.168.70.11_8006
probe_host 192.168.71.10 22 host_to_192.168.71.10_22
probe_host 192.168.72.2 443 host_to_192.168.72.2_443
probe_host 192.168.73.2 9090 host_to_192.168.73.2_9090
probe_host 192.168.1.1 443 host_to_192.168.1.1_443
probe_host 192.168.10.1 443 host_to_192.168.10.1_443
echo '--- direct-IP egress ---'
printf 'FROM alpine:3.22\nRUN apk add --no-cache netcat-openbsd\n' |
  docker build -q -t kasm-isolation-check:2026-07-28 - >/dev/null
for lane in 74 77 79; do
  dns="192.168.${lane}.10"
  [ "$lane" = 74 ] && dns=9.9.9.9
  docker run -d --name "kasm-verify-${lane}" \
    --network "lab${lane}" --ip "192.168.${lane}.210" --dns "$dns" \
    kasm-isolation-check:2026-07-28 sleep 600 >/dev/null
  output=$(docker exec "kasm-verify-${lane}" timeout 5 nc -zvw 4 1.1.1.1 443 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then state=OPEN; else state=BLOCKED; fi
  printf 'lab%s_to_1.1.1.1_443=%s|rc=%s|%s\n' "$lane" "$state" "$rc" "$output"
done
cleanup
trap - EXIT
echo '--- cleanup verification ---'
printf 'test_containers='
docker ps -a --format '{{.Names}}' | grep -c '^kasm-verify-' || true
printf 'all_containers='
docker ps -aq | wc -l
printf 'all_images='
docker image ls -aq | sort -u | wc -l
printf 'dangling_images='
docker image ls -qf dangling=true | wc -l
printf 'lab_endpoints='
for n in lab74 lab77 lab79; do
  docker network inspect "$n" --format '{{len .Containers}}'
done | paste -sd, -
```

## Complete Standard Output

```text
timestamp=2026-07-28T15:09:02-04:00
--- management host image pull ---
latest: Pulling from library/hello-world
4f55086f7dd0: Pulling fs layer
4f55086f7dd0: Download complete
4f55086f7dd0: Pull complete
d5e71e642bf5: Download complete
Digest: sha256:c3cbe1cc1aa588a64951ac6286e0df7b27fe2e6324b1001c619bb358770c0178
Status: Downloaded newer image for hello-world:latest
docker.io/library/hello-world:latest
--- management host protected targets ---
host_to_self_443=OPEN|rc=0|
host_to_192.168.80.10_22=BLOCKED|rc=124|
host_to_192.168.70.10_8006=BLOCKED|rc=124|
host_to_192.168.70.11_8006=BLOCKED|rc=124|
host_to_192.168.71.10_22=BLOCKED|rc=124|
host_to_192.168.72.2_443=BLOCKED|rc=124|
host_to_192.168.73.2_9090=BLOCKED|rc=124|
host_to_192.168.1.1_443=BLOCKED|rc=124|
host_to_192.168.10.1_443=BLOCKED|rc=124|
--- direct-IP egress ---
lab74_to_1.1.1.1_443=OPEN|rc=0|Connection to 1.1.1.1 443 port [tcp/https] succeeded!
lab77_to_1.1.1.1_443=BLOCKED|rc=1|nc: connect to 1.1.1.1 port 443 (tcp) timed out: Operation in progress
lab79_to_1.1.1.1_443=BLOCKED|rc=1|nc: connect to 1.1.1.1 port 443 (tcp) timed out: Operation in progress
--- cleanup verification ---
test_containers=0
all_containers=8
all_images=8
dangling_images=0
lab_endpoints=0,0,0
```

**Standard error:** empty  
**Guest command exit code:** 0  
**SSH Manager exit code:** 0  
**Structured result:** `success: true`

The management host pulled a public image, reached its own required HTTPS listener, and failed toward every protected remote target. VLAN 74 reached a public IP on TCP 443. VLANs 77 and 79 timed out to the same address. The cleanup returned the guest to eight service containers, eight images, no dangling image, and no lab endpoint.
