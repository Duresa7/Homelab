#!/usr/bin/env python3

import argparse
import json
import socket
import struct
import subprocess
import time


def encode_varint(value: int) -> bytes:
    value &= 0xFFFFFFFF
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        output.append(byte)
        if not value:
            return bytes(output)


def read_exact(stream: socket.socket, length: int) -> bytes:
    output = bytearray()
    while len(output) < length:
        chunk = stream.recv(length - len(output))
        if not chunk:
            raise ConnectionError("connection closed before the response completed")
        output.extend(chunk)
    return bytes(output)


def read_varint(stream: socket.socket) -> int:
    value = 0
    for index in range(5):
        byte = read_exact(stream, 1)[0]
        value |= (byte & 0x7F) << (7 * index)
        if not byte & 0x80:
            return value
    raise ValueError("VarInt exceeds five bytes")


def packet(payload: bytes) -> bytes:
    return encode_varint(len(payload)) + payload


def text_description(value) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    parts = [str(value.get("text", ""))]
    parts.extend(text_description(item) for item in value.get("extra", []))
    return "".join(parts)


def resolve_srv(host: str, timeout: float) -> tuple[str, int]:
    result = subprocess.run(
        [
            "dig",
            f"+time={max(1, round(timeout))}",
            "+tries=1",
            "+short",
            "SRV",
            f"_minecraft._tcp.{host.rstrip('.')}",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout + 1,
    )
    records = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 4:
            continue
        priority, weight, port, target = fields
        records.append((int(priority), -int(weight), target.rstrip("."), int(port)))
    if not records:
        raise LookupError(f"no Minecraft SRV record found for {host}")
    _, _, target, port = min(records)
    return target, port


def query(
    connect_host: str,
    port: int,
    timeout: float,
    display_host: str | None = None,
) -> dict:
    encoded_host = connect_host.encode("utf-8")
    handshake = (
        encode_varint(767)
        + encode_varint(len(encoded_host))
        + encoded_host
        + struct.pack(">H", port)
        + encode_varint(1)
    )

    started = time.monotonic()
    with socket.create_connection((connect_host, port), timeout=timeout) as stream:
        stream.settimeout(timeout)
        stream.sendall(packet(encode_varint(0) + handshake))
        stream.sendall(packet(encode_varint(0)))
        read_varint(stream)
        packet_id = read_varint(stream)
        if packet_id != 0:
            raise ValueError(f"unexpected response packet id {packet_id}")
        payload_length = read_varint(stream)
        response = json.loads(read_exact(stream, payload_length).decode("utf-8"))

    players = response.get("players", {})
    version = response.get("version", {})
    return {
        "host": display_host or connect_host,
        "port": port,
        "latency_ms": round((time.monotonic() - started) * 1000, 1),
        "version_name": version.get("name"),
        "protocol": version.get("protocol"),
        "players_online": players.get("online"),
        "players_max": players.get("max"),
        "description": text_description(response.get("description")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Query a Minecraft Java status endpoint.")
    parser.add_argument("host")
    parser.add_argument("--port", type=int)
    parser.add_argument(
        "--srv",
        action="store_true",
        help="resolve _minecraft._tcp SRV and query its target without disclosing it",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if args.srv and args.port is not None:
        parser.error("--srv and --port cannot be used together")

    if args.srv:
        connect_host, port = resolve_srv(args.host, args.timeout)
        display_host = args.host
    else:
        connect_host = args.host
        port = args.port or 25565
        display_host = None

    print(
        json.dumps(
            query(connect_host, port, args.timeout, display_host=display_host),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
