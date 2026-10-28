# Image Update

**Created:** 2026-10-28  
**Last updated:** 2026-10-28

I updated CLI Proxy API on docker-main from v8.0.45 (`ad8bdd3`) to v8.0.46 (`9717e32`) using `eceasy/cli-proxy-api:latest`. A fresh registry pull produced image `sha256:9e842cd8e6387513e1fdea66dbb5edf0a91d0c944473f89f02367b7ada4a88d7`, which differed from the running image. I validated `/opt/docker/cli-proxy-api` with `docker compose config --quiet` and recreated only `cli-proxy-api` with `docker compose up -d --no-deps --pull never cli-proxy-api`. The container then matched the pulled image and reported v8.0.46.

The version probe used `--version`, which is not a supported flag; the executable printed its version banner before reporting that flag error. The banner supplied the observed version.

After recreation, the local root and management page each returned HTTP 200, unauthenticated `/v1/models` returned HTTP 401, and `https://aiproxy.alphasecunited.com/` returned HTTP 200. The container remained running with restart count 0. I did not run an authenticated model request or a provider generation request, so provider functionality remains unverified by this update check.

I retained no standalone transcript for the pull, recreation, or checks. I created no snapshot or backup and changed no configuration files.
