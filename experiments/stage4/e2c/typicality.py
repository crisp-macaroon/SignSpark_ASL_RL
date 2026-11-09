"""E2c (i) N4 typicality constraints (proposed pre-registration C-c3 amendment 2; NOT registered until approved).

Amendment-2 code changes (2026-11-03): B1 (non-finite arrays rejected; projection output verified), B2 (feasibility
evaluated on the exact float32 model-input array; internal M/V inward margin 1e-5). Registered bounds unchanged.
Pre-fix version: research/archive/typicality_pre_B1B2.py.

Per sample and per hand: noise x in R^{C x L}, C = 90 channels, L active frames. Under the base law every entry
is i.i.d. N(0, 1). Each constraint holds for base noise with a stated null probability, so the constrained set is
a typical set of the base law, not an arbitrary restriction.

  N  overall norm      ||x||^2 kept equal to its initial value (exact projection; chi^2_{CL} typicality preserved)
  M  channel mean      |mean_t x_c| <= z_c / sqrt(L)                                  (exact: N(0, 1/L))
  V  channel 2nd mom.  mean_t x_c^2 in [chi2_L(a_c/2)/L, chi2_L(1-a_c/2)/L]             (exact: chi^2_L / L)
  A  channel lag-1     |r_c| <= z_c / sqrt(L),  r_c = sum_t x_c,t x_c,t+1 / sum_t x_c,t^2   (asymptotic; simulated)
  P  pooled lag-1      |mean_c r_c| <= z_p / sqrt(C (L - 1))                            (asymptotic; simulated)
with a_c = 0.005 / C per channel (family 0.5% per hand for each of M, V, A), z_c = Phi^-1(1 - a_c/2),
z_p = Phi^-1(1 - 0.0005) (0.1% per hand). Nominal per-hand null violation <= 1.6%.
Monitored, not constrained: pooled lag-2..4 autocorrelation, max |cross-correlation| with the body noise.
"""

import numpy as np
from scipy.stats import chi2, norm

C = 90
FAM = {"M": 0.005, "V": 0.005, "A": 0.005, "P": 0.001}


def bounds(L, C=C):
    a_c = FAM["M"] / C
    z_c = norm.ppf(1 - a_c / 2)
    z_p = norm.ppf(1 - FAM["P"] / 2)
    return {"mean": z_c / np.sqrt(L),
            "var_lo": chi2.ppf(FAM["V"] / C / 2, L) / L, "var_hi": chi2.ppf(1 - FAM["V"] / C / 2, L) / L,
            "lag1": norm.ppf(1 - FAM["A"] / C / 2) / np.sqrt(L),
            "lag1_pooled": z_p / np.sqrt(C * (L - 1))}


def stats(x):
    """x: [..., C, L] -> per-sample statistics (numpy)."""
    L = x.shape[-1]
    m = x.mean(-1)
    q = (x ** 2).mean(-1)
    r = (x[..., 1:] * x[..., :-1]).sum(-1) / (x ** 2).sum(-1)
    out = {"mean": np.abs(m).max(-1), "var_min": q.min(-1), "var_max": q.max(-1), "lag1": np.abs(r).max(-1),
           "lag1_pooled": np.abs(r.mean(-1))}
    for lag in (2, 3, 4):
        out[f"lag{lag}_pooled"] = np.abs(((x[..., lag:] * x[..., :-lag]).sum(-1) / (x ** 2).sum(-1)).mean(-1))
    return out


def violations(s, b):
    return {"M": s["mean"] > b["mean"], "V": (s["var_min"] < b["var_lo"]) | (s["var_max"] > b["var_hi"]),
            "A": s["lag1"] > b["lag1"], "P": s["lag1_pooled"] > b["lag1_pooled"]}


NORM_RTOL = 1e-6        # registered N tolerance (relative)
INWARD_MARGIN = 1e-5    # internal projection target for M and V (B2); NOT a change of the registered bounds
MODEL_DTYPE = np.float32


def feasible(x, b, norm2):
    """Hard check for one hand x [C, L] (any float dtype; evaluated in float64). B1: non-finite arrays are rejected
    before any comparison (comparisons with NaN are False and would otherwise pass). Returns (ok, detail)."""
    x = np.asarray(x)
    if not np.isfinite(x).all() or not np.isfinite(norm2):
        return False, {"finite": False, "N": True, "M": True, "V": True, "A": True, "P": True}
    x = x.astype(np.float64)
    s = stats(x[None])
    v = {k: bool(m[0]) for k, m in violations(s, b).items()}
    v["N"] = not abs(float((x ** 2).sum()) - norm2) <= NORM_RTOL * norm2
    v["finite"] = True
    return not any(v[k] for k in ("N", "M", "V", "A", "P")), v


def mvn_ok(x, b, norm2):
    """Finite and N, M, V satisfied (the projection's own responsibility)."""
    ok, v = feasible(x, b, norm2)
    return bool(v["finite"] and not (v["N"] or v["M"] or v["V"]))


def project_mvn_alternating(x, b, norm2, iters=5):
    """Original E-1 (rev. 1 of C-c3): clamp means, clamp second moments, rescale norm; repeat `iters` times."""
    x = x.copy()
    for _ in range(iters):
        m = x.mean(1, keepdims=True)
        x = x - (m - np.clip(m, -b["mean"], b["mean"]))
        q = (x ** 2).mean(1, keepdims=True)
        x = x * np.sqrt(np.clip(q, b["var_lo"], b["var_hi"]) / q)
        x = x * np.sqrt(norm2 / (x ** 2).sum())
    return x


