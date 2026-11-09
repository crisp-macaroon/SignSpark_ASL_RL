# E2e report: Gaussian noise-controller technical feasibility (Stage 4 rev. 4.0 §15.3–15.4)

*Run 2026-11-03, within the authorised consolidated campaign.*

**Conclusion: FAIL, by the registered stop gate FM13** (T3 and T4 both fail).
- **Implementation and theory checks pass:** T0, T1, T2 (calibration-inconclusive, so theory-conditional) and T5-A (no fail).
- **Under §5, the campaign stopped here.** E2e-J, E2a, E2b and E2c were not run. R0 was paused (resumable).
- There was **no automatic switch** to any other controller.

**Labels:**
- Released-checkpoint results, **not** a paper reproduction (R10).
- Rotation-space (R) results only; there is no joint-space (J) analysis because E2e-J did not run.
- No perceptual, preference, semantic or intelligibility claim.

## 1. Objective (§15.3)

Does the Gaussian controller, as derived:
- (i) behave as the mathematics says (marginals; Theorem 4 parity)?
- (ii) transmit fixed body–hand (T3) and left–right (T4) noise coupling to output timing?
- (iii) let side scales reach dominance levels D-a to D-c (T5-B)?

## 2. Code, configuration, data

| Item | Value |
|---|---|
| Code | `experiments/stage4/e2e/e2e_run.py` (orchestrator), `noise_transform.py`, `metrics.py`, `stats.py`; sampler `experiments/stage4/e2d/unrolled_sampler.py` (E2d-validated) |
| Preflight decisions | P-1 to P-14 as approved (`E2E_PREFLIGHT_DECISIONS.md`, `E2E_PREFLIGHT_CHANGELOG.md`); self-test 42/42 |
| Command | `.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2e\e2e_run.py --out experiments\stage4\e2e\out --dumps experiments\stage4\e2e\dumps` (`HF_HOME=models\hf_cache`, `WANDB_MODE=disabled`, `HF_HUB_OFFLINE=1`) |
| Clips | dev-256 clips 0–31 (`-d5dN54tH2E_0-1-rgb_front` … `-f1_kdl050s_27-1-rgb_front`), GF, oracle length; names and lengths checked against the dev-256 dump at run time |
| Checkpoints | SHA-256 re-verified against `models/MANIFEST.json` at campaign start (body, hand, face: match) |
| Seeds | noise = 10,000,000 (A0) or 20,000,000 (A0′) + 1000·j + k; (U, V) orientation seeds 0/1/2; bootstrap seed 0 (2,000 clip resamples); T1 null seed 777 |
| Numerics | fp32; eval() (F5 checked); matmul TF32 off; cuDNN TF32 on; benchmark off; RTX A4000 |
| Runtime | 1,726 s (28.8 min) of the 1.5 h cap |
| Peak GPU memory | **not logged by `e2e_run.py` (a deviation).** E2d measured the same harness at ≤ 8.8 GiB; no OOM occurred |
| Outputs | `experiments/stage4/e2e/out/results.json`; `run.log`; dumps `experiments/stage4/e2e/dumps/` (224 files, 1.6 GB: all 16 conditions, A0/A0′ k = 1–32, gate conditions k = 1–32, the others k = 1–8) |

**Deviation (launch 1):** the first launch crashed before any work. `shutil.disk_usage` was called on the empty anchor of a relative path. Nothing was generated or written; the crash log is kept as `experiments/stage4/e2e/run_launch1_crash.log`. The fix resolves the path, and the run was relaunched unchanged otherwise.

## 3. Results

### 3.1 Step 0 (references only)

| Quantity | Value | Rule | Outcome |
|---|---|---|---|
| t*₂₅₆ | **−0.310**, 95% CI [−0.345, −0.275] | R1 if \|t\| ≥ 0.20 and the CI excludes 0 | **R1**; δ_S₂ = 0.05 |
| T1 (a) analytic, 16 conditions | all diagonal blocks = I, λ_min, log-det | pass | **PASS** |
| T1 null calibration (P-1, new procedure), both gate conditions | widened in 2 rounds: mean 0.03 → **0.035**; var, corr, cross unchanged; **lag-1 stays at the registered 0.03**; family-wise null rate 0.9% | < 1% | calibrated |

