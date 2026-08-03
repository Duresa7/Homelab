# Docusaurus

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

I run Docusaurus 3.10.2 as the homelab documentation site on Docker Main. A Node.js 24.14.0 build stage generates static files, then Nginx 1.29.5 serves only those files at `http://192.168.40.35:3010`.

## Layout

| Path | Contents |
| --- | --- |
| [Source](Source/) | Docusaurus source, locked npm dependencies, Dockerfile, & Nginx configuration |
| [Configuration](Configuration/) | Docker Compose service definition |
| [Documentation](Documentation/) | Deployment record, operating commands, & troubleshooting |
| [Evidence](Evidence/) | Command transcripts from the 2026-08-02 deployment |

## Key records

- [Deployment & operations](Documentation/Deployment-and-Operations.md)
- [Docusaurus deployment change record](Documentation/Change%20Records/Docusaurus%20Deployment%20-%202026-08-02.md)
- [Nginx directory redirect correction](Documentation/Troubleshooting/Nginx%20Directory%20Redirect%20Used%20Container%20Port%20-%202026-08-02.md)
- [Unknown-route status correction](Documentation/Troubleshooting/Unknown%20Routes%20Returned%20HTTP%20200%20-%202026-08-02.md)

I own the source in this folder. Docker Main carries a deployed copy under `/opt/docker/docusaurus`; I rebuild the image after changing the versioned source.
