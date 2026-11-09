# E2c (ii): per-clip Gaussian-family capacity experiment

*2026-11-04. Released-checkpoint result, not a paper reproduction. No perceptual, semantic, intelligibility or ASL-quality claim.*

**Verdict (C-c6): NEGATIVE.**
- The mean held-out (ii) right arm–right hand coordination is **0.034** [95% CI 0.007, 0.063].
- The primary typical-only best-of-8×8 level is **0.446**, so the result falls far short.
- The verdict is the same against every comparator (not comparator-sensitive).
- **This is the registered negative outcome for (ii), FM4.** (i) was not run, by your decision.

**Does this support a separate Stage 5 pre-registration? No.** Route A's necessary precondition is not met (§6).

**Labels:** [V] directly measured · [D] mathematical implication / derived · [I] interpretation · [U] unresolved.

---

## 1. Authorisation and scope

**Authorised (2026-11-04):** E2c (ii) only, on dev clips 0–31, under C-c1, C-c2, C-c4, C-c5 and C-c6, with the four implementation corrections you approved before the run (§2.2).

**Not done:**
- E2c (i), E2a, E2b, E2d, E2e;
- any amortised controller;
- training of model weights, any Stage 5 work;
- test data;
- any change to thresholds, frozen R0 targets, metrics or the validity layer.

**Noise draws:** training used only A0 k = 1–4 and held-out evaluation only A0 k = 5–8. No other samples were generated.

## 2. Method

### 2.1 Registered specification (unchanged)

| Item | Specification as run |
|---|---|
| **C-c1 objective** | Right arm–right hand coordination in space R: the registered geodesic metric `e2e/metrics.py` v1.<br>Gradient surrogate: chordal speeds (the E2d statistic). The clip-mean surrogate tracked the clip-mean geodesic objective to ≤ 6e-4 at every iteration [V] |
| **C-c2 benchmark** | Primary: typical-only best-of-8×8 from E2e A0 (k = 1–8; body r × right hand s).<br>Secondary: the all-candidate best-of-8×8, and the dev-256 N = 8 dumps (clips 0–31).<br>The A3 figure 0.408 (256 clips) is context only.<br>**All levels were computed and logged before optimisation began** (log line at 86 s) |
| **C-c4 family** | Per clip: Stiefel U (90×60) and V (60×60) by sign-fixed QR; κ = min(0.95·sigmoid(a), 0.9); BH structure, r = 60.<br>z_R = K ε_body + S ε_R, with K = U diag κ Vᵀ and S = I − U diag(1 − √(1 − κ²)) Uᵀ.<br>Exact KL per frame = −½ Σ log(1 − κ²), which must be ≤ 49.82 for the right hand (≤ 99.64 overall).<br>Init: Gaussian U, V with seed 1000 + j; κ = 0.1 |
| **C-c5 optimisation** | Adam on (U, V, a) only, lr 0.05, 30 iterations.<br>Objective: the mean over training noises A0 k = 1–4; held-out evaluation on k = 5–8.<br>K = 10 Euler steps, gradient checkpointing, **B = 8 contexts per pass**.<br>Model weights: `requires_grad = False`, `eval()` |
| **C-c6 criterion** | Reaches the benchmark if the mean held-out (ii) coordination ≥ the C-c2 level |

### 2.2 Implementation corrections (approved by you before the run; nothing in the procedure changed)

**New file:** `experiments/stage4/e2c/e2c_ii_run.py`.
- It imports every registered component from `e2c_run.py`: the comparators, family init, Stiefel parametrisation, coupling, κ clamp, surrogate, metric, lr, iteration count and the 2 h cap.
- `e2c_run.py` itself is **unchanged** (SHA ea6a468f…).

