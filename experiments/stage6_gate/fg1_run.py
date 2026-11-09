"""FG-1 fresh-noise controllability gate (research/stage6_proposal/MC_REDESIGN_PROPOSAL.md Â§5; final authorisation
2026-11-07). Per-clip fitting of initial-noise controllers on 16 TRAIN clips; paired fresh-noise held-out evaluation.

Phases (each a separate process, run in this order: prep, V2, V1, V3):
  prep  bodies x_b for the 16 fit + 16 held-out noises per clip (no grad), arm features, the V0 (uncoupled) hands
  V1    M-C BH family per clip (E2c (ii) family, imported unchanged from e2c_run.py: Stiefel U 90x60, V 60x60,
        kappa = min(0.95 sigmoid(a), 0.9), z_R = K eps_b + S xi_R); init seed 1000 + a; objective surrogate coord_ah^R
  V2    ACMS form per clip (acms_policy.ACMS unchanged; 433 parameters; right hand; mu from s_hat_R); init seed 8000 + a;
        objective surrogate coord_ah^R
  V3    SC-MC per clip [new direction, authorised]: two ACMS heads, eps_L = xi_L + mu_L(s_hat_L), eps_R = xi_R + mu_R(s_hat_R);
        866 parameters; init seeds 8000 + a (right), 8100 + a (left); objective sum of the surrogates of coord_ah^L,
        coord_ah^R, coord_lr
Fitting (all variants, E2c (ii) settings): Adam lr 0.05 (e2c_run.LR), 30 iterations (e2c_run.ITERS_II), full 16-noise
batch per iteration (gradient accumulated over passes of 8 hand rows), loss = -(1/16) sum over noises of the
surrogate, per clip. Surrogate = E2d chordal-speed correlation (e2c_run.surrogate construction); the registered
geodesic metric is logged every iteration. Held-out: 16 fresh noises per clip, common to all variants (paired);
outputs saved; the state-shuffle ablation (V2, V3: s_hat from held-out noise k+1 mod 16) is evaluated too.
Noise seeds: fit 60,000,000 + 1000 a + k, held-out 61,000,000 + 1000 a + k (a = gate clip 0..15, k = 1..16).
Operational caps (documented before running, research/stage6_gate/FG1_OPERATIONAL_DECISIONS.md): per variant 75 min
(V1, V2) / 120 min (V3); GPU reserved memory 14 GiB; abort on non-finite output or gradient; SignSparK checksum
checked; only TRAIN opened. Released checkpoints, not a paper reproduction.

  python -E -s experiments/stage6_gate/fg1_run.py --phase prep|V1|V2|V3
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in ("experiments/stage5", "experiments/stage4/e2c", "experiments/stage4"):
    sys.path.insert(0, str(ROOT / p))
import common5 as C  # noqa: E402
import acms_policy as P  # noqa: E402
import rewards as RW  # noqa: E402
import e2c_run as E  # noqa: E402  (registered E2c components, unchanged)

E2D = E.G.E2D
us = C.us
OUT = HERE / "out"
FIT_BASE, HO_BASE = 60_000_000, 61_000_000
K = 16
ITERS = E.ITERS_II
ROWS_PER_PASS = 8
CAP = {"V1": 75 * 60, "V2": 75 * 60, "V3": 120 * 60, "prep": 30 * 60}
MEM_CAP_GIB = 14.0
R_ARM, L_ARM = [7, 9], [6, 8]


class Abort(Exception):
    pass


def left_arm_feature(xb, L):
    """As common5.arm_feature, for the left arm (arm_signals(...)[1])."""
    out = np.zeros(xb.shape[1], np.float32)
    if not np.isfinite(xb[:, :L]).all():
        return out, False
    with np.errstate(invalid="ignore", divide="ignore"):
        s = C.MR.arm_signals(xb, L)[1]
    if not C.V.r_signal_valid(s):
        return out, False
    s = np.concatenate([s, s[-1:]])
    out[:L] = ((s - s.mean()) / s.std()).astype(np.float32)
    return out, True


def gen(ctx, prep, stream, rows, noise, grad):
    embed, cond = prep[stream]
    c, e = us.subset(cond, embed, rows)
    with torch.set_grad_enabled(grad):
        return us.unrolled_decode(ctx.m[stream], noise, c, e, n_steps=10, use_checkpoint=grad)


def surr(xa, xh, L, arm):
    """Chordal-speed corr per row; xa [n, 60|90, T] reference stream (body if arm else hand), xh [n, 90, T]."""
    sa = E2D.speeds(xa, arm) if arm is not None else E2D.speeds(xa, None)
    sh = E2D.speeds(xh, None)
    out = []
    for i in range(xh.shape[0]):
        m = torch.zeros(sa.shape[1], dtype=torch.bool, device=sa.device)
        m[: L[i] - 1] = True
        out.append(E2D.corr(sa[i], sh[i], m))
    return torch.stack(out)


def geo(xb, xl, xr, L):
    """Registered geodesic coordination statistics (space R v1)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        ar, al = C.MR.arm_signals(xb, L)
        hl, hr = C.MR.hand_stats(xl, L)["s"], C.MR.hand_stats(xr, L)["s"]
    return {"R": C.MR.corr(ar, hr), "L": C.MR.corr(al, hl), "LR": C.MR.corr(hl, hr)}


