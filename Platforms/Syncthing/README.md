# Syncthing

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

I run Syncthing 2.1.2 on `docker-main` as an always-on peer for my Obsidian vault. The Windows working copy stays at `D:\Documents\Vault-DK\The Vault`; `docker-main` stores the synchronized copy under `/data/syncthing/vaults/the-vault`.

## Deployment

| Item | Value |
|---|---|
| Server | `docker-main` (`192.168.40.35`) |
| Container | `syncthing` |
| Image | `syncthing/syncthing:2.1.2` |
| Compose file | `/opt/docker/syncthing/docker-compose.yml` |
| Persistent configuration | `/opt/docker/syncthing/config` |
| Server vault | `/data/syncthing/vaults/the-vault` |
| Server versions | `/data/syncthing/versions/the-vault` |
| Windows vault | `D:\Documents\Vault-DK\The Vault` |
| Folder ID | `obsidian-the-vault` |
| Version retention | Staggered, 90 days |
| GUI | `127.0.0.1:8384` on each peer |
| Transfer listeners | TCP/UDP 22000; UDP 21027 discovery |

## Layout

- `Configuration/` contains the versioned Compose definition.
- `Documentation/` contains the deployment, operating procedure, troubleshooting index, & backlog.
- `Evidence/` contains the retained verification result from the first deployment.

## Key Records

- [Deployment and operations](Documentation/Deployment.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform TODO](Documentation/TODO.md)