| # | Correction | Why |
|---|---|---|
| 1 | Part (i) skipped; the verdict comes from (ii) alone | (i) not authorised |
| 2 | 2 clips × 4 noises = 8 contexts per pass (was 4 clips × 4 noises = 16) | C-c5 specifies B = 8. The same per-clip objective and scaling, still one Adam step per iteration |
| 3 | Per-clip logging added (objective per iteration, KL, κ, U, V, checks) | the reporting you asked for |
| 4 | "Best training objective" = the best per-iteration geodesic training objective. Feasibility = the registered κ ≤ 0.9 / KL bound plus finite outputs, recorded rather than enforced | (ii) has no E-3 feasibility rule; none was added |

## 3. Directly measured results [V]

### 3.1 Aggregate (n = 32 clips; 95% clip-bootstrap CIs, 2,000 resamples, seed 0)

| Quantity | Value |
|---|---|
| **Primary level** (typical-only best-of-8×8) | **0.4457** (0 clips without a typical candidate; 7.78 of 8 typical per clip) |
| Secondary: all-candidate best-of-8×8 | 0.4457 (identical: no per-clip best was atypical) |
| Secondary: dev-256 N = 8 dumps | 0.4554 |
| A3 (256 clips, context) | 0.408 |
| Initial training objective (iteration 0, κ = 0.1) | 0.052 [0.016, 0.094] |
| **Best training objective** (in-sample, k = 1–4) | **0.737** [0.695, 0.777] |
| **Mean held-out objective (k = 5–8)** | **0.034 [0.007, 0.063]** |
| Uncoupled A0 on the same held-out noises | 0.036 [0.011, 0.063] |
| Held-out gain vs uncoupled (paired) | **−0.003 [−0.017, +0.012]**; 18 of 32 clips positive; Wilcoxon p = 0.83 |
| Held-out minus primary level, clip-wise | −0.412 [−0.479, −0.353] |
| Generalisation gap (best train − held-out) | 0.704 [0.650, 0.759] |
| **C-c6 reached?** primary / all-candidate / dev-256 | **no / no / no** (not comparator-sensitive) |
| Split by length: L < 100 (n = 11) | held-out 0.002 vs level 0.565 |
| Split by length: L ≥ 100 (n = 21) | held-out 0.050 vs level 0.384 |

**Per-clip distributions:**
- **Held-out:** min −0.157, p25 −0.029, median 0.034, p75 0.085, max 0.188.
  - **0 of 32 clips** reach their own primary level; the smallest shortfall is 0.088.
  - Mean held-out by noise: k5 0.023, k6 0.008, k7 0.041, k8 0.063.
- **Best training objective:** min 0.475, median 0.749, max 0.957. It exceeds the clip's primary level in **32 of 32 clips**, but in-sample only.

**Training trajectory (mean over clips):** 0.052 → 0.284 (iteration 5) → 0.394 (10) → 0.498 (15) → 0.591 (20) → 0.678 (25) → 0.737 (29).
- The best iterate was the last one in 30 of 32 clips: **in-sample, the objective was still rising when the 30-iteration budget ended.**

### 3.2 Family parameters, KL and constraints

| Quantity | Value |
|---|---|
| Learned κ, mean per clip | 0.185–0.287 (mean 0.257) |
| Learned κ, largest single value | 0.361 |
| κ entries at the 0.9 clamp | **0** of 1,920 |
| KL per frame (right hand), final | 1.19–2.71 nats (mean 2.27) |
| KL bound (right hand / overall) | 49.82 / 99.64. **The bound was never close to binding.** |
| Max Stiefel orthogonality error | 7.2e-7 |
| Non-finite outputs or gradients | 0 |
| Feasible (κ ≤ 0.9, KL ≤ bound, finite) | **32 / 32**; no constraint violations |

**Per-clip table** (L = length; init = iteration-0 training objective; best = best training objective; held = held-out mean; unc = uncoupled A0 held-out; level = primary C-c2 level; KL = nats/frame; κ̄ = mean κ). No clip reaches its level.

