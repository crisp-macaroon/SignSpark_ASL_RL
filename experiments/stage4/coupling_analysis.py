"""Stage 4 design-validation analysis on existing best-of-N dumps (no new generation, no training).

Questions it answers for the MDP design (dev, first 256 clips, N candidates per clip):
  A1 Independence: is body-hand coordination of a matched pair (body_r, hand_r) different from a
     mismatched pair (body_r, hand_s), s != r?  Equal => streams are statistically independent
     given (text, length), so coupling can only come from text-locked timing, selection or
     explicit conditioning.
  A2 Timing determinism: correlation between speed profiles of two candidates of the same
     clip (same text and length, different noise), per stream. ~0 => timing is set by the
     noise, not by the text.
  A3 Selection headroom: best coordination achievable by choosing a (body, hand) pair among
     N x N, and whether choosing by coordination changes reference error (reward validity).
  A4 Handedness in the reference: fraction of clips whose right hand is more active, and
     whether that holds for generated hands.

    python experiments/stage4/coupling_analysis.py --body B.npy --hand H.npy --out DIR
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from evaluate_dumps import R_ARM, corr, load, rel_angle, stream_metrics, to_mats  # noqa: E402


def speed(x, L):
    R = to_mats(x[:, :L])
    return rel_angle(R[:-1], R[1:])  # (L-1, J)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    body, hand = load(args.body), load(args.hand)
    N, B = body["pred_poses"].shape[:2]
    L_all = np.asarray(body["lengths"])

    matched, mismatched, gt_coord = [], [], []
    tim_body, tim_rh, tim_gt_body_pred = [], [], []
    best_coord, mean_coord, sel_err, mean_err, rho_coord_err = [], [], [], [], []
    gt_right_more, pred_right_more = [], []
    null_best = []  # best of N x N pairs when the hands come from a different clip (different text)
    curve_n = [n for n in (1, 2, 4, 8, 16) if n <= N]
    curve = {n: [] for n in curve_n}
    gt_ratio, pred_ratio, swap_ratio = [], [], []
    rng = np.random.default_rng(0)
    for i in range(B):
        L = int(L_all[0, i])
        if L < 8:
            continue
        arm = [speed(body["pred_poses"][r, i], L)[:, R_ARM].mean(1) for r in range(N)]
        rh = [speed(hand["pred_poses"][r, 2 * i + 1], L).mean(1) for r in range(N)]
        lh = [speed(hand["pred_poses"][r, 2 * i], L).mean(1) for r in range(N)]
        arm_gt = speed(body["gt_poses"][0, i], L)[:, R_ARM].mean(1)
        rh_gt = speed(hand["gt_poses"][0, 2 * i + 1], L).mean(1)
        lh_gt = speed(hand["gt_poses"][0, 2 * i], L).mean(1)
        gt_coord.append(corr(arm_gt, rh_gt))

        C = np.array([[corr(arm[r], rh[s]) for s in range(N)] for r in range(N)])  # body r x hand s
        matched.append(np.nanmean(np.diag(C)))
        mismatched.append(np.nanmean(C[~np.eye(N, dtype=bool)]))

        # A2: same-text, different-noise timing agreement; and generated vs reference timing
        tim_body.append(np.nanmean([corr(arm[r], arm[s]) for r in range(N) for s in range(r + 1, N)]))
        tim_rh.append(np.nanmean([corr(rh[r], rh[s]) for r in range(N) for s in range(r + 1, N)]))
        tim_gt_body_pred.append(np.nanmean([corr(arm[r], arm_gt) for r in range(N)]))

        # A3: pair selection by coordination; reference error of the selected hand
        kf = np.zeros(L, dtype=bool)
        err = np.array([stream_metrics(hand["pred_poses"][s, 2 * i + 1], hand["gt_poses"][s, 2 * i + 1], kf, L,
                                       "rh")[0]["rh_err_deg"] for s in range(N)])
        r_best, s_best = np.unravel_index(np.nanargmax(C), C.shape)
        best_coord.append(C[r_best, s_best])
        mean_coord.append(np.nanmean(C))
        sel_err.append(err[s_best])
        mean_err.append(err.mean())
        col = np.nanmean(C, axis=0)  # mean coordination of hand s across bodies
        if np.nanstd(col) > 0:
            rho_coord_err.append(spearmanr(col, err).correlation)

        # A3 null: same selection, hands from another clip j (truncated to the shorter length)
        j = int(rng.integers(B - 1))
        j = j + (j >= i)
        Lm = min(L, int(L_all[0, j]))
        if Lm >= 8:
            rh_j = [speed(hand["pred_poses"][s, 2 * j + 1], Lm).mean(1) for s in range(N)]
            null_best.append(np.nanmax([[corr(arm[r][:Lm - 1], rh_j[s]) for s in range(N)] for r in range(N)]))

        # A3 curve: best of n x n pairs for n = 1, 2, 4, ... N (first n candidates)
        for n in curve_n:
            curve[n].append(np.nanmax(C[:n, :n]))

        # A4: handedness (total activity)
        gt_right_more.append(rh_gt.sum() > lh_gt.sum())
        pred_right_more.append(np.mean([rh[r].sum() > lh[r].sum() for r in range(N)]))
        gt_ratio.append(lh_gt.sum() / max(rh_gt.sum(), 1e-8))
        pred_ratio.append(np.mean([lh[r].sum() / max(rh[r].sum(), 1e-8) for r in range(N)]))
        # side-assignment rule: put the more active of the two generated hands on the right
        swap_ratio.append(np.mean([min(lh[r].sum(), rh[r].sum()) / max(lh[r].sum(), rh[r].sum(), 1e-8)
                                   for r in range(N)]))

    m = lambda x: float(np.nanmean(x))
    res = {
        "clips": len(matched), "N": int(N),
        "A1_coord_matched_pair": m(matched), "A1_coord_mismatched_pair": m(mismatched),
        "A1_coord_reference": m(gt_coord),
        "A2_timing_agreement_body_same_text": m(tim_body), "A2_timing_agreement_rhand_same_text": m(tim_rh),
        "A2_timing_body_pred_vs_reference": m(tim_gt_body_pred),
        "A3_coord_mean_over_pairs": m(mean_coord), "A3_coord_best_of_NxN_pairs": m(best_coord),
        "A3_null_best_of_NxN_pairs_other_clip_hands": m(null_best),
        "A3_rhand_err_mean_deg": m(mean_err), "A3_rhand_err_coord_selected_deg": m(sel_err),
        "A3_spearman_coord_vs_rhand_err_within_clip": m(rho_coord_err),
        "A4_frac_clips_right_more_active_reference": m(gt_right_more),
        "A4_frac_samples_right_more_active_generated": m(pred_right_more),
        "A4_LR_activity_ratio_reference": m(gt_ratio), "A4_LR_activity_ratio_generated": m(pred_ratio),
        "A4_LR_activity_ratio_after_side_assignment_rule": m(swap_ratio),
        **{f"A3_coord_best_of_{n}x{n}": m(curve[n]) for n in curve_n},
    }
    (out / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