def project_mvn_exact(x, b, norm2, tol=1e-13, margin=INWARD_MARGIN):
    """E-1 (amendment 2): one-shot projection satisfying M, V and N simultaneously.
    (1) clamp channel means into the M band shrunk by `margin`; (2) keep means fixed and set each channel's centred
    energy so that q_c = m_c^2 + s_c^2 v_c lies in the V band shrunk by `margin` and sum_c q_c = norm2 / L, via one
    common log-scale t (monotone; bracket found by expansion, then bisection).
    Returns (y, ok). ok is True ONLY if y is finite and satisfies N, M and V when checked (B1). Any input that is
    non-finite, has a constant or numerically degenerate channel, or for which the target cannot be bracketed, gives
    ok = False; the caller must then not use y."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all() or not np.isfinite(norm2) or norm2 <= 0:
        return x, False
    C, L = x.shape
    mb, vlo, vhi = b["mean"] * (1 - margin), b["var_lo"] * (1 + margin), b["var_hi"] * (1 - margin)
    mu = x.mean(1, keepdims=True)
    m = np.clip(mu, -mb, mb)
    d = x - mu
    v = (d ** 2).mean(1)  # centred second moment per channel
    target = norm2 / L
    m2 = m[:, 0] ** 2
    # degenerate channels: no centred energy to scale (constant), or so little that scaling it to the band would
    # amplify rounding error beyond ~1e-6 relative (v below ~1e-24 of the lower band edge): fail safely
    if np.any(m2 > vhi) or np.any(~np.isfinite(v)) or np.any(v <= vlo * 1e-24):
        return x, False
    lo_q, hi_q = np.maximum(vlo, m2), np.full(C, vhi)
    if not (lo_q.sum() <= target <= hi_q.sum()):
        return x, False

    def total(t):
        return np.clip(m2 + np.exp(2 * t) * v, lo_q, hi_q).sum()

    a, c = -1.0, 1.0
    for _ in range(200):  # expand the bracket until it contains the target
        if total(a) <= target <= total(c):
            break
        a, c = a - 2.0 * (c - a), c + 2.0 * (c - a)
        if not (np.isfinite(total(a)) and np.isfinite(total(c))) or c - a > 1e4:
            return x, False
    else:
        return x, False
    for _ in range(300):
        mid = 0.5 * (a + c)
        if total(mid) < target:
            a = mid
        else:
            c = mid
        if c - a < tol:
            break
    q = np.clip(m2 + np.exp(2 * (0.5 * (a + c))) * v, lo_q, hi_q)
    s = np.sqrt(np.maximum(q - m2, 0) / v)
    y = m + s[:, None] * d
    if not mvn_ok(y, b, norm2):  # B1: verify the actual output
        return y, False
    return y, True


def to_model_input(x, b, norm2, dtype=MODEL_DTYPE, max_reproject=3):
    """B2: produce the exact model-input array. Project (E-1), cast to the model dtype, and check finiteness and
    N/M/V on that cast array (upcast to float64). If the cast breaks a constraint, re-project from the cast array and
    re-check, up to `max_reproject` times. Returns (x_model, ok_mvn, detail) where detail is feasible() on x_model
    (it includes A and P, which projection does not enforce; E-3 requires the full check)."""
    y, ok = project_mvn_exact(x, b, norm2)
    if not ok:
        return np.asarray(x).astype(dtype), False, {"reason": "projection failed"}
    for attempt in range(max_reproject + 1):
        xm = y.astype(dtype)
        if mvn_ok(xm, b, norm2):
            full, det = feasible(xm, b, norm2)
            det["reprojections"] = attempt
            return xm, True, det
        y, ok = project_mvn_exact(xm.astype(np.float64), b, norm2)
        if not ok:
            break
    return y.astype(dtype), False, {"reason": "cast violates N/M/V after re-projection"}


def repair_ap(x, b, norm2, lam=100.0, steps=300, lr=0.01, dtype=MODEL_DTYPE):
    """E-4 for A and P: minimise ||y - x||^2 / ||x||^2 + lam * hinge^2(A, P) by Adam on y (noise only), followed after
    each step by E-1; stops at the first iterate whose MODEL-INPUT array (B2: cast to `dtype`) passes the full hard
    check. Synthetic-array routine (no model). Returns (y_model, ok, steps_used); ok False = no feasible point found
    within `steps` (safe failure; the caller must apply E-5)."""
    import torch
    x = np.asarray(x, dtype=np.float64)
    if not np.isfinite(x).all():
        return x.astype(dtype), False, 0
    xm, okm, _ = to_model_input(x, b, norm2, dtype)
    if okm and feasible(xm, b, norm2)[0]:
        return xm, True, 0
    x0 = torch.as_tensor(x, dtype=torch.float64)
    y = x0.clone().requires_grad_(True)
    opt = torch.optim.Adam([y], lr=lr)
    for i in range(1, steps + 1):
        r = (y[:, 1:] * y[:, :-1]).sum(1) / (y ** 2).sum(1)
        loss = ((y - x0) ** 2).sum() / (x0 ** 2).sum() + lam * (torch.relu(r.abs() - b["lag1"]) ** 2).sum() \
            + lam * torch.relu(r.mean().abs() - b["lag1_pooled"]) ** 2
        opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            if not torch.isfinite(y).all():
                break
            ym, okm, _ = to_model_input(y.detach().numpy(), b, norm2, dtype)
            if okm:
                y.copy_(torch.as_tensor(ym.astype(np.float64)))
                if feasible(ym, b, norm2)[0]:
                    return ym, True, i
    return y.detach().numpy().astype(dtype), False, steps
