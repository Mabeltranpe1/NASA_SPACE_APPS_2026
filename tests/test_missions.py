"""
Checks the mission-type filters of the web app (web/src/comparator/missions.ts):
the "suitable for" score equals the browser comparator with the mission's weights, elevation
stays at 0 and the variables switched off per body stay off. Mission types only change weights,
so the scoring itself is still the one checked by tests/test_web_port.py against compare.py.

    python tests/test_missions.py        (needs node >= 22)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_missions():
    out = subprocess.run(["node", "--experimental-strip-types", "--no-warnings",
                          str(ROOT / "web" / "scripts" / "check-missions.ts")],
                         capture_output=True, text=True)
    print(out.stdout, out.stderr)
    assert out.returncode == 0


if __name__ == "__main__":
    test_missions()
    print("OK")
