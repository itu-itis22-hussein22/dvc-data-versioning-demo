# Live demo: what to show, what to say, what to paste

**Total: 4 minutes.** **Main message:** same code, new data, and DVC remembers which data made which model.

**How to use this file:** copy the **whole grey box**, paste it into PowerShell once.
The commands run one after another. If the last command doesn't start by itself, press **Enter** once.
Then say the text under it.

> If Windows Terminal asks *"You are about to paste text that contains multiple lines"*, click **Paste anyway**.

---

## BEFORE your turn (not in front of the class)

Open a new **PowerShell** window (not `bash`). Paste these two boxes, one at a time:

```
conda activate dvc
cd ~\Desktop\dvc-data-versioning-demo
git pull
```

```
python demo/run_demo.py --setup
cd ..\dvc-demo-sandbox
dvc init -q
git commit -q -m "Initialize DVC"
dvc remote add -d storage ../dvc-demo-storage
dvc config core.autostage true
git commit -q -am "Add remote"
cls
```

Check: your prompt ends with **`dvc-demo-sandbox>`** and the screen is empty.

Then get your screen ready:
1. **Terminal:** make the font big (Ctrl and +).
2. **Browser:** open your repo: https://github.com/itu-itis22-hussein22/dvc-data-versioning-demo
3. **Backup:** keep `docs/screenshots/` open in another tab.

---

## 1 · Show your code on GitHub · 0:00 – 0:30

**Show:** the GitHub repo page in the browser.

> "This is my repository. The `src` folder has normal Python ML code: prepare the data, train, evaluate."

**Click** `dvc.yaml`.

> "This file is the pipeline. It has three steps. Each one says which command to run, which files it uses, and which files it creates. That's how DVC knows what depends on what."

**Switch** to the terminal.

> "Let's see it working."

---

## 2 · Data v1 arrives · 0:30 – 1:00

**Paste:**
```
python src/make_dataset.py --version 1
dvc add data/raw/data.csv
cat data/raw/data.csv.dvc
git commit -q -m "Data v1"
```

**You'll see:** `150 rows`, then a small file with `md5: ...`

> "My first dataset arrives: 150 rows, and some labels are wrong.
> I give it to DVC with `dvc add`. DVC moves the real data into its cache, and this small file is all Git sees: a hash, a size and a path. I commit it like normal code."

---

## 3 · Train on v1 · 1:00 – 1:30

**Paste:**
```
dvc repro
dvc metrics show
```

**You'll see:** `Running stage 'prepare'`, `'train'`, `'evaluate'`, then a table with **accuracy 0.7778**

> "`dvc repro` runs my pipeline: prepare, train, evaluate, in the right order.
> Accuracy is 0.78. Not great, because the data is small and messy."

---

## 4 · Save version 1 · 1:30 – 1:45

**Paste:**
```
git add -A
git commit -q -m "Model v1"
git tag v1.0
dvc push
```

**You'll see:** `5 files pushed`

> "I save this as version 1. Git saves the code and the pointers, and `dvc push` uploads the data and the model to storage."

---

## 5 · New data arrives · 1:45 – 2:05

**Paste:**
```
python src/make_dataset.py --version 2
dvc status
```

**You'll see:** `569 rows`, then `modified: data\raw\data.csv`

> "Now the full, clean dataset arrives: 569 rows. I didn't tell DVC anything, but `dvc status` already sees that the data changed and the pipeline is out of date."

---

## 6 · Retrain and save version 2 · 2:05 – 2:40

**Paste:**
```
dvc add data/raw/data.csv
dvc repro
git add -A
git commit -q -m "Model v2"
git tag v2.0
dvc push
```

**You'll see:** the 3 stages running again, accuracy **0.9415**, `5 files pushed`

> "I track the new data and run the pipeline again. Notice I didn't change a single line of code. Then I save it as version 2."

---

## 7 · Compare ⭐ the main moment · 2:40 – 3:05

**Paste:**
```
dvc metrics diff v1.0 v2.0
```

**You'll see:** a table with `accuracy 0.7778 → 0.9415`

> *(Slow down and point at the screen.)*
> "Here's the result. Same code, same settings. Only the data changed, and accuracy went from **0.78 to 0.94**. And DVC knows exactly which data produced which model."

---

## 8 · Go back in time · 3:05 – 3:35

**Paste:**
```
git checkout -q v1.0
dvc checkout
cat metrics.json
```

**You'll see:** `M data\raw\data.csv`, `M models\model.pkl`, then **accuracy 0.7778**

> "Now I go back to version 1. Git brings back the old pointers, DVC brings back the old data and the old model. Accuracy is 0.78 again, exactly reproduced."

---

## 9 · Back to the latest · 3:35 – 3:50

**Paste:**
```
git checkout -q main
dvc checkout
cat metrics.json
```

**You'll see:** accuracy **0.9415** again

> "And with the same two commands, I'm back on the latest version."

---

## 10 · Close · 3:50 – 4:00

No command.

> "So with DVC, every model is tied to the exact data and code that produced it, and I can go back to any version with two commands. Thank you, I'm happy to take questions."

---

## Optional extras (only if you have time, or if someone asks)

**"How do you know which version is which?"**
```
git --no-pager log --oneline
```
> "Every version is a commit with a tag. Git remembers it, so I don't have to."

**"What if my laptop dies / a teammate clones the repo?"**
```
Remove-Item -Recurse -Force .dvc/cache, data/raw/data.csv, models/model.pkl
dvc pull
```
> "I just deleted my data and model. One `dvc pull` and everything comes back from storage."

---

## If something goes wrong

| Problem | What to do |
|---|---|
| A command shows red text | Don't debug live. Say *"I'll show the screenshot instead"* and open the screenshot below |
| You see `>>` or `>` at the start of a line | Press **Ctrl + C** |
| Prompt starts with `aya@DESKTOP` | You're in bash. Type `exit` |
| Screen is too full | Type `cls` and press Enter |

| You were at | Open screenshot |
|---|---|
| 2 · Data v1 | `step03.png` |
| 3–4 · Train / save | `step04.png` |
| 5 · New data | `step05.png` |
| 6–7 · Retrain / compare | `step06.png` |
| 8–9 · Time travel | `step08.png` |

## To rehearse again from zero

```
cd ~\Desktop\dvc-data-versioning-demo
```
Then paste the second "BEFORE your turn" box again.
