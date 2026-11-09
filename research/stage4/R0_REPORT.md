# R0 report: reference-only train targets in rotation space (R) and SMPL-X joint space (J)

*Stage 4 rev. 4.0 §6.0 rule iv; C-r1 to C-r6. Run 2026-11-03.*

- **Part 1:** run within the authorised campaign; paused at the FM13 stop after 30/60 chunks.
- **Part 2:** resumed from chunk 31 under your separate authorisation.

**Conclusion: COMPLETED.**
- Train-reference targets are computed in both spaces, with 95% clip-bootstrap CIs.
- U-A11 is resolved (approximate symmetry; negligible bias).
- V-R3 is done, with **one finding that needs attention**: the R-space statistics are numerically unstable for static poses (§4).

**Status of the targets:** they are recorded in `r0_results.json` and are **frozen as computed**. Under §6.0 rule (iii), any Stage 5 use takes them as they stand, and they are not retuned.

**Data:** How2Sign **train** references only. No dev or test data, and no generation.

## 1. Execution and integrity

| Item | Value |
|---|---|
| Code | `experiments/stage4/r0/r0_run.py` (space R: `experiments/stage4/e2e/metrics.py`; space J: `experiments/stage4/jspace.py`) |
| Data | `data/raw/SignSparK_data/train/How2Sign_reopt_train.lmdb` via the upstream `PoseDataset_Lmdb` (`dataset_feat = "full"`; `flip_left_hand=True`; seq_len 304 truncation), read-only |
| Clips | 29,630 train items; **29,630 used**; 0 excluded (none with L < 8) |
| Environment | `.venv-infer` with CUDA hidden, 4 threads, BelowNormal priority (R-1). The pure-Python `smplx` is imported read-only from `.venv-render` (a recorded deviation: `.venv-render` lacks lmdb/hydra/omegaconf; no environment modified) |
| Checkpointing (R-2) | 60 chunks of 500 (the last of 130); per-chunk `.npz` |
| Pause and resume | Paused by the STOP file before chunk 31 (campaign FM13 stop). Resumed under your authorisation. Pre-resume check (`experiments/stage4/resume_manifest_2026-11-03.json`): chunks 0–29 contiguous and valid; code unchanged since chunk 0 was written. **The resume computed chunks 31–60 only; the first 30 are bitwise identical to the manifest** |
| Running time | 29.8 min (part 1) + 30.4 min (part 2) = **60.2 min** of the 3 h cap (C-r6) |
| FK health | every clip finite; max bone-length deviation 1.63e-5 (limit 1e-4) |
| NaN | 0 in every per-clip statistic |
| Bootstrap | 2,000 clip resamples, seed 0 (C-r3) |
| Outputs | `experiments/stage4/r0/out/r0_results.json`; `out/chunks/chunk_000…059.npz`; logs `run_part1.log`, `run_part2.log`, `run_aggregate.log` |

**Incidents (recorded; none changed the data, loader, metrics, bootstrap seed or thresholds):**

| # | Incident | Handling |
|---|---|---|
| 1 | Launch 1: the LMDB was opened twice in one process, so it crashed before any chunk | Switched to the upstream `full` feature set, whose slices are identical to the hand and body streams. Crash logs kept |
| 2 | After all 60 chunks, the final V-R3 synthetic step crashed: the registered R-space metric (`metrics.sample_record`) computes `A_L / A_R` in plain Python and raises `ZeroDivisionError` for a frozen hand | Wrapped in R0's synthetic-check function only, recorded as "undefined (raises)"; `metrics.py` unchanged. **The aggregation was rerun, skipping all 60 existing chunks.** Chunk hashes were identical before and after (`chunk_hashes_before_aggregation.txt`). Crash log kept (`run_resume_vr3_crash.err`) |
| 3 | `status.json` showed the old "paused" text during the resume, because it is only rewritten at completion | Cosmetic; now "completed" |

## 2. Train-reference targets (mean over clips of the per-clip reference statistic; 95% clip-bootstrap CI; n = 29,630)

| Target | Space R | Space J |
|---|---|---|
| τ*_ah(L), left arm–left hand coordination | **0.610** [0.608, 0.612] | **0.422** [0.420, 0.424] |
| τ*_ah(R), right arm–right hand coordination | **0.451** [0.449, 0.454] | **0.249** [0.247, 0.252] |
| τ*_lr, left–right hand coordination | **0.323** [0.320, 0.325] | **0.320** [0.317, 0.322] |
| t*, mean log(A_L/A_R) | **−0.392** [−0.397, −0.388] | **−0.415** [−0.420, −0.410] |

