"""Step-by-step DVC demo.

Usage:
    python demo/run_demo.py            press Enter before each step
    python demo/run_demo.py --auto     run all steps without stopping
    python demo/run_demo.py --from 5   start from a later step
    python demo/run_demo.py --setup    only create the sandbox

Everything runs in ../dvc-demo-sandbox, and ../dvc-demo-storage is used
as the DVC remote, so this repo itself is never changed.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SANDBOX = REPO.parent / "dvc-demo-sandbox"
STORAGE = REPO.parent / "dvc-demo-storage"

BOLD, CYAN, GREEN, GREY, YELLOW, RESET = (
    "\033[1m", "\033[36m", "\033[32m", "\033[2m", "\033[33m", "\033[0m")


def rel(path):
    return Path(path).relative_to(SANDBOX).as_posix()


def rmtree(path):
    # dvc makes cached files read-only, which Windows won't delete otherwise
    def on_error(func, p, _):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onerror=on_error)


# small replacements for cat/rm/du/wc so the demo also works on Windows
def cat(path):
    print(Path(path).read_text().rstrip())


def rows(path):
    with open(path) as f:
        print(f"{rel(path)}: {sum(1 for _ in f) - 1} rows")


def rm(*paths):
    for p in map(Path, paths):
        if p.is_dir():
            rmtree(p)
        elif p.exists():
            p.chmod(0o600)
            p.unlink()
    print("deleted:", " ".join(rel(p) for p in paths))


def du(path):
    files = [f for f in Path(path).rglob("*") if f.is_file()]
    size = sum(f.stat().st_size for f in files) / 1024
    print(f"{rel(path)}: {len(files)} files, {size:.0f} KB")


HELPERS = {"cat": cat, "rows": rows, "rm": rm, "du": du}


STEPS = [
    ("Set up DVC",
     "dvc init adds a small .dvc/ folder to the git repo.",
     ["dvc init -q",
      "git commit -q -m 'Initialize DVC'"]),

    ("Add remote storage",
     "This is where DVC uploads data. Here it's a local folder instead of S3 or Drive.",
     ["dvc remote add -d storage ../dvc-demo-storage",
      "dvc config core.autostage true",
      "cat .dvc/config",
      "git commit -q -am 'Add DVC remote'"]),

    ("Track data v1",
     "dvc add moves the data into the cache. Git only gets the small .dvc file.",
     ["python src/make_dataset.py --version 1",
      "dvc add data/raw/data.csv",
      "cat data/raw/data.csv.dvc",
      "git status --short",
      "git commit -q -m 'Data v1: 150 rows'"]),

    ("Run the pipeline",
     "dvc repro runs prepare -> train -> evaluate and saves the hashes in dvc.lock.",
     ["dvc dag",
      "dvc repro",
      "dvc metrics show",
      "git add -A",
      "git commit -q -m 'Model trained on data v1'",
      "git tag v1.0",
      "dvc push"]),

    ("Data v2 arrives",
     "DVC sees the data changed. For git it's just a new hash.",
     ["python src/make_dataset.py --version 2",
      "dvc status",
      "dvc add data/raw/data.csv",
      "git diff --cached data/raw/data.csv.dvc"]),

    ("Retrain and compare",
     "Same code, new data.",
     ["dvc repro",
      "git add -A",
      "git commit -q -m 'Data v2: 569 rows, retrained'",
      "git tag v2.0",
      "dvc push",
      "dvc metrics diff v1.0 v2.0"]),

    ("Run again with no changes",
     "Nothing changed, so every stage is skipped.",
     ["dvc repro"]),

    ("Go back to v1.0",
     "git checkout brings back the old .dvc files, dvc checkout brings back the matching data.",
     ["git checkout -q v1.0",
      "dvc checkout",
      "rows data/raw/data.csv",
      "cat metrics.json",
      "git checkout -q main",
      "dvc checkout",
      "rows data/raw/data.csv"]),

    ("Restore from storage",
     "Delete the data and the cache, then get everything back with dvc pull.",
     ["du .dvc/cache",
      "rm .dvc/cache data/raw/data.csv models",
      "dvc pull",
      "rows data/raw/data.csv",
      "dvc status"]),

    ("Experiments",
     "Try other parameters without committing.",
     ["dvc exp run -S train.n_estimators=10 -S train.max_depth=2",
      "dvc exp show --no-pager --md --drop 'Created|State|Executor|prepare.*|train.seed|data.*|src.*|models.*'"]),
]


def run(cmd):
    print(f"{GREEN}$ {cmd}{RESET}")
    name, *args = cmd.split()
    if name in HELPERS:
        HELPERS[name](*[str(SANDBOX / a) for a in args])
        return
    if cmd.startswith("python "):
        cmd = f'"{sys.executable}" ' + cmd[len("python "):]
    if sys.platform == "win32":
        cmd = cmd.replace("'", '"')
    result = subprocess.run(cmd, shell=True, cwd=SANDBOX)
    if result.returncode != 0:
        sys.exit(f"{YELLOW}Command failed, stopping.{RESET}")


def git(cmd):
    subprocess.run(f"git {cmd}", shell=True, cwd=SANDBOX, check=True)


def setup():
    for folder in (SANDBOX, STORAGE):
        if folder.exists():
            rmtree(folder)
    SANDBOX.mkdir()
    for name in ("src", "params.yaml", "dvc.yaml", "requirements.txt"):
        src = REPO / name
        if src.is_dir():
            shutil.copytree(src, SANDBOX / name)
        else:
            shutil.copy2(src, SANDBOX / name)
    (SANDBOX / ".gitignore").write_text("__pycache__/\n.venv/\ndvc_plots/\n")
    git("init -q -b main")
    git('config user.name "DVC Demo"')
    git('config user.email "demo@example.com"')
    git("add -A")
    git('commit -q -m "Project code"')
    print(f"{GREY}Sandbox ready: {SANDBOX}{RESET}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--from", dest="start", type=int, default=1)
    parser.add_argument("--setup", action="store_true")
    args = parser.parse_args()

    if sys.platform == "win32":
        os.system("")  # turns on colours in the Windows terminal

    if args.setup:
        setup()
        print(f"\nNext: cd {SANDBOX}")
        return

    if args.start == 1:
        setup()
    elif not SANDBOX.exists():
        sys.exit("Run the demo from step 1 first.")

    for i, (title, note, cmds) in enumerate(STEPS, 1):
        if i < args.start:
            continue
        print(f"\n{BOLD}{CYAN}[{i}/{len(STEPS)}] {title}{RESET}\n{GREY}{note}{RESET}")
        if not args.auto:
            try:
                input(f"{GREY}  press Enter{RESET}")
            except KeyboardInterrupt:
                print()
                return
        for cmd in cmds:
            run(cmd)

    print(f"\n{BOLD}{GREEN}Done.{RESET}")


if __name__ == "__main__":
    main()
