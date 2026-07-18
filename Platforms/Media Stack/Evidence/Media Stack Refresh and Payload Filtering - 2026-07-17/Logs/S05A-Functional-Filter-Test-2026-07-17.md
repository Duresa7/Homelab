# S05A qBittorrent Functional Filter-Test Transcript

**Created:** 2026-07-17  
**Last updated:** 2026-07-17

**Capture timestamp:** 2026-07-17T21:32:51-04:00  
**Target:** `red_server`, Proxmox CT 842 `media-01`  
**Mechanism:** SSH Manager command execution; host shell invoking `pct exec`; guest POSIX shell  
**Working paths:** `/tmp/qbit-filter-source-20260717` and `/tmp/qbit-filter-verification-20260717.torrent`

## Purpose

Verify qBittorrent's filename filter with harmless one-byte placeholders and no public tracker or swarm. The test intentionally expected `.exe` and `.ps1` to receive priority `0`, while `.mkv` and `.zip` retained priority `1` because archives are not part of the deployed baseline.

## Test Command

The command first asserted that both fixed temporary paths were absent. The base64 value decodes to a Python script that creates four one-byte placeholder files and a trackerless v1 torrent, then prints its deterministic info hash. qBittorrent added it stopped, the API priorities were asserted, and the exact torrent and temporary source paths were removed.

