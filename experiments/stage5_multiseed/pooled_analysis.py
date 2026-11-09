"""MS-P: pooled multi-seed analysis (ACMS_MULTISEED_DESIGN.md §5) + OPT-C / OPT-G aggregation. CPU only; reads outputs.

Unit of inference = training run. Primary pooling set = the four new runs (7001-7004); secondary = all five
(7000 = the Stage 5 reference, read from experiments/stage5/out, never rewritten). Category rule §5.3, fixed before any
multi-seed result was seen. R primary; J descriptive; never combined.

  python -E -s experiments/stage5_multiseed/pooled_analysis.py
"""

import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S5 = ROOT / "experiments" / "stage5" / "out"
OUT = HERE / "out"
NEW = (7001, 7002, 7003, 7004)
ALL = (7000,) + NEW
TAU = 0.4514
B, BSEED = 2000, 0
R_STATS = ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "dom_X")
J_STATS = ("coord_ah_J_R", "coord_ah_J_L", "coord_lr_J", "dom_J")
CHECKS = ("artic_ratio_mean", "jerk_ratio_mean", "extreme_diff_mean", "abs_mean_log_activity_ratio", "undefined_fraction", "kl_max")


def paths(s):
    if s == 7000:
        return S5 / "train", S5 / "eval", OUT / "s7000"
    return OUT / f"s{s}" / "train", OUT / f"s{s}" / "eval", OUT / f"s{s}"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None


def boot_mean(v, seed=BSEED):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    m = v[np.random.default_rng(seed).integers(0, len(v), (B, len(v)))].mean(1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}


def tint(x):
    x = np.asarray(x, float)
    n = len(x)
    if n < 2:
        return {"n": n, "mean": float(x.mean()) if n else None, "sd": None, "ci95": [None, None]}
    m, sd = float(x.mean()), float(x.std(ddof=1))
    h = float(stats.t.ppf(0.975, n - 1)) * sd / math.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "ci95": [m - h, m + h], "t_crit": float(stats.t.ppf(0.975, n - 1)),
            "min": float(x.min()), "max": float(x.max())}


