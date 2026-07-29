# S05 Full Final State Readback

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Capture time:** 2026-07-29 00:44:43 through 00:45:45 UTC  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP, root shell on `purple-server`, QEMU guest agent, Docker CLI, and Kasm PostgreSQL readback

## Commands

I ran one read-only host and guest readback, then a focused 19-workspace query. The first readback exposed mode 0777 on the exercised `terminal-trusted` profile directory. With zero `alpha` sessions active, I restored all six exact profile directories to 0750. I then deleted only the earlier final snapshot and recreated it under the same planned name so the rollback point contains the corrected mode.

The material verification commands were:

```bash
qm status 122
qm config 122 | grep -E '^(name|memory|cores|scsi0|net[0-4]):'
qm listsnapshot 122
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,vg_name

qm guest exec 122 --timeout 180 -- /bin/bash -c 'set -o pipefail
printf "BOOT_ID="; cat /proc/sys/kernel/random/boot_id
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
df -h /
printf "SERVICES\n"; systemctl is-active kasm-lab-shims.service docker.service
printf "PARENTS_AND_SHIMS\n"
for i in enp6s19 enp6s20 enp6s21 enp6s22 shim74 shim75 shim77 shim79; do ip -br addr show "$i"; done
printf "ROUTES\n"; ip route show | grep -E "192\.168\.(74|75|77|79)\.208/28" | sort
printf "DOCKER_NETWORKS\n"
for n in lab74 lab75 lab77 lab79; do docker network inspect -f "{{.Name}}|{{(index .IPAM.Config 0).Subnet}}|{{(index .IPAM.Config 0).Gateway}}|{{(index .IPAM.Config 0).IPRange}}|{{index .Options \"parent\"}}" "$n"; done
printf "KASM_SERVICES\n"; docker ps --filter name=kasm_ --format "{{.Names}}|{{.Status}}" | sort
printf "KASM_HEALTH\n"; curl -ks https://127.0.0.1/api/__healthcheck; echo
printf "PROFILE_DIRS\n"; find /var/lib/kasm-profiles -mindepth 1 -maxdepth 1 -type d -printf "%f|%U|%G|%m\n" | sort
printf "GROUP_SETTINGS\n"
docker exec kasm_db psql -U kasmapp -d kasm -At -F "|" -c "SELECT gs.name,gs.value FROM group_settings gs JOIN groups g USING(group_id) WHERE g.name=\$q\$Lab Sessions\$q\$ ORDER BY gs.name;"
printf "GROUP_IMAGE_COUNTS\n"
docker exec kasm_db psql -U kasmapp -d kasm -At -F "|" -c "SELECT g.name,count(*) FROM group_images gi JOIN groups g USING(group_id) GROUP BY g.name ORDER BY g.name;"
printf "UNISOLATED_COUNT\n"
docker exec kasm_db psql -U kasmapp -d kasm -At -c "SELECT count(*) FROM images WHERE friendly_name LIKE \$q\$% (UNISOLATED)\$q\$;"
printf "ALPHA_ACTIVE_SESSIONS\n"
docker exec kasm_db psql -U kasmapp -d kasm -At -c "SELECT count(*) FROM kasms k JOIN users u USING(user_id) WHERE u.username=\$q\$alpha\$q\$;"
printf "TEMP_RESIDUE\n"; find /tmp -maxdepth 1 -type f -name "kasm-*" -printf "%f\n"'

qm guest exec 122 --timeout 90 -- /bin/bash -c 'printf "=== LAB SESSIONS WORKSPACES ===\n"
docker exec kasm_db psql -U kasmapp -d kasm -At -F "|" -c "SELECT i.friendly_name,i.run_config::jsonb->>\$q\$network\$q\$,i.run_config::jsonb->\$q\$dns\$q\$,coalesce(i.persistent_profile_path,\$q\$<null>\$q\$) FROM images i JOIN group_images gi USING(image_id) JOIN groups g USING(group_id) WHERE g.name=\$q\$Lab Sessions\$q\$ ORDER BY i.friendly_name;"
printf "=== PROFILE DIRECTORY MODES ===\n"
find /var/lib/kasm-profiles -mindepth 1 -maxdepth 1 -type d -printf "%f|%U|%G|%m\n" | sort'

qm guest exec 122 --timeout 60 -- /bin/bash -c 'set -euo pipefail
test "$(docker exec kasm_db psql -U kasmapp -d kasm -At -c "SELECT count(*) FROM kasms k JOIN users u USING(user_id) WHERE u.username=\$q\$alpha\$q\$;")" = 0
for d in claude-code codex-cli terminal-trusted nessus hunchly telegram; do
  test -d "/var/lib/kasm-profiles/$d"
  chmod 0750 "/var/lib/kasm-profiles/$d"
done
find /var/lib/kasm-profiles -mindepth 1 -maxdepth 1 -type d -printf "%f|%U|%G|%m\n" | sort'

qm delsnapshot 122 baseline-tiles-2026-07-28
qm snapshot 122 baseline-tiles-2026-07-28 --description 'Accepted Kasm workspace build-out baseline after lane, policy, persistence-mode, reboot, and launch verification'
qm listsnapshot 122
```

SSH Manager returned success and remote exit code 0 for each call. No standard error was returned. The bracketed guest commands are expanded by the complete output sections below; they contain no secret input.

## VM, disk, and snapshots

