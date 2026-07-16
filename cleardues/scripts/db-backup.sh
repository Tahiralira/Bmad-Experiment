#!/usr/bin/env bash
# ClearDues database backup sidecar (WS9 — S6-C2, S6-M5).
#
# Runs inside the postgres:17 image (bind-mounted by docker-compose.yml) so
# pg_dump always matches the server version — no third-party backup image
# holding DB credentials.
#
# Modes:
#   once [prefix]   take one dump (default prefix "nightly"), prune, exit.
#                   Used by the pre-migrate-dump gate: a failed dump FAILS the
#                   deploy, so migrations never run without a fresh backup.
#   daemon          dump every day at $BACKUP_TIME UTC (default 03:00), prune.
#
# Dumps are pg_dump custom-format archives (compressed, pg_restore-able) in
# $BACKUP_DIR (the app-db-backups volume). Retention: $BACKUP_KEEP_DAYS
# (default 14). Offsite sync of the volume is a host-level step — see
# deployment.md ("Backups").
#
# Restore (full drill in deployment.md):
#   pg_restore -h db -U $POSTGRES_USER -d <target-db> --clean --if-exists <file>
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
BACKUP_TIME="${BACKUP_TIME:-03:00}"
HOST="${POSTGRES_SERVER:-db}"
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}"

wait_for_db() {
  # The db healthcheck can pass while the first-boot entrypoint is still on
  # its unix-socket-only phase; wait for a real TCP accept (bounded).
  for _ in $(seq 1 30); do
    pg_isready -q -h "$HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" && return 0
    sleep 2
  done
  echo "ERROR: database at ${HOST} not ready after 60s" >&2
  return 1
}

dump_once() {
  local prefix="${1:-nightly}"
  local stamp file
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  file="${BACKUP_DIR}/${prefix}-${POSTGRES_DB}-${stamp}.dump"
  mkdir -p "$BACKUP_DIR"
  wait_for_db
  pg_dump -Fc -h "$HOST" -U "$POSTGRES_USER" "$POSTGRES_DB" > "${file}.part"
  mv "${file}.part" "$file"
  echo "backup written: ${file} ($(du -h "$file" | cut -f1))"
  # Prune outside the retention window; clear stale partials from crashes.
  find "$BACKUP_DIR" -name '*.dump' -mtime "+${KEEP_DAYS}" -delete
  find "$BACKUP_DIR" -name '*.part' -mmin +60 -delete
}

case "${1:-once}" in
  once)
    dump_once "${2:-nightly}"
    ;;
  daemon)
    echo "nightly backups at ${BACKUP_TIME} UTC to ${BACKUP_DIR}, keeping ${KEEP_DAYS} days"
    while true; do
      now="$(date -u +%s)"
      next="$(date -u -d "today ${BACKUP_TIME}" +%s)"
      if [ "$next" -le "$now" ]; then
        next="$(date -u -d "tomorrow ${BACKUP_TIME}" +%s)"
      fi
      sleep $(( next - now ))
      # A failed nightly must not kill the daemon — log and try again tomorrow.
      dump_once nightly || echo "WARNING: nightly backup failed" >&2
    done
    ;;
  *)
    echo "usage: db-backup.sh [once [prefix] | daemon]" >&2
    exit 2
    ;;
esac