def heterogeneity(d, se):
    d, se = np.asarray(d, float), np.asarray(se, float)
    w = 1 / se ** 2
    dw = float((w * d).sum() / w.sum())
    Q = float((w * (d - dw) ** 2).sum())
    k = len(d)
    p = float(1 - stats.chi2.cdf(Q, k - 1))
    I2 = max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0
    tau2 = max(0.0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    return {"Q": Q, "df": k - 1, "p": p, "I2": I2, "tau2_DL": tau2, "fixed_effect_mean": dw}


def category(per, pooled, het):
    """§5.3, applied in order."""
    if not all(r["valid_run"] for r in per):
        return "inconclusive (validity)"
    if pooled["mean"] <= 0:
        return "negative"
    lo = pooled["ci95"][0]
    indiv_neg = any(r["primary"]["ci95"][1] < 0 for r in per)
    indiv_pos = any(r["primary"]["ci95"][0] > 0 for r in per)
    if lo > 0 and not indiv_neg:
        return "reproducible positive"
    if lo > 0 and indiv_neg:
        return "seed-sensitive"
    if het["p"] < 0.05 or (indiv_neg and indiv_pos):
        return "seed-sensitive"
    return "inconclusive (precision)"


def per_run(s):
    tdir, edir, odir = paths(s)
    run, ev, groups, eps = load(tdir / "run.json"), load(edir / "eval_results.json"), load(tdir / "groups.json"), load(tdir / "episodes.json")
    if ev is None or run is None:
        return {"seed": s, "missing": True}
    R = ev["R_space"]
    pc = ev["preservation_checks_trained_vs_uncoupled"]
    d = R["coord_arm_rhand"]["trained-uncoupled"]["paired_clip_mean"]
    rec = {"seed": s, "missing": False, "primary": d,
           "primary_se": (d["ci95"][1] - d["ci95"][0]) / 3.92,
           "per_clip": R["coord_arm_rhand"]["trained-uncoupled"]["per_clip"],
           "deltas_R": {st: {pair: R[st][pair]["paired_clip_mean"] for pair in ("trained-uncoupled", "trained-initial", "initial-uncoupled")}
                        for st in R_STATS},
           "levels_R": {st: {c: R[st][c]["clip_mean"]["mean"] for c in ("uncoupled", "initial", "trained")} for st in R_STATS},
           "undefined_fraction": {st: {c: R[st][c]["undefined_fraction"] for c in ("uncoupled", "initial", "trained")} for st in R_STATS},
           "preservation": {k: pc[k] for k in CHECKS}, "all_checks_pass": ev["verdict"]["all_preservation_checks_pass"],
           "activity_ratio_R": ev["per_stream"]["hand_R.A"]["trained"]["mean"] / ev["per_stream"]["hand_R.A"]["uncoupled"]["mean"],
           "kl_per_frame": ev["kl_per_frame"], "validity_false_counts": ev["validity_flags_false_counts"],
           "verdict_single_run": ev["verdict"]["pre_registered"], "gap_closure": ev["verdict"]["gap_closure_toward_tau"],
           "J": {st: ev["J_space_descriptive"][st]["trained-uncoupled"]["paired_clip_mean"] for st in J_STATS}
           if ev.get("J_space_descriptive") else None,
           "leak_ratio_R": ev.get("J_space_descriptive", {}).get("leak_ratio_R"),
           "train": {"status": run["status"], "episodes": run["episodes_completed"], "seconds": run["seconds"],
                     "gpu_peak_alloc_GiB": run["gpu_peak_alloc_GiB"], "gpu_peak_reserved_GiB": run["gpu_peak_reserved_GiB"],
                     "weights_unchanged": run["model_weights_unchanged"], "opened_splits": run["opened_splits"],
                     "final_lambda": run["final_lambda"], "final_beta": run["final_beta"], "final_param_norm": run["final_param_norm"]},
           "eval_run": {k: ev["run"][k] for k in ("seconds", "gpu_peak_alloc_GiB", "gpu_peak_reserved_GiB", "model_weights_unchanged",
                                                    "opened_splits")}}
    Rg = np.array([g["R_mean"] for g in groups])
    rec["train"].update({"R_first25": float(Rg[:25].mean()), "R_last25": float(Rg[-25:].mean()), "R_all": float(Rg.mean()),
                         "max_c": {k: float(max(e["c"][k] for e in eps)) for k in ("art", "jerk", "ext", "act")},
                         "n_s3": int(sum(e["s3_undefined_primary"] for e in eps)),
                         "n_a3": int(sum(sum(e["a3_undefined"].values()) for e in eps)),
                         "grad_norm_pre_mean": float(np.mean([g["grad_norm_pre_clip"] for g in groups])),
                         "n_clipped": int(sum(g["grad_norm_pre_clip"] > 1.0 for g in groups)),
                         "kl_first": groups[0]["kl_mean"], "kl_last": groups[-1]["kl_mean"],
                         "beta_first": groups[0]["beta_after"], "beta_last": groups[-1]["beta_after"]})
    tw = np.array([e["controlled"]["coord_arm_rhand"] - e["uncoupled_twin"]["coord_arm_rhand"] for e in eps], float)
    tw_g = np.nanmean(tw.reshape(-1, 4), 1)
    rec["train"]["controlled_minus_twin"] = boot_mean(tw_g)
    rec["valid_run"] = bool(run["status"] == "completed" and run["episodes_completed"] == 500 and run["model_weights_unchanged"]
                            and ev["run"]["model_weights_unchanged"] and set(run["opened_splits"]) <= {"train"}
                            and set(ev["run"]["opened_splits"]) <= {"dev"} and ev["verdict"]["all_preservation_checks_pass"])
    # OPT-C (held-out vs training progress) and OPT-G (training-like)
    prog = {0: R["coord_arm_rhand"]["initial-uncoupled"]["paired_clip_mean"], 125: d}
    for u in (25, 50, 75, 100):
        o = load(odir / "optc" / f"u{u:03d}" / "eval_results.json")
        prog[u] = o["R_space"]["coord_arm_rhand"]["trained-uncoupled"]["paired_clip_mean"] if o else None
    rec["optc_progress"] = {str(k): prog[k] for k in sorted(prog)}
    rec["optc_runtime"] = {u: (load(odir / "optc" / f"u{u:03d}" / "eval_results.json") or {}).get("run", {}).get("seconds")
                           for u in (25, 50, 75, 100)}
    g = load(odir / "optg" / "train_eval_results.json")
    if g:
        gd = g["R_space"]["coord_arm_rhand"]["trained-uncoupled"]["paired_clip_mean"]
        rec["optg"] = {"train_like": gd, "heldout_dev": d["mean"], "gap_train_minus_dev": gd["mean"] - d["mean"],
                       "train_like_preservation_pass": g["verdict"]["all_preservation_checks_pass"],
                       "train_like_levels": {c: g["R_space"]["coord_arm_rhand"][c]["clip_mean"]["mean"] for c in ("uncoupled", "trained")},
                       "seconds": g["run"]["seconds"], "opened_splits": g["run"]["opened_splits"],
                       "weights_unchanged": g["run"]["model_weights_unchanged"]}
    else:
        rec["optg"] = None
    return rec


def pool(per, label):
    per = [r for r in per if not r["missing"]]
    d = [r["primary"]["mean"] for r in per]
    se = [r["primary_se"] for r in per]
    pooled = tint(d)
    het = heterogeneity(d, se) if len(d) >= 2 else None
    pcm = np.mean(np.array([r["per_clip"] for r in per], float), 0)
    rng = np.random.default_rng(BSEED)
    M = np.array([r["per_clip"] for r in per], float)
    hb = []
    for _ in range(B):
        si = rng.integers(0, len(per), len(per))
        ci = rng.integers(0, M.shape[1], M.shape[1])
        hb.append(np.nanmean(M[np.ix_(si, ci)]))
    unc = float(np.mean([r["levels_R"]["coord_arm_rhand"]["uncoupled"] for r in per]))
    out = {"label": label, "seeds": [r["seed"] for r in per], "primary_per_run": dict(zip([str(r["seed"]) for r in per], d)),
           "pooled_t": pooled, "eval_sampling_clip_bootstrap": boot_mean(pcm),
           "hierarchical_bootstrap": {"mean": float(np.mean(hb)), "ci95": [float(np.percentile(hb, 2.5)), float(np.percentile(hb, 97.5))]},
           "heterogeneity": het, "category": category(per, pooled, het) if het else None,
           "magnitude": {"gap_closure": pooled["mean"] / (TAU - unc), "ratio_to_0.05": pooled["mean"] / 0.05,
                         "any_run_point_ge_0.05": any(x >= 0.05 for x in d)}}
    sec = {}
    for st in R_STATS:
        for pair in ("trained-uncoupled", "trained-initial", "initial-uncoupled"):
            sec[f"R.{st}.{pair}"] = tint([r["deltas_R"][st][pair]["mean"] for r in per])
    for k in CHECKS:
        vals = [r["preservation"][k].get("value", r["preservation"][k].get("trained")) for r in per]
        sec[f"check.{k}"] = tint(vals)
    sec["activity_ratio_R"] = tint([r["activity_ratio_R"] for r in per])
    sec["kl_trained_mean"] = tint([r["kl_per_frame"]["trained"]["mean"] for r in per])
    sec["kl_trained_max"] = tint([r["kl_per_frame"]["trained"]["max"] for r in per])
    if all(r["J"] for r in per):
        for st in J_STATS:
            sec[f"J.{st}.trained-uncoupled"] = tint([r["J"][st]["mean"] for r in per])
    for k in ("R_first25", "R_last25", "seconds", "gpu_peak_alloc_GiB"):
        sec[f"train.{k}"] = tint([r["train"][k] for r in per])
    sec["train.controlled_minus_twin"] = tint([r["train"]["controlled_minus_twin"]["mean"] for r in per])
    sec["eval.seconds"] = tint([r["eval_run"]["seconds"] for r in per])
    prog = {}
    for u in ("0", "25", "50", "75", "100", "125"):
        v = [r["optc_progress"][u]["mean"] for r in per if r["optc_progress"].get(u)]
        prog[u] = tint(v) if len(v) == len(per) else {"n": len(v), "incomplete": True}
    out["optc_progress_pooled"] = prog
    g = [r["optg"] for r in per if r["optg"]]
    out["optg_pooled"] = ({"train_like": tint([x["train_like"]["mean"] for x in g]),
                           "gap_train_minus_dev": tint([x["gap_train_minus_dev"] for x in g])}
                          if len(g) == len(per) else {"n": len(g), "incomplete": True})
    out["secondary"] = sec
    return out


def main():
    per = [per_run(s) for s in ALL]
    # uncoupled identity across runs (same eval noise, mu = 0)
    ref = load(S5 / "eval" / "eval_samples.json")
    key = lambda r: (r["clip"], r["k"])  # noqa: E731
    ru = {key(r): r["R"]["coord_arm_rhand"] for r in ref if r["cond"] == "uncoupled"}
    ident = {}
    for s in NEW:
        sm = load(OUT / f"s{s}" / "eval" / "eval_samples.json")
        if sm:
            diffs = [abs(r["R"]["coord_arm_rhand"] - ru[key(r)]) for r in sm if r["cond"] == "uncoupled"]
            ident[str(s)] = {"max_abs_diff_vs_7000": float(np.nanmax(diffs)), "n": len(diffs),
                             "bitwise_equal": bool(np.nanmax(diffs) == 0.0)}
    vs7000 = {}
    p0 = np.array(per[0]["per_clip"], float)
    for r in per[1:]:
        if not r["missing"]:
            vs7000[str(r["seed"])] = boot_mean(np.array(r["per_clip"], float) - p0)
    res = {"label": "ACMS multi-seed replication; released-checkpoint result, not a paper reproduction; motion statistics only "
                    "(no semantic, naturalness, intelligibility or ASL-quality claim)",
           "primary_statistic": "R v1.1 right arm-right hand coordination, paired clip-mean trained(update 125) - uncoupled, dev-256 x 4",
           "per_run": per, "pooled_primary_new4": pool([r for r in per if r["seed"] in NEW], "primary: 4 new runs"),
           "pooled_secondary_all5": pool(per, "secondary: all 5 runs"), "uncoupled_identity_across_runs": ident,
           "run_minus_7000_paired": vs7000}
    (OUT / "pooled_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    for k in ("pooled_primary_new4", "pooled_secondary_all5"):
        p = res[k]
        print(k, "per run", {s: round(v, 5) for s, v in p["primary_per_run"].items()}, "pooled", p["pooled_t"], "category", p["category"])


if __name__ == "__main__":
    main()
