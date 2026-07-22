# First HTTP Probe Raced NPM Initialization

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-10  
**Step:** S05

**Symptom:** The first request to the NPM administrative endpoint returned HTTP result `000` while the newly created container initialized.

**Hypothesis and test:** The container was still starting rather than permanently unavailable. My deployment loop retried the same endpoint while watching the built-in health status.

**Corrective action:** I made no configuration change. The retry loop let initialization complete.

**Verification:** The second endpoint request returned HTTP `200`; the built-in health check became `healthy`; ports 80 and 81 then returned `200`.
