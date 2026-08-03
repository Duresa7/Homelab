# Unknown Routes Returned HTTP 200

**Created:** 2026-08-02  
**Last updated:** 2026-08-02

## Symptom

The initial Nginx configuration sent an unknown path to `/404.html` through the final `try_files` URI. That internal redirect served the error document as a successful page, which made missing routes return HTTP `200` instead of `404`.

I found this during the final configuration review. I didn't retain a before-change request transcript; the deployed rule was `try_files $uri $uri/ /404.html`.

## Root cause

Nginx treated `/404.html` as the next internal URI, not as an error response. The static file existed, so Nginx returned its normal success status.

## Corrective action

I configured the Docusaurus page as the Nginx error document and ended `try_files` with an explicit status:

```nginx
error_page 404 /404.html;

location / {
  try_files $uri $uri/ =404;
}

location = /404.html {
  internal;
}
```

I rebuilt the image and recreated the stateless container.

## Verification

Docker Main returned HTTP `200` for `/`, `/docs/intro`, `/docs/intro/`, & `/healthz`. `/route-that-does-not-exist` returned HTTP `404`, while Nginx served the 6,346-byte Docusaurus error page. Jedi PC repeated the home, docs, health, & missing-route checks through `192.168.40.35:3010` with the same status values.

Evidence: [host route matrix](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s09-final-route-matrix-2026-08-02.log) & [LAN route matrix](../../Evidence/Docusaurus%20Deployment%20-%202026-08-02/Logs/s10-final-lan-route-matrix-2026-08-02.log)
