# Directory Sign-In for the Portal

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

The portal recorded my directory account against every install while the only way in to administer it was a local password that existed nowhere else. I built directory sign-in so the admin pages accept a domain account, verified it against the live forest with a test account and then with my own Tier 2 administrator account, and stopped at the pull request, because a human merges and a human tags in that repository.

Work package [M1-11](https://github.com/Duresa7/app-portal/blob/plan/M1-11/docs/plans/M1-11-directory-sign-in.md), pull request [#19](https://github.com/Duresa7/app-portal/pull/19).

## What it does

An administrator signs in at `/admin/login` with `ALPHASEC\user`, a UPN, or a bare user name. The server binds that credential against a controller over LDAPS, checks membership of one configured group, and creates an administrator row named `DOMAIN\user` the first time, which is the same label the client already puts on installs.

Four decisions worth keeping:

- **Local accounts are checked first.** The portal must not be lockable by a domain controller being down, so the local table answers before anything crosses the network, and one local account stays.
- **The group is required.** An empty `Directory:RequiredGroup` stops the server at startup rather than admitting every account in the forest.
- **The bind is the user's own credential.** The portal stores no service account and no directory password; the row it keeps has a hash of random bytes that can never be matched, and a directory account's password cannot be set from the portal.
- **Off unless configured.** With the section absent the server opens no LDAP connection at all, which keeps the project's promise that it depends on no directory.

## What the forest needed

Three things had to exist before a bind could work, and none of them did.

**LDAPS was broken on both controllers.** They listened on 636 and reset every handshake. That is its own change record: [LDAPS on the Domain Controllers](../../../Active%20Directory/Documentation/Change%20Records/LDAPS%20on%20the%20Domain%20Controllers%20-%202026-09-20.md).

**A group to check.** I created `APP-AppPortal-Admins`, a global security group in `OU=Applications,OU=Groups`. It holds my `DK-user` daily account and my `DK-user` Tier 2 workstation administrator account. `testuser` joined it for the first test and was removed afterwards.

**A path through the firewall.** `docker-main` could not reach the identity plane at all. `Allow App Portal to Identity LDAPS` admits `192.168.40.35` in Internal to `192.168.65.10` and `192.168.65.11` in `AlphaSec-Identity` on TCP 636 only, index 10008. Plain 389 stays refused, which I checked as a control.

## Three failures worth remembering

The first live bind failed three times for three unrelated reasons, each of which would have cost an afternoon on its own.

1. `System.DirectoryServices.Protocols` throws *The LDAP server is unavailable* the moment you **set** `VerifyServerCertificate` on Linux: the callback is Windows-only, and it fails before any connection is attempted. The portal now opens its own TLS connection first, compares the certificate against the pinned SHA-256 thumbprints there, and only then binds. A substituted certificate is refused before a password is sent.
2. OpenLDAP on this image is built against **GnuTLS**, which refuses a trust anchor that is not marked as a certificate authority. That is why the controllers now issue their LDAPS certificates from a small authority instead of presenting a self-signed leaf.
3. `Environment.SetEnvironmentVariable` updates .NET's own copy of the environment and **not the process**, so `LDAPTLS_CACERT` never reached the native library that reads it. The bind failed with a bare *LDAP server is unavailable* while `ldapsearch` in the same container with the same file succeeded. The server now sets it through `libc`.

## Verification

Against the live forest, using a temporary container built from the branch on `docker-main`, with `testuser` in the group for the duration.

| Check | Observed result |
|---|---|
| Member signs in as `ALPHASEC\testuser` through the admin API | HTTP 200 with an `apa_` token and an expiry eight hours out |
| Same account typed as a bare user name | HTTP 200 |
| Same account, wrong password | HTTP 401 |
| A different real directory account, not in the group | HTTP 401, logged as refused for membership |
| Administrator row created | One row, `ALPHASEC\testuser`, source `directory`, enabled; the second sign-in reused it rather than adding another |
| Browser sign-in through the form | HTTP 302 to `/admin`, then `/admin/admins` and `/admin/installs` returned 200 |
| Account source in the admin pages | The row reads Directory |
| Certificate pinning | The bind proceeds only after the presented certificate matches a pinned thumbprint |
| Firewall | 636 open from `docker-main` to both controllers, 389 refused |
| Continuous integration | Every job green on the branch: version, tests on Linux and Windows, client archive verified and started on a Windows runner, server image smoke tested |

Then again with my own accounts, which is the point of the exercise:

| Check | Observed result |
|---|---|
| My Tier 2 administrator account, `DOMAIN\user` form | HTTP 200 with a token; the portal created `ALPHASEC\` and that account, source `directory` |
| Same account, UPN form | HTTP 200 |
| Same account, wrong password | HTTP 401 |
| My Tier 0 domain administrator account | HTTP 401, refused at the bind rather than at the group check |
| Browser sign-in, then all seven admin pages | 302 to `/admin`, then `/admin`, `/admin/catalog`, `/admin/devices`, `/admin/installs`, `/admin/requests`, `/admin/keys` and `/admin/admins` all 200 |
| Sign out | POST returns 302 to the sign-in page, and `/admin` then redirects to it, so the session row is gone and not just the cookie |

The test deployment, its image and its configuration were removed afterwards. Production still runs 0.3.0 with local sign-in and was not touched.

## Open

- The pull request is not merged and no release is cut. Production picks this up when 0.3.1 exists; the repository's rule is that a human merges and a human tags.
- When it is deployed, `deploy/.env` needs the `Directory__*` settings and `deploy/compose.yaml` needs the controller names resolvable and the authority bundle mounted at `/app/config/dc-certs.pem`.
- **Tier 0 cannot use this, and should not.** My Tier 0 account is in `Protected Users`, and the controller refused its bind outright: the portal logged no group refusal, which is the path a wrong password takes, and that group exists to stop exactly this kind of password-based authentication. A domain administrator account has no business signing in to a web application anyway. Tier 2 is the right account and is what I verified.
- My daily account is still in the group alongside the Tier 2 one. If the tiering model should hold here, the daily account comes out and only the administrator account signs in; I left the choice open rather than removing my own access.
- Every administrator is a full administrator. Group-to-role mapping is out of scope and stays out.
- The local `dkadi` account remains, deliberately: it is what gets you in when the controllers are down.