```sh
pct exec 842 -- sh -lc 'set -eu; test ! -e /tmp/qbit-filter-source-20260717; test ! -e /tmp/qbit-filter-verification-20260717.torrent; hash=$(printf %s aW1wb3J0IGhhc2hsaWIKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpzb3VyY2UgPSBQYXRoKCcvdG1wL3FiaXQtZmlsdGVyLXNvdXJjZS0yMDI2MDcxNycpCnNvdXJjZS5ta2Rpcihtb2RlPTBvNzAwLCBleGlzdF9vaz1GYWxzZSkKZm9yIG5hbWUgaW4gKCdzYW1wbGUtdmlkZW8ubWt2JywgJ2Jsb2NrZWQtdGVzdC5leGUnLCAnYmxvY2tlZC10ZXN0LnBzMScsICdhbGxvd2VkLWFyY2hpdmUuemlwJyk6CiAgICAoc291cmNlIC8gbmFtZSkud3JpdGVfYnl0ZXMoYid4JykKCmRlZiBiZW5jb2RlKHZhbHVlKToKICAgIGlmIGlzaW5zdGFuY2UodmFsdWUsIGJ5dGVzKToKICAgICAgICByZXR1cm4gc3RyKGxlbih2YWx1ZSkpLmVuY29kZSgpICsgYic6JyArIHZhbHVlCiAgICBpZiBpc2luc3RhbmNlKHZhbHVlLCBpbnQpOgogICAgICAgIHJldHVybiBiJ2knICsgc3RyKHZhbHVlKS5lbmNvZGUoKSArIGInZScKICAgIGlmIGlzaW5zdGFuY2UodmFsdWUsIGxpc3QpOgogICAgICAgIHJldHVybiBiJ2wnICsgYicnLmpvaW4oYmVuY29kZShpdGVtKSBmb3IgaXRlbSBpbiB2YWx1ZSkgKyBiJ2UnCiAgICBpZiBpc2luc3RhbmNlKHZhbHVlLCBkaWN0KToKICAgICAgICByZXR1cm4gYidkJyArIGInJy5qb2luKGJlbmNvZGUoa2V5KSArIGJlbmNvZGUodmFsdWVba2V5XSkgZm9yIGtleSBpbiBzb3J0ZWQodmFsdWUpKSArIGInZScKICAgIHJhaXNlIFR5cGVFcnJvcih0eXBlKHZhbHVlKSkKCmZpbGVzID0gW10KcGF5bG9hZCA9IGInJwpmb3IgcGF0aCBpbiBzb3J0ZWQoc291cmNlLml0ZXJkaXIoKSwga2V5PWxhbWJkYSBpdGVtOiBpdGVtLm5hbWUpOgogICAgZGF0YSA9IHBhdGgucmVhZF9ieXRlcygpCiAgICBwYXlsb2FkICs9IGRhdGEKICAgIGZpbGVzLmFwcGVuZCh7YidsZW5ndGgnOiBsZW4oZGF0YSksIGIncGF0aCc6IFtwYXRoLm5hbWUuZW5jb2RlKCldfSkKaW5mbyA9IHsKICAgIGInZmlsZXMnOiBmaWxlcywKICAgIGInbmFtZSc6IGIncWJpdC1maWx0ZXItdmVyaWZpY2F0aW9uJywKICAgIGIncGllY2UgbGVuZ3RoJzogMTYzODQsCiAgICBiJ3BpZWNlcyc6IGhhc2hsaWIuc2hhMShwYXlsb2FkKS5kaWdlc3QoKSwKfQp0b3JyZW50ID0ge2InY3JlYXRlZCBieSc6IGInQ29kZXggbG9jYWwgZmlsdGVyIHZlcmlmaWNhdGlvbicsIGInaW5mbyc6IGluZm99ClBhdGgoJy90bXAvcWJpdC1maWx0ZXItdmVyaWZpY2F0aW9uLTIwMjYwNzE3LnRvcnJlbnQnKS53cml0ZV9ieXRlcyhiZW5jb2RlKHRvcnJlbnQpKQpwcmludChoYXNobGliLnNoYTEoYmVuY29kZShpbmZvKSkuaGV4ZGlnZXN0KCkp | base64 -d | python3); echo test-hash=$hash; result=$(curl -fsS -F torrents=@/tmp/qbit-filter-verification-20260717.torrent -F stopped=true -F savepath=/data/downloads/incomplete/qbit-filter-verification http://127.0.0.1:8080/api/v2/torrents/add); echo add-result=$result; sleep 2; files=$(docker exec gluetun wget -qO- "http://127.0.0.1:8080/api/v2/torrents/files?hash=$hash"); printf "%s" "$files" | jq "map({name,priority})"; printf "%s" "$files" | jq -e '"'"'(.[] | select(.name|endswith(".exe")) | .priority) == 0 and (.[] | select(.name|endswith(".ps1")) | .priority) == 0 and (.[] | select(.name|endswith(".mkv")) | .priority) > 0 and (.[] | select(.name|endswith(".zip")) | .priority) > 0'"'"' >/dev/null; echo priority-check=passed; docker exec gluetun wget -qO- --post-data="hashes=$hash&deleteFiles=true" http://127.0.0.1:8080/api/v2/torrents/delete; rm -f -- /tmp/qbit-filter-verification-20260717.torrent; rm -rf -- /tmp/qbit-filter-source-20260717; test "$(docker exec gluetun wget -qO- "http://127.0.0.1:8080/api/v2/torrents/info?hashes=$hash" | jq length)" -eq 0; test ! -e /tmp/qbit-filter-verification-20260717.torrent; test ! -e /tmp/qbit-filter-source-20260717; echo cleanup-check=passed'
```

## Complete Result

Standard output:

```text
test-hash=e280806b676f58c1194617d7c1ff7d62eb7f6d18
add-result={"added_torrent_ids":["e280806b676f58c1194617d7c1ff7d62eb7f6d18"],"failure_count":0,"pending_count":0,"success_count":1}
[
  {
    "name": "qbit-filter-verification/allowed-archive.zip",
    "priority": 1
  },
  {
    "name": "qbit-filter-verification/blocked-test.exe",
    "priority": 0
  },
  {
    "name": "qbit-filter-verification/blocked-test.ps1",
    "priority": 0
  },
  {
    "name": "qbit-filter-verification/sample-video.mkv",
    "priority": 1
  }
]
priority-check=passed
cleanup-check=passed
```

Standard error: empty  
Exit code: `0`

## Verification Result

The executable and PowerShell placeholder names were filtered, ordinary media stayed selected, the deliberately allowed archive policy behaved as documented, and both the torrent and fixed temporary paths were absent after cleanup.
