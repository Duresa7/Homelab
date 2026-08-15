# Architecture

**Created:** 2026-07-09  
**Last updated:** 2026-08-14

Architecture holds designs that cross more than one owner: dependency maps, data flows, trust boundaries, & the diagrams, whose sources live with every other diagram in [Assets/Diagrams](../Assets/Diagrams).

Service-specific architecture stays with the service under `Platforms/<Service>/Documentation/`, and Galaxy-specific architecture stays under `Infrastructure/Compute/Galaxy/Documentation/Architecture/`.

## Contents

- [Isolated Security Lab](Isolated-Security-Lab.md) - my planning-phase design for a fenced malware-detonation & pentest VLAN with no route out
- [External Service Ingress](External-Service-Ingress.md) - how every public service reaches its container through Cloudflare, the edge-01 tunnel, Caddy, & Traefik
- [Diagrams/](../Assets/Diagrams/) - Excalidraw sources & exported SVGs for `homelab-overview` & `isolated-security-lab`

## Archived Designs

I archived my [persistent remote development research](../Archive/Architecture/Remote-AI-Development-Research-2026-07-12.md) on 2026-08-14, along with its `remote-dev-pattern` diagram. It compared the options and selected the always-on development VM I then built; that VM ran as `debian-dev` until `ubuntu-dev` replaced it and I decommissioned `debian-dev` on 2026-08-14.
