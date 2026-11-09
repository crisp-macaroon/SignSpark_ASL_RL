"""FG-1 analysis (MC_REDESIGN_PROPOSAL.md Â§5.2; FG1_OPERATIONAL_DECISIONS.md D3-D5, D10). CPU only (J via smplx on CPU).

Per variant: held-out paired delta vs V0 of the intended statistic(s) (clip mean over 16 fresh noises; clip bootstrap
B = 2000, seed 0, 16 clips), the registered outcome rule (positive: CI lower > 0 AND point >= 0.05 AND preservation
pass; negative: CI upper < 0.05; else inconclusive), Stage 5 preservation checks vs V0 (both hands for V3), in-sample
vs held-out (generalisation gap), length split, state-shuffle ablation (V2, V3), best-of-16 selection context, J
(descriptive), typicality monitor (descriptive).

  python -E -s experiments/stage6_gate/fg1_analyse.py [--no-j]
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage5"))
import common5 as C  # noqa: E402
import rewards as RW  # noqa: E402
import evaluate as EV  # noqa: E402  (j_context, j_record, typ_monitor; unchanged)

OUT = HERE / "out"
THR = 0.05
B, BSEED = 2000, 0
STAT = {"R": "coord_arm_rhand", "L": "coord_arm_lhand", "LR": "coord_lr"}
INTENDED = {"V1": ("R",), "V2": ("R",), "V3": ("R", "L", "LR")}
KL_BOUND = {"V1": 49.82, "V2": 1.0, "V3": 1.0}
ART, JERK, EXT, ACT, UND = (0.9, 1.1), 1.10, 0.02, math.log(1.25), 0.005


def boot(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"mean": None, "ci95": [None, None], "n": 0}
    m = v[np.random.default_rng(BSEED).integers(0, len(v), (B, len(v)))].mean(1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}


def outcome(d, pres_ok):
    lo, hi = d["ci95"]
    if lo is not None and lo > 0 and d["mean"] >= THR and pres_ok:
        return "positive"
    if hi is not None and hi < THR:
        return "negative"
    return "inconclusive"


def records(xb, xl, xr, L):
    n, K = xb.shape[:2]
    return [[RW.r_record(xb[a, k], xl[a, k], xr[a, k], L[a]) for k in range(K)] for a in range(n)]


def arr(recs, f):
    return np.array([[f(r) for r in row] for row in recs], float)


def preservation(recs, recs0, kl, bound, hands):
    out = {}
    for h in hands:
        key = f"hand_{h}"
        with np.errstate(all="ignore"):
            art = arr(recs, lambda r: r[key]["m2_artic"]) / arr(recs0, lambda r: r[key]["m2_artic"])
            jerk = arr(recs, lambda r: r[key]["m3_jerk"]) / arr(recs0, lambda r: r[key]["m3_jerk"])
            act = np.log(arr(recs, lambda r: r[key]["A"]) / arr(recs0, lambda r: r[key]["A"]))
        ext = arr(recs, lambda r: r[key]["extreme_frac"]) - arr(recs0, lambda r: r[key]["extreme_frac"])
        st = STAT["R"] if h == "R" else STAT["L"]
        u, u0 = np.isnan(arr(recs, lambda r: r[st])).mean(), np.isnan(arr(recs0, lambda r: r[st])).mean()
        out[h] = {"artic_ratio_mean": {"value": float(np.nanmean(art)), "pass": bool(ART[0] <= np.nanmean(art) <= ART[1])},
                  "jerk_ratio_mean": {"value": float(np.nanmean(jerk)), "pass": bool(np.nanmean(jerk) <= JERK)},
                  "extreme_diff_mean": {"value": float(np.nanmean(ext)), "pass": bool(np.nanmean(ext) <= EXT)},
                  "abs_mean_log_activity_ratio": {"value": float(abs(np.nanmean(act))), "pass": bool(abs(np.nanmean(act)) <= ACT)},
                  "undefined_fraction": {"value": float(u), "uncoupled": float(u0), "pass": bool(u <= u0 + UND)},
                  "kl_max": {"value": float(kl[h].max()), "bound": bound, "pass": bool(kl[h].max() <= bound)}}
    allp = all(c["pass"] for h in out.values() for c in h.values())
    return out, allp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-j", action="store_true")
    ap.add_argument("--test", action="store_true", help="analyse the smoke-test outputs in out_test/")
    a = ap.parse_args()
    global OUT
    if a.test:
        OUT = HERE / "out_test"
    D = np.load(OUT / "prep.npz")
    n, K = D["ho_xb"].shape[:2]
    gc = json.loads((OUT / "gate_clips.json").read_text(encoding="utf-8"))
    gc = {k: (v[:n] if isinstance(v, list) else v) for k, v in gc.items()}
    L = np.array(gc["lengths"])
    runs = {p: json.loads((OUT / f"run_{p}.json").read_text(encoding="utf-8")) for p in ("prep", "V1", "V2", "V3")
            if (OUT / f"run_{p}.json").exists()}
    xb = D["ho_xb"]
    rec0 = records(xb, D["ho_V0_xl"], D["ho_V0_xr"], L)
    fit0 = records(D["fit_xb"], D["fit_V0_xl"], D["fit_V0_xr"], L)
    V0 = {h: arr(rec0, lambda r, s=s: r[s]) for h, s in STAT.items()}
    V0fit = {h: arr(fit0, lambda r, s=s: r[s]) for h, s in STAT.items()}
    res = {"label": "FG-1 fresh-noise controllability gate; per-clip fits on 16 TRAIN clips; released-checkpoint result, not a "
                    "paper reproduction; motion statistics only", "clips": gc, "threshold": THR, "runs": runs,
           "V0": {h: boot(np.nanmean(V0[h], 1)) for h in STAT}, "V0_fit_noises": {h: boot(np.nanmean(V0fit[h], 1)) for h in STAT},
           "best_of_16_heldout_V0_selection_context": {h: boot(np.nanmax(V0[h], 1)) for h in STAT},
           "V0_undefined": {h: int(np.isnan(V0[h]).sum()) for h in STAT}, "variants": {}}
    jctx = None
    if not a.no_j:
        jctx = EV.j_context()
        res["J_V0"] = {}
    samples_J = {}
    for v in ("V1", "V2", "V3"):
        if v not in runs or runs[v].get("status") != "completed":
            res["variants"][v] = {"status": runs.get(v, {}).get("status", "not run")}
            continue
        H = np.load(OUT / f"{v}_heldout.npz")
        recs = records(xb, H["xl"], H["xr"], L)
        X = {h: arr(recs, lambda r, s=s: r[s]) for h, s in STAT.items()}
        kl = {"R": H["kl_R"], "L": H["kl_L"]}
        hands = ("L", "R") if v == "V3" else ("R",)
        pres, pres_ok = preservation(recs, rec0, kl, KL_BOUND[v], hands)
        hist = np.load(OUT / f"{v}_fit_history.npz")
        e = {"status": "completed", "params_per_clip": runs[v]["params_per_clip"], "seconds": runs[v]["seconds"],
             "gpu_peak_reserved_GiB": runs[v]["gpu_peak_reserved_GiB"], "preservation": pres, "preservation_pass": pres_ok,
             "kl_max": {h: float(kl[h].max()) for h in kl}, "kl_mean": {h: float(kl[h].mean()) for h in kl},
             "undefined": {h: int(np.isnan(X[h]).sum()) for h in STAT}, "statistics": {}}
        if v == "V1":
            e["kl_R_le_1_nat_frame"] = bool(kl["R"].max() <= 1.0)
        outs = []
        for h in STAT:
            d_clip = np.nanmean(X[h], 1) - np.nanmean(V0[h], 1)
            gkey = {"R": "geo_R", "L": "geo_L", "LR": "geo_LR"}[h]
            tr = np.nanmean(hist[gkey], 2)  # [it, clip]
            ins_last = tr[-1] - np.nanmean(V0fit[h], 1)
            ins_best = np.nanmax(tr, 0) - np.nanmean(V0fit[h], 1)
            st = {"heldout_level": boot(np.nanmean(X[h], 1)), "heldout_delta_vs_V0": boot(d_clip),
                  "per_clip_delta": d_clip.tolist(), "n_clips_positive": int((d_clip > 0).sum()),
                  "insample_delta_last_iter": boot(ins_last), "insample_delta_best_iter": boot(ins_best),
                  "generalisation_gap_last": boot(ins_last - d_clip),
                  "insample_mean_by_iteration": np.nanmean(tr, 1).tolist(),
                  "split_L": {"L<100": boot(d_clip[L < 100]), "L>=100": boot(d_clip[L >= 100])},
                  "intended": h in INTENDED[v]}
            if h in INTENDED[v]:
                st["outcome"] = outcome(st["heldout_delta_vs_V0"], pres_ok)
                outs.append(st["outcome"])
            e["statistics"][h] = st
        if v == "V3":
            e["outcome"] = ("positive" if "positive" in outs else "negative" if all(o == "negative" for o in outs) else "inconclusive")
        else:
            e["outcome"] = outs[0]
        if (OUT / f"{v}_shuffle.npz").exists():
            S = np.load(OUT / f"{v}_shuffle.npz")
            rs = records(xb, S["xl"], S["xr"], L)
            e["state_shuffle_ablation"] = {
                h: {"delta_vs_V0": boot(np.nanmean(arr(rs, lambda r, s=s: r[s]), 1) - np.nanmean(V0[h], 1)),
                    "delta_vs_unshuffled": boot(np.nanmean(arr(rs, lambda r, s=s: r[s]), 1) - np.nanmean(X[h], 1))}
                for h, s in STAT.items() if h in INTENDED[v]}
        typ = {"R": [], "L": []}
        for aa in range(n):
            for k in range(K):
                typ["R"].append(EV.typ_monitor(H["eps_R"][aa, k, :, : L[aa]]))
                if v == "V3":
                    typ["L"].append(EV.typ_monitor(H["eps_L"][aa, k, :, : L[aa]]))
        e["typicality_violation_fraction"] = {h: {q: float(np.mean([t[q] for t in typ[h]])) for q in ("M", "V", "A", "P")}
                                              for h in typ if typ[h]}
        if jctx is not None:
            jr = [[EV.j_record(jctx, xb[aa, k], H["xl"][aa, k], H["xr"][aa, k], L[aa]) for k in range(K)] for aa in range(n)]
            samples_J[v] = jr
        res["variants"][v] = e
        print(v, e["outcome"], {h: e["statistics"][h]["heldout_delta_vs_V0"] for h in INTENDED[v]}, "pres", pres_ok, flush=True)
    typ0 = [EV.typ_monitor(D["ho_noise"][aa, k, 150:240, : L[aa]]) for aa in range(n) for k in range(K)]
    res["V0_typicality_violation_fraction_R"] = {q: float(np.mean([t[q] for t in typ0])) for q in ("M", "V", "A", "P")}
    if jctx is not None:
        j0 = [[EV.j_record(jctx, xb[aa, k], D["ho_V0_xl"][aa, k], D["ho_V0_xr"][aa, k], L[aa]) for k in range(K)] for aa in range(n)]
        JS = ("coord_ah_J_R", "coord_ah_J_L", "coord_lr_J")
        J0 = {s: np.array([[r[s] for r in row] for row in j0], float) for s in JS}
        res["J_V0"] = {s: boot(np.nanmean(J0[s], 1)) for s in JS}
        for v, jr in samples_J.items():
            Jv = {s: np.array([[r[s] for r in row] for row in jr], float) for s in JS}
            res["variants"][v]["J_descriptive_delta_vs_V0"] = {s: boot(np.nanmean(Jv[s], 1) - np.nanmean(J0[s], 1)) for s in JS}
    (OUT / "fg1_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("wrote", OUT / "fg1_results.json")


if __name__ == "__main__":
    main()
