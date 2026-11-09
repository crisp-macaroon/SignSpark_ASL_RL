"""E2e statistics (Stage 4 rev. 4.0 §6.5, §15.3, §15.4). Every threshold below is the pre-registered value;
nothing here is tuned. Clip-cluster bootstrap: 2,000 resamples of the 32 clips, paired across conditions.

Per-condition data: dict metric -> array [J, n] (clip x noise; NaN allowed), plus "phi_L" [J, n, 30].
"""

import numpy as np
from scipy import linalg
from scipy.stats import chi2

B_BOOT = 2000
T2_METRICS = [f"{m}_{s}" for s in ("L", "R") for m in ("m1_speed", "m2_artic", "m3_jerk", "m4_angle")]
LOG08, LOG075 = np.log(0.8), np.log(0.75)


def boot_idx(J, seed, B=B_BOOT):
    return np.random.default_rng(seed).integers(0, J, (B, J))


def cmean(a):
    return np.nanmean(a, axis=1)  # per-clip mean over noises


def pct(x, q):
    return float(np.nanpercentile(x, q))


def three_way(lo, hi, a, b):
    """CI [lo, hi] vs equivalence region [a, b]: pass (inside), fail (entirely outside), straddle."""
    if a <= lo and hi <= b:
        return "pass"
    if hi < a or lo > b:
        return "fail"
    return "straddle"


# ---------------------------------------------------------------- T2 (eight-metric marginal check)
def t2(cond, base, idx, margin=0.05):
    out = {}
    for k in T2_METRICS:
        c, b = cmean(cond[k]), cmean(base[k])
        r = np.nanmean(c) / np.nanmean(b)
        rb = np.nanmean(c[idx], 1) / np.nanmean(b[idx], 1)
        lo, hi = pct(rb, 5), pct(rb, 95)
        out[k] = {"ratio": float(r), "ci90": [lo, hi], "half_width_pct": 100 * (hi - lo) / 2,
                  "outcome": three_way(lo, hi, 1 - margin, 1 + margin)}
    outcomes = [v["outcome"] for v in out.values()]
    out["_overall"] = "pass" if all(o == "pass" for o in outcomes) else ("fail" if "fail" in outcomes else "straddle")
    out["_h_pct"] = max(v["half_width_pct"] for k, v in out.items() if not k.startswith("_"))
    return out


# ---------------------------------------------------------------- T3 / T4 paired differences
def paired_delta(cond, base, key, idx):
    d = cmean(cond[key]) - cmean(base[key])
    db = np.nanmean(d[idx], 1)
    return {"delta": float(np.nanmean(d)), "ci95": [pct(db, 2.5), pct(db, 97.5)]}


def transmission(dl):
    return dl["delta"] >= 0.05 and dl["ci95"][0] > 0


def t3_verdict(gate_by_side, kappa_by_side, seeds_by_side):
    """P-4 reporting. gate_by_side: {side: delta dict at kappa0.9-seed0}; kappa_by_side: {side: [d0.3, d0.6, d0.9]};
    seeds_by_side: {side: [delta dict for seed 0, 1, 2]}. The registered transmission criterion (either side) is kept
    as 'existence'; bilateral transmission is reported separately and never inferred from one side."""
    tx = {s: bool(transmission(d)) for s, d in gate_by_side.items()}
    sides = [s for s in ("R", "L") if tx[s]]
    mono = {s: bool(v[0] <= v[1] + 0.01 and v[1] <= v[2] + 0.01) for s, v in kappa_by_side.items()}
    return {"transmission_by_side": tx,
            "existence_registered_criterion": bool(sides),
            "bilateral": bool(len(sides) == 2),
            "verdict": {0: "no transmission on either side", 1: f"transmission on {sides[0] if sides else ''} only",
                        2: "transmission on both sides"}[len(sides)],
            "monotone_by_side": mono,
            "monotone_on_transmitting_sides": {s: mono[s] for s in sides},
            "monotone_verdict": (all(mono[s] for s in sides) if sides else None),
            "orientation_pass_count_by_side": {s: int(sum(transmission(d) for d in v)) for s, v in seeds_by_side.items()},
            "deltas_by_side": {s: {"delta": d["delta"], "ci95": d["ci95"]} for s, d in gate_by_side.items()}}


