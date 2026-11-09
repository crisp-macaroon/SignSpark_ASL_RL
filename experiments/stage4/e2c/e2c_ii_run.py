"""E2c (ii) only: per-clip optimisation of the M-C Gaussian-family parameters (C-c1, C-c2, C-c4, C-c5, C-c6).

User authorisation 2026-11-04: run (ii) only; (i) is NOT run. The registered implementation `e2c_run.py` is left
unchanged and imported for every registered component (comparators, family init, Stiefel/QR, coupled noise, kappa
clamp, surrogate, geodesic metric, lr, iterations, cap). The four approved deviations from `e2c_run.py`:
  1. part (i) is skipped; the C-c6 verdict uses the mean held-out (ii) coordination only;
  2. B = 8 contexts per pass (2 clips x 4 noises) as registered in C-c5, instead of 16 (4 clips x 4 noises);
     the per-clip objective, its scaling and the single Adam step per iteration are unchanged;
  3. per-clip logging (training objective per iteration, KL, kappa, family parameters, checks) -- logging only;
  4. "best training objective" = best per-iteration geodesic training objective (mean over k = 1..4); no feasibility
     rule beyond the registered kappa <= 0.9 clamp is introduced (checks are recorded, not enforced).
Model weights frozen (requires_grad = False; eval()); Adam acts only on U, V, a. Released checkpoints, not a paper
reproduction. Noise allocation: training A0 k = 1..4, held-out A0 k = 5..8 only.

    python -E -s experiments/stage4/e2c/e2c_ii_run.py --dumps experiments/stage4/e2e/dumps --out experiments/stage4/e2c/out_ii
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import e2c_run as E  # noqa: E402  (registered implementation, unchanged)

G = E.G
CLIPS_PER_PASS = 2  # x 4 noises = B = 8 contexts per pass (C-c5)
TRAIN_K, HELD_K = (1, 2, 3, 4), (5, 6, 7, 8)
KL_HAND_BOUND, KL_BOUND = 49.82, 99.64


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def kappa_of(P):
    return torch.clamp(0.95 * torch.sigmoid(P[2]), max=0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out, dumps = Path(args.out).resolve(), Path(args.dumps).resolve()
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()

    inputs = {str(p.relative_to(G.ROOT)): sha(p) for p in
              [G.ROOT / f"models/SignSparK/{s}/ema_0.9999_200000.pt" for s in ("body", "hand")]
              + [dumps / "A0" / f"k{k:02d}.npz" for k in range(1, 9)] + list(E.DEV256.values())
              + [HERE / "e2c_run.py", HERE / "e2c_ii_run.py", HERE / "typicality.py", HERE.parent / "gpu_common.py",
                 HERE.parent / "e2e" / "metrics.py", HERE.parent / "e2d" / "unrolled_sampler.py"]}
    print("hashed inputs", f"{time.time() - t0:.0f}s", flush=True)

    ctx = G.Ctx()
    L = np.array(ctx.lengths)
    n_model_trainable = sum(p.requires_grad for s in ctx.m for p in ctx.m[s].parameters())
    assert n_model_trainable == 0, "model weights must be frozen"
    w0 = {s: sum(float(p.double().sum()) for p in ctx.m[s].parameters()) for s in ctx.m}
    repro = {"label": "E2c (ii); released-checkpoint result, not a paper reproduction; no perceptual claim",
             "command": " ".join([sys.executable] + sys.argv), "flags": ctx.flags(), "input_sha256": inputs,
             "seeds": {"noise": "E2e registered base_noise('A0', j, k); train k=1..4, held-out k=5..8",
                       "family_init": "torch.Generator seed 1000 + j (U 90x60, V 60x60), a s.t. kappa = 0.1"},
             "model_trainable_params": n_model_trainable, "clips": [str(n) for n in ctx.names], "lengths": L.tolist()}
    res = {"label": repro["label"], "deviations_from_e2c_run": __doc__.split("Model weights")[0].strip()}
    status = "completed"
    try:
        comp, body_a0, hand_r = E.comparators(ctx, dumps)
        print("comparators", {k: v for k, v in comp.items() if k != "per_clip"}, f"{time.time() - t0:.0f}s", flush=True)
        uncoupled = {k: np.array([E.geo_coord(body_a0[k][j], hand_r[k][j], L[j]) for j in range(G.J)]) for k in range(1, 9)}

        P = {j: E.family_params(j) for j in range(G.J)}
        opt = torch.optim.Adam([p for j in P for p in P[j]], lr=E.LR)
        eps = {(j, k): G.noise("A0", j, k).cuda() for j in range(G.J) for k in range(1, 9)}
        xb = {k: torch.as_tensor(np.stack([body_a0[k][j] for j in range(G.J)])).cuda() for k in range(1, 9)}

        def batch_out(clips, ks, grad):
            noise, xbs, lj, rows, kls = [], [], [], [], []
            for j in clips:
                for k in ks:
                    e = eps[(j, k)]
                    z, kl = E.coupled(P[j], e[:60, : L[j]], e[150:240, : L[j]])
                    noise.append(torch.cat([z, e[150:240][:, L[j]:]], dim=1))
                    rows.append(2 * j + 1); xbs.append(xb[k][j]); lj.append(L[j]); kls.append(kl)
            with torch.set_grad_enabled(grad):
                xh = ctx.hand(torch.stack(noise), rows, ck=grad)
            return xh, torch.stack(xbs), lj, kls

        train_geo = np.full((E.ITERS_II, G.J, 4), np.nan)
        surr_hist = np.full((E.ITERS_II, G.J), np.nan)
        kl_hist = np.full((E.ITERS_II, G.J), np.nan)
        nonfinite = {j: 0 for j in range(G.J)}
        for it in range(E.ITERS_II):
            if time.time() - t0 > E.CAP_S:
                raise E.Cap(f"cap reached during (ii) iteration {it}")
            opt.zero_grad()
            for bs in range(0, G.J, CLIPS_PER_PASS):
                clips = list(range(bs, bs + CLIPS_PER_PASS))
                xh, xbs, lj, kls = batch_out(clips, TRAIN_K, True)
                s = E.surrogate(xbs, xh, lj)
                (-s.sum() / 4.0).backward()
                xn = xh.detach().cpu().numpy()
                for i, j in enumerate(clips):
                    kl_hist[it, j] = kls[i * 4]
                    surr_hist[it, j] = float(s[i * 4: i * 4 + 4].mean())
                    nonfinite[j] += int(not np.isfinite(xn[i * 4: i * 4 + 4]).all())
                    for q, k in enumerate(TRAIN_K):
                        train_geo[it, j, q] = E.geo_coord(body_a0[k][j], xn[i * 4 + q], L[j])
            grads_finite = all(torch.isfinite(p.grad).all() for j in P for p in P[j])
            if not grads_finite:
                raise RuntimeError(f"non-finite gradient at iteration {it}")
            opt.step()
            if it % 5 == 0 or it == E.ITERS_II - 1:
                print(f"[{time.time() - t0:6.0f}s] (ii) iter {it} train surrogate {np.nanmean(surr_hist[it]):.4f} "
                      f"train geodesic {np.nanmean(train_geo[it]):.4f} peak {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB",
                      flush=True)

        held, kl_final = np.zeros((G.J, 4)), np.zeros(G.J)
        with torch.no_grad():
            for bs in range(0, G.J, CLIPS_PER_PASS):
                clips = list(range(bs, bs + CLIPS_PER_PASS))
                xh, _, lj, kl = batch_out(clips, HELD_K, False)
                xn = xh.cpu().numpy()
                for i, j in enumerate(clips):
                    kl_final[j] = kl[i * 4]
                    nonfinite[j] += int(not np.isfinite(xn[i * 4: i * 4 + 4]).all())
                    for q, k in enumerate(HELD_K):
                        held[j, q] = E.geo_coord(body_a0[k][j], xn[i * 4 + q], L[j])
        print(f"[{time.time() - t0:6.0f}s] held-out mean {held.mean():.4f}", flush=True)

        # weights unchanged
        w1 = {s: sum(float(p.double().sum()) for p in ctx.m[s].parameters()) for s in ctx.m}
        repro["model_weight_checksum_unchanged"] = all(w0[s] == w1[s] for s in w0)

        # ---- per clip
        prim = np.array(comp["per_clip"]["typical_only"], float)
        per_clip, fam = [], {}
        train_mean = np.nanmean(train_geo, axis=2)  # [it, j]
        for j in range(G.J):
            with torch.no_grad():
                U, V = E.stiefel(P[j][0]), E.stiefel(P[j][1])
                kap = kappa_of(P[j]).cpu().numpy().astype(float)
                orth = max(float((U.T @ U - torch.eye(60, device=U.device)).abs().max()),
                           float((V.T @ V - torch.eye(60, device=V.device)).abs().max()))
            fam[f"U_{j}"], fam[f"V_{j}"], fam[f"kappa_{j}"] = U.cpu().numpy(), V.cpu().numpy(), kap
            bi = int(np.nanargmax(train_mean[:, j]))
            per_clip.append({
                "clip": j, "name": str(ctx.names[j]), "L": int(L[j]),
                "initial_train_objective": float(train_mean[0, j]),
                "best_train_objective": float(train_mean[bi, j]), "best_train_iteration": bi,
                "final_train_objective_iter29": float(train_mean[-1, j]),
                "heldout_mean": float(held[j].mean()), "heldout_per_noise": held[j].tolist(),
                "uncoupled_A0_train_mean": float(np.mean([uncoupled[k][j] for k in TRAIN_K])),
                "uncoupled_A0_heldout_mean": float(np.mean([uncoupled[k][j] for k in HELD_K])),
                "kl_per_frame_final": float(kl_final[j]), "kl_per_frame_max_over_iters": float(np.nanmax(kl_hist[:, j])),
                "kappa": {"mean": float(kap.mean()), "max": float(kap.max()), "min": float(kap.min()),
                          "n_at_clamp_0.9": int((kap >= 0.9 - 1e-7).sum()), "n_ge_0.5": int((kap >= 0.5).sum())},
                "checks": {"kl_le_49.82_hand": bool(np.nanmax(kl_hist[:, j]) <= KL_HAND_BOUND and kl_final[j] <= KL_HAND_BOUND),
                           "kl_le_99.64": bool(kl_final[j] <= KL_BOUND), "kappa_le_0.9": bool(kap.max() <= 0.9 + 1e-7),
                           "stiefel_orth_err": orth, "nonfinite_output_batches": nonfinite[j]},
                "feasible": bool(kl_final[j] <= KL_HAND_BOUND and kap.max() <= 0.9 + 1e-7 and nonfinite[j] == 0),
                "primary_level_clip": None if not np.isfinite(prim[j]) else float(prim[j]),
                "reaches_primary_clip": None if not np.isfinite(prim[j]) else bool(held[j].mean() >= prim[j]),
                "reaches_all_candidate_clip": bool(held[j].mean() >= comp["per_clip"]["all_candidate"][j]),
                "reaches_dev256_clip": bool(held[j].mean() >= comp["per_clip"]["dev256"][j]),
                "train_objective_history": train_mean[:, j].tolist(), "surrogate_history": surr_hist[:, j].tolist()})
        np.savez(out / "e2c_ii_family_params.npz", **fam)
        (out / "e2c_ii_per_clip.json").write_text(json.dumps(per_clip, indent=1), encoding="utf-8")

        # ---- aggregate
        hm = held.mean(1)
        lvl = {"primary": comp["primary_typical_only"], "secondary_all": comp["secondary_all_candidate_E2e"],
               "secondary_dev256": comp["secondary_dev256_dumps"]}
        reaches = {k: bool(hm.mean() >= v) for k, v in lvl.items()}
        short, long_ = L < 100, L >= 100
        unc_h = np.array([c["uncoupled_A0_heldout_mean"] for c in per_clip])
        agg = {
            "label": repro["label"], "n_clips": G.J, "comparators": {k: v for k, v in comp.items() if k != "per_clip"},
            "comparators_per_clip": comp["per_clip"],
            "mean_heldout": G.boot_mean_ci(hm), "mean_initial_train": G.boot_mean_ci(train_mean[0]),
            "mean_best_train": G.boot_mean_ci(np.nanmax(train_mean, 0)),
            "mean_uncoupled_A0_heldout": G.boot_mean_ci(unc_h),
            "gain_heldout_vs_uncoupled": G.boot_mean_ci(hm - unc_h),
            "diff_heldout_minus_primary_clipwise": G.boot_mean_ci(hm - prim),
            "train_minus_heldout_best": G.boot_mean_ci(np.nanmax(train_mean, 0) - hm),
            "train_objective_mean_by_iteration": np.nanmean(train_mean, 1).tolist(),
            "surrogate_mean_by_iteration": np.nanmean(surr_hist, 1).tolist(),
            "heldout_quantiles": {q: float(np.percentile(hm, q)) for q in (0, 10, 25, 50, 75, 90, 100)},
            "kl_per_frame": {"mean": float(kl_final.mean()), "max": float(kl_final.max()), "bound_hand": KL_HAND_BOUND, "bound": KL_BOUND},
            "kappa_mean_over_clips": float(np.mean([c["kappa"]["mean"] for c in per_clip])),
            "kappa_at_clamp_total": int(sum(c["kappa"]["n_at_clamp_0.9"] for c in per_clip)),
            "all_feasible": all(c["feasible"] for c in per_clip),
            "clips_reaching_primary_clipwise": int(sum(bool(c["reaches_primary_clip"]) for c in per_clip)),
            "clips_with_primary_level": int(np.isfinite(prim).sum()),
            "reaches_C-c6": reaches, "comparator_sensitive": len(set(reaches.values())) > 1,
            "split_L": {"L<100": {"n": int(short.sum()), "mean_heldout": float(hm[short].mean()), "primary_level": float(np.nanmean(prim[short]))},
                        "L>=100": {"n": int(long_.sum()), "mean_heldout": float(hm[long_].mean()), "primary_level": float(np.nanmean(prim[long_]))}},
        }
        agg["outcome_C-c6_ii"] = ("(ii) reaches the primary typical-only best-of-8x8 level" if reaches["primary"] else
                                  "(ii) does not reach the primary best-of-8x8 level within the KL bound: registered negative "
                                  "outcome for (ii) (FM4; (i) not run by user decision)")
        if agg["comparator_sensitive"]:
            agg["outcome_C-c6_ii"] += "; comparator-sensitive (primary and secondary verdicts differ)"
        res["aggregate"] = agg
        (out / "e2c_ii_aggregate.json").write_text(json.dumps(agg, indent=1), encoding="utf-8")
    except E.Cap as e:
        status = f"stopped: {e}"
    except Exception as e:  # recorded, then re-raised
        status = f"error: {type(e).__name__}: {e}"
        repro["status"] = status
        (out / "e2c_ii_repro.json").write_text(json.dumps(repro, indent=1), encoding="utf-8")
        raise
    repro.update({"status": status, "seconds": round(time.time() - t0),
                  "peak_allocated_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                  "peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3)})
    (out / "e2c_ii_repro.json").write_text(json.dumps(repro, indent=1), encoding="utf-8")
    print(res.get("aggregate", {}).get("outcome_C-c6_ii", status), repro["seconds"], "s", flush=True)


if __name__ == "__main__":
    main()
