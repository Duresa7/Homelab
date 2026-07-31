import json
import re
from pathlib import Path
from urllib.parse import quote


MAC_PATTERN = re.compile(r"^[0-9a-f]{2}(?::[0-9a-f]{2}){5}$")


def normalize_mac(value):
    normalized = str(value).strip().lower().replace("-", ":")
    if not MAC_PATTERN.fullmatch(normalized):
        raise ValueError(f"invalid MAC address: {value}")
    return normalized


def find_mac_address(payload, registered_macs):
    registered = {normalize_mac(mac) for mac in registered_macs}

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in {"mac", "mac_address", "mac-address"}:
                    try:
                        candidate = normalize_mac(child)
                    except (TypeError, ValueError):
                        pass
                    else:
                        if candidate in registered:
                            return candidate
                found = walk(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child)
                if found:
                    return found
        return None

    return walk(payload)


def render_boot_script(base_url, should_install):
    if should_install:
        return (
            "#!ipxe\n"
            f"chain --replace {base_url}/assets/boot.ipxe || goto failed\n"
            ":failed\n"
            "echo Installer chain failed. Opening the iPXE shell.\n"
            "shell\n"
        )
    return "#!ipxe\necho This machine is not armed for installation.\nexit\n"


def _toml_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def render_answer(
    mac,
    machine,
    root_password_hash,
    base_url,
    attempt_id,
    root_ssh_keys,
):
    normalized = normalize_mac(mac)
    encoded_mac = quote(normalized, safe="")
    encoded_attempt = quote(attempt_id, safe="")
    fqdn = f"{machine['hostname']}.{machine['domain']}"
    keys = ", ".join(_toml_string(key) for key in root_ssh_keys)
    callback_query = f"mac={encoded_mac}&attempt={encoded_attempt}"
    reboot_mode = (
        'reboot-mode = "power-off"\n' if machine.get("acceptance_only") else ""
    )
    first_boot = ""
    if not machine.get("acceptance_only"):
        first_boot = f"""
[first-boot]
source = "from-url"
url = "{base_url}/v1/bootstrap?{callback_query}"
ordering = "network-online"
"""
    return f"""[global]
keyboard = "en-us"
country = "us"
fqdn = "{fqdn}"
mailto = "root@localhost"
timezone = "America/New_York"
root-password-hashed = "{root_password_hash}"
root-ssh-keys = [{keys}]
reboot-on-error = true
{reboot_mode}

[network]
source = "from-dhcp"

[network.interface-name-pinning]
enabled = true

[network.interface-name-pinning.mapping]
"{normalized}" = "nic0"

[disk-setup]
filesystem = "ext4"
disk-list = ["{machine['install_disk']}"]

[post-installation-webhook]
url = "{base_url}/v1/installer-complete?{callback_query}"
{first_boot}"""


