# Live demo script: type the commands yourself

Use this if you want to run every DVC command by hand in front of the audience.
Every command below works in **PowerShell, Git Bash, macOS and Linux**, except for the
one line in step 9 that has separate versions.

> Prefer not to type? `python demo/run_demo.py` runs the same steps when you press Enter.

---

## 0. Before the talk (not in front of the audience)

From the repo folder, with your virtual environment active:

```bash
python demo/run_demo.py --setup
cd ../dvc-demo-sandbox
```

This makes a clean folder `dvc-demo-sandbox` next to the repo, containing the project code
in a fresh Git repo with no DVC yet. **Run it again before every rehearsal** to start over.

Make the terminal font big (Ctrl + `+`) and keep this file open on your phone or a second screen.

---

## 1. Start DVC inside the Git repo

```bash
dvc init
git commit -m "Initialize DVC"
```

> *Say:* DVC sits on top of Git. `dvc init` only adds a small `.dvc/` folder.

## 2. Add remote storage

```bash
dvc remote add -d storage ../dvc-demo-storage
dvc config core.autostage true
```

> *Say:* In real life this would be S3, Google Drive or Azure. Here it's just a folder.
> Autostage means DVC runs `git add` for me.

```bash
git commit -am "Add DVC remote"
```

## 3. Data v1 arrives: track it

```bash
python src/make_dataset.py --version 1
dvc add data/raw/data.csv
cat data/raw/data.csv.dvc
```

> *Say:* The CSV went into DVC's cache. Git only gets this 5-line pointer: a hash, a size, a path.

```bash
git status
git commit -m "Data v1: 150 rows"
```

## 4. Run the pipeline

```bash
dvc dag
dvc repro
dvc metrics show
```

> *Say:* `dvc.yaml` defines prepare → train → evaluate. Accuracy on v1 is **0.78**.

```bash
git add -A
git commit -m "Model trained on data v1"
git tag v1.0
dvc push
```

> *Say:* Git stores code and pointers. `dvc push` uploads the data and model to storage.

## 5. Data v2 arrives

```bash
python src/make_dataset.py --version 2
dvc status
```

> *Say:* DVC noticed the data changed and that `prepare` is now out of date.

```bash
dvc add data/raw/data.csv
git diff --cached data/raw/data.csv.dvc
```

> *Say:* For Git, the whole dataset change is just a new hash.

## 6. Reproduce and compare ⭐ (main moment)

```bash
dvc repro
git add -A
git commit -m "Data v2: 569 rows"
git tag v2.0
dvc push
dvc metrics diff v1.0 v2.0
```

> *Say:* Same code, same parameters. Only the data changed: **0.78 → 0.94**,
> and every model is linked to the exact data that trained it.

## 7. Nothing changed, nothing runs

```bash
dvc repro
```

> *Say:* All hashes match `dvc.lock`, so every stage is skipped.

## 8. Go back in time to v1.0

```bash
git checkout v1.0
dvc checkout
python -c "import pandas as pd; print(len(pd.read_csv('data/raw/data.csv')), 'rows')"
cat metrics.json
```

> *Say:* Git brought back the old pointers, DVC brought back the old data and model. 150 rows, 0.78.

```bash
git checkout main
dvc checkout
```

## 9. Lose everything, get it back

Delete the cache, the data and the model. **Pick the line for your terminal:**

PowerShell:
```powershell
Remove-Item -Recurse -Force .dvc/cache, data/raw/data.csv, models
```
Git Bash / macOS / Linux:
```bash
rm -rf .dvc/cache data/raw/data.csv models
```

Then:
```bash
dvc pull
dvc status
```

> *Say:* This is what a teammate does after `git clone`: one `dvc pull` and they have the exact same data and model.

## 10. Bonus: experiments (skip if short on time)

```bash
dvc exp run -S train.n_estimators=10 -S train.max_depth=2
dvc exp show --only-changed
```

> *Say:* I tried new hyperparameters without a commit. `prepare` was skipped because its inputs didn't change.
> (If the table opens full-screen, press `q` to close it. Maximise the terminal window so it fits.)

---

## If something goes wrong

| Problem | Fix |
|---|---|
| A command errors in the middle | Stay calm and switch to `docs/screenshots/stepNN.png` for that step |
| `git checkout v1.0` warns about "detached HEAD" | That's normal; just continue |
| `git commit` says "nothing to commit" | Fine, carry on with the next command |
| You want to restart from zero | `cd ../dvc-data-versioning-demo` then `python demo/run_demo.py --setup` |
| In a hurry, want to jump ahead | Use the automatic runner: `python demo/run_demo.py --from 6` (needs one full run first) |
