# Wazuh MCP Server Configuration

**Created:** 2026-09-03  
**Last updated:** 2026-09-25

This is the versioned reference for the Wazuh MCP Server Compose project at `/opt/docker/wazuh-mcp-server` on `security-01`.

The container uses host networking so it can reach the loopback-only Wazuh Indexer without publishing Indexer port 9200. The MCP listener binds only to `192.168.72.2:3000`. Executor reaches `http://192.168.72.2:3000/mcp` with a read-only bearer credential.

`Dockerfile` builds `wazuh-mcp-server-local:4.3.0-compat` from the digest-pinned upstream 4.3.0 image. `wazuh-indexer-x509-compat.patch` keeps certificate and hostname verification but relaxes Python 3.13's additional strict-extension check for Wazuh's generated Indexer CA. `static-bearer-api-key.patch` makes the documented static API key usable by Executor without a 24-hour JWT refresh loop; it preserves the key's configured scope.

The live `.env` is root-owned at mode `0600` and is not versioned. It holds separate credentials for the Wazuh Manager API and Indexer, the MCP bearer credential, the server's authentication signing key, and the You.com API key used by `search_external_context`. The Manager and Indexer identities are both read-only.

`wazuh-ca-bundle.pem` contains only the Manager API's self-signed certificate and the Indexer root CA. The image build appends those local anchors to the base image's public CA bundle at `/etc/ssl/certs/wazuh-combined-ca-bundle.pem`. `SSL_CERT_FILE` points at the combined bundle so the Wazuh clients and optional You.com client can verify their respective TLS chains. The bundle is mode `0644` because it contains public trust anchors, not private keys. The bundle is `wazuh-ca-bundle.pem` in this folder, and I stage the same file on `security-01` before running `bootstrap.py`, which refuses to continue without it.

`bootstrap.py` provisions the dedicated Manager and Indexer identities, installs the project, builds the compatibility image, and starts it. `verify_mcp.py` reads the live key without printing it, negotiates and closes an MCP session, confirms no write tools are exposed, and exercises Manager, alert, and vulnerability queries.

Upstream source: [gensecaihq/Wazuh-MCP-Server](https://github.com/gensecaihq/Wazuh-MCP-Server).
