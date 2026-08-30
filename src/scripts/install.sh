#!/usr/bin/env bash
# Thin POSIX shim around scripts/install.py. Use install.py directly for
# full cross-platform behavior; this script exists for muscle-memory
# `./install.sh` usage on macOS / Linux.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$here/install.py" "$@"

