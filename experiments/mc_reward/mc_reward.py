"""M-C reward (Stage 4 rev. 4.0 §6.0-6.2, App. G.4) as registered: reward code only, no controller, no training.

All statistics are space R v1.1 (experiments/stage4/validity/validity.py on the registered v1 metric); targets are
read from the frozen research/stage4/FROZEN_TARGETS_R0.json R_space block and never retuned. J space never enters.

Components (§6.1), each reported separately (§6.2: "optimised and reported separately first"):
  r_coord = r_ah(R) + r_ah(L) + r_lr                                    M-C/kappa (P1a)
            r_ah(s) = -|coord_ah^R(s) - tau_ah(s)|,  r_lr = -|coord_lr^R - tau_lr|
  r_dom   = -|dom^R - t*|,  dom^R = log(A_L / A_R)                     M-C/sigma (P1b)
Constraints c_k (c_k <= 0 satisfied; clipped to [-1, 1]; x0 = paired base sample, same base noise, identity transform):
  both components   art_s  = |m2_s(x) / m2_s(x0) - 1| - 0.10           s in {L, R}
                    jerk_s = m3_s(x) / m3_s(x0) - (1 + delta), delta = 0.10
  c_left (sigma)    calib_L = log 0.8 - median_batch log(A_L(x) / A_L^ref)   (batch level, train references)
                    jerk_L  (= c_left (ii); shared with jerk_s above)
                    ext_L   = extreme_L(x) - extreme_L(x0) - 0.02
                    lr_floor = (coord_lr(x0) - 0.03) - coord_lr(x)
KL (App. G.4, exact, logged separately): KL_kappa, KL_sigma per active frame from noise_transform.kl_per_frame.

  R = r_task - alpha_kappa * L * KL_kappa - alpha_sigma * L * KL_sigma - sum_k lambda_k c_k
  r_task = z(r_coord) (mode "coord") | z(r_dom) (mode "dom") | z(r_coord) + z(r_dom) (mode "combined")
  z(r) = (r - mean_base) / std_base when train base-model statistics are supplied (§6.2), else r (flagged).

Undefined values (never dropped, always flagged):
  coordination term undefined -> its worst case -(1 + |tau|) (S-3 as authorised for Stage 5);
  constraint undefined        -> +1 (A3);
  r_dom undefined             -> cfg.dom_undefined_reward. r_dom is unbounded below, so S-3 has no worst case for it;
                                 the value is NOT registered and must be set explicitly (no default) [U].
Unregistered settings (alpha_kappa, alpha_sigma, z-normalisation statistics, dom_undefined_reward, eta) are listed by
MCRewardConfig.unresolved() so every run records which values were conventions rather than registered.
"""

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in ("experiments/stage4/e2e", "experiments/stage4/validity"):
    sys.path.insert(0, str(ROOT / p))
import metrics as MR  # noqa: E402  (space R v1, registered, unchanged)
import noise_transform as NT  # noqa: E402  (exact M-C KL, App. G.4)
import validity as V  # noqa: E402  (R v1.1)

FROZEN = ROOT / "research" / "stage4" / "FROZEN_TARGETS_R0.json"
MODES = ("coord", "dom", "combined")
SIDES = ("L", "R")
ART_TOL, JERK_DELTA, EXT_TOL, LR_DROP, CALIB_FLOOR = 0.10, 0.10, 0.02, 0.03, math.log(0.8)
CLIP, A3_UNDEFINED = 1.0, 1.0
CONSTRAINTS = {
    "coord": ("art_L", "art_R", "jerk_L", "jerk_R"),
    "dom": ("art_L", "art_R", "jerk_L", "jerk_R", "ext_L", "lr_floor", "calib_L"),
}
CONSTRAINTS["combined"] = CONSTRAINTS["dom"]
HAND_KEYS = ("A", "m2_artic", "m3_jerk", "extreme_frac")


def load_targets(path=FROZEN):
    """Frozen R-space targets (values only) and the file SHA-256, so a run can record what it read."""
    raw = Path(path).read_bytes()
    r = json.loads(raw.decode("utf-8"))["R_space"]
    return {k: float(r[k]["value"]) for k in ("tau_ah_L", "tau_ah_R", "tau_lr", "t_dom")}, hashlib.sha256(raw).hexdigest()


TARGETS, TARGETS_SHA256 = load_targets()


