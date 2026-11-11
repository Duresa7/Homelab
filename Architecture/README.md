# Architecture

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Architecture holds designs that cross more than one owner: dependency maps, data flows and trust boundaries. The diagrams live in [Assets/Diagrams](../Assets/Diagrams).

Service-specific architecture stays with the service under `Platforms/<Service>/Documentation/`, and Galaxy-specific architecture stays under `Infrastructure/Compute/Galaxy/Documentation/Architecture/`.

## Contents

- [Access Paths](Access-Paths.md): the five ways into the lab (public ingress, internal HTTPS, remote access, remote control, agent access)
- [External Service Ingress](External-Service-Ingress.md): the public path in detail, from Cloudflare through the edge-01 tunnel, Caddy and Traefik
- [Diagrams](../Assets/Diagrams/): the diagram sources and SVGs

## Archived Designs

I archived my [persistent remote development research](../Archive/Architecture/Remote-AI-Development-Research-2026-07-12.md) on 2026-08-14, along with its `remote-dev-pattern` diagram. It compared the options and selected the always-on development VM I then built; that VM ran as `debian-dev` until `ubuntu-dev` replaced it and I decommissioned `debian-dev` on 2026-08-14.

I archived the [Isolated Security Lab](../Archive/Architecture/Isolated-Security-Lab.md) and its diagrams on 2026-08-19 when I retired Kasm Workspaces and destroyed VM 122.
