"""Synthetic validation of the proposed C-c3 typicality bounds. Pure N(0, 1) arrays only: no model, no dataset,
no generation, no campaign seeds. (1) Null coverage at the 32 E2e clip lengths (from the E2d record of clip
lengths, a list of integers). (2) Sensitivity to typical 'gaming' manipulations of noise.

    python -E -s experiments/stage4/e2c/validate_typicality.py --out experiments/stage4/e2c/typicality_validation.json
"""

import argparse
import json
from pathlib import Path

import numpy as np

import typicality as T

LENGTHS = [157, 56, 139, 171, 189, 99, 116, 263, 212, 67, 248, 84, 71, 177, 83, 85, 102, 47, 219, 120, 220, 71,
           159, 125, 304, 174, 132, 28, 304, 252, 78, 146]  # dev-256 clips 0..31 (E2d t0.json)
N_NULL, N_POW = 4000, 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rng = np.random.default_rng(424242)  # validation seed, unrelated to any campaign seed
    res = {"null": {}, "power": {}, "bounds": {}}
    for L in sorted(set(LENGTHS)):
        b = T.bounds(L)
        res["bounds"][L] = {k: float(v) for k, v in b.items()}
        x = rng.standard_normal((N_NULL, T.C, L), dtype=np.float32).astype(np.float64)
        s = T.stats(x)
        v = T.violations(s, b)
        res["null"][L] = {**{k: float(m.mean()) for k, m in v.items()},
                          "any": float(np.any(np.stack(list(v.values())), 0).mean())}
    per_clip = [res["null"][L]["any"] for L in LENGTHS]
    res["null_summary"] = {"per_hand_any_mean": float(np.mean(per_clip)), "per_hand_any_max": float(np.max(per_clip)),
                           "nominal_per_hand": sum(T.FAM.values()),
                           "expected_violating_hands_of_64": float(2 * np.sum(per_clip))}

    def ma(x, w):
        k = np.ones(w) / np.sqrt(w)
        return np.apply_along_axis(lambda r: np.convolve(r, k, mode="same"), -1, x)

    manip = {
        "AR(1) 0.15 all channels": lambda x: np.concatenate([x[..., :1], 0.15 * x[..., :-1] + np.sqrt(1 - 0.15 ** 2) * x[..., 1:]], -1),
        "AR(1) 0.5 on 10 channels": None,
        "moving average w=3 all channels (unit variance)": lambda x: ma(x, 3),
        "10 channels scaled x1.5": None,
        "10 channels offset +0.3": None,
    }
    for L in (56, 150, 304):
        b = T.bounds(L)
        out = {}
        for name, f in manip.items():
            x = rng.standard_normal((N_POW, T.C, L))
            if name == "AR(1) 0.5 on 10 channels":
                y = x.copy()
                for t in range(1, L):
                    y[:, :10, t] = 0.5 * y[:, :10, t - 1] + np.sqrt(0.75) * x[:, :10, t]
                x = y
            elif name == "10 channels scaled x1.5":
                x[:, :10] *= 1.5
            elif name == "10 channels offset +0.3":
                x[:, :10] += 0.3
            else:
                x = f(x)
            v = T.violations(T.stats(x), b)
            out[name] = {**{k: float(m.mean()) for k, m in v.items()}, "any": float(np.any(np.stack(list(v.values())), 0).mean())}
        res["power"][L] = out
    Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({"null_summary": res["null_summary"],
                      "null_by_L_any": {L: round(res["null"][L]["any"], 4) for L in (28, 56, 99, 157, 304)},
                      "bounds_L150_nearest": res["bounds"][146], "power": res["power"]}, indent=1))


if __name__ == "__main__":
    main()
