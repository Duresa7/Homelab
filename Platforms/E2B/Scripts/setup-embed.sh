#!/bin/sh
# Lay out E2B Embed under /opt/e2b on e2b-01 from a pinned e2b-dev/runtime commit,
# apply the two dashboard patches, append the pinned secrets and the built-in
# OpenTelemetry collector, and start the stack. Run as root.
#
#   setup-embed.sh <runtime commit> [secrets file]
#
# The secrets file holds TEAM_API_KEY, ADMIN_TOKEN and SANDBOX_ACCESS_TOKEN_HASH_SEED
# lines, staged mode 0600 from my password manager. It is appended to .env and shredded.
# An upgrade reruns this with a newer commit and no secrets file: the existing
# secret lines are carried over from the current .env.
set -eu
REV=${1:?runtime commit}
SECRETS=${2:-}
D=/opt/e2b
RAW=https://raw.githubusercontent.com/e2b-dev/runtime/$REV/embed/compose
umask 077
install -d -m 0750 "$D"
cd "$D"

curl -fsSL "$RAW/compose.yaml" -o compose.yaml.new
curl -fsSL "$RAW/.env" -o env.new

# Dashboard patch: the browser reaches sandbox traffic through NPM over HTTPS, so an
# HTTPS dashboard page does not block it as mixed content.
n=$(grep -c 'PUBLIC_SANDBOX_URL: http://${E2B_DASHBOARD_HOST:-localhost}:3002' compose.yaml.new || true)
[ "$n" = 1 ] || { echo "FIX: expected one PUBLIC_SANDBOX_URL line, found $n"; exit 1; }
sed -i 's|PUBLIC_SANDBOX_URL: http://${E2B_DASHBOARD_HOST:-localhost}:3002|PUBLIC_SANDBOX_URL: https://sandbox.e2b.alphasecunited.com|' compose.yaml.new
# Second patch (2026-11-11): the dashboard is served over HTTPS, so its sign-in
# cookie can carry the Secure flag.
n=$(grep -c 'DASHBOARD_COOKIE_SECURE: "false"' compose.yaml.new || true)
[ "$n" = 1 ] || { echo "FIX: expected one DASHBOARD_COOKIE_SECURE line, found $n"; exit 1; }
sed -i 's|DASHBOARD_COOKIE_SECURE: "false"|DASHBOARD_COOKIE_SECURE: "true"|' compose.yaml.new

{
  cat env.new
  echo
  echo "# --- e2b-01 additions ---"
  if [ -n "$SECRETS" ]; then
    cat "$SECRETS"
  else
    grep -E '^(TEAM_API_KEY|ADMIN_TOKEN|SANDBOX_ACCESS_TOKEN_HASH_SEED)=' .env
  fi
  echo "HUGEPAGES=3072"
  echo "E2B_OTEL_COLLECTOR_GRPC_ENDPOINT=127.0.0.1:4317"
  echo "COMPOSE_PROFILES=otel"
} > env.next
[ -n "$SECRETS" ] && shred -u "$SECRETS"
[ "$(grep -cE '^(TEAM_API_KEY|ADMIN_TOKEN|SANDBOX_ACCESS_TOKEN_HASH_SEED)=' env.next)" = 3 ] || { echo "FIX: secrets missing"; exit 1; }

mv compose.yaml.new compose.yaml
mv env.next .env
rm -f env.new
chmod 0600 .env compose.yaml
echo "$REV" > RUNTIME_COMMIT
docker compose config --quiet && echo "compose config ok"
echo "patched: $(grep -c -E 'PUBLIC_SANDBOX_URL: https://sandbox.e2b.alphasecunited.com|DASHBOARD_COOKIE_SECURE: "true"' compose.yaml)"
nohup docker compose up -d --wait > /var/log/e2b-up.log 2>&1 &
echo "up started"
