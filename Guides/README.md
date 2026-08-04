# Homelab Guides

**Created:** 2026-07-20  
**Last updated:** 2026-08-03

This directory is the shortest route through my homelab. Each guide turns the current build records, runbooks, screenshots, & verified command results into one sequence a reader can follow without opening every infrastructure folder first.

The original records still own the facts. A guide explains the path; its Source Records section points back to the dated change, current configuration, rollback notes, & troubleshooting history.

## Lab Map

![Homelab lab map: edge and compute layers feeding the platform groups](../Assets/Diagrams/lab-map.svg)

## Infrastructure and Shared Procedures

| Guide | What it covers |
|---|---|
| [Galaxy Proxmox Cluster](Galaxy-Proxmox-Cluster.md) | Five-node cluster, original setup, node expansion, Corosync link1, firewall objects, Docker LXC foundation, & Debian development VM |
| [UniFi Network](UniFi-Network.md) | VLANs, zones, Security-A migration, DNS, egress policy order, & verification |
| [Linux Host Baseline](Linux-Host-Baseline.md) | Package updates, administrative account, three SSH keys, key-only SSH, locked root, locale, & checks |
| [SSH Key Lifecycle](SSH-Key-Lifecycle.md) | Key inventory, fleet cleanup, onboarding, staged rotation, verification, & retirement |
| [Security Incident Response](Security-Incident-Response.md) | Scope, containment, credential rotation, service checks, residual risk, & closure |

## Platform Guides

| Guide | What it covers |
|---|---|
| [Ansible SSH Identity Automation](Ansible-SSH-Identity-Automation.md) | Controller setup, identity files, audit, onboarding, rotation, Semaphore, & recovery |
| [Immich Storage Migration](Immich-Storage-Migration.md) | Database backup, replacement pool, file copy, verification, & old-disk retirement |
| [Media Stack](Media-Stack.md) | LXC, Docker services, VPN-isolated qBittorrent, Jellyfin, Arr applications, Seerr, & completed request-to-play acquisition test |
| [NetBird](NetBird.md) | Control plane, NPM publication, peer enrollment, routed subnet, access policy, & tunnel verification |
| [Nginx Proxy Manager](Nginx-Proxy-Manager.md) | Compose deployment, first-run setup, NetBird routes, DNS-01 certificate, health checks, & renewal |
| [Portainer](Portainer.md) | Portainer server 2.39.5, four Edge Agent 2.39.1 hosts, UniFi ports, & environment registration |
| [Prometheus](Prometheus.md) | Prometheus 3.13.1, 49 targets across six jobs, config validation, reload behavior, & exact target checks |
| [Splunk](Splunk.md) | Rocky VM, Splunk Enterprise, HEC, SC4S, UniFi CEF routing, field checks, & Enterprise Security |
| [TeamSpeak](TeamSpeak.md) | Three servers, Playit tunnels, Cloudflare SRV records, TS3 Manager, boot recovery, & outage checks |
| [Wazuh](Wazuh.md) | Wazuh 4.14.6, 14 active remote agents, manager checks, dashboard state, & recovery |

## Archived & Retired Guides

I preserved the Discord assistant configuration formerly hosted on deleted CT 104 `ai-alpha-01` in the [archived OpenClaw walkthrough](../Archive/Guides/OpenClaw.md). I preserved the lore-retrieval & Discord-bot workflow from stopped CT 105 `ai-bravo-02` in the [archived TNIO walkthrough](../Archive/Guides/TNIO-AI-Bot.md).

## Status Language

`Verified` means the linked record contains the observed command result, UI state, or screenshot. `Partial` names the exact unfinished check. I don't turn a plan into a completed result because the command appears plausible.

Cloudflare and Windows Servers don't have standalone guides yet. Their current public records contain inventories or supporting steps, not a complete deployment sequence.
