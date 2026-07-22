# NetBird Troubleshooting

**Created:** 2026-07-11  
**Last updated:** 2026-07-22

This is my chronological troubleshooting record for the combined `docker-network` access-stack deployment. Configuration stays owned by its platform or infrastructure system; I keep the combined deployment narrative here.

I keep one dated Markdown record per problem in this folder. The index links to the complete symptom, tests, cause, correction, & verification for each issue.

## Issue Index

| # | Step | Symptom | Resolution | Status |
|---:|---|---|---|---|
| <a id="1-pvestatd-was-failed-on-blue-server"></a>[1](pvestatd%20Was%20Failed%20on%20blue-server%20-%202026-07-10.md) | Preflight | `pvestatd` failed on `blue-server` | Restart restored status temporarily; recurring issue transferred to Galaxy | Recurring / transferred |
| <a id="2-netbird-installer-required-jq"></a>[2](NetBird%20Installer%20Required%20jq%20-%202026-07-10.md) | S08 | Official NetBird installer stopped because `jq` was missing | Installed Debian `jq` and reran from a clean state | Resolved |
| <a id="3-embedded-identity-provider-probe-raced-container-recreation"></a>[3](Embedded%20Identity-Provider%20Probe%20Raced%20Container%20Recreation%20-%202026-07-10.md) | S08 | First embedded identity-provider probe reset during recreation | Two-second retry returned HTTP `200` | Resolved |
| <a id="4-unifi-rejected-the-first-web-egress-policy-create"></a>[4](UniFi%20Rejected%20the%20First%20Web-Egress%20Policy%20Create%20-%202026-07-11.md) | S05A | UniFi rejected the first web-egress policy create | Set `create_allow_respond` to `false` and reapplied | Resolved |
| <a id="5-handcrafted-ntp-probe-was-inconclusive"></a>[5](Handcrafted%20NTP%20Probe%20Was%20Inconclusive%20-%202026-07-11.md) | S05A | Handcrafted NTP probe returned no conclusive response | Installed `ntpsec-ntpdig` and verified Cloudflare NTP | Resolved |
| <a id="6-npm-advanced-gear-dismissed-the-proxy-host-modal"></a>[6](NPM%20Advanced%20Gear%20Dismissed%20the%20Proxy-Host%20Modal%20-%202026-07-11.md) | S07 | NPM Advanced gear dismissed the proxy-host modal | Saved the basic host first, then applied Advanced configuration | Resolved |
| <a id="7-npm-retained-a-stale-netbird-upstream-address-after-recreation"></a>[7](NPM%20Retained%20a%20Stale%20NetBird%20Upstream%20Address%20After%20Recreation%20-%202026-07-12.md) | Operational follow-up | Routing peer Management channel returned HTTP `502` after sequential container recreation | Reloaded validated NPM configuration to refresh the changed NetBird upstream address | Resolved |

