"""Read-only analysis of EXISTING arrays (no generation, no model): how far real motion statistics sit above the
floating-point noise floor that produced the V-R3 spurious values, to ground the proposed R-space validity thresholds.

Inputs: E2e dumps (16 conditions, noises 1..8; generated, released checkpoint), dev-256 reference poses (clips 0..31).
Per stream (body arm = R_Elbow+R_Wrist, L hand, R hand): mean frame speed A/(L-1), std of the frame-speed signal,
and max frame speed (registered geodesic metric, e2e/metrics.py). Also the noise floor of a static non-identity pose.

    python -E -s experiments/stage4/speed_floor_analysis.py --out experiments/stage4/speed_floor_analysis.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2e"))
import metrics as M  # noqa: E402
import noise_transform as NT  # noqa: E402

DEV256 = {s: ROOT / f"experiments/baseline/runs/{s}/h2s_dev256_gf_s10_N8/debug0_eulerstepsize10_can8_anchor0_samples/seed102_clampstep0_h2s_dev256_gf_s10_N8.npy"
          for s in ("body", "hand")}


def stream_stats(x6, L, joints=None):
    w = M.joint_speed(M.to_mats(x6[:, :L]))
    s = w[:, joints].mean(1) if joints is not None else w.mean(1)
    return s.mean(), s.std(), s.max()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = json.loads((ROOT / "experiments/stage4/e2e/out/results.json").read_text(encoding="utf-8"))
    L = res["steps"]["0"]["ref32_lengths"]
    dumps = ROOT / "experiments/stage4/e2e/dumps"
    acc = {"generated": {k: [] for k in ("arm", "L", "R")}, "reference": {k: [] for k in ("arm", "L", "R")}}
    body = {k: np.load(dumps / "A0" / f"k{k:02d}.npz")["body"] for k in range(1, 9)}
    for c in NT.CONDITIONS:
        for k in range(1, 9):
            z = np.load(dumps / c["name"] / f"k{k:02d}.npz")
            b = z["body"] if "body" in z.files else body[k]
            for j in range(32):
                acc["generated"]["arm"].append(stream_stats(b[j], L[j], [7, 9]))
                acc["generated"]["L"].append(stream_stats(z["hand"][j, 0], L[j]))
                acc["generated"]["R"].append(stream_stats(z["hand"][j, 1], L[j]))
    db = np.load(DEV256["body"], allow_pickle=True).item()  # our own dumps (dict pickled by np.save)
    dh = np.load(DEV256["hand"], allow_pickle=True).item()
    Ld = db["lengths"][0]
    for j in range(256):
        acc["reference"]["arm"].append(stream_stats(db["gt_poses"][0, j], int(Ld[j]), [7, 9]))
        acc["reference"]["L"].append(stream_stats(dh["gt_poses"][0, 2 * j], int(Ld[j])))
        acc["reference"]["R"].append(stream_stats(dh["gt_poses"][0, 2 * j + 1], int(Ld[j])))
    out = {}
    for src, d in acc.items():
        out[src] = {}
        for k, v in d.items():
            a = np.array(v)
            out[src][k] = {"n": len(a), "min_mean_speed": float(a[:, 0].min()), "p01_mean_speed": float(np.percentile(a[:, 0], 1)),
                           "median_mean_speed": float(np.median(a[:, 0])), "min_speed_std": float(a[:, 1].min()),
                           "p01_speed_std": float(np.percentile(a[:, 1], 1)), "min_max_speed": float(a[:, 2].min())}
    # noise floor: static non-identity pose (normalised mean of the first reference frame perturbed off-orthonormal)
    rng = np.random.default_rng(0)
    floors = []
    for _ in range(50):
        six = rng.normal(size=(1, 90))
        x = np.repeat(six.T, 100, axis=1)  # static, non-orthonormal 6D
        _, sd, mx = stream_stats(x, 100)
        floors.append((mx, sd))
    f = np.array(floors)
    out["static_noise_floor"] = {"max_frame_speed_max": float(f[:, 0].max()), "speed_std_max": float(f[:, 1].max())}
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
