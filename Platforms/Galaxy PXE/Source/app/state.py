#!/usr/bin/env python3

import argparse
import json

from registry import MachineRegistry


def parse_args():
    parser = argparse.ArgumentParser(description="Manage Galaxy PXE machine state")
    parser.add_argument("--machines", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("mac")
    parser.add_argument(
        "state",
        nargs="?",
        choices=["disabled", "ready"],
        help="Omit this value to display the current state.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required to rearm an active or finished machine.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Display the full provisioning-attempt record.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    registry = MachineRegistry(args.machines, args.state_file)
    if args.state:
        registry.set_state(args.mac, args.state, force=args.force)
    if args.json:
        print(json.dumps(registry.record(args.mac), indent=2, sort_keys=True))
    else:
        print(registry.status(args.mac))


if __name__ == "__main__":
    main()
