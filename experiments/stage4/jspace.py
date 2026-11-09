"""SMPL-X joint-space (space J) statistics shared by R0 and E2e-J (Stage 4 rev. 4.0 §6.0; E0.4 FK setup;
E0.6 definitions, extended to the left side and to L-R coordination as §6.0 specifies).

  arm signal   s_arm,s(tau)  = linear speed of the side-s wrist joint (world frame)
  hand signal  s_hand,s(tau) = mean linear speed of the 15 hand joints + 5 fingertips in the side-s wrist's local
                               frame (forearm and wrist rotation removed; E0.6 amendment)
  coord_ah_J(s) = corr_tau(s_arm,s, s_hand,s);  coord_lr_J = corr_tau(s_hand,L, s_hand,R)
  A_s^J = sum_tau s_hand,s;  dom_J = log(A_L^J / A_R^J)
FK: SMPL-X neutral, betas 0, flat_hand_mean, no PCA, flip_left_hand=True, via upstream build_smplx_input.
The SMPL-X model files are licensed and read from models/smplx/smplx/ only.
"""

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK" / "tools"))
import visualize as upstream  # noqa: E402  (rot6d, build_smplx_input; upstream file, unmodified)

L_WRIST, R_WRIST = 20, 21
L_HAND = list(range(25, 40)) + list(range(66, 71))
R_HAND = list(range(40, 55)) + list(range(71, 76))
CHAIN = {"L": [1, 4, 6, 8], "R": [2, 5, 7, 9]}  # collar, shoulder, elbow, wrist in the 10 predicted body joints


def load_model():
    import smplx
    m = smplx.create(str(ROOT / "models" / "smplx"), model_type="smplx", gender="neutral", use_pca=False,
                     flat_hand_mean=True, num_betas=10, num_expression_coeffs=10, ext="npz").eval()
    with torch.no_grad():
        rest = m().joints[0].numpy().astype(np.float64)
    parents = m.parents.numpy()
    rest_len = np.linalg.norm(rest[1:55] - rest[parents[1:55]], axis=-1)
    return m, rest, parents, rest_len


def mats(x6):
    T = x6.shape[0]
    return upstream.rot6d_to_matrix(torch.from_numpy(np.ascontiguousarray(x6)).double().reshape(T, -1, 6)).numpy()


def corr(a, b):
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def fk(model, b6, lh6, rh6):
    kw = upstream.build_smplx_input(torch.from_numpy(np.ascontiguousarray(b6)).float(),
                                    torch.from_numpy(np.ascontiguousarray(lh6)).float(),
                                    torch.from_numpy(np.ascontiguousarray(rh6)).float(),
                                    num_expression=10, flip_left_hand=True)
    with torch.no_grad():
        return model(**kw).joints.numpy().astype(np.float64)


def jstats(ctx, b6, lh6, rh6):
    """b6 (L, 60), lh6 (L, 90), rh6 (L, 90) rotations (6D) over active frames -> space-J statistics + FK health."""
    model, rest, parents, rest_len = ctx
    J = fk(model, b6, lh6, rh6)
    finite = bool(np.isfinite(J).all())
    bone = float((np.abs(np.linalg.norm(J[:, 1:55] - J[:, parents[1:55]], axis=-1) - rest_len) / rest_len).max()) if finite else np.inf
    Rb = mats(b6)
    out = {"fk_finite": finite, "fk_bone_max_rel_dev": bone}
    hand = {}
    for s, H, W in (("L", L_HAND, L_WRIST), ("R", R_HAND, R_WRIST)):
        c = CHAIN[s]
        G = Rb[:, c[0]] @ Rb[:, c[1]] @ Rb[:, c[2]] @ Rb[:, c[3]]
        loc = np.einsum("tji,tnj->tni", G, J[:, H] - J[:, [W]])
        hand[s] = np.linalg.norm(np.diff(loc, axis=0), axis=-1).mean(1)
        arm = np.linalg.norm(np.diff(J[:, W], axis=0), axis=-1)
        out[f"coord_ah_J_{s}"] = corr(arm, hand[s])
        out[f"A_J_{s}"] = float(hand[s].sum())
    out["coord_lr_J"] = corr(hand["L"], hand["R"])
    out["dom_J"] = float(np.log(out["A_J_L"] / out["A_J_R"])) if out["A_J_R"] > 0 and out["A_J_L"] > 0 else np.nan
    return out
