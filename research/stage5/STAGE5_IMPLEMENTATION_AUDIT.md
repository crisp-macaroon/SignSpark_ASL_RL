# Stage 5 ACMS pilot: implementation audit, tests, hashes and final configuration

*2026-11-04. Implementation and tests only. **The 500-episode training run has NOT been started.***

**Authorised:** A1–A7 of `STAGE5_500EP_DESIGN.md`, plus implementation, unit tests and integration tests.

**Not done:**
- the 500-episode run;
- evaluation of a trained controller;
- any change to SignSparK weights, the R0 targets, metric definitions, the validity layer or Stage 4 artifacts;
- any use of test data.

**Labels:** [V] verified by test or hash · [D] derived · [I] interpretation · [U] unresolved.

**Framing (for every later report):**
- The reward is **target matching toward the frozen R-space right arm–hand coordination target**, not unrestricted maximisation.
- R is the primary space. J is descriptive only.
- Paired improvement is reported separately from attainment of 0.05.
- No semantic, naturalness, intelligibility or ASL-quality claim.

---

## 1. Code (`experiments/stage5/`)

| File | Role | Design item |
|---|---|---|
| `common5.py` | Frozen samplers (the E2d harness `unrolled_sampler`, imported unchanged).<br>Train/dev batches by dataset index through the **unmodified upstream** `PoseDataset_Lmdb` + `custom_collate_fn`; one "full"-feature dataset per split, sliced into the body/hand streams (as R0).<br>Cached M-CLIP embeddings; R-space arm feature.<br>**Split guard:** only `train` / `dev` can be opened (`ValueError` otherwise); every opened split is logged. Sets `HF_HUB_OFFLINE=1` | A7, A5 |
| `acms_policy.py` | ACMS policy: μ = β·U·tanh(W∗ŝ + c), with r = 4, a 17-tap kernel and β_max = √(2/r) (KL < 1 nat per frame by construction).<br>Exact Gaussian log π; exact KL per frame; 433 parameters | A1 |
| `rewards.py` | R = r_ah − Σ λ_k c_k, with r_ah = −\|coord − τ\| and τ read from `FROZEN_TARGETS_R0.json`.<br>**S-3:** an undefined primary term gives −(1 + τ) and is flagged.<br>Constraints art / jerk / ext / act, clipped to [−1, 1]. **A3:** an undefined constraint gives +1 and is flagged.<br>RLOO baseline; dual ascent | A2, A3, A4 |
| `episode_sampler.py` | 125 train clips: `default_rng(5000).choice(29,630, 125, replace=False)`.<br>Noise seed = base + 1000a + b: train base 5e7, eval base 4e7; disjoint from E2e (1e7, 2e7) [V] | A5 |
| `train_500ep.py` | REINFORCE + RLOO, one Adam step per group (lr 0.01, clip 1.0), dual ascent after each step.<br>Checkpoints at updates 0/25/50/75/100/125. Logs per episode and per group.<br>1 h cap; STOP file.<br>**Refuses any non-test config other than 500 = 125 × 4** | A5 |
| `evaluate.py` | Dev-256 × 4 eval noises; three conditions on common noise; R v1.1 primary; J v1.1 descriptive (with the right-hand leakage ratio).<br>Pre-registered verdict logic; S-4 worst-case sensitivity; C-c3 typicality monitor (descriptive).<br>**Refuses any non-test protocol other than dev-256 × 4** | A6 |
| `plots.py` | Training curves (R, r_ah, coordination vs twin, loss, gradient norm, KL, β, parameter norm, c_k, λ_k) and evaluation panels. R and J are never on one panel | deliverable |
| `record_env.py` | Environment, `pip freeze`, and SHA-256 of code, config, Stage 4 inputs, checkpoints and LMDBs | deliverable |
| `tests/run_tests.py`, `tests/config_test.json` | Unit and integration tests. The test config (`test_mode`) is used only by the tests | §5 |

