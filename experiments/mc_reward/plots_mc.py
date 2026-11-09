"""Plots of the registered M-C reward applied to the existing E2e dumps (apply_e2e.py output). Descriptive only.

    python -E -s experiments/mc_reward/plots_mc.py
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "stage5"))
import plots_all as P  # noqa: E402  (shared style, palette and finish())

plt = P.plt
OUT = HERE / "out" / "plots"
FAM = {"base": ("No transform (A0p, independent noise)", "#52514e"), "BH": ("BH: body → hand coupling", "#2a78d6"),
       "BH_arm": ("BH-arm: arm channels → hand", "#6250d6"), "LR": ("LR: left → right hand", "#eb6834"),
       "SS": ("SS: per-hand scale σ", "#1baf7a")}
LABEL = ("M-C reward (registered §6.1) on existing E2e dumps · dev clips 0–31 × 8 noises · fixed transforms, no "
         "training · λ = α = 0, no z-norm · released-checkpoint result")
COMP = {"r_ah_R": "r_ah right", "r_ah_L": "r_ah left", "r_lr": "r_lr", "r_coord": "r_coord (sum)", "r_dom": "r_dom"}
CONSTR = {"art_L": "art L", "art_R": "art R", "jerk_L": "jerk L", "jerk_R": "jerk R", "ext_L": "ext L",
          "lr_floor": "L–R floor", "calib_L": "calib L"}


def finish(fig, path, title):
    P.LABEL, old = LABEL, P.LABEL
    P.finish(fig, path, title)
    P.LABEL = old


def rows(res):
    return [c for c in res["conditions"] if c != "A0"]


def forest(res, path):
    cs = rows(res)
    fig, axes = plt.subplots(1, len(COMP), figsize=(14, 5.6), sharey=True)
    for ax, (k, name) in zip(axes, COMP.items()):
        for y, c in enumerate(cs):
            e = res["conditions"][c]
            q = e["paired_delta_vs_A0"][k]
            col = FAM[e["kind"]][1]
            ax.plot(q["ci95"], [y, y], color=P.INK2, lw=1.6, solid_capstyle="round")
            ax.plot(q["mean"], y, "o", ms=6.5, color=col, mec=P.SURF, mew=1.5)
        ax.axvline(0, color=P.INK, lw=1)
        ax.set_title(name, fontsize=9, loc="left")
        ax.set_yticks(range(len(cs)), cs, fontsize=7.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Δ reward vs A0 (higher = closer to target)", fontsize=7.5)
    axes[0].set_ylim(len(cs) - 0.5, -0.5)  # shared y: first row at the top
    handles = [plt.Line2D([], [], marker="o", ls="", color=v[1], label=v[0]) for v in FAM.values()]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, 0.02))
    fig.subplots_adjust(bottom=0.2)
    finish(fig, path, "M-C reward components: paired change vs the untransformed sampler (A0), 95% clip CI")


def reward_vs_kl(res, path):
    cs = [c for c in rows(res) if c != "A0p"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    for ax, k, klkey, title in ((axes[0], "r_coord", "kl_kappa_per_frame", "Coordination reward vs coupling KL (BH, LR)"),
                                (axes[1], "r_dom", "kl_sigma_per_frame", "Dominance reward vs scale KL (SS)")):
        fams = ("BH", "BH_arm", "LR") if k == "r_coord" else ("SS",)
        seen = []
        for c in cs:
            e = res["conditions"][c]
            if e["kind"] not in fams:
                continue
            q, x = e["paired_delta_vs_A0"][k], e[klkey]
            dodge = 1.2 * sum(abs(x - s) < 1.0 for s in seen)  # same-KL conditions side by side
            seen.append(x)
            xd = x + dodge
            ax.plot([xd, xd], q["ci95"], color=P.INK2, lw=1.4)
            ax.plot(xd, q["mean"], "o", ms=7, color=FAM[e["kind"]][1], mec=P.SURF, mew=1.5)
            near = [s for s in seen[:-1] if abs(x - s) < 1.0]
            ax.annotate(c.replace("-seed", " s"), (xd, q["mean"]), xytext=(6, 9 * len(near)), textcoords="offset points",
                        fontsize=6.5, color=P.INK, va="center")
        ax.axhline(0, color=P.INK, lw=1)
        ax.set_xlabel("exact KL per active frame (nats)")
        ax.set_ylabel(f"Δ {k} vs A0")
        ax.set_title(title, fontsize=9, loc="left")
    handles = [plt.Line2D([], [], marker="o", ls="", color=FAM[f][1], label=FAM[f][0]) for f in ("BH", "BH_arm", "LR", "SS")]
    axes[0].legend(handles=handles[:3], fontsize=7, loc="upper left")
    axes[0].set_ylim(top=0.14)
    finish(fig, path, "Reward gained per unit of KL (fixed M-C transforms)")


def constraints(res, path):
    cs = rows(res)
    M = np.array([[res["conditions"][c]["constraint_mean"][k]["mean"] for k in CONSTR] for c in cs])
    V = np.array([[res["conditions"][c]["constraint_violated_fraction"][k] for k in CONSTR] for c in cs])
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#eb6834"])
    lim = max(0.3, float(np.nanmax(np.abs(M))))
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.imshow(M, cmap=cmap, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:+.2f}\n{100 * V[i, j]:.0f}%", ha="center", va="center", fontsize=6.5, color=P.INK)
    ax.set_xticks(range(len(CONSTR)), list(CONSTR.values()))
    ax.set_yticks(range(len(cs)), cs, fontsize=7.5)
    ax.grid(False)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("cell: mean raw c_k (≤ 0 satisfied; blue = slack, orange = violated) and % of episodes violating",
                 fontsize=8, loc="left")
    finish(fig, path, "M-C constraints (registered §6.1) vs the paired base sample")


def reward_shape(res, per_clip, path):
    t = res["targets"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    for ax, stat, tk, comp, show in ((axes[0], "coord_ah_R", "tau_ah_R", "r_ah right", ("A0", "BH-r60-k0.9-seed0")),
                                     (axes[1], "dom", "t_dom", "r_dom", ("A0", "SS-1.0-1.15", "SS-0.75-1.0"))):
        tau = t[tk]
        allv = np.concatenate([per_clip[c][stat] for c in show])
        x = np.linspace(min(allv.min(), tau) - 0.15, max(allv.max(), tau) + 0.15, 400)
        ax.plot(x, -np.abs(x - tau), color=P.INK, lw=1.5, label=f"{comp} = −|x − {tau:+.3f}|")
        ax.axvline(tau, color=P.INK, lw=1, ls=(0, (4, 3)))
        cols = ("#52514e", "#2a78d6", "#1baf7a")
        for c, col in zip(show, cols):
            v = np.array(per_clip[c][stat])
            ax.plot(v, -np.abs(v - tau), "o", ms=4, alpha=0.75, color=col, mec="none", label=f"{c} (per-clip means)")
        ax.set_xlabel(f"{stat} (space R)")
        ax.set_ylabel("reward term")
        ax.set_title(f"Target matching: peak at the frozen target {tau:+.3f}", fontsize=9, loc="left")
        ax.legend(fontsize=7, loc="lower center")
    finish(fig, path, "Shape of the M-C reward terms and where real samples fall on them")


def levels(res, path):
    cs = ["A0"] + rows(res)
    stats = {"coord_ah_R": "tau_ah_R", "coord_ah_L": "tau_ah_L", "coord_lr": "tau_lr", "dom": "t_dom"}
    fig, axes = plt.subplots(1, 4, figsize=(14, 5.4), sharey=True)
    for ax, (s, tk) in zip(axes, stats.items()):
        for y, c in enumerate(cs):
            e = res["conditions"][c]
            q = e["level"][s]
            ax.plot(q["ci95"], [y, y], color=P.INK2, lw=1.6)
            ax.plot(q["mean"], y, "o", ms=6, color=FAM[e["kind"]][1] if c != "A0" else P.INK, mec=P.SURF, mew=1.5)
        ax.axvline(res["targets"][tk], color=P.INK, lw=1, ls=(0, (4, 3)))
        ax.annotate(f"target {res['targets'][tk]:+.3f}", (res["targets"][tk], -0.7), xytext=(-4, 0),
                    textcoords="offset points", ha="right", fontsize=7, color=P.INK)
        ax.set_title(s, fontsize=9, loc="left")
        ax.set_yticks(range(len(cs)), cs, fontsize=7.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("mean of clip means, 95% CI")
    axes[0].set_ylim(len(cs) - 0.5, -0.9)  # shared y: A0 at the top, room for the target label
    finish(fig, path, "Underlying statistics (space R) per condition vs the frozen targets")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = json.loads((HERE / "out" / "mc_reward_e2e.json").read_text(encoding="utf-8"))
    per_clip = json.loads((HERE / "out" / "mc_reward_e2e_per_clip.json").read_text(encoding="utf-8"))
    forest(res, OUT / "mc1_reward_components_delta.png")
    reward_vs_kl(res, OUT / "mc2_reward_vs_kl.png")
    constraints(res, OUT / "mc3_constraints.png")
    reward_shape(res, per_clip, OUT / "mc4_reward_shape.png")
    levels(res, OUT / "mc5_statistics_vs_targets.png")


if __name__ == "__main__":
    main()