### 3.2 T0 (step 1)

| Check | Value | Rule | Outcome |
|---|---|---|---|
| Harness vs upstream `decode`, A0 k = 1 | max \|Δ\| body 0.0, hand 0.0 | ≤ 1e-4 | PASS |
| BH body regenerated vs A0 body | 0.0 | ≤ 1e-5 | PASS |
| F2 shared L/R inputs; F5 eval | true; no module in training mode | — | PASS |

### 3.3 T2 calibration (steps 2–3)

| n per clip | h (max 90% CI half-width, A0′ vs A0) |
|---|---|
| 8 | 3.83% |
| 16 | 3.20% |
| 32 | **1.88%** |

h stayed above 1.5% at 32 noises, so under the registered rule **n\* = 32 and T2 is "calibration-inconclusive"**: the run continues with theory-conditional wording (§15.4.4). A0's T5-A half-width at n = 8 was 0.038, below 0.8·δ_S₂ = 0.040.

### 3.4 Gate conditions at n* = 32 (step 4)

| Test | BH-r60-κ0.9-seed0 | LR-r90-κ0.9-seed0 |
|---|---|---|
| T1 (b)–(f), statistic vs margin | mean 0.0224 ≤ 0.035; var 0.0355 ≤ 0.05; corr 0.0207 ≤ 0.035; cross 0.0196 ≤ 0.035; lag-1 0.0226 ≤ 0.03: **PASS** | 0.0260, 0.0355, 0.0201, 0.0199, 0.0245: **PASS** |
| T2, eight means, 90% CI ⊂ [0.95, 1.05] | all eight pass (e.g. right articulation 1.016 [1.008, 1.024]); this run's h = 1.63%: **PASS** | all eight pass (left hand exactly 1.000, unchanged by construction): **PASS** |
| T5-A, S₂: μ, 90% CI vs ±0.05 | 0.0044 [−0.018, 0.028]: **pass** | −0.0018 [−0.022, 0.019]: **pass** |
| T5-A, S₁: 90% CI vs [0.95, 1.05] | 1.006 [0.986, 1.028]: **pass** | 1.001 [0.985, 1.019]: **pass** |
| S₄ / S₃ (descriptive; S₃ caveat) | 0.49 / 1.083 | 0.49 / 1.073 |
| Energy distance (non-gating) | 0.0065, p = 0.46 | 0.0035, p = 1.00 |

**Wording (§15.4.4):** per-stream preservation is "exact by Theorem 3 *conditional on* its assumptions, checked as listed (F4 by code reading only); the empirical eight-metric consequence check was inconclusive at the calibration level". The gate conditions' own eight TOSTs passed.

### 3.5 T5-A, remaining BH/LR conditions (steps 5–6; n = 8; any fail ⇒ stop)

| Condition | μ [90% CI] | S₂ | S₁ |
|---|---|---|---|
| BH-r60-κ0.3-seed0 | −0.029 [−0.073, 0.012] | inconclusive | pass |
| BH-r60-κ0.6-seed0 | −0.009 [−0.050, 0.031] | pass | pass |
| BH-r60-κ0.9-seed1 | 0.020 [−0.015, 0.055] | inconclusive | pass |
| BH-r60-κ0.9-seed2 | 0.010 [−0.020, 0.040] | pass | pass |
| BH-arm12-κ0.9 | −0.011 [−0.049, 0.022] | pass | pass |
| LR-r90-κ0.6-seed0 | −0.015 [−0.055, 0.026] | inconclusive | pass |
| LR-r90-κ0.9-seed1 | 0.012 [−0.040, 0.062] | inconclusive | inconclusive |
| LR-r90-κ0.9-seed2 | −0.003 [−0.043, 0.035] | pass | pass |

**No fail.** Inconclusive results are reported, not treated as passes. This is consistent with the Theorem 4 parity prediction.

