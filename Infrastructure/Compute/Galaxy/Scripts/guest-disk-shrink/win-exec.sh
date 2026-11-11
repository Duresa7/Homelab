#!/bin/bash
# usage: win-exec.sh <vmid> <script.ps1> [targetGiB] -- runs a script in the guest as SYSTEM
set -euo pipefail
V=$1; S=$2; T=$(( ${3:-0} * 1024 * 1024 * 1024 ))
B=$(sed "s/__TARGET__/$T/" "$S" | iconv -f UTF-8 -t UTF-16LE | base64 -w0)
qm guest exec "$V" --timeout 900 -- powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand "$B" | python3 -c 'import json,sys,re; d=json.load(sys.stdin); print(d.get("out-data","")); e=re.sub(r"<Objs.*?</Objs>","",d.get("err-data",""),flags=re.S).replace("#< CLIXML","").strip(); print("ERR:",e) if e else None; print("exitcode", d.get("exitcode"))'