**Episode record (each of the 500):**
- **Identity:** episode, group, i, the clip (split, dataset index, name, L), seed, noise id.
- **Action:** arm-feature validity; ‖μ‖ mean and max, KL per frame, β.
- **log π.**
- **Statistics:** full R v1.1 statistics and validity flags for **both** the controlled sample and the uncoupled twin (all coordinations, dominance, signal stats, both hands' A, m1–m4, extreme fraction).
- **Reward:** r_ah, S-3 flag, c_raw, clipped c, A3 flags, λ used, R, baseline, advantage.

**Group record (each of the 125):**
- **Optimisation:** loss, gradient norm before and after clipping, parameter norm, update norm, β, λ after.
- **Group means:** R, r_ah, coordination (controlled vs twin), c_k; S-3/A3 counts.
- **Cost:** KL, seconds, GPU peak memory.

**Outputs:** episodes JSON and CSV, groups JSON, `run.json` (configuration, flags, train clips, weight checksums start and end, opened splits, runtime, GPU memory, status).

## 2. Audit findings and decisions taken during implementation

| # | Finding | Action / status |
|---|---|---|
| F1 | **Text-embedding batch convention.**<br>Integration run 1, I2 FAILED: the hand sample differed from the E2e A0 dump by 2.4e-3 while the body was bitwise.<br>**Diagnosis [V]:** M-CLIP embeddings of the same text differ by 9.5e-7 depending on batch composition (32 unique texts vs E2e's 64-entry duplicated hand list). The 10-step sampler amplifies this to 2.4e-3 | `common5.Ctx5` now encodes each stream's text list exactly as its batch presents it (body [t₀, t₁, …], hand [t₀, t₀, t₁, t₁, …], chunks of 32 clips in index order).<br>**Rerun: I2 bitwise (0.0) for body and hands.** Run 1 kept as `tests/out/integration_tests_run1.json`.<br>No effect on the design: all conditions share one cache |
| F2 | **Target value.** The frozen record holds τ_ah(R) = **0.4514** (`FROZEN_TARGETS_R0.json`; R0 mean 0.45136). So S-3 = −(1 + τ) = **−1.4514**. The design and your approval wrote the 3-dp display values 0.451 / −1.451 | **Implemented with the frozen value 0.4514 / −1.4514** (never-retune rule). Changing to 0.451 is a one-line change; **please confirm** (§6) |
| F3 | **KL cap.** Analytically KL < 1 nat per frame. At deliberately saturated parameters (U4: W × 1000, b = 30) float32 tanh/sigmoid saturation gives a maximum per-frame value of 1.0000001 | The evaluation check (max KL ≤ 1) could only fail under that saturation, which training cannot reach in practice [I]. Recorded; nothing changed |
| F4 | **Initial controller is nearly uncoupled:** β = 0.0707 and KL ≈ 0.001 nats per frame (mini-runs) | As approved (init β = 0.1 β_max). The "initial" comparison condition is therefore close to uncoupled by design [D] |
| F5 | **The logged loss is not an objective value.** The policy loss −(1/G) Σ A_i log π_i is large (≈ +11) because log π contains −½‖ξ‖². RLOO advantages sum exactly to 0 (U6), so the constant normaliser contributes nothing | Gradient correctness verified (U7, U7b). Reported loss curves will carry this note |
| F6 | **GPU memory:** peak 10.4 GiB allocated (mini-run), higher than E2c (8.5) because both streams' M-CLIP are on the GPU while the cache is built (they move to the CPU afterwards) | Within the 16 GiB card (≈ 15 GiB free) |
| F7 | **Left hand and body unaffected [V]:** the left hand is identical across the three conditions (I5, `left_identical_across_conditions`) | as derived in the design |
| F8 | **Undefined handling in constraints:** a c_k is undefined (→ +1) if either right-hand stream fails R v1.1 validity or has non-finite input, or the term is non-finite or has a non-positive denominator. The extreme-frame term has no denominator, so it is undefined only through stream validity (U8) | the A3 implementation as approved |

## 3. Test results

**Unit tests: 15/15 PASS** (`tests/out/unit_tests.json`, SHA 102289d6…; CPU, no model):

| Test | Result |
|---|---|
| U1 exact log-probability | matches `torch.distributions.Normal`; relative error < 1e-6 |
| U2 β = 0 | μ ≡ 0; ε_R = ξ bitwise |
| U3 padding | μ = 0 on padded frames |
| U4 KL | cap holds (max per frame 1.0000001 at saturation, F3); formula error 1.2e-7 |
| U5 U | orthonormal (2.4e-7) |
| U6 RLOO | advantages sum to 0; b_i independent of R_i |
| U7 score-function estimator (RLOO, 120,000 Monte-Carlo episodes) | **unbiased:** max \|z\| = 3.16 over 1,440 elements; mean z −0.07; parameter-gradient cosine 0.987 |
| U7b | the training-loss gradient equals the analytic estimator (relative 1.2e-7) |
| U8 S-3 / A3 | NaN coordination → −1.4514, flagged; undefined constraints → +1, flagged; a real static right hand is invalid under R v1.1 → S-3 + A3; no episode dropped |
| U9 | dual ascent correct, non-negative |
| U10 | τ = 0.4514 from the frozen JSON; registered thresholds; R v1.1 floors |
| U11 | sampler deterministic; 125 distinct train clips; seed ranges disjoint |
| U12 | arm feature z-scored; static or NaN body → zero feature, flagged |
| U13 | non-500 configs rejected |
| U14 | `test` split refused, never opened |

**Integration tests: 6/6 PASS** (`tests/out/integration_tests.json`, SHA e70df4f2…; GPU). Run 1 was 5/6 (F1; kept).

| Test | Result |
|---|---|
| I1 loader | body and hand batches **identical** to `unrolled_sampler.load_first_batch` (embed, mask, lengths, text, keyframes, names) |
| I2 reproduction | **reproduces the E2e A0 k = 1 dumps bitwise** (body and hands, 32 clips) |
| I3 | β = 0 → controlled right hand bitwise = uncoupled within one call |
| I3b | only `dev` opened; 0 trainable model parameters |
| I4 mini training (8 episodes, test config, run twice in fresh processes) | completed; all required fields present and finite; checkpoints 0/1/2; weights unchanged; only `train` opened<br>**Determinism: the two runs are identical** (max difference 0)<br>1.8–4.6 s per group, 0 S-3 / 0 A3 |
| I5 mini evaluation (2 dev clips × 1 noise, R + J) | completed; left hand identical across conditions; uncoupled ≠ initial; KL(uncoupled) = 0; J statistics present; only `dev` opened |

**Mini-run outputs** (`tests/out/mini_*`) are test artefacts only, not results.

## 4. Hashes (SHA-256, first 16 hex; full values in `experiments/stage5/out/env_preflight/environment.json`)

| Group | File | SHA-256 |
|---|---|---|
| Stage 5 code | `common5.py` | 103ca740dba787f9 |
| | `acms_policy.py` | 8f89a5848b9b92c4 |
| | `rewards.py` | b8af2e7ab722c63e |
| | `episode_sampler.py` | ff26058e3cb862c3 |
| | `train_500ep.py` | e637ec386b46c108 |
| | `evaluate.py` | 602c5efd6066a87a |
| | `plots.py` | 8213acb00160357a |
| | `record_env.py` | 76264ec01a70a40f |
| | `tests/run_tests.py` | eec48760f4eff069 |
| Config | **`config_500ep.json`** | **ccf2112c76ebdfc5** |
| | `tests/config_test.json` | 2ea9a898ee41e86c |
| Stage 4 / upstream, **unchanged** | `unrolled_sampler.py` | d2ad413e928e865c |
| | `metrics.py` (R v1) | 9930224cadd0781d |
| | `validity.py` (v1.1) | edef79b3f83aa0be |
| | `jspace.py` | f664592de79a53e2 |
| | `typicality.py` | 514ccba91d6fec1f |
| | `r0_results.json` | 427dd3631db8f8d6 |
| | `FROZEN_TARGETS_R0.json` (target values unchanged) | 26f28f9a68bc4d53 |
| | `e2c_run.py` | ea6a468f0dab375e |
| | upstream `pose_datasets_lmdb.py` | 440cd965409898a4 |
| | upstream `unet_model.py` | 48ba37234f428517 |
| SignSparK checkpoints | body | bf95bb02802b1c46 (= E2c (ii) record) |
| | hand | 5bb8e407ba2c106a |
| Data | train LMDB `data.mdb` | 7950807733e7c09f |
| | dev LMDB `data.mdb` | 79f37363d0086f99 |

**Environment:** Python 3.12.10; torch 2.10.0+cu128 (CUDA 12.8); NVIDIA RTX A4000 16 GB, driver 595.79; `.venv-infer`; `pip freeze` in `out/env_preflight/pip_freeze.txt`.
- **Flags:** as E2d (fp32, matmul TF32 off, cuDNN TF32 on, benchmark off); `HF_HUB_OFFLINE=1`.

## 5. Final configuration (`config_500ep.json`, SHA ccf2112c…)

| Item | Value |
|---|---|
| Episodes | **500 = 125 groups × 4** |
| Policy | ACMS, r = 4, ±8-frame kernel, KL cap 1 nat/frame; init seed 7000, β₀ = 0.1 β_max, W ~ N(0, 0.1²), c = 0 |
| Optimiser | REINFORCE with an RLOO baseline; Adam lr 0.01, betas (0.9, 0.999); gradient-norm clip 1.0; one update per group |
| Reward | r_ah = −\|coord_ah^R(right) − 0.4514\|<br>S-3: −1.4514<br>constraints art ±10%, jerk ≤ 1.10×, ext +2 points, act \|log ratio\| ≤ log 1.25; clipped to [−1, 1]; A3 undefined → +1<br>dual ascent η = 1.0, λ₀ = 0 |
| Seeds | train clips 5000; train noise 50,000,000 + 1000g + i; eval noise 40,000,000 + 1000j + k |
| Checkpoints | updates 0, 25, 50, 75, 100, 125; **evaluate update 125 only** |
| Evaluation | dev-256 × 4; uncoupled / initial / trained on common noise; bootstrap 2,000, seed 0; the pre-registered rules of design §4 |
| Cap | 3,600 s for training |
| Projected cost [E] | training **≈ 5–8 min** (1.8 s per group after warm-up, plus about 40 s loading); evaluation ≈ 6 min GPU plus ≈ 10–15 min CPU FK (J with leakage re-posing) |

## 6. Exact commands for the run (NOT executed; awaiting your approval)

```
.\.venv-infer\Scripts\python.exe -E -s experiments\stage5\record_env.py --out experiments\stage5\out\env --lmdb
.\.venv-infer\Scripts\python.exe -E -s experiments\stage5\train_500ep.py --config experiments\stage5\config_500ep.json --out experiments\stage5\out\train
.\.venv-infer\Scripts\python.exe -E -s experiments\stage5\evaluate.py --config experiments\stage5\config_500ep.json --ckpt-init experiments\stage5\out\train\checkpoints\update_000.pt --ckpt-final experiments\stage5\out\train\checkpoints\update_125.pt --out experiments\stage5\out\eval --save-dumps
.\.venv-infer\Scripts\python.exe -E -s experiments\stage5\plots.py --train experiments\stage5\out\train --eval experiments\stage5\out\eval --out experiments\stage5\out\plots
```

**Decision needed with the run approval:**
- **F2:** keep τ = 0.4514 (the frozen value, implemented) or use 0.451 as written in the approval.

**Stopped. Awaiting your explicit approval before training.**
