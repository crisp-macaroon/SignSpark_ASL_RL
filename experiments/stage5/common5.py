"""Stage 5 shared harness: frozen SignSparK samplers, train/dev batches by dataset index, cached M-CLIP embeddings.

Reuses the E2d-validated unrolled sampler (experiments/stage4/e2d/unrolled_sampler.py; bitwise = upstream decode) and
the unmodified upstream dataset class (third_party/SignSparK/signspark/pose_datasets_lmdb.py). One "full"-feature
dataset per split ([left 90 | right 90 | body 60 | face] per frame, flip_left_hand=True) is sliced into the body and
hand streams exactly as the per-stream datasets would produce them (R0 used the same construction because LMDB cannot
be opened twice in one process). Batches are then prepared as `unrolled_sampler.load_first_batch` does (hands split
into L/R and interleaved L0,R0,L1,R1,...; GF obs_mask all False). Only the train and dev splits can be opened.

Model weights: eval(), requires_grad=False (load_model), never passed to an optimiser. Text embeddings: each stream's
own frozen M-CLIP encodes every needed text once on the GPU (chunks in index order); the encoders are then moved to
the CPU and `encode_text` serves only cached texts (any other text raises).
"""

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # approved A5: M-CLIP from the local cache, no hub query

import copy  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
for p in ("experiments/stage4/e2d", "experiments/stage4/e2e", "experiments/stage4/validity", "experiments/stage4",
          "experiments/stage4/e2c"):
    sys.path.insert(0, str(ROOT / p))
import unrolled_sampler as us  # noqa: E402  (E2d harness; imports upstream unmodified)
import metrics as MR  # noqa: E402  (space R v1, registered)
import validity as V  # noqa: E402  (R v1.1 / J v1.1)

DATA = ROOT / "data" / "raw" / "SignSparK_data"
FROZEN = ROOT / "research" / "stage4" / "FROZEN_TARGETS_R0.json"
ALLOWED_SPLITS = ("train", "dev")
SEQ = 304
CH = {"body": 60, "hand": 90}
OPENED_SPLITS = []  # audit trail: every split opened in this process


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def frozen_targets():
    return json.loads(FROZEN.read_text(encoding="utf-8"))


def data_cfg(split):
    from hydra import compose, initialize_config_dir
    ov = ["data_v2=full", "data_v2/common@common=inference", f"base_path={DATA}", "train_data=[How2Sign]",
          "dev_data=[How2Sign]", f"eval.split={split}", "flip_left_hand=True"]
    with initialize_config_dir(config_dir=str(ROOT / "third_party" / "SignSparK" / "configs"), version_base=None):
        return compose(config_name="default", overrides=ov)


def lmdb_path(split):
    if split not in ALLOWED_SPLITS:
        raise ValueError(f"split {split!r} is not allowed in Stage 5 (train/dev only)")
    paths = sorted((DATA / split).glob("*How2Sign*.lmdb"))
    if len(paths) != 1:
        raise FileNotFoundError(f"expected one How2Sign LMDB for {split}, found {paths}")
    return paths[0]


def open_dataset(split):
    from signspark.pose_datasets_lmdb import PoseDataset_Lmdb
    path = lmdb_path(split)
    OPENED_SPLITS.append(split)
    return PoseDataset_Lmdb(data_cfg(split), split=split, seq_len=SEQ, data=str(path), concat_hands=False)


def stream_items(item):
    """One "full" dataset item -> (body item, hand item) as the per-stream datasets return them."""
    f, n, text, kf, name = item
    return (f[:, 180:240], n, text, kf, name), (f[:, :180], n, text, kf, name)