@dataclass
class MCRewardConfig:
    mode: str = "coord"
    allow_combined: bool = False             # §6.2: combined objective only after both components were evaluated alone
    alpha_kappa: float = 0.0                 # [U] KL weights: separate per §6.1, values not registered
    alpha_sigma: float = 0.0
    znorm: dict = field(default_factory=dict)  # {"r_coord": (mean, std), "r_dom": (mean, std)} from train base [U]
    dom_undefined_reward: float = None       # [U] required only if r_dom is undefined in a reward-bearing mode
    eta: float = 1.0                         # dual-ascent step (Stage 5 value; not registered for M-C) [U]

    def __post_init__(self):
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if self.mode == "combined" and not self.allow_combined:
            raise ValueError("combined objective needs allow_combined=True (§6.2: components alone first)")
        for k, (m, s) in self.znorm.items():
            if k not in ("r_coord", "r_dom") or not (np.isfinite(m) and np.isfinite(s) and s > 0):
                raise ValueError(f"bad z-normalisation entry {k}: {(m, s)}")

    def constraints(self):
        return CONSTRAINTS[self.mode]

    def unresolved(self):
        """Settings in use that are conventions, not registered values (record with every run)."""
        out = {"alpha_kappa": self.alpha_kappa, "alpha_sigma": self.alpha_sigma, "eta": self.eta}
        uses = {"coord": ("r_coord",), "dom": ("r_dom",), "combined": ("r_coord", "r_dom")}[self.mode]
        out["znorm_missing"] = [k for k in uses if k not in self.znorm]
        if self.mode != "coord":
            out["dom_undefined_reward"] = self.dom_undefined_reward
        return out


def _hand(x, L):
    if not np.isfinite(x[:, :L]).all():
        return {k: float("nan") for k in HAND_KEYS}
    with np.errstate(invalid="ignore", divide="ignore"):
        h = MR.hand_stats(x, L)
    return {k: float(h[k]) for k in HAND_KEYS}


def record(xb, xl, xr, L):
    """R v1.1 statistics + validity flags + per-hand summaries for one sample (body (60, T), hands (90, T))."""
    st = V.r_stats(xb, xl, xr, L)
    return {"coord_ah_L": float(st["coord_arm_lhand"]), "coord_ah_R": float(st["coord_arm_rhand"]),
            "coord_lr": float(st["coord_lr"]), "dom": float(st["X"]), "valid": st["valid"],
            "hand_L": _hand(xl, L), "hand_R": _hand(xr, L), "L": int(L)}


def coord_terms(rec):
    """r_ah(L), r_ah(R), r_lr with S-3 worst case for undefined values; flags per term."""
    terms, undef = {}, {}
    for name, stat, tau in (("r_ah_L", "coord_ah_L", TARGETS["tau_ah_L"]), ("r_ah_R", "coord_ah_R", TARGETS["tau_ah_R"]),
                            ("r_lr", "coord_lr", TARGETS["tau_lr"])):
        v = rec[stat]
        undef[name] = not np.isfinite(v)
        terms[name] = -(1.0 + abs(tau)) if undef[name] else -abs(v - tau)
    return terms, undef


def dom_term(rec):
    """r_dom = -|dom - t*| (NaN if dom undefined; the caller applies cfg.dom_undefined_reward)."""
    d = rec["dom"]
    return (-abs(d - TARGETS["t_dom"]), False) if np.isfinite(d) else (float("nan"), True)


def _ratio(a, b):
    return a / b if (np.isfinite(a) and np.isfinite(b) and b > 0) else float("nan")


def _side_ok(rec, rec0, s):
    return (rec["valid"].get("input_finite", False) and rec0["valid"].get("input_finite", False)
            and rec["valid"].get(f"hand_{s}", False) and rec0["valid"].get(f"hand_{s}", False))


def episode_constraints(rec, rec0):
    """Per-episode raw constraint values (NaN = undefined) vs the paired base sample. calib_L is batch-level."""
    raw = {}
    for s in SIDES:
        h, h0 = rec[f"hand_{s}"], rec0[f"hand_{s}"]
        ok = _side_ok(rec, rec0, s)
        art, jerk = _ratio(h["m2_artic"], h0["m2_artic"]), _ratio(h["m3_jerk"], h0["m3_jerk"])
        raw[f"art_{s}"] = abs(art - 1) - ART_TOL if ok else float("nan")
        raw[f"jerk_{s}"] = jerk - (1 + JERK_DELTA) if ok else float("nan")
        if s == "L":
            raw["ext_L"] = h["extreme_frac"] - h0["extreme_frac"] - EXT_TOL if ok else float("nan")
    lr, lr0 = rec["coord_lr"], rec0["coord_lr"]
    raw["lr_floor"] = (lr0 - LR_DROP) - lr if (np.isfinite(lr) and np.isfinite(lr0)) else float("nan")
    return {k: (float(v) if np.isfinite(v) else float("nan")) for k, v in raw.items()}


