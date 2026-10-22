# Demo transcript

Output of `python demo/run_demo.py --auto`. Experiment names are random and will be different on your run.

```text
Sandbox ready: dvc-demo-sandbox

[1/10] Set up DVC
dvc init adds a small .dvc/ folder to the git repo.
$ dvc init -q
$ git commit -q -m 'Initialize DVC'

[2/10] Add remote storage
This is where DVC uploads data. Here it's a local folder instead of S3 or Drive.
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

[3/10] Track data v1
dvc add moves the data into the cache. Git only gets the small .dvc file.
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
dvc repro runs prepare -> train -> evaluate and saves the hashes in dvc.lock.
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
DVC sees the data changed. For git it's just a new hash.
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

[6/10] Retrain and compare
Same code, new data.
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

[7/10] Run again with no changes
Nothing changed, so every stage is skipped.
$ dvc repro
'data/raw/data.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
Stage 'evaluate' didn't change, skipping
Data and pipelines are up to date.

[8/10] Go back to v1.0
git checkout brings back the old .dvc files, dvc checkout brings back the matching data.
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

[9/10] Restore from storage
Delete the data and the cache, then get everything back with dvc pull.
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

[10/10] Experiments
Try other parameters without committing.
$ dvc exp run -S train.n_estimators=10 -S train.max_depth=2
Reproducing experiment 'olive-veep'
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

Ran experiment(s): olive-veep
Experiment results have been applied to your workspace.
$ dvc exp show --no-pager --md --drop 'Created|State|Executor|prepare.*|train.seed|data.*|src.*|models.*'
| Experiment               | accuracy   | f1     | roc_auc   | n_test   | train.n_estimators   | train.max_depth   |
|--------------------------|------------|--------|-----------|----------|----------------------|-------------------|
| workspace                | 0.9298     | 0.9444 | 0.9809    | 171      | 10                   | 2                 |
| main                     | 0.9415     | 0.9537 | 0.9893    | 171      | 100                  | 5                 |
| └── 153a773 [olive-veep] | 0.9298     | 0.9444 | 0.9809    | 171      | 10                   | 2                 |


Done.
```
