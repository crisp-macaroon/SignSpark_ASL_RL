"""E2b: time-shift equivariance (Stage 4 rev. 4.0 §15.2 l. 951; pre-registrations C-b1..C-b3). NON-GATING.

C-b1  eps'(tau) = eps(tau - delta) inside the active frames; vacated frames get fresh N(0, 1) noise
      (seed 30,000,000 + 1000*j + (delta + 100)); padded frames unchanged; body and both hands shifted together.
      Base noise: A0 k = 1 (E2e seeds).
C-b2  E(delta) per stream = Pearson corr between the shifted-noise output's speed profile s'(tau) and the base
      output's profile s(tau - delta), over overlapping frames; mean over 32 clips with 95% bootstrap CI
      (2,000, seed 0). Streams: body arm (mean geodesic speed of both elbows and wrists), L hand, R hand.
      References: identical noise (delta = 0) = 1 by construction (checked); independent noise = A0 k = 2 vs k = 1.
C-b3  "viable" iff E(delta) >= 0.5 for |delta| <= 8 in every stream (point means). No action or architecture change
      follows from it.
delta in {-16, -8, -4, 4, 8, 16}. Cap 1 h.

    python -E -s experiments/stage4/e2b/e2b_run.py --out experiments/stage4/e2b/out
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gpu_common as G  # noqa: E402

DELTAS = (-16, -8, -4, 4, 8, 16)
FRESH_BASE = 30_000_000


def shifted(eps, L, delta, j):
    """eps [240, 304] -> shifted copy (C-b1)."""
    out = eps.clone()
    g = torch.Generator().manual_seed(FRESH_BASE + 1000 * j + (delta + 100))
    fresh = torch.randn(240, L, generator=g)
    for t in range(L):
        s = t - delta
        out[:, t] = eps[:, s] if 0 <= s < L else fresh[:, t]
    return out


def profiles(xb, xh, L):
    w = G.MR.joint_speed(G.MR.to_mats(xb[:, :L]))
    return {"body_arm": w[:, [6, 7, 8, 9]].mean(1), "L": G.hand_speed(xh[0], L), "R": G.hand_speed(xh[1], L)}


def generate(ctx, eps):
    with torch.no_grad():
        xb = ctx.body(eps[:, :60].cuda(), list(range(G.J))).cpu().numpy()
        eh = torch.stack([eps[:, 60:150], eps[:, 150:]], 1).reshape(2 * G.J, 90, 304).cuda()
        xh = ctx.hand(eh, list(range(2 * G.J))).cpu().numpy().reshape(G.J, 2, 90, 304)
    return xb, xh


def eq_index(p_new, p_base, delta):
    out = {}
    for k in p_new:
        a, b = p_new[k], p_base[k]
        n = len(a)
        t = np.arange(n)
        ok = (t - delta >= 0) & (t - delta < n)
        out[k] = G.MR.corr(a[ok], b[t[ok] - delta]) if ok.sum() >= 3 else np.nan
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    ctx = G.Ctx()
    L = ctx.lengths
    base = torch.stack([G.noise("A0", j, 1) for j in range(G.J)])
    indep = torch.stack([G.noise("A0", j, 2) for j in range(G.J)])
    xb0, xh0 = generate(ctx, base)
    xb0b, xh0b = generate(ctx, base)
    xbi, xhi = generate(ctx, indep)
    P0 = [profiles(xb0[j], xh0[j], L[j]) for j in range(G.J)]
    res = {"label": "E2b (non-gating); released-checkpoint results, not a paper reproduction", "flags": ctx.flags(),
           "E": {}, "reference": {}}
    streams = ("body_arm", "L", "R")
    ident = [eq_index(profiles(xb0b[j], xh0b[j], L[j]), P0[j], 0) for j in range(G.J)]
    ind = [eq_index(profiles(xbi[j], xhi[j], L[j]), P0[j], 0) for j in range(G.J)]
    res["reference"]["identical_noise_delta0"] = {s: G.boot_mean_ci([v[s] for v in ident]) for s in streams}
    res["reference"]["independent_noise_delta0"] = {s: G.boot_mean_ci([v[s] for v in ind]) for s in streams}
    for d in DELTAS:
        eps = torch.stack([shifted(base[j], L[j], d, j) for j in range(G.J)])
        xb, xh = generate(ctx, eps)
        e = [eq_index(profiles(xb[j], xh[j], L[j]), P0[j], d) for j in range(G.J)]
        res["E"][d] = {s: G.boot_mean_ci([v[s] for v in e]) for s in streams}
        print(f"[{time.time() - t0:5.0f}s] delta {d}: " + ", ".join(f"{s} {res['E'][d][s]['mean']:.3f}" for s in streams), flush=True)
    res["viable_C-b3"] = bool(all(res["E"][d][s]["mean"] >= 0.5 for d in DELTAS if abs(d) <= 8 for s in streams))
    res["verdict"] = "low-dimensional time-shift action viable" if res["viable_C-b3"] else "low-dimensional time-shift action not viable"
    res["peak_reserved_GiB"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
    res["seconds"] = round(time.time() - t0)
    res["status"] = "completed"
    (out / "e2b_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
