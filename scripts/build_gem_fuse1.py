#!/usr/bin/env python3
"""Retired GEM-FUSE1 builder.

The tracked GEM-FUSE1 receipt records 100% candidate-dot overlap with the r13
lattice, above the strict 70% duplicate/stop threshold. No density exception is
authorized, so this builder is intentionally disabled to prevent recreating or
promoting a known lane duplicate. The historical artifact and receipts remain
available for audit; they are not slot approval.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "STOP: GEM-FUSE1 is a strict lane duplicate (100% overlap; limit 70%). "
        "No file was built or changed. Do not submit.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
