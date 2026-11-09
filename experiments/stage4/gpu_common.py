"""Shared GPU setup for E2a, E2b, E2c: the E2d-validated unrolled harness, dev clips 0..31 (GF, oracle length),
E2e's registered noise seeds (CRN), M-CLIP run once with per-text cached embeddings (M-CLIP identical in all three
checkpoints, E2d-H), fp32, eval(), default flags. Released checkpoints read-only; no optimiser on model weights."""

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2d"))
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2e"))
import unrolled_sampler as us  # noqa: E402
import e2d_run as E2D  # noqa: E402  (differentiable chordal speeds, corr, statistic)
import e2e_run as E2E  # noqa: E402  (registered noise seeds: base_noise)
import metrics as MR  # noqa: E402  (registered space-R geodesic metrics, numpy)

J = 32


class Ctx:
    def __init__(self):
        self.m, self.cond, self.embed, self.cache = {}, {}, {}, {}
        for s in ("body", "hand"):
            cfg = us.build_cfg(s)
            self.m[s], _ = us.load_model(s, cfg)
            self.embed[s], self.cond[s] = us.load_first_batch(s, cfg)
            texts = self.cond[s]["y"]["text"]
            with torch.no_grad():
                emb = self.m[s].encode_text(list(texts)).detach().clone()  # M-CLIP on GPU once
            self.cache[s] = {t: emb[i] for i, t in enumerate(texts)}
            self.m[s].text_enc_model.to("cpu")
            self.m[s].encode_text = (lambda raw, s=s: torch.stack([self.cache[s][t] for t in raw]))
        torch.cuda.empty_cache()
        self.lengths = [int(v) for v in self.cond["body"]["y"]["lengths"]]
        self.names = self.cond["body"]["y"]["video_names"]
        assert all(not mod.training for s in self.m for mod in self.m[s].modules())

    def flags(self):
        return {"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32, "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                "cudnn_benchmark": torch.backends.cudnn.benchmark, "cudnn_deterministic": torch.backends.cudnn.deterministic,
                "dtype": "float32", "device": torch.cuda.get_device_name(0), "torch": torch.__version__,
                "training_any": any(mod.training for s in self.m for mod in self.m[s].modules())}

    def rows(self, stream, idx):
        return us.subset(self.cond[stream], self.embed[stream], idx)

    def body(self, eps_b, clips, n_steps=10):
        c, e = self.rows("body", clips)
        return us.unrolled_decode(self.m["body"], eps_b, c, e, n_steps=n_steps)

    def hand(self, eps_h, hand_rows, n_steps=10, ck=False, keep_states=False):
        c, e = self.rows("hand", hand_rows)
        return us.unrolled_decode(self.m["hand"], eps_h, c, e, n_steps=n_steps, use_checkpoint=ck, keep_states=keep_states)


def noise(set_name, j, k):
    """E2e registered seeds: [240, 304] (body 0:60, L 60:150, R 150:240), float32 CPU."""
    return E2E.base_noise(set_name, j, k)


def arm_r_speed(xb6, L):
    """Registered geodesic right-arm speed profile (numpy), body (60, T)."""
    return MR.arm_signals(xb6, L)[0]


def hand_speed(xh6, L):
    return MR.hand_stats(xh6, L)["s"]


def boot_mean_ci(v, seed=0, B=2000):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    idx = np.random.default_rng(seed).integers(0, len(v), (B, len(v)))
    m = v[idx].mean(1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}
