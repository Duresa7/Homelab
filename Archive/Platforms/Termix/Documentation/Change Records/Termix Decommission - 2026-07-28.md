# Termix Decommission

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Date:** 2026-07-28  
**Scope:** Remove the Termix web SSH platform from `docker-main`, revoke its deployed key, and clear every live reference. I kept no backup.

## Why

I stopped using Termix as a management path. The 2026-07-27 MGMT-A lockdown had already cut its route to the four Proxmox nodes, so it held an SSH inventory it couldn't reach. Rather than maintain a second SSH front end beside the SSH Manager and Ansible paths I actually use, I retired it.

## Starting state

Termix 2.5.0 ran on `docker-main` (`192.168.40.35`) with a `guacd` 1.6.0 companion, both healthy for five days. Its data lived in the 15.45 MB Docker volume `termix_termix-data`. The compose project sat at `/opt/docker/termix` and held two application-data tarballs from 2026-07-14 totalling 11.83 MB.

The platform reached the network through `termix.<YOUR_BASE_DOMAIN>`: a UniFi static DNS record, NPM proxy host 11, and a Prometheus blackbox probe. The `termix` Ed25519 identity was registered in the ssh-key-automation project against 14 target hosts.

## Step 1: Revoke the deployed SSH key

The audit surprised me. The identity file claimed 14 targets, but the key was only present on four: `grey-server`, `purple-server`, `blue-server`, and `red-server`, each in `/root/.ssh/authorized_keys`. A retired web SSH client held root on all four hypervisors, so this came first.

I removed the key with the Ansible `authorized_key` module at `state=absent`. All four nodes reported `CHANGED`. A follow-up grep returned zero matches for the key on every node, and each node kept its remaining seven authorized keys. My own session survived the change, which is the check that matters.

## Step 2: Destroy the service and its data

I ran `docker compose down -v --remove-orphans` in `/opt/docker/termix`. Compose stopped and removed both containers, then removed the `termix_termix-data` volume and the `termix_termix-net` network.

I deleted `/opt/docker/termix` outright, which took both 2026-07-14 tarballs with it, then removed the `ghcr.io/lukegus/termix:latest` and `guacamole/guacd:1.6.0` images. A filesystem-wide search for `*termix*` on `docker-main` returned nothing.

No backup exists. That was the intent.

## Step 3: Clear the network path

I deleted the `termix.<YOUR_BASE_DOMAIN>` A record from the UniFi controller, which left 20 static DNS records.

NPM proxy host 11 forwarded `termix.<YOUR_BASE_DOMAIN>` to `192.168.40.35:8080`. I deleted it through the NPM API and confirmed 19 proxy hosts remain, none disabled. The [runbook](../../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Runbook.md) records an API login returning HTTP 400 during an earlier attempt; the `/api/tokens` login worked on this run, so that note is stale.

## Step 4: Remove the Prometheus probe

I dropped the blackbox target from `/home/dkadi/monitoring/prometheus.yml` on `monitor-01`, leaving 18 probed service names. `promtool check config` passed.

`POST /-/reload` returned HTTP 403 because this Prometheus runs without `--web.enable-lifecycle`, so I restarted the container instead. The first read 12 seconds later showed 30 targets not up, which was just the 15-second and 60-second scrape intervals not having fired yet. A read 75 seconds later returned 45 active targets with 45 up and no Termix entry.

## Step 5: Retire the ssh-key-automation identity

I removed the `termix` identity from the deployed project on `ansible-01` and from the repository source: the identity file, the two `termix_*` inventory groups, five Semaphore templates and the Termix view, the `REQUIRED_IDENTITIES` entry in the validator, and the remaining prose examples. I deleted the identity file rather than moving it to `identities/Archive/`, because I wanted no copy left on the host.

The validator now passes with three identities, 14 supported hosts, zero unknown hosts, and 13 Semaphore templates. `ansible-inventory --graph` parses and still lists 14 hosts.

## Step 6: Archive the records

I moved `Platforms/Termix/` to `Archive/Platforms/Termix/` and the walkthrough and its Excalidraw diagram to `Archive/Guides/`. I removed the guide's row from the Guides index and repointed the Mission Control project at the archived path.

Dated change records elsewhere keep their Termix references. The [Galaxy Data Center Firewall](../../../../../Infrastructure/Compute/Galaxy/Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md) record already showed the TCP 22 exception retired on 2026-07-27. Historical records describe the state I observed when I wrote them.

## Verification

| Check | Observed result |
|---|---|
| Key on Proxmox nodes | Zero matches on all four; seven authorized keys remain per node |
| Containers, volume, network | All removed; `docker ps -a` returns no `termix` or `guacd` |
| Filesystem on `docker-main` | No path matching `*termix*` |
| UniFi DNS | 20 records; `termix.<YOUR_BASE_DOMAIN>` absent |
| NPM | 19 proxy hosts; none disabled; no termix domain |
| Prometheus | 45 active targets, 45 up, no termix probe |
| ssh-key-automation validator | 3 identities, 14 hosts, 0 unknown, 13 templates |
| Repository | No `termix` match outside `Archive/` and dated historical records |

## Rollback

There is none. The application data, both tarballs, and the container images are gone by design. Rebuilding Termix means a fresh deployment, a new identity, and re-onboarding every host.

## Remaining work

The retired `termix` public key may still sit in `authorized_keys` on hosts the audit couldn't reach. `supabase-01` was unreachable during the sweep (no route to `192.168.80.20:22`), so I'll re-run the grep when it returns. Every reachable host in the inventory came back clean.
