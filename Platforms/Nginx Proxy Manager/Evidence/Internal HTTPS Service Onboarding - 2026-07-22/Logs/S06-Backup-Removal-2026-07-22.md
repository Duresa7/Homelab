# Step 6 Backup Removal

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Deletion date:** 2026-07-22 EDT; exact deletion timestamps not retained  
**Final verification:** 2026-07-22 15:48:54 through 15:48:55 EDT  
**Mechanism:** SSH Manager one-shot commands  
**Targets:** `docker_network`, `docker_main`, `red_server`, `grey_server`, `security_01`  
**Working directory:** SSH Manager configured default on each target

I resolved and inspected each named file before deletion. All five documented files matched their expected absolute paths. The security project directory also contained a 423-byte `security-ui-configs.tar.gz` archive from the earlier capture attempt, so I removed it after listing that exact directory.

## Deletion Commands and Results

### docker_network

```text
Command:
rm -- /opt/docker/nginx-proxy-manager/backups/internal-https-2026-07-22-prechange/npm-state.tar.gz && rmdir -- /opt/docker/nginx-proxy-manager/backups/internal-https-2026-07-22-prechange

stdout: empty
stderr: empty
exit code: 0
```

### docker_main

```text
Command:
rm -- /opt/docker/backups/internal-https-2026-07-22-prechange/docker-main-configs.tar.gz && rmdir -- /opt/docker/backups/internal-https-2026-07-22-prechange

stdout: empty
stderr: empty
exit code: 0
```

### red_server

```text
Command:
rm -- /var/lib/vz/dump/internal-https-2026-07-22-prechange/media-01-configs.tar.gz

stdout: empty
stderr: empty
exit code: 0
```

### grey_server

```text
Command:
rm -- /var/lib/vz/dump/internal-https-2026-07-22-prechange/ansible-01-configs.tar.gz

stdout: empty
stderr: empty
exit code: 0
```

### security_01

The first command removed the named sanitized archive, but `rmdir` returned exit code 1 because one other project-created file remained.

```text
Command:
rm -- /home/dkadi/backups/internal-https-2026-07-22-prechange/security-monitoring-compose-sanitized.tar.gz && rmdir -- /home/dkadi/backups/internal-https-2026-07-22-prechange

stdout: empty
stderr:
rmdir: failed to remove '/home/dkadi/backups/internal-https-2026-07-22-prechange': Directory not empty
exit code: 1
```

I listed only the exact project directory:

```text
Command:
find /home/dkadi/backups/internal-https-2026-07-22-prechange -mindepth 1 -maxdepth 1 -printf '%y %f %s bytes\n'

stdout:
f security-ui-configs.tar.gz 423 bytes
stderr: empty
exit code: 0
```

I then removed that file and its empty project directory:

```text
Command:
rm -- /home/dkadi/backups/internal-https-2026-07-22-prechange/security-ui-configs.tar.gz && rmdir -- /home/dkadi/backups/internal-https-2026-07-22-prechange

stdout: empty
stderr: empty
exit code: 0
```

## Final Verification

Each command below returned exit code 0.

```text
docker_network command:
date -Is; test ! -e /opt/docker/nginx-proxy-manager/backups/internal-https-2026-07-22-prechange && printf 'absent: NPM project backup directory\n'
stdout:
2026-07-22T15:48:54-04:00
absent: NPM project backup directory

docker_main command:
date -Is; test ! -e /opt/docker/backups/internal-https-2026-07-22-prechange && printf 'absent: Docker Main project backup directory\n'
stdout:
2026-07-22T19:48:55+00:00
absent: Docker Main project backup directory

red_server command:
date -Is; test ! -e /var/lib/vz/dump/internal-https-2026-07-22-prechange/media-01-configs.tar.gz && printf 'absent: Media Stack project backup\n'
stdout:
2026-07-22T15:48:55-04:00
absent: Media Stack project backup

grey_server command:
date -Is; test ! -e /var/lib/vz/dump/internal-https-2026-07-22-prechange/ansible-01-configs.tar.gz && printf 'absent: Ansible project backup\n'
stdout:
2026-07-22T15:48:55-04:00
absent: Ansible project backup

security_01 command:
date -Is; test ! -e /home/dkadi/backups/internal-https-2026-07-22-prechange && printf 'absent: security project backup directory\n'
stdout:
2026-07-22T19:48:55+00:00
absent: security project backup directory
```

The NPM, Docker Main, & security project directories are absent. The two archives stored directly in `/var/lib/vz/dump` are absent. I didn't remove any unrelated backup.
