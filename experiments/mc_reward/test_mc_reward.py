"""Unit tests for mc_reward.py on synthetic 6D rotation sequences (no models, no data, no generation, no training).

    python -E -s experiments/mc_reward/test_mc_reward.py
"""

import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mc_reward as M  # noqa: E402

FAIL = []


def check(name, ok, info=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({info})" if info else ""))
    if not ok:
        FAIL.append(name)


def rot(axis_angle):
    """(..., 3) axis-angle -> (..., 3, 3) by Rodrigues."""
    th = np.linalg.norm(axis_angle, axis=-1, keepdims=True)
    k = axis_angle / np.maximum(th, 1e-12)
    K = np.zeros(axis_angle.shape[:-1] + (3, 3))
    K[..., 0, 1], K[..., 0, 2], K[..., 1, 0] = -k[..., 2], k[..., 1], k[..., 2]
    K[..., 1, 2], K[..., 2, 0], K[..., 2, 1] = -k[..., 0], -k[..., 1], k[..., 0]
    th = th[..., None]
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def seq(n_joints, T, speed, rng, axis=None):
    """6D sequence (6 n_joints, T): joint rotations integrating per-frame increments of magnitude speed[t]."""
    R = np.tile(np.eye(3), (n_joints, 1, 1))
    out = np.zeros((T, n_joints, 6))
    for t in range(T):
        out[t, :, :3], out[t, :, 3:] = R[:, 0, :], R[:, 1, :]
        a = rng.normal(size=(n_joints, 3)) if axis is None else np.tile(axis, (n_joints, 1))
        a = a / np.linalg.norm(a, axis=1, keepdims=True) * speed[t]
        R = rot(a) @ R
    return out.reshape(T, -1).T.astype(np.float32)


rng = np.random.default_rng(0)
T, L = 120, 100
t = np.arange(T)
env = 0.05 + 0.04 * np.sin(2 * np.pi * t / 25) ** 2          # shared speed envelope (rad/frame)
indep = 0.05 + 0.04 * np.sin(2 * np.pi * t / 17 + 1.0) ** 2


def body(arm_speed):
    return np.concatenate([seq(1, T, arm_speed, np.random.default_rng(j)) for j in range(10)], axis=0)


xb = body(env)
xl = seq(15, T, 0.8 * indep, np.random.default_rng(11))
xr = seq(15, T, env, np.random.default_rng(12))

# 1. frozen targets, unchanged file
raw = M.FROZEN.read_bytes()
check("targets read from FROZEN_TARGETS_R0.json R_space", M.TARGETS == {"tau_ah_L": 0.6103, "tau_ah_R": 0.4514,
                                                                         "tau_lr": 0.3225, "t_dom": -0.3924}, str(M.TARGETS))
check("frozen target file hash recorded and unchanged", hashlib.sha256(raw).hexdigest() == M.TARGETS_SHA256)

# 2. record = validity layer (R v1.1) values
rec = M.record(xb, xl, xr, L)
st = M.V.r_stats(xb, xl, xr, L)
check("record matches R v1.1 r_stats", rec["coord_ah_R"] == st["coord_arm_rhand"] and rec["coord_ah_L"] == st["coord_arm_lhand"]
      and rec["coord_lr"] == st["coord_lr"] and rec["dom"] == st["X"] and all(rec["valid"].values()),
      f"coord_ah_R {rec['coord_ah_R']:.3f}, coord_ah_L {rec['coord_ah_L']:.3f}, dom {rec['dom']:.3f}")

# 3. coordination terms: target matching (zero at target, symmetric)
for d in (-0.2, 0.0, 0.3):
    r = dict(rec, coord_ah_R=M.TARGETS["tau_ah_R"] + d)
    ct, _ = M.coord_terms(r)
    check(f"r_ah_R = -|{d:+.1f}| at tau + {d:+.1f}", math.isclose(ct["r_ah_R"], -abs(d), abs_tol=1e-12))
ct, cu = M.coord_terms(rec)
check("r_coord components exact", math.isclose(ct["r_ah_L"], -abs(rec["coord_ah_L"] - 0.6103))
      and math.isclose(ct["r_lr"], -abs(rec["coord_lr"] - 0.3225)) and not any(cu.values()))

# 4. dominance term
rd, du = M.dom_term(rec)
check("r_dom = -|dom - t*|", math.isclose(rd, -abs(rec["dom"] + 0.3924)) and not du, f"{rd:.4f}")
rd, _ = M.dom_term(dict(rec, dom=-0.3924))
check("r_dom = 0 at t*", rd == 0.0)

# 5. identical controlled and base samples: every per-episode constraint at -tolerance (satisfied)
cfg_dom = M.MCRewardConfig(mode="dom", dom_undefined_reward=-2.0)
lam_dom = {k: 0.0 for k in cfg_dom.constraints()}
out = M.batch_reward(cfg_dom, [rec], [rec], lam_dom, A_L_ref=[rec["hand_L"]["A"]])[0]
exp = {"art_L": -0.10, "art_R": -0.10, "jerk_L": -0.10, "jerk_R": -0.10, "ext_L": -0.02, "lr_floor": -0.03,
       "calib_L": math.log(0.8)}
check("x == x0 -> every constraint = -tolerance", all(math.isclose(out["c_raw"][k], v, abs_tol=1e-12) for k, v in exp.items()),
      str({k: round(v, 4) for k, v in out["c_raw"].items()}))
check("dom mode: R = r_dom when lambda = 0, no KL", math.isclose(out["R"], out["r_dom"]))

# 6. constraint set per mode (§6.1: c_left only for M-C/sigma)
check("coord mode constraints = art, jerk (both hands)", M.MCRewardConfig().constraints() == ("art_L", "art_R", "jerk_L", "jerk_R"))
check("dom mode adds c_left (calib_L, ext_L, lr_floor)", set(cfg_dom.constraints()) - set(M.MCRewardConfig().constraints())
      == {"calib_L", "ext_L", "lr_floor"})
try:
    M.MCRewardConfig(mode="combined")
    check("combined refused without allow_combined", False)
except ValueError:
    check("combined refused without allow_combined", True)
cfg_c = M.MCRewardConfig(mode="combined", allow_combined=True, dom_undefined_reward=-2.0)
o = M.batch_reward(cfg_c, [rec], [rec], {k: 0.0 for k in cfg_c.constraints()}, A_L_ref=[rec["hand_L"]["A"]])[0]
check("combined: r_task = r_coord + r_dom (no z-norm)", math.isclose(o["r_task"], o["r_coord"] + o["r_dom"]))

# 7. violations: left hand jerkier and suppressed vs base
xl_bad = seq(15, T, 0.4 * indep + 0.03 * (t % 2), np.random.default_rng(11))
rec_bad = M.record(xb, xl_bad, xr, L)
o = M.batch_reward(cfg_dom, [rec_bad], [rec], lam_dom, A_L_ref=[rec["hand_L"]["A"]])[0]
check("suppressed left: calib_L violated (> 0)", o["c_raw"]["calib_L"] > 0, f"{o['c_raw']['calib_L']:.3f}")
check("jittery left: jerk_L violated (> 0)", o["c_raw"]["jerk_L"] > 0, f"{o['c_raw']['jerk_L']:.3f}")
check("constraints clipped to [-1, 1]", all(-1 <= v <= 1 for v in o["c"].values()))
lam1 = {k: 1.0 for k in cfg_dom.constraints()}
o1 = M.batch_reward(cfg_dom, [rec_bad], [rec], lam1, A_L_ref=[rec["hand_L"]["A"]])[0]
check("R = r_task - sum lambda c", math.isclose(o1["R"], o1["r_task"] - sum(o1["c"].values())))
lam_new = M.dual_update(lam_dom, [o], eta=1.0)
check("dual ascent: violated -> lambda up, satisfied -> stays 0",
      all((lam_new[k] > 0) == (o["c"][k] > 0) for k in lam_new), str({k: round(v, 3) for k, v in lam_new.items()}))

# 8. undefined values: static left hand -> coord_ah_L, coord_lr, dom undefined
xl_static = np.tile(xl[:, :1], (1, T))
rec_s = M.record(xb, xl_static, xr, L)
ct, cu = M.coord_terms(rec_s)
check("static left: S-3 worst case on r_ah_L and r_lr, r_ah_R defined",
      cu["r_ah_L"] and cu["r_lr"] and not cu["r_ah_R"] and ct["r_ah_L"] == -1.6103 and ct["r_lr"] == -1.3225)
try:
    M.batch_reward(M.MCRewardConfig(mode="dom"), [rec_s], [rec], lam_dom, A_L_ref=[1.0])
    check("undefined r_dom without a configured value raises", False)
except ValueError:
    check("undefined r_dom without a configured value raises", True)
o = M.batch_reward(cfg_dom, [rec_s], [rec], lam_dom, A_L_ref=[rec["hand_L"]["A"]])[0]
check("undefined r_dom -> configured value, flagged", o["r_dom"] == -2.0 and o["dom_undefined"])
check("left constraints undefined -> A3 +1, flagged; calib_L with no defined pair -> +1",
      all(o["c"][k] == 1.0 and o["a3_undefined"][k] for k in ("art_L", "jerk_L", "ext_L", "lr_floor", "calib_L")))
check("coord mode ignores undefined r_dom (no config needed)",
      math.isfinite(M.batch_reward(M.MCRewardConfig(), [rec_s], [rec], {k: 0.0 for k in M.CONSTRAINTS["coord"]})[0]["R"]))
xr_nan = xr.copy()
xr_nan[0, 5] = np.nan
o = M.batch_reward(cfg_dom, [M.record(xb, xl, xr_nan, L)], [rec], lam_dom, A_L_ref=[rec["hand_L"]["A"]])[0]
check("non-finite input: all coordination at worst case, episode kept, R finite",
      all(o["s3_undefined"].values()) and math.isfinite(o["R"]))

# 9. z-normalisation and KL
cfg_z = M.MCRewardConfig(znorm={"r_coord": (-1.0, 0.5)})
o = M.batch_reward(cfg_z, [rec], [rec], {k: 0.0 for k in cfg_z.constraints()})[0]
check("z-normalised r_coord", math.isclose(o["r_task"], (o["r_coord"] + 1.0) / 0.5))
check("unresolved() lists missing z-norm and unregistered values",
      M.MCRewardConfig(mode="dom").unresolved()["znorm_missing"] == ["r_dom"]
      and "dom_undefined_reward" in M.MCRewardConfig(mode="dom").unresolved())
m = M.NT.build({"kind": "BH", "r": 8, "kappa": 0.5, "seed": 3, "sigma": (0.9, 1.1)})
klk, kls = M.kl_terms(m, L)
check("KL terms = noise_transform.kl_per_frame x L (exact)",
      math.isclose(klk, L * -0.5 * 2 * 8 * math.log(1 - 0.25))
      and math.isclose(kls, L * 0.5 * 90 * sum(v ** 2 - 1 - math.log(v ** 2) for v in (0.9, 1.1))), f"{klk:.3f}, {kls:.3f}")
cfg_kl = M.MCRewardConfig(alpha_kappa=0.01, alpha_sigma=0.02)
o = M.batch_reward(cfg_kl, [rec], [rec], {k: 0.0 for k in cfg_kl.constraints()}, kl=[(klk, kls)])[0]
check("separate KL weights applied", math.isclose(o["R"], o["r_task"] - 0.01 * klk - 0.02 * kls))
check("identity transform: KL = 0", M.kl_terms(M.NT.build({"kind": "base"}), L) == (0.0, 0.0))

# 10. RLOO and paired delta
b, a = M.rloo([1.0, 2.0, 3.0, 6.0])
check("RLOO advantages sum to 0, baseline excludes self", math.isclose(a.sum(), 0, abs_tol=1e-12) and b[0] == 11 / 3)
cfg = M.MCRewardConfig()
lam0 = {k: 0.0 for k in cfg.constraints()}
d = M.paired_delta(M.batch_reward(cfg, [rec_bad], [rec], lam0), M.batch_reward(cfg, [rec], [rec], lam0))[0]
check("paired delta = controlled - base per component", math.isclose(d["r_ah_L"], M.coord_terms(rec_bad)[0]["r_ah_L"]
                                                                      - M.coord_terms(rec)[0]["r_ah_L"]))

print(f"\n{len(FAIL)} failed" if FAIL else "\nall passed")
sys.exit(1 if FAIL else 0)
