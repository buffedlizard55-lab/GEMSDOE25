#!/usr/bin/env python3
"""Retired H31-C registry writer.

The tracked H31-C lane receipt records 100% candidate-dot overlap with the r13
lattice, above the strict 70% duplicate/stop threshold. This legacy writer could
restore H31-C as primary and replace the safer registry status, so it is disabled.
The historical TIFF and receipts remain available for audit; do not submit.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "STOP: H31-C fails the strict lane rule (100% overlap; limit 70%). "
        "Registry was not changed. Do not submit.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