def efficiency(cond_a, cond_b, base, key, klf_a, klf_b, lengths, idx):
    """P-11: delta per KL nat for two conditions (same clips and noises), and their ratio a/b, with 95% bootstrap CIs.
    KL per sample = exact per-frame KL x L_j; its mean over the (resampled) clips is klf x mean(L)."""
    L = np.asarray(lengths, float)
    da, db = cmean(cond_a[key]) - cmean(base[key]), cmean(cond_b[key]) - cmean(base[key])
    ea, eb = np.nanmean(da) / (klf_a * L.mean()), np.nanmean(db) / (klf_b * L.mean())
    ea_b = np.nanmean(da[idx], 1) / (klf_a * L[idx].mean(1))
    eb_b = np.nanmean(db[idx], 1) / (klf_b * L[idx].mean(1))
    ratio_b = ea_b / eb_b
    return {"per_nat_a": float(ea), "per_nat_a_ci95": [pct(ea_b, 2.5), pct(ea_b, 97.5)],
            "per_nat_b": float(eb), "per_nat_b_ci95": [pct(eb_b, 2.5), pct(eb_b, 97.5)],
            "ratio_a_over_b": float(ea / eb) if eb != 0 else float("nan"),
            "ratio_ci95": [pct(ratio_b, 2.5), pct(ratio_b, 97.5)],
            "note": "descriptive (no registered threshold); KL is the total coupling KL of both hands; ratio CI unstable "
                    "if the denominator's delta is near 0"}


S3_CAVEAT = ("S3 is descriptive only; it may be infinite under T4-a..d (App. G.6.1); its sample mean and CI are "
             "unstable if T4-e (finite S3) fails")


# ---------------------------------------------------------------- T5-A (Theorem 4 parity, TOST)
def t5a(cond, idx, delta_s2):
    xb = cmean(cond["X"])
    mu = float(np.nanmean(xb))
    mub = np.nanmean(xb[idx], 1)
    lo, hi = pct(mub, 5), pct(mub, 95)
    s2 = "pass" if (-delta_s2 < lo and hi < delta_s2) else ("fail" if (hi < -delta_s2 or lo > delta_s2) else "inconclusive")
    al, ar = cmean(cond["A_L"]), cmean(cond["A_R"])
    s1 = float(np.nanmean(al) / np.nanmean(ar))
    s1b = np.nanmean(al[idx], 1) / np.nanmean(ar[idx], 1)
    l1, h1 = pct(s1b, 5), pct(s1b, 95)
    s1o = three_way(l1, h1, 0.95, 1.05)
    s1o = "inconclusive" if s1o == "straddle" else s1o
    s4 = np.nanmean(cond["A_R"] > cond["A_L"], axis=1)
    s3 = cmean(cond["A_L"] / cond["A_R"])
    return {"mu": mu, "mu_ci90": [lo, hi], "delta_S2": delta_s2, "S2_outcome": s2,
            "S1": s1, "S1_ci90": [l1, h1], "S1_outcome": s1o,
            "S4_descriptive": float(np.mean(s4)), "S4_ci95": [pct(np.mean(s4[idx], 1), 2.5), pct(np.mean(s4[idx], 1), 97.5)],
            "S3_descriptive": float(np.nanmean(s3)), "S3_ci95": [pct(np.nanmean(s3[idx], 1), 2.5), pct(np.nanmean(s3[idx], 1), 97.5)],
            "S3_caveat": S3_CAVEAT,
            "half_width_mu": (hi - lo) / 2}


# ---------------------------------------------------------------- Frechet distance (left-hand features)
def frechet(x, mu_r, cov_r):
    mu, cov = x.mean(0), np.cov(x, rowvar=False)
    s = linalg.sqrtm(cov @ cov_r)
    s = s.real if np.iscomplexobj(s) else s
    return float(((mu - mu_r) ** 2).sum() + np.trace(cov + cov_r - 2 * s))


