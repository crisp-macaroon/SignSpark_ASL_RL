# Stage 4 consolidated execution summary and failure report

*2026-11-03.*

## Closure 2026-11-03 (your decision)

**H0 is accepted for P1a under the tested fixed-orientation M-C Gaussian noise-coupling design.** E2c (ii), residual controllers, per-step control and further controller-design exploration are not pursued.
- **P1a:** the registered transmission criteria fail in R (gating) and in J (descriptive).
- **P1b:** fixed side scaling did not reach D-c, and showed suppression signatures.
- **This does not establish that RL cannot improve SignSparK.** It concerns this controller configuration only.
- No perceptual, semantic, intelligibility or ASL-quality claim is made.
- **Frozen targets:** `FROZEN_TARGETS_R0.json`.
- **Stage 5 readiness:** `research/STAGE5_READINESS_REPORT.md` (verdict: training not scientifically justified on current evidence).

## Update 2026-11-04: E2c (ii) (your authorisation; (i) not run)

- **Mean held-out coordination:** 0.034 [0.007, 0.063] against a primary best-of-8×8 level of 0.446. No gain over uncoupled (−0.003).
- **In-sample:** 0.737, i.e. overfitting to 4 training noises.
- **Constraints:** KL ≤ 2.7 nats/frame, so the bound was not binding.
- **Verdict:** **registered negative outcome (FM4)**; route A precondition not met.
- Report: `E2C_II_REPORT.md`. E2a, E2b and E2c (i) not run.

## Update 2026-11-04: J verification and skinning leakage (read-only)

- **J v1.1:** the frozen J targets are valid unchanged (0 invalid streams; bitwise = v1 on 29,630 train clips).
- **Skinning leakage, real data:** 1–2% of hand motion and +0.001 on J arm–hand coordination, so not material. It matters only for near-static hands.
- **J:** retained as a secondary, descriptive measure.
- Report: `J_VERIFY_LEAKAGE_REPORT.md`.

## Update 2026-11-03: numerical safeguards (Steps 0–1)

- **Validity layer:** R v1.1 and J v1.1, versioned; v1 unchanged; 21/21 unit tests.
- **S-5:** the R targets are valid under v1.1 unchanged (0 invalid streams).
- **New finding:** SMPL-X skinning leakage in J hand signals (≈ 2% of a moving hand).
- Report: `NUMERICAL_SAFEGUARDS_REPORT.md`.

## Update 2026-11-03: E2e-J run and R0 completed (your separate authorisation after the FM13 stop)

| Step | Status | Key results | Report |
|---|---|---|---|
| **E2e-J** (non-gating) | **COMPLETED** | Joint-space (J) analogues at the registered conditions are below 0.05:<br>• T3 (BH-κ0.9-seed0): R +0.021 [−0.001, 0.046], L +0.035 [0.004, 0.064];<br>• T4 (LR-κ0.9-seed0): +0.036 [0.002, 0.071].<br>So **FM13 also holds in joint space.**<br>Descriptive exception: orientation seed 2 gives J right arm–hand **+0.058 [0.031, 0.086]** (R: +0.037). Not a registered condition; no effect on the verdict.<br>Agreement R vs J: L–R "both" 6/10; arm–hand "both" 3/20, "J only" 3/20; no opposite signs.<br>Dominance in J: D-a 4/4, D-b 0/4, the same over-shoots as R.<br>FK: 4,128 calls healthy | `E2EJ_REPORT.md` |
| **R0** | **COMPLETED** (resumed at chunk 31; first 30 chunks bitwise unchanged) | **Train targets, R:** τ_ah(L) 0.610, τ_ah(R) 0.451, τ_lr 0.323, t* −0.392.<br>**Train targets, J:** τ_ah(L) 0.422, τ_ah(R) 0.249, τ_lr 0.320, t* −0.415.<br>CIs ±0.002–0.005; n = 29,630.<br>**U-A11:** not an exact mirror (≤ 5.3 mm), but the J dominance bias is ≤ 0.002 (negligible).<br>**V-R3:** degenerate motions do not maximise target-matching rewards, but **R-space statistics are numerically unstable on static non-identity poses** (spurious −1.0 correlation) **and raise ZeroDivisionError for a frozen hand**. This is a pre-Stage-5 implementation risk; nothing changed | `R0_REPORT.md` |
| E2a, E2b, E2c | **NOT RUN** (not authorised) | — | — |

