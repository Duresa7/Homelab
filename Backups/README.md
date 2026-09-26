# Backups

**Created:** 2026-08-05  
**Last updated:** 2026-09-25

This folder holds config files I copied off a host before editing them. It exists so a host does not have to keep the copy.

## Index

| File | Source host | Taken | Record |
|---|---|---|---|
| [`ansible-01-sshd_config-2026-08-15`](ansible-01-sshd_config-2026-08-15) | ansible-01 | 2026-08-15 | [Root SSH disabled](../Operations/Maintenance/Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md) |
| [`ansible-01-tftpd-hpa-before-migration-2026-09-12.conf`](ansible-01-tftpd-hpa-before-migration-2026-09-12.conf) | ansible-01 | 2026-09-12 | [ansible-01 Blue migration](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md) |
| [`docker-blue-docker-compose-2026-09-02.yml`](docker-blue-docker-compose-2026-09-02.yml) | docker-blue | 2026-09-02 | [SSH Manager gateway process exhaustion](../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/SSH%20Manager%20Gateway%20Process%20Exhaustion%20-%202026-09-02.md) |
| [`docker-blue-meshcentral-config-pre-proxy-2026-09-13.json`](docker-blue-meshcentral-config-pre-proxy-2026-09-13.json) | docker-blue | 2026-09-13 | [MeshCentral internal HTTPS](../Platforms/MeshCentral/Documentation/Change%20Records/Internal%20HTTPS%20Through%20Nginx%20Proxy%20Manager%20-%202026-09-13.md) |
| [`docker-main-immich-docker-compose-2026-09-05.yml`](docker-main-immich-docker-compose-2026-09-05.yml) | docker-main | 2026-09-05 | [Immich NVENC transcoding](../Platforms/Immich/Documentation/Change%20Records/GTX%201080%20Ti%20NVENC%20Transcoding%20-%202026-09-05.md) |
| [`docker-main-ossec.conf-2026-09-06`](docker-main-ossec.conf-2026-09-06) | docker-main | 2026-09-06 | [docker-main agent re-enrollment](../Platforms/Wazuh/Documentation/Change%20Records/docker-main%20Agent%20Re-enrollment%20-%202026-09-06.md) |
| [`docker-network-nginx-proxy-manager-docker-compose-2026-09-25.yml`](docker-network-nginx-proxy-manager-docker-compose-2026-09-25.yml) | docker-network | 2026-09-25 | [NPM scheduled update incident](../Security/Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md) |
| [`edge-01-interfaces-2026-08-07`](edge-01-interfaces-2026-08-07) | edge-01 | 2026-08-07 | [edge-01 move to DMZ](../Infrastructure/Network/UniFi/Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md) |
| [`grey-server-lxc-110.conf-2026-09-06`](grey-server-lxc-110.conf-2026-09-06) | grey-server | 2026-09-06 | [CT 110 phantom volume removal](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/CT%20110%20Phantom%20Unused%20Volume%20Removed%20-%202026-09-06.md) |
| [`grey-server-pve-authorized_keys-2026-08-15`](grey-server-pve-authorized_keys-2026-08-15) | grey-server (`/etc/pve/priv/authorized_keys`) | 2026-08-15 | No record names this copy. Its header says it was taken before the 2026-08-15 fleet access key cleanup |
| [`grey-server-pve-cluster.fw-2026-09-06`](grey-server-pve-cluster.fw-2026-09-06) | grey-server | 2026-09-06 | [docker-blue firewall grant narrowed](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/docker-blue%20Firewall%20Grant%20Narrowed%20to%20pve_ssh_manager%20-%202026-09-06.md) |
| [`grey-server-root-authorized_keys-2026-08-15`](grey-server-root-authorized_keys-2026-08-15) | grey-server | 2026-08-15 | [Broken node shell troubleshooting](../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Broken%20Node%20Shell%20and%20Standalone%20authorized_keys%20on%20grey-server%20-%202026-08-15.md) |
| [`media-01-docker-compose-2026-09-18.yml`](media-01-docker-compose-2026-09-18.yml) | media-01 | 2026-09-18 | [Lost proxy trust troubleshooting](../Platforms/Media%20Stack/Documentation/Troubleshooting/Lost%20Proxy%20Trust%20Broke%20Arr%20HTTPS%20Redirects%20-%202026-09-18.md) |
| [`media-01-sshd-60-hardening-2026-08-15.conf`](media-01-sshd-60-hardening-2026-08-15.conf) | media-01 | 2026-08-15 | [ai-agent account provisioning](../Operations/Maintenance/ai-agent%20Account%20Provisioning%20-%202026-08-15.md) |
| [`monitor-01-docker-compose-2026-08-10.yml`](monitor-01-docker-compose-2026-08-10.yml) | monitor-01 | 2026-08-10 | [Container stopped after restart](../Platforms/Prometheus/Documentation/Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md) |
| [`monitor-01-docker-compose-2026-09-02.yml`](monitor-01-docker-compose-2026-09-02.yml) | monitor-01 | 2026-09-02 | [Discord alert bot deployment](../Platforms/Discord%20Alert%20Bot/Documentation/Change%20Records/Deployment%20-%202026-09-02.md) |
| [`red-server-nut-ups.conf-2026-08-31`](red-server-nut-ups.conf-2026-08-31) | red-server | 2026-08-31 | [NUT driver restart loop](../Platforms/PeaNUT/Documentation/Troubleshooting/ups01%20NUT%20Driver%20Restart%20Loop%20After%20the%20UPS%20Swap%20-%202026-08-31.md) |
| [`security-01-sshd-00-ansible-hardening-2026-08-15.conf`](security-01-sshd-00-ansible-hardening-2026-08-15.conf) | security-01 | 2026-08-15 | [Root SSH disabled](../Operations/Maintenance/Root%20SSH%20Disabled%20on%20ansible-01%20and%20security-01%20-%202026-08-15.md) |
| [`splunk-siem-fstab-2026-08-29`](splunk-siem-fstab-2026-08-29) | splunk-siem | 2026-08-29 | [Root filesystem expansion](../Platforms/Splunk/Enterprise/Documentation/Change%20Records/Root%20Filesystem%20Expansion%20-%202026-08-29.md) |

## How a file gets here

1. I copy the file on the host before the edit, because an edit I cannot reverse is not one I want to make blind.
2. Once the new config works and I have verified it, I check the copy for withheld values and redact them.
3. I commit the redacted copy here.
4. **Then I delete the copy from the host.** The host keeps nothing.

The change record for that work says the copy was made, where it landed, and that the host copy was removed.

## What does not belong here

A tracked file under a platform's `Configuration/` is the configuration a service actually reads. That is a versioned reference, not a backup, and it is never moved or deleted by this process. If you are looking for what a service runs today, read its `Configuration/` folder, not this one.

This is also not a home for hypervisor snapshots or disk images. I keep none.

## Naming

`<hostname>-<original filename>-<YYYY-MM-DD>`, so `monitor-01-docker-compose-2026-08-05.yml`. The date is the day I took the copy.

## Redaction is not optional

**This folder is published.** A config file is the single most likely place for a token, a password, or a key to reach the public repository by accident, because the sensitive part is usually one line in a file that is otherwise dull. Read the whole file before committing it, not a diff of it.

Withheld: credentials, API tokens, keys, my WAN address, MAC addresses, drive serials and WWNs, tunnel and relay identifiers, and the name of my password manager. A scrub cannot unpublish what a push already sent, so the check happens before the commit or not at all.
