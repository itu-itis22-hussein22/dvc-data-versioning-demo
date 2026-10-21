"""Stage 3 - evaluate the model on the test set and write metrics + plots."""
import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

test = pd.read_csv("data/prepared/test.csv")
X, y = test.drop(columns="target"), test["target"]

with open("models/model.pkl", "rb") as f:
    model = pickle.load(f)

pred = model.predict(X)
proba = model.predict_proba(X)[:, 1]

metrics = {
    "accuracy": round(accuracy_score(y, pred), 4),
    "f1": round(f1_score(y, pred), 4),
    "roc_auc": round(roc_auc_score(y, proba), 4),
    "n_test": int(len(test)),
}
Path("eval").mkdir(exist_ok=True)
json.dump(metrics, open("metrics.json", "w"), indent=2)

# Rows of (actual, predicted) -> rendered as a confusion matrix by `dvc plots`
pd.DataFrame({"actual": y, "predicted": pred}).to_csv(
    "eval/predictions.csv", index=False
)
print("evaluate:", metrics)
