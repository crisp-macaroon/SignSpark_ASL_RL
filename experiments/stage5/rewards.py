"""Stage 5 reward (design §2; A2-A4): target matching toward the frozen R-space right arm-hand coordination target,
registered constraints via dual ascent. All statistics: space R v1.1 (validity layer) on the registered v1 metric.

  R = r_ah - sum_k lambda_k * c_k
  r_ah = -|coord_ah^R(right; x) - tau|          tau = FROZEN_TARGETS_R0.json R_space.tau_ah_R (never retuned)
  S-3 (A2): coord undefined (R v1.1 NaN)  ->  r_ah = -(1 + |tau|); counted, flagged, never dropped
  c_art  = |m2_R(x) / m2_R(x0) - 1| - 0.10          (registered c_art)
  c_jerk = m3_R(x) / m3_R(x0) - 1.10                (registered c_jerk)
  c_ext  = extreme_R(x) - extreme_R(x0) - 0.02      (registered +2 points)
  c_act  = |log(A_R(x) / A_R(x0))| - log(1.25)      (A4, new: right-hand activity band)
  each c_k clipped to [-1, 1]; A3: undefined c_k -> +1 (flagged). c_k is undefined if either right-hand stream fails
  R v1.1 validity (or has non-finite input), or the term itself is non-finite / has a non-positive denominator.
  x0 = uncoupled CRN twin (same xi, mu removed): used only inside c_k, never as a baseline.
  Dual ascent (registered §6.2): lambda_k <- max(0, lambda_k + eta * mean_batch c_k).
"""

import math

import numpy as np

import common5 as C

MR, V = C.MR, C.V
CONSTRAINTS = ("art", "jerk", "ext", "act")
ART_TOL, JERK_MAX, EXT_TOL, ACT_LOG = 0.10, 1.10, 0.02, math.log(1.25)
CLIP, A3_UNDEFINED = 1.0, 1.0


def tau_ah_R():
    return float(C.frozen_targets()["R_space"]["tau_ah_R"]["value"])


TAU = tau_ah_R()
S3_WORST = -(1.0 + abs(TAU))
HAND_KEYS = ("A", "m1_speed", "m2_artic", "m3_jerk", "m4_angle", "extreme_frac")


def hand_summary(x, L):
    if not np.isfinite(x[:, :L]).all():
        return {k: float("nan") for k in HAND_KEYS}
    with np.errstate(invalid="ignore", divide="ignore"):
        h = MR.hand_stats(x, L)
    return {k: float(h[k]) for k in HAND_KEYS}


def r_record(xb, xl, xr, L):
    """R v1.1 statistics + validity flags + per-stream summaries (both hands) for one sample."""
    st = V.r_stats(xb, xl, xr, L)
    return {"coord_arm_rhand": float(st["coord_arm_rhand"]), "coord_arm_lhand": float(st["coord_arm_lhand"]),
            "coord_lr": float(st["coord_lr"]), "dom_X": float(st["X"]), "valid": st["valid"],
            "signal_stats": st.get("signal_stats"), "hand_R": hand_summary(xr, L), "hand_L": hand_summary(xl, L)}


def _ratio(a, b):
    return a / b if (np.isfinite(a) and np.isfinite(b) and b > 0) else float("nan")


def constraints(rec, rec0):
    """Raw constraint values (NaN = undefined) for controlled rec vs uncoupled twin rec0."""
    ok = (rec["valid"].get("input_finite", False) and rec0["valid"].get("input_finite", False)
          and rec["valid"].get("hand_R", False) and rec0["valid"].get("hand_R", False))
    h, h0 = rec["hand_R"], rec0["hand_R"]
    if not ok:
        return {k: float("nan") for k in CONSTRAINTS}
    art, jerk, act = _ratio(h["m2_artic"], h0["m2_artic"]), _ratio(h["m3_jerk"], h0["m3_jerk"]), _ratio(h["A"], h0["A"])
    raw = {"art": abs(art - 1) - ART_TOL, "jerk": jerk - JERK_MAX,
           "ext": h["extreme_frac"] - h0["extreme_frac"] - EXT_TOL,
           "act": abs(math.log(act)) - ACT_LOG if (np.isfinite(act) and act > 0) else float("nan")}
    return {k: (float(v) if np.isfinite(v) else float("nan")) for k, v in raw.items()}


def episode_reward(rec, rec0, lam):
    """Reward components for one episode. lam: dict k -> lambda_k (values used for this group)."""
    coord = rec["coord_arm_rhand"]
    s3 = not np.isfinite(coord)
    r_ah = S3_WORST if s3 else -abs(coord - TAU)
    raw = constraints(rec, rec0)
    und = {k: not np.isfinite(raw[k]) for k in CONSTRAINTS}
    c = {k: (A3_UNDEFINED if und[k] else float(np.clip(raw[k], -CLIP, CLIP))) for k in CONSTRAINTS}
    R = r_ah - sum(lam[k] * c[k] for k in CONSTRAINTS)
    return {"r_ah": float(r_ah), "s3_undefined_primary": bool(s3), "c_raw": raw, "c": c, "a3_undefined": und,
            "lambda_used": {k: float(lam[k]) for k in CONSTRAINTS}, "R": float(R)}


def rloo(R):
    """Leave-one-out baselines and advantages for one group of rewards."""
    R = np.asarray(R, float)
    G = len(R)
    b = (R.sum() - R) / (G - 1)
    return b, R - b


def dual_update(lam, c_batch, eta):
    """lambda_k <- max(0, lambda_k + eta * mean_i c_k,i) (clipped / A3 values)."""
    return {k: float(max(0.0, lam[k] + eta * float(np.mean([c[k] for c in c_batch])))) for k in CONSTRAINTS}
