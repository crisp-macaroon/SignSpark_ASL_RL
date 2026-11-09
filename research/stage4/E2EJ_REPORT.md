# E2e-J report: joint-space secondary analysis of E2e (Stage 4 rev. 4.0 §15.3.2; C-j1). NON-GATING

*Run 2026-11-03 under your separate authorisation, after the E2e FM13 stop.*

**Conclusion: COMPLETED.**
- **E2e-J cannot change any E2e verdict.** E2e remains **FAIL (FM13)**.
- Joint-space (J) analogues of the registered T3/T4 conditions are also below 0.05.
- J agrees with rotation space (R) on the dominance pattern.

Released-checkpoint results, not a paper reproduction. No perceptual claim.

## 1. Inputs, code, settings

| Item | Value |
|---|---|
| Code | `experiments/stage4/e2e_j/e2ej_run.py`, `experiments/stage4/jspace.py` (E0.4 FK setup; E0.6 definitions extended to the left side and to L–R, §6.0) |
| Inputs (read only) | E2e dumps `experiments/stage4/e2e/dumps/` (all 16 conditions complete; SHA-256 in `experiments/stage4/resume_manifest_2026-11-03.json`); E2e `results.json` (SHA 2d392a30…); dev-256 reference dumps (`gt_poses`, clips 0–31); SMPL-X neutral NPZ. **No generation** |
| Pre-run integrity check | `experiments/stage4/verify_resume.py`: dumps complete, shapes correct, finite; no issue |
| Environment | `.venv-render` (CPU) |
| Noises / pairing | first 8 noises for every condition, paired by clip with A0 (as the registered R-space T3/T4/T5-B, P-10) |
| Bootstrap | 2,000 clip resamples, seed 0 (C-j1); 95% CIs |
| FK health | 4,128 FK calls; all finite; max bone-length deviation 1.59e-5 (limit 1e-4) |
| Runtime | 656 s (cap 1 h) |
| Output | `experiments/stage4/e2e_j/out/e2ej_results.json`, `experiments/stage4/e2e_j/run.log` |

**Joint-space definitions (§6.0):**
- **Arm signal:** wrist linear speed.
- **Hand signal:** mean speed of the 20 hand points in the wrist's local frame.
- **Coordination:** coord_ah^J(s) = corr(arm, hand); coord_lr^J = corr(hand L, hand R).
- **Dominance:** dom^J = log(A_L^J/A_R^J).
- **Target:** t*₃₂^J = mean over the 32 dev references = **−0.258** (rotation space: t*₃₂ = −0.234).

## 2. T3-J / T4-J: Δ vs A0 (95% CI) and agreement with rotation space

**Agreement categories:**
- "both": same sign, both CIs exclude 0;
- "R only" / "J only": only that space's CI excludes 0;
- "neither": neither CI excludes 0;
- "opposite": both exclude 0 with opposite signs.

| Condition | Δ arm–R-hand J | agree | Δ arm–L-hand J | agree | Δ L–R J | agree |
|---|---|---|---|---|---|---|
| BH-r60-κ0.3-seed0 | 0.008 [−0.001, 0.016] | neither | 0.012 [−0.001, 0.025] | neither | 0.013 [−0.000, 0.025] | R only |
| BH-r60-κ0.6-seed0 | 0.013 [−0.002, 0.027] | neither | 0.023 [0.002, 0.046] | J only | 0.022 [0.001, 0.040] | both |
| **BH-r60-κ0.9-seed0** (registered T3 condition) | **0.021 [−0.001, 0.046]** | neither | **0.035 [0.004, 0.064]** | J only | 0.043 [0.017, 0.070] | both |
| BH-r60-κ0.9-seed1 | 0.039 [0.009, 0.069] | both | 0.008 [−0.022, 0.037] | neither | 0.035 [0.007, 0.062] | both |
| BH-r60-κ0.9-seed2 | **0.058 [0.031, 0.086]** | both | 0.022 [−0.006, 0.045] | neither | 0.028 [0.004, 0.051] | both |
| BH-arm12-κ0.9 | 0.015 [0.002, 0.028] | J only | 0.016 [0.003, 0.029] | both | −0.014 [−0.033, 0.005] | neither |
| LR-r90-κ0.6-seed0 | 0.004 [−0.016, 0.023] | neither | 0 (exact) | neither | 0.018 [−0.005, 0.045] | neither |
| **LR-r90-κ0.9-seed0** (registered T4 condition) | 0.010 [−0.021, 0.037] | neither | 0 (exact) | neither | **0.036 [0.002, 0.071]** | both |
| LR-r90-κ0.9-seed1 | 0.012 [−0.015, 0.040] | neither | 0 | neither | 0.025 [−0.002, 0.053] | neither |
| LR-r90-κ0.9-seed2 | 0.001 [−0.029, 0.029] | neither | 0 | neither | 0.028 [0.007, 0.048] | both |

