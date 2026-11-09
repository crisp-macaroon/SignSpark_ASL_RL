"""Differentiable unrolled 10-step Euler sampler for the frozen SignSparK streams (Stage 4 E2d).

Reproduces upstream RFlow.decode / sflow_sampler(ode_package="torchdiffeq", method="euler",
step_size=1/ode_stepnum) without its @torch.no_grad and odeint_adjoint wrapper:
  * grid: torchdiffeq _grid_constructor_from_step_size, i.e. arange(0, n+1)*h + 0, last = 1;
  * per step: x_t := x_embed*obs_mask + x_t*(~obs_mask) (model input only), then
    x_{k+1} = x_k + (t_{k+1} - t_k) * model(x_t, t_k*ones(B), **cond);
  * the initial state is x_embed*keyframe_mask + noise*(~keyframe_mask), as in decode.
Optional non-reentrant torch.utils.checkpoint per Euler step. No learnable parameters here;
upstream code under third_party/ is imported, never modified.

Text embeddings: `cache_text(model, texts)` runs the model's own frozen M-CLIP once and makes
`model.encode_text` return the cached tensor for exactly that text list (the controller design's
"encode_text bypassed"); any other list raises, so a stale cache cannot be used silently.
"""

import copy
import sys
from pathlib import Path

import torch
from torch.utils.checkpoint import checkpoint

ROOT = Path(__file__).resolve().parents[3]
UPSTREAM = ROOT / "third_party" / "SignSparK"
sys.path.insert(0, str(UPSTREAM))
sys.path.insert(0, str(ROOT / "experiments" / "common"))
import offline_mclip  # noqa: E402,F401  (config-only M-CLIP construction; weights come from the checkpoint)

STREAM_DIMS = {"body": 60, "hand": 90}


def euler_grid(n_steps, device, dtype=torch.float32):
    """torchdiffeq fixed grid for t in [0, 1] with step_size = 1/n_steps."""
    t = torch.tensor([0.0, 1.0], device=device, dtype=dtype)
    h = 1.0 / n_steps
    niters = torch.ceil((t[-1] - t[0]) / h + 1).item()
    grid = torch.arange(0, niters, dtype=dtype, device=device) * h + t[0]
    grid[-1] = t[-1]
    return grid


def unrolled_decode(model, noise, cond, x_embed, n_steps=10, use_checkpoint=False, keep_states=False):
    """Euler-integrate the frozen velocity field from `noise`. Gradients flow if `noise` requires grad."""
    mask = cond["obs_mask"]
    x = x_embed * mask + noise * (~mask)
    grid = euler_grid(n_steps, noise.device, noise.dtype)
    states = [x]

    def step(x_k, t0, t1):
        t_vec = torch.ones(len(x_k), device=x_k.device) * t0
        x_in = x_embed * mask + x_k * (~mask)
        return x_k + (t1 - t0) * model(x_in, t_vec, **cond)

    for k in range(len(grid) - 1):
        if use_checkpoint and torch.is_grad_enabled():
            x = checkpoint(step, x, grid[k], grid[k + 1], use_reentrant=False)
        else:
            x = step(x, grid[k], grid[k + 1])
        if keep_states:
            states.append(x)
    return (x, states) if keep_states else x


def cache_text(model, texts):
    """Encode `texts` once with the model's frozen M-CLIP; route later identical calls to the cache."""
    with torch.no_grad():
        emb = model.encode_text(list(texts)).detach().clone()
    key = tuple(texts)
    original = model.encode_text

    def cached(raw_text):
        if tuple(raw_text) != key:
            raise RuntimeError("encode_text called with an uncached text list")
        return emb

    model.encode_text = cached
    return emb, original


def build_cfg(stream, overrides=()):
    """Same Hydra config as the Stage 3 GF runs (experiments/baseline/run_baseline.ps1)."""
    from hydra import compose, initialize_config_dir
    ov = [f"data_v2={stream}", "data_v2/common@common=inference",
          f"base_path={ROOT / 'data' / 'raw' / 'SignSparK_data'}", "dev_data=[How2Sign]", "eval.split=dev",
          "eval.batch_size=32", "eval.ode_stepnum=10", "flip_left_hand=True", "eval.keyframes_mask_all=True",
          *overrides]
    with initialize_config_dir(config_dir=str(UPSTREAM / "configs"), version_base=None):
        return compose(config_name="default", overrides=ov)


def load_model(stream, cfg, device="cuda"):
    from basic_utils import args_to_dict, create_model_and_flow
    model, flow = create_model_and_flow(**args_to_dict(cfg, cfg.keys()))
    sd = torch.load(ROOT / f"models/SignSparK/{stream}/ema_0.9999_200000.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(sd, strict=True)
    del sd
    model.eval().requires_grad_(False).to(device)
    return model, flow


def load_first_batch(stream, cfg, device="cuda"):
    """First dev batch of 32 clips in the deterministic loader order (= dev-256 clips 0..31), prepared as
    sample.py does: hands split into L/R and interleaved L0,R0,L1,R1,...; GF obs_mask = all False."""
    from signspark.pose_datasets_lmdb import load_lmdb_dataset
    data = load_lmdb_dataset(batch_size=cfg.eval.batch_size, seq_len=cfg.eval.seq_len, data_args=cfg,
                             split=cfg.eval.split, deterministic=True, segments=False, num_workers=0,
                             drop_last=False, concat_hands=(stream == "hand"))
    embed, batch = next(iter(data))
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


def subset(cond, embed, idx):
    """Rows `idx` of a prepared batch (cond dict + x_embed)."""
    idx = list(idx)
    y = cond["y"]
    sub_y = {}
    for k, v in y.items():
        if torch.is_tensor(v):
            sub_y[k] = v[idx]
        elif isinstance(v, list):
            sub_y[k] = [v[i] for i in idx]
        else:
            sub_y[k] = v
    return {"y": sub_y, "obs_x0": cond["obs_x0"][idx], "obs_mask": cond["obs_mask"][idx]}, embed[idx]