# ---------------------------------------------------------------- T5-B / T6 dominance levels (§6.5)
def dominance(cond, a0, a0p, ref, phi_ref, sigma, idx, delta_s2):
    """cond/a0/a0p: per-condition data dicts; ref: dict A_L, A_R, X arrays [J] (dev references of the 32 clips);
    phi_ref: [256, 30] dev-256 reference left-hand features. Returns D-a, D-b, D-c, T6 and suppression flags."""
    J = len(ref["X"])
    mu_r, cov_r = phi_ref.mean(0), np.cov(phi_ref, rowvar=False)

    def point(data, rows):
        xb = cmean(data["X"])[rows]
        cl = np.nanmedian(np.log(data["A_L"][rows] / ref["A_L"][rows, None]), axis=1)
        cr = np.nanmedian(np.log(data["A_R"][rows] / ref["A_R"][rows, None]), axis=1)
        return {"m": np.nanmean(xb), "e_L": abs(np.nanmean(cl)), "e_R": abs(np.nanmean(cr)), "m_L": np.nanmean(cl),
                "jerk_L": np.nanmean(cmean(data["m3_jerk_L"])[rows]), "jerk_R": np.nanmean(cmean(data["m3_jerk_R"])[rows]),
                "ext_L": np.nanmean(cmean(data["extreme_frac_L"])[rows]), "ext_R": np.nanmean(cmean(data["extreme_frac_R"])[rows]),
                "lr": np.nanmean(cmean(data["coord_lr"])[rows]),
                "FD": frechet(data["phi_L"][rows].reshape(-1, data["phi_L"].shape[-1]), mu_r, cov_r),
                **{k: np.nanmean(cmean(data[k])[rows]) for k in T2_METRICS if k.endswith("_R")}}

    def derived(pc, pa, pp, t32):
        d = np.sign(t32 - pa["m"])
        return {"t32": t32, "dir_gap": t32 - pa["m"], "d": d, "delta": pc["m"] - pa["m"],
                "g_c": abs(pc["m"] - t32), "g_a": abs(pa["m"] - t32), "rho_g": abs(pc["m"] - t32) / max(abs(pa["m"] - t32), 1e-12),
                "m_minus_t": pc["m"] - t32, "de_L": pc["e_L"] - pa["e_L"], "de_R": pc["e_R"] - pa["e_R"], "m_L": pc["m_L"],
                "jerk_ratio_L": pc["jerk_L"] / pa["jerk_L"], "ext_diff_L": pc["ext_L"] - pa["ext_L"],
                "jerk_ratio_R": pc["jerk_R"] / pa["jerk_R"], "ext_diff_R": pc["ext_R"] - pa["ext_R"],
                "lr_diff": pc["lr"] - pa["lr"], "FD_diff": pc["FD"] - pa["FD"], "FDp_diff": pp["FD"] - pa["FD"],
                **{f"ratio_{k}": pc[k] / pa[k] for k in T2_METRICS if k.endswith("_R")}}

    rows = np.arange(J)
    pt = derived(point(cond, rows), point(a0, rows), point(a0p, rows), float(np.mean(ref["X"])))
    reps = [derived(point(cond, r), point(a0, r), point(a0p, r), float(np.mean(ref["X"][r]))) for r in idx]
    R = {k: np.array([r[k] for r in reps]) for k in reps[0]}

    d = pt["d"]
    assessable_a = not (pct(R["dir_gap"], 2.5) <= 0 <= pct(R["dir_gap"], 97.5))
    da = {"assessable": assessable_a, "direction": float(d), "delta": pt["delta"],
          "delta_ci95": [pct(R["delta"], 2.5), pct(R["delta"], 97.5)], "t32": pt["t32"],
          "t32_minus_mA0_ci95": [pct(R["dir_gap"], 2.5), pct(R["dir_gap"], 97.5)]}
    da["pass"] = bool(assessable_a and np.sign(pt["delta"]) == d and abs(pt["delta"]) >= 0.10
                      and not (da["delta_ci95"][0] <= 0 <= da["delta_ci95"][1]))
    assessable_b = pct(R["g_a"], 2.5) >= 0.10
    db = {"assessable": bool(assessable_b), "g_A0": pt["g_a"], "g_A0_ci95_lo": pct(R["g_a"], 2.5), "g_cond": pt["g_c"],
          "rho_g": pt["rho_g"], "rho_g_upper95": pct(R["rho_g"], 95),
          "closer": bool(assessable_b and pct(R["rho_g"], 95) <= 0.50),
          "at_target_ci90": [pct(R["m_minus_t"], 5), pct(R["m_minus_t"], 95)],
          "overshoot": bool(d * (pt["m_minus_t"]) > 0.10)}
    db["at_target"] = bool(-delta_s2 <= db["at_target_ci90"][0] and db["at_target_ci90"][1] <= delta_s2)
    q95 = pct(R["FDp_diff"], 95)
    left = {"jerk_ratio": pt["jerk_ratio_L"], "jerk_ratio_upper95": pct(R["jerk_ratio_L"], 95),
            "extreme_diff": pt["ext_diff_L"], "extreme_diff_upper95": pct(R["ext_diff_L"], 95),
            "FD_diff": pt["FD_diff"], "FD_q95_A0p_minus_A0": q95,
            "coord_lr_diff": pt["lr_diff"], "coord_lr_diff_lower95": pct(R["lr_diff"], 5)}
    left["pass"] = bool(left["jerk_ratio_upper95"] <= 1.10 and left["extreme_diff_upper95"] <= 0.02
                        and left["FD_diff"] <= q95 and left["coord_lr_diff_lower95"] >= -0.03)
    if sigma[1] == 1.0:  # right hand unchanged in theory: TOST +-5% on the four right-hand T2 metrics
        right = {k: {"ratio": pt[f"ratio_{k}"], "ci90": [pct(R[f"ratio_{k}"], 5), pct(R[f"ratio_{k}"], 95)]}
                 for k in T2_METRICS if k.endswith("_R")}
        right["pass"] = all(0.95 <= v["ci90"][0] and v["ci90"][1] <= 1.05 for v in right.values())
    else:
        right = {"jerk_ratio": pt["jerk_ratio_R"], "jerk_ratio_upper95": pct(R["jerk_ratio_R"], 95),
                 "extreme_diff": pt["ext_diff_R"], "extreme_diff_upper95": pct(R["ext_diff_R"], 95)}
        right["pass"] = bool(right["jerk_ratio_upper95"] <= 1.10 and right["extreme_diff_upper95"] <= 0.02)
    calib = {"de_L_upper95": pct(R["de_L"], 95), "de_R_upper95": pct(R["de_R"], 95),
             "m_L": pt["m_L"], "m_L_lower95": pct(R["m_L"], 5)}
    c_i = calib["de_L_upper95"] <= 0.05 and calib["de_R_upper95"] <= 0.05
    c_ii = calib["m_L"] >= LOG08 and calib["m_L_lower95"] >= LOG075
    dc = {"i_side_calibration": bool(c_i), "ii_left_floor": bool(c_ii), "iii_left_checks": left["pass"],
          "iv_right_checks": right["pass"]}
    dc["pass"] = bool(da["pass"] and db["closer"] and not db["overshoot"] and c_i and c_ii and left["pass"] and right["pass"])
    return {"D_a": da, "D_b": db, "D_c": dc, "calibration": calib, "T6_left": left, "T6_right": right,
            "suppression": bool(da["pass"] and (not c_ii or not left["pass"])),
            "moved_not_closer": bool(da["pass"] and not db["closer"])}


