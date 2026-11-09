"""Chance level for the arm-hand / left-right speed-correlation coordination metric.

Pairs the reference right-arm speed of clip i with the reference hand speeds of a random
other clip j (both truncated to the shorter length), i.e. motion with realistic statistics
but no shared timing. Uses the gt_poses stored in the body/hand sample dumps.

    python experiments/common/coordination_null.py --body B.npy --hand H.npy
"""

import argparse
import json

import numpy as np

from evaluate_dumps import R_ARM, corr, load, rel_angle, to_mats


def speeds(x, L):
    R = to_mats(x[:, :L])
    return rel_angle(R[:-1], R[1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    body, hand = load(args.body), load(args.hand)
    L = np.asarray(body["lengths"])[0]
    n = len(L)
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(n)
    arm_rh, lr = [], []
    for i in range(n):
        j = perm[i] if perm[i] != i else perm[(i + 1) % n]
        m = int(min(L[i], L[j]))
        if m < 4:
            continue
        arm = speeds(body["gt_poses"][0, i], m)[:, R_ARM].mean(1)
        rh = speeds(hand["gt_poses"][0, 2 * j + 1], m).mean(1)
        lh_i = speeds(hand["gt_poses"][0, 2 * i], m).mean(1)
        arm_rh.append(corr(arm, rh))
        lr.append(corr(lh_i, rh))
    out = {"null_arm_rhand_mean": float(np.nanmean(arm_rh)), "null_lr_hand_mean": float(np.nanmean(lr)),
           "n": int(np.isfinite(arm_rh).sum())}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
