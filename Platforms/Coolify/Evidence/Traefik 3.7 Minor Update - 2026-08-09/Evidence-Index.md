# Coolify Traefik 3.7 Minor Update Evidence Index

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

| Step | Artifact | Demonstrates |
|---|---|---|
| Starting state | [Live state before the update](Logs/S00-Starting-State-2026-08-09.txt) | Traefik 3.6.25, the v3.6 Compose reference, Docker & file providers, no affected wildcard rules, six healthy Coolify containers, & expected HTTP 302 and 404 responses |
| Candidate test | [Traefik 3.7.10 candidate](Logs/S01-Candidate-Test-2026-08-09.txt) | The dated 3.6.25 rollback tag, v3.7.10 image digest, isolated binary test, candidate Compose validation, & unchanged running proxy |
| Proxy update | [Compose edit and proxy recreation](Logs/S02-Proxy-Update-2026-08-09.txt) | The atomic image-reference change, single-service recreation, 7-second health wait, six healthy containers, expected HTTP responses, & zero proxy errors |
| Coolify state | [Detected-version refresh](Logs/S03-Coolify-State-Refresh-2026-08-09.txt) | Coolify stored Traefik 3.7.10 and cleared its outdated-version state |
| Final verification | [Delayed app-01 and edge-01 checks](Logs/S04-Final-Verification-2026-08-09.txt) | Persistent v3.7.10 health, the Compose checksum, no temporary configuration files, zero errors, six healthy containers, & edge-to-proxy reachability |
