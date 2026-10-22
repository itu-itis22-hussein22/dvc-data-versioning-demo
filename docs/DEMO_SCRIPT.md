# 4-minute live demo script

**The one message:** same code, new data, and DVC remembers which data made which model.

Copy-paste each block, press Enter, then say the line under it.
Every command works in PowerShell, Git Bash, macOS and Linux.

---

## Step 0 · Setup (before you present, NOT live)

From the repo folder, with your virtual environment active:

```bash
python demo/run_demo.py --setup
cd ../dvc-demo-sandbox
dvc init
git commit -m "Initialize DVC"
dvc remote add -d storage ../dvc-demo-storage
dvc config core.autostage true
git commit -am "Add remote"
```

Then:
- Leave this terminal open and make the font big (Ctrl and +).
- Open `dvc.yaml` in VS Code next to the terminal.
- Open the `docs/screenshots/` folder in a tab, in case something breaks.

To start over for another rehearsal: `cd ../dvc-data-versioning-demo` and run Step 0 again.

---

## Step 1 · Show your code (0:00 – 0:30)

No command. Switch to VS Code and show `dvc.yaml`.

> "This is my pipeline: prepare, train, evaluate. A random forest on a cancer dataset.
> Now watch what happens when the data changes."

---

## Step 2 · Data v1 arrives (0:30 – 1:15)

```bash
python src/make_dataset.py --version 1
dvc add data/raw/data.csv
cat data/raw/data.csv.dvc
```

> "My first dataset, 150 messy rows. DVC moved it into its cache,
> and Git only gets this 5-line file with a hash."

```bash
git commit -m "Data v1"
```

---

## Step 3 · Train on v1 (1:15 – 2:00)

```bash
dvc repro
dvc metrics show
```

> "DVC ran all three stages. Accuracy is 0.78."

```bash
git add -A
git commit -m "Model v1"
git tag v1.0
dvc push
```

> "I save this version: Git keeps the code and pointers,
> and dvc push uploads the data to storage."

---

## Step 4 · Data v2 arrives ⭐ main moment (2:00 – 3:00)

```bash
python src/make_dataset.py --version 2
dvc status
```

> "New, clean data arrived, 569 rows. DVC noticed immediately."

```bash
dvc add data/raw/data.csv
dvc repro
git add -A
git commit -m "Model v2"
git tag v2.0
dvc push
dvc metrics diff v1.0 v2.0
```

> "Same code, same settings. Only the data changed, and accuracy went from
> **0.78 to 0.94**. DVC knows exactly which data made which model."

---

## Step 5 · Go back in time (3:00 – 3:45)

```bash
git checkout v1.0
dvc checkout
cat metrics.json
```

> "I go back to version 1, and the old data and old model are back.
> That's reproducibility."

(A "detached HEAD" warning is normal. Ignore it.)

```bash
git checkout main
dvc checkout
```

---

## Step 6 · Close (3:45 – 4:00)

No command.

> "So with DVC, every model is tied to the exact data that produced it,
> and you can go back to any version with two commands. Thank you."

---

## Optional extra · only if your rehearsal is under 3:30

Add this after Step 5. It shows a teammate getting everything from storage.

Delete the local data. **Pick the line for your terminal:**

PowerShell:
```powershell
Remove-Item -Recurse -Force .dvc/cache, data/raw/data.csv, models/model.pkl
```
Git Bash / macOS / Linux:
```bash
rm -rf .dvc/cache data/raw/data.csv models/model.pkl
```

Then:
```bash
dvc pull
```

> "I deleted my data. One dvc pull, and it's all back from storage.
> That's what a teammate does after cloning the repo."

---

## If something breaks

Don't debug live. Say *"I'll show the screenshot instead"* and open:

| You were on | Open |
|---|---|
| Step 2 | `docs/screenshots/step03.png` |
| Step 3 | `docs/screenshots/step04.png` |
| Step 4 | `docs/screenshots/step05.png`, then `step06.png` |
| Step 5 | `docs/screenshots/step08.png` |
| Optional extra | `docs/screenshots/step09.png` |
