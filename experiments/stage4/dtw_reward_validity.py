"""Stage 4 reward-validity checks for a timing-tolerant reference reward (DTW), on existing
best-of-N dumps (no new generation, no training). Training-time reward candidate:
    R_dtw(x, ref) = -DTW(x, ref) / (len(x) + len(ref)),  Euclidean cost on 6D rotation features.

  V1 Discrimination: is DTW(sample_i, ref_i) < DTW(sample_i, ref_j) for a length-matched other
     clip j? If not, samples carry no clip-specific content the reward could amplify.
  V2 Exploitable spread and side effects: within-clip spread over N candidates, and what
     selecting the DTW-best candidate does to pointwise error and articulation.
  V3 Collapse test: does a static pose (dataset mean, or the clip's own mean pose) score better
     than real samples? If yes, the reward alone rewards mean-collapse.

    python experiments/stage4/dtw_reward_validity.py --dump X.npy --stream body|rhand --out DIR
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from evaluate_dumps import load, stream_metrics  # noqa: E402


def dtw_batch(A, B, la, lb, dev="cuda"):
    """Batched DTW with Euclidean frame cost. A: (P, T1, C), B: (P, T2, C) zero-padded;
    la, lb: valid lengths. Returns D[la, lb] / (la + lb)."""
    A, B = torch.as_tensor(A, device=dev, dtype=torch.float32), torch.as_tensor(B, device=dev, dtype=torch.float32)
    P, T1, _ = A.shape
    T2 = B.shape[1]
    C = torch.cdist(A, B)  # (P, T1, T2)
    D = torch.full((P, T1 + 1, T2 + 1), float("inf"), device=dev)
    D[:, 0, 0] = 0
    for d in range(2, T1 + T2 + 1):
        i = torch.arange(max(1, d - T2), min(T1, d - 1) + 1, device=dev)
        j = d - i
        best = torch.minimum(torch.minimum(D[:, i - 1, j], D[:, i, j - 1]), D[:, i - 1, j - 1])
        D[:, i, j] = C[:, i - 1, j - 1] + best
    la, lb = torch.as_tensor(la, device=dev), torch.as_tensor(lb, device=dev)
    return (D[torch.arange(P, device=dev), la, lb] / (la + lb)).cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--stream", choices=["body", "rhand"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    d = load(args.dump)
    pred, gt = d["pred_poses"], d["gt_poses"]
    N = pred.shape[0]
    if args.stream == "rhand":  # interleaved L0,R0,L1,R1,...
        pred, gt = pred[:, 1::2], gt[:, 1::2]
        L = np.asarray(d["lengths"])[0, 1::2]
    else:
        L = np.asarray(d["lengths"])[0]
    B, Cdim, T = pred.shape[1:]
    L = np.minimum(L, T).astype(int)
    rng = np.random.default_rng(0)

    # length-matched partner j for every clip i (closest length among other clips)
    order = np.argsort(L)
    partner = np.empty(B, dtype=int)
    for k, i in enumerate(order):
        partner[i] = order[k + 1] if k + 1 < B else order[k - 1]

    def seq(x):  # (C, T) -> (T, C)
        return np.ascontiguousarray(x.T)

    ds_mean = np.concatenate([gt[0, i][:, :L[i]] for i in range(B)], axis=1).mean(1)
    rows = []
    for r in range(N):
        A = np.stack([seq(pred[r, i]) for i in range(B)])
        Ref = np.stack([seq(gt[0, i]) for i in range(B)])
        Ref_j = Ref[partner]
        matched = dtw_batch(A, Ref, L, L)
        mism = dtw_batch(A, Ref_j, L, L[partner])
        for i in range(B):
            m, _, _ = stream_metrics(pred[r, i], gt[0, i], np.zeros(T, bool), L[i], "s")
            rows.append({"cand": r, "clip": i, "dtw": matched[i], "dtw_mismatch": mism[i],
                         "err": m["s_err_deg"], "artic": m["s_artic_ratio"]})
    # controls (computed once)
    Ref = np.stack([seq(gt[0, i]) for i in range(B)])
    static_ds = np.repeat(ds_mean[None, None, :], T, axis=1).repeat(B, axis=0)
    static_own = np.stack([np.repeat(gt[0, i][:, :L[i]].mean(1)[None, :], T, axis=0) for i in range(B)])
    other_gt = Ref[partner]
    ctrl = {"static_dataset_mean_pose": dtw_batch(static_ds, Ref, L, L),
            "static_own_clip_mean_pose": dtw_batch(static_own, Ref, L, L),
            "real_motion_other_clip": dtw_batch(other_gt, Ref, L[partner], L)}

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(out / "candidates.csv", index=False)
    piv = {k: df.pivot(index="clip", columns="cand", values=k).to_numpy() for k in ("dtw", "dtw_mismatch", "err", "artic")}
    sel = np.argmin(piv["dtw"], axis=1)
    ar = np.arange(B)
    res = {
        "stream": args.stream, "clips": int(B), "N": int(N),
        "V1_dtw_matched_mean": float(piv["dtw"].mean()),
        "V1_dtw_mismatched_mean": float(piv["dtw_mismatch"].mean()),
        "V1_frac_matched_lower": float((piv["dtw"] < piv["dtw_mismatch"]).mean()),
        "V2_within_clip_std": float(piv["dtw"].std(1).mean()),
        "V2_between_clip_std": float(piv["dtw"].mean(1).std()),
        "V2_err_mean_deg": float(piv["err"].mean()), "V2_err_dtw_selected_deg": float(piv["err"][ar, sel].mean()),
        "V2_artic_mean": float(piv["artic"].mean()), "V2_artic_dtw_selected": float(piv["artic"][ar, sel].mean()),
        "V3_samples_dtw_mean": float(piv["dtw"].mean()),
        **{f"V3_{k}": float(v.mean()) for k, v in ctrl.items()},
        "V3_frac_clips_static_dataset_beats_mean_sample": float((ctrl["static_dataset_mean_pose"] < piv["dtw"].mean(1)).mean()),
        "V3_frac_clips_static_own_beats_mean_sample": float((ctrl["static_own_clip_mean_pose"] < piv["dtw"].mean(1)).mean()),
    }
    (out / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
