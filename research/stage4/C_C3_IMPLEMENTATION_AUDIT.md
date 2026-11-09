# C-c3 implementation audit (E2c typicality enforcement)

*2026-11-03. Read-only audit: static inspection of code, evidence files and documents, plus mathematical analysis. Nothing was executed: no synthetic test, no model, no data. No file other than this audit and its companion was changed.*

**Labels:**
- **VERIFIED:** checked directly in code or evidence files.
- **REPORTED:** present in the synthetic review, not independently reproduced.
- **INFERRED:** follows from mathematical reasoning or static analysis.
- **UNRESOLVED:** needs more evidence, an experiment, or code that does not yet exist.

## 0. Files inspected

| File | Status |
|---|---|
| `experiments/stage4/e2c/typicality.py` | present; inspected in full |
| `experiments/stage4/e2c/review_typicality.py` | present; inspected in full |
| `experiments/stage4/e2c/typicality_review.json` (+ `review.log`) | present; key values read |
| `experiments/stage4/e2c/validate_typicality.py`, `typicality_validation.json` | present (source of the issue-5 detection rates) |
| "Updated Stage 4 report, §2a" | **There is no §2a in `research/STAGE4_REPORT.md`.** C-c2, C-c3 and E-1 to E-5 exist **only** in `research/stage4/STAGE4_CAMPAIGN_PLAN.md` (§2, §2a, §6). The Stage 4 report rev. 4.0 contains only the registered E2c row (§15.2, l. 952) **[VERIFIED]** |
| `research/stage4/STAGE4_CAMPAIGN_PLAN.md` | present; §2, §2a, §6 inspected |
| `research/stage4/E2_EXECUTION_CHECKLIST.md` | present; its E2c step has no C-c content (see the consistency file) |
| `research/RESEARCH_LOG.md` | present; C-c3 entries at l. 271–278 |
| **The E2c runner** (the code implementing E-3/E-5, the monitored quantities, the comparator) | **does not exist.** Planned for campaign Phase 0. E-3 (as a gate in the optimisation loop), E-5, the comparator and the monitoring are therefore **specification-only** and cannot be verified **[UNRESOLVED]** |

## 1. Issue 1: null calibration