def load_ctx(gc):
    ctx = C.Ctx5({"train": gc["clips"]})
    assert ctx.n_trainable() == 0
    prep = ctx.batch("train", gc["clips"])
    return ctx, prep


def phase_prep(gc, t0):
    ctx, prep = load_ctx(gc)
    w0 = ctx.weight_checksum()
    n = len(gc["clips"])
    L = gc["lengths"]
    data = {}
    for tag, base in (("fit", FIT_BASE), ("ho", HO_BASE)):
        nz = torch.stack([torch.stack([C.noise(base, a, k) for k in range(1, K + 1)]) for a in range(n)])  # [n, K, 240, 304]
        xb = np.zeros((n, K, 60, C.SEQ), np.float32)
        xl = np.zeros((n, K, 90, C.SEQ), np.float32)
        xr = np.zeros((n, K, 90, C.SEQ), np.float32)
        for a in range(n):
            xb[a] = gen(ctx, prep, "body", [a] * K, nz[a, :, :60].cuda(), False).cpu().numpy()
            h = gen(ctx, prep, "hand", [2 * a] * K + [2 * a + 1] * K,
                    torch.cat([nz[a, :, 60:150], nz[a, :, 150:240]]).cuda(), False).cpu().numpy()
            xl[a], xr[a] = h[:K], h[K:]
        fR = np.zeros((n, K, C.SEQ), np.float32)
        fL = np.zeros((n, K, C.SEQ), np.float32)
        vR = np.zeros((n, K), bool)
        vL = np.zeros((n, K), bool)
        for a in range(n):
            for k in range(K):
                fR[a, k], vR[a, k] = C.arm_feature(xb[a, k], L[a])
                fL[a, k], vL[a, k] = left_arm_feature(xb[a, k], L[a])
        data.update({f"{tag}_noise": nz.numpy(), f"{tag}_xb": xb, f"{tag}_V0_xl": xl, f"{tag}_V0_xr": xr,
                     f"{tag}_sR": fR, f"{tag}_sL": fL, f"{tag}_sR_valid": vR, f"{tag}_sL_valid": vL})
        print(f"[{time.time() - t0:6.0f}s] prep {tag} done", flush=True)
    np.savez(OUT / "prep.npz", **data)
    return {"weights_unchanged": w0 == ctx.weight_checksum(), "flags": ctx.flags(), "opened_splits": list(C.OPENED_SPLITS),
            "arm_feature_invalid": {t: {"R": int((~data[f"{t}_sR_valid"]).sum()), "L": int((~data[f"{t}_sL_valid"]).sum())}
                                    for t in ("fit", "ho")}}


def make_params(v, n):
    if v == "V1":
        return {a: E.family_params(a) for a in range(n)}
    pols = {}
    for a in range(n):
        heads = {"R": P.ACMS(init_seed=8000 + a).cuda()}
        if v == "V3":
            heads["L"] = P.ACMS(init_seed=8100 + a).cuda()
        pols[a] = heads
    return pols


def param_list(v, prm):
    if v == "V1":
        return [p for a in prm for p in prm[a]]
    return [p for a in prm for h in prm[a].values() for p in h.parameters()]


def actions(v, prm, a, L, noise, sR, sL):
    """noise [m, 240, 304] cuda; sR, sL [m, 304] -> eps_L [m, 90, 304], eps_R [m, 90, 304], KL per frame {hand: [m]}."""
    xiL, xiR, eb = noise[:, 60:150], noise[:, 150:240], noise[:, :60]
    m = noise.shape[0]
    kl = {"L": torch.zeros(m, device=noise.device), "R": torch.zeros(m, device=noise.device)}
    if v == "V0":
        return xiL, xiR, kl
    if v == "V1":
        zs, kls = [], []
        for i in range(m):
            z, k_ = E.coupled(prm[a], eb[i, :, :L], xiR[i, :, :L])
            zs.append(torch.cat([z, xiR[i, :, L:]], dim=1))
            kls.append(k_)
        kl["R"] = torch.tensor(kls, device=noise.device)
        return xiL, torch.stack(zs), kl
    muR = prm[a]["R"].mu(sR, [L] * m)
    kl["R"] = P.ACMS.kl_per_frame(muR, [L] * m)
    epsL = xiL
    if v == "V3":
        muL = prm[a]["L"].mu(sL, [L] * m)
        kl["L"] = P.ACMS.kl_per_frame(muL, [L] * m)
        epsL = xiL + muL
    return epsL, xiR + muR, kl


