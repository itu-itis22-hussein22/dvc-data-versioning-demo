"""Live, step-by-step DVC demo.

Copies the project code into a fresh sandbox folder (next to this repo),
then walks through the DVC workflow one command at a time:

    python demo/run_demo.py            # interactive: press Enter before each step
    python demo/run_demo.py --auto     # run everything without pausing
    python demo/run_demo.py --from 4   # skip ahead (sandbox must already exist)

Nothing in this repository is modified; all git/DVC state lives in
../dvc-demo-sandbox and ../dvc-demo-storage (the "remote").
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SANDBOX = REPO.parent / "dvc-demo-sandbox"
STORAGE = REPO.parent / "dvc-demo-storage"
PY = Path(sys.executable).name if sys.platform == "win32" else sys.executable

# ANSI colours (work in modern Windows Terminal, macOS, Linux)
B, C, Y, G, D, R = "\033[1m", "\033[36m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


# ---------------------------------------------------------------- built-ins
# A few tiny portable stand-ins for shell tools, so the demo runs the same
# on Windows, macOS and Linux. They are shown on screen like normal commands.
def _rel(p):
    return Path(p).relative_to(SANDBOX).as_posix()


def _cat(path):
    print(Path(path).read_text().rstrip())


def _rows(path):
    n = sum(1 for _ in open(path)) - 1
    print(f"{_rel(path)}: {n} rows")


def _force_rmtree(p):
    # DVC marks cached files read-only; Windows refuses to delete those
    def fix(func, path, _):
        Path(path).chmod(0o700)
        func(path)
    shutil.rmtree(p, onerror=fix)


def _rm(*paths):
    for p in map(Path, paths):
        if p.is_dir():
            _force_rmtree(p)
        elif p.exists():
            p.chmod(0o600)
            p.unlink()
    print("deleted:", " ".join(_rel(p) for p in paths))


def _du(path):
    p = Path(path)
    files = [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
    size = sum(f.stat().st_size for f in files) / 1024
    print(f"{_rel(path)}: {len(files)} files, {size:.0f} KB")


BUILTINS = {"cat": _cat, "rows": _rows, "rm": _rm, "du": _du}


# -------------------------------------------------------------------- steps
STEPS = [
    ("Start a DVC project inside a Git repo",
     "DVC sits on top of Git. `dvc init` adds a small .dvc/ folder.",
     ["git init -q -b main", "dvc init -q", "git commit -q -m 'Initialize DVC'"]),

    ("Configure remote storage",
     "Big files go to a remote (S3, GCS, Azure, SSH, Drive...). "
     "Here it is just a local folder.",
     ["dvc remote add -d storage ../dvc-demo-storage",
      "dvc config core.autostage true",
      "cat .dvc/config",
      "git commit -q -am 'Add DVC remote'"]),

    ("Data v1 arrives -> track it with DVC",
     "`dvc add` moves the file into the cache and leaves a tiny pointer "
     "file (.dvc) for Git. The CSV itself is git-ignored. "
     "(autostage = DVC git-adds the pointer for us.)",
     ["python src/make_dataset.py --version 1",
      "dvc add data/raw/data.csv",
      "cat data/raw/data.csv.dvc",
      "git status --short",
      "git commit -q -m 'Data v1: 150 rows'"]),

    ("Run the pipeline",
     "dvc.yaml defines prepare -> train -> evaluate. `dvc repro` runs it "
     "and records the hash of every input/output in dvc.lock.",
     ["dvc dag", "dvc repro", "dvc metrics show",
      "git add -A",
      "git commit -q -m 'Model trained on data v1'", "git tag v1.0",
      "dvc push"]),

    ("Data v2 arrives",
     "DVC notices the data changed. Git only sees a new hash in the pointer file.",
     ["python src/make_dataset.py --version 2",
      "dvc status",
      "dvc add data/raw/data.csv",
      "git diff --cached data/raw/data.csv.dvc"]),

    ("Reproduce and compare",
     "Re-run only what is affected, then compare metrics across Git revisions.",
     ["dvc repro",
      "git add -A", "git commit -q -m 'Data v2: 569 rows, retrained'",
      "git tag v2.0", "dvc push",
      "dvc metrics diff v1.0 v2.0"]),

    ("Nothing changed -> nothing re-runs",
     "Every stage's hashes match dvc.lock, so DVC skips all of them.",
     ["dvc repro"]),

    ("Time travel to v1.0",
     "`git checkout` restores the pointer files; `dvc checkout` restores "
     "the matching data and model from the cache.",
     ["git checkout -q v1.0", "dvc checkout", "rows data/raw/data.csv",
      "cat metrics.json",
      "git checkout -q main", "dvc checkout", "rows data/raw/data.csv"]),

    ("A teammate clones the repo (or your laptop dies)",
     "Delete the data and the local cache. `dvc pull` restores everything "
     "from remote storage.",
     ["du .dvc/cache", "rm .dvc/cache data/raw/data.csv models",
      "dvc pull", "rows data/raw/data.csv", "dvc status"]),

    ("Bonus: experiments",
     "Try hyperparameters without new commits. Note `prepare` is skipped: "
     "its inputs did not change.",
     ["dvc exp run -S train.n_estimators=10 -S train.max_depth=2",
      "dvc exp show --no-pager --md --drop 'Created|State|Executor|prepare.*|train.seed|data.*|src.*|models.*'"]),
]


# ------------------------------------------------------------------- runner
def run(cmd: str) -> None:
    print(f"{G}$ {cmd}{R}")
    name, *args = cmd.split()
    if name in BUILTINS:
        BUILTINS[name](*[str(SANDBOX / a) for a in args])
        return
    if cmd.startswith("python "):
        cmd = f'"{PY}" ' + cmd[len("python "):]
    if sys.platform == "win32":
        cmd = cmd.replace("'", '"')
    res = subprocess.run(cmd, shell=True, cwd=SANDBOX)
    if res.returncode != 0:
        sys.exit(f"{Y}Command failed (exit {res.returncode}). Stopping.{R}")


def setup_sandbox() -> None:
    for p in (SANDBOX, STORAGE):
        if p.exists():
            _force_rmtree(p)
    SANDBOX.mkdir()
    for item in ("src", "params.yaml", "dvc.yaml", "requirements.txt"):
        src = REPO / item
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, SANDBOX / item)
    (SANDBOX / ".gitignore").write_text("__pycache__/\n.venv/\ndvc_plots/\n")
    subprocess.run("git init -q -b main", shell=True, cwd=SANDBOX, check=True)
    subprocess.run('git config user.name "DVC Demo"', shell=True, cwd=SANDBOX, check=True)
    subprocess.run('git config user.email "demo@example.com"', shell=True, cwd=SANDBOX, check=True)
    subprocess.run("git add -A", shell=True, cwd=SANDBOX, check=True)
    subprocess.run('git commit -q -m "Project code"', shell=True, cwd=SANDBOX, check=True)
    print(f"{D}Sandbox ready: {SANDBOX}{R}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true", help="don't pause between steps")
    ap.add_argument("--from", dest="start", type=int, default=1, help="first step to run")
    ap.add_argument("--setup", action="store_true",
                    help="only create a fresh sandbox, then type the commands yourself "
                         "(see docs/DEMO_SCRIPT.md)")
    a = ap.parse_args()

    if sys.platform == "win32":
        import os
        os.system("")  # enable ANSI colours in the Windows console

    if a.setup:
        setup_sandbox()
        print(f"\nNext:  cd {SANDBOX}\nthen follow docs/DEMO_SCRIPT.md")
        return

    if a.start == 1:
        setup_sandbox()
    elif not SANDBOX.exists():
        sys.exit("No sandbox yet - run from step 1 first.")

    for i, (title, why, cmds) in enumerate(STEPS, 1):
        if i < a.start:
            continue
        if i == 1:
            cmds = cmds[1:]  # sandbox already has a git repo
        print(f"\n{B}{C}[{i}/{len(STEPS)}] {title}{R}\n{D}{why}{R}")
        if not a.auto:
            try:
                input(f"{D}  (Enter to run, Ctrl+C to quit){R}")
            except KeyboardInterrupt:
                print()
                return
        for cmd in cmds:
            run(cmd)
    print(f"\n{B}{G}Demo complete.{R} Explore it yourself: cd {SANDBOX}")


if __name__ == "__main__":
    main()
