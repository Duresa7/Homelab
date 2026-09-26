# Samba

**Created:** 2026-09-14  
**Last updated:** 2026-09-25

I run Samba on `ubuntu-dev` (VM 105, `192.168.40.179`) as a file server for my own machines. The versioned [configuration](Configuration/smb.conf) is the live `smb.conf`.

| Item | Value |
|---|---|
| Host | `ubuntu-dev`, VLAN 40 |
| Protocols | SMB2 (`SMB2_02`) to SMB3 only; NetBIOS off |
| Listener | TCP 445 on `lo` and `ens18` |
| Authentication | Samba user `dkadi`; file operations run as `ai-agent` (`force user`) |
| Guest access | Off (`map to guest = never`) |
| Client restriction | None in Samba; the upstream UniFi policy decides who reaches TCP 445 |

## Shares

| Share | Path | Access |
|---|---|---|
| `ai-agent` | `/home/ai-agent` | Read-write, `dkadi` only, dot-files visible, links cannot escape the tree |
| `shared-folder` | `/home/ai-agent/Documents/shared-folder` | Read-write, `dkadi` only; added 2026-09-14 |

New files get no group or other permission bits (`create mask = 0700`, `force create mode = 0600`), directories are `0700`, and both are owned by `ai-agent`. The `catia`, `fruit` and `streams_xattr` modules keep macOS metadata and filenames intact.

Addresses: `\\192.168.40.179\shared-folder` from Windows, `smb://192.168.40.179/shared-folder` from a Linux or macOS file manager.

## Records

- [Configuration](Configuration/smb.conf)
- [Shared Folder Share - 2026-09-14](Documentation/Change%20Records/Shared%20Folder%20Share%20-%202026-09-14.md)
