"""Stage 5 ACMS pilot: held-out evaluation (design §4, A6). Dev-256 clips x 4 eval noises (base 40,000,000), three
conditions on COMMON noise: uncoupled (mu = 0), initial controller (update 0), trained controller (final; no
selection). Primary space R v1.1; J v1.1 descriptive only (never combined with R). No test data.

Pre-registered interpretation (fixed before the run; config "evaluation"):
  positive      trained - uncoupled right arm-hand coordination (R): 95% clip-bootstrap CI lower bound > 0, AND all
                preservation checks pass (mean articulation ratio in [0.9, 1.1]; mean jerk ratio <= 1.10; mean extreme-
                frame difference <= 0.02; |mean log activity ratio| <= log 1.25; undefined fraction <= uncoupled + 0.005;
                max KL <= 1 nat/frame)
  inconclusive  CI lower bound > 0 but any check fails
  negative      CI lower bound <= 0
Reported separately (no criterion): attainment of 0.05 (point and CI lower bound), gap closure toward tau = 0.4514.

  python -E -s experiments/stage5/evaluate.py --config experiments/stage5/config_500ep.json \
      --ckpt-init experiments/stage5/out/train/checkpoints/update_000.pt \
      --ckpt-final experiments/stage5/out/train/checkpoints/update_125.pt --out experiments/stage5/out/eval
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common5 as C  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

import acms_policy as P  # noqa: E402
import episode_sampler as ES  # noqa: E402
import rewards as RW  # noqa: E402
import typicality as TY  # noqa: E402  (C-c3 statistics; descriptive monitor only)
from train_500ep import load_config, make_policy  # noqa: E402

CONDS = ("uncoupled", "initial", "trained")
R_STATS = ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "dom_X")
J_STATS = ("coord_ah_J_R", "coord_ah_J_L", "coord_lr_J", "dom_J")
PAIRS = (("trained", "uncoupled"), ("trained", "initial"), ("initial", "uncoupled"))


def load_policy(cfg, path):
    pol = make_policy(cfg)
    pol.load_state_dict(torch.load(path, map_location="cpu", weights_only=False)["policy"])
    return pol.cuda().eval()


def j_context():
    sys.path.append(str(C.ROOT / ".venv-render" / "Lib" / "site-packages"))  # smplx only (as R0)
    import jspace as JS
    return JS.load_model()


def j_record(jctx, xb, xl, xr, L):
    b6, l6, r6 = xb[:, :L].T, xl[:, :L].T, xr[:, :L].T
    st = C.V.j_stats(jctx, b6, l6, r6)
    rec = {k: float(st[k]) for k in J_STATS}
    rec["valid"] = st["valid"]
    sig = C.V.j_signals(jctx, b6, l6, r6) if st["valid"].get("fk_finite", False) else None
    leak = C.V.j_signals(jctx, b6, l6, np.repeat(r6[:1], L, 0)) if sig is not None else None
    if sig is not None and leak is not None and sig["hand_R"].mean() > 0:
        rec["leak_ratio_R"] = float(leak["hand_R"].mean() / sig["hand_R"].mean())
    else:
        rec["leak_ratio_R"] = float("nan")
    return rec


def typ_monitor(x):
    """C-c3 M/V/A/P violation flags of one right-hand noise array (90, L) (descriptive; not a constraint)."""
    b = TY.bounds(x.shape[1])
    s = TY.stats(x[None].astype(np.float64))
    v = TY.violations(s, b)
    return {k: bool(np.asarray(v[k])[0]) for k in v}


def generate(cfg, args, ctx, pols, jctx):
    n_clips, K, base = args.n_clips, args.n_noises, cfg["seeds"]["eval_noise_base"]
    recs, dumps = [], {c: [] for c in ("body", "left") + CONDS}
    for c0 in range(0, n_clips, 32):
        idx = list(range(c0, min(n_clips, c0 + 32)))
        n = len(idx)
        prep = ctx.batch("dev", idx)
        metas = [ctx.meta("dev", j) for j in idx]
        Ls = [m["L"] for m in metas]
        for k in range(1, K + 1):
            nz = [ES.eval_noise(base, j, k) for j in idx]
            eb = torch.stack([z[:60] for z in nz]).cuda()
            el = torch.stack([z[60:150] for z in nz]).cuda()
            xi = torch.stack([z[150:240] for z in nz]).cuda()
            xb = ctx.gen("body", prep, list(range(n)), eb).cpu().numpy()
            feats = [C.arm_feature(xb[a], Ls[a]) for a in range(n)]
            s_hat = torch.as_tensor(np.stack([f for f, _ in feats])).cuda()
            with torch.no_grad():
                mu = {"uncoupled": torch.zeros_like(xi), "initial": pols["initial"].mu(s_hat, Ls),
                      "trained": pols["trained"].mu(s_hat, Ls)}
            eps = {c: xi + mu[c] for c in CONDS}
            left_rows, right_rows = [2 * a for a in range(n)], [2 * a + 1 for a in range(n)]
            h1 = ctx.gen("hand", prep, left_rows + right_rows, torch.cat([el, eps["uncoupled"]])).cpu().numpy()
            h2 = ctx.gen("hand", prep, right_rows + right_rows, torch.cat([eps["initial"], eps["trained"]])).cpu().numpy()
            xl, xr = h1[:n], {"uncoupled": h1[n:], "initial": h2[:n], "trained": h2[n:]}
            kl = {c: P.ACMS.kl_per_frame(mu[c], Ls).cpu().numpy() for c in CONDS}
            if args.save_dumps:
                dumps["body"].append(xb); dumps["left"].append(xl)
                for c in CONDS:
                    dumps[c].append(xr[c])
            for a, j in enumerate(idx):
                L = Ls[a]
                for c in CONDS:
                    r = {"clip": j, "name": metas[a]["name"], "L": L, "k": k, "cond": c,
                         "seed": base + 1000 * j + k, "arm_feature_valid": bool(feats[a][1]),
                         "kl_per_frame": float(kl[c][a]), "R": RW.r_record(xb[a], xl[a], xr[c][a], L),
                         "typicality": typ_monitor(eps[c][a, :, :L].cpu().numpy())}
                    if jctx is not None:
                        r["J"] = j_record(jctx, xb[a], xl[a], xr[c][a], L)
                    recs.append(r)
        print(f"clips {c0}-{c0 + n - 1} done ({len(recs)} records)", flush=True)
    return recs, dumps


# ---------------------------------------------------------------------------------------------------- analysis
def boot(v, B, seed):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return {"mean": None, "ci95": [None, None], "n": 0}
    idx = np.random.default_rng(seed).integers(0, len(v), (B, len(v)))
    m = v[idx].mean(1)
    return {"mean": float(v.mean()), "median": float(np.median(v)), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            "n": int(len(v))}


def table(recs, get):
    """{cond: array [n_clips, K]} of a per-sample value (NaN = undefined)."""
    clips = sorted({r["clip"] for r in recs})
    K = max(r["k"] for r in recs)
    ci = {c: i for i, c in enumerate(clips)}
    out = {c: np.full((len(clips), K), np.nan) for c in CONDS}
    for r in recs:
        out[r["cond"]][ci[r["clip"]], r["k"] - 1] = get(r)
    return out, clips


def clip_mean(a):
    with np.errstate(all="ignore"):
        ok = np.isfinite(a).any(1)
        m = np.full(a.shape[0], np.nan)
        m[ok] = np.nanmean(a[ok], 1)
    return m


def describe(t, B, seed):
    out = {}
    for c in CONDS:
        v = t[c]
        d = v[np.isfinite(v)]
        out[c] = {"mean": float(d.mean()) if len(d) else None, "median": float(np.median(d)) if len(d) else None,
                  "n_defined": int(len(d)), "n_undefined": int(np.isnan(v).sum()), "undefined_fraction": float(np.isnan(v).mean()),
                  "clip_mean": boot(clip_mean(v), B, seed),
                  "per_clip_quantiles": {q: float(np.nanpercentile(clip_mean(v), q)) for q in (0, 10, 25, 50, 75, 90, 100)}
                  if np.isfinite(clip_mean(v)).any() else None}
    for a, b in PAIRS:
        d = t[a] - t[b]  # paired per sample (common noise); NaN if either undefined
        out[f"{a}-{b}"] = {"paired_clip_mean": boot(clip_mean(d), B, seed), "sample_median": float(np.nanmedian(d)) if np.isfinite(d).any() else None,
                           "n_pairs": int(np.isfinite(d).sum()), "per_clip": clip_mean(d).tolist()}
    return out


def analyse(recs, cfg):
    ev = cfg["evaluation"]
    B, seed = ev["bootstrap"]["B"], ev["bootstrap"]["seed"]
    pres = ev["preservation"]
    res = {"label": cfg["label"], "n_records": len(recs), "R_space": {}, "J_space_descriptive": {}}
    for s in R_STATS:
        t, clips = table(recs, lambda r, s=s: r["R"][s])
        res["R_space"][s] = describe(t, B, seed)
    res["clips"] = clips
    # per-stream statistics (both hands), per condition and paired vs uncoupled
    streams = {}
    for side in ("hand_R", "hand_L"):
        for k in RW.HAND_KEYS:
            t, _ = table(recs, lambda r, side=side, k=k: r["R"][side][k])
            streams[f"{side}.{k}"] = {c: {"mean": float(np.nanmean(t[c])), "median": float(np.nanmedian(t[c]))} for c in CONDS}
            streams[f"{side}.{k}"]["left_identical_across_conditions"] = bool(
                side == "hand_L" and all(np.array_equal(t[c], t["uncoupled"], equal_nan=True) for c in CONDS)) if side == "hand_L" else None
    res["per_stream"] = streams
    # validity flags
    flags = {}
    for c in CONDS:
        rc = [r for r in recs if r["cond"] == c]
        keys = sorted({k for r in rc for k in r["R"]["valid"]})
        flags[c] = {k: int(sum(not r["R"]["valid"].get(k, False) for r in rc)) for k in keys}
        flags[c]["arm_feature_invalid"] = int(sum(not r["arm_feature_valid"] for r in rc))
    res["validity_flags_false_counts"] = flags
    # KL and typicality monitor
    res["kl_per_frame"] = {c: {"mean": float(np.mean([r["kl_per_frame"] for r in recs if r["cond"] == c])),
                               "max": float(np.max([r["kl_per_frame"] for r in recs if r["cond"] == c]))} for c in CONDS}
    res["typicality_monitor_fraction"] = {c: {k: float(np.mean([r["typicality"][k] for r in recs if r["cond"] == c]))
                                              for k in ("M", "V", "A", "P")} for c in CONDS}
    # preservation checks: trained vs uncoupled, right hand, paired per sample
    def ratio(key):
        t, _ = table(recs, lambda r: r["R"]["hand_R"][key])
        with np.errstate(all="ignore"):
            return t["trained"] / t["uncoupled"], t
    art, _ = ratio("m2_artic")
    jerk, _ = ratio("m3_jerk")
    act, _ = ratio("A")
    with np.errstate(all="ignore"):
        logact = np.log(act)
    te, _ = table(recs, lambda r: r["R"]["hand_R"]["extreme_frac"])
    ext = te["trained"] - te["uncoupled"]
    tc = res["R_space"]["coord_arm_rhand"]
    und_tr, und_un = tc["trained"]["undefined_fraction"], tc["uncoupled"]["undefined_fraction"]
    checks = {
        "artic_ratio_mean": {"value": float(np.nanmean(art)), "band": pres["artic_ratio_band"],
                             "pass": bool(pres["artic_ratio_band"][0] <= np.nanmean(art) <= pres["artic_ratio_band"][1])},
        "jerk_ratio_mean": {"value": float(np.nanmean(jerk)), "max": pres["jerk_ratio_max"], "pass": bool(np.nanmean(jerk) <= pres["jerk_ratio_max"])},
        "extreme_diff_mean": {"value": float(np.nanmean(ext)), "max": pres["extreme_diff_max"], "pass": bool(np.nanmean(ext) <= pres["extreme_diff_max"])},
        "abs_mean_log_activity_ratio": {"value": float(abs(np.nanmean(logact))), "max": float(np.log(pres["abs_log_activity_ratio_max_log"])),
                                        "pass": bool(abs(np.nanmean(logact)) <= np.log(pres["abs_log_activity_ratio_max_log"]))},
        "undefined_fraction": {"trained": und_tr, "uncoupled": und_un, "max_excess": pres["undefined_excess_max"],
                               "pass": bool(und_tr <= und_un + pres["undefined_excess_max"])},
        "kl_max": {"value": res["kl_per_frame"]["trained"]["max"], "max": pres["kl_max_nats_per_frame"],
                   "pass": bool(res["kl_per_frame"]["trained"]["max"] <= pres["kl_max_nats_per_frame"])},
    }
    res["preservation_checks_trained_vs_uncoupled"] = checks
    # pre-registered verdict
    d = tc["trained-uncoupled"]["paired_clip_mean"]
    lo = d["ci95"][0]
    all_pass = all(v["pass"] for v in checks.values())
    if lo is None or lo <= 0:
        verdict = "negative"
    else:
        verdict = "positive" if all_pass else "inconclusive"
    thr = ev["threshold_reported_separately"]
    unc_mean = tc["uncoupled"]["clip_mean"]["mean"]
    res["verdict"] = {
        "pre_registered": verdict,
        "paired_improvement_trained_minus_uncoupled": d,
        "all_preservation_checks_pass": all_pass,
        "threshold_0.05_reported_separately": {"point_estimate_ge": bool(d["mean"] is not None and d["mean"] >= thr),
                                               "ci_lower_ge": bool(lo is not None and lo >= thr)},
        "gap_closure_toward_tau": (float(d["mean"] / (RW.TAU - unc_mean)) if d["mean"] is not None and unc_mean is not None else None),
        "tau_ah_R": RW.TAU, "A3_context_best_of_8x8_256": 0.408}
    # S-4 worst-case sensitivity: trained undefined -> -1, uncoupled undefined -> +1
    t, _ = table(recs, lambda r: r["R"]["coord_arm_rhand"])
    tw, uw = np.where(np.isnan(t["trained"]), -1.0, t["trained"]), np.where(np.isnan(t["uncoupled"]), 1.0, t["uncoupled"])
    res["s4_worst_case_trained_minus_uncoupled"] = boot((tw - uw).mean(1), B, seed)
    # J descriptive
    if all("J" in r for r in recs):
        for s in J_STATS:
            t, _ = table(recs, lambda r, s=s: r["J"][s])
            res["J_space_descriptive"][s] = describe(t, B, seed)
        t, _ = table(recs, lambda r: r["J"]["leak_ratio_R"])
        res["J_space_descriptive"]["leak_ratio_R"] = {c: {"median": float(np.nanmedian(t[c])), "p95": float(np.nanpercentile(t[c], 95)),
                                                          "n_gt_0.1": int(np.nansum(t[c] > 0.1))} for c in CONDS}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ckpt-init", required=True)
    ap.add_argument("--ckpt-final", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-clips", type=int, default=None)
    ap.add_argument("--n-noises", type=int, default=None)
    ap.add_argument("--no-j", action="store_true")
    ap.add_argument("--save-dumps", action="store_true")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    ev = cfg["evaluation"]
    args.n_clips = args.n_clips or ev["n_clips"]
    args.n_noises = args.n_noises or ev["n_noises"]
    if not cfg.get("test_mode", False):
        assert (args.n_clips, args.n_noises) == (ev["n_clips"], ev["n_noises"]), "approved protocol: dev-256 x 4"
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    ctx = C.Ctx5({"dev": list(range(args.n_clips))})
    w0 = ctx.weight_checksum()
    pols = {"initial": load_policy(cfg, args.ckpt_init), "trained": load_policy(cfg, args.ckpt_final)}
    jctx = None if args.no_j else j_context()
    recs, dumps = generate(cfg, args, ctx, pols, jctx)
    (out / "eval_samples.json").write_text(json.dumps(recs, default=float), encoding="utf-8")
    if args.save_dumps:
        np.savez(out / "eval_dumps.npz", **{k: np.concatenate(v) for k, v in dumps.items() if v})
    res = analyse(recs, cfg)
    res["run"] = {"checkpoints": {"initial": str(args.ckpt_init), "trained": str(args.ckpt_final),
                                  "sha256": {"initial": C.sha256(args.ckpt_init), "trained": C.sha256(args.ckpt_final)}},
                  "n_clips": args.n_clips, "n_noises": args.n_noises, "flags": ctx.flags(), "opened_splits": list(C.OPENED_SPLITS),
                  "model_weights_unchanged": w0 == ctx.weight_checksum(), "seconds": round(time.time() - t0, 1),
                  "gpu_peak_alloc_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                  "gpu_peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3)}
    (out / "eval_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("verdict", res["verdict"]["pre_registered"], res["run"]["seconds"], "s", flush=True)
    return res


if __name__ == "__main__":
    main()
