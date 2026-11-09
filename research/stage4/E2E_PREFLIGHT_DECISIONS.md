# E2e preflight decisions P-1 to P-14: specification basis and recommendations

*2026-11-03. Documentation only. Nothing was executed, and no registered threshold or code was changed.*

**Specification source:** `research/STAGE4_REPORT.md` rev. 4.0. Quotes give line numbers in that file.

**Classification of each decision:**
- **E**: explicitly specified;
- **L**: logically implied by specified text;
- **I**: an implementation choice the specification does not cover. These are new and must be approved; they are **never** to be described as registered.

## Decision table

| P | Specification basis (verbatim) | Class | Proposed interpretation | Effect on results | Can flip PASS ↔ FAIL? | Recommendation |
|---|---|---|---|---|---|---|
| **P-1** | §15.4.1 (l. 1112): "The family-wise false-failure rate must be < 1%. If not, the margins are widened, but never beyond: mean 0.05, variance [0.90, 1.10], correlation 0.05." Margins (l. 1104–1108): mean 0.03, variance [0.95, 1.05], (d) 0.035, (e) 0.035, (f) lag-1 "90% CI ⊂ [−0.03, 0.03]" | **Mixed:** see the P-1 detail below | **Registered:** the initial margins, the < 1% target, 1,000 null sets, three caps, recording before the run. **New (I):** the widening schedule, the (e) and (f) caps, the action if the caps are insufficient | Widening raises the T1 tolerance only where the null itself fails | **Yes:** a true deviation inside the widened band passes T1 instead of failing. Not widening can turn a calibration shortfall into a stop at step 0 | Adopt the **revised** P-1 below. **Withdraw the 0.05 lag-1 cap** |
| **P-2** | l. 556: "fraction of frames > 45°/frame up by ≤ 2 points"; l. 658: "the fraction of left-hand frames with speed > 45°/frame"; l. 1007–1008 (T6). "Speed" of a *frame* across 15 joints is not defined | **I** | A frame counts if **any** hand joint exceeds 45°/frame (max over joints) | Max-over-joints gives higher fractions and is sensitive to single-joint spikes, like the Stage 2 D4 wrist-spike definition (per joint). The mean over 15 finger joints rarely exceeds 45°, which would make the check nearly vacuous [I] | **Yes** (T6 left/right, hence D-c) | Approve max-over-joints as the gating definition; also report the mean-over-joints fraction descriptively |
| **P-3** | l. 681: "Bounds are percentile bounds: two-sided 95% where stated, one-sided 95% for the D-b and 'upper/lower bound' criteria." l. 682: "D-c is an intersection of sub-criteria, each tested at its own level … (an intersection–union test)." l. 1008 states the left-hand checks as plain thresholds ("left jerk ≤ +10%; … coord_lr not below A0 − 0.03"). l. 677: FD criterion "FD_cond − FD_A0 ≤ q₉₅" | **L** for jerk, extreme frames and coord_lr: "each tested at its own level" requires a test, not a point comparison. **E** for FD (point vs q₉₅) | Jerk ratio: one-sided 95% upper bound ≤ 1.10. Extreme-frame difference: upper bound ≤ 0.02. coord_lr difference: lower bound ≥ −0.03. FD: point ≤ q₉₅, as written. The same applies to the σ_R > 1 right-hand checks | See the P-3 detail below | **Yes:** bounds turn some point-estimate passes into fails (conservative) | Approve, stated as an interpretation of l. 682 |
| **P-4** | l. 1003: "Transmission: Δ(κ0.9-seed0) ≥ 0.05 on at least one side, 95% CI lower bound > 0. Monotone in κ (tolerance 0.01). Orientation robustness reported (pass on how many of 3 seeds)." | **E** for either-side transmission. **I** for how monotonicity and orientation aggregate across sides | Transmission as registered. **Per-side reporting is mandatory**; monotonicity is assessed on each side that transmits; orientation counts are reported per side | See the P-4 detail below | Only through the aggregation rules (monotone / orientation), which are reporting items, not gates | Approve, with the per-side reporting rule. **Code change needed:** per-side orientation counts and a monotonicity verdict on the transmitting side(s) |
| **P-5** | l. 1099: "the realised ε̃ for all active frames of the **256 samples** of the tested condition"; l. 1111: null sets "of the same size" | **E** | T1 on the first 8 noises (256 samples) even when n* > 8 | None beyond the registered design. The calibration size matches the test size | No | Approve as specified |
| **P-6** | l. 1032: "(a) Controlled-harness side: A0's first noise (k = 1) … i.e. existing A0 sequences, so no extra." The run order puts T0 (step 1) before A0 generation (step 2) | **L:** resolves the order of the two statements | A0 k = 1 is generated at step 1 through the harness and reused as A0's first noise | None: the same sequence either way | No | Approve |
| **P-7** | l. 1005: "S₁: the same three-way rule with the 90% CI of S₁ against [0.95, 1.05]"; the S₂ rule says "Inconclusive otherwise" | **E** | A straddle for S₁ is labelled "inconclusive" | Naming only | No | Approve as specified |
| **P-8** | l. 959: "fixed recorded seeds"; no values registered | **I** (values) | Noise seed 10,000,000 / 20,000,000 + 1000·j + k; bootstrap seed 0; T1 null seed 777 | Realised values depend on the seeds. Fixing them before the run prevents seed selection | Not systematically (any fixed seed is valid) | Approve; freeze in the authorisation record |
| **P-9** | l. 1005 (T5-A): "**Stop** on any fail" for "all BH and LR conditions"; §15.2 l. 944: stop gate "T0/T1/T2/T5-A fail (error)". **But** the run-order table l. 1067–1068 lists "—" (no stop) for steps 5–6 | **E** (T5-A row and §15.2); the run-order table is silent, not contradictory | A T5-A fail in any remaining BH/LR condition stops the run | A stop at step 5–6 prevents SS (step 7) and the T3/T4 summaries. A fail means Theorem 4's parity prediction is violated, i.e. an implementation or assumption error, so later results would be uninterpretable | Run completion, not a test verdict | Approve as specified; add "T5-A fail ⇒ stop" to the run-order table for consistency (wording-only fix, needs your instruction) |
| **P-10** | l. 981: "32 clips × 8 base noises each unless stated"; l. 1066: gate conditions at n*; T3/T4/T5-B do not state which noises to use for the gate conditions | **I** | T3/T4/T5-B use the first 8 noises for every condition, paired with A0's first 8 | It keeps κ-levels, seeds and conditions on an equal footing (monotonicity, orientation and efficiency compare like with like). Using all n* noises for the gate conditions only would narrow their CIs | **Yes, borderline:** a gate condition's transmission CI lower bound could cross 0 with more noises | Approve 8 for all as gating; report the n* version for the two gate conditions descriptively |
| **P-11** | §5.3 l. 417: "Exact KL (per active frame, × L)"; l. 1003: "Efficiency: Δcoord per KL nat, arm12 vs r60" (no threshold) | **L** | KL per sample = per-frame KL × L; efficiency = Δ / mean KL = Δ / (KL_frame · mean L) | See the P-11 detail below | No (descriptive; no threshold) | Approve; add a bootstrap CI for the efficiency ratio (code change) |
| **P-12** | l. 1150: "energy distance between standardised per-sample feature vectors, with a within-clip permutation test (1,000 permutations)"; the feature vector is not defined | **I** | Features = the eight T2 metrics, standardised by pooled mean and SD | Non-gating diagnostic | No | Approve |
| **P-13** | l. 644: "Also reported (descriptive, with CIs) S₄ … and S₃"; l. 1005: "S₄ and S₃ are descriptive only"; CI level not stated | **I** (level) | 95% percentile CIs | Descriptive. S₃ may be heavy-tailed or infinite (App. G.6.1), so its CI may be unstable | No | Approve; label the S₃ CI "unstable if T4-e fails" |
| **P-14** | l. 981: "body sampled once per noise, reused because z_b = ε_b"; l. 1032 (c): a body-identity check at k = 1 | **E** | Coupled conditions reuse A0's body; T0 (c) checks k = 1 bitwise | None; exact by construction (App. G, Thm 3 corollary) | No | Approve as specified |

