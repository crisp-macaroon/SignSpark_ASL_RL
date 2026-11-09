"""OPT-G: training-like evaluation of an ACMS run (ACMS_MULTISEED_DESIGN.md §6). The run's own 125 TRAIN clips, FRESH
noise (base 45,000,000 + 1000 g + k, g = group / clip position 0..124, k = 1..4; disjoint from every training and
evaluation seed), three conditions on common noise (uncoupled / initial / final), space R only (J not computed:
documented operational choice). Generation mirrors evaluate.generate exactly (batches of 32 clips; one body call, two
hand calls per noise); the analysis is evaluate.analyse unchanged. Monitoring / generalisation measurement only: no
checkpoint selection. Opens only the TRAIN split.

  python -E -s experiments/stage5_multiseed/evaluate_train.py --config <cfg> --train-dir <run>/train --out <run>/optg
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "stage5"))
import common5 as C  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

import acms_policy as P  # noqa: E402
import evaluate as EV  # noqa: E402
import rewards as RW  # noqa: E402
from train_500ep import load_config  # noqa: E402

FRESH_BASE = 45_000_000
K = 4


def generate(ctx, clips, pols):
    recs = []
    for c0 in range(0, len(clips), 32):
        pos = list(range(c0, min(len(clips), c0 + 32)))
        n = len(pos)
        prep = ctx.batch("train", [clips[g] for g in pos])
        metas = [ctx.meta("train", clips[g]) for g in pos]
        Ls = [m["L"] for m in metas]
        for k in range(1, K + 1):
            nz = [C.noise(FRESH_BASE, g, k) for g in pos]
            eb = torch.stack([z[:60] for z in nz]).cuda()
            el = torch.stack([z[60:150] for z in nz]).cuda()
            xi = torch.stack([z[150:240] for z in nz]).cuda()
            xb = ctx.gen("body", prep, list(range(n)), eb).cpu().numpy()
            feats = [C.arm_feature(xb[a], Ls[a]) for a in range(n)]
            s_hat = torch.as_tensor(np.stack([f for f, _ in feats])).cuda()
            with torch.no_grad():
                mu = {"uncoupled": torch.zeros_like(xi), "initial": pols["initial"].mu(s_hat, Ls),
                      "trained": pols["trained"].mu(s_hat, Ls)}
            eps = {c: xi + mu[c] for c in EV.CONDS}
            lr_, rr_ = [2 * a for a in range(n)], [2 * a + 1 for a in range(n)]
            h1 = ctx.gen("hand", prep, lr_ + rr_, torch.cat([el, eps["uncoupled"]])).cpu().numpy()
            h2 = ctx.gen("hand", prep, rr_ + rr_, torch.cat([eps["initial"], eps["trained"]])).cpu().numpy()
            xl, xr = h1[:n], {"uncoupled": h1[n:], "initial": h2[:n], "trained": h2[n:]}
            kl = {c: P.ACMS.kl_per_frame(mu[c], Ls).cpu().numpy() for c in EV.CONDS}
            for a, g in enumerate(pos):
                for c in EV.CONDS:
                    recs.append({"clip": g, "dataset_index": clips[g], "name": metas[a]["name"], "L": Ls[a], "k": k, "cond": c,
                                 "seed": FRESH_BASE + 1000 * g + k, "arm_feature_valid": bool(feats[a][1]),
                                 "kl_per_frame": float(kl[c][a]), "R": RW.r_record(xb[a], xl[a], xr[c][a], Ls[a]),
                                 "typicality": EV.typ_monitor(eps[c][a, :, :Ls[a]].cpu().numpy())})
        print(f"clips {c0}-{c0 + n - 1} done ({len(recs)} records)", flush=True)
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--train-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    tdir, out = Path(a.train_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    run = json.loads((tdir / "run.json").read_text(encoding="utf-8"))
    clips = run["train_clips"]
    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    ctx = C.Ctx5({"train": clips})
    w0 = ctx.weight_checksum()
    ck = tdir / "checkpoints"
    pols = {"initial": EV.load_policy(cfg, ck / "update_000.pt"), "trained": EV.load_policy(cfg, ck / "update_125.pt")}
    recs = generate(ctx, clips, pols)
    (out / "train_eval_samples.json").write_text(json.dumps(recs, default=float), encoding="utf-8")
    res = EV.analyse(recs, cfg)
    res["label"] = "OPT-G training-like evaluation (own TRAIN clips, fresh noise); " + cfg["label"]
    res["run"] = {"split": "train", "fresh_noise_base": FRESH_BASE, "n_clips": len(clips), "n_noises": K,
                  "checkpoints_sha256": {"initial": C.sha256(ck / "update_000.pt"), "trained": C.sha256(ck / "update_125.pt")},
                  "flags": ctx.flags(), "opened_splits": list(C.OPENED_SPLITS), "model_weights_unchanged": w0 == ctx.weight_checksum(),
                  "seconds": round(time.time() - t0, 1), "gpu_peak_alloc_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
                  "gpu_peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2**30, 3)}
    (out / "train_eval_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("train-like trained-uncoupled", res["R_space"]["coord_arm_rhand"]["trained-uncoupled"]["paired_clip_mean"], res["run"]["seconds"], "s")


if __name__ == "__main__":
    main()
