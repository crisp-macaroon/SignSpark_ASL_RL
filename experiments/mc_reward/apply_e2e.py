"""Apply the registered M-C reward (mc_reward.py) to the existing Stage 4 E2e dumps: descriptive, no generation.

Data: experiments/stage4/e2e/dumps (dev clips 0..31, the fixed M-C transforms of E2e; noises k = 1..8 shared by all
conditions). Under M-C the body noise is untouched (z_b = eps_b; E2e T0c body identity max |diff| = 0.0), so each
condition's hands pair with the A0 body of the same k; the paired base sample x0 is A0 itself (CRN, same base noise).
A0p (independent base noise, own body) is a no-transform control: its difference from A0 is pure noise.
calib_L: per-clip reference left-hand activity of these dev clips from our dev-256 baseline dump (reference poses;
no generation). The registered c_left (i) names train references; for dev clips the clip's own reference is the only
per-clip one, so this is a deviation, recorded in the output.
Fixed transforms, not a controller: no training, lambda = 0 (no dual ascent), alpha = 0, no z-normalisation (train
base statistics not computed). Released-checkpoint result, not a paper reproduction.

    python -E -s experiments/mc_reward/apply_e2e.py
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mc_reward as M  # noqa: E402

DUMPS = M.ROOT / "experiments/stage4/e2e/dumps"
DEV256_HAND = M.ROOT / ("experiments/baseline/runs/hand/h2s_dev256_gf_s10_N8/debug0_eulerstepsize10_can8_anchor0_samples/"
                        "seed102_clampstep0_h2s_dev256_gf_s10_N8.npy")
E2E_RESULTS = M.ROOT / "experiments/stage4/e2e/out/results.json"
OUT = HERE / "out"
KS = range(1, 9)
J = 32
COMPONENTS = ("r_ah_L", "r_ah_R", "r_lr", "r_coord", "r_dom")
STATS = ("coord_ah_L", "coord_ah_R", "coord_lr", "dom")
CONSTR = ("art_L", "art_R", "jerk_L", "jerk_R", "ext_L", "lr_floor", "calib_L")


def load(cond, k):
    return np.load(DUMPS / cond / f"k{k:02d}.npz")


def boot(v, B=2000, seed=0):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    m = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}


def main():
    OUT.mkdir(exist_ok=True)
    lengths = json.loads(E2E_RESULTS.read_text(encoding="utf-8"))["steps"]["0"]["ref32_lengths"]
    d = np.load(DEV256_HAND, allow_pickle=True).item()
    gt, lens = d["gt_poses"][0], d["lengths"][0]
    assert [int(lens[2 * i]) for i in range(J)] == lengths
    A_L_ref = [M.MR.reference_record(gt[2 * i], gt[2 * i + 1], int(lens[2 * i]))["A_L"] for i in range(J)]
    specs = {c["name"]: c for c in M.NT.CONDITIONS}
    conds = [c for c in specs if c != "A0"]
    base = {k: load("A0", k) for k in KS}
    rec0 = {k: [M.record(base[k]["body"][j], base[k]["hand"][j, 0], base[k]["hand"][j, 1], lengths[j]) for j in range(J)]
            for k in KS}
    res = {"label": "M-C reward (registered §6.1) applied to existing E2e dumps; descriptive; fixed transforms, no "
                    "training; released-checkpoint result, not a paper reproduction",
           "targets": M.TARGETS, "targets_sha256": M.TARGETS_SHA256, "clips": J, "noises": list(KS),
           "settings": {"lambda": 0.0, "alpha_kappa": 0.0, "alpha_sigma": 0.0, "znorm": None,
                        "calib_L_reference": "dev clip's own reference (deviation: registered = train references)",
                        "A0p": "independent noise control, not CRN-paired"},
           "conditions": {}}
    per_clip = {}
    for c in ["A0"] + conds:
        spec = specs[c]
        klk, kls = M.kl_terms(M.NT.build(spec), 1)
        comp = {n: np.full((len(KS), J), np.nan) for n in COMPONENTS + STATS + CONSTR}
        flags = {"s3_undefined": 0, "dom_undefined": 0, "a3_undefined": {k: 0 for k in CONSTR}}
        for a, k in enumerate(KS):
            if c == "A0":
                recs = rec0[k]
            else:
                z = load(c, k)
                body = z["body"] if "body" in z.files else base[k]["body"]
                recs = [M.record(body[j], z["hand"][j, 0], z["hand"][j, 1], lengths[j]) for j in range(J)]
            calib, _ = M.calib_left(recs, A_L_ref)
            for j, (r, r0) in enumerate(zip(recs, rec0[k])):
                ct, cu = M.coord_terms(r)
                rd, du = M.dom_term(r)
                raw = M.episode_constraints(r, r0)
                raw["calib_L"] = calib
                for n in ("r_ah_L", "r_ah_R", "r_lr"):
                    comp[n][a, j] = ct[n]
                comp["r_coord"][a, j] = sum(ct.values())
                comp["r_dom"][a, j] = rd
                for n in STATS:
                    comp[n][a, j] = r[n]
                for n in CONSTR:
                    comp[n][a, j] = raw[n]
                    flags["a3_undefined"][n] += int(not np.isfinite(raw[n]))
                flags["s3_undefined"] += int(any(cu.values()))
                flags["dom_undefined"] += int(du)
        cm = {n: np.nanmean(v, 0) for n, v in comp.items()}  # per-clip means over the 8 noises
        per_clip[c] = {n: v.tolist() for n, v in cm.items()}
        entry = {"kind": spec["kind"], "kappa": spec.get("kappa"), "r": spec.get("r"), "sigma": spec.get("sigma"),
                 "kl_kappa_per_frame": klk, "kl_sigma_per_frame": kls, "flags": flags,
                 "level": {n: boot(cm[n]) for n in COMPONENTS + STATS},
                 "constraint_mean": {n: boot(cm[n]) for n in CONSTR},
                 "constraint_violated_fraction": {n: float(np.nanmean(comp[n] > 0)) for n in CONSTR}}
        if c != "A0":
            entry["paired_delta_vs_A0"] = {n: boot(cm[n] - np.array(per_clip["A0"][n])) for n in COMPONENTS + STATS}
        res["conditions"][c] = entry
        print(f"{c:<20} r_coord {entry['level']['r_coord']['mean']:+.4f}  r_dom {entry['level']['r_dom']['mean']:+.4f}  "
              f"KL {klk:.2f}/{kls:.2f}  S3 {flags['s3_undefined']} dom-undef {flags['dom_undefined']}")
    (OUT / "mc_reward_e2e.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (OUT / "mc_reward_e2e_per_clip.json").write_text(json.dumps(per_clip), encoding="utf-8")
    print("wrote", OUT / "mc_reward_e2e.json")


if __name__ == "__main__":
    main()
