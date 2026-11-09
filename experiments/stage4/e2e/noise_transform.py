"""E2e fixed noise transforms (Stage 4 rev. 4.0 §15.3; App. G.1–G.4). Constants only: no learnable
parameters, no controller network, no training.

Per active frame tau <= L, with base noise eps = (eps_b in R^60, eps_L in R^90, eps_R in R^90):
    z_b = eps_b
    z_L = K_L eps_b + S_L eps_L
    z_R = K_Rb eps_b + K_RL eps_L + S_R eps_R          (K_R = [K_Rb, K_RL], 90 x 150)
    eps~ = (z_b, sigma_L z_L, sigma_R z_R);  padded frames: eps~ = eps.
K = U diag(kappa) V^T with Stiefel U (90 x r), V (source x r); S = I - U diag(1 - sqrt(1 - kappa^2)) U^T.
"""

import numpy as np

BODY, HAND = 60, 90
# body channels are joint-major 6D blocks over the 10 predicted joints
# [Neck, L_Collar, R_Collar, Head, L_Shoulder, R_Shoulder, L_Elbow, R_Elbow, L_Wrist, R_Wrist]
ARM_CH = {"L": [c for j in (6, 8) for c in range(6 * j, 6 * j + 6)],
          "R": [c for j in (7, 9) for c in range(6 * j, 6 * j + 6)]}


def stiefel(n, r, rng):
    """Random n x r matrix with orthonormal columns: QR of a Gaussian, signs fixed by diag(R) > 0."""
    q, rr = np.linalg.qr(rng.standard_normal((n, r)))
    return q * np.sign(np.diag(rr))[None, :]


def selection(n, idx):
    v = np.zeros((n, len(idx)))
    v[idx, np.arange(len(idx))] = 1.0
    return v


def s_matrix(u, kappa):
    return np.eye(u.shape[0]) - u @ np.diag(1.0 - np.sqrt(1.0 - kappa ** 2)) @ u.T


def build(spec):
    """spec: dict(name, kind in {base, BH, BH_arm, LR, SS}, r, kappa, seed, sigma=(sL, sR)).
    Returns dict of float64 matrices K_L (90x60), K_Rb (90x60), K_RL (90x90), S_L, S_R (90x90), sigma."""
    kind = spec["kind"]
    zero_b, zero_h, eye = np.zeros((HAND, BODY)), np.zeros((HAND, HAND)), np.eye(HAND)
    out = {"K_L": zero_b.copy(), "K_Rb": zero_b.copy(), "K_RL": zero_h.copy(), "S_L": eye.copy(), "S_R": eye.copy(),
           "sigma": np.array(spec.get("sigma", (1.0, 1.0)), float), "kappa_L": np.zeros(0), "kappa_R": np.zeros(0)}
    if kind in ("base", "SS"):
        return out
    k, r = float(spec["kappa"]), int(spec["r"])
    rng = np.random.default_rng(spec["seed"])
    kap = np.full(r, k)
    if kind == "BH":  # full body rank, random orientations; K_RL = 0
        u_l, v_l = stiefel(HAND, r, rng), stiefel(BODY, r, rng)
        u_r, v_r = stiefel(HAND, r, rng), stiefel(BODY, r, rng)
    elif kind == "BH_arm":  # hypothesis-driven V: each hand's own elbow + wrist channels; U random
        u_l, v_l = stiefel(HAND, r, rng), selection(BODY, ARM_CH["L"])
        u_r, v_r = stiefel(HAND, r, rng), selection(BODY, ARM_CH["R"])
    elif kind == "LR":  # K_L = 0, K_Rb = 0, K_RL = kappa U V^T
        u, v = stiefel(HAND, r, rng), stiefel(HAND, r, rng)
        out["K_RL"] = u @ np.diag(kap) @ v.T
        out["S_R"] = s_matrix(u, kap)
        out["kappa_R"] = kap
        return out
    else:
        raise ValueError(kind)
    out["K_L"], out["S_L"], out["kappa_L"] = u_l @ np.diag(kap) @ v_l.T, s_matrix(u_l, kap), kap
    out["K_Rb"], out["S_R"], out["kappa_R"] = u_r @ np.diag(kap) @ v_r.T, s_matrix(u_r, kap), kap
    return out


def joint_cov(m):
    """Exact covariance of (z_b, z_L, z_R) before sigma (240 x 240) implied by the construction."""
    A = np.zeros((240, 240))
    A[:60, :60] = np.eye(60)
    A[60:150, :60], A[60:150, 60:150] = m["K_L"], m["S_L"]
    A[150:, :60], A[150:, 60:150], A[150:, 150:] = m["K_Rb"], m["K_RL"], m["S_R"]
    return A @ A.T, A


