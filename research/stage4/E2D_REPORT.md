# E2d report: sampler and gradient feasibility (Stage 4 rev. 4.0, Step 1)

*Run 2026-11-03 under the user's explicit go-ahead for E2d (the execution assignment of 2026-11-03).*

**Conclusion: PASS.**
- T0 passed, with exact (bitwise) agreement.
- Every K = 10 configuration tested fits in ≤ 8.8 GiB peak reserved memory. The gate is 14 GiB.
- Gradients are finite.

All generation numbers are **released-checkpoint results, not a paper reproduction** (R10). No perceptual or semantic claim is made.

## Objective
1. Verify that the differentiable unrolled 10-step sampler reproduces the released sampler.
2. Measure the real memory and runtime of one M-C gradient pass.
3. Check M-CLIP weight sharing across the stream checkpoints.

## Code and configuration

| Item | Value |
|---|---|
| Harness | `experiments/stage4/e2d/unrolled_sampler.py` |
| Runner | `experiments/stage4/e2d/e2d_run.py --phase all` |
| Environment | `.venv-infer` (Python 3.12.10, torch 2.10.0+cu128, CUDA 12.8, cuDNN 91002). Verified against `requirements-infer.lock.txt`: no differences except the editable local `signspark-bt` entry, which the lock records in another form |
| Config | Hydra compose of upstream `configs/default.yaml` with the Stage 3 GF overrides: `data_v2=<stream>`, `data_v2/common@common=inference`, `dev_data=[How2Sign]`, `eval.split=dev`, `eval.batch_size=32`, `eval.ode_stepnum=10`, `flip_left_hand=True`, `eval.keyframes_mask_all=True` |
| Upstream code | `third_party/SignSparK` imported, **not modified**. The adaptation is `experiments/common/offline_mclip.py`: config-only M-CLIP construction, with weights loaded strictly from the checkpoint, as in Stage 3 |
| Environment variables | `HF_HOME=models/hf_cache`, `WANDB_MODE=disabled`, `HF_HUB_OFFLINE=1` |

**Noise injection:**
- Upstream `RFlow.decode(model, noise, keyframe_mask, ...)` takes the initial noise as an argument [C, `rflow.py:198–218`], so **identical noise is passed directly**. No patching was needed.
- Noise comes from `torch.Generator().manual_seed(seed)` on the CPU, then is moved to the GPU.

**Harness:**
- It replicates torchdiffeq's fixed-grid Euler exactly:
  - grid `arange(0, 11)·0.1`, with the last point set to 1;
  - `x_{k+1} = x_k + (t_{k+1} − t_k)·model(x_in, t_k·1_B, y, obs_x0, obs_mask)`;
  - keyframe masking of the model input, and the initial state `x_embed·mask + noise·(~mask)`, as upstream.
- Optional non-reentrant `torch.utils.checkpoint` per Euler step.
- No learnable parameters.

