# S06 Containment and Cleanup Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture timestamp:** 2026-07-28T14:50:41-04:00  
**Target:** `kasm-01`, VM 122  
**Mechanism:** SSH Manager MCP to `purple-server`, Proxmox QEMU guest agent, base64 transport, guest Bash, default working directory

I base64-encoded the following exact payload only to avoid shell-quoting damage. SSH Manager issued it through `qm guest exec 122 -- /bin/bash -lc "echo <base64-payload> | base64 -d | bash"`.

## Exact decoded command payload

```bash
set -u
cleanup() {
  docker rm -f kasm-verify-74 kasm-verify-77 kasm-verify-79 >/dev/null 2>&1 || true
  docker image rm -f kasm-isolation-check:2026-07-28 alpine:3.22 >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup
printf 'FROM alpine:3.22\nRUN apk add --no-cache curl bind-tools netcat-openbsd\n' | docker build -q -t kasm-isolation-check:2026-07-28 - >/dev/null
for lane in 74 77 79; do
  dns="192.168.${lane}.10"
  [ "$lane" = 74 ] && dns=9.9.9.9
  docker run -d --name "kasm-verify-${lane}" --network "lab${lane}" --ip "192.168.${lane}.210" --dns "$dns" kasm-isolation-check:2026-07-28 sleep 600 >/dev/null
done
docker exec kasm-verify-74 sh -c 'nohup nc -lk -p 9010 >/tmp/nc.log 2>&1 &'
docker exec kasm-verify-77 sh -c 'nohup nc -lk -p 9010 >/tmp/nc.log 2>&1 &'
docker exec kasm-verify-79 sh -c 'nohup nc -lk -p 9010 >/tmp/nc.log 2>&1 &'
sleep 1
probe() {
  source_lane="$1"; target="$2"; port="$3"; label="$4"
  output=$(docker exec "kasm-verify-${source_lane}" timeout 3 nc -zvw 2 "$target" "$port" 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then state=OPEN; else state=BLOCKED; fi
  printf '%s=%s|rc=%s|%s\n' "$label" "$state" "$rc" "$output"
}
echo "timestamp=$(date -Is)"
echo '--- lane matrix ---'
probe 74 192.168.77.210 9010 lab74_to_lab77
probe 77 192.168.74.210 9010 lab77_to_lab74
probe 74 192.168.79.210 9010 lab74_to_lab79
probe 77 192.168.79.210 9010 lab77_to_lab79
probe 79 192.168.74.210 9010 lab79_to_lab74
probe 79 192.168.77.210 9010 lab79_to_lab77
echo '--- DNS and Internet ---'
for lane in 74 77 79; do
  output=$(docker exec "kasm-verify-${lane}" timeout 6 getent hosts example.com 2>&1); rc=$?; printf 'lab%s_dns_rc=%s|%s\n' "$lane" "$rc" "$output"
  output=$(docker exec "kasm-verify-${lane}" curl -4fsS --max-time 10 https://api.ipify.org 2>&1); rc=$?; printf 'lab%s_internet_rc=%s|%s\n' "$lane" "$rc" "$output"
done
echo '--- protected targets ---'
for lane in 74 77 79; do
  probe "$lane" 192.168.78.10 443 "lab${lane}_to_192.168.78.10_443"
  probe "$lane" 192.168.80.10 22 "lab${lane}_to_192.168.80.10_22"
  probe "$lane" 192.168.70.10 8006 "lab${lane}_to_192.168.70.10_8006"
  probe "$lane" 192.168.70.11 8006 "lab${lane}_to_192.168.70.11_8006"
  probe "$lane" 192.168.71.10 22 "lab${lane}_to_192.168.71.10_22"
  probe "$lane" 192.168.72.2 443 "lab${lane}_to_192.168.72.2_443"
  probe "$lane" 192.168.73.2 9090 "lab${lane}_to_192.168.73.2_9090"
  probe "$lane" 192.168.1.1 443 "lab${lane}_to_192.168.1.1_443"
  probe "$lane" 192.168.10.1 443 "lab${lane}_to_192.168.10.1_443"
done
cleanup
trap - EXIT
echo '--- cleanup verification ---'
printf 'test_containers='; docker ps -a --format '{{.Names}}' | grep -c '^kasm-verify-' || true
printf 'all_images='; docker image ls -aq | sort -u | wc -l
printf 'dangling_images='; docker image ls -qf dangling=true | wc -l
printf 'lab_endpoints='; for n in lab74 lab77 lab79; do docker network inspect "$n" --format '{{len .Containers}}'; done | paste -sd, -
```

## Complete standard output