def analytic_checks(m):
    """T1 (a): diagonal blocks = I; min eigenvalue; closed-form vs numeric log-det (of D Sigma D)."""
    sig, A = joint_cov(m)
    d = np.concatenate([np.ones(60), np.full(90, m["sigma"][0]), np.full(90, m["sigma"][1])])
    full = d[:, None] * sig * d[None, :]
    blocks = [sig[:60, :60], sig[60:150, 60:150], sig[150:, 150:]]
    diag_dev = max(float(np.abs(b - np.eye(b.shape[0])).max()) for b in blocks)
    lam_min = float(np.linalg.eigvalsh(sig).min())
    closed = float(np.sum(np.log(1 - m["kappa_L"] ** 2)) + np.sum(np.log(1 - m["kappa_R"] ** 2))
                   + 2 * 90 * (np.log(m["sigma"][0]) + np.log(m["sigma"][1])))
    numeric = float(np.linalg.slogdet(full)[1])
    rel = abs(closed - numeric) / max(abs(closed), 1e-12) if abs(closed) > 1e-12 else abs(numeric)
    return {"max_diag_block_dev": diag_dev, "lambda_min": lam_min, "logdet_closed": closed, "logdet_numeric": numeric,
            "logdet_rel_err": rel,
            "pass": diag_dev <= 1e-5 and lam_min >= 1e-3 and (rel <= 1e-6 or abs(closed - numeric) <= 1e-9)}


def kl_per_frame(m):
    """Exact KL(q || N(0, I)) per active frame (App. G.4): coupling + scale."""
    kc = -0.5 * np.sum(np.log(1 - m["kappa_L"] ** 2)) - 0.5 * np.sum(np.log(1 - m["kappa_R"] ** 2))
    s = m["sigma"]
    ks = 0.5 * 90 * sum(v ** 2 - 1 - np.log(v ** 2) for v in s)
    return float(kc), float(ks)


def apply(m, eps, lengths):
    """eps: torch tensor [N, 240, T] (body 0:60, L 60:150, R 150:240); returns eps~ with padded frames untouched."""
    import torch
    dev, dt = eps.device, eps.dtype
    t = {k: torch.as_tensor(v, device=dev, dtype=dt) for k, v in m.items() if k in ("K_L", "K_Rb", "K_RL", "S_L", "S_R")}
    eb, el, er = eps[:, :60], eps[:, 60:150], eps[:, 150:]
    zl = torch.einsum("ij,njt->nit", t["K_L"], eb) + torch.einsum("ij,njt->nit", t["S_L"], el)
    zr = (torch.einsum("ij,njt->nit", t["K_Rb"], eb) + torch.einsum("ij,njt->nit", t["K_RL"], el)
          + torch.einsum("ij,njt->nit", t["S_R"], er))
    z = torch.cat([eb, float(m["sigma"][0]) * zl, float(m["sigma"][1]) * zr], dim=1)
    T = eps.shape[-1]
    active = (torch.arange(T, device=dev)[None, :] < torch.as_tensor(lengths, device=dev)[:, None])[:, None, :]
    return torch.where(active, z, eps)


CONDITIONS = (
    [{"name": "A0", "kind": "base"}, {"name": "A0p", "kind": "base"}]
    + [{"name": f"BH-r60-k{k}-seed0", "kind": "BH", "r": 60, "kappa": k, "seed": 0} for k in (0.3, 0.6, 0.9)]
    + [{"name": f"BH-r60-k0.9-seed{s}", "kind": "BH", "r": 60, "kappa": 0.9, "seed": s} for s in (1, 2)]
    + [{"name": "BH-arm12-k0.9", "kind": "BH_arm", "r": 12, "kappa": 0.9, "seed": 0}]
    + [{"name": f"LR-r90-k{k}-seed0", "kind": "LR", "r": 90, "kappa": k, "seed": 0} for k in (0.6, 0.9)]
    + [{"name": f"LR-r90-k0.9-seed{s}", "kind": "LR", "r": 90, "kappa": 0.9, "seed": s} for s in (1, 2)]
    + [{"name": f"SS-{a}-{b}", "kind": "SS", "sigma": (a, b)} for a, b in ((0.9, 1.0), (0.75, 1.0), (1.0, 1.15), (0.85, 1.15))]
)
GATE = ("BH-r60-k0.9-seed0", "LR-r90-k0.9-seed0")
