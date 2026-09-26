# Vercel Credential Rotation After Vendor Bulletin

**Created:** 2026-04-19  
**Last updated:** 2026-09-25

**Incident ID:** SIR-2026-04-19-01  
**Date of action:** 2026-04-19  
**Status:** Complete with tracked follow-ups  
**Version:** 1.1

## Incident Metadata

| Field | Value |
|---|---|
| Incident source | Vercel public bulletin |
| Reference URL | https://vercel.com/kb/bulletin/vercel-april-2026-security-incident |
| Vendor | Vercel Inc. |
| Date reported by vendor | April 2026 |
| Vendor classification | "Unauthorized access to certain internal Vercel systems" |
| Customer direct notification received | No (not identified as part of "limited subset of customers impacted") |
| Response initiated | 2026-04-19 |
| Response concluded | 2026-04-19 |
| Severity | Not assigned |

## Summary

In response to Vercel's April 2026 security bulletin, I rotated the affected application credentials and reviewed access across Vercel, Supabase, and GitHub. I disabled the legacy Supabase anon key, reinstalled the Vercel GitHub integration with access limited to one repository, and verified the application after the changes. I found no evidence of unauthorized access to this project. Follow-Up Items tracks the remaining precautionary work.

## Impact

I found no evidence of unauthorized access to my project. The impact was the precautionary rotation itself: new Supabase keys and database password, a disabled legacy anon key, and a reinstalled Vercel GitHub integration. The site passed login, data load and account deletion after the changes.

## Affected Assets

### In-scope systems
- **Hosting platform:** Vercel (primary deployment of the `AlphaSec` web application)
- **Backend-as-a-service:** Supabase (project `<REDACTED_SUPABASE_PROJECT_REF>`, organization `<REDACTED_SUPABASE_ORGANIZATION_ID>`)
- **Source control:** GitHub (auto-deploy integration to Vercel)
- **Edge Functions:** Supabase `delete-account` function and its configuration

### Out of Scope

- Google OAuth provider credentials
- Resend transactional email API key
- End-user session tokens

## Symptoms

None on my project. Vercel's April 2026 bulletin reported "unauthorized access to certain internal Vercel systems", and I received no direct notification as part of the "limited subset of customers impacted". The bulletin was the trigger.

## Timeline

| Date | Event |
|---|---|
| April 2026 | Vercel publishes its security bulletin |
| 2026-04-19 | I start the response, rotate the Supabase credentials, update the edge function and Vercel variables, reinstall the GitHub integration and verify the site |
| 2026-04-19 | Response concluded, with follow-ups F-1 to F-5 open |

## Findings

| Asset | Incident scope | Action I took |
|---|---|---|
| Supabase publishable key (`VITE_SUPABASE_ANON_KEY`) | Affected environment | Rotated |
| Supabase project URL (`VITE_SUPABASE_URL`) | Public identifier | No action |
| Supabase secret / service key | Precautionary | Rotated |
| Supabase database password | Precautionary | Rotated |
| Supabase legacy anon JWT API key | Legacy access path | Disabled |
| Vercel GitHub integration | Potentially affected integration | Reinstalled with one-repository access |
| Supabase Personal Access Token (`SUPABASE_ACCESS_TOKEN`) | Not implicated | Rotation remains open in Follow-Up Items |
| Google OAuth client secret | Not implicated | Rotate only if later evidence warrants it |
| Resend API key | Not implicated | Rotate only if later evidence warrants it |

## Root Cause

The cause sat with the vendor: unauthorized access to internal Vercel systems, per the bulletin. My project was not identified as affected, so every rotation here was precautionary.

## Corrective Action

All actions performed on 2026-04-19.

### Supabase credential rotation
- I rotated the project publishable key. The new active key is labeled `default_v2` (type: publishable). I deleted the previous publishable key from the project.
- I rotated the project secret (service) key. The new active key is labeled `secret_v2`. I deleted the previous secret key from the project.
- I rotated the Postgres database password.
- I disabled the legacy anon JWT API key as part of this response. Before this incident it remained active on the project; it is now marked `disabled` and no longer honored for authentication.

