#!/usr/bin/env bash

set -euo pipefail

script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/../Scripts" && pwd)/disable-proxmox-subscription-popup.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "${test_root}"' EXIT

write_stock_fixture() {
    cat > "${test_root}/proxmoxlib.js" <<'EOF'
if (res.data.status.toLowerCase() !== 'active') {
    first();
}
const subscription = !(res.data.status.toLowerCase() !== 'active');
EOF
}

write_stock_fixture
GALAXY_PROXMOXLIB_PATH="${test_root}/proxmoxlib.js" \
GALAXY_RESTART_PVEPROXY=0 \
    bash "${script_path}" --apply
[[ "$(grep -Fc "res.data.status.toLowerCase() == 'NoMoreNagging'" "${test_root}/proxmoxlib.js")" -eq 2 ]]

GALAXY_PROXMOXLIB_PATH="${test_root}/proxmoxlib.js" \
GALAXY_RESTART_PVEPROXY=0 \
    bash "${script_path}" --apply

cat > "${test_root}/proxmoxlib.js" <<'EOF'
if (res.data.status.toLowerCase() !== 'active') {
    only_one();
}
EOF
if GALAXY_PROXMOXLIB_PATH="${test_root}/proxmoxlib.js" \
    GALAXY_RESTART_PVEPROXY=0 \
    bash "${script_path}" --apply; then
    echo "Unsupported one-match fixture was accepted" >&2
    exit 1
fi
[[ "$(grep -Fc "res.data.status.toLowerCase() !== 'active'" "${test_root}/proxmoxlib.js")" -eq 1 ]]

echo "subscription popup patch tests passed"
