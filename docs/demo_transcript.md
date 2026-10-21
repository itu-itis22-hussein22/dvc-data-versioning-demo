# Demo transcript (backup)

Full output of `python demo/run_demo.py --auto` with DVC 3.67.1. Experiment names are random and will differ on your run.

```text
Sandbox ready: dvc-demo-sandbox

[1/10] Start a DVC project inside a Git repo
DVC sits on top of Git. `dvc init` adds a small .dvc/ folder.
$ dvc init -q
$ git commit -q -m 'Initialize DVC'

[2/10] Configure remote storage
Big files go to a remote (S3, GCS, Azure, SSH, Drive...). Here it is just a local folder.
$ dvc remote add -d storage ../dvc-demo-storage
Setting 'storage' as a default remote.
$ dvc config core.autostage true
$ cat .dvc/config
[core]
    remote = storage
    autostage = true
['remote "storage"']
    url = ../../dvc-demo-storage
$ git commit -q -am 'Add DVC remote'

[3/10] Data v1 arrives -> track it with DVC
`dvc add` moves the file into the cache and leaves a tiny pointer file (.dvc) for Git. The CSV itself is git-ignored. (autostage = DVC git-adds the pointer for us.)
$ python src/make_dataset.py --version 1
Wrote data v1: 150 rows -> data/raw/data.csv
$ dvc add data/raw/data.csv
$ cat data/raw/data.csv.dvc
outs:
- md5: ba78b06ab7b1490dba7df6d78a7fcd44
  size: 31999
  hash: md5
  path: data.csv
$ git status --short
A  data/raw/.gitignore
A  data/raw/data.csv.dvc
$ git commit -q -m 'Data v1: 150 rows'

[4/10] Run the pipeline
dvc.yaml defines prepare -> train -> evaluate. `dvc repro` runs it and records the hash of every input/output in dvc.lock.
$ dvc dag
  +-----------------------+  
  | data/raw/data.csv.dvc |  
  +-----------------------+  
              *              
              *              
              *              
         +---------+         
         | prepare |         
         +---------+         
         **        **        
       **            *       
      *               **     
+-------+               *    
| train |             **     
+-------+            *       
         **        **        
           **    **          
             *  *            
        +----------+         
        | evaluate |         
        +----------+         
$ dvc repro
'data/raw/data.csv.dvc' didn't change, skipping
Running stage 'prepare':
> python src/prepare.py
prepare: 105 train rows, 45 test rows
Generating lock file 'dvc.lock'
Updating lock file 'dvc.lock'

Running stage 'train':
> python src/train.py
train: fitted RandomForest on 105 rows
Updating lock file 'dvc.lock'

Running stage 'evaluate':
> python src/evaluate.py
evaluate: {'accuracy': 0.7778, 'f1': 0.8276, 'roc_auc': 0.821, 'n_test': 45}
Updating lock file 'dvc.lock'
Use `dvc push` to send your updates to remote storage.
$ dvc metrics show
Path          accuracy    f1      n_test    roc_auc
metrics.json  0.7778      0.8276  45        0.821
$ git add -A
$ git commit -q -m 'Model trained on data v1'
$ git tag v1.0
$ dvc push
5 files pushed

[5/10] Data v2 arrives
DVC notices the data changed. Git only sees a new hash in the pointer file.
$ python src/make_dataset.py --version 2
Wrote data v2: 569 rows -> data/raw/data.csv
$ dvc status
prepare:
	changed deps:
		modified:           data/raw/data.csv
data/raw/data.csv.dvc:
	changed outs:
		modified:           data/raw/data.csv
$ dvc add data/raw/data.csv
$ git diff --cached data/raw/data.csv.dvc
diff --git a/data/raw/data.csv.dvc b/data/raw/data.csv.dvc
index c17f329..991fe8d 100644
--- a/data/raw/data.csv.dvc
+++ b/data/raw/data.csv.dvc
@@ -1,5 +1,5 @@
 outs:
-- md5: ba78b06ab7b1490dba7df6d78a7fcd44
-  size: 31999
+- md5: 597f07978de0eb402b7f22d9f256e744
+  size: 120381
   hash: md5
   path: data.csv

[6/10] Reproduce and compare
Re-run only what is affected, then compare metrics across Git revisions.
$ dvc repro
'data/raw/data.csv.dvc' didn't change, skipping
Running stage 'prepare':
> python src/prepare.py
prepare: 398 train rows, 171 test rows
Updating lock file 'dvc.lock'

Running stage 'train':
> python src/train.py
train: fitted RandomForest on 398 rows
Updating lock file 'dvc.lock'

Running stage 'evaluate':
> python src/evaluate.py
evaluate: {'accuracy': 0.9415, 'f1': 0.9537, 'roc_auc': 0.9893, 'n_test': 171}
Updating lock file 'dvc.lock'
Use `dvc push` to send your updates to remote storage.
$ git add -A
$ git commit -q -m 'Data v2: 569 rows, retrained'
$ git tag v2.0
$ dvc push
5 files pushed
$ dvc metrics diff v1.0 v2.0
Path          Metric    v1.0    v2.0    Change
metrics.json  accuracy  0.7778  0.9415  0.1637
metrics.json  f1        0.8276  0.9537  0.1261
metrics.json  n_test    45      171     126
metrics.json  roc_auc   0.821   0.9893  0.1683

[7/10] Nothing changed -> nothing re-runs
Every stage's hashes match dvc.lock, so DVC skips all of them.
$ dvc repro
'data/raw/data.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
Stage 'evaluate' didn't change, skipping
Data and pipelines are up to date.

[8/10] Time travel to v1.0
`git checkout` restores the pointer files; `dvc checkout` restores the matching data and model from the cache.
$ git checkout -q v1.0
$ dvc checkout
M       data/prepared/
M       data/raw/data.csv
M       models/model.pkl
$ rows data/raw/data.csv
data/raw/data.csv: 150 rows
$ cat metrics.json
{
  "accuracy": 0.7778,
  "f1": 0.8276,
  "roc_auc": 0.821,
  "n_test": 45
}
$ git checkout -q main
$ dvc checkout
M       data/prepared/
M       data/raw/data.csv
M       models/model.pkl
$ rows data/raw/data.csv
data/raw/data.csv: 569 rows

[9/10] A teammate clones the repo (or your laptop dies)
Delete the data and the local cache. `dvc pull` restores everything from remote storage.
$ du .dvc/cache
.dvc/cache: 20 files, 747 KB
$ rm .dvc/cache data/raw/data.csv models
deleted: .dvc/cache data/raw/data.csv models
$ dvc pull
A       data/raw/data.csv
A       models/model.pkl
5 files fetched and 2 files added
$ rows data/raw/data.csv
data/raw/data.csv: 569 rows
$ dvc status
Data and pipelines are up to date.

[10/10] Bonus: experiments
Try hyperparameters without new commits. Note `prepare` is skipped: its inputs did not change.
$ dvc exp run -S train.n_estimators=10 -S train.max_depth=2
Reproducing experiment 'leery-vang'
'data/raw/data.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping
Running stage 'train':
> python src/train.py
train: fitted RandomForest on 398 rows
Updating lock file 'dvc.lock'

Running stage 'evaluate':
> python src/evaluate.py
evaluate: {'accuracy': 0.9298, 'f1': 0.9444, 'roc_auc': 0.9809, 'n_test': 171}
Updating lock file 'dvc.lock'

Ran experiment(s): leery-vang
Experiment results have been applied to your workspace.
$ dvc exp show --no-pager --md --drop 'Created|State|Executor|prepare.*|train.seed|data.*|src.*|models.*'
| Experiment               | accuracy   | f1     | roc_auc   | n_test   | train.n_estimators   | train.max_depth   |
|--------------------------|------------|--------|-----------|----------|----------------------|-------------------|
| workspace                | 0.9298     | 0.9444 | 0.9809    | 171      | 10                   | 2                 |
| main                     | 0.9415     | 0.9537 | 0.9893    | 171      | 100                  | 5                 |
| └── 3374553 [leery-vang] | 0.9298     | 0.9444 | 0.9809    | 171      | 10                   | 2                 |


Demo complete. Explore it yourself: cd dvc-demo-sandbox
```
