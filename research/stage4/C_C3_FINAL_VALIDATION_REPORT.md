# C-c3 amendment 2: final validation report

*2026-11-03.*

**Scope (authorised):** fixes B1/B2, documentation corrections D1–D8, synthetic tests A–C, finalisation of C-c3 amendment 2.

**Not done:** E2c or any other experiment; R0; any model, checkpoint, dataset or generated-sample access; training. **No registered numerical bound changed.**

**Labels:** VERIFIED (checked directly) · REPORTED (earlier synthetic evidence) · INFERRED (reasoning) · UNRESOLVED (needs future model execution or code).

## Results

| Item | Result | Evidence |
|---|---|---|
| **B1** non-finite handling | **PASS** [VERIFIED] | `typicality.py`:<br>• `feasible()` tests `np.isfinite` before any comparison, and rejects a non-finite norm target;<br>• `project_mvn_exact()` rejects non-finite input and output, constant channels, numerically degenerate channels (centred energy ≤ 1e-24 × the lower band edge) and targets it cannot bracket;<br>• it returns ok = True only after `mvn_ok()` verifies N, M and V on the actual output.<br>Test A |
| **B2** float32 feasibility | **PASS** [VERIFIED] | Internal M/V inward margin 1e-5 relative (`INWARD_MARGIN`; registered bounds unchanged). `to_model_input()` casts to float32, checks finiteness and N/M/V on that exact array (upcast to float64), and re-projects up to 3 times otherwise, then fails. `repair_ap()` accepts only a model-input array that passes the full `feasible()`. N tolerance stays 1e-6 relative. Test B |
| **Test A** non-finite inputs | **PASS**: 21/21 | Cases: NaN (single, row, all), +inf, −inf, NaN norm target, at L = 28, 146, 304.<br>• All are rejected by `feasible`, `project_mvn_exact`, `to_model_input` and `repair_ap`.<br>• No ok = True ever came with a non-finite or out-of-bounds array.<br>• The **pre-fix** `feasible()` (`research/archive/typicality_pre_B1B2.py`) accepted NaN in 12/21 cases, which confirms B1 [VERIFIED].<br>**Run-1 note:** my extra "1e39 finite outlier" case was set to expect failure. That expectation was a test-design error: the pipeline projects in float64 *before* the cast, so it legitimately returns a finite in-bounds array. Run 1 reported 3 "failures" for that reason only. The expectation was corrected and the run repeated; run 1 is kept (`c_c3_fix_tests_run1.json/.log`) |
| **Test B** float32 feasibility, 10,000 cases | **PASS** | Design of review part 2: L = 28, 56, 146, 304 × {null M/V violators, offset, scale, global, combined} × 500.<br>• **Successful projections 10,000; failed 0.**<br>• **Post-cast N/M/V violations 0.**<br>• Non-finite 0.<br>• **Max relative norm error 7.07e-9** (tolerance 1e-6).<br>• **Max M boundary deviation −9.97e-6** and **max V deviation −9.95e-6** (relative; negative = inside the bound, consistent with the 1e-5 margin).<br>• Re-projections needed: 0.<br>• Informational: 150 projected cases still violate A/P (offsets and scales create lag-1 structure). Projection does not enforce A/P; E-4 repair and the E-3 gate handle them |
| **Test C** near-constant channels, 540 calls | **PASS**: 0 cases of ok = True with an N/M/V violation | **Fail safely (ok = False):**<br>• exactly constant channels (one, or all);<br>• a zero channel;<br>• near-constant 1e-15.<br>**Partial success, rest failing safely:** near-constant 1e-12 (26/40, 26/40, 12/40 ok at L = 28, 146, 304).<br>**Succeed with verified feasibility:** near-constant 1e-8; variance 1e-6 or 1e-3 on 10 channels; mixed 45 ordinary + 45 near-constant.<br>No float32 violation among the ok outputs |
| **D1** checklist | done | E2c step: constrained N4, the C-c2 comparator, split at L < 100 / ≥ 100 |
| **D2** start noise | done | C-c5: A0 hand noise k = 1; body fixed at A0 k = 1 |
| **D3** result definition | done | C-c6: best feasible iterate (E-3) or the E-5 imputation |
| **D4** short clips | done | +0.3 offset: ≈ 7% at L = 28, labelled **analytical**; no claims at untested lengths |
| **D5** N wording | done | "within a relative 1e-6 numerical tolerance" |
| **D6** monitoring | done | **non-gating** flags: lag-k (k = 2–4) > 3.29/√(90(L − k)); hand–body \|corr\| > 4.59/√L; ‖x‖² outside the central 99.9% of χ²_{90L}. No new gating condition |
| **D7** history | done | Plan archived to `research/archive/STAGE4_CAMPAIGN_PLAN_2026-11-03.md` (new file, nothing overwritten). Amendment record in plan §2b. Pre-fix code archived |
| **D8** calibration wording | done | "consistent with Monte-Carlo noise (z = 1.45; not significant)", plus the detectability limit (≤ ≈ 1.9% per length, not exact calibration), in the plan and the research log |

