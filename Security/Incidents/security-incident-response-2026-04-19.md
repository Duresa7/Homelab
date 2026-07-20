# Security Incident Response Record

**Created:** 2026-04-19  
**Last updated:** 2026-07-20

**Document ID:** SIR-2026-04-19-01
**Classification:** Internal / Confidential
**Status:** Complete (with tracked follow-ups)
**Date of Action:** 2026-04-19
**Version:** 1.1

---

## 1. Executive Summary

In response to the publicly disclosed Vercel security incident of April 2026, I performed a credential rotation and access-control review across the hosting, backend, and identity components of the `<YOUR_ORG_NAME>` application stack. I rotated all primary access credentials that were stored in or reachable from the affected platform, disabled legacy credentials, and verified related configuration. I observed no evidence of unauthorized access to this project during the review. I have identified and scoped residual follow-up items below.

---

## 2. Incident Reference

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

---

## 3. Scope of Review

### In-scope systems
- **Hosting platform:** Vercel (primary deployment of the `<YOUR_ORG_NAME>` web application)
- **Backend-as-a-service:** Supabase (project `<YOUR_SUPABASE_PROJECT_REF>`, organization `<YOUR_SUPABASE_ORGANIZATION_ID>`)
- **Source control:** GitHub (auto-deploy integration to Vercel)
- **Edge Functions:** Supabase `delete-account` function and its configured secrets

### Out-of-scope (no indication of impact)
- Google OAuth provider credentials (stored in Supabase, not Vercel)
- Resend transactional email API key (stored in Supabase, not Vercel)
- End-user session tokens (held in end-user browsers, not in Vercel infrastructure)

---

## 4. Risk Assessment

| Asset | Could it have been exposed via the Vercel breach? | Action I took |
|---|---|---|
| Supabase publishable key (`VITE_SUPABASE_ANON_KEY`) | Yes; stored as a Vercel environment variable | Rotated |
| Supabase project URL (`VITE_SUPABASE_URL`) | Yes; stored as a Vercel environment variable, but not secret | No action (public identifier) |
| Supabase secret / service key | Not stored in Vercel (edge function secret only) | Rotated as a precaution |
| Supabase database password | Not stored in Vercel | Rotated as a precaution |
| Supabase legacy anon JWT API key | Not stored in Vercel by design, but present as a project-level credential | Disabled |
| Vercel ↔ GitHub integration token | Managed by Vercel; potentially within scope of internal systems | Reinstalled integration |
| Supabase Personal Access Token (`SUPABASE_ACCESS_TOKEN`) | Stored locally only (`.env`); not in Vercel | Flagged for rotation (see §8) |
| Google OAuth client secret | Stored in Supabase only | Flagged for rotation only if warranted (see §8) |
| Resend API key | Stored in Supabase only | Flagged for rotation only if warranted (see §8) |

---

## 5. Actions Taken

All actions performed on 2026-04-19.

### 5.1 Supabase credential rotation
- I rotated the project publishable key. The new active key is labeled `default_v2` (type: publishable). I deleted the previous publishable key from the project.
- I rotated the project secret (service) key. The new active key is labeled `secret_v2`. I deleted the previous secret key from the project.
- I rotated the Postgres database password.
- I disabled the legacy anon JWT API key as part of this response. Before this incident it remained active on the project; it is now marked `disabled` and no longer honored for authentication.

### 5.2 Edge function secret update
- I updated the `delete-account` edge function's stored secrets (`EDGE_PUBLISHABLE_KEY`, `EDGE_SECRET_KEY`) to reference the new publishable and secret key values respectively.
- I verified the function's configured CORS allowlist and environment variables.

### 5.3 Vercel environment variable update
- I updated `VITE_SUPABASE_ANON_KEY` in the Vercel project environment to the new publishable key.
- I confirmed that `VITE_SUPABASE_URL` remained unchanged (public identifier).
- I confirmed no other environment variables in the Vercel project reference rotated values.

### 5.4 Local environment update
- I updated the local `.env` file to the new publishable key.

### 5.5 GitHub integration refresh
- I uninstalled the Vercel GitHub App from the connected GitHub account.
- I reinstalled the Vercel GitHub App, restricting repository access to the `<YOUR_ORG_NAME>` project repository only.
- I triggered a test deployment to confirm the auto-deploy pipeline was restored.

### 5.6 Code verification
- I confirmed the repository working tree contains no references to the rotated key values. Grep searches for the prior publishable key value, the legacy anon JWT signature, the generic `sb_secret_` prefix, and the HS256 JWT header pattern all returned zero results.
- I confirmed the `delete-account` edge function validates the caller's JWT via `auth.getUser(token)` inside the function body rather than relying solely on gateway-level verification.

---

## 6. Verification

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

---

## 7. Residual Risk

- **Git history** was not rewritten. Any value ever committed historically remains in the repository's commit objects. Because I have rotated the corresponding credentials and disabled the originals, any such historical exposure is **mitigated by invalidation**. I consider no further action necessary unless the repository is published or shared outside the current access boundary.
- **Vercel activity audit** was performed via the Vercel dashboard; I observed no suspicious activity. This finding does not rule out undetected access before logging availability.
- **End-user sessions** were not forcibly invalidated. User access tokens remain valid for the duration of their normal lifetime. I have no evidence that these tokens are at risk, and mass invalidation would cause widespread sign-out disruption disproportionate to the observed risk.

---

## 8. Follow-Up Items

| ID | Item | Priority | Notes |
|---|---|---|---|
| F-1 | Rotate `SUPABASE_ACCESS_TOKEN` | Medium | Not present in the affected Vercel project; precautionary rotation remains open. |
| F-2 | Mark secret Vercel environment variables as "Sensitive" | Medium | For any future secret environment variable added to Vercel, enable the Sensitive flag to prevent read-back after save. |
| F-3 | Establish periodic rotation schedule | Low | Calendar reminder for annual rotation of Supabase keys and quarterly review of third-party integrations. |
| F-4 | Evaluate rotation of Google OAuth client secret | Low | Rotate only if evidence of Supabase-side exposure emerges. Not indicated by the current incident. |
| F-5 | Evaluate rotation of Resend API key | Low | Rotate only if evidence of Supabase-side exposure emerges. Not indicated by the current incident. |

---

## 9. Lessons Learned

1. **Environment variable inventory before an incident saves time during one.** Maintaining a current inventory of where each secret is stored (which platform, which configuration path) accelerates targeted rotation.
2. **Sensitive environment variable flags should be enabled on creation**, not retrofitted during incident response.
3. **Pre-existing bugs can mask root cause during incident response.** A separate edge function bug surfaced during post-rotation testing and I initially suspected it was rotation-related. Distinguishing coincidental failures from incident-caused failures required careful log review.
4. **Credential rotation without verification is incomplete.** I followed each rotation with a functional test to confirm the new credential was accepted and the old one was no longer honored.

---

## 10. Sign-Off

| Name | Role | Performed | Date |
|---|---|---|---|
| Duresa7 | Project Owner | Actions §5, verification §6 | 2026-04-19 |

