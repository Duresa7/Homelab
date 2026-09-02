#!/bin/sh
# Managed by Ansible: monitoring-exporters/playbooks/textfile-collectors.yml
#
# Pending-update counts for a dnf host, in the shape node_exporter's textfile
# collector reads. prometheus-node-exporter-collectors ships apt_info.py for
# Debian and nothing for dnf, so this fills the gap with the same three facts:
# how many updates are waiting, how many of those are security updates, and
# whether the running kernel is the newest one installed.
set -u
OUT=/var/lib/prometheus/node-exporter/dnf.prom
TMP=$(mktemp "${OUT}.XXXXXX") || exit 1
trap 'rm -f "$TMP"' EXIT

# check-update exits 100 when updates exist, 0 when none, anything else is a
# real failure and the old file is left in place.
ALL=$(dnf -q check-update 2>/dev/null); rc=$?
[ "$rc" -eq 0 ] || [ "$rc" -eq 100 ] || exit 1
SEC=$(dnf -q check-update --security 2>/dev/null); rc=$?
[ "$rc" -eq 0 ] || [ "$rc" -eq 100 ] || exit 1

# Output rows are "name.arch  version  repo". The Obsoleting section that can
# follow uses a different shape and is not a pending upgrade.
count_rows() { printf '%s\n' "$1" | awk 'NF == 3 && $1 !~ /^Obsoleting/ { n++ } END { print n + 0 }'; }

RUNNING=$(uname -r)
NEWEST=$(rpm -q kernel --qf '%{VERSION}-%{RELEASE}.%{ARCH}\n' 2>/dev/null | sort -V | tail -1)
if [ -n "$NEWEST" ] && [ "$RUNNING" != "$NEWEST" ]; then REBOOT=1; else REBOOT=0; fi

{
  echo '# HELP dnf_upgrades_pending Pending package upgrades by repository, from dnf check-update.'
  echo '# TYPE dnf_upgrades_pending gauge'
  printf '%s\n' "$ALL" | awk 'NF == 3 && $1 !~ /^Obsoleting/ { c[$3]++ } END { for (r in c) printf "dnf_upgrades_pending{repo=\"%s\"} %d\n", r, c[r] }'
  echo '# HELP dnf_security_upgrades_pending Pending package upgrades that carry a security advisory.'
  echo '# TYPE dnf_security_upgrades_pending gauge'
  echo "dnf_security_upgrades_pending $(count_rows "$SEC")"
  echo '# HELP node_reboot_required 1 when the running kernel is not the newest installed kernel.'
  echo '# TYPE node_reboot_required gauge'
  echo "node_reboot_required $REBOOT"
  echo '# HELP dnf_updates_check_timestamp_seconds When this file was written.'
  echo '# TYPE dnf_updates_check_timestamp_seconds gauge'
  echo "dnf_updates_check_timestamp_seconds $(date +%s)"
} > "$TMP"
chmod 0644 "$TMP"
mv "$TMP" "$OUT"
trap - EXIT