FIRST_BOOT_TEMPLATE = r"""#!/bin/bash
set -Eeuo pipefail

exec > >(tee -a /var/log/galaxy-pxe-first-boot.log) 2>&1

BASE_URL="@@BASE_URL@@"
MAC_ENCODED="@@MAC_ENCODED@@"
ATTEMPT_ENCODED="@@ATTEMPT_ENCODED@@"
JOIN_KEY="/run/galaxy-pxe-join-key"

report_state() {
    local phase="$1"
    local detail="${2:-{}}"
    curl --fail --silent --show-error \
        --connect-timeout 5 \
        --max-time 15 \
        --retry 30 \
        --retry-delay 2 \
        --retry-connrefused \
        --request POST \
        --header "Content-Type: application/json" \
        --data "${detail}" \
        "${BASE_URL}/v1/state/${phase}?mac=${MAC_ENCODED}&attempt=${ATTEMPT_ENCODED}" \
        --output /dev/null
}

on_error() {
    local exit_code="$?"
    local line="$1"
    trap - ERR
    report_state failed \
        "{\"exit_code\":${exit_code},\"line\":${line}}" || true
    exit "${exit_code}"
}

fail() {
    local reason="$1"
    local message="$2"
    local line="${BASH_LINENO[0]:-0}"
    echo "${message}" >&2
    trap - ERR
    report_state failed \
        "{\"exit_code\":1,\"line\":${line},\"reason\":\"${reason}\"}" || true
    exit 1
}

cleanup() {
    rm -f "${JOIN_KEY}"
}

trap 'on_error "$LINENO"' ERR
trap cleanup EXIT

report_state first_boot_started

curl --fail --silent --show-error \
    --connect-timeout 5 \
    --max-time 15 \
    --retry 30 \
    --retry-delay 2 \
    --retry-connrefused \
    "${BASE_URL}/v1/join-key?mac=${MAC_ENCODED}&attempt=${ATTEMPT_ENCODED}" \
    --output "${JOIN_KEY}"
chmod 0600 "${JOIN_KEY}"

cat > /etc/apt/sources.list.d/debian.sources <<'EOF'
Types: deb
URIs: http://deb.debian.org/debian
Suites: trixie trixie-updates
Components: main contrib non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

cat > /etc/apt/sources.list.d/proxmox.sources <<'EOF'
Types: deb
URIs: http://download.proxmox.com/debian/pve
Suites: trixie
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF

cat > /etc/apt/sources.list.d/ceph.sources <<'EOF'
Types: deb
URIs: http://download.proxmox.com/debian/ceph-squid
Suites: trixie
Components: no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF

rm -f /etc/apt/sources.list.d/pve-enterprise.list
rm -f /etc/apt/sources.list.d/pve-enterprise.sources
rm -f /etc/apt/sources.list.d/ceph.list

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade
DEBIAN_FRONTEND=noninteractive apt-get install -y prometheus-node-exporter

cat > /etc/ssh/sshd_config.d/99-galaxy-proxmox.conf <<'EOF'
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
EOF
sshd -t
systemctl reload ssh

cat > /etc/hosts <<'EOF'
127.0.0.1 localhost.localdomain localhost
@@MANAGEMENT_IP@@ @@FQDN@@ @@HOSTNAME@@

::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

cat > /etc/resolv.conf <<'EOF'
search @@DOMAIN@@
nameserver @@MANAGEMENT_GATEWAY@@
EOF

cat > /etc/network/interfaces <<'EOF'
auto lo
iface lo inet loopback

iface nic0 inet manual

auto vmbr0
iface vmbr0 inet manual
    bridge-ports nic0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

auto vmbr0.70
iface vmbr0.70 inet static
    address @@MANAGEMENT_CIDR@@
    gateway @@MANAGEMENT_GATEWAY@@

auto vmbr0.71
iface vmbr0.71 inet static
    address @@CLUSTER_CIDR@@
#Cluster-Net Corosync link1

source /etc/network/interfaces.d/*
EOF

ifreload -a

ip -4 -o addr show dev vmbr0.70 | grep -Fq "inet @@MANAGEMENT_CIDR@@"
ip -4 -o addr show dev vmbr0.71 | grep -Fq "inet @@CLUSTER_CIDR@@"

install -d -m 0700 /root/.ssh
cat > /root/.ssh/config <<EOF
Host @@CLUSTER_PEER@@
    User root
    IdentityFile ${JOIN_KEY}
    IdentitiesOnly yes
    BatchMode yes
    ConnectTimeout 5
    StrictHostKeyChecking accept-new
EOF
chmod 0600 /root/.ssh/config

for attempt in $(seq 1 30); do
    if ssh -o BatchMode=yes -o ConnectTimeout=5 \
        root@@@CLUSTER_PEER@@ hostname; then
        break
    fi
    if [ "${attempt}" -eq 30 ]; then
        fail "join_ssh_unreachable" \
            "Grey did not accept the dedicated SSH join key."
    fi
    sleep 2
done

report_state network_ready

pvecm add @@CLUSTER_PEER@@ \
    --link0 address=@@MANAGEMENT_IP@@ \
    --link1 address=@@CLUSTER_IP@@ \
    --use_ssh

cluster_ready=false
for attempt in $(seq 1 60); do
    status="$(pvecm status 2>/dev/null || true)"
    nodes="$(pvecm nodes 2>/dev/null || true)"
    corosync_status="$(corosync-cfgtool -s 2>/dev/null || true)"
    links_ready=true

    printf '%s\n' "${status}" | grep -q "Name:[[:space:]]*Galaxy" || links_ready=false
    printf '%s\n' "${status}" | grep -q "Nodes:[[:space:]]*5" || links_ready=false
    printf '%s\n' "${status}" | grep -q "Quorate:[[:space:]]*Yes" || links_ready=false
    printf '%s\n' "${nodes}" | grep -q "@@HOSTNAME@@" || links_ready=false

    for link_id in 0 1; do
        link_block="$(
            printf '%s\n' "${corosync_status}" |
                awk -v target="${link_id}" '
                    $0 == "LINK ID " target " udp" { capture = 1; next }
                    /^LINK ID / { capture = 0 }
                    capture
                '
        )"
        if [ "${link_id}" -eq 0 ]; then
            expected_address="@@MANAGEMENT_IP@@"
        else
            expected_address="@@CLUSTER_IP@@"
        fi
        printf '%s\n' "${link_block}" |
            grep -Eq "^[[:space:]]*addr[[:space:]]*=[[:space:]]*${expected_address}$" ||
            links_ready=false
        connected_count="$(
            printf '%s\n' "${link_block}" | grep -c "connected$" || true
        )"
        test "${connected_count}" -eq 4 || links_ready=false
    done

    if [ "${links_ready}" = true ]; then
        cluster_ready=true
        break
    fi
    sleep 2
done

if [ "${cluster_ready}" != true ]; then
    fail "cluster_not_converged" \
        "Galaxy did not converge to five nodes with both Corosync links."
fi
printf '%s\n' "${corosync_status}"

report_state cluster_joined

systemctl enable --now prometheus-node-exporter
systemctl enable --now pve-firewall
systemctl is-active ssh pveproxy pvedaemon pve-cluster pve-firewall \
    prometheus-node-exporter
sshd -T | grep -q "^permitrootlogin without-password$"
sshd -T | grep -q "^passwordauthentication no$"
pvs --noheadings -o pv_name | grep -q "/dev/@@INSTALL_DISK@@p3"
if pvs --noheadings -o pv_name | grep -q "/dev/sda"; then
    fail "sata_became_lvm_pv" \
        "The untouched SATA disk unexpectedly became an LVM physical volume."
fi

report_state complete
"""