def calib_left(recs, A_L_ref):
    """c_left (i), batch level: log 0.8 - median_i log(A_L(x_i) / A_L^ref_i) over defined pairs; NaN if none.
    A_L_ref: train-reference left-hand activity of each episode's clip (R v1 hand_stats A)."""
    logs = [math.log(r["hand_L"]["A"] / a) for r, a in zip(recs, A_L_ref)
            if r["valid"].get("hand_L", False) and np.isfinite(r["hand_L"]["A"]) and r["hand_L"]["A"] > 0
            and np.isfinite(a) and a > 0]
    return (CALIB_FLOOR - float(np.median(logs)), len(logs)) if logs else (float("nan"), 0)


def kl_terms(m, L):
    """Exact per-episode KL of the M-C transform m (noise_transform.build output): (KL_kappa, KL_sigma) x L frames."""
    kc, ks = NT.kl_per_frame(m)
    return kc * L, ks * L


def _z(cfg, name, r):
    if name in cfg.znorm:
        m, s = cfg.znorm[name]
        return (r - m) / s
    return r


def batch_reward(cfg, recs, recs0, lam, kl=None, A_L_ref=None):
    """Rewards for one batch of episodes.

    recs / recs0: record() of controlled / paired base samples (same base noise). lam: {constraint: lambda_k}.
    kl: per-episode (KL_kappa, KL_sigma) from kl_terms (None -> 0, flagged). A_L_ref: needed for calib_L (dom modes).
    Returns one dict per episode with every component, constraint, flag and the total R."""
    keys = cfg.constraints()
    if set(lam) != set(keys):
        raise ValueError(f"lambda keys {sorted(lam)} != constraints {sorted(keys)}")
    calib, n_calib = (float("nan"), 0)
    if "calib_L" in keys:
        if A_L_ref is None or len(A_L_ref) != len(recs):
            raise ValueError("calib_L needs one train-reference A_L per episode")
        calib, n_calib = calib_left(recs, A_L_ref)
    out = []
    for i, (rec, rec0) in enumerate(zip(recs, recs0)):
        ct, cu = coord_terms(rec)
        r_coord = sum(ct.values())
        r_dom, dom_undef = dom_term(rec)
        if dom_undef and cfg.mode != "coord":
            if cfg.dom_undefined_reward is None:
                raise ValueError("r_dom undefined and cfg.dom_undefined_reward is not set (no registered value)")
            r_dom = float(cfg.dom_undefined_reward)
        r_task = {"coord": _z(cfg, "r_coord", r_coord), "dom": _z(cfg, "r_dom", r_dom),
                  "combined": _z(cfg, "r_coord", r_coord) + _z(cfg, "r_dom", r_dom)}[cfg.mode]
        raw = episode_constraints(rec, rec0)
        raw["calib_L"] = calib
        raw = {k: raw[k] for k in keys}
        und = {k: not np.isfinite(v) for k, v in raw.items()}
        c = {k: (A3_UNDEFINED if und[k] else float(np.clip(raw[k], -CLIP, CLIP))) for k in keys}
        klk, kls = (float("nan"), float("nan")) if kl is None else map(float, kl[i])
        kl_pen = 0.0 if kl is None else cfg.alpha_kappa * klk + cfg.alpha_sigma * kls
        R = r_task - kl_pen - sum(lam[k] * c[k] for k in keys)
        out.append({"mode": cfg.mode, "r_ah_L": ct["r_ah_L"], "r_ah_R": ct["r_ah_R"], "r_lr": ct["r_lr"],
                    "r_coord": r_coord, "r_dom": r_dom, "r_task": float(r_task),
                    "s3_undefined": cu, "dom_undefined": dom_undef,
                    "kl_kappa": klk, "kl_sigma": kls, "kl_missing": kl is None, "kl_penalty": float(kl_pen),
                    "c_raw": raw, "c": c, "a3_undefined": und, "calib_L_n": n_calib,
                    "lambda_used": {k: float(lam[k]) for k in keys}, "R": float(R)})
    return out


def dual_update(lam, terms, eta):
    """lambda_k <- max(0, lambda_k + eta * mean_i c_k,i) (§6.2 dual ascent; clipped / A3 values)."""
    return {k: float(max(0.0, lam[k] + eta * float(np.mean([t["c"][k] for t in terms])))) for k in lam}


def rloo(R):
    """Leave-one-out group baselines and advantages (§6.2 item 3: the REINFORCE baseline)."""
    R = np.asarray(R, float)
    b = (R.sum() - R) / (len(R) - 1)
    return b, R - b


def paired_delta(terms, terms0):
    """CRN monitoring quantity Delta = r(controlled) - r(base) per component (§6.2 item 2). Not a baseline."""
    names = ("r_ah_L", "r_ah_R", "r_lr", "r_coord", "r_dom")
    return [{k: t[k] - t0[k] for k in names} for t, t0 in zip(terms, terms0)]