def objective(v, xb, xl, xr, Ls):
    s = surr(xb, xr, Ls, R_ARM)
    if v == "V3":
        s = s + surr(xb, xl, Ls, L_ARM) + surr(xl, xr, Ls, None)
    return s


def phase_fit(v, gc, t0):
    ctx, prep = load_ctx(gc)
    w0 = ctx.weight_checksum()
    D = np.load(OUT / "prep.npz")
    n, L = len(gc["clips"]), gc["lengths"]
    prm = make_params(v, n)
    params = param_list(v, prm)
    n_params_per_clip = sum(p.numel() for p in param_list(v, {0: prm[0]}))
    opt = torch.optim.Adam(params, lr=E.LR)
    two = v == "V3"
    ctx_per_pass = ROWS_PER_PASS // (2 if two else 1)
    hist = {"surrogate": np.full((ITERS, n), np.nan), "geo_R": np.full((ITERS, n, K), np.nan),
            "geo_L": np.full((ITERS, n, K), np.nan), "geo_LR": np.full((ITERS, n, K), np.nan),
            "kl_R": np.full((ITERS, n), np.nan), "kl_L": np.full((ITERS, n), np.nan)}
    gnorm = []
    for it in range(ITERS):
        opt.zero_grad()
        for a in range(n):
            for k0 in range(0, K, ctx_per_pass):
                if time.time() - t0 > CAP[v]:
                    raise Abort(f"operational cap {CAP[v]} s reached at iteration {it}, clip {a}")
                ks = list(range(k0, min(K, k0 + ctx_per_pass)))
                noise = torch.as_tensor(D["fit_noise"][a, ks]).cuda()
                sR = torch.as_tensor(D["fit_sR"][a, ks]).cuda()
                sL = torch.as_tensor(D["fit_sL"][a, ks]).cuda()
                xb = torch.as_tensor(D["fit_xb"][a, ks]).cuda()
                epsL, epsR, kl = actions(v, prm, a, L[a], noise, sR, sL)
                m = len(ks)
                if two:
                    h = gen(ctx, prep, "hand", [2 * a] * m + [2 * a + 1] * m, torch.cat([epsL, epsR]), True)
                    xl, xr = h[:m], h[m:]
                else:
                    xr = gen(ctx, prep, "hand", [2 * a + 1] * m, epsR, True)
                    xl = torch.as_tensor(D["fit_V0_xl"][a, ks]).cuda()
                s = objective(v, xb, xl, xr, [L[a]] * m)
                (-s.sum() / K).backward()
                xln, xrn = xl.detach().cpu().numpy(), xr.detach().cpu().numpy()
                if not (np.isfinite(xrn).all() and np.isfinite(xln).all()):
                    raise Abort(f"non-finite output at iteration {it}, clip {a}")
                for i, k in enumerate(ks):
                    g = geo(D["fit_xb"][a, k], xln[i], xrn[i], L[a])
                    hist["geo_R"][it, a, k], hist["geo_L"][it, a, k], hist["geo_LR"][it, a, k] = g["R"], g["L"], g["LR"]
                hist["surrogate"][it, a] = np.nansum([hist["surrogate"][it, a], float(s.detach().sum()) / K])
                hist["kl_R"][it, a] = float(kl["R"].max())
                hist["kl_L"][it, a] = float(kl["L"].max())
                if torch.cuda.max_memory_reserved() / 2**30 > MEM_CAP_GIB:
                    raise Abort(f"GPU reserved memory above {MEM_CAP_GIB} GiB at iteration {it}")
        if not all(torch.isfinite(p.grad).all() for p in params if p.grad is not None):
            raise Abort(f"non-finite gradient at iteration {it}")
        gnorm.append(float(torch.sqrt(sum((p.grad ** 2).sum() for p in params if p.grad is not None))))
        opt.step()
        print(f"[{time.time() - t0:6.0f}s] {v} iter {it} surrogate {np.nanmean(hist['surrogate'][it]):.4f} geo_R "
              f"{np.nanmean(hist['geo_R'][it]):.4f} geo_L {np.nanmean(hist['geo_L'][it]):.4f} geo_LR "
              f"{np.nanmean(hist['geo_LR'][it]):.4f} KL_R {np.nanmax(hist['kl_R'][it]):.3f} "
              f"peak {torch.cuda.max_memory_reserved() / 2**30:.2f} GiB", flush=True)
    # held-out (fresh noise, paired with V0) + state-shuffle ablation
    res_out = {}
    shuffles = (False, True) if v in ("V2", "V3") else (False,)
    for shuffle in shuffles:
        xl_all = np.zeros((n, K, 90, C.SEQ), np.float32)
        xr_all = np.zeros((n, K, 90, C.SEQ), np.float32)
        klR, klL = np.zeros((n, K)), np.zeros((n, K))
        epsR_all = np.zeros((n, K, 90, C.SEQ), np.float32)
        epsL_all = np.zeros((n, K, 90, C.SEQ), np.float32)
        with torch.no_grad():
            for a in range(n):
                perm = [(k + 1) % K for k in range(K)] if shuffle else list(range(K))
                noise = torch.as_tensor(D["ho_noise"][a]).cuda()
                sR = torch.as_tensor(D["ho_sR"][a, perm]).cuda()
                sL = torch.as_tensor(D["ho_sL"][a, perm]).cuda()
                epsL, epsR, kl = actions(v, prm, a, L[a], noise, sR, sL)
                if two:
                    h = gen(ctx, prep, "hand", [2 * a] * K + [2 * a + 1] * K, torch.cat([epsL, epsR]), False)
                    xl_all[a], xr_all[a] = h[:K].cpu().numpy(), h[K:].cpu().numpy()
                else:
                    xr_all[a] = gen(ctx, prep, "hand", [2 * a + 1] * K, epsR, False).cpu().numpy()
                    xl_all[a] = D["ho_V0_xl"][a]
                klR[a], klL[a] = kl["R"].cpu().numpy(), kl["L"].cpu().numpy()
                epsR_all[a], epsL_all[a] = epsR.cpu().numpy(), epsL.cpu().numpy()
        tag = "shuffle" if shuffle else "heldout"
        np.savez(OUT / f"{v}_{tag}.npz", xl=xl_all, xr=xr_all, kl_R=klR, kl_L=klL, eps_R=epsR_all, eps_L=epsL_all)
        res_out[tag] = {"kl_R_max": float(klR.max()), "kl_L_max": float(klL.max())}
    if v == "V1":
        state = {f"{a}_{i}": t.detach().cpu() for a in prm for i, t in enumerate(prm[a])}
    else:
        state = {f"{a}_{h}": {kk: vv.detach().cpu() for kk, vv in prm[a][h].state_dict().items()} for a in prm for h in prm[a]}
    torch.save(state, OUT / f"{v}_params.pt")
    np.savez(OUT / f"{v}_fit_history.npz", **hist, grad_norm=np.array(gnorm))
    return {"params_per_clip": int(n_params_per_clip), "weights_unchanged": w0 == ctx.weight_checksum(),
            "flags": ctx.flags(), "opened_splits": list(C.OPENED_SPLITS), "outputs": res_out,
            "final_train_geo_R": float(np.nanmean(hist["geo_R"][-1])), "grad_norm_last": gnorm[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["prep", "V1", "V2", "V3"])
    ap.add_argument("--test", action="store_true", help="smoke test: 2 clips, 4 noises, 2 iterations, out_test/")
    a = ap.parse_args()
    global OUT, K, ITERS
    gc = json.loads((OUT / "gate_clips.json").read_text(encoding="utf-8"))
    if a.test:
        OUT, K, ITERS = HERE / "out_test", 4, 2
        gc = {k: (v[:2] if isinstance(v, list) else v) for k, v in gc.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    rec = {"phase": a.phase, "command": " ".join([sys.executable] + sys.argv), "start": time.strftime("%Y-%m-%d %H:%M:%S"),
           "lr": E.LR, "iterations": ITERS, "noises_fit": K, "noises_heldout": K, "rows_per_pass": ROWS_PER_PASS,
           "cap_seconds": CAP[a.phase], "mem_cap_GiB": MEM_CAP_GIB}
    try:
        rec.update(phase_prep(gc, t0) if a.phase == "prep" else phase_fit(a.phase, gc, t0))
        rec["status"] = "completed"
    except Abort as e:
        rec["status"] = f"aborted: {e}"
    rec.update({"seconds": round(time.time() - t0, 1), "gpu_peak_alloc_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                "gpu_peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3)})
    (OUT / f"run_{a.phase}.json").write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    print(rec["status"], rec["seconds"], "s", flush=True)


if __name__ == "__main__":
    main()
