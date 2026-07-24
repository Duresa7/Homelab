# Architecture

**Created:** 2026-07-09  
**Last updated:** 2026-07-24

Architecture holds designs that cross more than one owner: dependency maps, data flows, trust boundaries, & the two editable diagrams in `Diagrams/`.

Service-specific architecture stays with the service under `Platforms/<Service>/Documentation/`, and Galaxy-specific architecture stays under `Infrastructure/Compute/Galaxy/Documentation/Architecture/`.

## Contents

- [Isolated Security Lab](Isolated-Security-Lab.md) - my planning-phase design for a fenced malware-detonation & pentest VLAN with no route out
- [External Service Ingress](External-Service-Ingress.md) - how every public service reaches its container through Cloudflare, the edge-01 tunnel, Caddy, & Traefik
- [Diagrams/](Diagrams/) - Excalidraw sources & exported SVGs for `homelab-overview`, `remote-dev-pattern`, & `isolated-security-lab`
- [Persistent Remote Development: My Research](Remote-AI-Development-Research-2026-07-12.md) - my 2026-07-12 comparison and selected design for an always-on development VM
