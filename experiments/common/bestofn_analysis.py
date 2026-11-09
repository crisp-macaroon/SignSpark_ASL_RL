"""Best-of-N headroom analysis over the N candidates written by sample.py (eval.candidate_num=N).

For every clip and candidate r: body / hand geodesic error vs the reference (non-keyframe frames)
and the sentence-level chrF of the SignSparK-BT translation of the candidate against the input
sentence. Reports
  * mean over candidates (expected single-sample quality),
  * oracle best-of-N by reference error (an upper bound; uses the reference, training-time only),
  * BT-selected best-of-N (test-time legal: only the input sentence is used), evaluated on the
    reference rotation error, i.e. does the BT verifier pick poses that are closer to the reference?
  * Spearman correlation between BT chrF and rotation error across candidates of the same clip.

    python experiments/common/bestofn_analysis.py --body B.npy --hand H.npy --out DIR
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr

from evaluate_dumps import load, stream_metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bt-model", default=str(Path(__file__).resolve().parents[2] / "models/SignSparK_BT/How2Sign"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    body, hand = load(args.body), load(args.hand)
    N, B = body["pred_poses"].shape[:2]

    rows = []
    for r in range(N):
        L = np.asarray(body["lengths"])[r]
        for i in range(B):
            Li = int(L[i])
            kf_b = np.asarray(body["keyframes"])[r, i].any(0)
            mb, _, _ = stream_metrics(body["pred_poses"][r, i], body["gt_poses"][r, i], kf_b, Li, "body")
            kf_h = np.asarray(hand["keyframes"])[r, 2 * i + 1].any(0)
            mh, _, _ = stream_metrics(hand["pred_poses"][r, 2 * i + 1], hand["gt_poses"][r, 2 * i + 1], kf_h, Li, "rhand")
            rows.append({"cand": r, "clip": i, "body_err": mb["body_err_nonkf_deg"], "rhand_err": mh["rhand_err_nonkf_deg"],
                         "body_artic": mb["body_artic_ratio"]})
    df = pd.DataFrame(rows)

    # BT sentence-level chrF of each candidate vs the input sentence (official normalisation)
    import signspark_bt.helpers as bt_helpers
    import signspark_bt.inference as bt_inf
    from signspark_bt.cli import _normalize
    from signspark_bt.data.sample_dumps import load_sample_dump
    from signspark_bt.metrics import chrf

    def safe_load_checkpoint(path, use_cuda=True):
        allow = [np._core.multiarray.scalar, np.dtype] + [getattr(np.dtypes, n) for n in dir(np.dtypes)
                                                           if n.endswith("DType")]
        with torch.serialization.safe_globals(allow):
            return torch.load(path, map_location="cuda" if use_cuda else "cpu", weights_only=True)

    bt_helpers.load_checkpoint = safe_load_checkpoint
    bt_inf.load_checkpoint = safe_load_checkpoint
    data_cfg = bt_helpers.load_config(Path(args.bt_model) / "config.yaml")["data"]
    model = bt_inf.make_back_translation_model(args.bt_model)
    chrf_scores = np.full((N, B), np.nan)
    for r in range(N):
        feats, raw_refs, _ = load_sample_dump(args.body, args.hand, poses="pred_poses", repetition=r)
        refs = [_normalize(x, data_cfg) for x in raw_refs]
        hyps = bt_inf.back_translate(model, feats)
        for i, (ref, hyp) in enumerate(zip(refs, hyps)):
            chrf_scores[r, i] = chrf(references=[ref], hypotheses=[hyp])
    df["bt_chrf"] = [chrf_scores[r, i] for r, i in zip(df["cand"], df["clip"])]
    df.to_csv(out / "candidates.csv", index=False)

    piv = {m: df.pivot(index="clip", columns="cand", values=m).to_numpy() for m in ("body_err", "rhand_err", "bt_chrf")}
    sel_bt = np.nanargmax(piv["bt_chrf"], axis=1)
    res = {"N": int(N), "clips": int(B)}
    for m in ("body_err", "rhand_err"):
        x = piv[m]
        res[m] = {"single_sample_mean": float(np.nanmean(x)),
                  "candidate0_mean": float(np.nanmean(x[:, 0])),
                  "oracle_best_of_N": float(np.nanmean(np.nanmin(x, axis=1))),
                  "oracle_worst_of_N": float(np.nanmean(np.nanmax(x, axis=1))),
                  "bt_selected": float(np.nanmean(x[np.arange(B), sel_bt])),
                  "within_clip_std": float(np.nanmean(np.nanstd(x, axis=1)))}
        rho = [spearmanr(piv["bt_chrf"][i], x[i]).correlation for i in range(B)
               if np.nanstd(piv["bt_chrf"][i]) > 0 and np.nanstd(x[i]) > 0]
        res[m]["spearman_btchrf_vs_err_mean"] = float(np.nanmean(rho)) if rho else None
    res["bt_chrf"] = {"single_sample_mean": float(np.nanmean(piv["bt_chrf"])),
                      "bt_selected_mean": float(np.nanmean(piv["bt_chrf"][np.arange(B), sel_bt]))}
    (out / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
