# E2 execution checklist (Stage 4 rev. 4.0)

*2026-11-03.*

**Status: none of the steps below is authorised.**
- Each step needs your explicit go-ahead naming that step.
- I stop and report after each step.
- Approving one step's go-ahead authorises only that step.
- **Approval of the specification or plan, including "approval in principle" in report §19, is never execution authorisation.**

The specifications are in `research/STAGE4_REPORT.md` (rev. 4.0), §15. Where this checklist and the report differ, **the report governs**.

## Common rules (every step)

| # | Rule |
|---|---|
| C1 | Dev clips only: the first 32 of the dev-256 subset (E2 steps), with dev references only. **No test data.** R0 uses train references only |
| C2 | Checkpoints read-only and SHA-verified against `models/MANIFEST.json` before the run; no weight updates; no training or fine-tuning of any network; no optimiser step on any parameter in E2d or E2e |
| C3 | One numerical implementation for every arm: fp32, eval(), the same device, the same TF32/cuDNN flags (recorded) |
| C4 | Fixed, recorded seeds; noise lists shared across conditions (CRN) |
| C5 | Upstream code in `third_party/` unmodified. Adaptations live in `experiments/common` or `experiments/stage4/e2*/` |
| C6 | Environments: `.venv-infer` (GPU steps), `.venv-render` (CPU joint-space steps). Python 3.15 and original data untouched |
| C7 | Every generation result is labelled "released-checkpoint, not a paper reproduction" (R10). Every claim is typed G / M (report §0.2); no perceptual claim |
| C8 | Wall-clock cap per step; on reaching it I stop and report what was completed |
| C9 | No automatic switch to the residual controller or any alternative if a step fails (report §15.2) |
| C10 | GPU shared with the display: free memory is recorded at start; the 14 GiB gate refers to peak *reserved* memory |

## Order and gates

| Order | Step | Needs before it | Gate to pass | Cap | Report file |
|---|---|---|---|---|---|
| 1 | **E2d** | your go-ahead | T0 pass; a K = 10 configuration ≤ 14 GiB | 45 min | `research/stage4/E2D_REPORT.md` |
| 2 | **E2e** (+ save dumps) | E2d report + your go-ahead | report §15.3.1 stop rules | 1.5 h | `research/stage4/E2E_REPORT.md` |
| 2b | **E2e-J** (non-gating) | E2e dumps + your explicit go-ahead for E2e-J (it may be stated in the same message as the E2e go-ahead) | FK health only | 1 h | appended to the E2e report |
| 3 | **E2a** | E2e report + your go-ahead | finite gradients; norm ratio ≤ 10³ | 1 h | `E2A_REPORT.md` |
| 4 | **E2b** | E2a report + your go-ahead | none (non-gating) | 1 h | `E2B_REPORT.md` |
| 5 | **E2c** | E2b report + your go-ahead | report §15.2 | 2 h | `E2C_REPORT.md` |
| any time before Stage 5 | **R0** (reference-only) | your go-ahead | data integrity | 2 h CPU | `R0_REPORT.md` |

---

## Step 1: E2d (next executable step), ready to start on your go-ahead

**Purpose:**
- verify that a differentiable unrolled 10-step sampler reproduces the released sampler;
- measure the real memory and time of one M-C gradient step;
- check whether one cached M-CLIP embedding serves all streams.

**Pre-run (no GPU):**
- [ ] Your go-ahead for E2d recorded in `RESEARCH_LOG.md`.
- [ ] Checkpoint SHA-256 values match `models/MANIFEST.json`.
- [ ] `.venv-infer` package versions match `requirements-infer.lock.txt`.
- [ ] Code reading: confirm how to inject a given noise tensor into upstream `decode` without modifying `third_party/`. Candidates:
  - a wrapper in `experiments/common`;
  - a patched RNG at runtime.

  If injection is impossible without modifying upstream code, **stop and report** (blocker).
