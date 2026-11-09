"""Stage 5 figures (static PNG, matplotlib Agg): training curves per group and evaluation distributions.
Single-axis panels only; R and J never share a panel; fixed condition order and colours.

  python -E -s experiments/stage5/plots.py --train experiments/stage5/out/train --eval experiments/stage5/out/eval --out experiments/stage5/out/plots
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

COND_COLOR = {"uncoupled": "#5b6770", "initial": "#2a78b5", "trained": "#c8553d"}  # fixed order, never cycled
CONSTR = ("art", "jerk", "ext", "act")
CONSTR_COLOR = {"art": "#2a78b5", "jerk": "#c8553d", "ext": "#3f8f5a", "act": "#8a5bb0"}


def style(ax, title, ylabel):
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8)


def training(groups, out):
    g = np.array([x["group"] for x in groups])
    panels = [("R_mean", "Group mean reward R (target matching + constraints)", "R"),
              ("r_ah_mean", "Group mean r_ah = -|coord - 0.4514|", "r_ah"),
              ("coord_mean", "Right arm-hand coordination (R v1.1), controlled", "coordination"),
              ("loss", "Policy loss", "loss"), ("grad_norm_pre_clip", "Gradient norm (before clip 1.0)", "norm"),
              ("kl_mean", "KL per frame (cap 1.0)", "nats/frame"), ("beta_after", "beta (mean-shift magnitude)", "beta"),
              ("param_norm", "Controller parameter norm", "norm")]
    fig, axes = plt.subplots(len(panels) + 2, 1, figsize=(7.5, 2.0 * (len(panels) + 2)), constrained_layout=True)
    for ax, (k, title, yl) in zip(axes, panels):
        y = np.array([np.nan if x[k] is None else x[k] for x in groups], float)
        ax.plot(g, y, color="#2a78b5", linewidth=1.2)
        if k == "coord_mean":
            yt = np.array([np.nan if x["coord_twin_mean"] is None else x["coord_twin_mean"] for x in groups], float)
            ax.plot(g, yt, color="#5b6770", linewidth=1.0, label="uncoupled twin")
            ax.plot(g, y, color="#c8553d", linewidth=1.2, label="controlled")
            ax.legend(fontsize=8, frameon=False)
        style(ax, title, yl)
    for k in CONSTR:
        axes[-2].plot(g, [x["c_mean"][k] for x in groups], color=CONSTR_COLOR[k], linewidth=1.0, label=k)
        axes[-1].plot(g, [x["lambda_after"][k] for x in groups], color=CONSTR_COLOR[k], linewidth=1.0, label=k)
    style(axes[-2], "Group mean clipped constraint value c_k (<= 0 satisfied)", "c_k")
    style(axes[-1], "Dual variables lambda_k", "lambda")
    for ax in axes[-2:]:
        ax.legend(fontsize=8, frameon=False, ncol=4)
    axes[-1].set_xlabel("group (update)", fontsize=9)
    fig.savefig(out / "training_curves.png", dpi=130)
    plt.close(fig)


def evaluation(res, out):
    conds = ("uncoupled", "initial", "trained")
    for space, key, stat in (("R_space", "coord_arm_rhand", "Right arm-hand coordination, R v1.1 (primary)"),
                             ("J_space_descriptive", "coord_ah_J_R", "Right arm-hand coordination, J v1.1 (descriptive)")):
        if key not in res.get(space, {}):
            continue
        d = res[space][key]
        fig, axes = plt.subplots(2, 1, figsize=(7.5, 5.6), constrained_layout=True)
        ax = axes[0]
        for i, c in enumerate(conds):
            ci = d[c]["clip_mean"]
            if ci["mean"] is None:
                continue
            ax.errorbar([i], [ci["mean"]], yerr=[[ci["mean"] - ci["ci95"][0]], [ci["ci95"][1] - ci["mean"]]], fmt="o",
                        color=COND_COLOR[c], capsize=4, markersize=7)
        ax.set_xticks(range(3), conds)
        style(ax, f"{stat}: clip-mean with 95% bootstrap CI", "coordination")
        ax = axes[1]
        pc = np.array(d["trained-uncoupled"]["per_clip"], float)
        pc = pc[np.isfinite(pc)]
        ax.hist(pc, bins=30, color=COND_COLOR["trained"], edgecolor="white", linewidth=0.6)
        ax.axvline(0, color="#333333", linewidth=0.8)
        style(ax, "Per-clip paired difference, trained - uncoupled (common noise)", "clips")
        ax.set_xlabel("difference in coordination", fontsize=9)
        fig.savefig(out / f"eval_{space}_{key}.png", dpi=130)
        plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--eval", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    training(json.loads((Path(a.train) / "groups.json").read_text(encoding="utf-8")), out)
    if a.eval:
        evaluation(json.loads((Path(a.eval) / "eval_results.json").read_text(encoding="utf-8")), out)
    return sorted(p.name for p in out.glob("*.png"))


if __name__ == "__main__":
    print(main())
