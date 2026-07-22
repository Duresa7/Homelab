# Search returned 0 results (real-time trap)

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Symptom:** `index=* sourcetype=sc4s:events "starting up"` showed **0 of 0 events**, even though the SC4S logs showed it had started.

**Cause:** I had the time picker set to **"All time (real-time)"**. A real-time search only shows events arriving from the moment you run it; the startup event had happened minutes earlier.

**Fix:** I switched the time range to a historical window (**Last 24 hours** / **All time**). The events appeared.
