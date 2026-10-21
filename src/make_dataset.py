"""Simulate raw data "arriving" in two versions.

v1: an early, small snapshot (150 rows) with some mislabelled samples,
    like a first batch collected before data cleaning.
v2: the full, cleaned dataset (569 rows).

In a real project this file would not exist: new data would land from
a database export, a labelling tool, a sensor, etc. We only need a
reproducible way to produce two different versions of `data/raw/data.csv`
so we can show how DVC versions them.
"""
import argparse
from pathlib import Path

import numpy as np
from sklearn.datasets import load_breast_cancer

OUT = Path("data/raw/data.csv")


def main(version: int) -> None:
    df = load_breast_cancer(as_frame=True).frame  # 30 features + "target"
    df.columns = [c.replace(" ", "_") for c in df.columns]

    if version == 1:
        rng = np.random.default_rng(0)
        df = df.sample(n=150, random_state=0).reset_index(drop=True)
        noisy = rng.choice(len(df), size=20, replace=False)  # ~13% label noise
        df.loc[noisy, "target"] = 1 - df.loc[noisy, "target"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, float_format="%.6g")
    print(f"Wrote data v{version}: {len(df)} rows -> {OUT}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--version", type=int, choices=[1, 2], required=True)
    main(p.parse_args().version)
