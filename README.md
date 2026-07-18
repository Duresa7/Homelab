# Homelab Enterprise Workspace

**Created:** 2026-07-09  
**Last updated:** 2026-07-17

This workspace intentionally combines enterprise-style IT and cybersecurity records with the source, configuration, automation, and evidence used to operate the homelab.

## Workspace Map

| Category | Purpose |
|---|---|
| [Governance](Governance/README.md) | Documentation standards, conventions, and future policies |
| [Architecture](Architecture/README.md) | Environment-wide architecture, dependency maps, and diagrams |
| [Infrastructure](Infrastructure/README.md) | Network, compute, cluster, and physical infrastructure |
| [Platforms](Platforms/README.md) | Deployed applications and services, including their documentation and source |
| [Engineering](Engineering/README.md) | Shared automation, reusable tooling, and pre-deployment projects |
| [Operations](Operations/README.md) | Inventories, maintenance records, diagnostics, and raw operational results |
| [Security](Security/README.md) | Incidents, assessments, hardening records, and security operations artifacts |
| [Archive](Archive/README.md) | Superseded or retired material retained for historical reference |

## Key Records

- [Central TODO](TODO.md)
- [Galaxy cluster](Infrastructure/Compute/Galaxy/README.md)
- [UniFi network](Infrastructure/Network/UniFi/README.md)
- [Cloudflare](Infrastructure/Network/Cloudflare/README.md)
- [Galaxy inventory](Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [Incident records](Security/Incidents/)

## Organizing Principle

Store a record with the system that owns or enforces the configuration. Keep deployed services self-contained under `Platforms/`, with documentation, implementation, configuration, scripts, tests, and evidence separated as their complexity requires. Store service-specific evidence beside the service and incident-specific evidence beside the incident.

## Conventions

Secret values never enter this repository; credentials live in 1Password and are referenced, not embedded. Some private identifiers appear as stable `REDACTED_*` placeholders so repeated references stay readable.
