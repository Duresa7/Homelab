# Nginx Directory Redirect Used Container Port

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

## Symptom

The site served `/docs/intro/` over host TCP 3010, but requesting `/docs/intro` and following its redirect failed. Curl reported `Failed to connect to 127.0.0.1 port 8080` after the first HTTP `301` response.

## Exact error

```text
curl: (7) Failed to connect to 127.0.0.1 port 8080 after 0 ms: Couldn't connect to server
DOCS_HTTP: status=301 bytes=0 redirects=1
```

Evidence: [failed check](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s05-final-state-2026-08-02.log)

## Hypothesis & test

Nginx listened on container TCP 8080 while Docker published host TCP 3010. Nginx handled the directory slash redirect itself and inserted its listener port into the absolute `Location` value.

I inspected the redirect headers after changing the server block. The corrected response returned `Location: /docs/intro/`, which removed the container address and port from the client-visible redirect.

## Root cause

The Nginx server used its default absolute redirect behavior behind a port translation. It knew its listener as TCP 8080, not the Docker host's TCP 3010 mapping.

## Corrective action

I added this directive to the server block in `Source/nginx.conf`:

```nginx
absolute_redirect off;
```

I rebuilt `homelab/docusaurus:3.10.2` and recreated the stateless container.

## Verification

The response now includes `Location: /docs/intro/`. Curl followed one redirect through `127.0.0.1:3010` and returned HTTP `200` with 10,251 bytes. A second request from Jedi PC followed `http://192.168.40.35:3010/docs/intro` to `/docs/intro/` and returned the same 10,251-byte page.

Evidence: [corrective build & host verification](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s06-relative-redirect-fix-2026-08-02.log) & [LAN verification](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s07-lan-reachability-2026-08-02.log)

## Failed attempts

No configuration change preceded the fix. The original final-state command exposed the fault, but it printed a final `EXIT_CODE: 0` because the script didn't gate its exit on curl's return code. The corrective script captured `CURL_EXIT_CODE: 0` and stopped on any nonzero result.