| Claim | Finding | Label |
|---|---|---|
| 16,000 null samples per length | `part1(n_per_L=16000, chunk=2000)`: 8 chunks × 2,000 | VERIFIED |
| Number of lengths | `sorted(set(LENGTHS))`: **30 unique lengths** from the 32 clips (71 and 304 occur twice); 30 lines in `review.log` | VERIFIED |
| Max violation rate 1.57% | max "any" = 0.0156875 at L = 263 (`typicality_review.json` l. 1192) | VERIFIED |
| Target 1.59% | `NOM["any"] = 1 − Π_k(1 − nom_k)` = 0.015874, with nom_{M,V,A} = 1 − (1 − a_c)^90 and nom_P = 0.001. **This product assumes the four violations are independent.** They are not exactly (M and V share each channel's mean; P is the mean of the r_c that A tests). The union bound is ≤ 1.6%, so the target is approximate | VERIFIED (value); INFERRED (approximation) |
| SE and test | se = √(nom(1 − nom)/n) = 0.099% at n = 16,000. z = (rate − nom)/se. Flagged if z > Φ⁻¹(1 − 0.05/30) = 2.94 (one-sided, Bonferroni over 30 lengths). No flag is true (no `"significantly_above_nominal_bonferroni": true` in the JSON); max z = −0.19 | VERIFIED |
| "No length significantly exceeds the target" | **Justified as stated**, with a limit. The test can only detect an excess of ≥ ≈ 0.29 percentage points per length (2.94 × 0.099%). So the evidence supports "every length's rate ≤ ≈ 1.9% (family-wise 95%)", not "exactly calibrated". The per-length Wilson CIs in the JSON are **not** multiplicity-adjusted | INFERRED |
| "The earlier 1.88% was Monte-Carlo noise" | First run (`typicality_validation.json`, 4,000 per length): max 0.01875. At n = 4,000, se = 0.198%, so z = (1.875 − 1.587)/0.198 = 1.45: not significant even before multiplicity adjustment. **The wording "was Monte-Carlo noise" overstates this; correct wording: "is consistent with Monte-Carlo noise (z = 1.45; not significant)"** | VERIFIED (numbers); INFERRED (interpretation) |
| A and P use the specified definitions | Code: `r_c = Σ_t x_t x_{t+1} / Σ_t x_t²` (uncentred; denominator over all L); A bound Φ⁻¹(1 − 0.005/90/2)/√L = 4.03/√L; P: \|mean_c r_c\| ≤ Φ⁻¹(0.9995)/√(90(L − 1)) = 3.29/√(90(L − 1)). These match plan §2a exactly | VERIFIED |
| A conservative, P within MC error | Per-channel A tail 0 (L = 28) to 4.65e-5 (L = 252) vs nominal 5.56e-5. P rates 0.04–0.14% vs 0.1%. At 16,000 samples, se(P) ≈ 0.025%, so 0.14% is +1.6 se: not significant | VERIFIED (values); INFERRED (significance) |

**Verdict: PASS**, with a wording correction ("consistent with MC noise") and the stated detectability limit.

## 2. Issue 2: joint M/V/N projection (`project_mvn_exact`)

| Requirement | Finding | Label |
|---|---|---|
| M, V and N enforced simultaneously | Means are clamped to ±b_M(1 − 1e-9). The centred part of each channel is scaled by s_c with q_c = clip(m_c² + e^{2t}v_c, max(vlo, m_c²), vhi), using one common t found by bisection so that Σ q_c = ‖x‖²_target/L. The means stay m_c; q_c ∈ the nudged V band; the sum matches to bisection precision (Δt < 1e-12, so a relative norm error ≈ 2e-12 ≪ the N tolerance 1e-6) | VERIFIED (code); INFERRED (precision) |
| Short and long clips | Synthetic: 100% M/V/N-feasible over 10,000 cases (L = 28, 56, 146, 304 × 5 input types × 500) | REPORTED (`typicality_review.json` part 2) |
| The 1e-9 inward nudge | Applies **only** to the M and V band targets. N is not nudged, so the nudge cannot conflict with norm preservation. The feasibility test of the nudged set shrinks it by a relative 1e-9, which only matters in measure-zero cases. **Safe in float64.** **Not safe after a float32 cast:** float32 relative resolution ≈ 6e-8 ≫ 1e-9, so a channel projected onto the nudged M/V edge can cross the bound by ~1e-7 relative when cast to float32 for the fp32 model. The plan's E-3 says feasibility is "recomputed from the stored noise in float64"; it does not say which array (pre- or post-cast) | INFERRED → **blocking defect B2** |
| Degenerate inputs | `v_c == 0` (a constant channel) returns `(x, False)`, which is safe. **Near-constant channels** (v_c ≲ hi·e^{−40} ≈ 4e-18) can leave the bisection bracket [−20, 20] without reaching the target, and the function then returns **ok = True with N violated.** **Non-finite inputs:** if x contains inf, v becomes NaN, every comparison involving NaN is False, and the function returns a NaN array **with ok = True** | INFERRED (static, IEEE semantics) |
| No silent infeasible return | **Not guaranteed by `project_mvn_exact` alone** (previous row). Feasibility depends on `feasible()`, and `feasible()` **accepts NaN arrays**: `np.abs(NaN).max() > b` is False, and so is `abs(NaN − norm2) > tol`, so every violation flag is False and the result is "feasible". A diverged optimiser iterate (NaN/inf) would therefore pass the hard gate | INFERRED (static) → **blocking defect B1** |
| Old alternating 5-iteration scheme | Not guaranteed: 0% feasible on null violators at L = 28 and 56; 6–33% after scale or combined perturbations | REPORTED |

**Verdict: the algorithm PASSES; the implementation has two blocking defects (B1, B2)**, fixable without any change of bound or method.

## 3. Issue 3: A/P repair and E-5

| Requirement | Finding | Label |
|---|---|---|
| Limited to noise variables | `repair_ap(x, b, norm2, ...)` optimises a tensor copy `y` of the noise only; it receives no model or checkpoint object | VERIFIED |
| Cannot modify model parameters or checkpoints | No model reference in `typicality.py`; no file writes | VERIFIED |
| 300-step limit | `for i in range(1, steps + 1)`, `steps = 300` | VERIFIED |
| Every returned feasible start passes the final hard check | Returns `ok = True` only after `feasible(yp)` is True, or when the input is already feasible. **Subject to B1** (a NaN array would pass) | VERIFIED (logic); INFERRED (B1 caveat) |
| An infeasible start cannot enter the optimisation | Requires the E2c runner, **which does not exist** | UNRESOLVED |
| Repair can fail | AR(1) ρ = 0.3 at L = 304: 0/60 repaired within 300 steps | REPORTED |
| **E-5 specification** (plan §2a) | States everything required:<br>• the sample is "not optimised";<br>• it enters "at its unprojected base objective (zero gain)";<br>• it is "marked 'no feasible start'";<br>• it stays in the aggregate;<br>• "more than 3 of the 32 clips (> 10%)" makes N4 "inconclusive (feasibility)";<br>• a feasible-only aggregate is also reported.<br>Note: "> 3 of 32" means ≥ 4 = 12.5%; "> 10%" is consistent | VERIFIED (text) |
| E-5 implementation | Not implemented (no runner) | UNRESOLVED |
| E-5 interpretation note | The imputed value is the coordination of an *atypical* raw base sample, so it is unbiased for the base level, with no optimisation credit. That is conservative for "gain"; it is not a typical-set result. The label "no feasible start" is therefore essential | INFERRED |

**Verdict: the specification PASSES; the implementation is UNRESOLVED (pending Phase 0).**

## 4. Issue 4: projection bias and comparator

| Claim | Finding | Label |
|---|---|---|
| 1.34% of starting hand-noises projected | `fraction_modified` = 0.013385 = 257/19,200. Computed in part 4 as the fraction of synthetic hands (32 real lengths × 600, duplicates included) failing `feasible()` with their own norm (so N holds trivially). Monte-Carlo se ≈ 0.08 percentage points (not reported in the plan) | VERIFIED (value); INFERRED (se) |
| Median change 0.14%, max 1.7% | `rel_change_among_modified`: median 0.00141, p95 0.0099, max 0.01667. Measure: ‖z − x‖/‖x‖ after E-1 + `repair_ap` | VERIFIED |
| 0 unrepaired | `"unrepaired": 0` | VERIFIED |
| KS ≤ 0.0055 | max over statistics = 0.00552 (L-scaled mean) | VERIFIED |
| "About 10% of clips have an atypical right-hand candidate" | **Computed, not counted:** 1 − (1 − 0.0134)^8 = 0.102 | INFERRED |
| No claim that projection leaves the generated motion unchanged | The plan states "its effect on generated coordination is not measured … equivalence is **not** claimed" | VERIFIED (text); **UNRESOLVED (science):** needs model execution |
| C-c2 revised: primary typical-only, secondary all-candidate, "comparator-sensitive" | Present in plan §2 C-c2, §2a and §6 | VERIFIED |
| C-c2 reflected in report and checklist | **Not in the Stage 4 report** (acceptable: C-items are campaign pre-registrations; the registered E2c row is unchanged). **Not in the checklist**, whose E2c step still reads "(i) Unrestricted per-sample noise optimisation (N4)", which is inconsistent with C-c3 | VERIFIED → documentation correction D1 |
| Effect on interpretation | The typical-only comparator has on average ≈ 7.9 of 8 eligible right-hand candidates, so its level is expected to be slightly **lower** than the all-candidate level. That makes "reaching the level" marginally easier for N4. Hence secondary reporting and the comparator-sensitivity flag are required (present) | INFERRED |
| Gaps | (a) The N4 **start noise index** is not specified (C-c5 says only "1 noise per clip"). (b) The fixed **body noise** for N4 is not specified. (c) **C-c6 says "final (i)"**, but E-3 says the result is the **best feasible iterate**. They conflict | VERIFIED → D2, D3 |

**Verdict: the statistics are VERIFIED; the comparator spec PASSES in the plan; the documentation is inconsistent in the checklist and C-c6.**

## 5. Issue 5: short-clip offset limitation

| Claim | Finding | Label |
|---|---|---|
| Test design | `validate_typicality.py`: 1,000 samples per condition (`N_POW`); +0.3 added to channels 0–9 of null N(0, 1) noise; detection = any of M/V/A/P violated | VERIFIED |
| ≈ 30% at L = 56 | "any" 0.301 (M 0.296). 95% CI ≈ ±2.8 percentage points (se 1.45) | VERIFIED (value); INFERRED (CI) |
| Analytic check | Per channel P(\|N(0.3, 1/56)\| > 4.03/√56 = 0.539) ≈ P(z > 1.79) ≈ 3.7%; over 10 channels 1 − 0.963^10 ≈ 31%. Agrees | INFERRED |
| "99–100% at 150 frames and longer" | Tested only at L = 150 (0.988) and L = 304 (1.000). **"And longer" is an inference** (power rises with L for a fixed offset, since the bound shrinks as 1/√L). The plan's table states only the tested values, which is correct. **The chat summary generalised beyond the tests** | VERIFIED (values); INFERRED (monotonicity) |
| Shortest clip | At L = 28 (not tested), analytically ≈ 0.7% per channel, ≈ 7% for 10 channels. **The limitation is worse than the 56-frame figure at the shortest E2e clip.** The plan mentions L = 28 but gives no rate | INFERRED → add to the limitation text (D4) |
| Split at L = 100 | Specified only in plan §2a ("reported split by clip length (L < 100 vs ≥ 100)"). E2e lengths: 11 clips with L < 100, 21 with L ≥ 100. Not in the checklist | VERIFIED → D1 |

**Verdict: PASS**, with the L = 28 addition and no generalisation beyond the tested lengths.

## 6. C-c3 specification check (code vs plan §2a)

| Constraint | Code (`bounds`, `stats`, `feasible`) | Plan §2a | Match |
|---|---|---|---|
| N | `abs(‖x‖² − norm2) > 1e-6·norm2` (tolerance 1e-6 relative) | "exact projection"; E-3 says "N within 1e-6 relative"; the final wording says "preserved exactly" | **wording mismatch** (D5) |
| M | z_c/√L, z_c = Φ⁻¹(1 − (0.005/90)/2) ≈ 4.03 | same | ✓ |
| V | [χ²_L(a_c/2)/L, χ²_L(1 − a_c/2)/L], a_c = 0.005/90; uncentred second moment | same | ✓ |
| A | uncentred r_c; 4.03/√L | same | ✓ |
| P | 3.29/√(90(L − 1)) | same | ✓ |
| Lags 2–4 monitored | computed in `stats()` | monitored | ✓ (no flag threshold defined: D6) |
| Body-noise correlation, χ² position monitored | **not implemented** | monitored | UNRESOLVED (runner) and threshold undefined (D6) |
| Bounds changed? | `FAM` and `bounds()` are identical to the first C-c3 proposal | — | **no change** (VERIFIED) |
| New constraints introduced? | none beyond N/M/V/A/P | — | ✓ |
| Finiteness | **not checked** | not stated | **B1** |

## 7. Pre-registration amendment record (C-c2, C-c3)

| Amendment | Previous text | New text | Why | Evidence | Still unverified |
|---|---|---|---|---|---|
| C-c3 rev. 1 → 2 | "each hand's noise is projected after every step to keep its initial norm … Proposed bound: none beyond norm preservation" (first campaign plan, 2026-11-03) | five constraints N/M/V/A/P | your instruction: norm-only insufficient | `typicality_validation.json` | effect on generated motion |
| E-1 rev. 1 → 2 | "clamp channel means …; rescale channels …; rescale to the initial norm. Repeat (1)–(3) up to 5 times or until all of M, V and N hold" | exact one-shot projection | alternating not guaranteed | `typicality_review.json` part 2 | float32 behaviour (B2) |
| E-3 rev. 1 → 2 | "Only feasible iterates count … If none improves on the projected initial noise, the initial value is reported" | hard feasibility gate; failing iterates never reported | penalty does not guarantee A/P | part 3 | runner not written; B1 |
| E-4 rev. 1 → 2 | "first projected by E-1, plus the minimal penalty descent for A and P" | E-1 + repair ≤ 300 steps, stop at the first feasible iterate | precision | parts 3–4 | runner |
| E-5 (new) | — | the no-feasible-start rule | repair can fail | part 3 | runner |
| C-c2 rev. 1 → 2 | "best-of-8×8 for these 32 clips, computed from the existing dev-256 N = 8 GF dumps (clips 0–31) …" | typical-only primary (E2e A0), all-candidate secondary, sensitivity flag | raw candidates ≈ 1.3% atypical per hand | part 4 | model-based effect |

**Notes on the record:**
- The previous texts above are quoted from this session's edit record. The plan file itself was edited in place, and **no archived copy of the earlier plan exists**. To preserve history, this record should be kept with the plan (proposed correction D7: copy the current plan to `research/archive/STAGE4_CAMPAIGN_PLAN_<date>.md` before any further edit). **[VERIFIED: no archive copy exists.]**
- All amendments are **awaiting approval** (plan header: "Still awaiting approval: C-c1 … C-c6"). **[VERIFIED]**

## 8. Blocking defects

| # | Defect | Fix (no bound or method change) |
|---|---|---|
| **B1** | `feasible()` returns True for non-finite arrays; `project_mvn_exact()` can return a non-finite array with ok = True | `feasible()`: first `if not np.isfinite(x).all(): return False, {"finite": False, ...}`. `project_mvn_exact()`: reject non-finite input and output (ok = False), and verify N on the output (ok = False if outside 1e-6) |
| **B2** | The 1e-9 inward margin is below float32 resolution; E-3 does not say which array is checked | E-3: the hard check is applied to **the exact array passed to the model** (float32, upcast to float64 for computation). E-1: inward target margin 1e-5 relative (an internal target; registered bounds unchanged); after the cast, re-check, and re-project if needed |

## 9. Unresolved risks

1. **No E2c runner exists**, so E-3 (as a loop gate), E-5, the comparator filter, the length split and the monitoring are unverified [UNRESOLVED].
2. **The effect of projection or constraints on generated coordination** is unmeasured. It needs model execution [UNRESOLVED].
3. **The target 1.59% assumes independence across M/V/A/P** [INFERRED]. The evidence supports ≤ ~1.9% per length, not exact calibration.
4. **Detection power at L = 28 for small offsets ≈ 7%** [INFERRED]: static offsets are not excluded on short clips.
5. **Monitored-quantity flag thresholds are undefined** (lags 2–4, body correlation, χ² position).
6. **Lags ≥ 2 and cross-stream structure are unconstrained.** An optimiser could exploit them. They are only monitored [INFERRED].
7. **Near-constant channels** (v ≈ 0) in `project_mvn_exact` (covered by the B1 fix's N verification).
