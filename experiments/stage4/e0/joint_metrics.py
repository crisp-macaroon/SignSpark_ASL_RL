"""E0.6 joint-space metrics on existing dev dumps (Stage 4 rev. 3.3a, §15.5; §7.2).

Released-checkpoint outputs only (R10): the dev GF and KF2P dumps already on disk (1 candidate,
repetition 0). Nothing is sampled. These are our joint-space measures, frame-aligned under the
oracle reference length (A1); they are NOT the paper's DTW-JPE / DTW-PA-JPE (SOKE protocol, not
reimplemented here) and must not be compared with the paper's tables.

Pre-specified (fixed before the run):
  Clips      all dev clips with length >= 8 (as in the Stage 4 coupling analysis).
  FK         SMPL-X neutral, betas 0, flat_hand_mean, no PCA, flip_left_hand=True (E0.4).
  Isolation  body error uses generated body + reference hands; hand error uses reference body +
             generated hands, so each stream is scored on its own output.
  J1/J2      body MPJPE / PA-MPJPE (mm) over the 7 body joints whose position varies (head,
             shoulders, elbows, wrists); PA = per-frame similarity Procrustes.
  J3/J4      hand MPJPE / PA-MPJPE (mm) per side over 15 hand joints + 5 fingertips, wrist-relative.
  Frames     all valid frames; for KF2P also non-keyframe frames only (keyframes are copied).
  Aggregate  mean over clips with a 95% percentile bootstrap CI over clips (2000 draws, seed 0).
  V1         validity of the rotation-space error: per-clip Spearman between geodesic error (deg)
             and the joint-space MPJPE of the same stream.
  V2         coordination: per-clip corr(right-arm angular speed, right-hand finger angular speed)
             in rotation space vs corr(right-wrist linear speed, mean right-finger linear speed in
             the wrist's local frame) in joint space; Spearman across clips and corpus means.
  V3         dominance: per-clip log(A_L/A_R) with A = summed mean finger angular speed (rotation)
             vs summed mean finger linear speed in the wrist's local frame (joint); Spearman and
             corpus means.
  All V statistics are descriptive (no pass/fail rule was pre-registered for E0.6).
  Amendment before the full run: a 10-clip debug run (scratch output, discarded) showed that
  wrist-relative finger positions in the world frame also move when the forearm/wrist rotates
  (body stream), confounding V2/V3; finger speeds are therefore taken in the wrist's local frame.

    python -E -s experiments/stage4/e0/joint_metrics.py --out experiments/stage4/out/e0/joint_metrics
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK" / "tools"))
import visualize as upstream  # noqa: E402

RUN = "debug0_eulerstepsize10_can1_anchor0_samples/seed102_clampstep0_h2s_dev_{r}_s10.npy"
MODELS = ROOT / "models" / "smplx"
BODY_J = [15, 16, 17, 18, 19, 20, 21]
L_WRIST, R_WRIST = 20, 21
L_HAND = list(range(25, 40)) + list(range(66, 71))
R_HAND = list(range(40, 55)) + list(range(71, 76))
R_ARM_6D = [7, 9]  # R_Elbow, R_Wrist in the 10 predicted body joints
R_CHAIN_6D, L_CHAIN_6D = [2, 5, 7, 9], [1, 4, 6, 8]  # collar, shoulder, elbow, wrist
REGIMES = ("gf", "kf2p")


def load(path):
    # Dumps are produced locally by our own sampling runs (dict pickled by np.save).
    return np.load(path, allow_pickle=True).item()


def mats(x6):  # (T, C) -> (T, J, 3, 3) float64
    T = x6.shape[0]
    return upstream.rot6d_to_matrix(torch.from_numpy(x6).double().reshape(T, -1, 6)).numpy()


def geo(A, B):  # geodesic angle (rad) between rotation stacks
    R = np.swapaxes(A, -1, -2) @ B
    return np.arccos(np.clip((np.trace(R, axis1=-2, axis2=-1) - 1) / 2, -1, 1))


def ang_speed(x6):  # (T, C) -> (T-1, J)
    R = mats(x6)
    return geo(R[:-1], R[1:])


def corr(a, b):
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def procrustes(P, G):  # per-frame similarity alignment of P onto G; (T, N, 3)
    mp, mg = P.mean(1, keepdims=True), G.mean(1, keepdims=True)
    p, g = P - mp, G - mg
    U, S, Vt = np.linalg.svd(np.swapaxes(p, 1, 2) @ g)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.ones_like(S); D[:, -1] = d
    R = U @ (D[:, :, None] * Vt)
    s = (S * D).sum(1) / (p ** 2).sum((1, 2))
    return s[:, None, None] * p @ R + mg


def err(P, G, mask):
    e = np.linalg.norm(P - G, axis=-1).mean(1)[mask] * 1000
    pa = np.linalg.norm(procrustes(P, G) - G, axis=-1).mean(1)[mask] * 1000
    return float(e.mean()), float(pa.mean())


def boot(x, rng):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return None
    idx = rng.integers(0, len(x), (2000, len(x)))
    m = x[idx].mean(1)
    return {"mean": float(x.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(x))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="debug only: first N clips")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import smplx
    model = smplx.create(str(MODELS), model_type="smplx", gender="neutral", use_pca=False, flat_hand_mean=True,
                         num_betas=10, num_expression_coeffs=10, ext="npz").eval()

    def fk(b, lh, rh):
        kw = upstream.build_smplx_input(torch.from_numpy(b), torch.from_numpy(lh), torch.from_numpy(rh),
                                        num_expression=10, flip_left_hand=True)
        with torch.no_grad():
            return model(**kw).joints.numpy().astype(np.float64)

    d = {(s, r): load(ROOT / f"experiments/baseline/runs/{s}/h2s_dev_{r}_s10" / RUN.format(r=r))
         for s in ("body", "hand") for r in REGIMES}
    B = d["body", "gf"]["lengths"].shape[1]
    B = min(B, args.limit) if args.limit else B
    rows, t0 = [], time.time()
    for i in range(B):
        L = int(d["body", "gf"]["lengths"][0, i])
        if L < 8:
            continue
        name = str(d["body", "gf"]["video_names"][0, i])
        g = lambda s, r, src, k: d[s, r][src][0, k, :, :L].T.copy()
        gb, glh, grh = g("body", "gf", "gt_poses", i), g("hand", "gf", "gt_poses", 2 * i), g("hand", "gf", "gt_poses", 2 * i + 1)
        JG = fk(gb, glh, grh)
        rowbase = {"clip": i, "name": name, "frames": L}

        # reference-side descriptors (shared by regimes)
        def descr(J, b6, lh6, rh6):
            wr_sp = np.linalg.norm(np.diff(J[:, R_WRIST], axis=0), axis=-1)
            Rb = mats(b6)

            def fr(H, W, chain):  # finger speed in the wrist's local frame (removes forearm/wrist rotation)
                G = Rb[:, chain[0]] @ Rb[:, chain[1]] @ Rb[:, chain[2]] @ Rb[:, chain[3]]  # spine/pelvis are identity
                loc = np.einsum("tji,tnj->tni", G, J[:, H] - J[:, [W]])
                return np.linalg.norm(np.diff(loc, axis=0), axis=-1).mean(1)
            frR, frL = fr(R_HAND, R_WRIST, R_CHAIN_6D), fr(L_HAND, L_WRIST, L_CHAIN_6D)
            arm = ang_speed(b6)[:, R_ARM_6D].mean(1)
            sR, sL = ang_speed(rh6).mean(1), ang_speed(lh6).mean(1)
            return {"coord_rot": corr(arm, sR), "coord_joint": corr(wr_sp, frR),
                    "dom_rot": float(np.log(sL.sum() / max(sR.sum(), 1e-12))),
                    "dom_joint": float(np.log(frL.sum() / max(frR.sum(), 1e-12)))}

        ref = descr(JG, gb, glh, grh)
        for r in REGIMES:
            pb, plh, prh = g("body", r, "pred_poses", i), g("hand", r, "pred_poses", 2 * i), g("hand", r, "pred_poses", 2 * i + 1)
            JB = fk(pb, glh, grh)          # generated body, reference hands
            JH = fk(gb, plh, prh)          # reference body, generated hands
            kb = d["body", r]["keyframes"][0, i, :, :L].any(0)
            kh = d["hand", r]["keyframes"][0, 2 * i, :, :L].any(0) | d["hand", r]["keyframes"][0, 2 * i + 1, :, :L].any(0)
            row = dict(rowbase, regime=r)
            for tag, mb, mh in (("all", np.ones(L, bool), np.ones(L, bool)), ("nonkf", ~kb, ~kh)):
                if tag == "nonkf" and (r == "gf" or not mb.any() or not mh.any()):
                    continue
                row[f"J1_body_mpjpe_{tag}"], row[f"J2_body_pa_{tag}"] = err(JB[:, BODY_J], JG[:, BODY_J], mb)
                for side, H, W in (("L", L_HAND, L_WRIST), ("R", R_HAND, R_WRIST)):
                    P, G = JH[:, H] - JH[:, [W]], JG[:, H] - JG[:, [W]]
                    row[f"J3_{side}hand_mpjpe_{tag}"], row[f"J4_{side}hand_pa_{tag}"] = err(P, G, mh)
            row["rot_body_err_deg"] = float(np.rad2deg(geo(mats(pb), mats(gb))).mean())
            row["rot_Lhand_err_deg"] = float(np.rad2deg(geo(mats(plh), mats(glh))).mean())
            row["rot_Rhand_err_deg"] = float(np.rad2deg(geo(mats(prh), mats(grh))).mean())
            gen = descr(fk(pb, plh, prh), pb, plh, prh)
            row.update({f"ref_{k}": v for k, v in ref.items()})
            row.update({f"gen_{k}": v for k, v in gen.items()})
            rows.append(row)
        if i % 100 == 0:
            print(f"clip {i}/{B}  {time.time() - t0:.0f}s", flush=True)

    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("clip", "name", "frames", "regime"), k))
    with open(out / "per_clip.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    rng = np.random.default_rng(0)
    summ = {"label": "released-checkpoint outputs, dev split; frame-aligned joint-space measures; "
                     "not DTW-JPE and not a paper reproduction (R10)", "regimes": {}}
    for r in REGIMES:
        R = [x for x in rows if x["regime"] == r]
        col = lambda k: np.array([x.get(k, np.nan) for x in R], float)
        s = {k: boot(col(k), rng) for k in keys if k.startswith(("J1", "J2", "J3", "J4", "rot_")) and np.isfinite(col(k)).any()}
        sp = lambda a, b: float(spearmanr(col(a), col(b), nan_policy="omit").correlation)
        s["V1_spearman_rot_vs_joint"] = {"body": sp("rot_body_err_deg", "J1_body_mpjpe_all"),
                                         "Lhand": sp("rot_Lhand_err_deg", "J3_Lhand_mpjpe_all"),
                                         "Rhand": sp("rot_Rhand_err_deg", "J3_Rhand_mpjpe_all")}
        for who in ("ref", "gen"):
            s[f"V2_coord_{who}"] = {"spearman_rot_vs_joint": sp(f"{who}_coord_rot", f"{who}_coord_joint"),
                                    "mean_rot": boot(col(f"{who}_coord_rot"), rng),
                                    "mean_joint": boot(col(f"{who}_coord_joint"), rng)}
            s[f"V3_dom_{who}"] = {"spearman_rot_vs_joint": sp(f"{who}_dom_rot", f"{who}_dom_joint"),
                                  "mean_logratio_rot": boot(col(f"{who}_dom_rot"), rng),
                                  "mean_logratio_joint": boot(col(f"{who}_dom_joint"), rng)}
        summ["regimes"][r] = s
    summ["clips"] = len({x["clip"] for x in rows})
    summ["seconds"] = round(time.time() - t0)
    (out / "summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