| clip | L | init | best | held | unc | level | KL | κ̄ |
|---|---|---|---|---|---|---|---|---|
| 0 | 157 | +0.068 | 0.739 | +0.065 | +0.053 | 0.369 | 1.99 | 0.239 |
| 1 | 56 | +0.078 | 0.905 | +0.022 | +0.097 | 0.813 | 2.02 | 0.246 |
| 2 | 139 | −0.008 | 0.721 | +0.142 | +0.072 | 0.312 | 2.46 | 0.269 |
| 3 | 171 | +0.009 | 0.681 | +0.000 | −0.008 | 0.288 | 1.76 | 0.221 |
| 4 | 189 | +0.039 | 0.610 | +0.052 | +0.070 | 0.386 | 1.86 | 0.235 |
| 5 | 99 | +0.002 | 0.816 | −0.048 | −0.077 | 0.440 | 2.61 | 0.277 |
| 6 | 116 | +0.319 | 0.889 | +0.126 | +0.102 | 0.710 | 2.15 | 0.252 |
| 7 | 263 | −0.107 | 0.475 | −0.055 | −0.072 | 0.321 | 2.71 | 0.286 |
| 8 | 212 | −0.051 | 0.626 | −0.066 | +0.002 | 0.381 | 2.50 | 0.272 |
| 9 | 67 | −0.135 | 0.804 | −0.073 | −0.148 | 0.368 | 2.46 | 0.269 |
| 10 | 248 | +0.105 | 0.757 | +0.034 | +0.000 | 0.341 | 2.53 | 0.276 |
| 11 | 84 | +0.103 | 0.737 | +0.042 | +0.075 | 0.660 | 1.54 | 0.210 |
| 12 | 71 | −0.012 | 0.889 | −0.032 | −0.037 | 0.701 | 2.22 | 0.254 |
| 13 | 177 | +0.113 | 0.740 | +0.023 | +0.026 | 0.309 | 1.95 | 0.239 |
| 14 | 83 | +0.050 | 0.765 | −0.005 | −0.043 | 0.419 | 2.25 | 0.256 |
| 15 | 85 | −0.055 | 0.816 | +0.009 | +0.032 | 0.522 | 2.47 | 0.267 |
| 16 | 102 | +0.057 | 0.767 | −0.007 | +0.004 | 0.362 | 2.36 | 0.260 |
| 17 | 47 | +0.037 | 0.933 | +0.071 | +0.040 | 0.568 | 2.10 | 0.249 |
| 18 | 219 | +0.020 | 0.599 | −0.037 | −0.020 | 0.376 | 2.31 | 0.261 |
| 19 | 120 | +0.009 | 0.685 | +0.126 | +0.099 | 0.424 | 2.67 | 0.281 |
| 20 | 220 | +0.045 | 0.679 | −0.027 | −0.026 | 0.350 | 2.63 | 0.281 |
| 21 | 71 | +0.188 | 0.861 | +0.036 | +0.027 | 0.432 | 2.14 | 0.249 |
| 22 | 159 | −0.051 | 0.768 | −0.057 | +0.044 | 0.479 | 2.55 | 0.274 |
| 23 | 125 | −0.024 | 0.662 | +0.099 | +0.156 | 0.425 | 2.71 | 0.287 |
| 24 | 304 | +0.074 | 0.544 | +0.177 | +0.151 | 0.325 | 2.11 | 0.246 |
| 25 | 174 | +0.096 | 0.610 | +0.080 | +0.075 | 0.343 | 1.69 | 0.220 |
| 26 | 132 | +0.215 | 0.785 | +0.127 | +0.173 | 0.507 | 2.67 | 0.277 |
| 27 | 28 | +0.419 | 0.957 | −0.157 | −0.080 | 0.851 | 1.19 | 0.185 |
| 28 | 304 | +0.038 | 0.538 | +0.188 | +0.191 | 0.275 | 2.16 | 0.251 |
| 29 | 252 | +0.034 | 0.666 | +0.034 | +0.003 | 0.265 | 2.70 | 0.283 |
| 30 | 78 | −0.087 | 0.799 | +0.155 | +0.154 | 0.437 | 2.69 | 0.282 |
| 31 | 146 | +0.079 | 0.771 | +0.037 | +0.028 | 0.505 | 2.42 | 0.267 |

