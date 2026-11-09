"""Campaign Phase 0 synthetic self-test: pure functions of the new E2e-J, E2a, E2b, E2c and R0 code on toy arrays.
No model, no SMPL-X, no dataset, no generation.

    python -E -s experiments/stage4/phase0_selftest.py
"""

import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
for d in ("", "e2e", "e2d", "e2c", "e2b", "e2e_j", "r0", "e2a"):
    sys.path.insert(0, str(HERE / d))

torch.manual_seed(0)
rng = np.random.default_rng(0)
R = {}


def check(name, ok, info=""):
    R[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  {info}" if info else ""), flush=True)


# ---------------------------------------------------------------- E2b
import e2b_run as B  # noqa: E402

eps = torch.randn(240, 304)
L = 100
s = B.shifted(eps, L, 8, 3)
check("E2b shift: eps'(t) = eps(t - 8) inside the active frames", torch.equal(s[:, 8:L], eps[:, 0:L - 8]))
check("E2b shift: vacated frames are fresh noise, not the old values", not torch.equal(s[:, :8], eps[:, :8]))
check("E2b shift: padded frames unchanged", torch.equal(s[:, L:], eps[:, L:]))
s2 = B.shifted(eps, L, -4, 3)
check("E2b negative shift: eps'(t) = eps(t + 4)", torch.equal(s2[:, :L - 4], eps[:, 4:L]))
check("E2b fresh noise deterministic", torch.equal(B.shifted(eps, L, 8, 3), s))
sig = rng.normal(size=200)
p_base = {"x": sig}
p_new = {"x": np.r_[rng.normal(size=8), sig[:-8]]}
check("E2b equivariance index = 1 for an exact shift", abs(B.eq_index(p_new, p_base, 8)["x"] - 1) < 1e-12)

# ---------------------------------------------------------------- E2e-J
import e2ej_run as EJ  # noqa: E402

check("E2e-J agreement categories", EJ.agree({"ci95": [0.1, 0.2]}, {"ci95": [0.05, 0.3]}) == "both"
      and EJ.agree({"ci95": [0.1, 0.2]}, {"ci95": [-0.1, 0.3]}) == "R only"
      and EJ.agree({"ci95": [-0.2, 0.2]}, {"ci95": [-0.3, -0.1]}) == "J only"
      and EJ.agree({"ci95": [-0.2, 0.2]}, {"ci95": [-0.1, 0.1]}) == "neither"
      and EJ.agree({"ci95": [0.1, 0.2]}, {"ci95": [-0.3, -0.1]}) == "opposite")
import stats as S  # noqa: E402

idx = S.boot_idx(32, 0)[:300]
a0 = rng.normal(0, 0.05, (32, 8))
cond = a0 - 0.35
dd = EJ.da_db(cond, a0, np.full(32, -0.4), idx, 0.05)
check("E2e-J D-a/D-b in J: a -0.35 shift toward -0.4 passes D-a and is closer", dd["D_a_J"]["pass"] and dd["D_b_J"]["closer"])

# ---------------------------------------------------------------- E2c
import e2c_run as C  # noqa: E402
import typicality as T  # noqa: E402

M = torch.randn(90, 60)
U = C.stiefel(M)
check("E2c Stiefel U^T U = I", torch.allclose(U.T @ U, torch.eye(60), atol=1e-5))
params = [torch.randn(90, 60), torch.randn(60, 60), torch.full((60,), 10.0)]  # sigmoid -> 1 => kappa clamped at 0.9
eb, er = torch.randn(60, 20000), torch.randn(90, 20000)
z, kl = C.coupled(params, eb, er)
cov = (z @ z.T / z.shape[1]).numpy()
check("E2c (ii) coupled noise has unit covariance (marginal preserved)", np.abs(cov - np.eye(90)).max() < 0.06,
      f"max |cov - I| {np.abs(cov - np.eye(90)).max():.3f}")
check("E2c (ii) kappa clamped at 0.9, KL = 60*(-0.5 log 0.19) <= 99.64", abs(kl - 60 * (-0.5 * np.log(0.19))) < 1e-3 and kl <= 99.64,
      f"{kl:.3f} nats/frame")
p0 = C.family_params(0)
k0 = torch.clamp(0.95 * torch.sigmoid(p0[2]), max=0.9)
check("E2c (ii) init kappa = 0.1", torch.allclose(k0, torch.full_like(k0, 0.1), atol=1e-6))
b = T.bounds(146)
x = torch.randn(90, 146)
while not T.feasible(x.numpy(), b, float((x.double() ** 2).sum()))[0]:
    x = torch.randn(90, 146)
check("E2c E-2 penalty is 0 inside the A/P bounds", float(C.ap_penalty(x, b)) == 0.0)
xs = x.clone()
for t in range(1, 146):
    xs[:, t] = 0.6 * xs[:, t - 1] + 0.8 * x[:, t]
check("E2c E-2 penalty > 0 for AR(1) 0.6 noise", float(C.ap_penalty(xs, b)) > 0)
mon = C.monitor(x.numpy(), rng.normal(size=(60, 146)), 146)
check("E2c monitoring flags computed (non-gating)", set(mon) == {"lag2_pooled", "lag3_pooled", "lag4_pooled", "hand_body_corr",
                                                                  "norm_chi2_outside_99.9"})
xb = torch.randn(2, 60, 120)
xh = torch.randn(2, 90, 120)
sur = C.surrogate(xb, xh, [120, 100])
check("E2c surrogate finite and within [-1, 1]", torch.isfinite(sur).all() and (sur.abs() <= 1 + 1e-6).all())

# ---------------------------------------------------------------- R0
import r0_run as R0  # noqa: E402
import gpu_common  # noqa: E402,F401  (import check only)
sys.path.insert(0, str(HERE.parents[1] / "third_party" / "SignSparK" / "tools"))
import visualize as up  # noqa: E402

_ax = np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8])  # R0 passes unit axes (run-1 test bug: unnormalised)
six = R0.rot6d_from_axis_angle(_ax, 0.7)
from scipy.spatial.transform import Rotation  # noqa: E402

Rm = up.rot6d_to_matrix(torch.tensor(six)[None]).numpy()[0]
check("R0 rot6d round trip matches the upstream rot6d_to_matrix",
      np.abs(Rm - Rotation.from_rotvec(np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8]) * 0.7).as_matrix()).max() < 1e-6)
bc = R0.boot_ci(np.r_[np.ones(100), np.nan], lambda n: np.random.default_rng(0).integers(0, n, (200, n)))
check("R0 boot_ci excludes NaN and reports n", bc["n"] == 100 and bc["mean"] == 1.0)
check("R0 uses train references only", "train" in str(R0.LMDB) and "dev" not in str(R0.LMDB) and "test" not in str(R0.LMDB))

print(f"\n{sum(R.values())}/{len(R)} checks passed")
sys.exit(0 if all(R.values()) else 1)
