"""Read-only pre-execution integrity check for the E2e-J run and the R0 resume (2026-11-03 authorisation).
Writes a manifest of SHA-256 hashes; modifies nothing else.

    python -E -s experiments/stage4/verify_resume.py
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2e"))
import noise_transform as NT  # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rep = {"e2e_dumps": {}, "r0": {}, "issues": []}
dumps = ROOT / "experiments/stage4/e2e/dumps"
res = json.loads((ROOT / "experiments/stage4/e2e/out/results.json").read_text(encoding="utf-8"))
nstar = res["steps"]["2_3"]["n_star"]
for c in NT.CONDITIONS:
    n = c["name"]
    want = nstar if (c["kind"] == "base" or n in NT.GATE) else 8
    files = sorted((dumps / n).glob("k*.npz"))
    ks = sorted(int(f.stem[1:]) for f in files)
    ok = ks == list(range(1, want + 1))
    shapes_ok, finite = True, True
    for f in files:
        z = np.load(f)
        shapes_ok &= z["hand"].shape == (32, 2, 90, 304) and (("body" not in z.files) or z["body"].shape == (32, 60, 304))
        finite &= bool(np.isfinite(z["hand"]).all()) and (("body" not in z.files) or bool(np.isfinite(z["body"]).all()))
        if c["kind"] == "base" and "body" not in z.files:
            shapes_ok = False
    rep["e2e_dumps"][n] = {"k_present": f"{ks[0]}..{ks[-1]}" if ks else "none", "expected": f"1..{want}", "complete": ok,
                           "shapes_ok": shapes_ok, "finite": finite,
                           "sha256_k01_to_k08": [sha(dumps / n / f"k{k:02d}.npz") for k in range(1, 9)]}
    if not (ok and shapes_ok and finite):
        rep["issues"].append(f"dump problem: {n}")
rep["e2e_results_sha256"] = sha(ROOT / "experiments/stage4/e2e/out/results.json")
rep["e2e_status"] = res["status"]

r0 = ROOT / "experiments/stage4/r0/out/chunks"
chunks = sorted(r0.glob("chunk_*.npz"))
idx = [int(p.stem.split("_")[1]) for p in chunks]
rep["r0"]["chunk_indices"] = f"{min(idx)}..{max(idx)}" if idx else "none"
rep["r0"]["n_chunks"] = len(chunks)
rep["r0"]["contiguous_0_to_29"] = idx == list(range(30))
rows, run_time, bad = 0, 0.0, []
for p in chunks:
    z = np.load(p)
    nr = z["rows"].shape[0]
    rows += nr
    run_time += float(z["seconds"])
    if z["rows"].shape[1] != 9 or nr + int(z["excluded"]) != 500 or not np.isfinite(z["rows"][:, -1]).all():
        bad.append(p.name)
rep["r0"]["clips_done"] = rows
rep["r0"]["bad_chunks"] = bad
rep["r0"]["run_time_min_so_far"] = round(run_time / 60, 1)
rep["r0"]["next_chunk_index_0based"] = 30
rep["r0"]["next_chunk_human"] = "chunk 31 of 60"
rep["r0"]["chunk_sha256"] = {p.name: sha(p) for p in chunks}
rep["r0"]["stop_file_present"] = (ROOT / "experiments/stage4/r0/STOP").exists()
rep["code_sha256"] = {p: sha(ROOT / p) for p in ("experiments/stage4/r0/r0_run.py", "experiments/stage4/e2e_j/e2ej_run.py",
                                                  "experiments/stage4/jspace.py", "experiments/stage4/e2e/metrics.py",
                                                  "experiments/stage4/e2e/stats.py")}
if bad or not rep["r0"]["contiguous_0_to_29"]:
    rep["issues"].append("R0 checkpoint problem")
out = ROOT / "experiments/stage4/resume_manifest_2026-11-03.json"
out.write_text(json.dumps(rep, indent=1), encoding="utf-8")
print(json.dumps({k: (v if k != "e2e_dumps" else {n: {kk: vv for kk, vv in d.items() if kk != "sha256_k01_to_k08"}
                                                    for n, d in v.items()}) for k, v in rep.items() if k != "code_sha256"
                  and not (k == "r0")}, indent=1))
print(json.dumps({k: v for k, v in rep["r0"].items() if k != "chunk_sha256"}, indent=1))
print("issues:", rep["issues"])
