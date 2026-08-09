#!/bin/bash
set -Eeuo pipefail

readonly interface_file=/etc/network/interfaces
readonly backup_file=/etc/network/interfaces.pre-networkmanager-20260715
readonly connection_name='Wired connection 1'

rollback() {
  rc=$?
  echo "CUTOVER_FAILED rc=${rc}; restoring ifupdown ownership" >&2
  cp -a "${backup_file}" "${interface_file}"
  nmcli connection down "${connection_name}" >/dev/null 2>&1 || true
  systemctl restart networking || ifup ens18 || true
  systemctl restart NetworkManager || true
  exit "${rc}"
}

trap rollback ERR

cp -a "${interface_file}" "${backup_file}"

ifdown ens18
sed -i '/^# The primary network interface/,$d' "${interface_file}"
systemctl restart NetworkManager
nmcli connection up "${connection_name}"

for attempt in $(seq 1 15); do
  if test "$(nmcli -t -f STATE general)" = connected \
    && nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | grep -q '^ens18:ethernet:connected:' \
    && ip -4 address show dev ens18 | grep -q '192\.168\.40\.135/24' \
    && ip route show default | grep -q '^default via 192\.168\.40\.1 dev ens18' \
    && getent hosts deb.debian.org >/dev/null; then
    echo "network_ready_attempt=${attempt}"
    break
  fi

  if test "${attempt}" -eq 15; then
    echo NETWORK_READINESS_TIMEOUT >&2
    false
  fi

  sleep 2
done

test "$(nmcli -t -f STATE general)" = connected
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status | grep -q '^ens18:ethernet:connected:'
ip -4 address show dev ens18 | grep -q '192\.168\.40\.135/24'
ip route show default | grep -q '^default via 192\.168\.40\.1 dev ens18'
getent hosts deb.debian.org >/dev/null

trap - ERR

echo CUTOVER_VERIFIED
nmcli -t -f STATE general
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status
ip -4 address show dev ens18
ip route show default
