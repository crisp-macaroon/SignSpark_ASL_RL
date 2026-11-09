"""Stage 4 E2d: sampler equivalence, numerical flags, M-CLIP hash sharing, memory/time of one M-C
gradient pass, per-Euler-step input-gradient norms. Rev. 4.0 checklist Step 1.

Released checkpoints, read-only; no optimiser, no parameter update, no training. Dev clips 0..31
of the dev-256 subset (GF regime: no keyframes, reference length), released-checkpoint results,
not a paper reproduction.

    python -E -s experiments/stage4/e2d/e2d_run.py --out experiments/stage4/e2d/out --phase all
"""

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unrolled_sampler as us  # noqa: E402

ROOT = us.ROOT
SEED = 20261103  # E2d noise seed (recorded); body = SEED, hand = SEED + 1
T0_TOL = 1e-4
GATE_GIB = 14.0
B_LIST = (1, 2, 4, 8)


def flags():
    return {"torch": torch.__version__, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
            "device": torch.cuda.get_device_name(0), "python": platform.python_version(),
            "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "dtype": "float32"}


def noise_for(shape, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(shape, generator=g).cuda()


def training_flags(model):
    return sorted({m.training for m in model.modules()})


def phase_hash(out):
    """E2d-H: SHA-256 over the M-CLIP sub-weights (text_enc_model.*) of each checkpoint, read-only."""
    res = {}
    for s in ("body", "hand", "face"):
        sd = torch.load(ROOT / f"models/SignSparK/{s}/ema_0.9999_200000.pt", map_location="cpu", weights_only=True)
        keys = sorted(k for k in sd if k.startswith("text_enc_model."))
        h = hashlib.sha256()
        n = 0
        for k in keys:
            t = sd[k].contiguous()
            h.update(k.encode())
            h.update(str(tuple(t.shape)).encode() + str(t.dtype).encode())
            h.update(t.numpy().tobytes())
            n += t.numel()
        res[s] = {"n_tensors": len(keys), "n_params": n, "sha256": h.hexdigest()}
        del sd
        print(s, res[s], flush=True)
    res["identical_all_three"] = len({v["sha256"] for v in res.values() if isinstance(v, dict)}) == 1
    (out / "mclip_hash.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def phase_t0(out):
    """T0a (harness vs upstream decode), T0b (determinism), T0c (checkpoint vs not), E2d-F (flags)."""
    res = {"flags": flags(), "streams": {}}
    for s, seed in (("body", SEED), ("hand", SEED + 1)):
        cfg = us.build_cfg(s)
        model, flow = us.load_model(s, cfg)
        embed, cond = us.load_first_batch(s, cfg)
        names = cond["y"]["video_names"]
        noise = noise_for(embed.shape, seed)
        r = {"batch_shape": list(embed.shape), "noise_seed": seed, "video_names": names,
             "lengths": [int(v) for v in cond["y"]["lengths"]]}

        torch.cuda.synchronize(); t0 = time.time()
        with torch.no_grad():
            up, nfe = flow.decode(model, noise=noise, keyframe_mask=cond["obs_mask"], x_embed=embed,
                                  model_kwargs=cond, ode_package="torchdiffeq", ode_stepnum=10)
        torch.cuda.synchronize(); r["upstream_s"] = round(time.time() - t0, 2); r["upstream_nfe"] = int(nfe)
        r["training_flags_upstream"] = training_flags(model)

        emb, original = us.cache_text(model, cond["y"]["text"])
        r["text_emb_shape"] = list(emb.shape)
        with torch.no_grad():
            torch.cuda.synchronize(); t0 = time.time()
            h1 = us.unrolled_decode(model, noise, cond, embed)
            torch.cuda.synchronize(); r["harness_s"] = round(time.time() - t0, 2)
            h2 = us.unrolled_decode(model, noise, cond, embed)
        act = cond["y"]["mask"].bool().expand_as(up)  # [B,1,T] length mask -> active frames
        d = (up - h1).abs()
        r["T0a_max_abs_all"] = float(d.max())
        r["T0a_max_abs_active"] = float(d[act].max())
        r["T0a_pass"] = r["T0a_max_abs_all"] <= T0_TOL
        r["T0b_max_abs"] = float((h1 - h2).abs().max())
        r["T0b_pass"] = r["T0b_max_abs"] == 0.0

        # T0c: 4 clips (hand: 2 clips x 2 sides), grad mode with a scale leaf so checkpointing engages
        idx = list(range(4))
        c4, e4 = us.subset(cond, embed, idx)
        model.encode_text = original
        us.cache_text(model, c4["y"]["text"])
        outs, grads = [], []
        for ck in (False, True):
            sc = torch.ones(1, device="cuda", requires_grad=True)
            x = us.unrolled_decode(model, noise[idx] * sc, c4, e4, use_checkpoint=ck)
            x.pow(2).mean().backward()
            outs.append(x.detach()); grads.append(sc.grad.detach())
        r["T0c_max_abs_out"] = float((outs[0] - outs[1]).abs().max())
        r["T0c_pass"] = r["T0c_max_abs_out"] == 0.0
        r["T0c_grad_noCk_vs_Ck"] = [float(grads[0]), float(grads[1])]
        r["training_flags_harness"] = training_flags(model)
        r["F_pass"] = r["training_flags_harness"] == [False] and r["training_flags_upstream"] == [False]
        np.savez_compressed(out / f"t0_{s}.npz", upstream=up.cpu().numpy(), harness=h1.cpu().numpy(),
                            noise=noise.cpu().numpy())
        res["streams"][s] = r
        print(s, {k: v for k, v in r.items() if k != "video_names"}, flush=True)
        del model, flow
        torch.cuda.empty_cache()
    res["T0_pass"] = all(v["T0a_pass"] and v["T0b_pass"] and v["T0c_pass"] and v["F_pass"]
                         for v in res["streams"].values())
    (out / "t0.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def speeds(x6, chunk):
    """Differentiable per-frame joint speed proxy: chordal ||R_{t+1} - R_t||_F (= 2*sqrt(2)*sin(theta/2)),
    mean over joints. x6: [N, C, T] 6D rotations -> [N, T-1]."""
    n, c, t = x6.shape
    d = x6.permute(0, 2, 1).reshape(n, t, c // 6, 6)
    a1, a2 = d[..., :3], d[..., 3:]
    b1 = torch.nn.functional.normalize(a1, dim=-1)
    b2 = torch.nn.functional.normalize(a2 - (b1 * a2).sum(-1, keepdim=True) * b1, dim=-1)
    R = torch.stack((b1, b2, torch.cross(b1, b2, dim=-1)), dim=-2)
    dR = R[:, 1:] - R[:, :-1]
    sp = torch.sqrt(dR.pow(2).sum((-1, -2)) + 1e-12)
    return sp[..., chunk].mean(-1) if chunk is not None else sp.mean(-1)


def corr(a, b, m):
    a, b = a[m], b[m]
    a, b = a - a.mean(), b - b.mean()
    return (a * b).sum() / torch.sqrt((a * a).sum() * (b * b).sum() + 1e-12)


def statistic(xb, xh, lengths):
    """r_coord-type scalar (no target): mean over contexts of corr(R-arm, R-hand) + corr(L-hand, R-hand)."""
    sa = speeds(xb, [7, 9])  # R_Elbow, R_Wrist in the 10 predicted body joints
    sh = speeds(xh, None)
    tot = 0.0
    for i in range(xb.shape[0]):
        m = torch.zeros(sa.shape[1], dtype=torch.bool, device=sa.device)
        m[: int(lengths[i]) - 1] = True
        tot = tot + corr(sa[i], sh[2 * i + 1], m) + corr(sh[2 * i], sh[2 * i + 1], m)
    return tot / xb.shape[0]


def phase_memory(out):
    """E2d-M / E2d-G: one forward+backward per configuration; no optimiser, no update."""
    models, data = {}, {}
    for s in ("body", "hand"):
        cfg = us.build_cfg(s)
        m, _ = us.load_model(s, cfg)
        e, c = us.load_first_batch(s, cfg)
        data[s] = (e, c)
        models[s] = m
    texts = {s: data[s][1]["y"]["text"] for s in models}
    # cache per-B text embeddings with the resident M-CLIP, then move M-CLIP off the GPU
    caches = {}
    for B in B_LIST:
        for s in models:
            n = B if s == "body" else 2 * B
            with torch.no_grad():
                caches[(s, B)] = models[s].encode_text(list(texts[s][:n])).detach().clone()
    for s in models:
        models[s].text_enc_model.to("cpu")
    torch.cuda.empty_cache()
    weights_gib = round(torch.cuda.memory_allocated() / 2**30, 3)
    nb, nh = noise_for(data["body"][0].shape, SEED), noise_for(data["hand"][0].shape, SEED + 1)

    def set_cache(s, B):
        n = B if s == "body" else 2 * B
        key, emb = tuple(texts[s][:n]), caches[(s, B)]

        def cached(raw_text):
            if tuple(raw_text) != key:
                raise RuntimeError("uncached text")
            return emb
        models[s].encode_text = cached

    def one(B, variant, ck):
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
        cb, eb = us.subset(data["body"][1], data["body"][0], range(B))
        ch, eh = us.subset(data["hand"][1], data["hand"][0], range(2 * B))
        set_cache("body", B); set_cache("hand", B)
        sig = torch.ones(2, device="cuda", requires_grad=True)  # (sigma_L, sigma_R) at identity
        t0 = time.time()
        if variant == "design":  # z_b = eps_b does not depend on phi: body forward without grad
            with torch.no_grad():
                xb = us.unrolled_decode(models["body"], nb[:B], cb, eb)
        else:  # conservative: body also on the gradient path (dummy body scale)
            sb = torch.ones(1, device="cuda", requires_grad=True)
            xb = us.unrolled_decode(models["body"], nb[:B] * sb, cb, eb, use_checkpoint=ck)
        hn = nh[: 2 * B] * sig.repeat(B)[:, None, None]
        xh, states = us.unrolled_decode(models["hand"], hn, ch, eh, use_checkpoint=ck, keep_states=True)
        for st in states:
            st.retain_grad()
        r = statistic(xb, xh, cb["y"]["lengths"])
        r.backward()
        torch.cuda.synchronize()
        res = {"B": B, "variant": variant, "checkpoint": ck, "step_s": round(time.time() - t0, 3),
               "peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3),
               "peak_alloc_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
               "statistic": float(r), "grad_sigma": [float(v) for v in sig.grad],
               "grad_finite": bool(torch.isfinite(sig.grad).all()),
               "grad_norm_per_state": [float(st.grad.norm()) if st.grad is not None else None for st in states]}
        return res

    runs = []
    plan = [(B, "design", True) for B in B_LIST] + [(1, "design", False), (4, "conservative", True)]
    for B, v, ck in plan:
        for rep in (1, 2):  # rep 1 includes cuDNN/allocator warm-up; rep 2 is reported as the step time
            try:
                r = one(B, v, ck)
            except torch.OutOfMemoryError:
                r = {"B": B, "variant": v, "checkpoint": ck, "peak_reserved_GiB": "OOM"}
                torch.cuda.empty_cache()
            r["rep"] = rep
            runs.append(r)
            print(json.dumps({k: v2 for k, v2 in r.items() if k != "grad_norm_per_state"}), flush=True)
    res = {"flags": flags(), "weights_resident_GiB": weights_gib, "gate_GiB": GATE_GIB, "runs": runs,
           "gpu_total_GiB": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)}
    ok = [r for r in runs if r.get("variant") == "design" and r.get("checkpoint") and r["rep"] == 2
          and isinstance(r["peak_reserved_GiB"], float) and r["peak_reserved_GiB"] <= GATE_GIB and r["grad_finite"]]
    res["fits"] = [r["B"] for r in ok]
    res["largest_B_fitting"] = max(res["fits"]) if res["fits"] else None
    res["M_pass"] = bool(ok)
    big = [r for r in ok if r["B"] == res["largest_B_fitting"]]
    if big:
        g = [v for v in big[0]["grad_norm_per_state"] if v is not None]
        res["G_grad_norms_x0_to_x10"] = big[0]["grad_norm_per_state"]
        res["G_all_finite"] = all(np.isfinite(g))
        res["G_norm_ratio_max_over_min"] = float(max(g) / max(min(g), 1e-30))
    (out / "memory.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--phase", default="all", choices=["all", "hash", "t0", "memory"])
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    if args.phase in ("all", "hash"):
        phase_hash(out)
    if args.phase in ("all", "t0"):
        t0 = phase_t0(out)
        if not t0["T0_pass"]:
            print("T0 FAILED: stopping before the memory probe", flush=True)
            return
    if args.phase in ("all", "memory"):
        phase_memory(out)
    print(f"total_s {time.time() - t_start:.0f}", flush=True)


if __name__ == "__main__":
    main()
