# S03 Gate, Group, and Workspace State

**Created:** 2026-07-28  
**Last updated:** 2026-07-29

**Capture time:** 2026-07-28 EDT  
**Target:** Kasm Workspaces 1.19.0 on `kasm-01`  
**Mechanism:** SSH Manager MCP, Kasm API, Kasm PostgreSQL readback, and Docker inspection

## Step 3 gate

I created `Debian - Target 77` from the existing Debian image and assigned it only to `Lab Sessions`. The live container joined only `lab77` at `192.168.77.208` and carried `HostConfig.Dns=["192.168.77.10"]`.

Docker placed `127.0.0.11` in the container's generated `/etc/resolv.conf` and recorded `ExtServers: [192.168.77.10]` in the file comment. A packet capture showed only ARP attempts for `192.168.77.10`, followed by `SERVFAIL`, with no query sent to another resolver. I accepted the verified traffic path even though the generated file did not contain the literal nameserver line expected by the plan.

I did not retain the original raw command and packet-capture transcript. This section records the observed values and result; I am not reconstructing output after the session was destroyed.

## Lab Sessions policy

I added `alpha` to `Lab Sessions` and read the effective values from `group_settings`:

```text
allow_kasm_clipboard_down=False
allow_kasm_clipboard_seamless=False
allow_kasm_clipboard_up=False
allow_kasm_downloads=False
allow_kasm_microphone=False
allow_kasm_printing=False
allow_kasm_sharing=False
allow_kasm_uploads=True
allow_persistent_profile=True
allow_user_storage_mapping=False
max_kasms_per_user=2
session_time_limit=3600
```

`All Users` settings and the `<YOUR_ADMIN_USERNAME>` membership rows did not change.

## Persistent profiles

I created six host directories beneath `/var/lib/kasm-profiles`: `claude-code`, `codex-cli`, `terminal-trusted`, `nessus`, `hunchly`, and `telegram`. Each directory initially read back as UID 1000, GID 1000, and mode 0750. The real Terminal launch widened `terminal-trusted` to 0777. The final review caught that drift, and I restored all six directories to 0750 before replacing the final snapshot.

## Workspace inventory

I created 19 isolated definitions:

```text
lab75: Claude Code, Codex CLI, Terminal
lab74: Chrome, Tor, Kali, Nessus, Hunchly, Telegram, Spiderfoot, Forensic OSINT, Cyberbro, Terminal
lab77: REMnux, Debian, Fedora, Terminal
lab79: REMnux, Debian
```

Each definition belonged only to `Lab Sessions`, carried its required network and DNS override, and retained the source image's hostname, user, and environment entries. Only the six named tools carried a persistent profile bind. I appended ` (UNISOLATED)` to the 15 original definitions, moved them to `Unisolated - Management Network`, and left them assigned only to `All Users`.

An API request authenticated as `alpha` returned 34 definitions: 19 isolated lane definitions and 15 unisolated originals.
