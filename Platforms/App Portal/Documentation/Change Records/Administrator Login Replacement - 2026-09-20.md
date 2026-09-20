# Administrator Login Replacement

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

I replaced the initial App Portal administrator login with the username and password from my newly saved vault login. The saved username differed from `portal-admin`, so I created the replacement administrator through the application's CLI, verified browser sign-in, then disabled `portal-admin` through the CLI. Disabling the old account revoked its existing sessions. One administrator remains enabled.

I transferred the replacement credentials encrypted to a temporary key on `docker-main`. The temporary credential file was mode 600 inside a mode-700 directory. I removed the credential file and private key after applying the change and removed the local reference file. Neither saved vault item was edited or deleted; the original *<REDACTED_CREDENTIAL_ITEM_NAME>* item now holds an inactive login.

| Verification | Result |
|---|---|
| Replacement saved login through the HTTPS browser form | Dashboard returned HTTP 200 |
| Browser sign-out | HTTP 302 |
| Old saved credential after disabling `portal-admin` | API login returned HTTP 401 |
| Replacement saved credential after disabling the old account | API login returned HTTP 200 |
| Verification session cleanup | API logout returned HTTP 204 |
| Account state | Original administrator disabled, replacement enabled, exactly one enabled administrator |

I did not retain full command transcripts for the credential transfer, account changes or login checks. The table records the observed results. No work remains for this login replacement.
