"""Stage 1 - split the raw data into train and test sets."""
from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

params = yaml.safe_load(open("params.yaml"))["prepare"]

df = pd.read_csv("data/raw/data.csv")
train, test = train_test_split(
    df,
    test_size=params["test_size"],
    random_state=params["seed"],
    stratify=df["target"],
)

out = Path("data/prepared")
out.mkdir(parents=True, exist_ok=True)
train.to_csv(out / "train.csv", index=False)
test.to_csv(out / "test.csv", index=False)
print(f"prepare: {len(train)} train rows, {len(test)} test rows")