def prepare(stream, items, device="cuda"):
    """Collate per-stream items and prepare cond exactly as unrolled_sampler.load_first_batch."""
    from signspark.pose_datasets_lmdb import custom_collate_fn
    embed, batch = custom_collate_fn(items)
    embed = embed.to(device)
    cond = {"y": copy.deepcopy(batch)}
    if stream == "hand":
        left, right = embed[:, : embed.shape[1] // 2, :], embed[:, embed.shape[1] // 2:, :]
        embed = torch.stack([left, right], dim=1).reshape(-1, left.shape[1], left.shape[2])
        cond["y"]["mask"] = cond["y"]["mask"].repeat_interleave(2, dim=0)
        cond["y"]["lengths"] = cond["y"]["lengths"].repeat_interleave(2, dim=0)
        cond["y"]["text"] = [t for t in cond["y"]["text"] for _ in range(2)]
        cond["y"]["keyframes"] = [k for k in cond["y"]["keyframes"] for _ in range(2)]
        cond["y"]["video_names"] = [v for v in cond["y"]["video_names"] for _ in range(2)]
    cond["obs_x0"] = embed
    cond["obs_mask"] = torch.zeros_like(embed, dtype=torch.bool)
    return embed, cond


class Ctx5:
    """Frozen body + hand samplers and the clips of `needed` = {split: [dataset indices]}."""

    def __init__(self, needed, text_chunk=32):
        self.m = {}
        for s in ("body", "hand"):
            self.m[s], _ = us.load_model(s, us.build_cfg(s))
        self.items, self.n_split = {}, {}
        for split, idx in needed.items():
            ds = open_dataset(split)
            self.n_split[split] = len(ds)
            for i in idx:
                self.items[(split, int(i))] = ds[int(i)]
        # Text lists are encoded exactly as each stream's batch presents them (E2e/E2d convention: body [t_0, t_1, ...],
        # hand [t_0, t_0, t_1, t_1, ...]), in chunks of 32 clips in index order (dev 0..31 = the E2e/E2d batch). M-CLIP
        # embeddings depend on batch composition at the 1e-6 level, which the 10-step sampler amplifies to ~2e-3
        # (integration test I2, diagnosed 2026-11-04), so the convention is kept exactly. A text met again later keeps
        # its first embedding.
        self.cache = {}
        clips = [(split, int(i)) for split, idx in needed.items() for i in idx]
        for s in ("body", "hand"):
            enc = self.m[s].encode_text
            self.cache[s] = {}
            with torch.no_grad():
                for a in range(0, len(clips), text_chunk):
                    tl = [self.items[c][2] for c in clips[a: a + text_chunk]]
                    if s == "hand":
                        tl = [t for t in tl for _ in range(2)]
                    emb = enc(list(tl)).detach().clone()
                    for t, e in zip(tl, emb):
                        self.cache[s].setdefault(t, e)
            self.m[s].text_enc_model.to("cpu")
            self.m[s].encode_text = (lambda raw, s=s: torch.stack([self.cache[s][t] for t in raw]))
        torch.cuda.empty_cache()
        assert all(not mod.training for s in self.m for mod in self.m[s].modules())
        assert self.n_trainable() == 0

    def n_trainable(self):
        return sum(p.requires_grad for s in self.m for p in self.m[s].parameters())

    def weight_checksum(self):
        return {s: float(sum(float(p.double().sum()) for p in self.m[s].parameters())) for s in self.m}

    def flags(self):
        return {"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32, "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                "cudnn_benchmark": torch.backends.cudnn.benchmark, "cudnn_deterministic": torch.backends.cudnn.deterministic,
                "dtype": "float32", "device": torch.cuda.get_device_name(0), "torch": torch.__version__,
                "training_any": any(mod.training for s in self.m for mod in self.m[s].modules()),
                "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE")}

    def meta(self, split, i):
        f, n, text, kf, name = self.items[(split, int(i))]
        return {"split": split, "index": int(i), "name": str(name), "L": int(n)}

    def batch(self, split, idx):
        """Prepared (embed, cond) per stream for dataset indices idx (in that order)."""
        items = [stream_items(self.items[(split, int(i))]) for i in idx]
        return {"body": prepare("body", [b for b, _ in items]), "hand": prepare("hand", [h for _, h in items])}

    def gen(self, stream, prepared, rows, noise):
        """No-grad 10-step generation for rows `rows` of a prepared batch; noise [n, C, 304] float32 on cuda."""
        embed, cond = prepared[stream]
        c, e = us.subset(cond, embed, rows)
        with torch.no_grad():
            return us.unrolled_decode(self.m[stream], noise, c, e, n_steps=10)


def noise(base, a, b):
    """Registered-style base noise [240, 304] (body 0:60, left 60:150, right 150:240), float32 CPU."""
    g = torch.Generator().manual_seed(int(base) + 1000 * int(a) + int(b))
    return torch.randn(240, SEQ, generator=g)


def arm_feature(xb, L):
    """Generated body (60, T) -> z-scored right-arm geodesic speed per frame (length T, zeros beyond L), validity flag.
    Speed of frame t = angle between frames t and t+1 (registered arm_signals); the last active frame repeats the
    previous speed. Invalid (R v1.1 floor) or non-finite arm signal -> all-zero feature (flagged)."""
    out = np.zeros(xb.shape[1], np.float32)
    if not np.isfinite(xb[:, :L]).all():
        return out, False
    with np.errstate(invalid="ignore", divide="ignore"):
        s = MR.arm_signals(xb, L)[0]
    ok = V.r_signal_valid(s)
    if not ok:
        return out, False
    s = np.concatenate([s, s[-1:]])
    out[:L] = ((s - s.mean()) / s.std()).astype(np.float32)
    return out, True
