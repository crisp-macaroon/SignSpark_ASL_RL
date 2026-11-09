"""Unit tests for the Stage 6 analysis code (synthetic arrays only; no models, no data, no generation).

  python -E -s experiments/stage5_multiseed/tests/test_stage6.py
"""

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "experiments" / "stage6_gate"))
import pooled_analysis as PA  # noqa: E402
import preflight as PF  # noqa: E402
import fg1_analyse as FA  # noqa: E402
import fg1_run as FR  # noqa: E402

results = []


def check(name, cond):
    results.append({"test": name, "pass": bool(cond)})
    print(("PASS " if cond else "FAIL ") + name)


def run(per_means, per_ci, valid=True):
    return [{"seed": i, "missing": False, "valid_run": valid, "primary": {"mean": m, "ci95": list(c)}} for i, (m, c) in
            enumerate(zip(per_means, per_ci))]


# t-interval
t = PA.tint([1.0, 2.0, 3.0, 4.0])
check("tint mean/sd", abs(t["mean"] - 2.5) < 1e-12 and abs(t["sd"] - np.std([1, 2, 3, 4], ddof=1)) < 1e-12)
check("tint half-width uses t(0.975, 3)", abs((t["ci95"][1] - t["mean"]) - 3.182446 * t["sd"] / 2) < 1e-5)
# heterogeneity
h = PA.heterogeneity([0.002] * 4, [0.0004] * 4)
check("heterogeneity identical -> Q = 0, I2 = 0", h["Q"] == 0 and h["I2"] == 0 and abs(h["p"] - 1) < 1e-12)
h2 = PA.heterogeneity([0.0, 0.01, 0.0, 0.01], [0.0004] * 4)
check("heterogeneity spread -> p < 0.05", h2["p"] < 0.05)
# category rule (§5.3)
ci = [(0.001, 0.003)] * 4
pos = run([0.002, 0.0021, 0.0019, 0.002], ci)
check("category reproducible positive", PA.category(pos, PA.tint([r["primary"]["mean"] for r in pos]),
                                                    PA.heterogeneity([0.002, 0.0021, 0.0019, 0.002], [0.0005] * 4)) == "reproducible positive")
neg = run([-0.001, 0.0, -0.002, 0.0005], ci)
check("category negative", PA.category(neg, PA.tint([-0.001, 0.0, -0.002, 0.0005]), PA.heterogeneity([-0.001, 0.0, -0.002, 0.0005], [0.0005] * 4)) == "negative")
inv = run([0.002] * 4, ci, valid=False)
check("category inconclusive (validity) first", PA.category(inv, PA.tint([0.002] * 4), PA.heterogeneity([0.002] * 4, [0.0005] * 4)) == "inconclusive (validity)")
mix = run([0.004, -0.002, 0.003, 0.001], [(0.003, 0.005), (-0.003, -0.001), (0.002, 0.004), (0.0, 0.002)])
check("category seed-sensitive (opposite-sign individual CIs)",
      PA.category(mix, PA.tint([0.004, -0.002, 0.003, 0.001]), PA.heterogeneity([0.004, -0.002, 0.003, 0.001], [0.0005] * 4)) == "seed-sensitive")
imp = run([0.002, 0.0, 0.001, 0.0005], [(-0.01, 0.014), (-0.012, 0.012), (-0.011, 0.013), (-0.0115, 0.0125)])
check("category inconclusive (precision)",
      PA.category(imp, PA.tint([0.002, 0.0, 0.001, 0.0005]), PA.heterogeneity([0.002, 0.0, 0.001, 0.0005], [0.006] * 4)) == "inconclusive (precision)")
# FG-1 outcome rule
check("FG-1 positive needs CI > 0 and point >= 0.05", FA.outcome({"mean": 0.06, "ci95": [0.01, 0.11]}, True) == "positive")
check("FG-1 positive blocked by preservation", FA.outcome({"mean": 0.06, "ci95": [0.01, 0.11]}, False) == "inconclusive")
check("FG-1 negative when CI upper < 0.05", FA.outcome({"mean": 0.01, "ci95": [-0.01, 0.04]}, True) == "negative")
check("FG-1 inconclusive when CI straddles 0.05", FA.outcome({"mean": 0.03, "ci95": [0.0, 0.07]}, True) == "inconclusive")
check("FG-1 point < 0.05 with CI > 0 and upper >= 0.05 is inconclusive", FA.outcome({"mean": 0.045, "ci95": [0.02, 0.07]}, True) == "inconclusive")
# preflight configs
for s in PF.SEEDS:
    c = PF.seed_config(s)
    ref = PF.flat(json.loads(PF.REF_CFG.read_text(encoding="utf-8-sig")))
    f = PF.flat(c)
    diff = {k for k in set(ref) | set(f) if ref.get(k) != f.get(k)}
    check(f"preflight config s{s} differs only in allowed fields", diff <= PF.ALLOWED_DIFF and "policy.init_seed" in diff)
rr = PF.ranges({s: PF.seed_config(s) for s in PF.SEEDS} | {7000: json.loads(PF.REF_CFG.read_text(encoding="utf-8-sig"))})
check("preflight noise ranges pairwise disjoint",
      not [(a, b) for i, (a, l1, h1) in enumerate(rr) for (b, l2, h2) in rr[i + 1:] if l1 <= h2 and l2 <= h1])
# left-arm feature: z-scored, zero beyond L; invalid input -> zeros + flag
rng = np.random.default_rng(0)
T, L = 304, 120
ang = np.cumsum(rng.normal(0, 0.05, (T, 10, 3)), 0)
mats = []
for t_ in range(T):
    row = []
    for j in range(10):
        a, b, c = ang[t_, j]
        Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
        R = Rz @ Rx
        row.append(np.concatenate([R[:, 0], R[:, 1]]))
    mats.append(np.concatenate(row))
xb = np.array(mats, np.float32).T  # (60, T)
f, ok = FR.left_arm_feature(xb, L)
check("left arm feature valid, z-scored over L", ok and abs(f[:L].mean()) < 1e-5 and abs(f[:L].std() - 1) < 1e-4 and not f[L:].any())
bad = xb.copy()
bad[0, 3] = np.nan
fb, okb = FR.left_arm_feature(bad, L)
check("left arm feature non-finite -> zeros + invalid", (not okb) and not fb.any())
out = HERE / "out"
out.mkdir(exist_ok=True)
(out / "test_stage6.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
n_pass = sum(r["pass"] for r in results)
print(f"{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
