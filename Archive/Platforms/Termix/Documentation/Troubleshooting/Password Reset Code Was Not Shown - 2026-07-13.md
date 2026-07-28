# Password Reset Code Was Not Shown

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Date:** 2026-07-13  
**Target:** `docker-main`, container `termix`  
**Impact:** The local user `<YOUR_ADMIN_USERNAME>` could initiate password recovery, but the six-digit code was unavailable through either location named by the application. The service otherwise remained healthy.

## Symptom

Termix logged the successful reset request without the value:

```text
[11:27:57 PM] [INFO] Password reset code generated for user <YOUR_ADMIN_USERNAME> (expires at 7/13/2026, 11:42:57 PM). Check admin panel or database settings table for code.
```

The API response also instructed the user to check Docker logs for a code that was not present.

## Investigation

I tested these hypotheses in order:

| Rank | Hypothesis | Test | Result |
|---:|---|---|---|
| 1 | The deployed logger template never includes the generated value | Inspected the compiled reset route and ran the same static assertion twice against the observed event | Confirmed; both assertions reported `RED:code-absent` |
| 2 | The admin UI provides the value instead | Searched the deployed `AdminSettings` asset and backend settings routes | Ruled out; no reset-code field or lookup exists in the admin bundle, and the settings routes are feature-specific |
| 3 | Browser cache served an old frontend | Compared the deployed package and image with the registry's current manifest and upstream release source | Not causal; the deployed backend itself omitted the value |

The deployed route created `resetCode` but logged only the username and expiry. The `AdminSettings` bundle contained no reset-code field, so neither documented retrieval path exposed the value.

## Root Cause

`docker-main` was running Termix package version 2.2.1 from an image created on 2026-05-13. Although the mutable image tag was `latest`, the local repository digest was `sha256:577c0e7024fa7767ffbd00e19a1e0ce28fb0027aab37c3f7d49e2c18bc001210`. The registry's current `latest` index was `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c`, so the running tag was stale.

The defect is corrected in [Termix 2.5.0's password-reset route](https://github.com/Termix-SSH/Termix/blob/release-2.5.0-tag/src/backend/database/routes/user-password-reset-routes.ts), which includes the six-digit value in the Docker log message. [Termix 2.5.0](https://github.com/Termix-SSH/Termix/releases/tag/release-2.5.0-tag) was released on 2026-06-30.

## Corrective Action

I chose a direct Compose upgrade and deliberately took no backup. From `/opt/docker/termix`, I upgraded the existing project with `docker compose pull`, `docker compose down`, and `docker compose up -d`. Both `termix` and `guacd` were recreated; the named `termix_termix-data` volume was retained. I changed no Compose file or environment setting.

I didn't initiate a password-reset request during the upgrade. Verification inspected the corrected 2.5.0 logger template.

## Verification

Termix now reports package version 2.5.0 and repository digest `sha256:4d3371311087d6757aa9d1c94117e854d749b1c5e8fd07bd36e7a99e0686d26c`. Its health check is `healthy`, HTTP port 8080 returns `200`, restart count is zero, and the startup-error scan returned zero. The deployed logger template contains the reset-code variable.

`guacd` logged that it was listening on TCP 4822. Its manual health command passed, Termix established a TCP connection to `guacd:4822`, and Docker's first scheduled five-minute health probe exited zero and changed the container to `healthy`. Both containers remained healthy with zero restarts in the final Compose check.

The earlier 2026-07-13 reset code expired with the former process. A fresh reset remains the final functional test.

The completed upgrade is recorded in [Termix Upgrade 2.2.1 to 2.5.0 - 2026-07-13](../Change%20Records/Termix%20Upgrade%202.2.1%20to%202.5.0%20-%202026-07-13.md).
