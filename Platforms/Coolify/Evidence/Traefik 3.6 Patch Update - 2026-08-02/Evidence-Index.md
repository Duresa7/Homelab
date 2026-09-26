# Coolify Traefik 3.6 Patch Update Evidence Index

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

| Step | Artifact | Demonstrates |
|---|---|---|
| Starting state | [Live state before the update](Logs/S00-Starting-State-2026-08-02.txt) | Traefik 3.6.11, its image ID, six healthy Coolify containers, & expected HTTP 302 & 404 results |
| Step 1 | [Preflight & candidate test](Logs/S01-Preflight-and-Candidate-2026-08-02.txt) | The 3.6.11 rollback tag, Docker API 1.55, the 3.6.25 candidate digest, isolated version test, & unchanged running proxy |
| Step 1 | [Compose validation](Logs/S01B-Compose-Validation-2026-08-02.txt) | Docker Compose 5.3.1 accepted the Coolify proxy file before the optional routed-host probe found no router label on running containers |
| Step 2 | [Proxy recreation](Logs/S02-Proxy-Recreation-2026-08-02.txt) | The single-service Compose recreation, 7-second health wait, image change, six healthy containers, expected HTTP results, & zero proxy errors |
| Step 3 | [Final verification](Logs/S03-Final-Verification-2026-08-02.txt) | The delayed app-01 state, provider & affected-middleware counts, zero router labels on running containers, & edge-01-to-Traefik reachability check |