- [ ] Write the harness `experiments/stage4/e2d/unrolled_sampler.py`:
  - grid t_k = k/10, h = 0.1;
  - the same `model(x, t, y, obs_x0, obs_mask)` call;
  - the length mask;
  - optional per-step `torch.utils.checkpoint` (non-reentrant).

  This is a sampler harness, **not a controller**: no learnable parameters.

**Runs:**

| ID | What | Data | Rule |
|---|---|---|---|
| E2d-T0a | Harness (no_grad) vs upstream `decode`, identical noise | 32 clips, k = 1; body, left hand, right hand | max \|Δx\| ≤ 1e-4 per stream. **Fail ⇒ stop** |
| E2d-T0b | Harness determinism: two runs, same noise | same | bit-identical (max \|Δ\| = 0) |
| E2d-T0c | With per-step checkpointing vs without | 4 clips | outputs bit-identical |
| E2d-F | Record dtype, device, `torch.backends.cuda.matmul.allow_tf32`, `torch.backends.cudnn.allow_tf32`, `model.training` for every call | — | logged; any `training == True` ⇒ stop |
| E2d-H | SHA-256 of the M-CLIP sub-weights inside the body, hand and face checkpoints (read-only) | checkpoints | identical ⇒ one cached embedding; different ⇒ per-stream embeddings (recorded, no stop) |
| E2d-M | Peak reserved memory and time of **one forward + backward** pass: ε̃ = identity transform of ε⁰ with a dummy leaf tensor (κ = 0, σ = 1) requiring grad; a differentiable rotation-space statistic as the scalar output; per-step checkpointing; B ∈ {1, 2, 4, 8} contexts (body B + hands 2B). **No optimiser, no parameter update** | dev clips | some B with peak ≤ 14 GiB; gradient finite. **No configuration fits ⇒ stop** |
| E2d-G | Per-Euler-step input-gradient norms from E2d-M at the largest feasible B | — | logged (feeds E2a); non-finite ⇒ stop |

**Outputs:**
- `experiments/stage4/e2d/out/{t0.json, flags.json, mclip_hash.json, memory.json, grad_norms.json}`;
- the report `research/stage4/E2D_REPORT.md` with measured numbers replacing the report §11 estimates [E].

**Runtime [E]:**
- model loads ≈ 2–3 min;
- T0 ≈ 200 sequences ≈ 1–2 min;
- memory probe 4 configurations ≈ 5–10 min.
- **Total ≈ 15–20 min; cap 45 min.**

**Stop after E2d.** I report and wait for your E2e go-ahead.

---

## Step 2: E2e (report §15.3–15.4; unchanged in rev. 4.0 except dump saving)

**Pre-run:**
- [ ] E2d passed, and your go-ahead was given.
- [ ] Harness = the E2d harness (one implementation).
- [ ] Synthetic T1 null calibration margins recorded (no model).

**Run order (report §15.3.1; frozen):**

| Step | Action | Stop / branch |
|---|---|---|
| 0 | t*₂₅₆ + 95% CI from dev-256 references; branch R1/R2/R3 and δ_S₂ = min(0.05, max(0.025, \|t*₂₅₆\|/4)); T1 synthetic margins. **No generation** | not computable ⇒ stop; R3 ⇒ SS removed |
| 1 | T0 (a)–(c) | any failure ⇒ stop |
| 2 | A0, A0′ at n = 8 noises per clip; T2 calibration half-width h | — |
| 3 | Calibration loop: n ∈ {8, 16, 32} on A0/A0′ only; fix n* (or n* = 32 with "calibration-inconclusive") | n* recorded before step 4 |
| 4 | Gate conditions BH-r60-κ0.9-seed0, LR-r90-κ0.9-seed0 at n*; T1, T2, T5-A | T1 fail, T2 fail/straddle, or T5-A fail ⇒ stop. Calibration-inconclusive ⇒ continue with theory-conditional wording |
| 5 | Remaining BH conditions (n = 8) | T5-A fail ⇒ stop (restates the registered T5-A rule; P-9 wording consistency) |
| 6 | Remaining LR conditions (n = 8) | T5-A fail ⇒ stop (same) |
| 7 | SS conditions (n = 8), unless R3 | — |
| — | **Rev. 4.0:** save every generated sample's rotations to `experiments/stage4/e2e/dumps/` (≈ 1.2–2.2 GB) | write failure ⇒ stop |