**The two spaces give different values, and targets are space-specific (§6.0 rule i).**
- The **R-space** targets apply only to R statistics, the **J-space** targets only to J statistics.
- The historical 0.47 / 0.32 are superseded as targets. For comparison only, the train R values are 0.451 and 0.323.

**Per-clip agreement R vs J (Spearman, train):**

| Statistic | Spearman |
|---|---|
| arm–hand right | 0.58 |
| arm–hand left | 0.52 |
| left–right | 0.93 |
| dominance | 0.96 |

This confirms E0 at train scale. Dominance and L–R are space-consistent; arm–hand coordination is only moderately so.

**Observation (descriptive):** left arm–hand coordination exceeds right in both spaces (R 0.61 vs 0.45; J 0.42 vs 0.25). Earlier documents used only the right side (0.47). The left-side targets are new.

**Relation to the E2e values:** the dev-256 t*₂₅₆ (−0.310) and the 32-clip t*₃₂ (−0.234) differ from the train t*_R (−0.392). This is expected from subset variation. The E2e margins were fixed from t*₂₅₆ before any generation, and they are not affected.

## 3. U-A11: SMPL-X left/right hand mirror symmetry (T4-b in joint space)

| Check | Result |
|---|---|
| Max \|p_L − M p_R\|, rest hand joints and fingertips (absolute) | 3.30 mm |
| Same, wrist-relative | 5.32 mm |
| Wrist mirror error | 3.10 mm |
| dom^J of identical synthetic hand-pose sequences (20 sequences) | mean −0.0003; max \|·\| **0.0019** |

**Verdict:** the SMPL-X neutral hands are **not an exact mirror**, so T4-b, and with it Theorem 4, holds in J only approximately [VERIFIED].
- The induced bias in the J log-ratio is ≤ 0.002. That is 25× below δ_S₂ (0.05) and 200× below \|t*_J\| (0.415).
- Practically negligible for this project [INFERRED].
- Theorem 4 remains exact in space R.

## 4. V-R3 synthetic non-triviality checks (expected values stated in the code before the run)

| Sequence | Expected | R result | J result | Match |
|---|---|---|---|---|
| Static identity pose | all undefined (NaN) | coordination NaN; dominance **raises ZeroDivisionError** | all NaN | yes in substance (undefined); **R raises rather than returning NaN** |
| Train mean pose (static, non-identity) | all undefined (NaN) | **coord_ah(L) = −1.0, coord_lr = −1.0, dom = −0.090**; coord_ah(R) NaN | all NaN | **R: NO.** J: yes |
| Shared spike (arms and hands rotate 0.3 rad at one frame) | coordination = 1.0; dom_R = 0; dom_J ≈ 0 | 1.0, 1.0, 1.0; dom 0.0 | 1.0, 1.0, 1.0; dom −0.014 | yes |

**Interpretation:**
- **Numerical instability of R statistics on static input [VERIFIED].** For a static pose whose 6D vector is not exactly orthonormal (the train mean), Gram–Schmidt plus arccos near 1 produces speeds at the floating-point noise floor (~1e-8 rad/frame) instead of exact zeros. Correlations and log-ratios of that noise are meaningless but finite (−1.0, −0.09). J-space positions are exactly static, so J returns NaN as expected.
- **Effect on the rewards [INFERRED]:**
  - Under the target-matching rewards (§6.1), none of these degenerate motions maximises a reward. A static −1.0 is far from τ* (0.45–0.61), and the spike's 1.0 is also off-target.
  - So V-R3's purpose ("the statistic is not maximised by a degenerate motion") is **met in substance**.
  - **But** any future R-space reward or evaluation code must guard against near-static input (for example, treat frame speeds below a fixed floor as zero, and coordination or dominance as undefined), and must catch the A_R = 0 division.
  - **This is a finding to address before Stage 5**, not a change made now. `metrics.py` was not modified.
- **The shared spike** maximises raw coordination (1.0) in both spaces, which confirms why rewards are target-matching and why c_jerk exists (§6.1).

## 5. Status

| Item | Outcome |
|---|---|
| R and J targets with CIs | **done** |
| U-A11 | resolved: approximate symmetry; bias ≤ 0.002 |
| V-R3 | met in substance; **R-space static-input instability and division-by-zero recorded as a pre-Stage-5 implementation risk** |
| Train only; no dev or test data; no generation | confirmed |
