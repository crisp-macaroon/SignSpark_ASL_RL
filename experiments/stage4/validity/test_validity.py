"""Unit tests for the validity layer (R v1.1, J v1.1) on SYNTHETIC poses only (SMPL-X FK for the J tests; no
SignSparK model, no dataset, no generation).

    python -E -s experiments/stage4/validity/test_validity.py --out experiments/stage4/validity/out/unit_tests.json
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "e2e"))
import metrics as MR  # noqa: E402
import validity as V  # noqa: E402

ROOT = HERE.parents[2]
rng = np.random.default_rng(2026)
R = {}


def check(name, ok, info=""):
    R[name] = {"pass": bool(ok), "info": info}
    print(("PASS " if ok else "FAIL ") + name + (f"  {info}" if info else ""), flush=True)


def six_from_rotvec(rv):
    M = Rotation.from_rotvec(rv.reshape(-1, 3)).as_matrix()
    return np.concatenate([M[:, 0, :], M[:, 1, :]], axis=-1)  # rows b1, b2 (upstream rot6d convention)


def seq(J, T, step):
    """Random-walk rotations: (J*6, T) 6D, per-frame step size `step` rad (0 = static identity)."""
    rv = np.cumsum(rng.normal(0, step, (T, J, 3)), axis=0) if step > 0 else np.zeros((T, J, 3))
    return np.stack([six_from_rotvec(rv[t]).reshape(-1) for t in range(T)], axis=1)


def same(a, b):
    return (np.isnan(a) and np.isnan(b)) or a == b


T = L = 120
body_mv, lh_mv, rh_mv = seq(10, T, 0.05), seq(15, T, 0.05), seq(15, T, 0.05)

# ---------------------------------------------------------------- space R
# 1. ordinary motion: v1.1 == v1 exactly
v1 = MR.sample_record(body_mv, lh_mv, rh_mv, L)
v11 = V.r_stats(body_mv, lh_mv, rh_mv, L)
check("R ordinary motion: v1.1 equals v1 exactly (4 statistics)",
      all(same(v1[a], v11[b]) for a, b in (("coord_arm_rhand",) * 2, ("coord_arm_lhand",) * 2, ("coord_lr",) * 2, ("X", "X")))
      and all(v11["valid"].values()), str({k: round(v11[k], 4) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")}))

# 2. static identity: v1 raises; v1.1 all NaN, no exception
st = seq(10, T, 0), seq(15, T, 0), seq(15, T, 0)
try:
    MR.sample_record(*st, L)
    v1_raised = False
except ZeroDivisionError:
    v1_raised = True
s = V.r_stats(*st, L)
check("R static identity: v1 raises ZeroDivisionError (documented); v1.1 returns all NaN",
      v1_raised and all(np.isnan(s[k]) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")))

# 3. static non-identity (non-orthonormal 6D tiled): v1 spurious finite values; v1.1 NaN
nb, nl, nr = (np.repeat(rng.normal(size=(c, 1)), T, axis=1) for c in (60, 90, 90))
try:
    sp = MR.sample_record(nb, nl, nr, L)
    spurious = [k for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X") if np.isfinite(sp[k])]
except ZeroDivisionError:
    spurious = ["raised"]
s = V.r_stats(nb, nl, nr, L)
check("R static non-identity: v1.1 all NaN (v1 gave finite spurious values or raised)",
      all(np.isnan(s[k]) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")) and not any(s["valid"][k] for k in ("hand_L", "hand_R")),
      f"v1 finite spurious: {spurious}; v1.1 signal stats {s['signal_stats']['hand_L']}")

# 4. frozen left hand, everything else moving
s = V.r_stats(body_mv, seq(15, T, 0), rh_mv, L)
check("R frozen left hand: left-hand statistics and dom NaN; right arm-hand defined and = v1",
      np.isnan(s["coord_arm_lhand"]) and np.isnan(s["coord_lr"]) and np.isnan(s["X"])
      and same(s["coord_arm_rhand"], MR.sample_record(body_mv, lh_mv, rh_mv, L)["coord_arm_rhand"]))

# 5. near-static motion below and above the floors
tiny = seq(15, T, 1e-7)
s = V.r_stats(body_mv, tiny, rh_mv, L)
check("R near-static hand (steps 1e-7 rad): invalid (mean speed < 1e-5)", not s["valid"]["hand_L"] and np.isnan(s["X"]),
      f"mean, std = {s['signal_stats']['hand_L']}")
small = seq(15, T, 1e-3)
s = V.r_stats(body_mv, small, rh_mv, L)
check("R slow but real hand (steps 1e-3 rad): valid, all statistics defined", s["valid"]["hand_L"] and np.isfinite(s["X"]),
      f"mean, std = {s['signal_stats']['hand_L']}")

# 6. non-finite input
bad = lh_mv.copy(); bad[3, 10] = np.nan
s = V.r_stats(body_mv, bad, rh_mv, L)
check("R non-finite input: no exception, all NaN, input_finite False",
      all(np.isnan(s[k]) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")) and s["valid"]["input_finite"] is False)
bad = rh_mv.copy(); bad[0, 0] = np.inf
s = V.r_stats(body_mv, lh_mv, bad, L)
check("R +inf input: all NaN", all(np.isnan(s[k]) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")))

# 7. never a finite replacement: every undefined value is NaN (checked across the cases above implicitly) + floors exact
check("R floor constants as specified", V.R_MEAN_FLOOR == 1e-5 and V.R_STD_FLOOR == 1e-6 and V.J_STD_FLOOR == 1e-7)

# ---------------------------------------------------------------- space J (pure signal-level)
ok_sig = {k: rng.random(119) * 0.01 + 0.005 for k in ("arm_L", "arm_R", "hand_L", "hand_R")}
s = V.j_from_signals(ok_sig)
check("J ordinary signals: all statistics defined", all(np.isfinite(s[k]) for k in ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")))
lowstd = dict(ok_sig, hand_L=np.full(119, 0.01) + rng.normal(0, 5e-8, 119))
s = V.j_from_signals(lowstd)
check("J hand signal std < 1e-7 m/frame: invalid; dependent statistics NaN",
      not s["valid"]["hand_L"] and np.isnan(s["coord_ah_J_L"]) and np.isnan(s["coord_lr_J"]) and np.isnan(s["dom_J"]))
zero = dict(ok_sig, hand_R=np.zeros(119))
s = V.j_from_signals(zero)
check("J zero-activity hand: dom NaN, no exception", np.isnan(s["dom_J"]) and np.isnan(s["coord_ah_J_R"]))
nf = dict(ok_sig, arm_L=np.r_[np.nan, ok_sig["arm_L"][1:]])
s = V.j_from_signals(nf)
check("J non-finite signal: invalid, NaN", not s["valid"]["arm_L"] and np.isnan(s["coord_ah_J_L"]))
check("J FK failure (None): all NaN", all(np.isnan(V.j_from_signals(None)[k]) for k in ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")))

# ---------------------------------------------------------------- space J with SMPL-X FK (synthetic poses)
import jspace as JS  # noqa: E402

ctx = JS.load_model()
v1j = JS.jstats(ctx, body_mv.T, lh_mv.T, rh_mv.T)
v11j = V.j_stats(ctx, body_mv.T, lh_mv.T, rh_mv.T)
check("J (FK) ordinary motion: v1.1 equals jspace v1 exactly",
      all(same(v1j[k], v11j[k]) for k in ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")))
s = V.j_stats(ctx, seq(10, T, 0).T, seq(15, T, 0).T, seq(15, T, 0).T)
check("J (FK) static identity: all NaN", all(np.isnan(s[k]) for k in ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")))
# Run-1 expectation error (kept in out/unit_tests_run1.json): a static hand POSE under a MOVING arm is not static in
# space J. SMPL-X hand joints / fingertips are regressed from skinned vertices, so forearm motion leaks a small
# non-rigid motion into the wrist-local hand signal (~5.6e-5 m/frame, std 2.3e-5; ~2% of a moving hand). The J v1.1
# floor targets numerical noise, not "frozen pose" semantics, so these J statistics are correctly DEFINED.
s = V.j_stats(ctx, body_mv.T, seq(15, T, 0).T, rh_mv.T)
check("J (FK) static left-hand pose, moving arm: defined (skinning leakage, documented); right arm-hand = v1",
      s["valid"]["hand_L"] and np.isfinite(s["coord_ah_J_L"]) and same(s["coord_ah_J_R"], v1j["coord_ah_J_R"]),
      f"leakage signal hand_L valid={s['valid']['hand_L']}")
s = V.j_stats(ctx, seq(10, T, 0).T, seq(15, T, 0).T, rh_mv.T)
check("J (FK) frozen left hand with static body: left statistics, L-R and dom NaN; right hand defined",
      np.isnan(s["coord_ah_J_L"]) and np.isnan(s["coord_lr_J"]) and np.isnan(s["dom_J"]) and not s["valid"]["hand_L"])
bad = lh_mv.T.copy(); bad[4, 2] = np.nan
check("J (FK) non-finite input: all NaN without FK", all(np.isnan(V.j_stats(ctx, body_mv.T, bad, rh_mv.T)[k]) for k in ("coord_ah_J_L", "dom_J")))

# ---------------------------------------------------------------- v1 code unchanged
man = json.loads((ROOT / "experiments/stage4/resume_manifest_2026-11-03.json").read_text(encoding="utf-8"))["code_sha256"]
for p in ("experiments/stage4/e2e/metrics.py", "experiments/stage4/jspace.py"):
    h = hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    check(f"v1 unchanged: {p}", h == man[p])

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
args = ap.parse_args()
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps({"results": R, "passed": sum(v["pass"] for v in R.values()), "total": len(R)}, indent=1),
                          encoding="utf-8")
print(f"\n{sum(v['pass'] for v in R.values())}/{len(R)} tests passed")
sys.exit(0 if all(v["pass"] for v in R.values()) else 1)
