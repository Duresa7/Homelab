# Facial Recognition Threshold Tuning

**Created:** 2026-09-05  
**Last updated:** 2026-09-05

**Date:** 2026-09-05  
**Status:** Settings applied; one Missing-mode recognition job waits for me in the admin UI

## Change

After the [model research](../Facial%20Recognition%20Model%20Research%20-%202026-09-05.md) settled on keeping `buffalo_l`, I tuned the two recognition thresholds that can be changed without losing assigned names. I raised the maximum recognition distance from the default 0.5 to 0.55 and the minimum recognized faces from the default 3 to 5. The detection score stays at my earlier 0.65.

## Starting State

The library had 238 people, 52 of them named and 8 hidden, over 4,580 detected faces. 1,050 faces, about 23 %, were unassigned, and 134 people carried only one or two faces. 4,145 of the faces come from video preview frames and 435 from photos, so most faces are single extracted frames at whatever quality the video offered, which is exactly the population that ends up unassigned or in tiny junk clusters.

## Why These Values

Immich's facial recognition documentation says a higher recognition distance and a lower detection score both call for a higher minimum face count to compensate. Both apply here: I already run detection at 0.65, and I loosened the distance so more of the unassigned frame faces reach an existing person. Raising the core-point threshold to 5 stops those same low-quality frames from spawning new one-off people. The documentation's hard limits are 0.3 to 0.7 for distance, and a January 2026 community test on a 60,000-face library landed at 0.6 and 7; I stayed inside both.

In v3.1.0, `minFaces` only drives clustering in `PersonService.handleRecognizeFaces`. The People list filters on `isHidden` alone, so the six named people with fewer than five faces stay visible.

## What I Did Not Change

The detection score only applies to new detection jobs, and applying it to existing assets means Face Detection in All mode. In v3.1.0 that path deletes every machine-learning face, then removes every person left without faces, which takes the 52 names with it. Facial Recognition in All mode unassigns every face and does the same cleanup. I left the score alone and ruled out both All-mode jobs.

## Method and Verification

- I wrote the two values into the `facialRecognition` object of the `system-config` row and restarted `immich-server` so both workers dropped their cached configuration. Stored object afterwards: `{"minFaces": 5, "minScore": 0.65, "maxDistance": 0.55}`.
- Server healthy at restart count zero after the restart; `/api/server/ping` returned 200; no validation or error line in the first minute of log.
- Machine learning, PostgreSQL, and Valkey were untouched.

No separate evidence transcript was retained.

## Remaining Work

From Administration, Jobs, run **Facial Recognition, Missing**. That mode only touches the 1,050 unassigned faces, keeps every name, and uses the new thresholds. If it merges two people wrongly, the fix is a manual unmerge in the People view; if it leaves many faces unassigned, the next step is distance 0.6 and another Missing run, not an All run.
