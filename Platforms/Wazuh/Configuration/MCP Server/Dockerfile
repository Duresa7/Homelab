# syntax=docker/dockerfile:1.9

FROM ghcr.io/gensecaihq/wazuh-mcp-server:4.3.0@sha256:4b3dc5e031f79d113cdb1f14ba03620499461f0d9c713e8e34cd3a047d7319d8 AS patcher

USER root
RUN apk add --no-cache patch
COPY wazuh-indexer-x509-compat.patch /tmp/wazuh-indexer-x509-compat.patch
COPY static-bearer-api-key.patch /tmp/static-bearer-api-key.patch
RUN patch -p1 -d /app/src < /tmp/wazuh-indexer-x509-compat.patch \
    && patch -p1 -d /app/src < /tmp/static-bearer-api-key.patch \
    && python -m py_compile \
        /app/src/wazuh_mcp_server/api/wazuh_indexer.py \
        /app/src/wazuh_mcp_server/auth.py

FROM ghcr.io/gensecaihq/wazuh-mcp-server:4.3.0@sha256:4b3dc5e031f79d113cdb1f14ba03620499461f0d9c713e8e34cd3a047d7319d8

USER root
COPY --chown=root:root wazuh-ca-bundle.pem /tmp/wazuh-local-ca-bundle.pem
RUN cat /etc/ssl/certs/ca-certificates.crt /tmp/wazuh-local-ca-bundle.pem \
        > /etc/ssl/certs/wazuh-combined-ca-bundle.pem \
    && chmod 0644 /etc/ssl/certs/wazuh-combined-ca-bundle.pem \
    && rm /tmp/wazuh-local-ca-bundle.pem

COPY --from=patcher --chown=1000:1000 \
    /app/src/wazuh_mcp_server/api/wazuh_indexer.py \
    /app/src/wazuh_mcp_server/api/wazuh_indexer.py
COPY --from=patcher --chown=1000:1000 \
    /app/src/wazuh_mcp_server/auth.py \
    /app/src/wazuh_mcp_server/auth.py

LABEL homelab.wazuh-indexer-x509-compat="python-3.13-no-x509-strict"
LABEL homelab.static-bearer-api-key="enabled-read-scope-preserved"
LABEL homelab.combined-ca-bundle="system-roots-plus-wazuh-trust-anchors"

USER 1000:1000
