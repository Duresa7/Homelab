---
sidebar_position: 1
title: Start here
---

# Homelab documentation

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

This Docusaurus 3.10.2 site is ready for runbooks, architecture notes, & change records. I keep the source in `Platforms/Docusaurus/Source` and publish the generated static files through Nginx on Docker Main.

## Editing the site

Add Markdown or MDX files beneath `docs/`. The sidebar is generated from that directory, and the container image rebuilds the site before Nginx serves it.

## Deployment target

Docker Main serves this site on TCP 3010. The container has no database or writable application data; its content comes from the versioned source tree at build time.
