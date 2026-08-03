# Docusaurus Deployment Evidence Index

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

This folder holds the command transcripts for the Docusaurus 3.10.2 deployment on Docker Main. Remote timestamps use UTC; the implementation date is 2026-08-02 in America/New_York.

| Step | Artifact | What it proves |
| --- | --- | --- |
| S01 | [Preflight](Logs/s01-preflight-2026-08-02.log) | Compose syntax passed and the deployed files had recorded SHA256 values |
| S02 | [Build & deployment](Logs/s02-build-deploy-2026-08-02.log) | Docusaurus built static output and Compose started the first container |
| S03 | [Runtime verification](Logs/s03-runtime-verification-2026-08-02.log) | Health, runtime user, read-only filesystem, dropped capabilities, routes, & restart recovery passed |
| S04 | [Project-name correction](Logs/s04-project-name-correction-2026-08-02.log) | The project changed from `configuration` to `docusaurus` and returned healthy |
| S05 | [Failed redirect check](Logs/s05-final-state-2026-08-02.log) | The no-slash documentation route tried to follow a redirect to container TCP 8080 |
| S06 | [Relative redirect fix](Logs/s06-relative-redirect-fix-2026-08-02.log) | The rebuilt image returned a relative location and the followed route reached HTTP `200` |
| S07 | [LAN reachability](Logs/s07-lan-reachability-2026-08-02.log) | Jedi PC reached all published routes through Docker Main TCP 3010 |
| S08 | [Final convergence](Logs/s08-final-convergence-2026-08-02.log) | The deployed introductory Markdown matched repository metadata rules, the final image was healthy, & the published routes passed |
| S09 | [Final host route matrix](Logs/s09-final-route-matrix-2026-08-02.log) | Known routes returned HTTP `200`, an unknown route returned `404`, the redirect stayed relative, & the final image was healthy |
| S10 | [Final LAN route matrix](Logs/s10-final-lan-route-matrix-2026-08-02.log) | Jedi PC received the same `200` and `404` status values through Docker Main TCP 3010 |
