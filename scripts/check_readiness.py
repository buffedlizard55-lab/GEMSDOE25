#!/usr/bin/env python3
"""Check supplied computed receipts; never authorizes an upload or a weekly slot."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems25.readiness import assess_readiness  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', help='JSON receipts bound to the exact raster SHA256')
    parser.add_argument('--output', required=True, help='JSON decision path')
    args = parser.parse_args()
    with open(args.evidence) as stream:
        evidence = json.load(stream)
    if not isinstance(evidence, dict):
        parser.error('evidence must be a JSON object')
    result = assess_readiness(evidence)
    with open(args.output, 'w') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(result['decision'])
    return 0 if result['selector_eligible'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
