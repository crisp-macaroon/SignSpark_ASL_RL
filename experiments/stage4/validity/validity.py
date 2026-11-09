"""Versioned numerical validity layer for the Stage 4 statistics (Stage 5 readiness safeguards S-1, S-2, S-6).

Registered v1 code is NOT modified: space R v1 = experiments/stage4/e2e/metrics.py; space J v1 =
experiments/stage4/jspace.py. This module computes the same statistics through the same v1 functions and adds:

  R v1.1  (S-1 + S-2)  - non-finite input -> every statistic undefined (NaN), no exception
                       - a signal (arm speed s_arm,s or hand speed s_hand,s; per frame, geodesic) is VALID only if
                         mean_tau s >= 1e-5 rad/frame AND std_tau s >= 1e-6 rad/frame (near-static floor, S-2)
                       - coord(a, b) is defined only if both signals are valid; otherwise NaN
                       - dom = log(A_L / A_R) is defined only if both hand signals are valid and A_L, A_R are finite
                         and > 0 (S-1: no ZeroDivisionError); otherwise NaN
                       - for every input on which both signals pass the floors, the value equals v1 exactly
  J v1.1  (S-6)        - same structure in space J: non-finite input or FK -> NaN; a signal is valid only if its
                         std >= 1e-7 m/frame and it is finite; dom needs A^J_L, A^J_R finite and > 0
Undefined is always NaN plus an explicit validity flag; it is never replaced by a finite value.
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "e2e"))
sys.path.insert(0, str(HERE.parent))
import metrics as MR  # noqa: E402  (space R v1, unchanged)

VERSION_R = "R v1.1"
VERSION_J = "J v1.1"
R_MEAN_FLOOR = 1e-5   # rad/frame (S-2)
R_STD_FLOOR = 1e-6    # rad/frame (S-2)
J_STD_FLOOR = 1e-7    # m/frame (S-6)


def r_signal_valid(s):
    s = np.asarray(s, float)
    return bool(len(s) >= 3 and np.isfinite(s).all() and s.mean() >= R_MEAN_FLOOR and s.std() >= R_STD_FLOOR)


def j_signal_valid(s):
    s = np.asarray(s, float)
    return bool(len(s) >= 3 and np.isfinite(s).all() and s.std() >= J_STD_FLOOR)


def _corr_if(a, b, ok):
    return MR.corr(a, b) if ok else np.nan


def _dom_if(AL, AR, ok):
    if ok and np.isfinite(AL) and np.isfinite(AR) and AL > 0 and AR > 0:
        return float(np.log(AL / AR))
    return np.nan


def r_stats(xb, xl, xr, L):
    """Space R v1.1. xb (60, T), xl/xr (90, T) 6D rotations, active length L. Returns statistics + validity flags."""
    keys = ("coord_arm_rhand", "coord_arm_lhand", "coord_lr", "X")
    if not (np.isfinite(xb[:, :L]).all() and np.isfinite(xl[:, :L]).all() and np.isfinite(xr[:, :L]).all()):
        return {**{k: np.nan for k in keys}, "valid": {"input_finite": False}, "version": VERSION_R}
    with np.errstate(invalid="ignore", divide="ignore"):
        hl, hr = MR.hand_stats(xl, L), MR.hand_stats(xr, L)
        arm_r, arm_l = MR.arm_signals(xb, L)
    v = {"input_finite": True, "arm_R": r_signal_valid(arm_r), "arm_L": r_signal_valid(arm_l),
         "hand_L": r_signal_valid(hl["s"]), "hand_R": r_signal_valid(hr["s"])}
    return {"coord_arm_rhand": _corr_if(arm_r, hr["s"], v["arm_R"] and v["hand_R"]),
            "coord_arm_lhand": _corr_if(arm_l, hl["s"], v["arm_L"] and v["hand_L"]),
            "coord_lr": _corr_if(hl["s"], hr["s"], v["hand_L"] and v["hand_R"]),
            "X": _dom_if(hl["A"], hr["A"], v["hand_L"] and v["hand_R"]),
            "signal_stats": {"arm_R": (float(np.mean(arm_r)), float(np.std(arm_r))), "arm_L": (float(np.mean(arm_l)), float(np.std(arm_l))),
                             "hand_L": (float(np.mean(hl["s"])), float(np.std(hl["s"]))),
                             "hand_R": (float(np.mean(hr["s"])), float(np.std(hr["s"])))},
            "valid": v, "version": VERSION_R}


def j_signals(ctx, b6, lh6, rh6):
    """Space-J arm and hand signals with the jspace v1 definitions (wrist linear speed; wrist-local finger speed)."""
    import jspace as JS
    J = JS.fk(ctx[0], b6, lh6, rh6)
    if not np.isfinite(J).all():
        return None
    Rb = JS.mats(b6)
    out = {}
    for s, H, W in (("L", JS.L_HAND, JS.L_WRIST), ("R", JS.R_HAND, JS.R_WRIST)):
        c = JS.CHAIN[s]
        G = Rb[:, c[0]] @ Rb[:, c[1]] @ Rb[:, c[2]] @ Rb[:, c[3]]
        loc = np.einsum("tji,tnj->tni", G, J[:, H] - J[:, [W]])
        out[f"hand_{s}"] = np.linalg.norm(np.diff(loc, axis=0), axis=-1).mean(1)
        out[f"arm_{s}"] = np.linalg.norm(np.diff(J[:, W], axis=0), axis=-1)
    return out


def j_from_signals(sig):
    """Space J v1.1 statistics from signals (pure function; unit-testable without FK)."""
    keys = ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")
    if sig is None:
        return {**{k: np.nan for k in keys}, "valid": {"fk_finite": False}, "version": VERSION_J}
    v = {"fk_finite": True, **{k: j_signal_valid(sig[k]) for k in ("arm_L", "arm_R", "hand_L", "hand_R")}}
    AL, AR = float(np.sum(sig["hand_L"])), float(np.sum(sig["hand_R"]))
    return {"coord_ah_J_L": _corr_if(sig["arm_L"], sig["hand_L"], v["arm_L"] and v["hand_L"]),
            "coord_ah_J_R": _corr_if(sig["arm_R"], sig["hand_R"], v["arm_R"] and v["hand_R"]),
            "coord_lr_J": _corr_if(sig["hand_L"], sig["hand_R"], v["hand_L"] and v["hand_R"]),
            "dom_J": _dom_if(AL, AR, v["hand_L"] and v["hand_R"]), "valid": v, "version": VERSION_J}


def j_stats(ctx, b6, lh6, rh6):
    """Space J v1.1 on 6D inputs (L, C). Non-finite input -> undefined without FK."""
    if not (np.isfinite(b6).all() and np.isfinite(lh6).all() and np.isfinite(rh6).all()):
        return j_from_signals(None)
    return j_from_signals(j_signals(ctx, b6, lh6, rh6))