**Per-clip structure:**
- Spearman correlation of held-out with uncoupled held-out: 0.87. The held-out value is essentially each clip's uncoupled value.
- Spearman correlation of the generalisation gap with L: −0.73. Shorter clips overfit more.
- Spearman correlation of KL with held-out: −0.05.
- Full per-clip records, including the 30-iteration histories, are in `e2c_ii_per_clip.json`. U, V and κ are in `e2c_ii_family_params.npz`.

## 4. Mathematical implications [D]

1. **The held-out estimate is unbiased for the learned parameters.**
   - For fixed learned parameters θ_j, the held-out mean over k = 5–8 is an unbiased estimate of that θ_j's expected objective over fresh noise.
   - The in-sample value (0.737) is an optimistically biased estimate: θ_j was chosen on k = 1–4.
   - The 0.70 gap is therefore an overfitting gap, not a sampling artefact of the held-out set; its CI excludes 0 by a wide margin.
2. **The amortisation bound.**
   - An amortised controller h_φ(c, L) inside the same Gaussian family is, for each clip, one member of the per-clip family. Its expected objective on fresh noise is therefore ≤ the per-clip population optimum sup_θ E_ε[obj].
   - (ii) estimated that optimum with a 4-noise sample-average and 30 Adam steps, and obtained **no detectable held-out gain over uncoupled** (−0.003 [−0.017, 0.012]).
3. **What the bound does not license.** (ii) is a lower estimate of the population optimum, not an upper bound. A per-clip optimum fitted on many noises could exceed it.
   - The only other evidence on the population optimum is E2e. Its random-orientation BH conditions at κ = 0.9 (far larger KL) gave held-out-type gains of at most +0.037 (R, seed 2).
   - Reaching the C-c2 level from the uncoupled mean (≈ 0.036) would need a **mean** gain of about **+0.41**.
   - That is about 11× the largest gain observed in any E2e or E2c (ii) condition [V for the figures; D for the ratio].
4. **The KL bound was not the limiting factor** (KL ≤ 2.71 ≪ 49.82; no κ at the clamp). Within this family and budget, the negative result cannot be attributed to the registered KL constraint.
5. **The benchmark compares unlike quantities.** It is a per-clip *maximum over 64 candidates*, which includes selection on the held-out noises themselves. (ii) is a *mean over noises* for fixed parameters, which is the registered like-for-like comparison of what a deployed controller would deliver. Only the in-sample objective (0.737) exceeds the benchmark, and it is not a valid comparison: it too is selected on the noises it is evaluated on.

## 5. Interpretation and limitations [I]

**Interpretation:**
- **The optimiser found realisation-specific, not clip-specific, coupling.**
  - With about 9,060 free parameters per clip and 4 noise draws, a small coupling (κ ≈ 0.26, about 2 nats per frame) was enough to drive the in-sample objective to 0.74.
  - On fresh body/hand noise the same linear coupling gave nothing.
  - A natural reading [I]: whether a hand-noise direction helps arm–hand coordination depends on the particular body motion that ε_body produces, through the non-linear 10-step sampler. A fixed linear map K from ε_body cannot encode that across draws.
  - This agrees with E2e (small, orientation-dependent transmission) and with the fact that the sampler is highly sensitive to specific noise directions in-sample.

