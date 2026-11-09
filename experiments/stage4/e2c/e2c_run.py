"""E2c: family-capacity tests (Stage 4 rev. 4.0 §15.2 l. 952; pre-registrations C-c1..C-c6, C-c3 amendment 2).

Per-clip optimisation of NOISE or Gaussian-family parameters on dev clips 0..31. Model weights frozen
(requires_grad = False), never updated; Adam acts only on noise / family parameters. Released checkpoints.

C-c1  objective: right arm - right hand coordination (space R). Registered evaluation metric = geodesic speeds
      (e2e/metrics.py). The gradient surrogate uses chordal speeds (E2d statistic; monotone in the angle).
      Only the right hand enters the objective, so only the right-hand noise is optimised / generated.
C-c2  comparators from E2e A0 k = 1..8 (body r x right hand s): PRIMARY typical-only best-of-8x8 (right-hand
      candidates whose noise fails the C-c3 check are excluded, not projected); SECONDARY all-candidate (E2e A0) and
      the existing dev-256 N = 8 GF dumps (clips 0..31). The A3 figure 0.408 (256 clips) is reported alongside.
      Verdict differing between primary and secondary => "comparator-sensitive". Results also split at L < 100 / >= 100.
C-c3  (i) N4 typicality (amendment 2): finiteness + N/M/V/A/P on the float32 model-input array; E-1 exact projection
      (margin 1e-5) after every Adam step; E-2 A/P penalty lambda = 100; E-3 hard gate (only feasible iterates count);
      E-4 feasible start (projection + repair <= 300 steps); E-5 no feasible start => not optimised, enters at the
      unprojected base objective (zero gain), marked; > 3 such clips => N4 "inconclusive (feasibility)".
      Monitored (non-gating): pooled lag-2..4, max |corr| with the body noise, chi^2 position of ||x||^2.
C-c4  (ii) per-clip Stiefel U (90 x 60), V (60 x 60) by QR (sign-fixed), kappa = min(0.95 sigmoid(a), 0.9);
      right-hand coupling K = U diag(kappa) V^T on the body noise, S = I - U diag(1 - sqrt(1 - kappa^2)) U^T; exact KL
      per frame = -1/2 sum log(1 - kappa^2) <= 49.82 (right hand only) <= 99.64 bound.
      Init (implementation choice, recorded): Gaussian U, V seed 1000 + j; a such that kappa = 0.1.
C-c5  Adam lr 0.05; (i) 40 iterations, start A0 hand noise k = 1, body fixed at A0 k = 1; (ii) 30 iterations,
      expectation over A0 k = 1..4, evaluated on held-out A0 k = 5..8. K = 10, per-step checkpointing.
C-c6  "reaches the best-of-8x8 level" = mean over clips of the reported (i) result (best feasible iterate or E-5
      imputation), or the mean held-out (ii) coordination, >= the C-c2 level. Both fail => registered negative
      outcome (FM4: report options; no automatic switch). Cap 2 h.

    python -E -s experiments/stage4/e2c/e2c_run.py --dumps experiments/stage4/e2e/dumps --out experiments/stage4/e2c/out
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import gpu_common as G  # noqa: E402
import typicality as T  # noqa: E402

CAP_S = 2 * 3600
LR = 0.05
ITERS_I, ITERS_II = 40, 30
BATCH_I, BATCH_II_CLIPS = 8, 4
KAPPA_INIT = 0.1
DEV256 = {s: G.ROOT / f"experiments/baseline/runs/{s}/h2s_dev256_gf_s10_N8/debug0_eulerstepsize10_can8_anchor0_samples/seed102_clampstep0_h2s_dev256_gf_s10_N8.npy"
          for s in ("body", "hand")}
A3_256 = 0.408


class Cap(Exception):
    pass


def geo_coord(xb6, xr6, L):
    return G.MR.corr(G.arm_r_speed(xb6, L), G.hand_speed(xr6, L))


def surrogate(xb, xh, L):
    """Differentiable corr(R-arm, R-hand) per row with chordal speeds; xb [n, 60, T] (no grad), xh [n, 90, T]."""
    sa = G.E2D.speeds(xb, [7, 9])
    sh = G.E2D.speeds(xh, None)
    out = []
    for i in range(xb.shape[0]):
        m = torch.zeros(sa.shape[1], dtype=torch.bool, device=sa.device)
        m[: L[i] - 1] = True
        out.append(G.E2D.corr(sa[i], sh[i], m))
    return torch.stack(out)


def ap_penalty(p, b, lam=100.0):
    r = (p[:, 1:] * p[:, :-1]).sum(1) / (p ** 2).sum(1)
    return lam * (torch.relu(r.abs() - b["lag1"]) ** 2).sum() + lam * torch.relu(r.mean().abs() - b["lag1_pooled"]) ** 2


def monitor(x, body_noise, L):
    """Non-gating flags (C-c3 D6)."""
    from scipy.stats import chi2, norm
    s = T.stats(x[None].astype(np.float64))
    flags = {f"lag{k}_pooled": bool(s[f"lag{k}_pooled"][0] > 3.29 / np.sqrt(90 * (L - k))) for k in (2, 3, 4)}
    xc = x - x.mean(1, keepdims=True)
    bc = body_noise - body_noise.mean(1, keepdims=True)
    c = (xc @ bc.T) / (np.linalg.norm(xc, axis=1)[:, None] * np.linalg.norm(bc, axis=1)[None, :] + 1e-30)
    thr = norm.ppf(1 - 0.005 / (2 * 5400)) / np.sqrt(L)
    q = float((x.astype(np.float64) ** 2).sum())
    lo, hi = chi2.ppf(0.0005, 90 * L), chi2.ppf(0.9995, 90 * L)
    flags["hand_body_corr"] = bool(np.abs(c).max() > thr)
    flags["norm_chi2_outside_99.9"] = bool(q < lo or q > hi)
    return flags


def comparators(ctx, dumps):
    L = ctx.lengths
    a0 = {k: np.load(dumps / "A0" / f"k{k:02d}.npz") for k in range(1, 9)}
    body = {k: a0[k]["body"] for k in a0}
    hand_r = {k: a0[k]["hand"][:, 1] for k in a0}
    typ = np.zeros((G.J, 8), bool)
    for j in range(G.J):
        b = T.bounds(L[j])
        for k in range(1, 9):
            x = G.noise("A0", j, k)[150:240, : L[j]].numpy()  # the exact float32 model-input right-hand noise
            typ[j, k - 1] = T.feasible(x, b, float((x.astype(np.float64) ** 2).sum()))[0]
    best_all, best_typ = np.zeros(G.J), np.full(G.J, np.nan)
    for j in range(G.J):
        C = np.array([[geo_coord(body[r][j], hand_r[s][j], L[j]) for s in range(1, 9)] for r in range(1, 9)])
        best_all[j] = np.nanmax(C)
        if typ[j].any():
            best_typ[j] = np.nanmax(C[:, typ[j]])
    db = np.load(DEV256["body"], allow_pickle=True).item()  # our own dumps (dict pickled by np.save)
    dh = np.load(DEV256["hand"], allow_pickle=True).item()
    best_dev = np.array([np.nanmax([[geo_coord(db["pred_poses"][r, j], dh["pred_poses"][s, 2 * j + 1], L[j]) for s in range(8)]
                                    for r in range(8)]) for j in range(G.J)])
    return {"primary_typical_only": float(np.nanmean(best_typ)), "secondary_all_candidate_E2e": float(np.mean(best_all)),
            "secondary_dev256_dumps": float(np.mean(best_dev)), "A3_256_registered": A3_256,
            "typical_candidates_per_clip_mean": float(typ.sum(1).mean()), "clips_without_typical_candidate": int((~typ.any(1)).sum()),
            "per_clip": {"typical_only": best_typ.tolist(), "all_candidate": best_all.tolist(), "dev256": best_dev.tolist()}}, body, hand_r


def part_i(ctx, body_a0, t0):
    L = ctx.lengths
    eps = [G.noise("A0", j, 1) for j in range(G.J)]
    xb_fixed = torch.as_tensor(np.stack([body_a0[1][j] for j in range(G.J)])).cuda()
    base_rows = torch.stack([e[150:240] for e in eps]).cuda()  # right-hand base noise [J, 90, 304]
    raw_obj = None
    with torch.no_grad():
        xh = ctx.hand(base_rows, [2 * j + 1 for j in range(G.J)]).cpu().numpy()
    raw_obj = np.array([geo_coord(body_a0[1][j], xh[j], L[j]) for j in range(G.J)])
    # E-4 feasible start / E-5
    start, status, rel = {}, {}, {}
    for j in range(G.J):
        b = T.bounds(L[j])
        x = eps[j][150:240, : L[j]].numpy()
        n2 = float((x.astype(np.float64) ** 2).sum())
        if T.feasible(x, b, n2)[0]:
            start[j], status[j], rel[j] = x.astype(np.float32), "raw start feasible", 0.0
        else:
            y, ok, steps = T.repair_ap(x.astype(np.float64), b, n2)
            if ok and T.feasible(y, b, n2)[0]:
                start[j], status[j] = y.astype(np.float32), f"projected start (E-4, {steps} repair steps)"
                rel[j] = float(np.linalg.norm(y - x) / np.linalg.norm(x))
            else:
                status[j] = "no feasible start (E-5)"
    opt_clips = sorted(start)
    params = {j: torch.tensor(start[j], device="cuda", requires_grad=True) for j in opt_clips}
    norm2 = {j: float((start[j].astype(np.float64) ** 2).sum()) for j in opt_clips}
    opt = torch.optim.Adam(list(params.values()), lr=LR)
    best = {j: (-np.inf, None, -1) for j in opt_clips}  # (objective, noise, iteration)
    start_obj = {}
    gate_fail = {j: 0 for j in opt_clips}
    for it in range(ITERS_I + 1):  # iteration ITERS_I evaluates the last iterate without a step
        if time.time() - t0 > CAP_S:
            raise Cap(f"cap reached during (i) iteration {it}")
        opt.zero_grad()
        for bs in range(0, len(opt_clips), BATCH_I):
            clips = opt_clips[bs: bs + BATCH_I]
            noise = base_rows[clips].clone()
            for i, j in enumerate(clips):
                noise[i, :, : L[j]] = params[j]
            xh = ctx.hand(noise, [2 * j + 1 for j in clips], ck=True)
            lj = [L[j] for j in clips]
            surr = surrogate(xb_fixed[clips], xh, lj)
            xn = xh.detach().cpu().numpy()
            for i, j in enumerate(clips):
                pj = params[j].detach().cpu().numpy()  # float32 = the exact model-input array (E-3)
                ok = T.feasible(pj, T.bounds(L[j]), norm2[j])[0]
                obj = geo_coord(body_a0[1][j], xn[i], L[j])
                if it == 0:
                    start_obj[j] = obj
                if ok and np.isfinite(obj) and obj > best[j][0]:
                    best[j] = (obj, pj.copy(), it)
                if not ok:
                    gate_fail[j] += 1
            if it < ITERS_I:
                loss = -surr.sum() + sum(ap_penalty(params[j], T.bounds(L[j])) for j in clips)
                loss.backward()
        if it == ITERS_I:
            break
        opt.step()
        with torch.no_grad():  # E-1 + float32 model-input check after every step
            for j in opt_clips:
                xm, ok, _ = T.to_model_input(params[j].detach().cpu().numpy().astype(np.float64), T.bounds(L[j]), norm2[j])
                if ok:
                    params[j].copy_(torch.as_tensor(xm, device="cuda"))
        if it % 5 == 0:
            print(f"[{time.time() - t0:6.0f}s] (i) iter {it} mean best {np.mean([best[j][0] for j in opt_clips]):.3f}", flush=True)
    reported = np.array([best[j][0] if j in best and best[j][1] is not None else raw_obj[j] for j in range(G.J)])
    e5 = [j for j in range(G.J) if status[j].startswith("no feasible") or (j in best and best[j][1] is None)]
    for j in e5:
        reported[j] = raw_obj[j]
    mon = {j: monitor(best[j][1], eps[j][:60, : L[j]].numpy(), L[j]) for j in opt_clips if best[j][1] is not None}
    return {"reported_per_clip": reported.tolist(), "raw_start_obj": raw_obj.tolist(),
            "projected_start_obj": [start_obj.get(j) for j in range(G.J)], "start_status": status, "start_rel_change": rel,
            "best_iteration": {j: best[j][2] for j in opt_clips}, "gate_failures_per_clip": gate_fail,
            "e5_clips": e5, "e5_count": len(e5), "inconclusive_feasibility": len(e5) > 3,
            "mean_reported": float(np.mean(reported)), "mean_raw_start": float(np.mean(raw_obj)),
            "mean_gain_vs_raw_start": float(np.mean(reported - raw_obj)),
            "feasible_only_mean": float(np.mean([reported[j] for j in range(G.J) if j not in e5])) if len(e5) < G.J else None,
            "monitoring_flags": mon,
            "monitoring_flag_counts": {k: int(sum(m[k] for m in mon.values())) for k in (next(iter(mon.values())).keys() if mon else [])}}


def family_params(j):
    g = torch.Generator().manual_seed(1000 + j)
    Ut = torch.randn(90, 60, generator=g)
    Vt = torch.randn(60, 60, generator=g)
    a0 = float(np.log((KAPPA_INIT / 0.95) / (1 - KAPPA_INIT / 0.95)))
    return [t.cuda().requires_grad_(True) for t in (Ut, Vt, torch.full((60,), a0))]


def stiefel(M):
    q, r = torch.linalg.qr(M)
    return q * torch.sign(torch.diagonal(r))[None, :]


def coupled(params, eb, er):
    """eb [60, L], er [90, L] -> right-hand noise z = K eb + S er; returns z and the exact KL per frame."""
    Ut, Vt, a = params
    U, V = stiefel(Ut), stiefel(Vt)
    kap = torch.clamp(0.95 * torch.sigmoid(a), max=0.9)
    K = U @ torch.diag(kap) @ V.T
    S = torch.eye(90, device=U.device) - U @ torch.diag(1 - torch.sqrt(1 - kap ** 2)) @ U.T
    return K @ eb + S @ er, float((-0.5 * torch.log(1 - kap ** 2)).sum())


def part_ii(ctx, body_a0, t0):
    L = ctx.lengths
    P = {j: family_params(j) for j in range(G.J)}
    opt = torch.optim.Adam([p for j in P for p in P[j]], lr=LR)
    eps = {(j, k): G.noise("A0", j, k).cuda() for j in range(G.J) for k in range(1, 9)}
    xb = {k: torch.as_tensor(np.stack([body_a0[k][j] for j in range(G.J)])).cuda() for k in range(1, 9)}

    def batch_out(clips, ks, grad):
        rows, noise, xbs, lj = [], [], [], []
        kls = []
        for j in clips:
            for k in ks:
                e = eps[(j, k)]
                z, kl = coupled(P[j], e[:60, : L[j]], e[150:240, : L[j]])
                full = e[150:240].clone()
                full = torch.cat([z, full[:, L[j]:]], dim=1)
                noise.append(full); rows.append(2 * j + 1); xbs.append(xb[k][j]); lj.append(L[j]); kls.append(kl)
        noise = torch.stack(noise)
        with torch.set_grad_enabled(grad):
            xh = ctx.hand(noise, rows, ck=grad)
        return xh, torch.stack(xbs), lj, kls

    hist = []
    for it in range(ITERS_II):
        if time.time() - t0 > CAP_S:
            raise Cap(f"cap reached during (ii) iteration {it}")
        opt.zero_grad()
        tot = 0.0
        for bs in range(0, G.J, BATCH_II_CLIPS):
            clips = list(range(bs, bs + BATCH_II_CLIPS))
            xh, xbs, lj, _ = batch_out(clips, (1, 2, 3, 4), True)
            s = surrogate(xbs, xh, lj)
            loss = -s.sum() / 4.0
            loss.backward()
            tot += float(s.sum()) / 4.0
        opt.step()
        hist.append(tot / G.J)
        if it % 5 == 0:
            print(f"[{time.time() - t0:6.0f}s] (ii) iter {it} train surrogate {hist[-1]:.3f}", flush=True)
    held, kls = np.zeros((G.J, 4)), []
    with torch.no_grad():
        for bs in range(0, G.J, BATCH_II_CLIPS * 2):
            clips = list(range(bs, min(G.J, bs + BATCH_II_CLIPS * 2)))
            xh, _, lj, kl = batch_out(clips, (5, 6, 7, 8), False)
            xn = xh.cpu().numpy()
            kls += kl
            for i, j in enumerate(clips):
                for q, k in enumerate((5, 6, 7, 8)):
                    held[j, q] = geo_coord(body_a0[k][j], xn[i * 4 + q], L[j])
    return {"heldout_per_clip_mean": held.mean(1).tolist(), "mean_heldout": float(np.mean(held)),
            "train_surrogate_history": hist, "kl_per_frame": {"mean": float(np.mean(kls)), "max": float(np.max(kls)),
                                                              "bound": 99.64}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out, dumps = Path(args.out), Path(args.dumps)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    ctx = G.Ctx()
    L = np.array(ctx.lengths)
    res = {"label": "E2c; released-checkpoint results, not a paper reproduction; no perceptual claim", "flags": ctx.flags()}
    try:
        comp, body_a0, hand_r = comparators(ctx, dumps)
        res["comparators"] = comp
        base_a0 = np.array([geo_coord(body_a0[1][j], hand_r[1][j], L[j]) for j in range(G.J)])
        res["A0_k1_raw_mean"] = float(base_a0.mean())
        print("comparators", {k: v for k, v in comp.items() if k != "per_clip"}, flush=True)
        res["i"] = part_i(ctx, body_a0, t0)
        res["ii"] = part_ii(ctx, body_a0, t0)
        lvl = {"primary": comp["primary_typical_only"], "secondary_all": comp["secondary_all_candidate_E2e"],
               "secondary_dev256": comp["secondary_dev256_dumps"]}
        short, long_ = L < 100, L >= 100
        for arm, val, per in (("i", res["i"]["mean_reported"], np.array(res["i"]["reported_per_clip"])),
                              ("ii", res["ii"]["mean_heldout"], np.array(res["ii"]["heldout_per_clip_mean"]))):
            res[arm]["reaches"] = {k: bool(val >= v) for k, v in lvl.items()}
            res[arm]["comparator_sensitive"] = len(set(res[arm]["reaches"].values())) > 1
            res[arm]["split_L"] = {"L<100": {"n": int(short.sum()), "mean": float(per[short].mean()),
                                             "primary_level": float(np.nanmean(np.array(comp["per_clip"]["typical_only"])[short]))},
                                   "L>=100": {"n": int(long_.sum()), "mean": float(per[long_].mean()),
                                              "primary_level": float(np.nanmean(np.array(comp["per_clip"]["typical_only"])[long_]))}}
        i_ok = res["i"]["reaches"]["primary"] and not res["i"]["inconclusive_feasibility"]
        ii_ok = res["ii"]["reaches"]["primary"]
        res["outcome_C-c6"] = ("at least one arm reaches the primary best-of-8x8 level" if (i_ok or ii_ok)
                               else ("N4 inconclusive (feasibility); (ii) below level" if res["i"]["inconclusive_feasibility"]
                                     else "registered negative outcome: neither reaches the best-of-8x8 level within the typicality/KL bound (FM4)"))
        res["status"] = "completed"
    except Cap as e:
        res["status"] = f"stopped: {e}"
    res["peak_reserved_GiB"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
    res["seconds"] = round(time.time() - t0)
    (out / "e2c_results.json").write_text(json.dumps(res, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)),
                                          encoding="utf-8")
    print(res.get("outcome_C-c6", res["status"]), res["seconds"], "s")


if __name__ == "__main__":
    main()
