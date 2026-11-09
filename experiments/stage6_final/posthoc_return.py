"""POST-HOC (not pre-registered) CPU-only analysis of episodic return and baseline-relative statistics for the ACMS runs.
Reads saved outputs only (eval_samples.json, episodes.json); runs no generation, training or GPU job; writes only to
experiments/stage6_final/posthoc_return/.

Return. Each episode is one decision (contextual bandit: one noise draw -> one sample), so the episodic return is the
registered reward itself, recomputed with rewards.episode_reward (experiments/stage5/rewards.py, unchanged):
    R = r_ah - sum_k lambda_k c_k,   r_ah = -|coord_ah^R - tau|,  tau = 0.4514 (frozen),  S-3 undefined -> -(1 + tau)
Evaluation uses each run's final lambda (the training log's last lambda_used); lambda == 0 in every run, so R = r_ah.
The c_k for an evaluation sample use its uncoupled CRN twin (same clip, same noise index k), exactly as in training.

Baseline-relative statistics (NOT regret):
    d_ik   = R(trained, clip i, noise k) - R(uncoupled, clip i, noise k)        paired (common random numbers)
    CRD    = sum_ik d_ik                                                         cumulative reward difference
    win    = mean_ik 1[d_ik > 0]   (ties = |d_ik| <= 1e-12 reported separately)
    clip-level statistics average over the 4 noise draws first; CIs: clip bootstrap (B = 2000, seed 0) within a run,
    t-interval across runs (runs are the unit of inference).
Conventional regret is not computed: the saved design contains no optimal-policy reference (see REGRET_NOTE).

  python -E -s experiments/stage6_final/posthoc_return.py
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU only

import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage5"))
sys.path.insert(0, str(ROOT / "experiments" / "stage5_multiseed"))
import rewards as RW  # noqa: E402  (registered reward, unchanged)
import pooled_analysis as PA  # noqa: E402  (boot_mean, tint: same estimators as the registered pooled analysis)

S5 = ROOT / "experiments" / "stage5" / "out"
MS = ROOT / "experiments" / "stage5_multiseed" / "out"
OUT = HERE / "posthoc_return"
NEW = (7001, 7002, 7003, 7004)
ALL = (7000,) + NEW
TIE = 1e-12
LABEL = "POST-HOC analysis (not pre-registered) · released-checkpoint result, not a paper reproduction · motion statistics only"
REGRET_NOTE = (
    "Conventional regret (optimal expected return minus achieved return) cannot be calculated. The saved design has no "
    "optimal-policy reference: (i) the reward supremum 0 (coord_ah^R = tau exactly) is a property of the reward function, "
    "not the value of any known or attainable policy; (ii) the best-of-8x8 (0.408) and FG-1 best-of-16 contexts are "
    "selection oracles over noise draws that use the outcome, not policies; (iii) per-clip FG-1 fits are a different "
    "estimator, clip set and noise set. No optimal reward, success criterion or regret bound is defined here. The "
    "statistics in this analysis are baseline-relative (trained minus uncoupled) and must not be read as regret.")


def tdir(s):
    return (S5 if s == 7000 else MS / f"s{s}") / "train"


def edir(s):
    return (S5 if s == 7000 else MS / f"s{s}") / "eval"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def describe(v):
    v = np.asarray(v, float)
    return {"n": int(len(v)), "mean": float(v.mean()), "sd": float(v.std(ddof=1)), "min": float(v.min()), "max": float(v.max())}


def win_stats(d, clips):
    """Paired win/tie/loss fractions over samples; clip-level win fraction (clip mean d > 0) with clip-bootstrap CI."""
    d = np.asarray(d, float)
    tie = np.abs(d) <= TIE
    w, l = (d > 0) & ~tie, (d < 0) & ~tie
    ids = sorted(set(clips))
    cm = np.array([d[np.asarray(clips) == c].mean() for c in ids])
    return {"sample_win": float(w.mean()), "sample_tie": float(tie.mean()), "sample_loss": float(l.mean()), "n_samples": int(len(d)),
            "sample_win_clip_bootstrap": PA.boot_mean(np.array([w[np.asarray(clips) == c].mean() for c in ids])),
            "clip_win": PA.boot_mean((cm > TIE).astype(float))}


def eval_run(s, lam):
    recs = load(edir(s) / "eval_samples.json")
    by = {(r["cond"], r["clip"], r["k"]): r for r in recs}
    clips = sorted({r["clip"] for r in recs})
    ks = sorted({r["k"] for r in recs})
    R, s3, above = {}, {}, {}
    for cond in ("uncoupled", "initial", "trained"):
        R[cond], s3[cond] = {}, 0
        above[cond] = float(np.mean([by[(cond, c, k)]["R"]["coord_arm_rhand"] > RW.TAU for c in clips for k in ks]))
        for c in clips:
            for k in ks:
                rec, rec0 = by[(cond, c, k)]["R"], by[("uncoupled", c, k)]["R"]
                t = RW.episode_reward(rec, rec0, lam)
                R[cond][(c, k)] = t["R"]
                s3[cond] += int(t["s3_undefined_primary"])
    keys = [(c, k) for c in clips for k in ks]
    cl = [c for c, _ in keys]
    out = {"n_clips": len(clips), "n_noises_per_clip": len(ks), "lambda": lam, "s3_undefined": s3,
           "fraction_coord_above_tau": above, "return": {}, "paired": {}}
    for cond in R:
        v = np.array([R[cond][q] for q in keys])
        cmean = np.array([v[np.asarray(cl) == c].mean() for c in clips])
        out["return"][cond] = {"sample": describe(v), "clip_mean": PA.boot_mean(cmean), "clip_mean_sd": float(cmean.std(ddof=1))}
    for a, b in (("trained", "uncoupled"), ("trained", "initial"), ("initial", "uncoupled")):
        d = np.array([R[a][q] - R[b][q] for q in keys])
        cmean = np.array([d[np.asarray(cl) == c].mean() for c in clips])
        out["paired"][f"{a}-{b}"] = {"mean_difference_clip_bootstrap": PA.boot_mean(cmean), "sample": describe(d),
                                     "cumulative_reward_difference": float(d.sum()), **win_stats(d, cl)}
    return out


def train_run(s):
    eps = load(tdir(s) / "episodes.json")
    lam_last = eps[-1]["lambda_used"]
    R = np.array([e["R"] for e in eps], float)
    # reproduce the logged return with the registered reward (check, not a replacement)
    rec = np.array([RW.episode_reward(e["controlled"], e["uncoupled_twin"], e["lambda_used"])["R"] for e in eps], float)
    twin = np.array([RW.episode_reward(e["uncoupled_twin"], e["uncoupled_twin"], e["lambda_used"])["R"] for e in eps], float)
    d = R - twin
    G = 4
    g = R.reshape(-1, G).mean(1)
    upd = np.arange(1, len(g) + 1)
    slope = float(np.polyfit(upd, g, 1)[0])
    q = len(g) // 5
    return {"n_episodes": int(len(R)), "n_updates": int(len(g)), "lambda_all_zero": bool(all(all(v == 0 for v in e["lambda_used"].values()) for e in eps)),
            "lambda_last": lam_last, "logged_return_reproduced_max_abs_err": float(np.max(np.abs(rec - R))),
            "return": describe(R), "group_mean_return": describe(g),
            "progression": {"first_25_updates_mean": float(g[:q].mean()), "last_25_updates_mean": float(g[-q:].mean()),
                            "last_minus_first": float(g[-q:].mean() - g[:q].mean()), "ols_slope_per_update": slope,
                            "quintile_means": [float(x) for x in g[: q * 5].reshape(5, q).mean(1)]},
            "twin_relative": {"mean": float(d.mean()), "sd": float(d.std(ddof=1)), "cumulative_reward_difference": float(d.sum()),
                              "win": float((d > TIE).mean()), "tie": float((np.abs(d) <= TIE).mean()), "loss": float((d < -TIE).mean()),
                              "quintile_means": [float(x) for x in d.reshape(5, -1).mean(1)]},
            "group_mean_return_series": [float(x) for x in g],
            "twin_relative_series": [float(x) for x in d]}


def figure(res):
    sys.path.insert(0, str(HERE))
    import make_figures as MF
    plt = MF.plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 3.9))
    for s in ALL:
        t = res["train"].get(str(s))
        if not t:
            continue
        ax[0].plot(np.arange(1, t["n_updates"] + 1), MF.rolling(t["group_mean_return_series"]), color=MF.RCOL[s], lw=1.5, label=f"run {s}")
        ax[1].plot(np.arange(1, t["n_episodes"] + 1), np.cumsum(t["twin_relative_series"]), color=MF.RCOL[s], lw=1.5)
    ax[0].set_xlabel("update (4 episodes each)")
    ax[0].set_ylabel("training return R (25-update running mean)")
    ax[0].set_title("Training return (TRAIN clips; clip-dependent)", fontsize=9, loc="left")
    ax[0].legend(fontsize=7, ncol=2)
    ax[1].axhline(0, color=MF.PA.INK, lw=1)
    ax[1].set_xlabel("training episode")
    ax[1].set_ylabel("cumulative R(controlled) − R(uncoupled twin)")
    ax[1].set_title("Training: cumulative reward difference vs twin", fontsize=9, loc="left")
    ys = []
    for i, s in enumerate(ALL):
        e = res["eval"].get(str(s))
        if not e:
            continue
        m = e["paired"]["trained-uncoupled"]["mean_difference_clip_bootstrap"]
        ax[2].errorbar(m["mean"], i, xerr=[[m["mean"] - m["ci95"][0]], [m["ci95"][1] - m["mean"]]], fmt="o", color=MF.RCOL[s], ms=6, capsize=3)
        ys.append((i, f"run {s}"))
    p = res["pooled_new4"]["trained-uncoupled_mean_difference"]
    ax[2].errorbar(p["mean"], len(ALL) + 0.5, xerr=[[p["mean"] - p["ci95"][0]], [p["ci95"][1] - p["mean"]]], fmt="D", color=MF.PA.INK, ms=7, capsize=3)
    ys.append((len(ALL) + 0.5, "pooled (4 new, t)"))
    ax[2].axvline(0, color=MF.PA.INK, lw=1)
    ax[2].set_yticks([y for y, _ in ys], [l for _, l in ys], fontsize=8)
    ax[2].invert_yaxis()
    ax[2].set_xlabel("held-out return difference, trained − uncoupled (dev-256 × 4)")
    ax[2].set_title("Evaluation: paired return difference (95% CI)", fontsize=9, loc="left")
    MF.OUT = OUT
    MF.fin(fig, "f13_posthoc_return.png", "Post-hoc: training return and baseline-relative return (not regret)",
           "POST-HOC · ACMS five runs")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"label": LABEL, "tau": RW.TAU, "s3_worst": RW.S3_WORST, "regret": {"available": False, "note": REGRET_NOTE},
           "formulas": {"return": "R = r_ah - sum_k lambda_k c_k; r_ah = -|coord_ah^R - tau|; single-step episodes, return = reward",
                        "paired_difference": "d_ik = R(trained,i,k) - R(uncoupled,i,k)",
                        "cumulative_reward_difference": "CRD = sum_ik d_ik", "win_fraction": "mean_ik 1[d_ik > 0]"},
           "train": {}, "eval": {}, "missing": []}
    for s in ALL:
        if not (tdir(s) / "episodes.json").exists():
            res["missing"].append(f"train {s}")
            continue
        res["train"][str(s)] = t = train_run(s)
        print(s, "train R", round(t["return"]["mean"], 4), "reproduced err", t["logged_return_reproduced_max_abs_err"], flush=True)
        if not (edir(s) / "eval_samples.json").exists():
            res["missing"].append(f"eval {s}")
            continue
        res["eval"][str(s)] = e = eval_run(s, t["lambda_last"])
        p = e["paired"]["trained-uncoupled"]
        print(s, "eval trained", round(e["return"]["trained"]["sample"]["mean"], 4), "diff", p["mean_difference_clip_bootstrap"],
              "win", round(p["sample_win"], 3), "CRD", round(p["cumulative_reward_difference"], 3), flush=True)
    for name, runs in (("pooled_new4", NEW), ("pooled_all5", ALL)):
        ev = [res["eval"][str(s)] for s in runs if str(s) in res["eval"]]
        tr = [res["train"][str(s)] for s in runs if str(s) in res["train"]]
        res[name] = {
            "trained-uncoupled_mean_difference": PA.tint([e["paired"]["trained-uncoupled"]["mean_difference_clip_bootstrap"]["mean"] for e in ev]),
            "trained-initial_mean_difference": PA.tint([e["paired"]["trained-initial"]["mean_difference_clip_bootstrap"]["mean"] for e in ev]),
            "trained_return": PA.tint([e["return"]["trained"]["clip_mean"]["mean"] for e in ev]),
            "uncoupled_return": PA.tint([e["return"]["uncoupled"]["clip_mean"]["mean"] for e in ev]),
            "sample_win_fraction": PA.tint([e["paired"]["trained-uncoupled"]["sample_win"] for e in ev]),
            "clip_win_fraction": PA.tint([e["paired"]["trained-uncoupled"]["clip_win"]["mean"] for e in ev]),
            "cumulative_reward_difference_eval": PA.tint([e["paired"]["trained-uncoupled"]["cumulative_reward_difference"] for e in ev]),
            "train_return": PA.tint([t["return"]["mean"] for t in tr]),
            "train_last_minus_first": PA.tint([t["progression"]["last_minus_first"] for t in tr]),
            "train_twin_cumulative_reward_difference": PA.tint([t["twin_relative"]["cumulative_reward_difference"] for t in tr]),
            "n_runs": len(ev)}
    (OUT / "posthoc_return_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    figure(res)
    print("wrote", OUT / "posthoc_return_results.json")


if __name__ == "__main__":
    main()