**Limitations:**
1. **4 training noises per clip** (as registered) makes overfitting likely. A larger noise sample per clip might regularise toward a transferable coupling. That would be a **new design**, not a registered E2c (ii) variant, and it was not run.
2. **The 30-iteration budget** ended with the in-sample objective still rising. More iterations would most plausibly widen the overfitting gap; this is untested [U].
3. **Small sample:** n = 32 dev clips and 4 held-out noises per clip. The CIs are clip-bootstrap only; noise-level variance within clips is not modelled separately.
4. **(i) was not run.** The registered two-arm C-c6 negative outcome ("both fail") is therefore evaluated on (ii) only, as you instructed. (i) concerns unrestricted per-sample noise optimisation, not the family an amortised controller would use, so it does not bear on route A's precondition [I].
5. **Run determinism:** the run used `cudnn_deterministic = false` and cuDNN TF32 on (the same flags as E2d/E2e). Bitwise reruns are not guaranteed; the differences would be far below the effect sizes here.
6. **M-CLIP loading:** the upstream loader queried the Hugging Face hub for the public M-CLIP model, giving Xet/symlink warnings in `run.err`. The same behaviour appears in the Stage 3 baseline log. No project data was sent, and M-CLIP is identical in all checkpoints (E2d-H).

## 6. Conclusion for the route-A decision

- **Measured:** the M-C Gaussian family, optimised per clip as registered, does **not** reach the best-of-8×8 level on held-out noise. It does not improve on uncoupled sampling at all, while staying feasible and far inside the KL bound.
- **Implication:** by the amortisation bound, an amortised h_φ(c, L) in this family has no measured headroom to learn. **Route A's necessary precondition is not met.**
- **Recommendation:** **the results do not support proceeding to a Stage 5 pre-registration for an amortised M-C controller.** The open options are yours:
  - route B, a new problem-selection revision;
  - route C, close P1a with H0, now supported by both E2e (fixed orientations) and E2c (ii) (optimised per clip);
  - a separately pre-registered many-noise per-clip capacity test (limitation 1), if you judge the 4-noise design inconclusive. I do **not** recommend it as a route to training: even its optimistic ceiling from E2e (+0.04) is about 10× short of the benchmark.
- Nothing further was run. **Stopped for your review.**

## 7. Reproducibility

| Item | Value |
|---|---|
| Command | `.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2c\e2c_ii_run.py --dumps experiments\stage4\e2e\dumps --out experiments\stage4\e2c\out_ii` (via `Start-Process`; stdout → `run.log`, stderr → `run.err`) |
| Environment | `.venv-infer`, torch 2.10.0+cu128, float32, NVIDIA RTX A4000 16 GB<br>matmul TF32 off, cuDNN TF32 on, cudnn.benchmark off, deterministic off<br>all modules in eval() |
| Model weights | trainable parameters **0**; parameter checksum before = after (**unchanged**) |
| Checkpoint SHA-256 | body `bf95bb02…a380`; hand `5bb8e407…16c2` (`models/SignSparK/{body,hand}/ema_0.9999_200000.pt`) |
| Input SHA-256 | A0 k01–k08, the dev-256 dumps, `e2c_run.py` (ea6a468f…), `e2c_ii_run.py` (fd53cff3…), `typicality.py`, `gpu_common.py`, `metrics.py` (9930224c…), `unrolled_sampler.py`: all listed in full in `e2c_ii_repro.json` |
| Seeds | noise: E2e `base_noise('A0', j, k)` = 10,000,000 + 1000·j + k; family init: torch seed 1000 + j; bootstrap seed 0 |
| Runtime | 1,614 s (26.9 min): hashing 29 s, comparators to 86 s, 30 iterations ≈ 1,510 s, held-out ≈ 15 s |
| GPU memory | peak allocated 8.53 GiB, peak reserved 8.70 GiB |
| Exit status | 0; status "completed"; stderr has only library warnings |
| Outputs (`experiments/stage4/e2c/out_ii/`) | `e2c_ii_per_clip.json` (d1f60ac4…), `e2c_ii_aggregate.json` (ce7d1b74…), `e2c_ii_repro.json` (6c6c9bfc…), `e2c_ii_family_params.npz` (355b96aa…), `run.log`, `run.err` |