# ---------------------------------------------------------------- T1 noise-level checks (torch, GPU)
# Registered initial margins (§15.4.1 l. 1104-1108). var is the half-width around 1.
T1_MARGINS = {"mean": 0.03, "var": 0.05, "corr": 0.035, "cross": 0.035, "lag1": 0.03}
# Registered caps (§15.4.1 l. 1112: "mean 0.05, variance [0.90, 1.10], correlation 0.05"). "cross" is under the
# correlation cap by interpretation (P-1: unit-variance channels, so the cross-covariance is a correlation).
# lag1 has NO registered cap and is never widened (P-1).
T1_CAPS = {"mean": 0.05, "var": 0.10, "corr": 0.05, "cross": 0.05}
T1_PROCEDURE = ("pre-run calibration procedure (preflight P-1; NOT a registered criterion): each round raises by 0.005 "
                "every widenable check (mean, var, corr, cross) whose own null failure rate is >= 0.25%, never beyond "
                "its registered cap; lag-1 stays at the registered 0.03; if the family-wise null rate is still >= 1%, "
                "E2e stops before any generation")


def t1_stats(X, pairs_a, pairs_b, blocks, cross):
    """X: [n, 240] realised frames (float64 torch); pairs_a/pairs_b: index tensors of consecutive active frames;
    blocks: {name: slice}; cross: list of (row_slice, col_slice, design_matrix or None).
    Returns the raw statistic per check (the worst case over channels / entries)."""
    import torch
    n = X.shape[0]
    mean = X.mean(0)
    sd = X.std(0)
    mean_stat = (mean.abs() + 1.645 * sd / n ** 0.5).max().item()          # CI must lie inside [-m, m]
    var = X.var(0)
    lo_q, hi_q = chi2.ppf(0.95, n - 1), chi2.ppf(0.05, n - 1)
    var_lo, var_hi = ((n - 1) * var / lo_q), ((n - 1) * var / hi_q)
    var_stat = max((1 - var_lo).max().item(), (var_hi - 1).max().item())   # CI must lie inside [1-m, 1+m]
    Xc = X - mean
    corr_stat = 0.0
    for sl in blocks.values():
        c = torch.corrcoef(Xc[:, sl].T)
        c = c - torch.diag(torch.diag(c))
        corr_stat = max(corr_stat, c.abs().max().item())
    cross_stat = 0.0
    for rs, cs, K in cross:
        C = Xc[:, rs].T @ Xc[:, cs] / (n - 1)
        D = C - (torch.as_tensor(K, dtype=X.dtype, device=X.device) if K is not None else 0)
        cross_stat = max(cross_stat, D.abs().max().item())
    a, b = Xc[pairs_a], Xc[pairs_b]
    r1 = (a * b).mean(0) / Xc.var(0)
    lag_stat = (r1.abs() + 1.645 / len(pairs_a) ** 0.5).max().item()
    return {"mean": mean_stat, "var": var_stat, "corr": corr_stat, "cross": cross_stat, "lag1": lag_stat}


