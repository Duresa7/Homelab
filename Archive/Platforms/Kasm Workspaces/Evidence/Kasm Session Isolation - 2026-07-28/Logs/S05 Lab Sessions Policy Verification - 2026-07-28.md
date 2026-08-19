# S05 Lab Sessions Policy Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture timestamp:** 2026-07-28T14:41:14-04:00  
**Target:** `kasm-01`, Kasm PostgreSQL database in `kasm_db`  
**Mechanism:** SSH Manager MCP to `purple-server`, Proxmox QEMU guest agent, guest Bash, `psql`

## Exact command

```bash
qm guest exec 122 -- /bin/bash -lc 'date -Is; docker exec kasm_db psql -U kasmapp -d kasm -P pager=off -F "|" -Atc "SELECT g.name,g.priority,g.description,count(ug.user_group_id) FROM groups g LEFT JOIN user_groups ug ON ug.group_id=g.group_id WHERE g.name=E'\''Lab Sessions'\'' GROUP BY g.group_id,g.name,g.priority,g.description; SELECT gs.name,gs.value FROM group_settings gs JOIN groups g ON g.group_id=gs.group_id WHERE g.name=E'\''Lab Sessions'\'' ORDER BY gs.name;"'
```

## Complete guest-agent result

```json
{
  "exitcode": 0,
  "exited": 1,
  "out-data": "2026-07-28T14:41:14-04:00\nLab Sessions|100|Disposable isolated security lab sessions|1\nallow_kasm_clipboard_down|False\nallow_kasm_clipboard_seamless|False\nallow_kasm_clipboard_up|False\nallow_kasm_downloads|False\nallow_kasm_uploads|True\nallow_persistent_profile|False\nsession_time_limit|3600\n"
}
```

**Standard error:** empty  
**SSH Manager exit code:** 0  
**Structured result:** `success: true`

The query is the follow-up verification. It returns one member and the seven policy values required by the plan without returning the member's account name.
