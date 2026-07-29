#!/usr/bin/env bash
set -euo pipefail

readonly role="${1:?role is required: target, malware, or evidence}"
readonly desktop_user="${2:?desktop user is required}"
readonly kds_url="https://kasm-static-content.s3.us-east-1.amazonaws.com/kasm_linux_service_installer_x86_64_1.8_8e3b288d3.deb"
readonly kds_sha256="25613f3979eb2596c3d7a289d2e49fa26670fc77397615f3f53afbf59f959e32"
readonly kds_package="/tmp/kasm-desktop-service-1.8-amd64.deb"

case "$role" in
    target|malware|evidence) ;;
    *) echo "unsupported role: $role" >&2; exit 2 ;;
esac

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get -y full-upgrade
apt-get install -y \
    xfce4 \
    xrdp \
    xorgxrdp \
    dbus-x11 \
    qemu-guest-agent \
    curl \
    ca-certificates \
    rclone \
    gnome-screenshot

if [[ "$role" == "target" ]]; then
    apt-get install -y nginx
else
    apt-get install -y yara clamav tcpdump
fi

curl --fail --location --retry 3 --output "$kds_package" "$kds_url"
printf '%s  %s\n' "$kds_sha256" "$kds_package" | sha256sum --check -
apt-get install -y "$kds_package"

install -d -m 0755 /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/10-kasm-lab-baseline.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
EOF

passwd -l root
usermod -aG ssl-cert "$desktop_user"
printf '%s\n' 'startxfce4' > "/home/${desktop_user}/.xsession"
chown "${desktop_user}:${desktop_user}" "/home/${desktop_user}/.xsession"
chmod 0600 "/home/${desktop_user}/.xsession"

systemctl enable ssh qemu-guest-agent xrdp kasm-desktop
systemctl restart ssh xrdp kasm-desktop
systemctl start qemu-guest-agent
if [[ "$role" == "target" ]]; then
    systemctl enable --now nginx
fi

install -d -o root -g root -m 0755 /var/lib/kasm-lab
printf '%s\n' "$role" > /var/lib/kasm-lab/template-role
sha256sum "$kds_package" > /var/lib/kasm-lab/kasm-desktop-service.sha256
date -u +%Y-%m-%dT%H:%M:%SZ > /var/lib/kasm-lab/template-configured

rm -f "$kds_package"
apt-get clean
