# Docusaurus Troubleshooting

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

This index holds dated Docusaurus operating problems and their verified corrections.

| Date | Issue | State |
| --- | --- | --- |
| 2026-08-02 | [Nginx directory redirect used container port](Nginx%20Directory%20Redirect%20Used%20Container%20Port%20-%202026-08-02.md) | Resolved with relative redirects; `/docs/intro` follows to HTTP `200` through TCP 3010 |
| 2026-08-02 | [Unknown routes returned HTTP 200](Unknown%20Routes%20Returned%20HTTP%20200%20-%202026-08-02.md) | Resolved with an explicit `=404` fallback and Docusaurus error page |
