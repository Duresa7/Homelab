# Syncthing

**Created:** 2026-07-22  
**Last updated:** 2026-08-06

> Retired on 2026-08-06. I destroyed the container, the image, the configuration, the 17-file server vault copy, and its version history, and I cleared the DNS record, NPM proxy host, and Prometheus probe. Nothing below is live and there is no backup. The Windows vault at `D:\Documents\Vault-DK\The Vault` was untouched and is now the only copy. See the [decommission record](Documentation/Change%20Records/Syncthing%20Decommission%20-%202026-08-06.md).

I ran Syncthing 2.1.2 on `docker-main` as an always-on peer for my Obsidian vault. The Windows working copy stayed at `D:\Documents\Vault-DK\The Vault`; `docker-main` stored the synchronized copy under `/data/syncthing/vaults/the-vault`.

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
| GUI | Server: `https://syncthing.alphasecunited.com` through NPM; Windows: `127.0.0.1:8384` |
| Transfer listeners | TCP/UDP 22000; UDP 21027 discovery |

## Layout

- `Configuration/` contains the versioned Compose definition.
- `Documentation/` contains the deployment, operating procedure, troubleshooting index, & decommission record.
- `Evidence/` contains the retained verification result from the first deployment.

## Key Records

- [Decommission](Documentation/Change%20Records/Syncthing%20Decommission%20-%202026-08-06.md)
- [Deployment and operations](Documentation/Deployment.md)
- [Add another Windows, macOS, or Linux device](Documentation/Adding%20a%20Device.md)
- [Obsidian sync alternatives research](Documentation/Obsidian%20Sync%20Alternatives%20-%202026-07-27.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Internal HTTPS onboarding](../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