## Detail

### P-1: registered thresholds vs new calibration procedure

**Registered (unchanged; the code uses exactly these as starting margins):**
- (b) mean: 90% CI ⊂ [−0.03, 0.03];
- (c) variance: 90% CI ⊂ [0.95, 1.05];
- (d) correlation ≤ 0.035;
- (e) cross-covariance vs design ≤ 0.035;
- (f) lag-1: 90% CI ⊂ [−0.03, 0.03];
- the family-wise null false-failure rate must be < 1% over 1,000 sets;
- caps: mean 0.05, variance [0.90, 1.10], correlation 0.05;
- final margins recorded before the real run.

**Not registered:**
1. **The widening schedule.** The preflight code uses +0.005 per round for any check whose own null failure rate is ≥ 0.25%. This is a new procedure.
2. **A cap for (e).** "Correlation 0.05" can reasonably cover (e): with unit-variance channels the cross-covariance is a correlation. This is an interpretation (L), not explicit.
3. **A cap for (f) lag-1.** **No cap is registered.** The preflight code used 0.05, which **introduces a new criterion**. Withdrawn.
4. **The action when the caps cannot reach < 1%.** Not registered.

**Revised proposal (for approval as a new, documented pre-run calibration procedure):**
- (a) Only checks with a registered cap may widen: mean, variance, (d), and (e) under interpretation 2.
- (b) **Lag-1 stays at the registered 0.03.**
- (c) Each round raises, by 0.005, every widenable check whose null failure rate is ≥ 0.25%, never beyond its cap.
- (d) If the family-wise rate is still ≥ 1%, stop before any generation and report. No further widening, and no new caps.
- (e) The calibration history (each round's margins and rates) is saved and reported.

**Feasibility [E, analytic, not computed from data].** n ≈ 37,600 active frames, so the CI half-width is ≈ 0.0085.

| Check | Null family-wise failure at the registered margin |
|---|---|
| (b) mean | ≈ 0.7% |
| (f) lag-1 | ≈ 0.8% |
| (c), (d), (e) | ≈ 0 |
| **Total** | ≈ 1.5% |

- Under the revised rule, the mean margin widens once to 0.035, making its failure rate ≈ 0. The family-wise rate becomes ≈ 0.8% < 1%, **with lag-1 untouched**.
- If the real null rate for lag-1 alone is ≥ 1%, E2e stops at step 0. That would be a procedural stop, not a T1 fail.

**Effect on verdicts:**
- Widening the mean margin from 0.03 to 0.035 means a true per-channel mean offset of about 0.027–0.035 could pass instead of fail.
- Implementation errors that T1 targets (wrong Σ blocks, untouched padding violated, scaling bugs) produce deviations far larger than 0.005 [I].

### P-3: statistical implications of bound-based thresholds

- **Bound version (proposed).** Each left-hand check is a one-sided non-inferiority test at α = 0.05: "no degradation beyond the threshold" is declared only if the 95% bound clears it.
  - At a true value exactly at the threshold, the false declaration rate is ≤ 5%.
  - D-c, as an intersection–union test, keeps its error ≤ 5% (l. 682).
  - With 32 clips, power is limited. A condition with a small true degradation, or none, may fail to *show* non-inferiority. Then D-c is "not reached", which is conservative and consistent with "no degradation **detected**" requiring evidence.
- **Point version (rejected).** At a true value equal to the threshold, the pass probability is ≈ 50%. Left-hand protection would then be a coin flip at the margin, and the "each tested at its own level" sentence would be meaningless.
- **Asymmetry.** Bounds can only remove passes, never create them, relative to point estimates, except in the rare case of a point estimate beyond the threshold, which also fails under bounds. So P-3 can turn **PASS → FAIL only**.

### P-4: why either-side transmission does not conceal a one-sided failure

- **What the test establishes.** The registered transmission criterion answers an **existence** question for the family (l. 1013, E2e "licenses" row): does some frame-local linear noise coupling raise output temporal coupling? One side suffices for that existence claim, because the coupling of each hand is constructed identically and independently (K_L, K_R). Transmission on one side shows that the noise-to-timing pathway exists in the shared hand network.
- **What it does not establish.** Bilateral transmission, or transmission for the hand not shown.
- **Safeguards (proposed rules):**
  - (1) Δ and its 95% CI are **always** reported for both sides.
  - (2) The verdict names the side(s): "transmission on R only" / "L only" / "both".
  - (3) Monotonicity is evaluated on each transmitting side, and reported for the other.
  - (4) Orientation robustness is counted per side.
  - (5) A one-sided result triggers **no** claim about the other hand.

  The current code reports per-side Δ and monotone vectors but aggregates orientation over sides. It needs a small reporting change on approval.

### P-11: statistical implications of the KL normalisation

- **Exactness.** KL per sample is exact per frame × L_j (App. G.4). The mean over samples is exactly KL_frame × mean(L), so no approximation enters.
- **Comparison is unaffected by the length convention.** The registered use compares arm12 with r60 on the **same clips and noises**. Their efficiency ratio is (Δ_arm / Δ_r60) × (KL_frame,r60 / KL_frame,arm), and mean(L) cancels. A per-clip alternative (mean_j Δ_j / KL_j) would weight short clips more and would not cancel; it is not proposed.
- **Interpretation caveat.** "Per nat" uses the total coupling KL of both hands (r directions each), while Δ is per side. That is consistent across the two conditions, so the comparison holds, but the absolute value is not a per-hand efficiency.
- **Uncertainty.** Efficiency is descriptive with no threshold. A bootstrap CI for the ratio is recommended (code change).

## Decisions that can change a PASS into a FAIL, or the reverse

| P | Direction |
|---|---|
| P-1 | widening the mean margin (0.03 → 0.035) can turn a T1 **FAIL → PASS** for small true offsets; not widening lag-1 can turn a run into a **stop at step 0** |
| P-2 | the definition of "extreme frame" can flip T6 / D-c **either way** |
| P-3 | **PASS → FAIL only** (conservative) for the T6 / D-c sub-criteria |
| P-10 | using n* instead of 8 for the gate conditions could flip a borderline T3/T4 transmission **FAIL → PASS** (rejected for gating) |
| P-9 | affects whether later conditions run, not any verdict |

No verdict effect: P-4 (transmission as registered; only reporting rules), P-5, P-6, P-7, P-8 (no systematic effect), P-11, P-12, P-13, P-14.

## Code changes required if you approve these recommendations

These are not made yet. Each is a reporting or procedure change; no registered threshold changes.

1. **P-1:**
   - exclude lag-1 from widening (remove the 0.05 lag-1 cap);
   - label the schedule "pre-run calibration procedure (preflight P-1, not registered)";
   - save the round history.
2. **P-2:** also report the mean-over-joints extreme fraction (descriptive).
3. **P-4:**
   - per-side orientation counts;
   - a monotonicity verdict on the transmitting side(s);
   - a side-naming verdict string.
4. **P-10:** a descriptive T3/T4 at n* for the two gate conditions.
5. **P-11:** a bootstrap CI for the efficiency ratio.
6. **P-13:** the S₃ CI caveat label.
7. **P-9 (documentation):** add "T5-A fail ⇒ stop" to run-order steps 5–6 in the Stage 4 report. Wording-only, on your instruction.

After the changes, the synthetic self-test would be rerun (no model, no data) before authorisation.
