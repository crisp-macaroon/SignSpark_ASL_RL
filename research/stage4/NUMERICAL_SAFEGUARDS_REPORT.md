# Numerical safeguards: implementation (Step 0), unit tests, and S-5 train verification (Step 1)

*2026-11-03.*

**Authorised:** Steps 0 and 1 only.
- **Not done:** E2c (ii), E2a, E2b, controller implementation, training, generation, checkpoint changes, threshold or target changes, dev or test data in S-5.

**Labels:** [V] measured / checked · [D] derived · [I] inference · [U] unresolved.

## 1. Implementation (Step 0)

**File:** `experiments/stage4/validity/validity.py`, a **separate, versioned layer**.
- The registered v1 code is untouched: space R `experiments/stage4/e2e/metrics.py` and space J `experiments/stage4/jspace.py`.
- **Both files are bitwise unchanged** (SHA-256 equal to the pre-resume manifest; checked in the unit tests) [V].

| Safeguard | Version | Rule | Behaviour on undefined input |
|---|---|---|---|
| **S-1** zero activity / non-finite (R) | R v1.1 (validity check) | dom = log(A_L/A_R) defined only if A_L, A_R are finite and > 0 (and both hand signals are valid); non-finite input means every statistic is undefined | **NaN plus an explicit validity flag**; no exception |
| **S-2** near-static floor (R) | **R v1.1 (new metric version)** | a signal (arm speed: mean of elbow + wrist; hand speed: mean of finger joints; geodesic, per frame) is valid only if **mean ≥ 1e-5** and **std ≥ 1e-6 rad/frame**. Coordination needs both of its signals valid; dominance needs both hand signals valid | NaN plus flag |
| **S-6** J guard | **J v1.1** | non-finite input or FK means undefined (input checked before FK); a J signal is valid only if finite and **std ≥ 1e-7 m/frame**; dom_J needs A^J_L, A^J_R finite and > 0 | NaN plus flag |

**Guarantee:**
- For every input on which the relevant signals pass the floors, **v1.1 returns exactly the v1 value**: it calls the same v1 functions.
- Undefined is **never replaced by a finite value**.

## 2. Unit tests

**File:** `experiments/stage4/validity/test_validity.py`, on synthetic poses only (SMPL-X FK for the J tests).

**Result: 21/21 PASS** (`experiments/stage4/validity/out/unit_tests.json`).

| Case | Space R | Space J |
|---|---|---|
| Ordinary motion | v1.1 = v1 **exactly** (4 statistics) | v1.1 = jspace v1 **exactly** |
| Static identity | v1 raises ZeroDivisionError (documented); v1.1 all NaN | all NaN |
| Static non-identity (non-orthonormal 6D) | v1 returned finite **spurious** coord_lr and X; v1.1 all NaN (signal mean 6.8e-9, std 2.5e-24) | — |
| Frozen left hand, rest moving | left-hand statistics and dom NaN; right arm–hand = v1 | see the finding below |
| Frozen left hand, static body | — | left statistics, L–R, dom NaN; right defined |
| Near-static hand (1e-7 rad steps) | invalid (mean 1.6e-7 < 1e-5) | — |
| Slow real hand (1e-3 rad steps) | valid (mean 1.6e-3) | — |
| NaN / +inf input | all NaN, no exception | all NaN, without FK |
| Signal-level J tests | — | std < 1e-7 invalid; zero activity gives dom NaN; non-finite invalid; FK failure all NaN |
| v1 files unchanged | SHA match | SHA match |

**Run-1 test-design error (kept in `out/unit_tests_run1.json`, 19/20):** I had expected a static hand **pose** under a **moving** arm to be undefined in J.

**Finding [V]:** it is not static in J.
- SMPL-X hand joints and fingertips are regressed from linear-blend-skinned vertices, so forearm motion leaks a small non-rigid motion into the wrist-local hand signal.
- Measured: mean 5.6e-5 m/frame, std 2.3e-5. That is about 2% of a synthetic moving hand (2.7e-3), and far above noise.
- The J floor correctly treats it as real geometric motion. J v1.1 is a numerical-validity layer, not a "frozen pose" detector.
- **Consequence [I]:** J-space arm–hand coordination can contain a small **mechanical (skinning) arm-to-hand component**. The frozen J targets were computed with the same definition, so J targets and J statistics remain like-for-like. But J arm–hand coordination is **not a pure measure of hand articulation**. Its size in real data is unmeasured [U]; see §4.

The expectation was corrected and a static-body frozen-hand test added: 21/21.

## 3. S-5: frozen R0 space-R targets under R v1.1 (Step 1)

**Script:** `experiments/stage4/validity/s5_verify.py`.
- **Data:** How2Sign **train** references only, the same loader, settings and 29,630 clips as R0. **No dev, no test, no generation, no FK.**
- **Runtime:** 159 s, CPU, BelowNormal.
- **Output:** `experiments/stage4/validity/out/s5_results.json`.

| Check | Result |
|---|---|
| Clips / clip order vs R0 chunks | 29,630; **0 order mismatches** |
| Non-finite inputs | 0 |
| **Invalid streams** (arm R, arm L, hand L, hand R; 118,520 in total) | **0 / 0 / 0 / 0** |
| v1 → v1.1 definedness changes (4 statistics × 29,630) | **0** |
| Max \|v1.1 − v1\| where defined | **0.0** (bitwise identical) |
| Smallest train signal mean / std (rad/frame) | arm R 1.2e-3 / 4.7e-4; arm L 7.4e-4 / 2.2e-4; **hand L 1.0e-4 / 2.2e-5**; hand R 1.1e-3 / 4.6e-5 |
| `r0_results.json` | unchanged (SHA 427dd363…) |

**Conclusion [V]:**
- **The frozen space-R R0 targets remain valid under R v1.1, unchanged:** τ_ah(L) 0.610, τ_ah(R) 0.451, τ_lr 0.323, t* −0.392.
- **No replacement targets were needed or computed.**

**Margin note [V]:** the slowest train left hand (mean 1.0e-4) is only **10×** above the 1e-5 mean floor. Its standard deviation (2.2e-5) is 22× above the std floor. The margin is much smaller than on dev (≈ 340×) and generated data (≈ 570×).
- It is still clear of the floor. But generated motion that moves the hand toward stillness (for example left-hand suppression under σ_L < 1) could approach it.
- That is acceptable: S-3/S-4 then count such samples as undefined with worst-case reward, which is the intended protection.

**Not verified:** the J targets under J v1.1. That needs FK on all train clips (≈ 60 min CPU) and was not authorised. They are unaffected for any clip whose J signals have std ≥ 1e-7 m/frame. R0 found no NaN and an FK maximum bone deviation of 1.6e-5, but the J floor itself was not evaluated on train [U].

## 4. Remaining issues

| # | Issue | Status |
|---|---|---|
| 1 | J targets under J v1.1 (FK pass on train) | **Resolved 2026-11-04:** valid unchanged, 0 invalid streams, bitwise = v1 (`J_VERIFY_LEAKAGE_REPORT.md`) |
| 2 | **Skinning leakage in J arm–hand coordination** (finding §2) | **Quantified 2026-11-04 [REAL]:** 1–2% of hand motion; +0.001 coordination; not material by the pre-stated criterion. Material only for near-static hands (`J_VERIFY_LEAKAGE_REPORT.md`) |
| 3 | Small train margin for the left-hand mean-speed floor (10×) | recorded; covered by S-3/S-4 |
| 4 | S-3 (reward) and S-4 (evaluation) treatment of undefined values | specified in the readiness report; to be implemented only with a controller (not authorised) |