```text
timestamp=2026-07-28T14:50:41-04:00
--- lane matrix ---
lab74_to_lab77=OPEN|rc=0|Connection to 192.168.77.210 9010 port [tcp/*] succeeded!
lab77_to_lab74=BLOCKED|rc=1|nc: connect to 192.168.74.210 port 9010 (tcp) timed out: Operation in progress
lab74_to_lab79=BLOCKED|rc=1|nc: connect to 192.168.79.210 port 9010 (tcp) timed out: Operation in progress
lab77_to_lab79=BLOCKED|rc=1|nc: connect to 192.168.79.210 port 9010 (tcp) timed out: Operation in progress
lab79_to_lab74=BLOCKED|rc=1|nc: connect to 192.168.74.210 port 9010 (tcp) timed out: Operation in progress
lab79_to_lab77=BLOCKED|rc=1|nc: connect to 192.168.77.210 port 9010 (tcp) timed out: Operation in progress
--- DNS and Internet ---
lab74_dns_rc=0|2606:4700:10::6814:179a  example.com  example.com
lab74_internet_rc=0|185.98.168.20
lab77_dns_rc=143|
lab77_internet_rc=6|curl: (6) Could not resolve host: api.ipify.org
lab79_dns_rc=143|
lab79_internet_rc=6|curl: (6) Could not resolve host: api.ipify.org
--- protected targets ---
lab74_to_192.168.78.10_443=BLOCKED|rc=1|nc: connect to 192.168.78.10 port 443 (tcp) timed out: Operation in progress
lab74_to_192.168.80.10_22=BLOCKED|rc=1|nc: connect to 192.168.80.10 port 22 (tcp) timed out: Operation in progress
lab74_to_192.168.70.10_8006=BLOCKED|rc=1|nc: connect to 192.168.70.10 port 8006 (tcp) timed out: Operation in progress
lab74_to_192.168.70.11_8006=BLOCKED|rc=1|nc: connect to 192.168.70.11 port 8006 (tcp) timed out: Operation in progress
lab74_to_192.168.71.10_22=BLOCKED|rc=1|nc: connect to 192.168.71.10 port 22 (tcp) timed out: Operation in progress
lab74_to_192.168.72.2_443=BLOCKED|rc=1|nc: connect to 192.168.72.2 port 443 (tcp) timed out: Operation in progress
lab74_to_192.168.73.2_9090=BLOCKED|rc=1|nc: connect to 192.168.73.2 port 9090 (tcp) timed out: Operation in progress
lab74_to_192.168.1.1_443=BLOCKED|rc=1|nc: connect to 192.168.1.1 port 443 (tcp) timed out: Operation in progress
lab74_to_192.168.10.1_443=BLOCKED|rc=1|nc: connect to 192.168.10.1 port 443 (tcp) timed out: Operation in progress
lab77_to_192.168.78.10_443=BLOCKED|rc=1|nc: connect to 192.168.78.10 port 443 (tcp) timed out: Operation in progress
lab77_to_192.168.80.10_22=BLOCKED|rc=1|nc: connect to 192.168.80.10 port 22 (tcp) timed out: Operation in progress
lab77_to_192.168.70.10_8006=BLOCKED|rc=1|nc: connect to 192.168.70.10 port 8006 (tcp) timed out: Operation in progress
lab77_to_192.168.70.11_8006=BLOCKED|rc=1|nc: connect to 192.168.70.11 port 8006 (tcp) timed out: Operation in progress
lab77_to_192.168.71.10_22=BLOCKED|rc=1|nc: connect to 192.168.71.10 port 22 (tcp) timed out: Operation in progress
lab77_to_192.168.72.2_443=BLOCKED|rc=1|nc: connect to 192.168.72.2 port 443 (tcp) timed out: Operation in progress
lab77_to_192.168.73.2_9090=BLOCKED|rc=1|nc: connect to 192.168.73.2 port 9090 (tcp) timed out: Operation in progress
lab77_to_192.168.1.1_443=BLOCKED|rc=1|nc: connect to 192.168.1.1 port 443 (tcp) timed out: Operation in progress
lab77_to_192.168.10.1_443=BLOCKED|rc=1|nc: connect to 192.168.10.1 port 443 (tcp) timed out: Operation in progress
lab79_to_192.168.78.10_443=BLOCKED|rc=1|nc: connect to 192.168.78.10 port 443 (tcp) timed out: Operation in progress
lab79_to_192.168.80.10_22=BLOCKED|rc=1|nc: connect to 192.168.80.10 port 22 (tcp) timed out: Operation in progress
lab79_to_192.168.70.10_8006=BLOCKED|rc=1|nc: connect to 192.168.70.10 port 8006 (tcp) timed out: Operation in progress
lab79_to_192.168.70.11_8006=BLOCKED|rc=1|nc: connect to 192.168.70.11 port 8006 (tcp) timed out: Operation in progress
lab79_to_192.168.71.10_22=BLOCKED|rc=1|nc: connect to 192.168.71.10 port 22 (tcp) timed out: Operation in progress
lab79_to_192.168.72.2_443=BLOCKED|rc=1|nc: connect to 192.168.72.2 port 443 (tcp) timed out: Operation in progress
lab79_to_192.168.73.2_9090=BLOCKED|rc=1|nc: connect to 192.168.73.2 port 9090 (tcp) timed out: Operation in progress
lab79_to_192.168.1.1_443=BLOCKED|rc=1|nc: connect to 192.168.1.1 port 443 (tcp) timed out: Operation in progress
lab79_to_192.168.10.1_443=BLOCKED|rc=1|nc: connect to 192.168.10.1 port 443 (tcp) timed out: Operation in progress
--- cleanup verification ---
test_containers=0
all_images=8
dangling_images=0
lab_endpoints=0,0,0
```

**Standard error:** empty  
**Guest command exit code:** 0  
**SSH Manager exit code:** 0  
**Structured result:** `success: true`

The final four lines are the follow-up cleanup verification. They prove that the recheck left no test container, test image, dangling image, or lab-network endpoint.