## Consistency of C-c3 amendment 2 (code ↔ plan ↔ checklist)

| Item | Code | Plan | Checklist | Status |
|---|---|---|---|---|
| Finiteness | `feasible` / `project` / `to_model_input` | §2a row "(all)", E-1, E-3 | "finiteness" | ✓ |
| N | 1e-6 relative | §2a N row (D5) | via C-c3 | ✓ |
| M, V, A, P | `bounds()`, unchanged constants | §2a | via C-c3 | ✓ |
| E-1 | exact, margin 1e-5, verified output | amendment-2 row | E-1 to E-5 | ✓ |
| E-2 | λ = 100 | ✓ | ✓ | ✓ |
| E-3 | `feasible` on the float32 model-input array | amendment-2 row | "checked on the float32 model-input array" | ✓ (loop gate: runner pending) |
| E-4 | `repair_ap` ≤ 300 steps, model-input check | amendment-2 row | ✓ | ✓ |
| E-5 | specification only | ✓ | ✓ | specification ✓, implementation pending |
| C-c2 | — | primary typical-only, secondary all-candidate, sensitivity flag | ✓ | ✓ |
| Split at L = 100 | — | ✓ | ✓ | ✓ |
| Limitations | — | short-clip offsets (56: 30% simulated; 28: ≈ 7% analytical); marginal shape | — | ✓ |

## Remaining risks (none blocking for approving the specification)

- **UNRESOLVED:** the E2c runner does not exist. The E-3 loop gate, E-5, the comparator filtering, the L-split and the monitoring flags are verified only as specification. They are to be implemented and self-tested in campaign Phase 0.
- **UNRESOLVED:** the effect of the constraints and the projection on generated motion is unmeasured (needs model execution). **No claim of "no effect" is made.**
- **INFERRED:** marginal shape (per-entry magnitude, kurtosis) is unconstrained. Test A showed that a single huge outlier is projected into a valid but spiky array. Recorded as a limitation; no new constraint was introduced.
- **INFERRED:** the 1.59% nominal assumes independent violations; the evidence supports ≤ ≈ 1.9% per length.
- **REPORTED:** the review parts 2–4 (`typicality_review.json`) were run with the pre-amendment-2 code (margin 1e-9). Test B re-establishes M/V/N feasibility under the amended code. The repair and bias statistics (parts 3–4) were not re-run; the 1e-5 margin changes the projection by ≤ 1e-5 relative.

## Readiness

**C-c3 amendment 2 is technically consistent, numerically safe on the tested synthetic cases, and ready for approval.**

It is approved through the campaign approval statement (campaign plan §6, updated to name amendment 2, the amended C-c5 and C-c6, and the limitations).

## Files

| Path | Content |
|---|---|
| `experiments/stage4/e2c/typicality.py` | amended code |
| `experiments/stage4/e2c/test_c_c3_fixes.py` | tests A–C |
| `experiments/stage4/e2c/c_c3_fix_tests.json`, `.log` | results of the final run |
| `experiments/stage4/e2c/c_c3_fix_tests_run1.json`, `.log` | run 1 |
| `research/stage4/STAGE4_CAMPAIGN_PLAN.md` | amended plan (§2, §2a, §2b, §6) |
| `research/archive/STAGE4_CAMPAIGN_PLAN_2026-11-03.md` | previous plan |
| `research/archive/typicality_pre_B1B2.py` | pre-fix code |
| `research/stage4/E2_EXECUTION_CHECKLIST.md` | D1 |
| `research/RESEARCH_LOG.md` | entry |
