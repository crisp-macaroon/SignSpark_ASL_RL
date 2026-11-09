"""S-5: read-only verification of the frozen R0 space-R targets under the validity layer R v1.1.

How2Sign TRAIN references only (the same 29,630 clips, loader and settings as R0); no dev, no test, no generation,
no FK (space R only). For every clip: the four space-R signals (arm R, arm L, hand L, hand R) are checked against the
R v1.1 floors; the v1.1 statistics are compared with R0's stored v1 per-clip values (chunk files, unchanged).
The frozen targets (research/stage4/FROZEN_TARGETS_R0.json) are NOT recomputed, overwritten or retuned. If any stream
is invalid, only counts and clip names are reported; no replacement target is computed.

    python -E -s experiments/stage4/validity/s5_verify.py --out experiments/stage4/validity/out
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""
for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[_k] = "4"

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "r0"))
import validity as V  # noqa: E402
import r0_run as R0  # noqa: E402  (same dataset construction and LMDB path; nothing executed on import)

STATS = (("coord_arm_lhand", 0), ("coord_arm_rhand", 1), ("coord_lr", 2), ("X", 3))  # R0 chunk row columns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    chunks = [np.load(ROOT / "experiments/stage4/r0/out/chunks" / f"chunk_{ci:03d}.npz") for ci in range(60)]
    v1_rows = np.concatenate([c["rows"] for c in chunks])
    v1_names = np.concatenate([c["names"] for c in chunks])
    ds = R0.dataset()
    N = len(ds)
    assert N == len(v1_names) == 29630, (N, len(v1_names))
    invalid = {k: [] for k in ("arm_R", "arm_L", "hand_L", "hand_R")}
    nonfinite_input = []
    changed = {k: 0 for k, _ in STATS}
    maxdiff = {k: 0.0 for k, _ in STATS}
    minsig = {k: [np.inf, np.inf] for k in invalid}
    name_mismatch = 0
    for i in range(N):
        ff, Lf, _, _, name = ds[i]
        if str(name) != str(v1_names[i]):
            name_mismatch += 1
        f = ff.numpy().astype(np.float64)
        L = int(Lf)
        h, b = f[:, :180], f[:, 180:240]
        s = V.r_stats(b[:L].T, h[:L, :90].T, h[:L, 90:180].T, L)
        if not s["valid"].get("input_finite", True):
            nonfinite_input.append(str(name))
            continue
        for k in invalid:
            if not s["valid"][k]:
                invalid[k].append(str(name))
            m, sd = s["signal_stats"][k]
            minsig[k] = [min(minsig[k][0], m), min(minsig[k][1], sd)]
        for k, col in STATS:
            a, b1 = s[k], v1_rows[i, col]
            if np.isnan(a) != np.isnan(b1):
                changed[k] += 1
            elif np.isfinite(a):
                maxdiff[k] = max(maxdiff[k], abs(a - b1))
        if (i + 1) % 2500 == 0:
            print(f"[{time.time() - t0:5.0f}s] {i + 1}/{N}", flush=True)
    n_invalid_streams = sum(len(v) for v in invalid.values())
    res = {"label": "S-5: R0 space-R targets under R v1.1; train references only; read-only",
           "clips": N, "name_order_mismatches_vs_R0": name_mismatch, "nonfinite_input_clips": nonfinite_input,
           "invalid_streams_total": n_invalid_streams,
           "invalid_streams_by_signal": {k: len(v) for k, v in invalid.items()},
           "invalid_clip_names": {k: v[:50] for k, v in invalid.items()},
           "min_signal_mean_std_rad_per_frame": minsig,
           "floors": {"mean": V.R_MEAN_FLOOR, "std": V.R_STD_FLOOR},
           "v1_to_v1.1_definedness_changes": changed,
           "max_abs_diff_where_defined": maxdiff,
           "seconds": round(time.time() - t0)}
    res["conclusion"] = ("No invalid streams: the frozen space-R R0 targets remain valid under R v1.1 unchanged."
                         if n_invalid_streams == 0 and not nonfinite_input and all(v == 0 for v in changed.values())
                         and all(v == 0.0 for v in maxdiff.values()) and name_mismatch == 0
                         else "Invalid streams or differences found: see counts; replacement targets NOT computed (needs user approval).")
    (out / "s5_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "invalid_clip_names"}, indent=1))


if __name__ == "__main__":
    main()
