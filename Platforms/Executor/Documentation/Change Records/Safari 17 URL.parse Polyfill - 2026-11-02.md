# Safari 17 URL.parse Polyfill

**Created:** 2026-11-02  
**Last updated:** 2026-11-02

On 2026-11-02 I made NPM proxy host 37 insert a `URL.parse` polyfill into Executor's HTML pages, so the web interface works on an iPad running iPadOS 17.7.11.

## Problem

On the iPad, in both Safari and Firefox, the sign-in page showed for about a second and then changed to "This page couldn't load", with a "Choose organization" link. Tapping the link reloaded `/`, the server sent it back to sign-in, and the same thing happened again.

## Cause

Executor 2.0.0-beta.34's web code calls `URL.parse()` without a fallback. Safari added `URL.parse()` in version 18.0. iPadOS 17 ships WebKit 17.6, and every iPad browser has to use WebKit, so Firefox fails the same way. One of those calls is the sign-in route's check of its `redirect` address, in `organization-*.js`. Another rewrites `/api/organizations/` requests. The first call throws as soon as the client-side router starts, and the router replaces the sign-in form with its error page.

The server and network were not involved. The NPM log showed the iPad receiving the HTML and every script with status 200. In Chromium I deleted `URL.parse` and moved the sign-in page to a new `redirect`. The page changed to "This page couldn't load / Choose organization". With `URL.parse` present, the same steps left the sign-in form in place. A one-line `URL.parse` replacement restored the form.

## Change

Before the change, host 37's advanced configuration held only these lines:

```nginx
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
send_timeout 3600s;
```

Through `PUT /api/nginx/proxy-hosts/37` I kept those lines and added a `location /` block. NPM then stops generating its default block, so mine repeats that block's WebSocket headers and `include conf.d/include/proxy.conf;` and adds three directives:

- `proxy_set_header Accept-Encoding "";`, because `sub_filter` cannot rewrite a compressed body
- `sub_filter_types text/html;` and `sub_filter_once on;`
- `sub_filter '<head>' '<head><script>…</script>';`

The script defines `URL.parse` only when the browser lacks it:

```js
if(typeof URL.parse!=="function"){URL.parse=function(u,b){try{return new URL(u,b)}catch(e){return null}}}
```

Executor's pages send only `Content-Security-Policy: frame-ancestors 'none'`, so the inline script is allowed. Host 38, which serves app pages, is unchanged.

The cost is that Executor's responses to NPM are no longer compressed. Traffic between NPM and `docker-blue` stays on the LAN.

## Verification

- NPM readback after the update: `nginx_online: true`, `nginx_err: null`, modified 2026-11-02 08:13:20.
- `/login` comes back with the script as the first element in `<head>`, once per page, for both plain and gzip-accepting requests.
- `/` returned 307. `/login`, `/favicon.png`, `/api/auth/get-session`, `/api/auth/self-host/config` and an `/assets/` script returned 200. Executor MCP calls kept working after the reload.
- In Chromium, I deleted `URL.parse` and ran the script exactly as served. It restored `URL.parse`, and a sign-in page with an `/app-auth` redirect kept its form.
- After the change, sign-in worked on the iPadOS 17.7.11 iPad.

## Removal

Once an Executor release stops depending on `URL.parse`, or no device older than Safari 18 needs the web interface, restore the five lines above as host 37's whole advanced configuration.