def t1_pass(stats, margins):
    return {k: stats[k] <= margins[k] for k in margins}


def t1_calibrate(null_stats, margins=None, step=0.005):
    """null_stats: list of stat dicts from pure N(0, I) sets. Registered target: family-wise false-failure < 1%.
    Widening follows T1_PROCEDURE (preflight P-1, new): only checks with a registered cap widen; lag-1 never does."""
    m = dict(margins or T1_MARGINS)
    hist = []
    while True:
        fails = np.array([[s[k] > m[k] for k in m] for s in null_stats])
        fw = float(fails.any(1).mean())
        per = dict(zip(m, fails.mean(0)))
        hist.append({"margins": dict(m), "fw_rate": fw, "per_check": {k: float(v) for k, v in per.items()}})
        if fw < 0.01:
            return {"margins": m, "fw_rate": fw, "calibrated": True, "history": hist, "procedure": T1_PROCEDURE,
                    "registered_initial": dict(T1_MARGINS), "registered_caps": dict(T1_CAPS)}
        grow = [k for k in T1_CAPS if per[k] >= 0.0025 and m[k] < T1_CAPS[k] - 1e-12]
        if not grow:
            return {"margins": m, "fw_rate": fw, "calibrated": False, "history": hist, "procedure": T1_PROCEDURE,
                    "registered_initial": dict(T1_MARGINS), "registered_caps": dict(T1_CAPS)}
        for k in grow:
            m[k] = min(T1_CAPS[k], round(m[k] + step, 6))


# ---------------------------------------------------------------- energy distance (non-gating diagnostic)
def energy_distance(fc, fa, clip_c, clip_a, n_perm=1000, seed=0):
    """fc, fa: [N, d] standardised per-sample feature vectors; within-clip label permutation test."""
    X = np.vstack([fc, fa])
    lab = np.r_[np.ones(len(fc), bool), np.zeros(len(fa), bool)]
    clips = np.r_[clip_c, clip_a]
    Dm = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))

    def ed(l):
        return 2 * Dm[l][:, ~l].mean() - Dm[l][:, l].mean() - Dm[~l][:, ~l].mean()

    obs = ed(lab)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n_perm):
        p = lab.copy()
        for c in np.unique(clips):
            ix = np.where(clips == c)[0]
            p[ix] = rng.permutation(p[ix])
        cnt += ed(p) >= obs
    return {"energy_distance": float(obs), "p_perm": (cnt + 1) / (n_perm + 1)}
