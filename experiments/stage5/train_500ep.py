"""Stage 5 ACMS exploratory pilot: training (REINFORCE + RLOO, 500 episodes = 125 groups x 4; design Â§3, A5).

Per group g (one TRAIN clip, 4 episodes i with noise base + 1000 g + i):
  1. body x_b = G_body(eps_b) (frozen, no grad); s_hat = z-scored right-arm speed of x_b
  2. action eps_R = mu_phi(s_hat) + xi (mu under no_grad); left hand from eps_L; uncoupled twin from xi
  3. one hand call: [left x4 | controlled right x4 | uncoupled right x4] (frozen, no grad)
  4. reward (rewards.py, R v1.1, frozen tau; S-3 / A3), RLOO baseline, advantage
  5. loss = -(1/G) sum_i A_i log pi(eps_R,i | s_hat_i) (exact Gaussian log-prob, grad only to phi);
     global grad-norm clip 1.0; one Adam step; then dual ascent on lambda
Only the controller phi is optimised; SignSparK weights are frozen (requires_grad False; checksum logged).

  python -E -s experiments/stage5/train_500ep.py --config experiments/stage5/config_500ep.json --out experiments/stage5/out/train
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common5 as C  # noqa: E402  (sets HF_HUB_OFFLINE before any upstream import)

import numpy as np  # noqa: E402
import torch  # noqa: E402

import acms_policy as P  # noqa: E402
import episode_sampler as ES  # noqa: E402
import rewards as RW  # noqa: E402


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    assert cfg["n_groups"] * cfg["group_size"] == cfg["episodes"], "episodes must equal n_groups x group_size"
    if not cfg.get("test_mode", False):
        assert cfg["episodes"] == 500 and cfg["n_groups"] == 125 and cfg["group_size"] == 4, "approved protocol: 500 = 125 x 4"
    return cfg


def make_policy(cfg):
    p = cfg["policy"]
    return P.ACMS(rank=p["rank"], half_width=p["half_width"], channels=p["channels"], init_seed=p["init_seed"],
                  init_beta_frac=p["init_beta_frac"], init_w_std=p["init_w_std"],
                  kl_cap_nats_per_frame=p["kl_cap_nats_per_frame"])


def save_ckpt(path, policy, opt, lam, update):
    torch.save({"policy": {k: v.detach().cpu() for k, v in policy.state_dict().items()}, "adam": opt.state_dict(),
                "lambda": lam, "update": update}, path)


def flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        elif isinstance(v, (list, tuple)):
            for i, x in enumerate(v):
                out[f"{key}.{i}"] = x
        else:
            out[key] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    out = Path(args.out).resolve()
    (out / "checkpoints").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    G, n_groups, sd = cfg["group_size"], cfg["n_groups"], cfg["seeds"]
    clips = ES.train_clips(n_groups, sd["train_clip_sampler"])
    ctx = C.Ctx5({"train": clips})
    assert ctx.n_split["train"] == ES.N_TRAIN, f"train size {ctx.n_split['train']} != R0 {ES.N_TRAIN}"
    w0 = ctx.weight_checksum()
    policy = make_policy(cfg).cuda()
    o = cfg["optim"]
    opt = torch.optim.Adam(policy.parameters(), lr=o["adam_lr"], betas=tuple(o["adam_betas"]))
    lam = {k: float(cfg["reward"]["lambda_init"]) for k in RW.CONSTRAINTS}
    eta = float(cfg["reward"]["dual_ascent_eta"])
    ck_at = set(cfg["checkpoints_at_updates"])
    if 0 in ck_at:
        save_ckpt(out / "checkpoints" / "update_000.pt", policy, opt, lam, 0)
    run = {"label": cfg["label"], "config": cfg, "train_clips": clips, "flags": ctx.flags(),
           "tau_ah_R": RW.TAU, "s3_worst": RW.S3_WORST, "model_weight_checksum_start": w0}
    episodes, groups = [], []
    log = open(out / "train_log.txt", "w", encoding="utf-8")

    def say(*a):
        line = " ".join(str(x) for x in a)
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    status = "completed"
    try:
        for g, clip in enumerate(clips):
            if time.time() - t0 > cfg["cap_seconds"]:
                raise TimeoutError(f"cap {cfg['cap_seconds']} s reached before group {g}")
            if (out / "STOP").exists():
                raise KeyboardInterrupt(f"STOP file before group {g}")
            tg = time.time()
            meta = ctx.meta("train", clip)
            L = meta["L"]
            prep = ctx.batch("train", [clip])
            nz = [ES.train_noise(sd["train_noise_base"], g, i) for i in range(G)]
            eb = torch.stack([n[:60] for n in nz]).cuda()
            el = torch.stack([n[60:150] for n in nz]).cuda()
            xi = torch.stack([n[150:240] for n in nz]).cuda()
            xb = gen_np(ctx, "body", prep, [0] * G, eb)
            feats = [C.arm_feature(xb[i], L) for i in range(G)]
            s_hat = torch.as_tensor(np.stack([f for f, _ in feats])).cuda()
            Ls = [L] * G
            with torch.no_grad():
                mu = policy.mu(s_hat, Ls)
            eps_r = xi + mu
            xh = gen_np(ctx, "hand", prep, [0] * G + [1] * G + [1] * G, torch.cat([el, eps_r, xi]))
            xl, xr, xr0 = xh[:G], xh[G:2 * G], xh[2 * G:]
            recs = [RW.r_record(xb[i], xl[i], xr[i], L) for i in range(G)]
            recs0 = [RW.r_record(xb[i], xl[i], xr0[i], L) for i in range(G)]
            lam_used = dict(lam)
            terms = [RW.episode_reward(recs[i], recs0[i], lam_used) for i in range(G)]
            R = np.array([t["R"] for t in terms])
            base, adv = RW.rloo(R)
            # policy update
            opt.zero_grad()
            mu_g = policy.mu(s_hat, Ls)
            logp = P.ACMS.log_prob(eps_r, mu_g, Ls)
            loss = -(torch.as_tensor(adv, dtype=logp.dtype, device=logp.device) * logp).mean()
            loss.backward()
            gn_pre = float(torch.nn.utils.clip_grad_norm_(policy.parameters(), o["grad_clip_norm"]))
            grads_finite = all(torch.isfinite(p.grad).all() for p in policy.parameters())
            if not grads_finite:
                raise FloatingPointError(f"non-finite controller gradient at group {g}")
            gn_post = float(torch.sqrt(sum((p.grad ** 2).sum() for p in policy.parameters())))
            beta_before = float(policy.beta())
            before = [p.detach().clone() for p in policy.parameters()]
            opt.step()
            upd = float(torch.sqrt(sum(((p.detach() - q) ** 2).sum() for p, q in zip(policy.parameters(), before))))
            lam = RW.dual_update(lam, [t["c"] for t in terms], eta)
            kl = P.ACMS.kl_per_frame(mu, Ls).cpu().numpy()
            mu_norm = mu.norm(dim=1)[:, :L].cpu().numpy()  # [G, L] per-frame ||mu_t||
            dt = time.time() - tg
            mem = torch.cuda.max_memory_allocated() / 2**30
            for i in range(G):
                episodes.append({
                    "episode": g * G + i, "group": g, "i": i, "clip": meta, "seed": sd["train_noise_base"] + 1000 * g + i,
                    "noise_id": f"train/{g}/{i}", "arm_feature_valid": bool(feats[i][1]),
                    "action": {"mu_norm_mean": float(mu_norm[i].mean()), "mu_norm_max": float(mu_norm[i].max()),
                               "kl_per_frame": float(kl[i]), "beta": beta_before},
                    "log_prob": float(logp[i].detach()), "controlled": recs[i], "uncoupled_twin": recs0[i],
                    **terms[i], "baseline": float(base[i]), "advantage": float(adv[i])})
            groups.append({"group": g, "clip": meta, "loss": float(loss.detach()), "grad_norm_pre_clip": gn_pre,
                           "grad_norm_post_clip": gn_post, "param_norm": policy.param_norm(), "update_norm": upd,
                           "beta_after": float(policy.beta()), "lambda_after": lam, "R_mean": float(R.mean()),
                           "r_ah_mean": float(np.mean([t["r_ah"] for t in terms])),
                           "coord_mean": float(np.nanmean([r["coord_arm_rhand"] for r in recs])) if any(np.isfinite(r["coord_arm_rhand"]) for r in recs) else None,
                           "coord_twin_mean": float(np.nanmean([r["coord_arm_rhand"] for r in recs0])) if any(np.isfinite(r["coord_arm_rhand"]) for r in recs0) else None,
                           "c_mean": {k: float(np.mean([t["c"][k] for t in terms])) for k in RW.CONSTRAINTS},
                           "n_s3": int(sum(t["s3_undefined_primary"] for t in terms)),
                           "n_a3": {k: int(sum(t["a3_undefined"][k] for t in terms)) for k in RW.CONSTRAINTS},
                           "kl_mean": float(kl.mean()), "seconds": dt, "gpu_peak_alloc_GiB": mem})
            if (g + 1) in ck_at:
                save_ckpt(out / "checkpoints" / f"update_{g + 1:03d}.pt", policy, opt, lam, g + 1)
            say(f"[{time.time() - t0:6.0f}s] group {g:3d} clip {meta['index']:5d} L {L:3d} R {R.mean():+.3f} "
                f"r_ah {groups[-1]['r_ah_mean']:+.3f} loss {groups[-1]['loss']:+.4f} gn {gn_pre:.3f} beta {groups[-1]['beta_after']:.4f} "
                f"KL {kl.mean():.4f} lam {[round(lam[k], 3) for k in RW.CONSTRAINTS]} S3 {groups[-1]['n_s3']} {dt:.1f}s")
    except (TimeoutError, KeyboardInterrupt, FloatingPointError) as e:
        status = f"stopped: {type(e).__name__}: {e}"
        say(status)
    finally:
        w1 = ctx.weight_checksum()
        run.update({"status": status, "episodes_completed": len(episodes), "groups_completed": len(groups),
                    "model_weight_checksum_end": w1, "model_weights_unchanged": w0 == w1,
                    "model_trainable_params": ctx.n_trainable(), "opened_splits": list(C.OPENED_SPLITS),
                    "seconds": round(time.time() - t0, 1),
                    "gpu_peak_alloc_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                    "gpu_peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3),
                    "final_lambda": lam, "final_param_norm": policy.param_norm(), "final_beta": float(policy.beta())})
        (out / "episodes.json").write_text(json.dumps(episodes, indent=1, default=float), encoding="utf-8")
        (out / "groups.json").write_text(json.dumps(groups, indent=1, default=float), encoding="utf-8")
        (out / "run.json").write_text(json.dumps(run, indent=1, default=float), encoding="utf-8")
        if episodes:
            rows = [flat({k: v for k, v in e.items()}) for e in episodes]
            keys = sorted({k for r in rows for k in r})
            with open(out / "episodes.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(rows)
        say(f"status {status}; episodes {len(episodes)}; {run['seconds']} s; peak {run['gpu_peak_alloc_GiB']} GiB")
        log.close()
    return run


def gen_np(ctx, stream, prep, rows, noise):
    return ctx.gen(stream, prep, rows, noise).cpu().numpy()


if __name__ == "__main__":
    main()
