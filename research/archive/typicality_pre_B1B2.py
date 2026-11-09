"""E2c (i) N4 typicality constraints (proposed pre-registration C-c3 rev.; NOT registered until approved).

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


NORM_RTOL = 1e-6


def feasible(x, b, norm2):
    """Hard check of all five constraints for one hand x [C, L]; norm2 = required ||x||^2. Returns (ok, detail)."""
    s = stats(x[None])
    v = {k: bool(m[0]) for k, m in violations(s, b).items()}
    v["N"] = abs(float((x ** 2).sum()) - norm2) > NORM_RTOL * norm2
    return not any(v.values()), v


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


def project_mvn_exact(x, b, norm2, tol=1e-12):
    """Proposed E-1 (rev. 2): one-shot projection satisfying M, V and N simultaneously whenever the set is non-empty.
    (1) clamp channel means into the M band (shift); (2) keep means fixed and set each channel's centred energy so that
    its second moment q_c = m_c^2 + s_c^2 v_c lies in [lo, hi] and sum_c q_c = norm2 / L, via a common log-scale t
    applied to all centred parts and clipped to the band (monotone in t, solved by bisection).
    Returns (x_projected, ok). ok is False only if the set is empty or degenerate (then the caller must not use x)."""
    C, L = x.shape
    eps = 1e-9  # aim a hair inside each band so floating-point error cannot leave it (bounds themselves unchanged)
    mb, vlo, vhi = b["mean"] * (1 - eps), b["var_lo"] * (1 + eps), b["var_hi"] * (1 - eps)
    m = np.clip(x.mean(1, keepdims=True), -mb, mb)
    d = x - x.mean(1, keepdims=True)
    v = (d ** 2).mean(1)  # centred second moment per channel
    target = norm2 / L
    m2 = m[:, 0] ** 2
    if np.any(m2 > vhi) or np.any(v <= 0):
        return x, False
    lo_q, hi_q = np.maximum(vlo, m2), np.full(C, vhi)
    if not (lo_q.sum() <= target <= hi_q.sum()):
        return x, False

    def q_of(t):
        return np.clip(m2 + np.exp(2 * t) * v, lo_q, hi_q)

    a, c = -20.0, 20.0
    for _ in range(200):
        mid = 0.5 * (a + c)
        if q_of(mid).sum() < target:
            a = mid
        else:
            c = mid
        if c - a < tol:
            break
    q = q_of(0.5 * (a + c))
    s = np.sqrt(np.maximum(q - m2, 0) / v)
    y = m + s[:, None] * d  # channel means stay m; sum of second moments = target to bisection precision
    return y, True


def repair_ap(x, b, norm2, lam=100.0, steps=300, lr=0.01):
    """Proposed E-4 for A and P: minimise ||y - x||^2 / ||x||^2 + lam * hinge^2(A, P) by Adam on y, followed after each
    step by project_mvn_exact; stops at the first iterate that passes the full hard check. Synthetic-array routine
    (no model). Returns (y, ok, steps_used); ok False means no feasible point was found (safe failure)."""
    import torch
    x0 = torch.as_tensor(x, dtype=torch.float64)
    y = x0.clone().requires_grad_(True)
    opt = torch.optim.Adam([y], lr=lr)
    ok, _ = feasible(x, b, norm2)
    if ok:
        return x, True, 0
    for i in range(1, steps + 1):
        r = (y[:, 1:] * y[:, :-1]).sum(1) / (y ** 2).sum(1)
        loss = ((y - x0) ** 2).sum() / (x0 ** 2).sum() + lam * (torch.relu(r.abs() - b["lag1"]) ** 2).sum() \
            + lam * torch.relu(r.mean().abs() - b["lag1_pooled"]) ** 2
        opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            yp, okp = project_mvn_exact(y.detach().numpy(), b, norm2)
            if okp:
                y.copy_(torch.as_tensor(yp))
                if feasible(yp, b, norm2)[0]:
                    return yp, True, i
    return y.detach().numpy(), False, steps
