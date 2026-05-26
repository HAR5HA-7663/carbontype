#!/usr/bin/env bash
# carbontype setup
# Creates a Python 3.10+ venv at ./.venv and installs runtime deps.
# Safe to re-run. Idempotent.
set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# 1. locate a Python >= 3.10
find_python() {
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      v="$("$c" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
      maj="${v%%.*}"; min="${v##*.}"
      if [ "$maj" -ge 3 ] && [ "$min" -ge 10 ]; then
        echo "$c"; return 0
      fi
    fi
  done
  return 1
}

PY="$(find_python || true)"

if [ -z "${PY}" ]; then
  if [ "$(uname -s)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    echo "no Python >=3.10 found; installing python@3.12 via Homebrew..."
    brew install python@3.12
    PY="$(find_python)"
  else
    echo "error: Python 3.10+ required. Install it and re-run." >&2
    exit 1
  fi
fi
echo "using $PY ($("$PY" --version))"

# 2. venv
if [ ! -d ".venv" ]; then
  "$PY" -m venv .venv
fi

# 3. deps
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
.venv/bin/python -c "from pynput.keyboard import Controller; print('pynput OK')"

# 4. perms
chmod +x carbontype carbontype.py

cat <<'EOF'

setup complete.

run:
  ./carbontype sample.txt --wpm 60

macOS first-run note:
  pynput needs Accessibility permission. The first keystroke will be blocked
  and macOS will prompt; enable your terminal app under
  System Settings -> Privacy & Security -> Accessibility, then re-run.
EOF
