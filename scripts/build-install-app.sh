#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python=/usr/bin/python3
if [[ -d "$root/.venv" ]]; then
    source "$root/.venv/bin/activate"
    python="$root/.venv/bin/python3"
fi
exec "$python" "$root/scripts/secure_build.py" app "$@"
