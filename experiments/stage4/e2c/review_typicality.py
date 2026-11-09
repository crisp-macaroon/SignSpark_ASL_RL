"""C-c3 final review on SYNTHETIC arrays only (no model, no dataset, no generation, no campaign seeds).

  1 null calibration per clip length: per-constraint and family violation rates with Wilson CIs; per-channel lag-1
    tail probability from pooled channels; moments of r_c vs the asymptotic N(0, 1/L)
  2 joint M/V/N projection: alternating 5-iteration scheme vs exact one-shot scheme, on null violators and on
    adversarial (optimiser-like) perturbations
  3 A/P repair by penalty descent + exact projection: success rate (safe failure otherwise)
  4 projection bias: how much E-4 changes the initial-noise population

    python -E -s experiments/stage4/e2c/review_typicality.py --out experiments/stage4/e2c/typicality_review.json
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import norm

import typicality as T

LENGTHS = [157, 56, 139, 171, 189, 99, 116, 263, 212, 67, 248, 84, 71, 177, 83, 85, 102, 47, 219, 120, 220, 71,
           159, 125, 304, 174, 132, 28, 304, 252, 78, 146]
NOM = {"M": 1 - (1 - T.FAM["M"] / T.C) ** T.C, "V": 1 - (1 - T.FAM["V"] / T.C) ** T.C,
       "A": 1 - (1 - T.FAM["A"] / T.C) ** T.C, "P": T.FAM["P"]}
NOM["any"] = 1 - np.prod([1 - v for v in NOM.values()])


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def part1(rng, n_per_L=16000, chunk=2000):
    out = {}
    zb = norm.ppf(1 - 0.05 / len(set(LENGTHS)))  # one-sided, Bonferroni over lengths
    for L in sorted(set(LENGTHS)):
        b = T.bounds(L)
        cnt = {k: 0 for k in ("M", "V", "A", "P", "any")}
        a_tail, r_sum, r_sq, r_n = 0, 0.0, 0.0, 0
        for _ in range(n_per_L // chunk):
            x = rng.standard_normal((chunk, T.C, L), dtype=np.float32).astype(np.float64)
            v = T.violations(T.stats(x), b)
            for k in ("M", "V", "A", "P"):
                cnt[k] += int(v[k].sum())
            cnt["any"] += int(np.any(np.stack(list(v.values())), 0).sum())
            r = (x[..., 1:] * x[..., :-1]).sum(-1) / (x ** 2).sum(-1)
            a_tail += int((np.abs(r) > b["lag1"]).sum())
            r_sum += float(r.sum()); r_sq += float((r ** 2).sum()); r_n += r.size
        rate = {k: cnt[k] / n_per_L for k in cnt}
        ci = {k: wilson(cnt[k], n_per_L) for k in cnt}
        p_a = a_tail / r_n
        var_r = r_sq / r_n - (r_sum / r_n) ** 2
        # implied family rates from pooled-channel estimates (channels independent)
        implied_A = 1 - (1 - p_a) ** T.C
        sd_pool = np.sqrt(var_r / T.C)
        implied_P = 2 * norm.sf(b["lag1_pooled"] / sd_pool)
        se_any = np.sqrt(NOM["any"] * (1 - NOM["any"]) / n_per_L)
        out[L] = {"rates": rate, "ci95": ci, "p_channel_A": p_a, "p_channel_A_nominal": T.FAM["A"] / T.C,
                  "p_channel_A_se": float(np.sqrt(p_a * (1 - p_a) / r_n)),
                  "implied_A_family": implied_A, "implied_P": float(implied_P),
                  "r_mean": r_sum / r_n, "r_var": var_r, "r_var_asymptotic_1_over_L": 1 / L, "r_var_exactish_(L-1)/L^2": (L - 1) / L ** 2,
                  "z_any_vs_nominal": (rate["any"] - NOM["any"]) / se_any,
                  "significantly_above_nominal_bonferroni": bool((rate["any"] - NOM["any"]) / se_any > zb)}
        print(L, {k: round(v, 4) for k, v in rate.items()}, "pA", f"{p_a:.2e}", "z_any", round(out[L]["z_any_vs_nominal"], 2), flush=True)
    return out


def perturb(x, rng, kind):
    y = x.copy()
    C = x.shape[0]
    if kind in ("offset", "combined"):
        ch = rng.choice(C, 5, replace=False)
        y[ch] += rng.uniform(0.3, 1.0, (5, 1)) * rng.choice([-1, 1], (5, 1))
    if kind in ("scale", "combined"):
        ch = rng.choice(C, 10, replace=False)
        y[ch] *= rng.uniform(0.3, 2.5, (10, 1))
    if kind in ("global", "combined"):
        y *= 1.3
    return y


def part2(rng, n=500):
    res = {}
    for L in (28, 56, 146, 304):
        b = T.bounds(L)
        res[L] = {}
        for kind in ("null_violators", "offset", "scale", "global", "combined"):
            ok_alt = ok_ex = mvn_alt = mvn_ex = 0
            tot = 0
            while tot < n:
                x = rng.standard_normal((T.C, L))
                n2 = float((x ** 2).sum())
                if kind == "null_violators":
                    v = T.violations(T.stats(x[None]), b)
                    if not (v["M"][0] or v["V"][0]):
                        continue
                    y = x
                else:
                    y = perturb(x, rng, kind)
                tot += 1
                ya = T.project_mvn_alternating(y, b, n2)
                fa = T.feasible(ya, b, n2)[1]
                mvn_alt += not (fa["M"] or fa["V"] or fa["N"])
                ye, okp = T.project_mvn_exact(y, b, n2)
                fe = T.feasible(ye, b, n2)[1]
                mvn_ex += okp and not (fe["M"] or fe["V"] or fe["N"])
            res[L][kind] = {"n": tot, "alternating5_MVN_feasible": mvn_alt / tot, "exact_MVN_feasible": mvn_ex / tot}
            print(L, kind, res[L][kind], flush=True)
    return res


def part3(rng, n=60):
    res = {}
    for L in (28, 56, 146, 304):
        b = T.bounds(L)
        res[L] = {}
        for kind in ("null_AP_violators", "AR(1) 0.3 all channels"):
            succ, steps, rel = 0, [], []
            tot = 0
            while tot < n:
                x = rng.standard_normal((T.C, L))
                n2 = float((x ** 2).sum())
                if kind == "null_AP_violators":
                    v = T.violations(T.stats(x[None]), b)
                    if not (v["A"][0] or v["P"][0]):
                        continue
                    y = x
                else:
                    y = x.copy()
                    for t in range(1, L):
                        y[:, t] = 0.3 * y[:, t - 1] + np.sqrt(0.91) * x[:, t]
                    n2 = float((y ** 2).sum())
                tot += 1
                y0, okp = T.project_mvn_exact(y, b, n2)
                z, ok, k = T.repair_ap(y0 if okp else y, b, n2)
                ok = ok and T.feasible(z, b, n2)[0]
                succ += ok
                if ok:
                    steps.append(k); rel.append(float(np.linalg.norm(z - y) / np.linalg.norm(y)))
            res[L][kind] = {"n": tot, "success": succ / tot, "median_steps": float(np.median(steps)) if steps else None,
                            "median_rel_change": float(np.median(rel)) if rel else None,
                            "max_rel_change": float(np.max(rel)) if rel else None}
            print(L, kind, res[L][kind], flush=True)
    return res


def part4(rng, n_per_L=600):
    """Population effect of E-4 on initial noise at the real clip lengths."""
    mod, rel, unrepaired = 0, [], 0
    pre, post = {k: [] for k in ("mean", "var_min", "var_max", "lag1", "lag1_pooled")}, {k: [] for k in ("mean", "var_min", "var_max", "lag1", "lag1_pooled")}
    tot = 0
    for L in LENGTHS:
        b = T.bounds(L)
        for _ in range(n_per_L):
            x = rng.standard_normal((T.C, L))
            n2 = float((x ** 2).sum())
            tot += 1
            ok, _ = T.feasible(x, b, n2)
            z = x
            if not ok:
                mod += 1
                y, okp = T.project_mvn_exact(x, b, n2)
                z, okr, _ = T.repair_ap(y if okp else x, b, n2)
                if not (okr and T.feasible(z, b, n2)[0]):
                    unrepaired += 1
                    z = x
                rel.append(float(np.linalg.norm(z - x) / np.linalg.norm(x)))
            s0, s1 = T.stats(x[None]), T.stats(z[None])
            for k in pre:
                pre[k].append(float(s0[k][0]) * (np.sqrt(L) if k in ("mean", "lag1") else 1))
                post[k].append(float(s1[k][0]) * (np.sqrt(L) if k in ("mean", "lag1") else 1))
    from scipy.stats import ks_2samp
    ks = {k: float(ks_2samp(pre[k], post[k]).statistic) for k in pre}
    sample_rel = np.array(rel + [0.0] * (tot - mod))
    return {"n": tot, "fraction_modified": mod / tot, "unrepaired": unrepaired,
            "rel_change_among_modified": {"median": float(np.median(rel)) if rel else None,
                                          "p95": float(np.percentile(rel, 95)) if rel else None,
                                          "max": float(np.max(rel)) if rel else None},
            "rel_change_population_mean": float(sample_rel.mean()),
            "KS_pre_vs_post_by_statistic(L-scaled mean, lag1)": ks,
            "P(at least one of 8 raw candidates atypical) at this rate": float(1 - (1 - mod / tot) ** 8)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rng = np.random.default_rng(97531)  # review seed, unrelated to any campaign seed
    t0 = time.time()
    res = {"nominal": NOM}
    res["part1_null_calibration"] = part1(rng)
    res["part2_mvn_projection"] = part2(rng)
    res["part3_ap_repair"] = part3(rng)
    res["part4_projection_bias"] = part4(rng)
    res["seconds"] = round(time.time() - t0)
    Path(args.out).write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(json.dumps(res["part4_projection_bias"], indent=1))


if __name__ == "__main__":
    main()