### 3.6 T3 (body–hand transmission) and T4 (L–R transmission), rotation space

Δ is the condition minus A0, paired by clip over the first 8 noises (P-10), with 95% CI.

| Condition | Δ arm–R-hand | Δ arm–L-hand | Δ L–R | KL per sample (nats) |
|---|---|---|---|---|
| BH-r60-κ0.3-seed0 | 0.002 [−0.007, 0.012] | 0.010 [−0.001, 0.020] | 0.016 [0.003, 0.029] | 831 |
| BH-r60-κ0.6-seed0 | 0.009 [−0.009, 0.028] | 0.017 [−0.003, 0.036] | 0.022 [0.003, 0.041] | 3,931 |
| **BH-r60-κ0.9-seed0** | **0.017 [−0.014, 0.049]** | **0.022 [−0.006, 0.048]** | 0.049 [0.023, 0.075] | 14,629 |
| BH-r60-κ0.9-seed1 | 0.033 [0.006, 0.061] | −0.020 [−0.044, 0.004] | 0.035 [0.009, 0.060] | 14,629 |
| BH-r60-κ0.9-seed2 | 0.037 [0.013, 0.062] | −0.001 [−0.032, 0.030] | 0.031 [0.006, 0.056] | 14,629 |
| BH-arm12-κ0.9 | 0.010 [−0.006, 0.026] | 0.018 [0.001, 0.034] | −0.011 [−0.029, 0.006] | 2,926 |
| LR-r90-κ0.6-seed0 | −0.006 [−0.029, 0.017] | 0 (exact) | 0.018 [−0.004, 0.042] | 2,948 |
| **LR-r90-κ0.9-seed0** | −0.012 [−0.050, 0.023] | 0 (exact) | **0.035 [0.006, 0.066]** | 10,972 |
| LR-r90-κ0.9-seed1 | −0.010 [−0.044, 0.021] | 0 | 0.024 [−0.002, 0.048] | 10,972 |
| LR-r90-κ0.9-seed2 | −0.004 [−0.035, 0.027] | 0 | 0.037 [0.016, 0.061] | 10,972 |

| Registered criterion | Result | Outcome |
|---|---|---|
| **T3 transmission:** Δ(κ0.9-seed0) ≥ 0.05 on ≥ 1 side and CI lower bound > 0 | R 0.017, L 0.022; neither CI excludes 0 | **FAIL**: verdict "no transmission on either side" (existence false, bilateral false) |
| T3 monotone in κ (tolerance 0.01) | R 0.002 → 0.009 → 0.017; L 0.010 → 0.017 → 0.022: monotone on both sides | reported (no transmitting side to judge) |
| T3 orientation robustness | per side: R 0/3, L 0/3 seeds meet the criterion. Seeds 1 and 2 give significant right-side Δ (0.033, 0.037) below 0.05 | reported |
| T3 efficiency (arm12 / r60 per KL nat) | right 2.83, 95% CI [−25.4, 22.7]; left 3.96 [−13.9, 24.9]: uninformative | descriptive |
| T3 specificity: max \|Δ arm–hand\| under LR ≤ 0.02 | 0.012 | pass |
| **T4 transmission:** Δ(LR-κ0.9-seed0) ≥ 0.05 and CI lower bound > 0 | 0.035 [0.006, 0.066] | **FAIL** (positive, below the registered 0.05) |
| T4 orientation robustness | 0/3 | reported |
| T4 induced under BH (reported only) | BH-κ0.9-seed0 0.049 [0.023, 0.075] | reported, not gating |
| Descriptive at n* = 32, gate conditions (P-10) | BH: R 0.021, L 0.016; LR: L–R 0.023 | descriptive; no change to the verdict |

**FM13 (T3 and T4 both fail) ⇒ the registered stop gate.**

### 3.7 T5-B dominance, side-scale conditions (n = 8; t*₃₂ = −0.234; space R)

