"""Sequential GPU runner for MS-T1..T4 and MS-E1..E4 (ACMS_MULTISEED_DESIGN.md §3-4). Unchanged Stage 5 code; one job at
a time; per-step stdout/stderr logs; wall-clock caps (training: the config's own 3,600 s cap; evaluation: 2,400 s,
killed and recorded as failed if exceeded). A failed step is recorded and NOT retried; the later steps of that seed are
skipped, other seeds continue.

  python -E -s experiments/stage5_multiseed/run_multiseed.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
S5 = ROOT / "experiments" / "stage5"
OUT = HERE / "out"
SEEDS = (7001, 7002, 7003, 7004)
EVAL_CAP = 2400


def run(name, cmd, cap, status):
    log = OUT / "logs"
    log.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    entry = {"name": name, "cmd": " ".join(str(c) for c in cmd), "start": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(log / f"{name}.out", "w", encoding="utf-8") as fo, open(log / f"{name}.err", "w", encoding="utf-8") as fe:
        try:
            p = subprocess.run([str(c) for c in cmd], cwd=ROOT, stdout=fo, stderr=fe, timeout=cap)
            entry["exit"] = p.returncode
        except subprocess.TimeoutExpired:
            entry["exit"] = "timeout"
    entry["seconds"] = round(time.time() - t0, 1)
    status.append(entry)
    (OUT / "runner_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
    print(entry, flush=True)
    return entry["exit"] == 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    status = []
    run("record_env", [PY, "-E", "-s", S5 / "record_env.py", "--out", OUT / "env", "--lmdb"], 900, status)
    for s in SEEDS:
        cfg = HERE / "configs" / f"config_500ep_s{s}.json"
        d = OUT / f"s{s}"
        if not run(f"train_s{s}", [PY, "-E", "-s", S5 / "train_500ep.py", "--config", cfg, "--out", d / "train"], 3900, status):
            continue
        run_json = json.loads((d / "train" / "run.json").read_text(encoding="utf-8"))
        if run_json["status"] != "completed" or not run_json["model_weights_unchanged"]:
            status.append({"name": f"train_s{s}", "note": "not completed / weights changed; eval skipped"})
            continue
        ck = d / "train" / "checkpoints"
        run(f"eval_s{s}", [PY, "-E", "-s", S5 / "evaluate.py", "--config", cfg, "--ckpt-init", ck / "update_000.pt",
                           "--ckpt-final", ck / "update_125.pt", "--out", d / "eval", "--save-dumps"], EVAL_CAP, status)
    (OUT / "runner_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
