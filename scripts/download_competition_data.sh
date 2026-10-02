#!/usr/bin/env bash
# Data placement in one command (the name used in earlier briefs).
# The DrivenData data page is login-walled, so this restores the SHA-256-pinned *owner mirrors* of the competition files
# (and the official-source derivatives) from the owner's public GitHub repositories into $GEMS_DATA_DIR (default: ./data).
# A hash match proves the mirror is unchanged; it does NOT authenticate the bytes as organizer files (IR-25-PROVENANCE).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
"$PY" scripts/restore_data.py --group all
echo "Next: $PY scripts/build_features.py && $PY scripts/build_addons.py"