| Condition (σ_L, σ_R) | D-a: δ [95% CI] | D-b: ρ_g (upper 95%) | Over-shoot | D-c sub-criteria (i, ii, iii, iv) | D-c | Suppression flag |
|---|---|---|---|---|---|---|
| (0.9, 1.0) | **pass**, −0.265 [−0.295, −0.236] | 0.28 (1.15): not closer | no | ✓, ✓, ✗ (FD 0.039 > q₉₅ 0.021), ✓ | **no** | **yes** (iii) |
| (0.75, 1.0) | pass, −0.732 | 2.55 (4.69) | **yes** | ✗, ✗ (m_L −0.60 < log 0.8), ✗, ✓ | no | **yes** |
| (1.0, 1.15) | pass, −0.301 | 0.46 (1.45) | no | ✗ (right calibration e_R +0.29), ✓, ✓, ✗ (right jerk ×1.39) | no | no; "moved, not closer" |
| (0.85, 1.15) | pass, −0.713 | 2.45 (4.74) | **yes** | ✗, ✓, ✗, ✗ | no | **yes** |

- **"M-C/σ feasible at D-c" (exploratory): no.**
- **Every scale moved the log-ratio toward the target direction (D-a).** But none was demonstrably closer (D-b): the gap-ratio upper bounds were all > 0.5, and two over-shot.
- **Left-hand reductions show suppression signatures:**
  - left jerk ratio 0.50–0.78;
  - the left-hand Fréchet distance up beyond the A0′ null.
- **Raising the right hand** raised right jerk ×1.39.

## 4. Acceptance summary

| Test | Registered criterion | Outcome |
|---|---|---|
| T0 | ≤ 1e-4 / ≤ 1e-5 | PASS |
| T1 | (a) analytic; (b)–(f) within the calibrated margins | PASS (both gates) |
| T2 | eight TOSTs, ±5%, with h ≤ 1.5% | gates pass; calibration-inconclusive (h = 1.88% at n = 32), so theory-conditional |
| T5-A | no fail | PASS (10 conditions: 6 pass, 4 S₂-inconclusive; no fail) |
| **T3** | Δ ≥ 0.05, CI > 0 on ≥ 1 side | **FAIL** |
| **T4** | Δ ≥ 0.05, CI > 0 | **FAIL** |
| T5-B | D-a/D-b/D-c reported | D-a 4/4; D-b 0/4; D-c 0/4 |
| T6 | per §6.5 | left checks fail in 3/4 SS conditions; right checks fail with σ_R > 1 |
| **E2e overall** | stop on T0/T1/T2/T5-A fail or FM13 | **FAIL: FM13 stop gate** |

## 5. What this licenses and does not license (§15.3 table)

**Licenses:**
- "With these fixed orientations and ranks, frame-local linear noise coupling at up to κ = 0.9 (≈ 11,000–14,600 nats per sample) did not raise rotation-space arm–hand coupling by the registered 0.05, nor L–R coupling by 0.05, on 32 dev clips."
- The changes that were detected are small: ≤ 0.049 L–R induced under BH; ≤ 0.037 arm–right-hand for some orientations.
- "Fixed side noise scaling shifted the log-ratio toward the reference direction, but did not halve the gap. Where it reduced left-hand activity, it did so with suppression signatures (D-c not reached)."

**Does not license:**
- impossibility for the family: learned U and V might find transmitting directions (U8; the subject of E2c (ii), not run);
- any statement in joint space (E2e-J not run);
- any perceptual claim.

## 5a. E2e-J (non-gating; run later under separate authorisation)

See `E2EJ_REPORT.md`.
- **Joint-space analogues at the registered conditions:** T3 R 0.021, L 0.035; T4 0.036. All are below 0.05.
- **One descriptive exception:** orientation seed 2 gives J right arm–hand 0.058 [0.031, 0.086].
- **Dominance:** D-a 4/4, D-b 0/4 in J, as in R.
- **No effect on the FM13 verdict.**

## 6. Reproduce

Set `HF_HOME`, `WANDB_MODE` and `HF_HUB_OFFLINE` as in §2, then run the command in §2.
- `results.json` stores every seed and margin.
- The dumps allow re-analysis without regeneration.
