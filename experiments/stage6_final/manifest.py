"""Closure: experiment manifest (every new output file with SHA-256 and size; every executed job with command, exit,
runtime), SignSparK checkpoint integrity, Stage 4 / Stage 5 immutability re-verification against the preflight
snapshot, and the final bundle (zip) of report, presentation, figures, source code and experiment outputs.
Large binary sample dumps (> 50 MB) are listed with hashes in the manifest but not copied into the zip.

  python -E -s experiments/stage6_final/manifest.py [--bundle]
"""

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NEW_DIRS = ["experiments/stage5_multiseed", "experiments/stage6_gate", "experiments/stage6_final", "research/stage6_proposal",
            "research/stage6_gate", "research/final"]
CKPT = {"models/SignSparK/body/ema_0.9999_200000.pt": "bf95bb02802b1c46f40afb4424f8f521be6c8641ad8acfe406a666b463e3a380",
        "models/SignSparK/hand/ema_0.9999_200000.pt": "5bb8e407ba2c106a22c3b0c16fd1b0fc0f412a58d235143325fdb67efe5916c2"}
SOURCE_DIRS = ["experiments/stage5", "experiments/stage4", "experiments/mc_reward", "experiments/stage5_multiseed",
               "experiments/stage6_gate", "experiments/stage6_final", "experiments/common"]
BIG = 50 * 2**20


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", action="store_true")
    a = ap.parse_args()
    files = {}
    for d in NEW_DIRS:
        for f in sorted((ROOT / d).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and "final_bundle" not in f.parts:
                files[rel(f)] = {"sha256": sha(f), "bytes": f.stat().st_size}
    jobs = []
    for st in ("experiments/stage5_multiseed/out/runner_status.json", "experiments/stage6_gate/out/runner_status.json"):
        p = ROOT / st
        if p.exists():
            jobs += json.loads(p.read_text(encoding="utf-8"))
    ck = {p: {"expected": h, "actual": sha(ROOT / p)} for p, h in CKPT.items()}
    for v in ck.values():
        v["match"] = v["expected"] == v["actual"]
    snap = json.loads((ROOT / "experiments/stage5_multiseed/out/reference_snapshot.json").read_text(encoding="utf-8"))["files"]
    changed = [p for p, h in snap.items() if not (ROOT / p).exists() or sha(ROOT / p) != h]
    man = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "label": "released-checkpoint results, not a paper reproduction",
           "signspark_checkpoints": ck, "stage4_stage5_immutability": {"files_checked": len(snap), "changed_or_missing": changed,
                                                                         "pass": not changed},
           "jobs": jobs, "new_files": files}
    out = ROOT / "research" / "final"
    out.mkdir(parents=True, exist_ok=True)
    (out / "EXPERIMENT_MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    lines = ["# Experiment manifest", "", f"*Generated {man['generated']}. Released-checkpoint results, not a paper reproduction.*", "",
             "## Integrity", "", "| Check | Result |", "|---|---|"]
    for p, v in ck.items():
        lines.append(f"| {p} | {'match' if v['match'] else 'MISMATCH'} ({v['actual'][:12]}…) |")
    lines.append(f"| Stage 4 / Stage 5 artifacts unchanged ({len(snap)} files) | {'pass' if not changed else 'FAIL: ' + ', '.join(changed[:10])} |")
    lines += ["", "## Executed jobs", "", "| Job | Exit | Seconds | Command |", "|---|---|---|---|"]
    for j in jobs:
        lines.append(f"| {j.get('name')} | {j.get('exit', j.get('note', ''))} | {j.get('seconds', '')} | `{j.get('cmd', '')}` |")
    lines += ["", "## New files", "", f"{len(files)} files; full SHA-256 list in `EXPERIMENT_MANIFEST.json`.", ""]
    (out / "EXPERIMENT_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")
    print("checkpoints", {p: v["match"] for p, v in ck.items()}, "immutability", not changed, "files", len(files), "jobs", len(jobs))
    if a.bundle:
        bdir = ROOT / "final_bundle"
        bdir.mkdir(exist_ok=True)
        zp = bdir / "SignSparK_RL_final_bundle.zip"
        skipped = []
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for d in ["research"] + SOURCE_DIRS:
                for f in sorted((ROOT / d).rglob("*")):
                    if not f.is_file() or "__pycache__" in f.parts:
                        continue
                    if f.stat().st_size > BIG or "dumps" in f.parts:
                        skipped.append({"path": rel(f), "bytes": f.stat().st_size, "sha256": sha(f)})
                        continue
                    z.write(f, rel(f))
            z.writestr("BUNDLE_EXCLUDED_LARGE_FILES.json", json.dumps(skipped, indent=1))
        print("bundle", zp, round(zp.stat().st_size / 2**20, 1), "MB; large files excluded:", len(skipped))


if __name__ == "__main__":
    main()
