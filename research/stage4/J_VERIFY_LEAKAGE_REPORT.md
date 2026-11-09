# J v1.1 train-target verification and SMPL-X skinning-leakage analysis

*2026-11-04. Released-checkpoint context; no generation was involved, and this is not a paper reproduction.*

**Authorised:** Task 1 (J-space target verification) and Task 2 (skinning leakage), read-only.
- **Not done:** E2c (ii), E2a, E2b, controller implementation, generation, training, checkpoint changes, threshold or target changes, Stage 5.
- No dev or test data was used.

**Labels:** [V] measured · [D] derived · [I] inference · [U] unresolved · **[SYN]** synthetic poses · **[REAL]** How2Sign train references.

**Script:** `experiments/stage4/validity/jverify_leakage.py` (SHA 7fa84ad0…).
- **Output:** `experiments/stage4/validity/jverify/jverify_leakage_results.json` (SHA d543f123…), plus 60 chunk files in `jverify/chunks/`.
- **Runtime:** 68.9 min CPU (`.venv-infer`, CUDA hidden, 4 threads, BelowNormal). Exit 0; stderr has only pydantic warnings.

**Unchanged:**
- SHA-256 checked after the run: `jspace.py` (J v1; f664592d…) and `r0_results.json` (427dd363…).
- `FROZEN_TARGETS_R0.json` target values.
- The SMPL-X model files and `third_party/`: read only and never written by the script (not separately hashed).

---

## Report 1: J v1.1 train-target verification (Task 1)

**Setup:**
- **Data:** the same loader, the upstream `full` feature set, the same R0 train split and clip ordering: all **29,630** How2Sign train references.
- **Method:** for each clip, SMPL-X FK and `validity.j_stats` (J v1.1, S-6), compared with R0's stored J v1 per-clip rows (chunk columns 4–7).

| Check | Result [V] |
|---|---|
| Clips; clip order vs R0 chunks | 29,630; **order identical** (names equal in all 60 chunks) |
| Clips with non-finite FK output | 0 |
| **Invalid J streams** (arm L, arm R, hand L, hand R; 118,520 in total) | **0 / 0 / 0 / 0** |
| v1 → v1.1 definedness changes (τ_ah(L), τ_ah(R), τ_lr, dom; 4 × 29,630) | **0 / 0 / 0 / 0** |
| Max \|v1.1 − v1\| where defined | **0.0 / 0.0 / 0.0 / 0.0** (bitwise identical) |
| Train means, v1.1 vs v1 | τ_ah(L) 0.42200 = 0.42200; τ_ah(R) 0.24902 = 0.24902; τ_lr 0.31962 = 0.31962; dom −0.41490 = −0.41490 |

**Conclusion [V]:**
- **The frozen J targets remain valid under J v1.1, unchanged:** τ_ah(L) 0.422, τ_ah(R) 0.249, τ_lr 0.320, t* −0.415.
- **No target changed and no stream became invalid.** There is therefore nothing to report separately.
- No replacement targets were computed or adopted, and `FROZEN_TARGETS_R0.json` values are untouched (only the verification note was updated).
- The R and J targets remain separate.

**Together with S-5:** all eight frozen R0 targets (R and J) are now verified under the v1.1 validity layer.

---

## Report 2: SMPL-X skinning-leakage analysis (Task 2)

### 2.1 Mechanism (from the earlier unit test)

- SMPL-X finger joints are regressed from linear-blend-skinned vertices.
- Forearm and wrist rotation therefore move them slightly relative to the wrist frame, even with the hand pose fixed.
- The J hand signal (wrist-local finger speed) thus contains a small mechanical, arm-driven component.
- No model file, metric definition or target was modified to measure this.

### 2.2 Design (pre-stated before the run; in the script docstring)

Three FK re-posings were made per clip, on every 10th train clip (**n = 2,963 [REAL]**):

| Variant | Body | Hands | Gives |
|---|---|---|---|
| actual | as recorded | as recorded | the registered J signals |
| arm-static | held at frame 0 | as recorded | the hand signal without arm-induced leakage ("no-leak") |
| hand-static | as recorded | held at frame 0 | the **leakage-only** hand signal |

**Pre-stated materiality criterion.** The leakage materially influences J arm–hand coordination if, for either side, one of the following holds:
- the paired mean of (coord_actual − coord_noleak) has a 95% bootstrap CI excluding 0 **and** |mean| ≥ 0.02; or
- the per-clip Spearman correlation between coord_actual and coord_noleak is < 0.90.

**Synthetic part:** 50 random-walk sequences (0.05 rad/frame steps). In each, either the arm moves with a static identity hand, or the arm is static with moving hands.

### 2.3 Results

**Leakage magnitude.** Columns L and R are [REAL]; the last column is [SYN].

| Quantity | L hand | R hand | Synthetic |
|---|---|---|---|
| Leakage, mean (median; p95), m/frame | 3.69e-5 (3.69e-5; 5.49e-5) | 2.96e-5 (2.95e-5; 4.36e-5) | 4.89e-5 |
| Actual hand signal, median, m/frame | 1.98e-3 | 2.92e-3 | 2.70e-3 (moving hand, static arm) |
| **Leakage / actual hand signal**, median (p95; max) | **1.9%** (3.4%; 46%) | **1.0%** (1.6%; 7.8%) | 1.8% |
| Clips with ratio > 5% / > 10% | 46 / 12 of 2,963 | 5 / 0 of 2,963 | — |
| Leakage per unit wrist speed | — | — | ≈ 1.0e-3 (arm speed 5.1e-2 m/frame) |

