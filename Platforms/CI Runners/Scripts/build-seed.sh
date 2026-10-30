#!/bin/bash
# Render the ci-k3s-01 autoinstall template and build the CIDATA seed ISO on green-server.
# Run from ubuntu-dev. Needs SSH as root to the node and as ansible to ansible-01.
# The dkadi hash is a throwaway: account-passwords.yml sets the real password later.
# Nothing secret is written locally; the rendered user-data exists only on the node
# and is deleted after the install (see the runbook).
set -euo pipefail
NODE=${NODE:-192.168.70.14}
T="$(dirname "$0")/../Configuration/ci-k3s-01-autoinstall.yaml"
CK=$(ssh -o BatchMode=yes ansible@192.168.40.36 'cut -d" " -f1,2,3 ~/.ssh/id_ed25519.pub')
UK=$(cut -d' ' -f1,2,3 ~/.ssh/id_ed25519.pub)
H=$(openssl passwd -6 "$(openssl rand -base64 33)")
python3 - "$T" "$H" "$UK" "$CK" <<'EOF' | ssh -o BatchMode=yes root@"$NODE" 'umask 077; d=/root/ci-k3s-01-seed; rm -rf $d; mkdir -p $d; cat > $d/user-data; printf "instance-id: ci-k3s-01\nlocal-hostname: ci-k3s-01\n" > $d/meta-data; rm -f /var/lib/vz/template/iso/ci-k3s-01-seed.iso; genisoimage -quiet -output /var/lib/vz/template/iso/ci-k3s-01-seed.iso -volid CIDATA -joliet -rock $d/user-data $d/meta-data; echo placeholders_left=$(grep -c "__[A-Z_]*__" $d/user-data || true)'
import sys, yaml
t = open(sys.argv[1]).read()
out = "#cloud-config\nautoinstall:" + t.split("autoinstall:", 1)[1]
out = out.replace("__DKADI_HASH__", sys.argv[2]).replace("__UBUNTU_DEV_KEY__", sys.argv[3]).replace("__CONTROLLER_KEY__", sys.argv[4])
d = yaml.safe_load(out)["autoinstall"]
# A late command containing ": " parses as a mapping and subiquity aborts.
assert all(isinstance(x, str) for x in d["late-commands"]), "late-commands must all be strings"
sys.stdout.write(out)
EOF
