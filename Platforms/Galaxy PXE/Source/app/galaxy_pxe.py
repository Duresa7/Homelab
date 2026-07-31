#!/usr/bin/env python3

import argparse

from registry import MachineRegistry, VALID_STATES
from rendering import (
    find_mac_address,
    normalize_mac,
    render_answer,
    render_boot_script,
    render_first_boot,
    summarize_installer_result,
)
from service import (
    build_server,
    stream_file_response,
    validate_runtime_inputs,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Galaxy Proxmox PXE service")
    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--machines", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--root-hash", required=True)
    parser.add_argument("--root-ssh-keys", required=True)
    parser.add_argument("--join-key", required=True)
    return parser.parse_args()


def main():
    server = build_server(parse_args())
    server.serve_forever()


if __name__ == "__main__":
    main()
