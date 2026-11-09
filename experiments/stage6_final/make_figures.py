"""Final figures (research/stage6_proposal/EVALUATION_PPT_FIGURE_PLAN.md groups 1-11 + ablations) from MEASURED outputs
only. A figure whose inputs do not exist is not drawn; it is listed as unavailable in figures_index.json. No value is
imputed. R primary, J descriptive in separate panels. CPU only.

  python -E -s experiments/stage6_final/make_figures.py
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage5"))
import plots_all as PA  # noqa: E402  (shared style, palette, finish())

plt = PA.plt
OUT = HERE / "figures"
MS = ROOT / "experiments" / "stage5_multiseed" / "out"
S5 = ROOT / "experiments" / "stage5" / "out"
GATE = ROOT / "experiments" / "stage6_gate" / "out"
E2E = ROOT / "experiments" / "stage4" / "e2e" / "out" / "results.json"
E2C = ROOT / "experiments" / "stage4" / "e2c" / "out_ii"
RUNS = (7000, 7001, 7002, 7003, 7004)
RCOL = {7000: "#52514e", 7001: "#2a78d6", 7002: "#eb6834", 7003: "#1baf7a", 7004: "#6250d6"}
VCOL = {"V0": "#52514e", "V1": "#2a78d6", "V2": "#1baf7a", "V3": "#eb6834"}
VNAME = {"V1": "V1 M-C learned BH", "V2": "V2 ACMS per clip", "V3": "V3 SC-MC bilateral"}
LBL = "released-checkpoint result, not a paper reproduction · motion statistics only (no ASL-quality claim)"
INDEX = {"drawn": {}, "unavailable": {}}


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def fin(fig, name, title, note):
    PA.finish(fig, OUT / name, title, label=f"{note} · {LBL}")
    INDEX["drawn"][name] = title


def missing(name, why):
    INDEX["unavailable"][name] = why
    print("UNAVAILABLE", name, "-", why)


def tdir(s):
    return S5 / "train" if s == 7000 else MS / f"s{s}" / "train"


def rolling(v, w=25):
    v = np.asarray(v, float)
    return np.array([np.nanmean(v[max(0, i - w + 1): i + 1]) for i in range(len(v))])


def f01_return(groups):
    fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
    for s, g in groups.items():
        R = np.array([x["R_mean"] for x in g])
        ep = (np.arange(len(R)) + 1) * 4
        ax[0].plot(ep, rolling(R), color=RCOL[s], lw=1.6, label=f"run {s}")
    ax[0].set_xlabel("training episode")
    ax[0].set_ylabel("return R = r_ah (25-group running mean)")
    ax[0].set_title("Training return (clip-dependent; R = r_ah since λ ≡ 0)", fontsize=9, loc="left")
    ax[0].legend(fontsize=7, ncol=2)
    for s in groups:
        eps = load(tdir(s) / "episodes.json")
        d = np.array([e["controlled"]["coord_arm_rhand"] - e["uncoupled_twin"]["coord_arm_rhand"] for e in eps], float)
        b = d.reshape(5, 100)
        ax[1].plot(np.arange(5) * 100 + 50, np.nanmean(b, 1), "o-", color=RCOL[s], ms=5, lw=1.2)
    ax[1].axhline(0, color=PA.INK, lw=1)
    ax[1].set_xlabel("training episode (100-episode bins)")
    ax[1].set_ylabel("controlled − uncoupled twin coord_ah^R")
    ax[1].set_title("Training-time effect vs the uncoupled twin (same noise)", fontsize=9, loc="left")
    fin(fig, "f01_training_return.png", "ACMS training return vs episodes, five runs", "ACMS · 125 TRAIN clips × 4 per run")


def f02_progress(pooled):
    per = {r["seed"]: r for r in pooled["per_run"] if not r["missing"]}
    if any(any(r["optc_progress"].get(u) is None for u in ("25", "50", "75", "100")) for r in per.values()):
        return missing("f02_heldout_vs_progress.png", "OPT-C incomplete")
    fig, ax = plt.subplots(figsize=(8, 4))
    us = [0, 25, 50, 75, 100, 125]
    for s, r in per.items():
        m = [r["optc_progress"][str(u)]["mean"] for u in us]
        lo = [r["optc_progress"][str(u)]["ci95"][0] for u in us]
        hi = [r["optc_progress"][str(u)]["ci95"][1] for u in us]
        x = np.array(us) * 4 + (s - 7002) * 3
        ax.errorbar(x, m, yerr=[np.array(m) - lo, np.array(hi) - m], color=RCOL[s], marker="o", ms=4, lw=1.2, capsize=0, label=f"run {s}")
    p = pooled["pooled_primary_new4"]["optc_progress_pooled"]
    pm = [p[str(u)]["mean"] for u in us]
    ax.plot(np.array(us) * 4, pm, color=PA.INK, lw=2.4, label="pooled mean, 4 new runs")
    ax.axhline(0, color=PA.INK, lw=1)
    ax.set_xlabel("training episodes (checkpoint updates 0, 25, …, 125)")
    ax.set_ylabel("held-out Δ coord_ah^R vs uncoupled (R)")
    ax.legend(fontsize=7, ncol=3)
    fin(fig, "f02_heldout_vs_progress.png", "Held-out improvement vs training progress (monitoring; no checkpoint selection)",
        "OPT-C · dev-256 × 4 common noise · 95% clip CIs")


def f03_constraints(groups):
    names = ("art", "jerk", "ext", "act")
    fig, ax = plt.subplots(1, 4, figsize=(14, 3.4), sharey=True)
    for s, g in groups.items():
        for a, k in zip(ax, names):
            a.plot((np.arange(len(g)) + 1) * 4, rolling([x["c_mean"][k] for x in g]), color=RCOL[s], lw=1.3)
    for a, k in zip(ax, names):
        a.axhline(0, color=PA.INK, lw=1)
        a.set_title(f"c_{k} (≤ 0 satisfied)", fontsize=9, loc="left")
        a.set_xlabel("episode")
    ax[0].set_ylabel("clipped constraint, group mean (running)")
    lam = {s: max(max(x["lambda_after"].values()) for x in g) for s, g in groups.items()}
    ax[3].text(0.02, 0.95, "max λ over training: " + ", ".join(f"{s}: {v:.2f}" for s, v in lam.items()),
               transform=ax[3].transAxes, fontsize=6.5, va="top")
    fin(fig, "f03_training_constraints.png", "ACMS constraint curves during training, five runs", "ACMS training")


def forest(ax, rows, title, xlabel):
    for y, (lab, m, ci, col) in enumerate(rows):
        ax.plot(ci, [y, y], color=PA.INK2, lw=1.6)
        ax.plot(m, y, "o", color=col, ms=7, mec=PA.SURF, mew=1.5)
    ax.axvline(0, color=PA.INK, lw=1)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_title(title, fontsize=9, loc="left")
    ax.set_xlabel(xlabel, fontsize=8)


def f04_coord(pooled):
    per = [r for r in pooled["per_run"] if not r["missing"]]
    p4, p5 = pooled["pooled_primary_new4"], pooled["pooled_secondary_all5"]
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.8), sharey=True)
    for a, st, ttl in zip(ax, ("coord_arm_rhand", "coord_lr", "dom_X"),
                          ("Right arm–hand coordination (primary)", "Left–right coordination", "Dominance log(A_L/A_R)")):
        rows = [(f"run {r['seed']}", r["deltas_R"][st]["trained-uncoupled"]["mean"], r["deltas_R"][st]["trained-uncoupled"]["ci95"],
                 RCOL[r["seed"]]) for r in per]
        k = f"R.{st}.trained-uncoupled"
        rows.append(("pooled, 4 new (t)", p4["secondary"][k]["mean"], p4["secondary"][k]["ci95"], PA.INK))
        rows.append(("pooled, all 5 (t)", p5["secondary"][k]["mean"], p5["secondary"][k]["ci95"], PA.INK))
        forest(a, rows, ttl, "Δ trained − uncoupled (R); runs: clip CI; pooled: across-run t-CI")
    fin(fig, "f04_coordination_multiseed.png", "Held-out coordination change per run and pooled (space R, primary)",
        f"ACMS · dev-256 × 4 · primary category: {p4['category']}")
    if all(r["J"] for r in per):
        fig, ax = plt.subplots(figsize=(6, 3.6))
        rows = [(f"run {r['seed']}", r["J"]["coord_ah_J_R"]["mean"], r["J"]["coord_ah_J_R"]["ci95"], RCOL[r["seed"]]) for r in per]
        k = "J.coord_ah_J_R.trained-uncoupled"
        rows.append(("pooled, 4 new (t)", p4["secondary"][k]["mean"], p4["secondary"][k]["ci95"], PA.INK))
        forest(ax, rows, "Right arm–hand coordination, J (descriptive)", "Δ trained − uncoupled (J)")
        fin(fig, "f04b_coordination_multiseed_J.png", "Same comparison in joint space J (descriptive; not an independent replication)",
            "ACMS · dev-256 × 4")


def f05_preservation(pooled):
    per = [r for r in pooled["per_run"] if not r["missing"]]
    spec = [("artic_ratio_mean", "articulation ratio", (0.9, 1.1)), ("jerk_ratio_mean", "jerk ratio", (None, 1.10)),
            ("extreme_diff_mean", "extreme-frame diff", (None, 0.02)), ("abs_mean_log_activity_ratio", "|mean log activity ratio|", (None, np.log(1.25))),
            ("kl_max", "max KL (nats/frame)", (None, 1.0))]
    fig, ax = plt.subplots(1, 5, figsize=(15, 3.2))
    for a, (k, name, (lo, hi)) in zip(ax, spec):
        for i, r in enumerate(per):
            a.plot(i, r["preservation"][k]["value"], "o", color=RCOL[r["seed"]], ms=7)
        for v in (lo, hi):
            if v is not None:
                a.axhline(v, color=PA.INK, lw=1, ls=(0, (4, 3)))
        a.set_xticks(range(len(per)), [str(r["seed"]) for r in per], fontsize=7)
        a.set_title(name, fontsize=9, loc="left")
    fin(fig, "f05_preservation_multiseed.png", "Pre-registered preservation checks per run (dashed = limit)",
        "ACMS trained vs uncoupled, paired · all runs: " + ("all pass" if all(r["all_checks_pass"] for r in per) else "SOME FAIL"))


def f06_kl(groups):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for s, g in groups.items():
        ax.plot((np.arange(len(g)) + 1) * 4, [x["kl_mean"] for x in g], color=RCOL[s], lw=1.3, label=f"run {s}")
    ax.axhline(1.0, color=PA.INK, lw=1, ls=(0, (4, 3)))
    ax.set_yscale("log")
    ax.set_xlabel("episode")
    ax.set_ylabel("KL per active frame (nats), group mean")
    ax.legend(fontsize=7, ncol=3)
    fin(fig, "f06_kl_multiseed.png", "Policy KL to the uncoupled sampler during training (cap 1 nat/frame, dashed)", "ACMS training")


def f07_mc_history():
    r, agg = load(E2E), load(E2C / "e2c_ii_aggregate.json")
    if r is None or agg is None:
        return missing("f07_mc_history.png", "E2e / E2c (ii) outputs missing")
    t3, kl = r["analysis"]["T3"], r["steps"]["0"]["KL_per_frame"]
    fig, ax = plt.subplots(1, 2, figsize=(13, 4))
    for side, mk, off in (("coord_arm_rhand", "o", -0.01), ("coord_arm_lhand", "s", 0.01)):
        for c, e in t3.items():
            if not c.startswith("BH-r60"):
                continue
            kap = float(c.split("-k")[1].split("-")[0])
            seed = int(c[-1])
            ax[0].errorbar(kap + off + 0.02 * seed, e[side]["delta"], yerr=[[e[side]["delta"] - e[side]["ci95"][0]], [e[side]["ci95"][1] - e[side]["delta"]]],
                           fmt=mk, color=["#2a78d6", "#eb6834", "#1baf7a"][seed], ms=6, capsize=0, lw=1.2)
    ax[0].axhline(0.05, color=PA.INK, lw=1, ls=(0, (4, 3)))
    ax[0].axhline(0, color=PA.INK, lw=1)
    ax[0].set_xlabel("κ (BH-r60; colour = orientation seed 0/1/2; ○ right, □ left)")
    ax[0].set_ylabel("Δ arm–hand coordination vs A0 (R)")
    ax[0].set_title("E2e: fixed M-C coupling never reaches 0.05 (dashed)", fontsize=9, loc="left")
    it = np.arange(len(agg["train_objective_mean_by_iteration"]))
    ax[1].plot(it, agg["train_objective_mean_by_iteration"], color="#2a78d6", label="in-sample (fit noises k1–4)")
    ax[1].axhline(agg["mean_heldout"]["mean"], color="#1baf7a", lw=2, label="held-out (k5–8), final params")
    ax[1].axhline(agg["mean_uncoupled_A0_heldout"]["mean"], color=PA.INK2, lw=1.4, ls=(0, (4, 3)), label="uncoupled, held-out")
    ax[1].axhline(agg["comparators"]["primary_typical_only"], color=PA.INK, lw=1, ls=":", label="best-of-8×8 selection level")
    ax[1].set_xlabel("Adam iteration")
    ax[1].set_ylabel("right arm–hand coordination (R)")
    ax[1].set_title("E2c (ii): per-clip learned coupling overfits its noise draws", fontsize=9, loc="left")
    ax[1].legend(fontsize=7)
    fin(fig, "f07_mc_history.png", "M-C historical feasibility (Stage 4)", "dev clips 0–31")


def f08_gate(fg, pooled):
    if fg is None:
        return missing("f08_fg1_comparison.png", "FG-1 results missing")
    V = fg["variants"]
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.8), sharey=True)
    for a, (h, ttl) in zip(ax, (("R", "Right arm–hand coord (V1, V2, V3)"), ("L", "Left arm–hand coord (V3)"), ("LR", "Left–right coord (V3)"))):
        rows = []
        for v in ("V1", "V2", "V3"):
            e = V.get(v, {})
            if e.get("status") != "completed":
                continue
            st = e["statistics"][h]
            d = st["heldout_delta_vs_V0"]
            rows.append((f"{v} held-out", d["mean"], d["ci95"], VCOL[v]))
            dl = st["insample_delta_last_iter"]
            rows.append((f"{v} in-sample", dl["mean"], dl["ci95"], "#bdbcb7"))
        if rows:
            forest(a, rows, ttl, "Δ vs V0 uncoupled (R), 16 clips, 95% clip CI")
            a.axvline(0.05, color=PA.INK, lw=1, ls=(0, (4, 3)))
    out = ", ".join(f"{v}: {V[v].get('outcome', V[v].get('status'))}" for v in ("V1", "V2", "V3") if v in V)
    fin(fig, "f08_fg1_comparison.png", "FG-1 like-for-like gate: M-C vs ACMS vs SC-MC vs uncoupled on fresh noise",
        f"16 TRAIN clips × 16 fresh noises · dashed = registered 0.05 · outcomes {out}")
    # descriptive cross-study panel
    r = load(E2E)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    if r:
        kl = r["steps"]["0"]["KL_per_frame"]
        for c, e in r["analysis"]["T3"].items():
            ax.errorbar(kl[c][0], e["coord_arm_rhand"]["delta"], yerr=[[e["coord_arm_rhand"]["delta"] - e["coord_arm_rhand"]["ci95"][0]],
                        [e["coord_arm_rhand"]["ci95"][1] - e["coord_arm_rhand"]["delta"]]], fmt="s", color="#2a78d6", ms=5, lw=1)
    agg = load(E2C / "e2c_ii_aggregate.json")
    if agg:
        g = agg["gain_heldout_vs_uncoupled"]
        ax.errorbar(agg["kl_per_frame"]["mean"], g["mean"], yerr=[[g["mean"] - g["ci95"][0]], [g["ci95"][1] - g["mean"]]], fmt="D", color="#6250d6", ms=7, lw=1)
    for rr in pooled["per_run"]:
        if not rr["missing"]:
            d = rr["primary"]
            ax.errorbar(rr["kl_per_frame"]["trained"]["mean"], d["mean"], yerr=[[d["mean"] - d["ci95"][0]], [d["ci95"][1] - d["mean"]]],
                        fmt="o", color="#1baf7a", ms=6, lw=1)
    for v in ("V1", "V2", "V3"):
        e = fg["variants"].get(v, {})
        if e.get("status") == "completed":
            d = e["statistics"]["R"]["heldout_delta_vs_V0"]
            ax.errorbar(max(e["kl_mean"]["R"], 1e-4), d["mean"], yerr=[[d["mean"] - d["ci95"][0]], [d["ci95"][1] - d["mean"]]],
                        fmt="^", color=VCOL[v], ms=8, lw=1)
    ax.axhline(0, color=PA.INK, lw=1)
    ax.axhline(0.05, color=PA.INK, lw=1, ls=(0, (4, 3)))
    ax.set_xscale("log")
    ax.set_xlabel("KL per active frame (nats, log)")
    ax.set_ylabel("held-out Δ right arm–hand coord vs own uncoupled (R)")
    hd = [plt.Line2D([], [], marker=m, ls="", color=c, label=l) for m, c, l in
          (("s", "#2a78d6", "E2e fixed BH/LR (32 dev clips)"), ("D", "#6250d6", "E2c (ii) per-clip M-C (32 dev clips)"),
           ("o", "#1baf7a", "ACMS amortised, 5 runs (dev-256)"), ("^", VCOL["V1"], "FG-1 V1"), ("^", VCOL["V2"], "FG-1 V2"), ("^", VCOL["V3"], "FG-1 V3"))]
    ax.legend(handles=hd, fontsize=7, loc="upper left")
    fin(fig, "f08b_cross_study_kl.png", "Held-out gain vs KL across studies (DESCRIPTIVE: different clips, noises, budgets)",
        "not a like-for-like comparison except within FG-1")


def f09_stability(pooled):
    per = [r for r in pooled["per_run"] if not r["missing"]]
    if len(per) < 2:
        return missing("f09_seed_stability.png", "fewer than two runs")
    items = [("primary Δ coord_ah^R", lambda r: r["primary"]["mean"]), ("Δ dominance", lambda r: r["deltas_R"]["dom_X"]["trained-uncoupled"]["mean"]),
             ("Δ L–R coord", lambda r: r["deltas_R"]["coord_lr"]["trained-uncoupled"]["mean"]), ("A_R ratio", lambda r: r["activity_ratio_R"]),
             ("KL mean (trained)", lambda r: r["kl_per_frame"]["trained"]["mean"]), ("final β", lambda r: r["train"]["final_beta"])]
    fig, ax = plt.subplots(1, 6, figsize=(16, 3))
    for a, (name, f) in zip(ax, items):
        for i, r in enumerate(per):
            a.bar(i, f(r), color=RCOL[r["seed"]], width=0.7)
        a.set_xticks(range(len(per)), [str(r["seed"]) for r in per], fontsize=7)
        a.set_title(name, fontsize=8.5, loc="left")
        a.axhline(0, color=PA.INK, lw=0.8)
    p = pooled["pooled_primary_new4"]
    fin(fig, "f09_seed_stability.png", "Across-run stability of the ACMS effect and controller statistics",
        f"pooled (4 new) Δ = {p['pooled_t']['mean']:+.5f}, SD {p['pooled_t']['sd']:.5f}, I² = {p['heterogeneity']['I2']:.2f}")


def f10_generalisation(pooled, fg):
    fig, ax = plt.subplots(1, 3, figsize=(15, 3.8))
    agg = load(E2C / "e2c_ii_aggregate.json")
    if agg:
        vals = [agg["mean_best_train"], agg["mean_heldout"], agg["mean_uncoupled_A0_heldout"]]
        for i, (v, c) in enumerate(zip(vals, ("#2a78d6", "#1baf7a", "#52514e"))):
            ax[0].bar(i, v["mean"], color=c, width=0.6)
            ax[0].plot([i, i], v["ci95"], color=PA.INK, lw=1.4)
        ax[0].set_xticks(range(3), ["in-sample best", "held-out", "uncoupled"], fontsize=8)
        ax[0].set_title("E2c (ii) M-C per clip (32 dev clips)", fontsize=9, loc="left")
        ax[0].set_ylabel("coord_ah^R (R)")
    per = [r for r in pooled["per_run"] if not r["missing"] and r["optg"]]
    if per:
        for i, r in enumerate(per):
            g = r["optg"]["train_like"]
            ax[1].errorbar(i - 0.12, g["mean"], yerr=[[g["mean"] - g["ci95"][0]], [g["ci95"][1] - g["mean"]]], fmt="o", color="#2a78d6", ms=6)
            d = r["primary"]
            ax[1].errorbar(i + 0.12, d["mean"], yerr=[[d["mean"] - d["ci95"][0]], [d["ci95"][1] - d["mean"]]], fmt="o", color="#1baf7a", ms=6)
        ax[1].axhline(0, color=PA.INK, lw=1)
        ax[1].set_xticks(range(len(per)), [str(r["seed"]) for r in per], fontsize=8)
        ax[1].set_title("ACMS: own TRAIN clips, fresh noise (blue) vs dev (green)", fontsize=9, loc="left")
        ax[1].set_ylabel("Δ coord_ah^R vs uncoupled (R)")
    else:
        ax[1].text(0.5, 0.5, "OPT-G not available", ha="center", transform=ax[1].transAxes)
    if fg:
        xs, labs = [], []
        for i, v in enumerate(("V1", "V2", "V3")):
            e = fg["variants"].get(v, {})
            if e.get("status") != "completed":
                continue
            st = e["statistics"]["R"]
            for j, (k, c) in enumerate((("insample_delta_last_iter", "#2a78d6"), ("heldout_delta_vs_V0", "#1baf7a"))):
                d = st[k]
                ax[2].errorbar(i + (j - 0.5) * 0.25, d["mean"], yerr=[[d["mean"] - d["ci95"][0]], [d["ci95"][1] - d["mean"]]], fmt="o", color=c, ms=6)
            xs.append(i)
            labs.append(v)
        ax[2].axhline(0, color=PA.INK, lw=1)
        ax[2].axhline(0.05, color=PA.INK, lw=1, ls=(0, (4, 3)))
        ax[2].set_xticks(xs, labs)
        ax[2].set_title("FG-1: in-sample (blue) vs fresh-noise (green), right arm–hand", fontsize=9, loc="left")
    fin(fig, "f10_generalisation.png", "Training-like vs held-out generalisation", "95% clip CIs")


def f11_compute(table):
    fig, ax = plt.subplots(1, 2, figsize=(13, 0.45 * len(table) + 1.6))
    names = [t["experiment"] for t in table]
    y = np.arange(len(table))
    ax[0].barh(y, [t["seconds"] / 60 for t in table], color="#2a78d6")
    ax[0].set_yticks(y, names, fontsize=7.5)
    ax[0].invert_yaxis()
    ax[0].set_xlabel("wall-clock (min)")
    mem = [t["gpu_peak_reserved_GiB"] if t["gpu_peak_reserved_GiB"] is not None else np.nan for t in table]
    ax[1].barh(y, mem, color="#eb6834")
    for i, m in enumerate(mem):
        if not np.isfinite(m):
            ax[1].text(0.1, i, "not logged", va="center", fontsize=7)
    ax[1].set_yticks(y, [""] * len(y))
    ax[1].invert_yaxis()
    ax[1].set_xlabel("peak GPU reserved (GiB)")
    fin(fig, "f11_compute.png", "Computational cost of every executed experiment (single RTX A4000)", "measured values only")


def f12_ablations(pooled, fg):
    per = [r for r in pooled["per_run"] if not r["missing"]]
    fig, ax = plt.subplots(1, 2, figsize=(13, 3.8))
    rows = []
    for r in per:
        for pair, c in (("trained-initial", "#1baf7a"), ("initial-uncoupled", "#eb6834")):
            d = r["deltas_R"]["coord_arm_rhand"][pair]
            rows.append((f"{r['seed']} {pair}", d["mean"], d["ci95"], c))
    forest(ax[0], rows, "Effect of training (trained − initial) vs random init (initial − uncoupled)", "Δ coord_ah^R (R)")
    if fg:
        rows = []
        for v in ("V2", "V3"):
            e = fg["variants"].get(v, {})
            if e.get("status") == "completed" and "state_shuffle_ablation" in e:
                for h, s in e["state_shuffle_ablation"].items():
                    d = s["delta_vs_unshuffled"]
                    rows.append((f"{v} {h}: shuffled − matched state", d["mean"], d["ci95"], VCOL[v]))
        if rows:
            forest(ax[1], rows, "FG-1 state-shuffle ablation (ŝ from another noise draw)", "Δ (R)")
    fin(fig, "f12_ablations.png", "Ablations that were actually run", "ACMS dev-256 × 4; FG-1 16 × 16")


def compute_table(pooled, fg):
    t = [{"experiment": "Stage 4 E2e (fixed M-C, 16 conditions)", "seconds": 1726.0, "gpu_peak_reserved_GiB": None, "params": 0},
         {"experiment": "Stage 4 E2c (ii) (per-clip M-C, 32 clips)", "seconds": 1614.0, "gpu_peak_reserved_GiB": 8.70, "params": "≈9,060/clip"}]
    for r in pooled["per_run"]:
        if r["missing"]:
            continue
        t.append({"experiment": f"ACMS train run {r['seed']}", "seconds": r["train"]["seconds"], "gpu_peak_reserved_GiB": r["train"]["gpu_peak_reserved_GiB"], "params": 433})
        t.append({"experiment": f"ACMS eval run {r['seed']} (R+J)", "seconds": r["eval_run"]["seconds"], "gpu_peak_reserved_GiB": r["eval_run"]["gpu_peak_reserved_GiB"], "params": 0})
    if fg:
        for p, rr in fg["runs"].items():
            if "seconds" in rr:
                t.append({"experiment": f"FG-1 {p}", "seconds": rr["seconds"], "gpu_peak_reserved_GiB": rr.get("gpu_peak_reserved_GiB"),
                          "params": rr.get("params_per_clip", 0), "status": rr.get("status")})
    st = load(ROOT / "experiments" / "stage6_gate" / "out" / "runner_status.json") or []
    for e in st:
        if e.get("name", "").startswith(("optg", "optc")):
            t.append({"experiment": e["name"], "seconds": e["seconds"], "gpu_peak_reserved_GiB": None, "params": 0, "exit": e.get("exit")})
    for e in t:
        n = e["experiment"]
        if n.startswith(("optg_", "optc_")):
            s, rest = n.split("_s")[1][:4], n
            od = MS / f"s{s}"
            p = od / "optg" / "train_eval_results.json" if n.startswith("optg") else od / "optc" / n.split("_")[-1] / "eval_results.json"
            j = load(p)
            if j:
                e["gpu_peak_reserved_GiB"] = j["run"]["gpu_peak_reserved_GiB"]
    return t


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pooled = load(MS / "pooled_results.json")
    fg = load(GATE / "fg1_results.json")
    groups = {s: load(tdir(s) / "groups.json") for s in RUNS}
    groups = {s: g for s, g in groups.items() if g}
    f01_return(groups)
    f03_constraints(groups)
    f06_kl(groups)
    f07_mc_history()
    if pooled:
        f02_progress(pooled)
        f04_coord(pooled)
        f05_preservation(pooled)
        f09_stability(pooled)
        f10_generalisation(pooled, fg)
        f12_ablations(pooled, fg)
        f08_gate(fg, pooled)
        table = compute_table(pooled, fg)
        (HERE / "compute_table.json").write_text(json.dumps(table, indent=1), encoding="utf-8")
        f11_compute(table)
    else:
        for n in ("f02", "f04", "f05", "f08", "f09", "f10", "f11", "f12"):
            missing(n, "pooled_results.json missing")
    (HERE / "figures_index.json").write_text(json.dumps(INDEX, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
