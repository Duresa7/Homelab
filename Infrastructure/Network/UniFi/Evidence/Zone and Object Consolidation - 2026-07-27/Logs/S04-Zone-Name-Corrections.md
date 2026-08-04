# Zone Name Corrections

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I corrected the two shortened zone names through the authenticated UniFi console at `https://unifi.ui.com/consoles/`.

| Zone ID | Before | After | Networks |
|---|---|---|---|
| `699cfa33c9d00a2842cceae1` | `AlphSec-Servers` | `AlphaSec-Servers` | `SERVERS-A` |
| `699cfa5fc9d00a2842cceb51` | `AlphSec-Mgmt` | `AlphaSec-Mgmt` | `MGMT-A` |

I captured a full custom-policy, zone, and firewall-group snapshot before each rename. The first structural diff contained only the server zone name. The second contained only the management zone name.

The UniFi API readback returned both corrected names. Custom policies stayed at 61, zones stayed at 16, and firewall groups stayed at 13. Policy bodies and firewall groups were byte-for-byte equal across both snapshot comparisons.

## Evidence boundary

I retained the controller snapshots and API readback. I didn't retain screenshots or a raw interaction transcript from the two UI renames.