**Effect on measured coordination [REAL]:**

| | L | R | L–R |
|---|---|---|---|
| Mean coordination, actual | 0.4204 | 0.2492 | 0.3198 |
| Mean coordination, no-leak (arm-static hand) | 0.4196 | 0.2479 | 0.3194 |
| **Paired diff, actual − no-leak** [95% CI] | **+0.0009** [0.0006, 0.0013] | **+0.0013** [0.0012, 0.0014] | +0.0003 [−0.0001, 0.0006] |
| Per-clip Spearman, actual vs no-leak | **0.9995** | **0.9999** | — |
| Per-clip \|diff\| p99 / max | 0.012 / 0.47 | 0.009 / 0.04 | — |
| Clips with \|diff\| > 0.02 / > 0.05 | 11 / 3 | 2 / 0 | — |
| Coordination of the leakage-only signal with the arm | 0.30 | 0.40 | — |
| **Material (pre-stated criterion)** | **no** | **no** | — |

**Reading the results:**
- **[REAL]** The leakage is real and statistically detectable: both arm–hand CIs exclude 0.
  - It inflates mean J arm–hand coordination by about **0.001**.
  - That is about 2–3% of the registered transmission threshold (0.05), and 0.2–0.5% of the frozen J targets.
  - The per-clip ranking is essentially unchanged (Spearman ≥ 0.9995).
  - L–R coordination is not detectably affected.
  - **By the pre-stated criterion the effect is not material.**
- **[REAL]** The leakage-only signal itself correlates with arm speed (0.30 L, 0.40 R), as expected for a mechanically arm-driven component. It is diluted because it is only about 1–2% of hand motion.
  - Where the hand barely moves, the dilution fails. The 12 slow-left-hand clips with leakage > 10% of the hand signal include the clip with a 0.47 coordination shift (ratio–|diff| correlation 0.39 on L).
  - **So leakage matters exactly when true hand motion is small.**
- **[SYN] vs [REAL]:**
  - The synthetic leakage (4.9e-5) is the same order as real-data leakage (3.0–3.7e-5), and the synthetic ratio (1.8%) matches the real left-hand median.
  - The synthetic arm moves faster than real arms (5.1e-2 vs about 1e-2 m/frame), so the per-arm-speed ratio is only indicative.
  - All verdicts above rest on [REAL] data.
- **[D]** The J v1.1 floor (std ≥ 1e-7 m/frame) is about 300× below the leakage level. **A completely frozen hand pose under a moving arm is therefore valid in J.** Its J arm–hand coordination would read the leakage-only value (≈ 0.3–0.4 on train-like arms) rather than undefined.
  - In R, the same case is undefined (R v1.1, S-2).
  - This is the one regime where J and R disagree by construction.

---

## Report 3: updated Stage 5 readiness assessment

**Status:** an addendum to `research/STAGE5_READINESS_REPORT.md` (update 2026-11-04 section).
- **Safeguard status:** S-1, S-2, S-6 implemented; S-5 verified for R and **now J**. S-3/S-4 (reward and evaluation treatment of undefined values) remain specified only; they are implemented with a controller, which is not authorised.
- **Frozen targets:** all 8 (R and J) verified under v1.1, unchanged.
- **New risk, quantified:** skinning leakage. Not material on real train motion. It is material only for near-static hands under arm motion, which is precisely the suppression regime seen in E2e (σ_L < 1).
  - **Consequence for any future J evaluation of generated motion [I]:** a left-hand-suppressing controller could show *spuriously retained* J arm–hand coordination.
  - The R metric would flag it as undefined, or show the drop.
- **Training verdict, unchanged:** no defensible training objective exists in the current frozen-base scope.
  - E2c (ii) remains the necessary precondition for route A.
  - These analyses change no statistic on real data and do not alter the capacity argument.
  - Stage 5 has not started.

---

## Report 4: recommendation — is J sufficiently independent as a secondary evaluation measure?

**Recommendation: yes, as a secondary, descriptive measure, with two stated limits.** It must not become a gating or reward measure.

1. **The skinning leakage does not compromise J on realistic motion [V].** The bias is about 0.001 in coordination, the ranking is preserved (Spearman ≥ 0.9995), and it is non-material by the pre-stated criterion. J arm–hand coordination on reference-like motion reflects hand articulation, not mechanics.
2. **Limit 1: the near-static-hand regime [D/I].** When the hand signal is within about 10× the leakage (≈ 3–5e-4 m/frame), J arm–hand coordination is partly mechanical. Any future J report on generated motion should therefore:
   - state each sample's leakage ratio, which can be computed with the hand-static re-posing used here;
   - show J arm–hand results with that ratio alongside, especially for suppression conditions.

   This is a reporting recommendation, **not a new threshold or metric version**. Adopting it as a rule would need your approval and a registered amendment.
3. **Limit 2: J is a different measurement, not independent data [D].**
   - J and R are computed from the same rotation sequences.
   - J differs in geometry: positions instead of geodesic angles, and wrist-local fingers.
   - It therefore guards against R-specific artefacts (such as the V-R3 6D instability) but **cannot provide statistically independent replication**. Agreement between R and J is corroboration across metrics, not a second sample.
4. **R remains the gating space,** as registered, and J remains descriptive (as in E2e-J). The E2e-J conclusion (FM13 also holds in J) is not changed by a bias of this size:
- the leakage shifts coordination by about 0.001 in both the baseline and the coupled conditions;
- the J transmission Δs miss 0.05 by margins (≥ 0.014) far larger than that.

This is [I]; E2e-J was not re-run.

**Stopped here for your review.** Nothing further was run.