**New incidents** (recorded in the step reports; none touched data, loader, metrics, seeds or thresholds):
- R0's final V-R3 step crashed on the ZeroDivisionError above. It was handled inside R0's synthetic-check wrapper, and the aggregation was rerun without recomputing any chunk.
- R0's `status.json` text was stale during the resume (cosmetic).

**Evidence relevant to your E2c (ii) decision** (not a recommendation to run it automatically):
- The coupling effect depends on orientation in both spaces.
- Seed 2 exceeds 0.05 in J (descriptively) and seeds 1–2 are significant in R.
- But the registered seed-0 condition, and every L–R condition, stay below 0.05 in both spaces.
- **Stage 4 status:** E2d PASS; E2e FAIL (FM13); E2e-J completed; R0 completed; E2a, E2b and E2c not run. Awaiting your decision.

**Campaign:** authorised 2026-11-03 (campaign plan §6).

**Status: STOPPED at E2e by the registered stop gate FM13** (T3 and T4 both fail).
- E2e-J, E2a, E2b and E2c were **not run**.
- R0 is **paused** at 30/60 chunks (resumable).
- Stage 5 has not started. There was no automatic switch to any controller, no threshold change, no test data, no training.

All generation numbers are **released-checkpoint results, not a paper reproduction**. No perceptual, preference, semantic or intelligibility claim is made.

## 1. Consolidated results

| Step | Status | Key results | Report |
|---|---|---|---|
| E0 | PASS (earlier) | FK valid; Windows rendering; J-space dev metrics | `E0_REPORT.md` |
| E2d | **PASS** | unrolled sampler bitwise equal to upstream `decode`; M-CLIP identical in 3/3 checkpoints; K = 10 gradient pass ≤ 8.8 GiB (B = 8); gradients finite; step-norm ratio 3.9 | `E2D_REPORT.md` |
| Phase 0 | **PASS** | E2e-J, E2a, E2b, E2c, R0 implemented; synthetic self-tests 19/19 (new) + 42/42 (E2e); checkpoint SHA re-verified | this file §3 |
| **E2e** | **FAIL (FM13)** | T0, T1, T2 (calibration-inconclusive), T5-A: pass / no fail. **T3 fail:** Δ arm–hand at κ0.9-seed0 = R 0.017 [−0.014, 0.049], L 0.022 [−0.006, 0.048] (needs ≥ 0.05, CI > 0). **T4 fail:** Δ L–R = 0.035 [0.006, 0.066] (needs ≥ 0.05). T5-B: D-a 4/4, D-b 0/4, **D-c 0/4**; suppression signatures in 3/4 | `E2E_REPORT.md` |
| E2e-J | **NOT RUN** (campaign stopped) | dumps for all 16 conditions are saved and complete, so it can run later without generation | — |
| E2a | **NOT RUN** | — | — |
| E2b | **NOT RUN** | — | — |
| E2c | **NOT RUN** | — | — |
| R0 | **PAUSED** (STOP file, campaign stop) | 30/60 chunks (15,000 train clips) checkpointed; 29.8 min of the 3 h cap used; no FK or data failure | `experiments/stage4/r0/out/` (partial; no targets computed) |

## 2. Why the campaign stopped

- **The authorised §5 stop rule:** "T3 and T4 both fail (FM13): E2a and E2c depend on E2e (§15.2), so the campaign stops with the options (a)–(e) of §15.2 and no automatic switch".
- **What I did:** paused R0 through its STOP file to honour "stop immediately"; R0 resumes exactly.

**Documentation inconsistency found (not acted on):**
- The plan's §5 sentence says E2a depends on E2e.
- But Stage 4 rev. 4.0 §15.2 lists E2a's dependency as **E2d (configuration)** only, and E2b has **none**. Only E2c depends on E2e.
- Under the plan as authorised the campaign still stops. **Whether E2e-J, E2a, E2b and R0, which do not need transmission, should now continue is your decision.**

## 3. Deviations and incidents (all recorded; none changes a registered criterion)