### Edge function secret update
- I updated the `delete-account` edge function's stored secrets (`EDGE_PUBLISHABLE_KEY`, `EDGE_SECRET_KEY`) to reference the new publishable and secret key values respectively.
- I verified the function's configured CORS allowlist and environment variables.

### Vercel environment variable update
- I updated `VITE_SUPABASE_ANON_KEY` in the Vercel project environment to the new publishable key.
- I confirmed that `VITE_SUPABASE_URL` remained unchanged (public identifier).
- I confirmed no other environment variables in the Vercel project reference rotated values.

### GitHub integration refresh
- I uninstalled the Vercel GitHub App from the connected GitHub account.
- I reinstalled the Vercel GitHub App, restricting repository access to the `AlphaSec` project repository only.
- I triggered a test deployment to confirm the auto-deploy pipeline was restored.

### Code verification
- I confirmed the repository working tree contains no references to the rotated values. The search returned zero matches.
- I confirmed the `delete-account` edge function validates the caller's JWT via `auth.getUser(token)` inside the function body rather than relying solely on gateway-level verification.

## Validation

| Check | Method | Result |
|---|---|---|
| Old publishable key no longer present on project | Supabase management API key list | Pass; only `default_v2` active |
| Old secret key no longer present on project | Manual verification in Supabase dashboard | Pass; deleted |
| Legacy anon JWT disabled | Supabase management API key list | Pass; `disabled: true` |
| Edge function secrets reference new keys | Manual verification in Supabase dashboard | Pass |
| Vercel environment variables reference new keys | Manual verification in Vercel dashboard | Pass |
| Site functional after rotation | Manual browser test (login + data load + account delete) | Pass |
| Edge function invocation returns success | Supabase edge function logs after deploy | Pass |
| No rotated values in repository working tree | `grep` across source tree | Pass; zero matches |

## Residual Risk

- **Git history:** I didn't rewrite history. The rotated and disabled values are no longer accepted.
- **Vercel activity:** I found no suspicious activity in the dashboard. This doesn't rule out access that occurred before the available logs.
- **End-user sessions:** I didn't invalidate active sessions. I found no evidence that user tokens were affected, and forced invalidation would have signed out every user.

## Follow-Up Items

| ID | Item | Priority | Notes |
|---|---|---|---|
| F-1 | Rotate `SUPABASE_ACCESS_TOKEN` | Medium | Not present in the affected Vercel project; precautionary rotation remains open. |
| F-2 | Mark secret Vercel environment variables as "Sensitive" | Medium | For any future secret environment variable added to Vercel, enable the Sensitive flag to prevent read-back after save. |
| F-3 | Establish periodic rotation schedule | Low | Calendar reminder for annual rotation of Supabase keys and quarterly review of third-party integrations. |
| F-4 | Evaluate rotation of Google OAuth client secret | Low | Rotate only if evidence of Supabase-side exposure emerges. Not indicated by the current incident. |
| F-5 | Evaluate rotation of Resend API key | Low | Rotate only if evidence of Supabase-side exposure emerges. Not indicated by the current incident. |

## Verification Findings

1. The Supabase key list showed only `default_v2` active and the legacy anon JWT disabled.
2. Login, data loading, account deletion, and the edge function all passed after rotation.
3. A pre-existing edge function bug surfaced during testing. Its logs separated that failure from the credential changes.
4. The repository search returned zero rotated-value matches.

## Sign-Off

| Name | Role | Performed | Date |
|---|---|---|---|
| Duresa7 | Project Owner | Corrective action and validation | 2026-04-19 |

## Closure

Status on 2026-04-19: complete with tracked follow-ups. F-1, the `SUPABASE_ACCESS_TOKEN` rotation, has no completion record as of 2026-09-25.
