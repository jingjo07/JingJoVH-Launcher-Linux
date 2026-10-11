#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
unset APPDIR APPIMAGE
exec python3 "$script_dir/launcher.py" "$@"
