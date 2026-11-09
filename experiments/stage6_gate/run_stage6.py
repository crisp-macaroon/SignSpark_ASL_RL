"""Sequential GPU runner after the multi-seed jobs: FG-1 smoke test -> FG-1 (prep, V2, V1, V3) -> OPT-G (5 runs) ->
OPT-C (5 runs x updates 25/50/75/100, R only). One job at a time; per-step logs; failures recorded, never retried.
If any smoke-test phase fails, the full FG-1 is skipped (reported) and the OPT jobs still run.

  python -E -s experiments/stage6_gate/run_stage6.py [--only fg1|optg|optc]
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
S5 = ROOT / "experiments" / "stage5"
MS = ROOT / "experiments" / "stage5_multiseed"
OUT = HERE / "out"
RUNS = (7000, 7001, 7002, 7003, 7004)
UPDATES = (25, 50, 75, 100)


def run_dirs(s):
    if s == 7000:  # reference run: read-only inputs, new outputs under stage5_multiseed/out/s7000
        return S5 / "config_500ep.json", S5 / "out" / "train", MS / "out" / "s7000"
    return MS / "configs" / f"config_500ep_s{s}.json", MS / "out" / f"s{s}" / "train", MS / "out" / f"s{s}"


def run(name, cmd, cap, status):
    log = OUT / "logs"
    log.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    entry = {"name": name, "cmd": " ".join(str(c) for c in cmd), "start": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(log / f"{name}.out", "w", encoding="utf-8") as fo, open(log / f"{name}.err", "w", encoding="utf-8") as fe:
        try:
            entry["exit"] = subprocess.run([str(c) for c in cmd], cwd=ROOT, stdout=fo, stderr=fe, timeout=cap).returncode
        except subprocess.TimeoutExpired:
            entry["exit"] = "timeout"
    entry["seconds"] = round(time.time() - t0, 1)
    status.append(entry)
    (OUT / "runner_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
    print(entry, flush=True)
    return entry["exit"] == 0


def phase_ok(path):
    return path.exists() and json.loads(path.read_text(encoding="utf-8")).get("status") == "completed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["fg1", "optg", "optc"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    status = []
    fg = HERE / "fg1_run.py"
    if a.only in (None, "fg1"):
        (HERE / "out_test").mkdir(exist_ok=True)
        shutil.copy(OUT / "gate_clips.json", HERE / "out_test" / "gate_clips.json")
        smoke = all(run(f"fg1_test_{p}", [PY, "-E", "-s", fg, "--phase", p, "--test"], 1800, status)
                    and phase_ok(HERE / "out_test" / f"run_{p}.json") for p in ("prep", "V2", "V1", "V3"))
        if smoke:
            for p, cap in (("prep", 2400), ("V2", 75 * 60 + 600), ("V1", 75 * 60 + 600), ("V3", 120 * 60 + 600)):
                if not run(f"fg1_{p}", [PY, "-E", "-s", fg, "--phase", p], cap, status) and p == "prep":
                    break
        else:
            status.append({"name": "fg1", "note": "smoke test failed; full FG-1 skipped"})
    if a.only in (None, "optg"):
        for s in RUNS:
            cfg, tdir, od = run_dirs(s)
            run(f"optg_s{s}", [PY, "-E", "-s", MS / "evaluate_train.py", "--config", cfg, "--train-dir", tdir,
                               "--out", od / "optg"], 2400, status)
    if a.only in (None, "optc"):
        for s in RUNS:
            cfg, tdir, od = run_dirs(s)
            ck = tdir / "checkpoints"
            for u in UPDATES:
                run(f"optc_s{s}_u{u:03d}", [PY, "-E", "-s", S5 / "evaluate.py", "--config", cfg, "--ckpt-init", ck / "update_000.pt",
                                            "--ckpt-final", ck / f"update_{u:03d}.pt", "--out", od / "optc" / f"u{u:03d}", "--no-j"],
                    2400, status)
    (OUT / "runner_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
