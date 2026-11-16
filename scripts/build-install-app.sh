#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -d "$root/.venv" ]]; then
    source "$root/.venv/bin/activate"
fi
exec python3 "$root/scripts/secure_build.py" app "$@"
