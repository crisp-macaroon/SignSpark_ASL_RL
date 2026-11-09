"""Rotation-space (space R) per-sample statistics for E2e (Stage 4 rev. 4.0 §6.0, §6.5, §15.3–15.4).

Conventions follow experiments/common/evaluate_dumps.py and experiments/stage4/coupling_analysis.py:
6D -> rotation matrix by Gram-Schmidt (float64); per-frame joint speed = geodesic angle between
consecutive frames (radians); all statistics over active frames 0..L-1 only.
"""

import numpy as np

R_ARM, L_ARM = [7, 9], [6, 8]  # R_Elbow, R_Wrist / L_Elbow, L_Wrist in the 10 predicted body joints
EXTREME = np.pi / 4  # 45 deg per frame


def to_mats(x):
    """x: (C, T) 6D rotations -> (T, J, 3, 3)."""
    d = x.T.astype(np.float64).reshape(x.shape[1], -1, 6)
    a1, a2 = d[..., :3], d[..., 3:6]
    b1 = a1 / np.linalg.norm(a1, axis=-1, keepdims=True)
    b2 = a2 - np.sum(b1 * a2, axis=-1, keepdims=True) * b1
    b2 = b2 / np.linalg.norm(b2, axis=-1, keepdims=True)
    return np.stack((b1, b2, np.cross(b1, b2, axis=-1)), axis=-2)


def angle(R):
    return np.arccos(np.clip((np.trace(R, axis1=-2, axis2=-1) - 1) / 2, -1, 1))


def joint_speed(R):
    """(T, J, 3, 3) -> (T-1, J) geodesic angle between consecutive frames."""
    return angle(np.swapaxes(R[:-1], -1, -2) @ R[1:])


def corr(a, b):
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def hand_stats(x, L):
    """One hand sequence (90, T), length L -> dict of per-sample scalars + per-frame activity signal."""
    R = to_mats(x[:, :L])
    w = joint_speed(R)                     # (L-1, 15)
    ang = angle(R)                         # (L, 15)
    s = w.mean(1)                          # per-frame activity s_hand(tau)
    return {
        "s": s,
        "A": float(s.sum()),               # activity A_s (App. G.6.1)
        "m1_speed": float(w.mean()),       # T2 (m1) mean angular speed
        "m2_artic": float(ang.std(0).mean()),  # T2 (m2) articulation
        "m3_jerk": float(np.abs(np.diff(w, axis=0)).mean()) if L > 2 else np.nan,  # T2 (m3) jerk
        "m4_angle": float(ang.mean()),     # T2 (m4) mean joint angle
        "extreme_frac": float((w.max(1) > EXTREME).mean()),  # gating (P-2): any hand joint > 45 deg/frame
        "extreme_frac_meanjoint": float((w.mean(1) > EXTREME).mean()),  # descriptive (P-2): mean over joints > 45
        "phi": np.concatenate([ang.mean(0), ang.std(0)]),   # 30-d joint-angle feature (15 x {mean, std})
    }


def arm_signals(xb, L):
    """Body sequence (60, T) -> per-frame arm speeds (mean of elbow + wrist), right and left."""
    w = joint_speed(to_mats(xb[:, :L]))
    return w[:, R_ARM].mean(1), w[:, L_ARM].mean(1)


def sample_record(xb, xl, xr, L):
    """All per-sample statistics used by T2, T3, T4, T5, T6 for one (clip, noise) sample."""
    hl, hr = hand_stats(xl, L), hand_stats(xr, L)
    arm_r, arm_l = arm_signals(xb, L)
    rec = {"L": L,
           "coord_arm_rhand": corr(arm_r, hr["s"]), "coord_arm_lhand": corr(arm_l, hl["s"]),
           "coord_lr": corr(hl["s"], hr["s"]),
           "A_L": hl["A"], "A_R": hr["A"], "X": float(np.log(hl["A"] / hr["A"])),
           "phi_L": hl["phi"], "phi_R": hr["phi"]}
    for side, h in (("L", hl), ("R", hr)):
        for k in ("m1_speed", "m2_artic", "m3_jerk", "m4_angle", "extreme_frac", "extreme_frac_meanjoint"):
            rec[f"{k}_{side}"] = h[k]
    return rec


def reference_record(xl, xr, L):
    """Reference hands of one clip: activities, log-ratio, left-hand feature."""
    hl, hr = hand_stats(xl, L), hand_stats(xr, L)
    return {"A_L": hl["A"], "A_R": hr["A"], "X": float(np.log(hl["A"] / hr["A"])), "phi_L": hl["phi"]}