```text
status: running
cores: 4
memory: 8192
name: kasm-01
net0: virtio=<YOUR_KASM_HOST_MAC>,bridge=vmbr0,firewall=1,tag=78
net1: virtio=<YOUR_KASM_LANE_74_MAC>,bridge=vmbr0,firewall=0,tag=74
net2: virtio=<YOUR_KASM_LANE_77_MAC>,bridge=vmbr0,firewall=0,tag=77
net3: virtio=<YOUR_KASM_LANE_79_MAC>,bridge=vmbr0,firewall=0,tag=79
net4: virtio=<YOUR_KASM_LANE_75_MAC>,bridge=vmbr0,firewall=0,tag=75
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=200G,ssd=1
pre-workspace-buildout-2026-07-28  2026-07-28 19:35:27  no-description
baseline-tiles-2026-07-28           2026-07-28 20:45:45  Accepted Kasm workspace build-out baseline after lane, policy, persistence-mode, reboot, and launch verification
current
ssd-lvm2  228.11  52.22  2.39  ssd-lvm2
```

The snapshot deletion removed only the earlier `baseline-tiles-2026-07-28` instance. Recreating it immediately restored the planned final recovery point with the corrected profile mode. The pre-change snapshot remained untouched.

## Guest disk, services, and network

```text
BOOT_ID=b74d3049-85a0-439c-8df3-ca976c382085
NAME     SIZE FSTYPE  MOUNTPOINTS
sda      200G
sda1     199G ext4    /
sda14      4M
sda15    106M vfat    /boot/efi
sda16    913M ext4    /boot
sr0        4M iso9660
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       193G  117G   76G  61% /
SERVICES
active
active
PARENTS_AND_SHIMS
enp6s19          UP
enp6s20          UP
enp6s21          UP
enp6s22          UP
shim74@enp6s19   UP  192.168.74.201/32
shim75@enp6s22   UP  192.168.75.201/32
shim77@enp6s20   UP  192.168.77.201/32
shim79@enp6s21   UP  192.168.79.201/32
ROUTES
192.168.74.208/28 dev shim74 scope link
192.168.75.208/28 dev shim75 scope link
192.168.77.208/28 dev shim77 scope link
192.168.79.208/28 dev shim79 scope link
DOCKER_NETWORKS
lab74|192.168.74.0/24|192.168.74.1|192.168.74.208/28|enp6s19
lab75|192.168.75.0/24|192.168.75.1|192.168.75.208/28|enp6s22
lab77|192.168.77.0/24|192.168.77.1|192.168.77.208/28|enp6s20
lab79|192.168.79.0/24|192.168.79.1|192.168.79.208/28|enp6s21
```

## Kasm services and health

```text
kasm_agent|Up 19 minutes (healthy)
kasm_api|Up 19 minutes (healthy)
kasm_db|Up 19 minutes (healthy)
kasm_guac|Up 19 minutes (healthy)
kasm_manager|Up 19 minutes (healthy)
kasm_proxy|Up 19 minutes
kasm_rdp_gateway|Up 18 minutes (healthy)
kasm_rdp_https_gateway|Up 19 minutes (healthy)
KASM_HEALTH
{"ok": true}
```

## Lab Sessions settings and counts

```text
allow_kasm_clipboard_down|False
allow_kasm_clipboard_seamless|False
allow_kasm_clipboard_up|False
allow_kasm_downloads|False
allow_kasm_microphone|False
allow_kasm_printing|False
allow_kasm_sharing|False
allow_kasm_uploads|True
allow_persistent_profile|True
allow_user_storage_mapping|False
max_kasms_per_user|2
session_time_limit|3600
All Users|15
Lab Sessions|19
UNISOLATED_COUNT
15
ALPHA_ACTIVE_SESSIONS
0
TEMP_RESIDUE
```

The empty line after `TEMP_RESIDUE` is the complete result: no matching file existed.

## Complete Lab Sessions workspace output

```text
Chrome - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Claude Code - Trusted 75|lab75|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/claude-code
Codex CLI - Trusted 75|lab75|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/codex-cli
Cyberbro - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Debian - Review 79|lab79|["192.168.79.10"]|<null>
Debian - Target 77|lab77|["192.168.77.10"]|<null>
Fedora - Target 77|lab77|["192.168.77.10"]|<null>
Forensic OSINT - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Hunchly - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/hunchly
Kali - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Nessus - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/nessus
REMnux - Malware 77|lab77|["192.168.77.10"]|<null>
REMnux - Review 79|lab79|["192.168.79.10"]|<null>
Spiderfoot - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Telegram - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/telegram
Terminal - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
Terminal - Malware 77|lab77|["192.168.77.10"]|<null>
Terminal - Trusted 75|lab75|["9.9.9.9", "149.112.112.112"]|/var/lib/kasm-profiles/terminal-trusted
Tor Browser - Lab 74|lab74|["9.9.9.9", "149.112.112.112"]|<null>
```

## Final profile directory output

```text
claude-code|1000|1000|750
codex-cli|1000|1000|750
hunchly|1000|1000|750
nessus|1000|1000|750
telegram|1000|1000|750
terminal-trusted|1000|1000|750
```

## Post-correction health readback

At 2026-07-29 00:47:30 UTC I ran one final read-only check after recreating the snapshot:

```text
status: running
pre-workspace-buildout-2026-07-28  2026-07-28 19:35:27
baseline-tiles-2026-07-28           2026-07-28 20:45:45
ssd-lvm2                            228.11  52.24  2.41
{"ok": true}
claude-code|1000|1000|750
codex-cli|1000|1000|750
hunchly|1000|1000|750
nessus|1000|1000|750
telegram|1000|1000|750
terminal-trusted|1000|1000|750
alpha_sessions=0
temp_files=
```
