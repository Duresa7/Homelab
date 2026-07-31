#!/usr/bin/env bash

set -euo pipefail

mode="${1:---apply}"
toolkit_file="${GALAXY_PROXMOXLIB_PATH:-/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js}"
restart_pveproxy="${GALAXY_RESTART_PVEPROXY:-1}"
stock_text="res.data.status.toLowerCase() !== 'active'"
patched_text="res.data.status.toLowerCase() == 'NoMoreNagging'"

case "${mode}" in
    --apply | --check) ;;
    *)
        echo "Usage: $0 [--apply|--check]" >&2
        exit 64
        ;;
esac

if [[ ! -f "${toolkit_file}" ]]; then
    echo "Missing proxmoxlib.js: ${toolkit_file}" >&2
    exit 2
fi

if [[ "${toolkit_file}" == "/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js" ]]; then
    toolkit_version="$(dpkg-query -W -f='${Version}' proxmox-widget-toolkit)"
else
    toolkit_version="fixture"
fi

stock_count="$(grep -Fc "${stock_text}" "${toolkit_file}" || true)"
patched_count="$(grep -Fc "${patched_text}" "${toolkit_file}" || true)"

if [[ "${patched_count}" -eq 2 && "${stock_count}" -eq 0 ]]; then
    echo "proxmox-widget-toolkit ${toolkit_version}: popup patch already present"
    exit 0
fi

if [[ "${stock_count}" -ne 2 || "${patched_count}" -ne 0 ]]; then
    echo "proxmox-widget-toolkit ${toolkit_version}: unsupported subscription-check layout" >&2
    exit 3
fi

if [[ "${mode}" == "--check" ]]; then
    echo "proxmox-widget-toolkit ${toolkit_version}: popup patch required"
    exit 1
fi

sed -i "s/${stock_text}/${patched_text}/g" "${toolkit_file}"

stock_count="$(grep -Fc "${stock_text}" "${toolkit_file}" || true)"
patched_count="$(grep -Fc "${patched_text}" "${toolkit_file}" || true)"
if [[ "${stock_count}" -ne 0 || "${patched_count}" -ne 2 ]]; then
    echo "proxmox-widget-toolkit ${toolkit_version}: post-patch verification failed" >&2
    exit 4
fi

if [[ "${restart_pveproxy}" == "1" ]]; then
    systemctl restart pveproxy
    systemctl is-active --quiet pveproxy
fi

echo "proxmox-widget-toolkit ${toolkit_version}: popup patch applied"
