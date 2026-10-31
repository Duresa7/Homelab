# syntax=docker/dockerfile:1
#
# ssh-mcp (https://github.com/tufantunc/ssh-mcp), pinned to one npm release.
# Upstream ships a Dockerfile that builds from a source checkout; installing the published
# package instead keeps the build to one pinned, provenance-attested artifact.

FROM node:22-slim

ARG SSH_MCP_VERSION=2.22.0
RUN npm install -g --omit=optional "ssh-mcp@${SSH_MCP_VERSION}" \
 && npm cache clean --force \
 && ssh-mcp --help >/dev/null

# ssh-mcp takes its bearer token only as a flag. Reading it from the environment here keeps
# it out of the Compose file and the container's recorded command.
RUN cat > /usr/local/bin/ssh-mcp-http <<'EOS' && chmod 755 /usr/local/bin/ssh-mcp-http
#!/bin/sh
set -eu
: "${SSH_MCP_BEARER_TOKEN:?SSH_MCP_BEARER_TOKEN is not set}"
exec ssh-mcp --config=/config/config.toml --transport=http \
  --httpHost=0.0.0.0 --httpPort=8813 \
  --allowedHosts=192.168.40.39:8813,127.0.0.1:8813,localhost:8813 \
  --hostKeyMode=strict --bearerToken="$SSH_MCP_BEARER_TOKEN" "$@"
EOS

# The audit log lands under $XDG_DATA_HOME/ssh-mcp, rotated at 100 MB with ten files kept.
ENV XDG_DATA_HOME=/data HOME=/tmp
USER 65532:65532
EXPOSE 8813
ENTRYPOINT ["/usr/local/bin/ssh-mcp-http"]