| # | Item | Effect |
|---|---|---|
| 1 | **First launch crashed before any work:**<br>• E2e: `disk_usage` on a relative path's empty anchor;<br>• R0: LMDB cannot be opened twice in one process.<br>Fixed: the path is resolved; R0 uses the upstream `full` feature set (identical slices). Crash logs kept | none: nothing was generated or written |
| 2 | **R0 environment:** runs in `.venv-infer` (CUDA hidden), importing the pure-Python `smplx` read-only from `.venv-render`. `.venv-render` lacks lmdb, hydra and omegaconf | no environment modified |
| 3 | `e2e_run.py` did not log peak GPU memory | E2d measured ≤ 8.8 GiB for the same harness; no OOM |
| 4 | T2 calibration-inconclusive (h = 1.88% > 1.5% at n = 32) | registered branch: continue with theory-conditional wording |
| 5 | Two Phase 0 test-design errors (C-c3 test A run 1; R0 rot6d axis normalisation) were corrected before any run; both run-1 outputs kept | none on the code under test |
| 6 | The campaign plan §5 dependency wording (above) | your decision |

## 4. Options under §15.2 (presented, NOT chosen)

| Option | What it would test | Evidence from E2e bearing on it |
|---|---|---|
| (a) **E2c (ii) family-capacity test:** can *optimised* U and V find transmitting directions that random ones miss? | whether the FM13 failure is orientation-specific or family-wide (U8) | Orientation dependence exists: right-side Δ was 0.033 and 0.037 (CIs > 0) for seeds 1 and 2, against 0.017 for seed 0. Induced L–R under BH-κ0.9 was 0.049 [0.023, 0.075]. These are small effects at a very large KL (≈ 14,600 nats per sample). E2c is implemented (C-c1–C-c6 approved, ≈ 40 min) but is registered as depending on E2e |
| (b) Residual controller (§5.6) | a non-linear noise map | no exact KL, no marginal guarantee; non-default |
| (c) Per-step control (C10/F4) | control inside the sampler | more implementation |
| (d) N5 keyframe cascade | explicit non-learned body → hand timing coupling through keyframes | KF2P shows keyframes do transmit timing (Stage 4 A2: 0.76–0.82 agreement) |
| (e) **Accept H0 for P1a via M-C** | — | consistent with T3/T4 at the registered threshold |

**Separately for P1b:** fixed side scales did **not** reach D-c. Every scale moved the ratio in the target direction, but none was demonstrably closer. Left-scale reductions show suppression signatures, and right-scale increases raised right-hand jerk. The non-RL side-assignment rule N9 remains the comparator.

## 5. Recommendation for the next research decision (yours; nothing started)

1. **Run the analyses of existing data now; they don't depend on transmission:**
   - **E2e-J**, non-gating: about 15–30 min CPU, no generation. It answers whether joint space shows the same failure.
   - **resume R0:** about 30 min CPU; it gives frozen train targets needed for any later work.
   - Both are already implemented and tested.
2. **Before accepting H0 for P1a, run the single most informative check: option (a), E2c (ii).**
   - The small but significant orientation-dependent effects (seeds 1 and 2) mean that a random-orientation failure does not establish family-wide failure.
   - E2c (ii) tests that directly within the KL bound, in about 40 min of GPU time.
   - **If (ii) also fails to reach the best-of-8×8 level, H0 for P1a via M-C is well supported.**
3. **P1b:** treat M-C/σ with fixed scales as not feasible at D-c. Any further P1b work would need a new design decision (for example the mean shift, which is deferred, or N9 as the comparator). Nothing is proposed for automatic adoption.
4. **E2a and E2b** (gradient agreement; time-shift equivariance) only matter if a controller is pursued. Defer them unless (a) is positive.

## 6. Files

| Path | Content |
|---|---|
| `research/stage4/E2D_REPORT.md`, `E2E_REPORT.md` | step reports |
| `research/stage4/STAGE4_CAMPAIGN_PLAN.md` | authorised plan |
| `experiments/stage4/e2e/out/results.json`, `run.log`, `dumps/` | E2e outputs |
| `experiments/stage4/r0/out/chunks/` (30), `status.json`, `run.log` | R0, partial |
| `experiments/stage4/{e2e_j,e2a,e2b,e2c,r0}/*.py`, `jspace.py`, `gpu_common.py`, `phase0_selftest.py` | Phase 0 code (E2e-J/E2a/E2b/E2c not executed) |
