"""Licence-free evaluation of SignSparK sample dumps (rotation space + back-translation).

Reads the per-stream .npy dumps written by upstream sample.py for one (split, regime) and
reports, per clip and aggregated:
  * geodesic rotation error vs the reference (degrees), on all valid frames and on
    non-keyframe frames only (keyframes are copied from the reference in KF2P);
  * articulation ratio: temporal std of joint rotation angle, generated / reference
    (< 1 = less articulated than the reference, i.e. regression toward the mean);
  * speed and jerk ratios, generated / reference;
  * coordination: Pearson correlation between right-arm angular speed (body stream) and
    right-hand finger angular speed (hand stream), and between left- and right-hand speed,
    for generated vs reference;
  * back-translation (SignSparK-BT, How2Sign model): corpus BLEU/chrF/ROUGE for reference
    poses and for generated poses, via the official signspark_bt functions.
No SMPL-X / MANO is used, so none of these numbers are comparable to the paper's JPE.

    python experiments/common/evaluate_dumps.py --body B.npy --hand H.npy [--face F.npy] --out DIR
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

BODY_KEPT = ["Neck", "L_Collar", "R_Collar", "Head", "L_Shoulder", "R_Shoulder",
             "L_Elbow", "R_Elbow", "L_Wrist", "R_Wrist"]
R_ARM = [BODY_KEPT.index("R_Elbow"), BODY_KEPT.index("R_Wrist")]


def rot6d_to_matrix(d6):
    a1, a2 = d6[..., :3], d6[..., 3:6]
    b1 = a1 / np.linalg.norm(a1, axis=-1, keepdims=True)
    b2 = a2 - np.sum(b1 * a2, axis=-1, keepdims=True) * b1
    b2 = b2 / np.linalg.norm(b2, axis=-1, keepdims=True)
    return np.stack((b1, b2, np.cross(b1, b2, axis=-1)), axis=-2)


def angle(R):
    return np.arccos(np.clip((np.trace(R, axis1=-2, axis2=-1) - 1) / 2, -1, 1))


def rel_angle(A, B):
    return angle(np.swapaxes(A, -1, -2) @ B)


def to_mats(x):  # (C, T) -> (T, J, 3, 3)
    return rot6d_to_matrix(x.T.astype(np.float64).reshape(x.shape[1], -1, 6))


def corr(a, b):
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def load(path):
    # Dumps are produced locally by our own sampling runs (dict pickled by np.save).
    return np.load(path, allow_pickle=True).item()


def stream_metrics(pred, gt, mask_kf, length, prefix):
    P, G = to_mats(pred[:, :length]), to_mats(gt[:, :length])
    err = np.rad2deg(rel_angle(P, G))  # (T, J)
    kf = mask_kf[:length]
    out = {f"{prefix}_err_deg": float(err.mean()),
           f"{prefix}_err_nonkf_deg": float(err[~kf].mean()) if (~kf).any() else np.nan}
    ap, ag = angle(P), angle(G)
    out[f"{prefix}_artic_ratio"] = float(ap.std(0).mean() / max(ag.std(0).mean(), 1e-8))
    if length > 2:
        sp, sg = rel_angle(P[:-1], P[1:]), rel_angle(G[:-1], G[1:])
        out[f"{prefix}_speed_ratio"] = float(sp.mean() / max(sg.mean(), 1e-8))
        jp, jg = np.abs(np.diff(sp, axis=0)).mean(), np.abs(np.diff(sg, axis=0)).mean()
        out[f"{prefix}_jerk_ratio"] = float(jp / max(jg, 1e-8))
        return out, sp, sg
    return out, None, None


def back_translation_scores(args, out, r):
    """Official SignSparK-BT scoring path (signspark_bt.cli._score): references are normalised
    exactly like the BT training text and scored with the config's dataset version/level."""
    import signspark_bt.helpers as bt_helpers
    import signspark_bt.inference as bt_inf
    from signspark_bt.cli import _normalize
    from signspark_bt.data.sample_dumps import load_sample_dump
    from signspark_bt.metrics import score_translations

    def safe_load_checkpoint(path, use_cuda=True):
        # Upstream uses weights_only=False (arbitrary pickle); allow only numpy scalar/dtype.
        allow = [np._core.multiarray.scalar, np.dtype] + [getattr(np.dtypes, n) for n in dir(np.dtypes)
                                                           if n.endswith("DType")]
        with torch.serialization.safe_globals(allow):
            return torch.load(path, map_location="cuda" if use_cuda else "cpu", weights_only=True)

    bt_helpers.load_checkpoint = safe_load_checkpoint
    bt_inf.load_checkpoint = safe_load_checkpoint
    data_cfg = bt_helpers.load_config(Path(args.bt_model) / "config.yaml")["data"]
    model = bt_inf.make_back_translation_model(args.bt_model)
    bt = {}
    for poses in ("gt_poses", "pred_poses"):
        feats, raw_refs, clip_names = load_sample_dump(args.body, args.hand, poses=poses, repetition=r)
        refs = [_normalize(x, data_cfg) for x in raw_refs]
        hyps = bt_inf.back_translate(model, feats)
        bt[poses] = score_translations(refs, hyps, dataset_version=data_cfg.get("version", ""),
                                       level=data_cfg.get("level", "word"))
        pd.DataFrame({"clip_id": clip_names, "ref": refs, "hyp": hyps}).to_csv(out / f"bt_{poses}.csv", index=False)
    return bt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--face")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bt-model", default=str(Path(__file__).resolve().parents[2] / "models/SignSparK_BT/How2Sign"))
    ap.add_argument("--repetition", type=int, default=0)
    ap.add_argument("--no-bt", action="store_true")
    ap.add_argument("--bt-only", action="store_true", help="recompute back-translation only, keep metrics")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    r = args.repetition
    if args.bt_only:
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        summary["back_translation"] = back_translation_scores(args, out, r)
        (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
        print(json.dumps(summary["back_translation"], indent=0, default=float))
        return

    body, hand = load(args.body), load(args.hand)
    face = load(args.face) if args.face else None
    names = np.asarray(body["video_names"])[r]
    lengths = np.asarray(body["lengths"])[r]
    hnames = np.asarray(hand["video_names"])[r]
    assert all(h.startswith(n) for h, n in zip(hnames[::2], names)), "hand/body clip order mismatch"
    if face is not None:
        assert list(np.asarray(face["video_names"])[r]) == list(names), "face/body clip order mismatch"

    rows = []
    for i, name in enumerate(names):
        L = int(lengths[i])
        row = {"clip_id": str(name), "T_eval": L}
        kf_b = np.asarray(body["keyframes"])[r, i].any(0)
        m, spb, sgb = stream_metrics(body["pred_poses"][r, i], body["gt_poses"][r, i], kf_b, L, "body")
        row.update(m)
        row["n_kf"] = int(kf_b[:L].sum())
        hand_speeds = {}
        for side, j in (("lhand", 2 * i), ("rhand", 2 * i + 1)):
            kf_h = np.asarray(hand["keyframes"])[r, j].any(0)
            m, sp, sg = stream_metrics(hand["pred_poses"][r, j], hand["gt_poses"][r, j], kf_h, L, side)
            row.update(m)
            hand_speeds[side] = (sp, sg)
        if face is not None:
            kf_f = np.asarray(face["keyframes"])[r, i].any(0)
            fp, fg = face["pred_poses"][r, i][:, :L], face["gt_poses"][r, i][:, :L]
            m, _, _ = stream_metrics(fp[:6], fg[:6], kf_f, L, "jaw")
            row.update(m)
            row["expr_l2"] = float(np.linalg.norm(fp[6:] - fg[6:], axis=0).mean())
            row["expr_artic_ratio"] = float(fp[6:].std(1).mean() / max(fg[6:].std(1).mean(), 1e-8))
        if spb is not None:
            arm_p, arm_g = spb[:, R_ARM].mean(1), sgb[:, R_ARM].mean(1)
            rh_p, rh_g = hand_speeds["rhand"][0].mean(1), hand_speeds["rhand"][1].mean(1)
            lh_p, lh_g = hand_speeds["lhand"][0].mean(1), hand_speeds["lhand"][1].mean(1)
            row.update({"coord_arm_rhand_pred": corr(arm_p, rh_p), "coord_arm_rhand_gt": corr(arm_g, rh_g),
                        "coord_lr_hand_pred": corr(lh_p, rh_p), "coord_lr_hand_gt": corr(lh_g, rh_g)})
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out / "per_clip.csv", index=False)

    def ci(x):
        x = np.asarray(x, float)
        x = x[np.isfinite(x)]
        rng = np.random.default_rng(0)
        boots = [rng.choice(x, len(x)).mean() for _ in range(1000)]
        return {"mean": float(x.mean()), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                "n": int(len(x))}

    summary = {"body": args.body, "hand": args.hand, "face": args.face, "repetition": r,
               "metrics": {c: ci(df[c]) for c in df.columns if c not in ("clip_id",)}}

    if not args.no_bt:
        summary["back_translation"] = back_translation_scores(args, out, r)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: v["mean"] for k, v in summary["metrics"].items()}, indent=0))
    if "back_translation" in summary:
        print(json.dumps(summary["back_translation"], indent=0, default=float))


if __name__ == "__main__":
    main()
