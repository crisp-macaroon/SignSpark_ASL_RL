"""Stage 5: plots of every evaluation metric from the saved dev-256 x 4 evaluation (no generation, no training).

Reads out/eval/eval_results.json (registered statistics and CIs) and out/eval/eval_samples.json (3,072 per-sample
records). R (primary) and J (descriptive) are always in separate figures, each against its own frozen target.
Per-stream paired ratios are bootstrapped here over clip means (2,000 resamples, seed 0, as in evaluate.py); every
other CI is read from eval_results.json. Released-checkpoint result, not a paper reproduction.

    python -E -s experiments/stage5/plots_all.py --eval experiments/stage5/out/eval --out experiments/stage5/out/plots_all
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONDS = ("uncoupled", "initial", "trained")
COL = {"uncoupled": "#2a78d6", "initial": "#eb6834", "trained": "#1baf7a"}  # categorical slots 1-3, fixed order
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
PAIRS = ("trained-uncoupled", "trained-initial", "initial-uncoupled")
R_STATS = {"coord_arm_rhand": ("Right arm–hand coordination", "tau_ah_R"),
           "coord_arm_lhand": ("Left arm–hand coordination", "tau_ah_L"),
           "coord_lr": ("Left–right hand coordination", "tau_lr"),
           "dom_X": ("Dominance log(A_L / A_R)", "t_dom")}
J_STATS = {"coord_ah_J_R": ("Right arm–hand coordination (J)", "tau_ah_R"),
           "coord_ah_J_L": ("Left arm–hand coordination (J)", "tau_ah_L"),
           "coord_lr_J": ("Left–right hand coordination (J)", "tau_lr"),
           "dom_J": ("Dominance log(A_L / A_R) (J)", "t_dom")}
STREAM = {"A": "Activity A", "m1_speed": "m1 mean speed", "m2_artic": "m2 articulation", "m3_jerk": "m3 jerk",
          "m4_angle": "m4 mean angle", "extreme_frac": "Extreme-frame fraction"}
LABEL = "Stage 5 ACMS pilot · dev-256 × 4 noises · released-checkpoint result, not a paper reproduction"

plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False, "lines.linewidth": 2})


def boot_ci(v, B=2000, seed=0):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    m = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
    return float(v.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def clip_means(samples, get):
    """{cond: array[n_clips]} of per-clip means over the noises."""
    out = {}
    for c in CONDS:
        d = {}
        for s in samples:
            if s["cond"] == c:
                d.setdefault(s["clip"], []).append(get(s))
        out[c] = np.array([np.nanmean(d[k]) for k in sorted(d)], float)
    return out


TRAIN_LABEL = ("Stage 5 ACMS pilot · training: 125 train clips × 4 episodes · released-checkpoint result, "
               "not a paper reproduction")
E2EJ_LABEL = ("Stage 4 E2e-J · dev clips 0–31 · fixed M-C transforms vs A0 (no training) · released-checkpoint result, "
              "not a paper reproduction")


def finish(fig, path, title, label=None):
    global LABEL
    if label is not None:
        old, LABEL = LABEL, label
        try:
            return finish(fig, path, title)
        finally:
            LABEL = old
    for ax in fig.axes:
        if not isinstance(ax.xaxis.get_major_locator(), matplotlib.ticker.FixedLocator):
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
    fig.tight_layout(rect=(0, 0.05, 1, 0.9))
    fig.suptitle(title, x=0.01, y=0.98, ha="left", fontsize=11, color=INK, fontweight="bold")
    fig.text(0.01, 0.0, LABEL, fontsize=7, color=INK2, ha="left", va="bottom")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path.name)


def paired_forest(res, stats, space, path, title):
    fig, axes = plt.subplots(1, len(stats), figsize=(3.2 * len(stats), 2.8), sharey=True)
    for ax, (k, (name, _)) in zip(axes, stats.items()):
        for y, p in enumerate(PAIRS):
            q = res[space][k][p]["paired_clip_mean"]
            lo, hi = q["ci95"]
            ax.plot([lo, hi], [y, y], color=INK2, lw=2, solid_capstyle="round")
            ax.plot(q["mean"], y, "o", ms=8, color=COL[p.split("-")[0]], mec=SURF, mew=2)
            ax.annotate(f"{q['mean']:+.4f}", (q["mean"], y), xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=7.5, color=INK)
        ax.axvline(0, color=INK, lw=1)
        ax.set_title(name, fontsize=9, loc="left")
        ax.set_yticks(range(len(PAIRS)), [p.replace("-", " − ") for p in PAIRS])
        ax.set_ylim(-0.6, len(PAIRS) - 0.4)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("paired difference (clip mean), 95% CI")
    finish(fig, path, title)


def ecdf_panels(cm, stats, targets, path, title):
    fig, axes = plt.subplots(1, len(stats), figsize=(3.2 * len(stats), 2.9))
    for ax, (k, (name, tk)) in zip(axes, stats.items()):
        for c in CONDS:
            v = np.sort(cm[k][c][np.isfinite(cm[k][c])])
            ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=COL[c], lw=1.6, label=c)
        tv = targets[tk]["value"]
        ax.axvline(tv, color=INK, lw=1, ls=(0, (4, 3)))
        left = tv < np.nanmedian(cm[k]["uncoupled"])
        ax.annotate(f"frozen\ntarget\n{tv:+.3f}", (tv, 0.95 if left else 0.06), xytext=(-4, 0), textcoords="offset points",
                    ha="right", va="top" if left else "bottom", fontsize=7, color=INK)
        ax.set_title(name, fontsize=9, loc="left")
        ax.set_xlabel("per-clip mean over 4 noises")
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("fraction of 256 clips")
    axes[0].legend(loc="upper left", fontsize=8)
    finish(fig, path, title)


def per_clip_diff(res, samples, path):
    d = np.array(res["R_space"]["coord_arm_rhand"]["trained-uncoupled"]["per_clip"], float)
    q = res["R_space"]["coord_arm_rhand"]["trained-uncoupled"]["paired_clip_mean"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.2), gridspec_kw={"width_ratios": [1, 1.4]})
    a1.hist(d, bins=40, color=COL["trained"], edgecolor=SURF, linewidth=1)
    a1.axvline(0, color=INK, lw=1)
    a1.axvline(q["mean"], color=INK2, lw=1.5, ls=(0, (4, 3)))
    a1.annotate(f"mean {q['mean']:+.4f}\n95% CI [{q['ci95'][0]:+.4f}, {q['ci95'][1]:+.4f}]", (q["mean"], a1.get_ylim()[1] * 0.92),
                xytext=(6, 0), textcoords="offset points", fontsize=7.5, color=INK, va="top")
    a1.set_xlabel("trained − uncoupled, per-clip mean")
    a1.set_ylabel("clips")
    a1.set_title("Distribution over 256 clips", fontsize=9, loc="left")
    o = np.argsort(d)
    a2.bar(np.arange(len(d)), d[o], width=1.0, color=np.where(d[o] > 0, COL["trained"], COL["uncoupled"]), linewidth=0)
    a2.axhline(0, color=INK, lw=1)
    j = int(np.nanargmax(d))
    a2.annotate(f"clip {j}: {d[j]:+.3f}", (len(d) - 1, d[j]), xytext=(-8, 0), textcoords="offset points",
                ha="right", va="center", fontsize=7.5, color=INK)
    a2.set_xlabel("clips, sorted by difference")
    a2.set_ylabel("trained − uncoupled")
    a2.set_title(f"{int((d > 0).sum())} of {int(np.isfinite(d).sum())} clips positive", fontsize=9, loc="left")
    a2.grid(axis="x", visible=False)
    finish(fig, path, "Per-clip change in right arm–hand coordination (R)")


def gap_figure(res, targets, path):
    v = {c: res["R_space"]["coord_arm_rhand"][c]["clip_mean"] for c in CONDS}
    tau = targets["tau_ah_R"]["value"]
    fig, ax = plt.subplots(figsize=(9, 2.6))
    ys = {c: i for i, c in enumerate(CONDS)}
    for c in CONDS:
        lo, hi = v[c]["ci95"]
        ax.plot([lo, hi], [ys[c], ys[c]], color=INK2, lw=2, solid_capstyle="round")
        ax.plot(v[c]["mean"], ys[c], "o", ms=8, color=COL[c], mec=SURF, mew=2)
        ax.annotate(f"{v[c]['mean']:.4f}", (v[c]["mean"], ys[c]), xytext=(10, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK)
    ref = [(tau, f"frozen train target τ = {tau}"), (res["verdict"]["A3_context_best_of_8x8_256"], "A3 best-of-8×8 context 0.408"),
           (v["uncoupled"]["mean"] + 0.05, "uncoupled + 0.05 (T3 threshold)")]
    for (x, lab), yl, ha in zip(ref, (0.5, 1.5, 1.0), ("right", "right", "left")):
        ax.axvline(x, color=INK, lw=1, ls=(0, (4, 3)))
        ax.annotate(lab, (x, yl), xytext=(-5 if ha == "right" else 5, 0), textcoords="offset points", ha=ha,
                    va="center", fontsize=7.5, color=INK)
    ax.set_yticks(range(3), CONDS)
    ax.set_ylim(-0.5, 2.5)
    ax.invert_yaxis()
    ax.set_xlim(-0.01, 0.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("right arm–hand coordination (R), mean of clip means, 95% CI")
    g = res["verdict"]["gap_closure_toward_tau"]
    finish(fig, path, f"Gain vs the target: {100 * g:.1f}% of the gap closed (pre-registered verdict: "
                      f"{res['verdict']['pre_registered']})")


def preservation(res, path):
    p = res["preservation_checks_trained_vs_uncoupled"]
    rows = [("Articulation ratio", p["artic_ratio_mean"]["value"], tuple(p["artic_ratio_mean"]["band"]), 1.0),
            ("Jerk ratio", p["jerk_ratio_mean"]["value"], (None, p["jerk_ratio_mean"]["max"]), 1.0),
            ("Extreme-frame difference", p["extreme_diff_mean"]["value"], (None, p["extreme_diff_mean"]["max"]), 0.0),
            ("|log activity ratio|", p["abs_mean_log_activity_ratio"]["value"], (None, p["abs_mean_log_activity_ratio"]["max"]), 0.0),
            ("Undefined-fraction excess", p["undefined_fraction"]["trained"] - p["undefined_fraction"]["uncoupled"],
             (None, p["undefined_fraction"]["max_excess"]), 0.0),
            ("Max KL per frame (nats)", p["kl_max"]["value"], (None, p["kl_max"]["max"]), 0.0)]
    passes = [p[k]["pass"] for k in ("artic_ratio_mean", "jerk_ratio_mean", "extreme_diff_mean",
                                     "abs_mean_log_activity_ratio", "undefined_fraction", "kl_max")]
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.0), gridspec_kw={"hspace": 0.9})
    for ax, (name, val, (lo, hi), neutral), ok in zip(axes.flat, rows, passes):
        lo_ = lo if lo is not None else min(neutral, val) - 0.15 * (hi - neutral)
        ax.axvspan(lo_, hi, color=COL["trained"], alpha=0.12, lw=0)
        ax.axvline(hi, color=INK, lw=1, ls=(0, (4, 3)))
        if lo is not None:
            ax.axvline(lo, color=INK, lw=1, ls=(0, (4, 3)))
        ax.axvline(neutral, color=INK2, lw=0.8)
        ax.plot(val, 0, "o", ms=9, color=COL["trained"], mec=SURF, mew=2)
        ax.annotate(f"{val:.4g}", (val, 0), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8, color=INK)
        span = hi - lo_
        ax.set_xlim(lo_ - 0.08 * span, hi + 0.08 * span)
        ax.set_ylim(-1, 1)
        ax.set_yticks([])
        ax.grid(False)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{name}  ·  {'✓ pass' if ok else '✗ FAIL'}", fontsize=9, loc="left")
    finish(fig, path, "Motion-preservation checks, trained vs uncoupled (shaded = allowed band)")


def per_stream(samples, path):
    keys = list(STREAM)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.3), sharex=True)
    for ax, side in zip(axes, ("R", "L")):
        for y, k in enumerate(keys):
            cm = clip_means(samples, lambda s: s["R"][f"hand_{side}"][k])
            for j, p in enumerate(("trained", "initial")):
                if k == "extreme_frac":
                    diff = cm[p] - cm["uncoupled"]
                    unit = "difference"
                else:
                    diff = 100 * (cm[p] / cm["uncoupled"] - 1)
                    unit = "%"
                m, ci = boot_ci(diff)
                yy = y + (j - 0.5) * 0.28
                ax.plot(ci, [yy, yy], color=INK2, lw=2, solid_capstyle="round")
                ax.plot(m, yy, "o", ms=6, color=COL[p], mec=SURF, mew=1.5, label=f"{p} vs uncoupled" if y == 0 else None)
        ax.axvline(0, color=INK, lw=1)
        ax.set_yticks(range(len(keys)), [STREAM[k] for k in keys])
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("change vs uncoupled, % of clip mean (extreme: absolute), 95% CI")
        ttl = "Right hand (controlled)" if side == "R" else "Left hand (identical by construction)"
        ax.set_title(ttl, fontsize=9, loc="left")
    axes[0].legend(loc="lower left", fontsize=7.5)
    finish(fig, path, "Per-stream motion statistics (R v1.1), paired against uncoupled")


def kl_typ_validity(res, samples, path):
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12, 3.0), gridspec_kw={"width_ratios": [1.4, 1, 1]})
    for c in ("initial", "trained"):
        v = np.array([s["kl_per_frame"] for s in samples if s["cond"] == c])
        a1.hist(v, bins=40, color=COL[c], alpha=0.85, edgecolor=SURF, linewidth=0.8, label=c)
    a1.set_xlabel("KL to uncoupled, nats per active frame (uncoupled = 0)")
    a1.set_ylabel("samples")
    a1.set_title("KL per frame (cap = 1.0, far right of this range)", fontsize=9, loc="left")
    a1.legend(fontsize=8)
    tm = res["typicality_monitor_fraction"]
    ks = list(tm["uncoupled"])
    w = 0.26
    for j, c in enumerate(CONDS):
        a2.bar(np.arange(len(ks)) + (j - 1) * w, [100 * tm[c][k] for k in ks], width=w - 0.03, color=COL[c], label=c)
    a2.set_xticks(range(len(ks)), ks)
    a2.set_ylabel("% of samples flagged")
    a2.set_title("Typicality monitor (non-gating)", fontsize=9, loc="left")
    a2.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.0, 1.0), ncol=3)
    a2.set_ylim(0, 0.6)
    a2.grid(axis="x", visible=False)
    vf = res["validity_flags_false_counts"]
    fk = list(vf["uncoupled"])
    n = sum(1 for s in samples if s["cond"] == "uncoupled")
    a3.axis("off")
    a3.set_title(f"Validity flags failed (of {n:,} samples per condition)", fontsize=9, loc="left")
    a3.text(0.0, 0.88, f"{'flag':<20}" + "".join(f"{c:>10}" for c in CONDS), family="monospace", fontsize=7,
            color=INK2, transform=a3.transAxes)
    for i, k in enumerate(fk):
        a3.text(0.0, 0.76 - 0.11 * i, f"{k:<20}" + "".join(f"{vf[c][k]:>10d}" for c in CONDS), family="monospace",
                fontsize=7, color=INK, transform=a3.transAxes)
    finish(fig, path, "KL, typicality monitor and validity flags")


def leakage(samples, path):
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    for c in CONDS:
        v = np.sort(100 * np.array([s["J"]["leak_ratio_R"] for s in samples if s["cond"] == c], float))
        v = v[np.isfinite(v)]
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=COL[c], lw=1.6,
                label=f"{c} (median {np.median(v):.2f}%)")
    ax.set_xlabel("right-hand J signal from arm skinning, % of the hand signal")
    ax.set_ylabel("fraction of samples")
    ax.legend(fontsize=8, loc="lower right")
    finish(fig, path, "SMPL-X skinning leakage (J, descriptive)")


def rolling(v, w=10):
    v = np.asarray(v, float)
    return np.array([np.nanmean(v[max(0, i - w + 1): i + 1]) for i in range(len(v))])


def train_reward(groups, episodes, path):
    g = np.arange(len(groups))
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.4))
    R = [x["R_mean"] for x in groups]
    axes[0].plot(g, R, "o", ms=3, color=COL["trained"], alpha=0.5, mec="none", label="group mean (4 episodes)")
    axes[0].plot(g, rolling(R), color=COL["trained"], label="10-group rolling mean")
    axes[0].set_ylabel("R = r_ah (λ = 0 throughout)")
    axes[0].set_title("Reward per update (train clips)", fontsize=9, loc="left")
    axes[0].legend(fontsize=7)
    cc, ct = [x["coord_mean"] for x in groups], [x["coord_twin_mean"] for x in groups]
    axes[1].plot(g, rolling(ct), color=COL["uncoupled"], label="uncoupled twin (10-group rolling)")
    axes[1].plot(g, rolling(cc), color=COL["trained"], label="controlled (10-group rolling)")
    axes[1].axhline(TAU, color=INK, lw=1, ls=(0, (4, 3)))
    axes[1].annotate(f"target {TAU}", (len(g) - 1, TAU), xytext=(0, -10), textcoords="offset points", ha="right",
                     fontsize=7, color=INK)
    axes[1].set_ylabel("right arm–hand coordination (R)")
    axes[1].set_title("Controlled vs CRN twin (lines nearly coincide)", fontsize=9, loc="left")
    axes[1].legend(fontsize=7, loc="center right")
    d = np.array([e["controlled"]["coord_arm_rhand"] - e["uncoupled_twin"]["coord_arm_rhand"] for e in episodes])
    dg = d.reshape(len(groups), -1).mean(1)
    cum = np.cumsum(dg) / np.arange(1, len(dg) + 1)
    axes[2].plot(g, dg, "o", ms=3, color=INK2, alpha=0.5, mec="none", label="group mean")
    axes[2].plot(g, cum, color=COL["trained"], label="cumulative mean")
    axes[2].axhline(0, color=INK, lw=1)
    m, ci = boot_ci(dg)
    axes[2].set_title(f"Controlled − twin: overall {m:+.5f} [{ci[0]:+.5f}, {ci[1]:+.5f}]", fontsize=9, loc="left")
    axes[2].set_ylabel("Δ coordination")
    axes[2].legend(fontsize=7)
    for ax in axes:
        ax.set_xlabel("update (group of 4 episodes)")
    finish(fig, path, "ACMS training: reward and coordination over 125 updates (no upward trend)", TRAIN_LABEL)


def train_optim(groups, path):
    g = np.arange(len(groups))
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2))
    axes[0].plot(g, [x["loss"] for x in groups], color=INK2, lw=1.2)
    axes[0].axhline(0, color=INK, lw=1)
    axes[0].set_title("REINFORCE loss", fontsize=9, loc="left")
    axes[1].plot(g, [x["grad_norm_pre_clip"] for x in groups], color=COL["uncoupled"], lw=1.2, label="before clip")
    axes[1].plot(g, [x["grad_norm_post_clip"] for x in groups], color=COL["initial"], lw=1.2, ls=(0, (3, 2)), label="after clip")
    axes[1].axhline(1.0, color=INK, lw=1, ls=(0, (4, 3)))
    axes[1].set_title("Gradient norm (clip at 1.0)", fontsize=9, loc="left")
    axes[1].legend(fontsize=7)
    axes[2].plot(g, [x["update_norm"] for x in groups], color=INK2, lw=1.2)
    axes[2].set_title("Parameter update norm per step", fontsize=9, loc="left")
    axes[3].plot(g, [x["beta_after"] for x in groups], color=COL["trained"])
    axes[3].set_title(f"β (cap β_max = {np.sqrt(0.5):.3f}, off this scale)", fontsize=9, loc="left")
    for ax in axes:
        ax.set_xlabel("update")
    finish(fig, path, "ACMS training: optimisation diagnostics", TRAIN_LABEL)


def train_constraints(groups, episodes, path):
    ep = np.arange(len(episodes))
    fig, axes = plt.subplots(2, 3, figsize=(13, 5.4), gridspec_kw={"hspace": 0.6})
    names = {"art": "articulation  |m2 ratio − 1| − 0.10", "jerk": "jerk  m3 ratio − 1.10",
             "ext": "extreme frames  Δ − 0.02", "act": "activity  |log A ratio| − log 1.25"}
    for ax, (k, n) in zip(axes.flat, names.items()):
        v = np.array([e["c_raw"][k] for e in episodes])
        ax.plot(ep, v, "o", ms=2, color=COL["trained"], alpha=0.5, mec="none")
        ax.axhline(0, color=INK, lw=1)
        ax.set_title(f"{n}  ·  max {np.nanmax(v):+.3f}", fontsize=8.5, loc="left")
        ax.set_xlabel("episode")
        ax.set_ylim(min(-0.25, np.nanmin(v) - 0.02), 0.05)
    kl = np.array([e["action"]["kl_per_frame"] for e in episodes])
    axes[1, 1].plot(ep, kl, "o", ms=2, color=COL["initial"], alpha=0.6, mec="none")
    axes[1, 1].set_title("KL per frame (cap 1.0, off this scale)", fontsize=8.5, loc="left")
    axes[1, 1].set_xlabel("episode")
    lam = np.array([[x["lambda_after"][k] for k in ("art", "jerk", "ext", "act")] for x in groups])
    for j, (k, col) in enumerate(zip(("art", "jerk", "ext", "act"), ("#2a78d6", "#eb6834", "#1baf7a", "#6250d6"))):
        axes[1, 2].plot(np.arange(len(groups)), lam[:, j], color=col, lw=1.5, label=k)
    axes[1, 2].set_ylim(-0.05, 1)
    axes[1, 2].set_title(f"dual variables λ_k (max {lam.max():.2f}: never active)", fontsize=8.5, loc="left")
    axes[1, 2].set_xlabel("update")
    axes[1, 2].legend(fontsize=7, ncol=4, loc="upper left")
    finish(fig, path, "ACMS training: constraints (≤ 0 satisfied), KL and dual variables per episode", TRAIN_LABEL)


def train_advantage(episodes, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
    a = np.array([e["advantage"] for e in episodes])
    axes[0].hist(a, bins=40, color=COL["trained"], edgecolor=SURF, linewidth=0.8)
    axes[0].axvline(0, color=INK, lw=1)
    axes[0].set_xlabel("RLOO advantage A_i = R_i − mean of the other 3")
    axes[0].set_ylabel("episodes")
    axes[0].set_title(f"Advantages: sd {a.std():.3f} (sum per group = 0)", fontsize=9, loc="left")
    mu = np.array([e["action"]["mu_norm_mean"] for e in episodes])
    axes[1].plot(np.arange(len(mu)), mu, "o", ms=2, color=COL["initial"], alpha=0.6, mec="none")
    axes[1].set_xlabel("episode")
    axes[1].set_ylabel("mean ‖μ_t‖ over active frames")
    axes[1].set_title("Size of the learned mean shift (noise sd = 1 per channel)", fontsize=9, loc="left")
    finish(fig, path, "ACMS training: advantages and action size", TRAIN_LABEL)


def j_per_clip_diff(res, path):
    d = np.array(res["J_space_descriptive"]["coord_ah_J_R"]["trained-uncoupled"]["per_clip"], float)
    q = res["J_space_descriptive"]["coord_ah_J_R"]["trained-uncoupled"]["paired_clip_mean"]
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    ax.hist(d, bins=40, color=COL["trained"], edgecolor=SURF, linewidth=1)
    ax.axvline(0, color=INK, lw=1)
    ax.axvline(q["mean"], color=INK2, lw=1.5, ls=(0, (4, 3)))
    ax.set_xlabel("trained − uncoupled, per-clip mean (J)")
    ax.set_ylabel("clips")
    ax.set_title(f"{int((d > 0).sum())} of {int(np.isfinite(d).sum())} clips positive · mean {q['mean']:+.4f} "
                 f"[{q['ci95'][0]:+.4f}, {q['ci95'][1]:+.4f}]", fontsize=9, loc="left")
    finish(fig, path, "Per-clip change in right arm–hand coordination (J, SMPL-X, descriptive)")


def e2ej_coord(ej, path):
    conds = [c for c, v in ej["conditions"].items() if "coord_ah_J_R" in v]
    fam = lambda c: "#2a78d6" if c.startswith("BH-r") else ("#6250d6" if c.startswith("BH-arm") else "#eb6834")
    pairs = (("coord_ah_J_R", "coord_arm_rhand", "right arm–hand"), ("coord_ah_J_L", "coord_arm_lhand", "left arm–hand"),
             ("coord_lr_J", "coord_lr", "left–right"))
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.6), sharey=True, gridspec_kw={"hspace": 0.55})
    for row, space in enumerate(("J (SMPL-X, descriptive)", "R (registered, for reference)")):
        for ax, (kj, kr, name) in zip(axes[row], pairs):
            for y, c in enumerate(conds):
                q = ej["conditions"][c][kj] if row == 0 else ej["conditions"][c]["R_space"][kr]
                ax.plot(q["ci95"], [y, y], color=INK2, lw=1.6)
                ax.plot(q["delta"], y, "o", ms=6, color=fam(c), mec=SURF, mew=1.5)
            ax.axvline(0, color=INK, lw=1)
            ax.set_title(f"{space}: Δ {name}", fontsize=8.5, loc="left")
            ax.set_yticks(range(len(conds)), conds, fontsize=7.5)
            ax.grid(axis="y", visible=False)
            ax.set_xlabel("Δ coordination vs A0, 95% CI", fontsize=8)
    axes[0, 0].set_ylim(len(conds) - 0.5, -0.5)
    fig.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=c, label=l) for c, l in (("#2a78d6", "BH: body → hand"), ("#6250d6", "BH-arm: arm channels → hand"), ("#eb6834", "LR: left → right hand"))], loc="upper right", ncol=3, fontsize=7.5)
    finish(fig, path, "E2e-J: fixed M-C coupling transforms in SMPL-X joint space (top) and rotation space (bottom)", E2EJ_LABEL)


def e2ej_dom(ej, path):
    conds = [c for c, v in ej["conditions"].items() if "delta_dom_J" in v]
    fig, axes = plt.subplots(1, 2, figsize=(11, 2.9), sharey=True)
    for ax, (title, get) in zip(axes, (("J (SMPL-X, descriptive): Δ dominance", lambda v: (v["delta_dom_J"]["delta"], v["delta_dom_J"]["ci95"])),
                                       ("R (registered, for reference): Δ dominance", lambda v: (v["R_space_D_a"]["delta"], v["R_space_D_a"]["delta_ci95"])))):
        for y, c in enumerate(conds):
            m, ci = get(ej["conditions"][c])
            ax.plot(ci, [y, y], color=INK2, lw=1.6)
            ax.plot(m, y, "o", ms=7, color=COL["trained"], mec=SURF, mew=1.5)
            ax.annotate(f"{m:+.3f}", (m, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7, color=INK)
        ax.axvline(0, color=INK, lw=1)
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_yticks(range(len(conds)), conds)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Δ log(A_L / A_R) vs A0, 95% CI")
    axes[0].set_ylim(len(conds) - 0.5, -0.6)
    finish(fig, path, "E2e-J: fixed M-C scale transforms (σ_L, σ_R), dominance in J and R", E2EJ_LABEL)


TAU = 0.4514


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default=str(ROOT / "experiments/stage5/out/eval"))
    ap.add_argument("--out", default=str(ROOT / "experiments/stage5/out/plots_all"))
    a = ap.parse_args()
    ev, out = Path(a.eval), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = json.loads((ev / "eval_results.json").read_text(encoding="utf-8"))
    samples = json.loads((ev / "eval_samples.json").read_text(encoding="utf-8"))
    targets = json.loads((ROOT / "research/stage4/FROZEN_TARGETS_R0.json").read_text(encoding="utf-8"))
    assert len(samples) == 3072 and {s["cond"] for s in samples} == set(CONDS)
    cmR = {k: clip_means(samples, lambda s, k=k: s["R"][k]) for k in R_STATS}
    cmJ = {k: clip_means(samples, lambda s, k=k: s["J"][k]) for k in J_STATS}
    # consistency with the registered analysis: plotted clip means reproduce eval_results.json
    for k in R_STATS:
        for c in CONDS:
            assert abs(np.nanmean(cmR[k][c]) - res["R_space"][k][c]["clip_mean"]["mean"]) < 1e-9, (k, c)
    for k in J_STATS:
        for c in CONDS:
            assert abs(np.nanmean(cmJ[k][c]) - res["J_space_descriptive"][k][c]["clip_mean"]["mean"]) < 1e-9, (k, c)
    assert targets["R_space"]["tau_ah_R"]["value"] == TAU
    tr = ev.parent / "train"
    groups = json.loads((tr / "groups.json").read_text(encoding="utf-8"))
    episodes = json.loads((tr / "episodes.json").read_text(encoding="utf-8"))
    ej = json.loads((ROOT / "experiments/stage4/e2e_j/out/e2ej_results.json").read_text(encoding="utf-8"))
    acms, smplx = out / "acms", out / "smplx"
    acms.mkdir(exist_ok=True)
    smplx.mkdir(exist_ok=True)
    train_reward(groups, episodes, acms / "a01_train_reward_coordination.png")
    train_optim(groups, acms / "a02_train_optimisation.png")
    train_constraints(groups, episodes, acms / "a03_train_constraints_kl_lambda.png")
    train_advantage(episodes, acms / "a04_train_advantage_action.png")
    gap_figure(res, targets["R_space"], acms / "a05_eval_gap_to_target_R.png")
    paired_forest(res, R_STATS, "R_space", acms / "a06_eval_paired_differences_R.png", "ACMS evaluation: paired differences, space R (primary)")
    per_clip_diff(res, samples, acms / "a07_eval_per_clip_difference_R.png")
    ecdf_panels(cmR, R_STATS, targets["R_space"], acms / "a08_eval_distributions_R.png", "ACMS evaluation: per-clip distributions, space R (primary)")
    preservation(res, acms / "a09_eval_preservation_checks.png")
    per_stream(samples, acms / "a10_eval_per_stream_statistics_R.png")
    kl_typ_validity(res, samples, acms / "a11_eval_kl_typicality_validity.png")
    paired_forest(res, J_STATS, "J_space_descriptive", smplx / "s01_acms_paired_differences_J.png",
                  "SMPL-X (J) evaluation of ACMS: paired differences (descriptive only)")
    j_per_clip_diff(res, smplx / "s02_acms_per_clip_difference_J.png")
    ecdf_panels(cmJ, J_STATS, targets["J_space"], smplx / "s03_acms_distributions_J.png",
                "SMPL-X (J) evaluation of ACMS: per-clip distributions vs J targets")
    leakage(samples, smplx / "s04_acms_leakage_J.png")
    e2ej_coord(ej, smplx / "s05_mc_e2ej_coordination.png")
    e2ej_dom(ej, smplx / "s06_mc_e2ej_dominance.png")


if __name__ == "__main__":
    main()
