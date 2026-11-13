# Embedded Identity-Provider Probe Raced Container Recreation

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-10  
**Step:** S08

**Symptom:** The first embedded identity-provider request immediately after recreating `netbird-server` returned `Recv failure: Connection reset by peer`.

**Hypothesis and test:** The request reached the container during its startup transition. I repeated the same health check two seconds later.

**Verification:** The retry returned HTTP `200`; subsequent direct and Nginx Proxy Manager network-path checks also returned `200`. No configuration change was required.