**Tests (report §15.3, unchanged):**
- T0, T1, T2;
- T3, T4 (rotation space);
- T5-A (TOST on S₂ against ±δ_S₂);
- T5-B (D-a, D-b, D-c in rotation space);
- T6.

D-d does not exist (rev. 4.0).

**Stop after E2e.** If T3 and T4 both fail, I present options (a)–(e) of report §15.2 and do nothing automatically.

## Step 2b: E2e-J (report §15.3.2; non-gating)

- [ ] Run in `.venv-render` on the saved E2e dumps.
- [ ] Use the E0.4 FK setup (`flip_left_hand=True`).
- [ ] Compute T3-J and T4-J (Δ vs A0, with CIs) and T5-J (D-a/D-b with t*₃₂^J), plus the R-vs-J agreement table.
- [ ] FK health check (finite; bone lengths within 1e-4 relative).

Nothing here changes any E2e outcome.

## Step 3: E2a (report §15.2)

- K ∈ {1, 2, 4, 10}: output agreement and ∇_ε r cosine vs K = 10, with the per-step gradient-norm profile.
- Optional bf16 agreement **for both arms** (speed-profile correlation ≥ 0.99, gradient cosine ≥ 0.95) before any precision change.
- **Stop:** non-finite gradients, or a norm ratio across steps > 10³.

## Step 4: E2b (report §15.2)

- Time-shift equivariance, δ ∈ {±4, ±8, ±16} frames.
- Non-gating; informs a low-dimensional action ablation only.

## Step 5: E2c (report §15.2)

- (i) Per-sample noise optimisation (N4), constrained to the base-typical set C-c3 (amendment 2; campaign plan §2a, pending approval):
  - finiteness plus N/M/V/A/P, checked on the float32 model-input array;
  - enforcement E-1 to E-5;
  - start: A0 hand noise k = 1, with the body fixed at A0 k = 1.
- Comparator C-c2:
  - typical-only best-of-8×8 from E2e A0 is primary;
  - the all-candidate values are secondary;
  - a disagreement is reported as "comparator-sensitive".
- Results are also split at L < 100 / ≥ 100 (D1).
- (ii) Per-clip optimisation of the Gaussian-family parameters (family capacity).

These are optimisations of noise / family parameters **per clip** on dev, not training of a policy network. The cap applies.

## R0: reference-only targets (report §6.0 rule iv; new in rev. 4.0)

- Train references only (29,630 clips), read-only. **No generation, no GPU.**
- **Space R:**
  - τ*_ah^R(L), τ*_ah^R(R), τ*_lr^R, t*^R;
  - each with a 95% clip-bootstrap CI.
- **Space J** (`.venv-render`, E0.4 FK):
  - τ*_ah^J(L), τ*_ah^J(R), τ*_lr^J, t*^J, with CIs;
  - dev reference values of the not-yet-computed J statistics (left-side arm–hand, L–R) for descriptive comparison.
- **U-A11:** numerical mirror-symmetry check of the SMPL-X left/right hand rest geometry (max \|p_L − M p_R\|).
- **V-R3 synthetic checks:** static pose, mean pose and shared-spike sequences evaluated with every reward statistic.
- **Output:** `R0_REPORT.md`. The targets are frozen there before Stage 5.

## Not in any step

- Stage 5;
- training of a controller network;
- fine-tuning;
- architecture changes;
- test-set runs;
- human evaluation (E1, deferred indefinitely);
- GPU rental;
- author or rater contact.
