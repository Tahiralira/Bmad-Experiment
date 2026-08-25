#! /usr/bin/env bash
#
# Regenerate the frontend's typed OpenAPI client from the live backend schema.
#
# Run from the repo root, with the Compose stack up:
#
#     docker compose up -d
#     bash scripts/generate-client.sh
#
# The schema is pulled out of the *running backend container*, not a local
# virtualenv — the backend's dependencies are only installed in the image, so
# the previous host-python version of this script could not run on a normal
# checkout at all (WS11).
#
# `frontend/openapi.json` is gitignored: it is a build input, not a source
# file. The generated `frontend/src/client/` IS committed, so a fresh clone
# type-checks without needing Docker.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! docker compose ps --status running --services 2>/dev/null | grep -qx backend; then
  echo "error: the 'backend' service is not running. Start it with:" >&2
  echo "         docker compose up -d" >&2
  exit 1
fi

echo "==> Dumping the OpenAPI schema from the backend container"
docker compose exec -T backend \
  python -c 'import app.main, json; print(json.dumps(app.main.app.openapi()))' \
  > frontend/openapi.json

# A failed exec can still leave a zero-byte file behind; refuse to hand that
# to the generator, which would happily wipe src/client/.
if [ ! -s frontend/openapi.json ]; then
  echo "error: the schema dump was empty; leaving src/client/ untouched" >&2
  rm -f frontend/openapi.json
  exit 1
fi

echo "==> Generating the client into frontend/src/client/"
cd frontend
npm run generate-client

echo
echo "Done. Review and commit the changes under frontend/src/client/."
