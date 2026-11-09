"""E0.4 forward-kinematics sanity check on 5 dev reference (GT) clips (Stage 4 rev. 3.3a, §15.5).

Reference poses only: no generation, no training. The SMPL-X model files are licensed and
are read from models/smplx/smplx/ only; nothing derived from them except numbers is written.

Clips (pre-specified): the first 5 clips of the dev GT dump (index 0..4), full valid length.
SMPL-X input construction is upstream tools/visualize.py:build_smplx_input (neutral, betas 0,
flat_hand_mean, no PCA, flip_left_hand=True); body zeroed for the 11 unpredicted leading joints.

Checks and pass criteria (fixed before the run):
  C0 conversion   our call path equals upstream build_smplx_input exactly (max |diff| == 0).
  C1 finite       no NaN/Inf in the 6D input, the SMPL-X joints or the vertices.
  C2 bone length  every kinematic edge (55 joints) keeps its rest length in every frame:
                  max |len - rest| / rest < 1e-4.
  C3 wrist        the hand chains hang off the body-stream wrist joints: every wrist -> finger
                  base edge is in C2 and the hand root equals SMPL-X joint 20/21 (L/R). Diagnostic
                  only (not pass/fail): forearm-hand angle > 90 deg and wrist angular speed
                  > 45 deg/frame (Stage 2 D4) per clip.
  C4 left flip    finger flexion side. With the body in T-pose, the mean displacement of the four
                  non-thumb fingertips from the flat hand, along y, gives the flexion side per frame.
                  The right hand (never flipped) calibrates the side. Pass: the right hand and the
                  flipped left hand both put >= 90% of frames on the same side. The unflipped left
                  hand is reported as the contrast; if it also passes, C4 is "not discriminative".

    python -E -s experiments/stage4/e0/fk_sanity.py --out experiments/stage4/out/e0/fk_sanity
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK" / "tools"))
import visualize as upstream  # noqa: E402  (sets PYOPENGL_PLATFORM default; irrelevant for FK)

RUN = "debug0_eulerstepsize10_can1_anchor0_samples/seed102_clampstep0_h2s_dev_gf_s10.npy"
BODY = ROOT / "experiments/baseline/runs/body/h2s_dev_gf_s10" / RUN
HAND = ROOT / "experiments/baseline/runs/hand/h2s_dev_gf_s10" / RUN
MODELS = ROOT / "models" / "smplx"  # smplx.create appends model_type -> models/smplx/smplx/
CLIPS = range(5)
L_ELBOW, R_ELBOW, L_WRIST, R_WRIST = 18, 19, 20, 21
L_MID1, R_MID1 = 28, 43
L_TIPS, R_TIPS = [67, 68, 69, 70], [72, 73, 74, 75]  # index, middle, ring, pinky tips (smplx order)


def load(path):
    # Dumps are produced locally by our own sampling runs (dict pickled by np.save).
    return np.load(path, allow_pickle=True).item()


def build(body, lh, rh, flip):
    return upstream.build_smplx_input(torch.from_numpy(body), torch.from_numpy(lh), torch.from_numpy(rh),
                                      num_expression=10, flip_left_hand=flip)


def edges_len(j, parents):
    return np.linalg.norm(j[:, 1:55] - j[:, parents[1:55]], axis=-1)  # (T, 54)


def angle_deg(a, b):
    c = (a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))
    return np.rad2deg(np.arccos(np.clip(c, -1, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import smplx
    model = smplx.create(str(MODELS), model_type="smplx", gender="neutral", use_pca=False, flat_hand_mean=True,
                         num_betas=10, num_expression_coeffs=10, ext="npz").eval()
    parents = model.parents.numpy()
    with torch.no_grad():
        rest = model().joints[0].numpy()
    rest_len = np.linalg.norm(rest[1:55] - rest[parents[1:55]], axis=-1)
    # fingertip indices must sit on their own hand
    assert all(np.linalg.norm(rest[t] - rest[L_WRIST]) < np.linalg.norm(rest[t] - rest[R_WRIST]) for t in L_TIPS)
    assert all(np.linalg.norm(rest[t] - rest[R_WRIST]) < np.linalg.norm(rest[t] - rest[L_WRIST]) for t in R_TIPS)

    body_d, hand_d = load(BODY), load(HAND)
    per_clip = []
    for i in CLIPS:
        L = int(body_d["lengths"][0, i])
        name = str(body_d["video_names"][0, i])
        assert str(hand_d["video_names"][0, 2 * i]) == name == str(hand_d["video_names"][0, 2 * i + 1])
        body = body_d["gt_poses"][0, i, :, :L].T.copy()
        lh = hand_d["gt_poses"][0, 2 * i, :, :L].T.copy()
        rh = hand_d["gt_poses"][0, 2 * i + 1, :, :L].T.copy()
        r = {"clip": i, "name": name, "frames": L}

        kw = build(body, lh, rh, flip=True)
        ref = upstream.build_smplx_input(torch.from_numpy(body), torch.from_numpy(lh), torch.from_numpy(rh),
                                         num_expression=10, flip_left_hand=True)
        r["C0_max_abs_diff"] = max(float((kw[k] - ref[k]).abs().max()) for k in kw)

        with torch.no_grad():
            o = model(**kw)
        J, V = o.joints.numpy(), o.vertices.numpy()
        r["C1_nonfinite"] = int((~np.isfinite(body)).sum() + (~np.isfinite(lh)).sum() + (~np.isfinite(rh)).sum()
                                + (~np.isfinite(J)).sum() + (~np.isfinite(V)).sum())

        rel = np.abs(edges_len(J, parents) - rest_len) / rest_len
        r["C2_max_rel_bone_dev"] = float(rel.max())

        # C3: hand root is the body-stream wrist; diagnostics on wrist plausibility
        hand_edges = [j - 1 for j in range(25, 55) if parents[j] in (L_WRIST, R_WRIST)]
        r["C3_wrist_children"] = len(hand_edges)
        r["C3_wrist_edge_max_rel_dev"] = float(rel[:, hand_edges].max())
        for side, el, wr, mid in (("L", L_ELBOW, L_WRIST, L_MID1), ("R", R_ELBOW, R_WRIST, R_MID1)):
            ang = angle_deg(J[:, wr] - J[:, el], J[:, mid] - J[:, wr])
            r[f"C3diag_{side}_forearm_hand_angle_p95_deg"] = float(np.percentile(ang, 95))
            r[f"C3diag_{side}_frac_frames_angle_gt90"] = float((ang > 90).mean())
        Rb = upstream.rot6d_to_matrix(torch.from_numpy(body).reshape(L, 10, 6)).numpy().astype(np.float64)
        for side, k in (("L", 8), ("R", 9)):
            d = Rb[1:, k] @ np.swapaxes(Rb[:-1, k], -1, -2)
            sp = np.rad2deg(np.arccos(np.clip((np.trace(d, axis1=-2, axis2=-1) - 1) / 2, -1, 1)))
            r[f"C3diag_{side}_wrist_frames_speed_gt45"] = int((sp > 45).sum())

        # C4: flexion side with the body in T-pose (hand pose only)
        sides = {}
        for tag, flip in (("R", True), ("L_flip", True), ("L_noflip", False)):
            kh = build(body, lh, rh, flip)
            for k in ("body_pose", "jaw_pose", "expression"):
                kh[k] = torch.zeros_like(kh[k])
            with torch.no_grad():
                Jh = model(**kh).joints.numpy()
            tips = R_TIPS if tag == "R" else L_TIPS
            dy = (Jh[:, tips, 1] - rest[None, tips, 1]).mean(1)  # (T,)
            sides[tag] = dy
            r[f"C4_{tag}_frac_neg_y"] = float((dy < 0).mean())
            r[f"C4_{tag}_mean_dy_mm"] = float(dy.mean() * 1000)
        per_clip.append(r)
        print(json.dumps(r))

    # aggregate and verdicts
    allR = np.concatenate([[c["C4_R_frac_neg_y"]] for c in per_clip])
    flex_neg = np.mean([c["C4_R_frac_neg_y"] for c in per_clip]) >= 0.5  # right hand defines the side

    def side_frac(c, tag):
        f = c[f"C4_{tag}_frac_neg_y"]
        return f if flex_neg else 1 - f

    v = {
        "C0": all(c["C0_max_abs_diff"] == 0 for c in per_clip),
        "C1": all(c["C1_nonfinite"] == 0 for c in per_clip),
        "C2": max(c["C2_max_rel_bone_dev"] for c in per_clip) < 1e-4,
        "C3": all(c["C3_wrist_children"] == 10 and c["C3_wrist_edge_max_rel_dev"] < 1e-4 for c in per_clip),
    }
    c4_flip = all(side_frac(c, "R") >= 0.9 and side_frac(c, "L_flip") >= 0.9 for c in per_clip)
    c4_noflip = all(side_frac(c, "L_noflip") >= 0.9 for c in per_clip)
    v["C4"] = "not discriminative" if (c4_flip and c4_noflip) else c4_flip
    summary = {
        "clips": [c["name"] for c in per_clip],
        "flexion_side_from_right_hand": "-y (palm-down in T-pose)" if flex_neg else "+y",
        "right_hand_frac_neg_y_per_clip": allR.tolist(),
        "verdicts": v,
        "all_pass": all(x is True for x in v.values()),
        "model": "SMPL-X neutral (npz), betas 0, flat_hand_mean, no PCA",
        "label": "reference (pseudo-GT) poses; no generated output involved",
    }
    (out / "per_clip.json").write_text(json.dumps(per_clip, indent=1), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
