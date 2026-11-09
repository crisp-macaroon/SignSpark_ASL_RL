"""Preflight self-test for the E2e code on SYNTHETIC arrays only: no model, no dataset, no generation,
no E2e seeds. Checks that the transforms, metrics and statistics behave as specified.

    python -E -s experiments/stage4/e2e/selftest.py
"""

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402
import noise_transform as NT  # noqa: E402
import stats as S  # noqa: E402

rng = np.random.default_rng(12345)  # self-test seeds (unrelated to the E2e seeds)
torch.manual_seed(12345)
results = {}


def check(name, ok, info=""):
    results[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  {info}" if info else ""), flush=True)


# 1. noise transforms ---------------------------------------------------------------------------
check("16 conditions (2 base, 6 BH, 4 LR, 4 SS)", len(NT.CONDITIONS) == 16
      and sum(c["kind"] in ("BH", "BH_arm") for c in NT.CONDITIONS) == 6
      and sum(c["kind"] == "LR" for c in NT.CONDITIONS) == 4 and sum(c["kind"] == "SS" for c in NT.CONDITIONS) == 4)
for c in NT.CONDITIONS:
    a = NT.analytic_checks(NT.build(c))
    if not a["pass"]:
        check(f"T1(a) analytic {c['name']}", False, str(a))
check("T1(a) analytic checks pass for all 16 conditions", all(NT.analytic_checks(NT.build(c))["pass"] for c in NT.CONDITIONS))
m = NT.build({"kind": "BH", "r": 60, "kappa": 0.9, "seed": 0})
check("BH: ||K_L||_2 = kappa < 1", abs(np.linalg.norm(m["K_L"], 2) - 0.9) < 1e-9)
check("BH: K_RL = 0", np.abs(m["K_RL"]).max() == 0)
mr = NT.build({"kind": "BH_arm", "r": 12, "kappa": 0.9, "seed": 0})
check("arm12: right-hand source = body channels 42..47, 54..59", set(np.nonzero(np.abs(mr["K_Rb"]).sum(0))[0]) ==
      set(range(42, 48)) | set(range(54, 60)))
check("arm12: left-hand source = body channels 36..41, 48..53", set(np.nonzero(np.abs(mr["K_L"]).sum(0))[0]) ==
      set(range(36, 42)) | set(range(48, 54)))
ml = NT.build({"kind": "LR", "r": 90, "kappa": 0.9, "seed": 0})
check("LR: K_L = K_Rb = 0; S_R = sqrt(1-k^2) I", np.abs(ml["K_L"]).max() == 0 and np.abs(ml["K_Rb"]).max() == 0
      and np.abs(ml["S_R"] - np.sqrt(0.19) * np.eye(90)).max() < 1e-12)
kc, ks = NT.kl_per_frame(m)
check("KL BH-r60-k0.9 = 2*60*(-0.5 log 0.19)", abs(kc - 120 * (-0.5 * np.log(0.19))) < 1e-9 and ks == 0, f"{kc:.3f} nats/frame")
kc2, ks2 = NT.kl_per_frame(NT.build({"kind": "SS", "sigma": (0.75, 1.0)}))
check("KL SS-0.75-1 = 45 (s^2 - 1 - log s^2)", kc2 == 0 and abs(ks2 - 45 * (0.5625 - 1 - np.log(0.5625))) < 1e-9)
eps = torch.randn(64, 240, 304, dtype=torch.float64)
lengths = list(rng.integers(28, 305, 64))
et = NT.apply(m, eps, lengths)
pad_ok = all(torch.equal(et[i, :, L:], eps[i, :, L:]) for i, L in enumerate(lengths))
check("padded frames untouched", pad_ok)
X = torch.cat([et[i, :, :L].T for i, L in enumerate(lengths)])
C = (X.T @ X / len(X)).numpy()
check("empirical cov of eps~ matches design (max |diff| < 0.05 at n ~ 10k)",
      np.abs(C - NT.joint_cov(m)[0]).max() < 0.05, f"max {np.abs(C - NT.joint_cov(m)[0]).max():.3f}")
check("body noise unchanged (z_b = eps_b)", torch.equal(et[:, :60], eps[:, :60]))

# 2. metrics -------------------------------------------------------------------------------------
def smooth6d(C, T):
    base = np.cumsum(rng.normal(0, 0.05, (C, T)), axis=1) + rng.normal(0, 1, (C, 1))
    return base


xb, xl, xr = smooth6d(60, 304), smooth6d(90, 304), smooth6d(90, 304)
rec = M.sample_record(xb, xl, xr, 150)
check("sample record finite", all(np.all(np.isfinite(v)) for v in rec.values()))
rec2 = M.sample_record(xb, xr, xl, 150)
check("swapping hands negates X", abs(rec["X"] + rec2["X"]) < 1e-12)
R = M.to_mats(xl[:, :10])
check("Gram-Schmidt gives rotations", np.abs(np.swapaxes(R, -1, -2) @ R - np.eye(3)).max() < 1e-10
      and np.allclose(np.linalg.det(R), 1))

# 3. statistics ----------------------------------------------------------------------------------
J, n = 32, 8
idx = S.boot_idx(J, 0)


def fake(shift_X=0.0, scale=1.0):
    d = {}
    for k in S.T2_METRICS:
        d[k] = rng.normal(1.0, 0.01, (J, n))
    d["A_L"] = np.exp(rng.normal(0, 0.05, (J, n))) * scale
    d["A_R"] = np.exp(rng.normal(0, 0.05, (J, n)))
    d["X"] = np.log(d["A_L"] / d["A_R"]) + shift_X
    d["A_L"] = d["A_R"] * np.exp(d["X"])
    for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr"):
        d[k] = rng.normal(0.02, 0.05, (J, n))
    for k in ("m3_jerk_L", "m3_jerk_R", "extreme_frac_L", "extreme_frac_R"):
        d[k] = rng.uniform(0.9, 1.1, (J, n)) * (0.01 if "extreme" in k else 1)
    d["phi_L"] = rng.normal(0, 1, (J, n, 30))
    return d


a, b = fake(), fake()
t2 = S.t2(a, b, idx)
check("T2 on equal-law synthetic data passes all eight", t2["_overall"] == "pass", f"h = {t2['_h_pct']:.2f}%")
b2 = {k: (v * 1.10 if k in S.T2_METRICS else v) for k, v in b.items()}
check("T2 detects a 10% shift as fail", S.t2(a, b2, idx)["_overall"] == "fail")
t5 = S.t5a(a, idx, 0.05)
check("T5-A parity data -> pass", t5["S2_outcome"] == "pass" and t5["S1_outcome"] == "pass", f"mu = {t5['mu']:.4f}")
check("T5-A shifted data (mu = 0.2) -> fail", S.t5a(fake(shift_X=0.2), idx, 0.05)["S2_outcome"] == "fail")
c = fake()
for k in ("coord_arm_rhand",):
    c[k] = c[k] + 0.10
dl = S.paired_delta(c, a, "coord_arm_rhand", idx)
check("paired delta detects +0.10 coupling", S.transmission(dl), f"delta = {dl['delta']:.3f}")
ref = {"X": np.full(J, -0.4), "A_L": np.exp(np.full(J, -0.4)), "A_R": np.ones(J)}
phi_ref = rng.normal(0, 1, (256, 30))
dom = S.dominance(fake(shift_X=-0.35), a, b, ref, phi_ref, (0.85, 1.15), idx[:300], 0.05)
check("D-a passes for a -0.35 shift toward t* = -0.4", dom["D_a"]["pass"])
check("D-b closer for that shift", dom["D_b"]["closer"])
null = [S.t1_stats(torch.randn(5000, 240, dtype=torch.float64), torch.arange(4999), torch.arange(1, 5000),
                   {"b": slice(0, 60), "L": slice(60, 150), "R": slice(150, 240)},
                   [(slice(60, 150), slice(0, 60), None)]) for _ in range(20)]
cal = S.t1_calibrate(null)
check("T1 calibration widens only within registered caps; lag-1 untouched",
      all(cal["margins"][k] <= S.T1_CAPS[k] for k in S.T1_CAPS) and cal["margins"]["lag1"] == 0.03,
      f"margins {cal['margins']} fw {cal['fw_rate']:.2f} (toy n=5000, 20 sets)")

# 3b. preflight corrections (P-1, P-2, P-4, P-11, P-13) ----------------------------------------------
check("P-1 registered initial margins unchanged",
      S.T1_MARGINS == {"mean": 0.03, "var": 0.05, "corr": 0.035, "cross": 0.035, "lag1": 0.03})
check("P-1 registered caps only (no lag-1 cap)", S.T1_CAPS == {"mean": 0.05, "var": 0.10, "corr": 0.05, "cross": 0.05})
base_ok = {"mean": 0.0, "var": 0.0, "corr": 0.0, "cross": 0.0, "lag1": 0.0}
lagfail = [dict(base_ok, lag1=0.031) if i < 5 else dict(base_ok) for i in range(100)]  # 5% lag-1 null failures
c1 = S.t1_calibrate(lagfail)
check("P-1 lag-1 null failures -> no widening, calibration fails (stop)", not c1["calibrated"]
      and c1["margins"] == S.T1_MARGINS and "NOT a registered criterion" in c1["procedure"])
meanfail = [dict(base_ok, mean=0.032) if i < 5 else dict(base_ok) for i in range(100)]
c2 = S.t1_calibrate(meanfail)
check("P-1 mean null failures -> mean widens once to 0.035, others unchanged", c2["calibrated"]
      and c2["margins"] == dict(S.T1_MARGINS, mean=0.035) and len(c2["history"]) == 2)
meanbig = [dict(base_ok, mean=0.06) if i < 5 else dict(base_ok) for i in range(100)]
c3 = S.t1_calibrate(meanbig)
check("P-1 widening stops at the registered mean cap 0.05", not c3["calibrated"] and c3["margins"]["mean"] == 0.05)
check("P-2 mean-over-joints extreme fraction reported and <= any-joint fraction",
      "extreme_frac_meanjoint_L" in rec and rec["extreme_frac_meanjoint_L"] <= rec["extreme_frac_L"])


def dl(delta, lo):
    return {"delta": delta, "ci95": [lo, lo + 0.1]}


v = S.t3_verdict({"R": dl(0.08, 0.02), "L": dl(0.01, -0.03)}, {"R": [0.01, 0.04, 0.08], "L": [0.03, 0.0, 0.01]},
                 {"R": [dl(0.08, 0.02), dl(0.06, 0.01), dl(0.02, -0.01)], "L": [dl(0.01, -0.03)] * 3})
check("P-4 R-only: existence true, bilateral false, side named", v["existence_registered_criterion"] and not v["bilateral"]
      and v["verdict"] == "transmission on R only")
check("P-4 monotonicity judged on the transmitting side only", v["monotone_on_transmitting_sides"] == {"R": True}
      and v["monotone_verdict"] is True and v["monotone_by_side"]["L"] is False)
check("P-4 orientation counts per side", v["orientation_pass_count_by_side"] == {"R": 2, "L": 0})
check("P-4 both sides / neither side named", S.t3_verdict({"R": dl(.1, .02), "L": dl(.1, .02)}, {"R": [0, 0, 0], "L": [0, 0, 0]},
      {"R": [], "L": []})["verdict"] == "transmission on both sides" and
      S.t3_verdict({"R": dl(0, -1), "L": dl(0, -1)}, {"R": [0, 0, 0], "L": [0, 0, 0]}, {"R": [], "L": []})["verdict"]
      == "no transmission on either side")
ca, cb, cbase = fake(), fake(), fake()
for k in ("coord_arm_rhand",):
    cbase[k] = np.zeros((J, n)); ca[k] = np.full((J, n), 0.06); cb[k] = np.full((J, n), 0.12)
eff = S.efficiency(ca, cb, cbase, "coord_arm_rhand", 10.0, 100.0, list(rng.integers(28, 305, J)), idx)
check("P-11 efficiency ratio = (0.06/10)/(0.12/100) = 5 with a bootstrap CI", abs(eff["ratio_a_over_b"] - 5) < 1e-9
      and eff["ratio_ci95"][0] <= 5 <= eff["ratio_ci95"][1] + 1e-9, str(eff["ratio_ci95"]))
check("P-13 S3 caveat attached to T5-A output", "T4-e" in S.t5a(a, idx, 0.05)["S3_caveat"])
ed = S.energy_distance(rng.normal(0, 1, (64, 8)), rng.normal(0, 1, (64, 8)), np.repeat(np.arange(8), 8),
                       np.repeat(np.arange(8), 8), n_perm=200)
check("energy distance permutation test runs", 0 < ed["p_perm"] <= 1, str(ed))

# 4. orchestrator analysis stage on synthetic records (no model, no data, no generation) -----------------
import json  # noqa: E402
import tempfile  # noqa: E402

import e2e_run as R  # noqa: E402

keys1 = ["coord_arm_rhand", "coord_arm_lhand", "coord_lr", "A_L", "A_R", "X"] + \
        [f"{m}_{s}" for s in ("L", "R") for m in ("m1_speed", "m2_artic", "m3_jerk", "m4_angle", "extreme_frac",
                                                  "extreme_frac_meanjoint")]
tmp = Path(tempfile.mkdtemp())
run = R.Runner(tmp, tmp / "dumps")
run.lengths = list(rng.integers(28, 305, J))
for c in NT.CONDITIONS:
    d = run.data.setdefault(c["name"], {})
    for k in range(1, 9):
        AL, AR = np.exp(rng.normal(0, .1, J)), np.exp(rng.normal(0, .1, J))
        rec_k = {"A_L": AL, "A_R": AR, "X": np.log(AL / AR), "phi_L": rng.normal(0, 1, (J, 30)), "phi_R": rng.normal(0, 1, (J, 30))}
        for kk in keys1:
            rec_k.setdefault(kk, rng.uniform(0.5, 1.5, J) if not kk.startswith("coord") else rng.normal(0.02, .05, J))
        for kk, vv in rec_k.items():
            d.setdefault(kk, {})[k] = vv
run.res["steps"] = {"0": {"KL_per_frame": {c["name"]: NT.kl_per_frame(NT.build(c)) for c in NT.CONDITIONS}},
                    "2_3": {"n_star": 8}}
ref = {"X": np.full(J, -0.4), "A_L": np.exp(np.full(J, -0.4)), "A_R": np.ones(J)}
run.analyse({c["name"]: c for c in NT.CONDITIONS}, idx[:100], 0.05, ref, rng.normal(0, 1, (256, 30)), True)
an = json.loads((tmp / "results.json").read_text(encoding="utf-8"))["analysis"]
check("orchestrator analysis runs end-to-end on synthetic records", an and "T3_summary" in an)
check("analysis carries P-4 fields", {"verdict", "bilateral", "existence_registered_criterion",
                                      "orientation_pass_count_by_side", "monotone_verdict"} <= set(an["T3_summary"]))
check("analysis carries P-11 efficiency CIs", "ratio_ci95" in an["T3_summary"]["efficiency_arm12_over_r60"]["R"])
check("analysis carries P-10 descriptive n* block", "gate_at_n_star_descriptive" in an and
      an["gate_at_n_star_descriptive"]["note"].startswith("descriptive"))
check("analysis carries P-2 descriptive mean-joint extremes", all("extreme_meanjoint_descriptive" in v for v in an["T5B"].values()))
plan = R.plan()
check("plan states registered vs new T1 items", "never widened" in plan["T1_lag1"] and "lag1" not in plan["T1_caps_registered"])

print(f"\n{sum(results.values())}/{len(results)} checks passed")
sys.exit(0 if all(results.values()) else 1)