def _ip_from_cidr(cidr):
    return cidr.split("/", 1)[0]


def render_first_boot(mac, machine, base_url, attempt_id):
    normalized = normalize_mac(mac)
    substitutions = {
        "@@BASE_URL@@": base_url,
        "@@MAC_ENCODED@@": quote(normalized, safe=""),
        "@@ATTEMPT_ENCODED@@": quote(attempt_id, safe=""),
        "@@HOSTNAME@@": machine["hostname"],
        "@@DOMAIN@@": machine["domain"],
        "@@FQDN@@": f"{machine['hostname']}.{machine['domain']}",
        "@@MANAGEMENT_CIDR@@": machine["management_cidr"],
        "@@MANAGEMENT_IP@@": _ip_from_cidr(machine["management_cidr"]),
        "@@MANAGEMENT_GATEWAY@@": machine["management_gateway"],
        "@@CLUSTER_CIDR@@": machine["cluster_cidr"],
        "@@CLUSTER_IP@@": _ip_from_cidr(machine["cluster_cidr"]),
        "@@CLUSTER_PEER@@": machine["cluster_peer"],
        "@@CLUSTER_PEER_ADDRESS@@": machine["cluster_peer_address"],
        "@@INSTALL_DISK@@": machine["install_disk"],
    }
    result = FIRST_BOOT_TEMPLATE
    for marker, value in substitutions.items():
        result = result.replace(marker, value)
    return result


def read_public_keys(path):
    keys = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not keys:
        raise ValueError("root SSH key file contains no keys")
    return keys


def summarize_installer_result(payload):
    schema = payload.get("$schema") or payload.get("schema") or {}
    disks = payload.get("disks") or []
    boot_disks = []
    other_disks = []
    for disk in disks:
        if not isinstance(disk, dict):
            continue
        udev = disk.get("udev-properties") or disk.get("udev_properties") or {}
        path = (
            disk.get("path")
            or disk.get("device")
            or disk.get("name")
            or udev.get("DEVNAME")
        )
        if not path:
            continue
        if disk.get("is-bootdisk") or disk.get("is_bootdisk"):
            boot_disks.append(path)
        else:
            other_disks.append(path)
    interfaces = []
    for interface in (
        payload.get("network-interfaces")
        or payload.get("network_interfaces")
        or []
    ):
        if not isinstance(interface, dict):
            continue
        interfaces.append(
            {
                key: interface[key]
                for key in ("name", "mac", "address")
                if interface.get(key) is not None
            }
        )
    return {
        "schema_version": schema.get("version"),
        "fqdn": payload.get("fqdn"),
        "filesystem": payload.get("filesystem"),
        "boot_info": payload.get("boot-info") or payload.get("boot_info"),
        "boot_disks": boot_disks,
        "other_disks": other_disks,
        "network_interfaces": interfaces,
    }
