#!/usr/bin/env python3
"""Write the live ssh-mcp config: the tracked config plus a trustedHostKey pin per profile.

    pin-host-keys.py <tracked config.toml> <known_hosts> > config.toml

Each pin is the SHA256 fingerprint of the host key ssh-mcp will negotiate, taken from
known_hosts. ssh-mcp prefers ed25519, then ECDSA, then RSA, so the pin follows the same
order. A profile with no known_hosts entry stops the run: under --hostKeyMode=strict an
unpinned profile cannot connect at all.
"""
import re
import subprocess
import sys
import tomllib

PREFERENCE = ["ED25519", "ECDSA", "RSA"]


def fingerprints(host: str, port: int, known_hosts: str) -> dict[str, str]:
    name = host if port == 22 else f"[{host}]:{port}"
    found = subprocess.run(
        ["ssh-keygen", "-F", name, "-f", known_hosts], capture_output=True, text=True
    ).stdout
    lines = [line for line in found.splitlines() if line and not line.startswith("#")]
    if not lines:
        return {}
    listed = subprocess.run(
        ["ssh-keygen", "-l", "-f", "/dev/stdin"],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    keys = {}
    for line in listed.splitlines():
        match = re.match(r"\d+ (SHA256:\S+) .*\((\w+)\)$", line)
        if match:
            keys.setdefault(match.group(2), match.group(1))
    return keys


def main() -> None:
    tracked, known_hosts = sys.argv[1], sys.argv[2]
    text = open(tracked, encoding="utf-8").read()
    config = tomllib.loads(text)
    pins = {}
    for profile in config["profiles"]:
        keys = fingerprints(profile["host"], profile.get("port", 22), known_hosts)
        kind = next((k for k in PREFERENCE if k in keys), None)
        if kind is None:
            sys.exit(f"no known_hosts entry for {profile['name']} ({profile['host']})")
        pins[profile["name"]] = keys[kind]

    out, current = [], None
    for line in text.splitlines():
        out.append(line)
        name = re.match(r'name = "([^"]+)"$', line)
        if name:
            current = name.group(1)
        if current and line.startswith("host = "):
            out.append(f'trustedHostKey = "{pins[current]}"')
            current = None
    print("\n".join(out))


if __name__ == "__main__":
    main()
