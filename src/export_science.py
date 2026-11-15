"""Export regional science without recalculating global scores or downloading data."""
import argparse
from pathlib import Path
from scientific_catalog import ROOT, build_science
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "web/public/data/science")
    args = parser.parse_args()
    index = build_science(ROOT / "data/features", ROOT / "data/results", ROOT / "data/processed", args.out,
                          pd.read_csv(ROOT / "data/targets.csv"))
    print(f"Exported {len(index['studies'])} regional studies, 72 PAI pairs and {len(index['artifacts'])} original artifacts to {args.out}")


if __name__ == "__main__":
    main()