**Text embedding:**
- Each model's own frozen M-CLIP encodes the batch's text list once.
- `model.encode_text` then returns that cached tensor for exactly that list, and raises on any other list.
- For the memory probe, the M-CLIP sub-modules were moved to the CPU after caching (the design's "M-CLIP not resident").

## Data, checkpoints, seeds, numerics

**Clips:** dev clips 0–31 in the deterministic loader order. They are cross-checked identical, in names and lengths, to entries 0–31 of the existing dev-256 dump.
- First: `-d5dN54tH2E_0-1-rgb_front`; last: `-f1_kdl050s_27-1-rgb_front`.
- Lengths 28–304 frames. The full lists are in `t0.json`.
- Hands are interleaved L/R, giving 64 sequences. GF regime: obs_mask all False.

**Checkpoint SHA-256** (all match `models/MANIFEST.json`):
- body `bf95bb02…a380`;
- hand `5bb8e407…16c2`;
- face `841e6ce5…ad53`.

**Seeds:** body noise 20261103; hand noise 20261104.

**Numerics (recorded, unchanged from defaults):**
- fp32;
- `matmul.allow_tf32 = False`; `cudnn.allow_tf32 = True`; float32 matmul precision "highest";
- `cudnn.benchmark = False`; `cudnn.deterministic = False`;
- device: RTX A4000.

## Results

### T0 and E2d-F (`out/t0.json`)

| Test | Criterion | Body | Hand | Outcome |
|---|---|---|---|---|
| T0a harness vs upstream `decode`, identical noise (32 clips) | max \|Δx\| ≤ 1e-4 | **0.0** (all and active frames) | **0.0** | PASS |
| T0b determinism (two harness runs) | bitwise | 0.0 | 0.0 | PASS |
| T0c checkpointed vs not (4 rows, grad mode) | outputs bitwise | 0.0 | 0.0 | PASS |
| E2d-F `model.training` on every module | all False | [False] | [False] | PASS |
| NFE | 10 | 10 | 10 | — |

**Observation (not a T0 criterion):** **backward** passes are not bitwise reproducible.
- With and without checkpointing, the input-gradient scalars differed in the 6th significant digit: body −0.0606435 vs −0.0606432; hand −0.0307445 vs −0.0307444.
- Repeated runs differed at the ~4e-5 relative level.
- **Cause [I]:** non-deterministic cuDNN/atomic backward kernels under `cudnn.deterministic = False`, the Stage 3 setting.
- Forward outputs are bitwise identical. This is relevant to E2a's gradient-cosine criterion (≥ 0.95) only at a negligible scale.

### E2d-H: M-CLIP sub-weights (`out/mclip_hash.json`)

393 `text_enc_model.*` tensors (560,546,432 parameters) per checkpoint.

| Checkpoint | SHA-256 over sorted names, shapes, dtypes and bytes |
|---|---|
| body | e39c1349…3e30 |
| hand | e39c1349…3e30 |
| face | e39c1349…3e30 |

**Result:** identical in all three, so **one cached text embedding can serve every stream** (resolves Q11).

### E2d-M: memory and time of one M-C gradient pass (`out/memory.json`)

**Pass definition:** B contexts → the body stream (B sequences) and the hand stream (2B sequences); unrolled K = 10.
- **Design path:** the body runs without grad, since z_b = ε_b does not depend on φ. Hand noise = σ·ε⁰ with a leaf σ = (1, 1).
- **Scalar output:** a differentiable rotation-space coordination statistic, mean over contexts of corr(R-arm, R-hand) + corr(L-hand, R-hand). Speed is the chordal ‖R_{t+1} − R_t‖_F, a monotone function of the geodesic angle.
- One `backward()`. **No optimiser; no parameter update.**
- Body and hand U-Nets resident without M-CLIP: **6.26 GiB**. GPU total 15.99 GiB; display ≈ 1.2 GiB.

Times are from the second repetition (warm):

| B | Variant | Checkpointing | Peak reserved (GiB) | Peak allocated (GiB) | Time per pass (s) | Gradient finite |
|---|---|---|---|---|---|---|
| 1 | design | yes | 7.41 | 6.62 | 2.99 | yes |
| 2 | design | yes | 7.39 | 6.87 | 3.05 | yes |
| 4 | design | yes | 7.46 | 7.44 | 3.77 | yes |
| 8 | design | yes | **8.80** | 8.61 | 5.93 | yes |
| 1 | design | no | 8.73 | 8.55 | 1.95 | yes |
| 4 | conservative (body also on the grad path) | yes | 7.70 | 7.44 | 5.51 | yes |

**Gate (≤ 14 GiB, K = 10, finite gradients): met at every B**, the largest being B = 8.

**Measured vs the Stage 4 §11 estimates [E]:**
- B = 4 with checkpointing: estimated ≈ 10–11 GiB and 5–8 s; measured 7.46 GiB and 3.8 s (design path).
- B = 1 without checkpointing: estimated ≈ 10.7 GiB; measured 8.7 GiB.
- The estimates were conservative.
- The M-C step in training would add only the small controller network and the Stiefel/QR maps. Those are not measured here [U].

### E2d-G: per-Euler-step input-gradient norms (B = 8, design path)

‖∂r/∂x_k‖ for the hand-stream states x_0 (= ε̃) … x_10 (output):

0.578, 0.627, 0.540, 0.422, 0.313, 0.246, 0.205, 0.183, 0.169, 0.162, 0.604

- All finite.
- Maximum/minimum ratio across steps: **3.9** (the E2a stop threshold is 10³).
- Measured directly. The decay toward t → 1 and the jump at the output state are recorded for E2a; no interpretation is drawn here.

## Acceptance

| Criterion | Outcome |
|---|---|
| Noise injection without modifying upstream code | met (decode takes `noise`) |
| T0 (a, b, c) and F | PASS |
| ≥ 1 K = 10 configuration ≤ 14 GiB peak reserved | PASS (B = 1, 2, 4, 8) |
| Finite gradients | PASS |
| **E2d** | **PASS** |

## Runtime, warnings, deviations
- **Wall time:** 200 s in total (cap 45 min), including three 5.6 GB checkpoint loads for hashing.
- **Warnings (benign):**
  - pydantic `UnsupportedFieldAttributeWarning`, from a transformers dependency at import;
  - a torch warning from `float()` on a grad tensor while logging.

  PowerShell labels the stderr of these warnings "NativeCommandError"; the exit code was 0.
- **Deviations:**
  - The checklist described the scalar only as "a differentiable rotation-space statistic". I used the r_coord-type correlation without a target (no train target exists yet; R0).
  - The "conservative" variant is an extra measurement, not a deviation.

## Outputs
- `experiments/stage4/e2d/out/`:
  - `t0.json`;
  - `t0_body.npz`, `t0_hand.npz` (noise, upstream and harness outputs);
  - `mclip_hash.json`;
  - `memory.json`;
  - `run.log`.

## Reproduce
From the project root, with `HF_HOME=models\hf_cache`, `WANDB_MODE=disabled` and `HF_HUB_OFFLINE=1`:

```
.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2d\e2d_run.py --out experiments\stage4\e2d\out --phase all
```

## Claim types
- **Measured:** every T0 difference, hash, memory, time and gradient norm.
- **Derived:** "one cached embedding serves all streams" (from identical hashes).
- **Assumption:** that the design path (body without grad) is the M-C gradient path. This follows from App. G (z_b = ε_b).
- **Unresolved:** the memory of the full controller (QR/Stiefel maps, controller MLP); backward nondeterminism.