**Reading (descriptive, non-gating):**
- **J analogues of the registered criteria:**
  - T3 condition (κ0.9-seed0): R +0.021 and L +0.035; neither reaches 0.05.
  - T4 condition: +0.036 < 0.05.
  - So **the FM13 pattern also holds in joint space** at the registered conditions [VERIFIED].
- **Orientation dependence in both spaces:**
  - right arm–hand: J +0.039 (seed 1) and **+0.058 (seed 2, CI [0.031, 0.086])**;
  - R gives +0.033 and +0.037 for the same seeds.
  - Seed 2 in J exceeds 0.05. **This is not a registered test condition and E2e-J is non-gating, so it does not alter FM13.** It is relevant evidence for the E2c (ii) decision (whether optimised orientations transmit more) [INFERRED].
- **Agreement:**
  - L–R effects agree ("both") in 6 of 10 conditions.
  - Arm–hand effects agree less often: "both" in 3 of 20 side-condition cells, with "J only" in 3.
  - **No "opposite" cases.**
  - This is consistent with E0's finding that the coordination statistic is only moderately space-consistent (per-clip ρ ≈ 0.5).
- **Exact zeros:** left arm–hand under LR is exactly 0, as expected. Under LR the left noise is unchanged (K_L = 0), so the left output is sample-wise identical to A0.

## 3. T5-J: dominance levels D-a and D-b in joint space (t*₃₂^J recomputed per replicate)

| Condition (σ_L, σ_R) | D-a_J: δ [95% CI] | D-b_J: ρ_g (upper 95%) | Closer | Over-shoot | D-a δ in R | Agreement (D-a δ) |
|---|---|---|---|---|---|---|
| (0.9, 1.0) | **pass**, −0.304 [−0.338, −0.269] | 0.36 (1.24) | no | no | −0.265 | both |
| (0.75, 1.0) | pass, −0.937 [−1.004, −0.873] | 3.19 (5.55) | no | **yes** | −0.732 | both |
| (1.0, 1.15) | pass, −0.276 [−0.299, −0.256] | 0.24 (1.02) | no | no | −0.301 | both |
| (0.85, 1.15) | pass, −0.765 [−0.829, −0.701] | 2.42 (4.56) | no | **yes** | −0.713 | both |

**Reading:** J reproduces the R pattern.
- D-a passes 4/4. D-b ("closer") passes 0/4, because the gap-ratio upper bounds are all > 0.5.
- The same two conditions over-shoot.
- J effects are slightly larger in magnitude for left-scale reductions.
- This matches E0's finding that dominance is highly space-consistent (ρ ≈ 0.96), so **J provides little independent evidence for P1b** (§16.1 L2).
- D-c in J was not defined (left-hand checks are R-space T6 quantities), so it is not computed.

## 4. Status

| Item | Outcome |
|---|---|
| FK health (finite; bone ≤ 1e-4) | PASS |
| All conditions available | yes (16/16; none unavailable) |
| Effect on E2e verdict | **none (non-gating). E2e = FAIL (FM13)** |
