#!/bin/bash
# reboot-node.sh <ip> <name> : schedule a reboot, wait for a new boot ID, report node state and guest states
ip=$1; name=$2
S="ssh -o BatchMode=yes -o ConnectTimeout=5 root@$ip"
old=$($S 'cat /proc/sys/kernel/random/boot_id') || { echo "cannot read boot id"; exit 1; }
echo "$name old_boot=$old guests_before: $($S 'qm list | awk "NR>1{print \$2\"=\"\$3}" | tr "\n" " "; pct list | awk "NR>1{print \$3\"=\"\$2}" | tr "\n" " "')"
$S "systemd-run --unit=fleet-reboot-$name-20261006 --on-active=3s --description='Fleet update reboot' /usr/bin/systemctl reboot >/dev/null 2>&1 && TZ=America/New_York date '+scheduled %Y-%m-%d %I:%M:%S %p %Z'"
start=$(date +%s); sleep 25
until b=$(timeout 8 ssh -o BatchMode=yes -o ConnectTimeout=4 root@$ip 'cat /proc/sys/kernel/random/boot_id' 2>/dev/null) && [ -n "$b" ] && [ "$b" != "$old" ]; do sleep 10; [ $(( $(date +%s) - start )) -gt 1200 ] && { echo "TIMEOUT waiting for $name"; exit 1; }; done
echo "$name back after $(( $(date +%s) - start ))s new_boot=$b"
$S 'echo "kernel=$(uname -r)"; systemctl is-active pve-cluster pvedaemon pveproxy pvestatd corosync pve-firewall wazuh-agent | tr "\n" " "; echo; pvecm status | grep -E "Quorate|Total votes" | tr "\n" " "; echo; echo "failed_units=$(systemctl --failed --no-legend | wc -l)"'
# wait for every guest on the node to be running (onboot)
gstart=$(date +%s)
until out=$($S 'qm list | awk "NR>1 && \$3!=\"running\"{print \$2}"; pct list | awk "NR>1 && \$2!=\"running\"{print \$3}"' 2>/dev/null) && [ -z "$out" ]; do sleep 10; [ $(( $(date +%s) - gstart )) -gt 600 ] && { echo "guests not all running after 600s: $out"; break; }; done
echo "$name guests_after ($(( $(date +%s) - gstart ))s): $($S 'qm list | awk "NR>1{print \$2\"=\"\$3}" | tr "\n" " "; pct list | awk "NR>1{print \$3\"=\"\$2}" | tr "\n" " "')"
