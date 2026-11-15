"""Reproduce Marco's original legacy contract without external experiment inputs.

The unified app reads comparisons.json v3 and global-rankings.json instead.
The historical calculation remains in Git at e75ecdb:src/export_web.py.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/reference/marco_analogos.json")
    parser.add_argument("--out", type=Path, default=ROOT / "web/public/data/analogos.json")
    args = parser.parse_args(argv)
    source = args.source.read_bytes()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(source)
    print(f"Restored legacy snapshot: {args.out}. Unified science uses comparisons.json v3; no score was recalculated.")


if __name__ == "__main__":
    main()
