#!/bin/sh
set -eu

# Run by the stopped hawser-updater container when I press Start in Dockhand.
# Follow the running agent's Compose files, including after a Dockhand deploy.
files=$(docker inspect --format '{{ index .Config.Labels "com.docker.compose.project.config_files" }}' hawser)
[ -n "$files" ] || { echo 'Hawser has no Compose source'; exit 1; }
set --
old_ifs=$IFS
IFS=,
for file in $files; do
  case "$file" in
    /opt/docker/*) [ -f "$file" ] || exit 1 ;;
    *) echo 'Hawser Compose source is outside /opt/docker'; exit 1 ;;
  esac
  set -- "$@" -f "$file"
done
IFS=$old_ifs
docker compose --project-name hawser "$@" pull hawser
docker compose --project-name hawser "$@" up -d --no-deps --no-build --pull never hawser
echo 'Hawser update finished; refresh the environment in Dockhand.'
