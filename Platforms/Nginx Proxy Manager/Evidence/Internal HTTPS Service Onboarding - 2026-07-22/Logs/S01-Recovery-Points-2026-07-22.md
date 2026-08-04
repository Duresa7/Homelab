# Step 1 Recovery-Point Verification

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Capture date:** 2026-07-22 EDT; exact timestamp not retained  
**Mechanism:** SSH Manager  
**Targets:** `docker_network`, `docker_main`, `red_server`, `grey_server`, `security_01`

The exact archive-creation and verification commands, complete output streams, exit codes, & timestamps weren't retained outside the task transcript. I retained the observed artifact paths, hashes, sizes, permissions, & failure boundary below instead of reconstructing a transcript after the fact.

```text
NPM
/opt/docker/nginx-proxy-manager/backups/internal-https-2026-07-22-prechange/npm-state.tar.gz
SHA-256 6967c6dd7cd76d34a7a3abdb4156dfe4e84191f21c8258d466c6abd7278b7cec
Size 340K; mode 0600

Docker Main
/opt/docker/backups/internal-https-2026-07-22-prechange/docker-main-configs.tar.gz
SHA-256 8dc6e361375aa7f93760a70cb7c26aee97c0ecfe95bc35be61390718563bbadb
Size 8K

Media Stack
/var/lib/vz/dump/internal-https-2026-07-22-prechange/media-01-configs.tar.gz
SHA-256 97114cea42417ef24eff75f00cb43db44634d4a896688cdba8b659cddbfa88e7
Size 4K

Ansible
/var/lib/vz/dump/internal-https-2026-07-22-prechange/ansible-01-configs.tar.gz
SHA-256 85cd68768ed57f47c0d60fd0177e3a82d1590ccb66493baf24778c35d53dfb26
Size 4K

Security monitoring
/home/dkadi/backups/internal-https-2026-07-22-prechange/security-monitoring-compose-sanitized.tar.gz
Sanitized Compose backup; credential values excluded
```

The successful artifact checks returned the listed values. The first security and Splunk archive attempts hit file-permission errors. I replaced the security capture with a sanitized Compose archive and made no Splunk configuration change.

I deleted every archive created for this project later on 2026-07-22 at the owner's request. These recovery points are historical observations, not available rollback files. The exact deletion commands and final absence checks are in [Step 6 backup removal](S06-Backup-Removal-2026-07-22.md).
