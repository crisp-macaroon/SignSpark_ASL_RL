# C-c3 / C-c2 cross-document consistency (proposed; nothing applied)

*2026-11-03. Read-only. The corrections below are **prepared, not applied**; each needs your acceptance. None changes a numerical bound or the method.*

**Abbreviations:**
- **Impl.:** `experiments/stage4/e2c/typicality.py`;
- **Report:** `research/STAGE4_REPORT.md` rev. 4.0;
- **Checklist:** `research/stage4/E2_EXECUTION_CHECKLIST.md`;
- **Plan:** `research/stage4/STAGE4_CAMPAIGN_PLAN.md`.

## Consistency table

| Item | Impl. | Report | Checklist | Plan | Status |
|---|---|---|---|---|---|
| N4 described as | constrained (typical set) | "(i) unrestricted per-sample noise optimisation (N4)" (§15.2, registered) | "(i) Unrestricted per-sample noise optimisation (N4)" | "constrained to the base-typical set" | **Conflict, checklist** (D1). The report is the registered text; leave it, with the plan's §2a explaining the refinement |
| "typicality/KL bound" | N/M/V/A/P; KL in C-c4 | undefined number (registered) | absent | defined (C-c3, C-c4) | OK (the plan defines it) |
| N | 1e-6 relative tolerance | — | — | §2a "exact projection"; E-3 "within 1e-6"; final wording "preserved exactly" | **Wording conflict** (D5) |
| M bound | 4.03/√L | — | — | 4.03/√L | ✓ |
| V bound | χ² interval, a_c = 0.005/90 | — | — | same | ✓ |
| A bound | 4.03/√L, uncentred r_c | — | — | same | ✓ |
| P bound | 3.29/√(90(L − 1)) | — | — | same | ✓ |
| Finiteness | **not checked** | — | — | not stated | **Defect B1** |
| Array checked for feasibility | float64 input | — | — | "stored noise in float64" | **Ambiguous** (B2) |
| E-1 projection | exact one-shot, 1e-9 margin | — | — | exact one-shot, 1e-9 | ✓ (margin: B2) |
| E-3 hard gate | `feasible()` | — | — | present | ✓ (B1 caveat) |
| E-4 repair ≤ 300 steps | `repair_ap(steps=300)` | — | — | present | ✓ |
| E-5 no-feasible-start | not implemented | — | — | present | spec ✓, implementation pending |
| C-c6 result definition | — | — | — | "final (i)" vs E-3 "best feasible iterate" | **Conflict** (D3) |
| N4 start / body noise | — | — | — | unspecified | **Gap** (D2) |
| C-c2 primary / secondary / sensitivity | — | — | absent | present (§2, §2a, §6) | **Checklist missing** (D1) |
| Split at L = 100 | — | — | absent | §2a | **Checklist missing** (D1) |
| Short-clip limitation | — | — | absent | §2a (L = 56 rate; mentions L = 28 without a rate) | **Incomplete** (D4) |
| Monitored quantities and flag thresholds | lags 2–4 computed; others absent | — | absent | listed; no thresholds | **Gap** (D6) |
| "1.88% was MC noise" | — | — | — | §2a row; research log l. 278 bullet | **Overstated wording** (D8) |
| Approval status | — | — | — | "Still awaiting approval: C-c1 … C-c6"; §6 statement | ✓ |
| Revision history of the plan | — | — | — | edited in place; no archive | **Gap** (D7) |

## Prepared minimal corrections (not applied)

| # | File | Correction |
|---|---|---|
| **D1** | Checklist, Step 5 | Replace "- (i) Unrestricted per-sample noise optimisation (N4)." with "- (i) Per-sample noise optimisation (N4), constrained to the base-typical set C-c3 (campaign plan §2a, pending approval); comparator C-c2 (typical-only primary, all-candidate secondary, 'comparator-sensitive' flag); results also split at L < 100 / ≥ 100." |
| **D2** | Plan C-c5 | Add "(i) start: A0 noise k = 1 per clip (right and left hand), body = A0 body k = 1 (fixed); seeds as E2e." |
| **D3** | Plan C-c6 | Replace "or final (i)" with "or the reported (i) result (the best feasible iterate per E-3; E-5 imputation for clips without a feasible start)." |
| **D4** | Plan §2a limitation | Add "At the shortest E2e clip (L = 28) the analytic detection rate for this offset is ≈ 7% (not simulated). Detection rates beyond the tested lengths (56, 150, 304) are not claimed." |
| **D5** | Plan §2a N row and final wording | "‖x‖² equal to its initial value within a relative 1e-6 numerical tolerance." |
| **D6** | Plan §2a monitored list | Flag thresholds (non-gating):<br>• pooled lag-k (k = 2–4): \|·\| > 3.29/√(90(L − k));<br>• max \|corr(hand channel, body channel)\| > Φ⁻¹(1 − 0.005/(2·5400))/√L ≈ 4.59/√L;<br>• ‖x‖² outside the central 99.9% of χ²_{90L}. |
| **D7** | Plan | Before any further edit, copy it to `research/archive/STAGE4_CAMPAIGN_PLAN_2026-11-03.md`, and add an "Amendment record" section (C_C3_IMPLEMENTATION_AUDIT.md §7) |
| **D8** | Plan §2a and research log | "The 1.88% is consistent with Monte-Carlo noise (z = 1.45; not significant)" instead of "was Monte-Carlo noise". The detectability limit: "the evidence supports ≤ ≈ 1.9% per length (family-wise 95%), not exact calibration." |
| **B1** | `typicality.py` | Finiteness check in `feasible()` and `project_mvn_exact()`; an N check on the projection output |
| **B2** | Plan E-1, E-3; `typicality.py` | Check feasibility on the exact array fed to the model (float32, upcast). Internal inward margin 1e-5 relative; re-check after the cast |

