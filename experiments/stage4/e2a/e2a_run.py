"""E2a: gradient agreement and K selection (Stage 4 rev. 4.0 §15.2 l. 950, §5.4; pre-registrations C-a1..C-a5).

C-a1  32 E2e clips; A0 noise k = 1 (E2e seeds; CRN)
C-a2  scalar r = target-free rotation-space coordination: corr(R-arm, R-hand) + corr(L-hand, R-hand) (chordal speeds;
      E2d statistic)
C-a3  per clip: speed-profile correlation of G_K vs G_10 hand outputs (geodesic speeds), and gradient cosine of
      d r / d eps_hand (K vs 10) over the clip's two hand rows and active frames; mean and min over clips
C-a4  descriptive only: K_train stays 10 whatever the agreement (K < 10 optimises a different sampler, §5.4 (b))
C-a5  bf16 arm not run
Registered stops: non-finite gradients; max/min per-Euler-step gradient-norm ratio > 1e3 (K = 10). Cap 1 h.
Body is generated with the same K (no grad: z_b = eps_b does not depend on the controller). Gradient w.r.t. the hand
noise only. No optimiser, no parameter update. Noise floor: two independent K = 10 backward passes (backward kernels
are not bitwise deterministic, E2d).

    python -E -s experiments/stage4/e2a/e2a_run.py --out experiments/stage4/e2a/out
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

KS = (1, 2, 4, 10)
BATCH = 8
CAP_S = 3600


def run(ctx, K, clips, need_states=False):
    L = [ctx.lengths[j] for j in clips]
    eps = torch.stack([G.noise("A0", j, 1) for j in clips]).cuda()
    with torch.no_grad():
        xb = ctx.body(eps[:, :60], clips, n_steps=K)
    rows = [r for j in clips for r in (2 * j, 2 * j + 1)]
    eh = torch.stack([eps[:, 60:150], eps[:, 150:]], 1).reshape(2 * len(clips), 90, 304).clone().requires_grad_(True)
    xh, states = ctx.hand(eh, rows, n_steps=K, ck=True, keep_states=True)
    if need_states:
        for s in states:
            s.retain_grad()
    r = G.E2D.statistic(xb, xh, torch.tensor(L))
    r.backward()
    torch.cuda.synchronize()
    out = {"r": float(r), "grad": eh.grad.detach().cpu().numpy(), "xh": xh.detach().cpu().numpy(), "L": L,
           "finite": bool(torch.isfinite(eh.grad).all())}
    if need_states:
        out["state_norms"] = [float(s.grad.norm()) if s.grad is not None else None for s in states]
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
    res = {"label": "E2a; released-checkpoint results, not a paper reproduction", "flags": ctx.flags(), "per_K": {},
           "stop": None, "batches": []}
    per_clip = {K: {"speed_corr": [], "grad_cos": []} for K in KS}
    noise_floor = []
    try:
        for bstart in range(0, G.J, BATCH):
            clips = list(range(bstart, bstart + BATCH))
            ref = run(ctx, 10, clips, need_states=True)
            ref2 = run(ctx, 10, clips)  # backward noise floor
            if not (ref["finite"] and ref2["finite"]):
                raise RuntimeError("non-finite gradients at K = 10")
            norms = [v for v in ref["state_norms"] if v is not None]
            ratio = max(norms) / max(min(norms), 1e-30)
            res["batches"].append({"clips": clips, "state_grad_norms_x0_to_x10": ref["state_norms"], "ratio": ratio})
            if not np.all(np.isfinite(norms)):
                raise RuntimeError("non-finite per-step gradient norms")
            if ratio > 1e3:
                raise RuntimeError(f"per-step gradient-norm ratio {ratio:.3g} > 1e3")
            for K in KS:
                o = ref if K == 10 else run(ctx, K, clips)
                if not o["finite"]:
                    raise RuntimeError(f"non-finite gradients at K = {K}")
                for i, j in enumerate(clips):
                    L = ref["L"][i]
                    sc = []
                    for h in (2 * i, 2 * i + 1):
                        sc.append(G.MR.corr(G.hand_speed(o["xh"][h], L), G.hand_speed(ref["xh"][h], L)))
                    gk = o["grad"][2 * i:2 * i + 2, :, :L].ravel()
                    g10 = (ref2 if K == 10 else ref)["grad"][2 * i:2 * i + 2, :, :L].ravel()
                    cos = float(gk @ g10 / (np.linalg.norm(gk) * np.linalg.norm(g10) + 1e-30))
                    per_clip[K]["speed_corr"].append(float(np.nanmean(sc)))
                    per_clip[K]["grad_cos"].append(cos)
                    if K == 10:
                        noise_floor.append(cos)
            print(f"[{time.time() - t0:5.0f}s] batch {bstart // BATCH + 1}/4 ratio {ratio:.2f}", flush=True)
            if time.time() - t0 > CAP_S:
                raise RuntimeError("1 h cap reached")
        for K in KS:
            sc, gc = np.array(per_clip[K]["speed_corr"]), np.array(per_clip[K]["grad_cos"])
            res["per_K"][K] = {"speed_profile_corr_vs_K10": {"mean": float(np.nanmean(sc)), "min": float(np.nanmin(sc))},
                               "grad_cosine_vs_K10": {"mean": float(np.mean(gc)), "min": float(np.min(gc))},
                               "meets_0.99_and_0.95_descriptive": bool(np.nanmin(sc) >= 0.99 and np.min(gc) >= 0.95)}
        res["K10_vs_K10_backward_noise_floor_cosine"] = {"mean": float(np.mean(noise_floor)), "min": float(np.min(noise_floor))}
        res["max_step_norm_ratio"] = max(b["ratio"] for b in res["batches"])
        res["K_train"] = 10
        res["K_train_note"] = "C-a4: descriptive; K_train stays 10 regardless of agreement"
        res["status"] = "completed"
    except RuntimeError as e:
        res["status"] = f"stopped: {e}"
        res["stop"] = str(e)
    res["peak_reserved_GiB"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
    res["seconds"] = round(time.time() - t0)
    (out / "e2a_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(res["status"], res["seconds"], "s")


if __name__ == "__main__":
    main()
