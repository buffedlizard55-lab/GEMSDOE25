import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retired_lattice_gap_publisher_exits_without_creating_files():
    before = {p.name: p.stat().st_size for p in (ROOT/'docs/downloads').iterdir()}
    result = subprocess.run([sys.executable, str(ROOT/'scripts/build_unique_submission.py')], capture_output=True, text=True)
    assert result.returncode == 2 and 'DO NOT SUBMIT' in result.stderr
    assert before == {p.name: p.stat().st_size for p in (ROOT/'docs/downloads').iterdir()}