**Proposed synthetic tests after B1/B2** (not run; they need your approval):
- (a) NaN/inf inputs are rejected by `feasible()` and `project_mvn_exact()`;
- (b) float32-cast feasibility of projected arrays at L = 28, 56, 146, 304 (10,000 cases);
- (c) near-constant-channel inputs.

All on synthetic arrays only, about 1 minute.

## Proposed final C-c3 specification (incorporating B1, B2, D2–D6; bounds unchanged)

> **C-c3 (E2c (i) typicality; new pre-registration, amendment 2; awaiting approval).**
>
> The noise used for N4 (per sample, per hand; x ∈ ℝ^{90×L}, the exact array passed to the model, evaluated in float64) must be **finite** and satisfy:
> - **N:** ‖x‖² = its initial value within 1e-6 relative;
> - **M:** \|mean_τ x_c\| ≤ 4.03/√L;
> - **V:** mean_τ x_c² ∈ [χ²_L(a_c/2)/L, χ²_L(1 − a_c/2)/L], a_c = 0.005/90;
> - **A:** \|r_c\| ≤ 4.03/√L, r_c = Σ_τ x_{c,τ}x_{c,τ+1} / Σ_τ x_{c,τ}²;
> - **P:** \|mean_c r_c\| ≤ 3.29/√(90(L − 1)).
>
> **Monitored (non-gating) with flags:** pooled lag-k, k = 2–4, > 3.29/√(90(L − k)); max hand–body channel \|corr\| > 4.59/√L; ‖x‖² outside the central 99.9% of χ²_{90L}.
>
> **Enforcement:**
> - **E-1:** exact one-shot M/V/N projection with an internal inward margin of 1e-5 relative; output rejected unless finite and N-satisfying.
> - **E-2:** A/P penalty λ = 100 (search aid only).
> - **E-3:** hard gate. No iterate failing any constraint or finiteness, evaluated on the model-input array, is reported, stored as a result or aggregated.
> - **E-4:** feasible start via E-1 plus noise-only repair, ≤ 300 steps.
> - **E-5:** no feasible start ⇒ not optimised; enters at its unprojected base objective with zero gain, marked "no feasible start". More than 3 of 32 such clips ⇒ N4 "inconclusive (feasibility)"; a feasible-only aggregate is also reported.
>
> **Start:** A0 noise k = 1 (hands), A0 body k = 1 fixed.
>
> **Result per clip:** the best feasible iterate (E-3), or the E-5 imputation.
>
> **Comparator (C-c2):** typical-only best-of-8×8 from E2e A0 (k = 1–8; atypical right-hand candidates excluded, not projected) is primary; all-candidate values are secondary; a disagreement is reported as "comparator-sensitive". Results are also split at L < 100 / ≥ 100.
>
> **Known limitations (not excluded):**
> - small static offsets on short clips: detected ≈ 30% at L = 56 (simulated), ≈ 7% at L = 28 (analytic);
> - unconstrained lags ≥ 2 and cross-stream structure;
> - the effect of constraints and projection on generated motion is unmeasured.

## Proposed approval statement for the research lead

> I accept the C-c3 implementation audit (`C_C3_IMPLEMENTATION_AUDIT.md`) and approve:
> - (1) defect fixes B1 (finiteness and N verification) and B2 (feasibility checked on the model-input float32 array; internal inward margin 1e-5);
> - (2) documentation corrections D1–D8 as listed in `C_C3_CROSS_DOCUMENT_CONSISTENCY.md`;
> - (3) the synthetic tests (a)–(c) listed there, on synthetic arrays only;
> - (4) the C-c3 amendment-2 wording as the specification to be pre-registered, subject to (3) passing.
>
> No numerical bound changes. This does not authorise E2c or any other experiment; campaign authorisation remains a separate decision.

## Proposed research-log entry (PROPOSED: not added until accepted)

> **2026-11-03, C-c3 implementation audit (PROPOSED, pending acceptance).** A read-only audit of `typicality.py`, `review_typicality.py` and the review evidence.
> - The five issues are verified: calibration PASS (wording "consistent with MC noise"); the exact projection algorithm PASS; repair and E-5 specification PASS (implementation pending); bias statistics verified; the short-clip limitation retained, including L = 28 ≈ 7% (analytic).
> - Blocking defects: B1 (non-finite arrays pass `feasible()`) and B2 (the 1e-9 margin below float32 resolution; the checked array is unspecified).
> - Documentation corrections D1–D8 are prepared.
> - No bound was changed. Nothing was executed.
