# Stage 4 Report: research problem, MDP design and validation

**Revision 3.3a** (revision 3.3 plus a wording-only clarification in §15.4.3) · 2026-11-03 · Scope: ASL / How2Sign / released SignSparK checkpoints · Status: **for final review; Stage 4 NOT approved** (Stage 5 not started)

**This revision is documentation and mathematical review only.** No experiment, sampling, training, registration or contact took place. The derivations are in [Appendix G](stage4/appendix_gaussian_controller.md).

All generation numbers are **released-checkpoint results**, not reproductions of the paper (R10).

## Evidence labels

| Label | Meaning |
|---|---|
| [V] | Verified by our own runs |
| [P] | Paper-reported |
| [A] | Author-reported |
| [C] | Read from the upstream code |
| [D] | Mathematical derivation with proof (Appendix G) |
| [I] | Inference / reasoning |
| [E] | **Estimate, not measured** |
| [H] | Hypothesis needing an experiment |
| [U] | Unresolved |
| [Pr] | Proposal awaiting approval |

---

## Change log

### Revision 3.3a (wording-only clarification)

- §15.4.3: added a short paragraph stating three things about t*₂₅₆.
  - Its 95% bootstrap CI is used only to choose the R1/R2/R3 branch.
  - Its point estimate is a fixed constant in the T5-A margin.
  - No uncertainty from it is propagated into T5-A, which tests μ against zero.
- No equation, branch definition, threshold, test logic, run order, experiment or decision changed.
- This is not approval to run E0, E2d, E2e or any other experiment.

### Revision 3.3 (documentation only)

The Gaussian M-C design, the experiment order (E0; E2d → E2e → E2a → E2b → E2c) and all existing numeric thresholds are unchanged, except for the documented mathematical corrections marked **(MC)**.

| # | Your point | Change | Where |
|---|---|---|---|
| 3.3-1 | t*_dev reconciled | Split into **t*₃₂** (the 32 E2e clips: the D-a/D-b target, estimated, recomputed in every bootstrap replicate) and **t*₂₅₆** (all dev-256 references: a fixed pre-run constant used only for the T5-A margin and the degenerate-target rule; no uncertainty propagated, since T5-A tests μ against 0). **(MC)** D-a is "direction not assessable" if the 95% CI of t*₃₂ − m_A0 includes 0; without this, the direction could be decided by sampling noise | §6.5, §15.4.3 |
| 3.3-1b | — | **(MC)** The over-shoot flag rewritten direction-generally, d·(m − t*₃₂) > 0.10. The rev. 3.2 form assumed a negative target | §6.5 |
| 3.3-2 | Degenerate δ_S₂ | A pre-run branch rule from references only (R1 \|t*₂₅₆\| ≥ 0.20; R2 0.10–0.20; R3 < 0.10 or CI ∋ 0). **(MC)** A floor δ_S₂ ≥ 0.025: as δ → 0 the TOST becomes unpassable by construction. The floor equals the R2 value at 0.10, so the rule is continuous. Under R3, P1b is declared target-degenerate, SS is not run, and I report to you. **Neither δ_S₂ nor the branch can change once any E2e sample exists** | §15.4.3 |
| 3.3-3 | T2 fallback vs run order | **(MC)** The calibration loop on A0/A0′ now happens *before* the gate conditions, so n* is fixed before any coupled sample. Rev. 3.2 listed top-ups after the gate conditions, which was inconsistent with fixing n* first. New step-by-step stop table. **Calibration-inconclusive ⇒ continue**, with theory-conditional wording; fail/straddle ⇒ stop | §15.3.1, §15.4.2 |
| 3.3-3b | Guarantees vs evidence | New §15.4.4: Theorem 3 is a guarantee *conditional on* F1–F6. A table gives the empirical or programmatic evidence for each assumption. **F4 (no batch coupling) remains code-reading only and is stated as such.** Pre-specified wording for each outcome | §15.4.4 |
| 3.3-4 | Logs | Change log, decision log (D4.20 amended; D4.23–D4.24), U-A3/U-A9/U-A10, checklist, research log updated | §17–19; `RESEARCH_LOG.md` |

### Revision 3.2

The Gaussian M-C design and the experiment order (E0; E2d → E2e → E2a → E2b → E2c) are unchanged.

| # | Your point | Change | Where |
|---|---|---|---|
| 3.2-1 | S₃ finiteness | Statement (3) holds as an extended-real expectation (S₃ ∈ [1, ∞]) under T4-a to T4-d. A finite S₃ needs the new condition T4-e (e.g. A_R ≥ a > 0 almost surely), which is **not guaranteed** [U]. S₃ is therefore descriptive only; gating uses S₁/S₂ | App. G.6.1 |
| 3.2-2 | T5-A equivalence | S₂ is now a genuine TOST: the 90% CI of μ = E log(A_L/A_R) against ±δ_S₂, with pass / fail / inconclusive outcomes. The pre-specified margin is δ_S₂ = min(0.05, \|t*_dev\|/4), justified in §15.4.3. S₁ uses the same three-way rule | §15.3 T5-A, §15.4.3 |
| 3.2-3 | D-c | Renamed **"target-directed dominance without detected left-hand degradation"** (no longer "genuine"). It now **requires D-b (≥ 50% gap reduction) and no over-shoot**, in addition to D-a and the left-hand criteria | §6.5, §15.3, App. G.6.3 |
| 3.2-4 | D-b test | The test is now on the gap ratio ρ_g = g_cond/g_A0: a one-sided 95% upper bound ≤ 0.50. It is assessable only if g_A0 ≥ 0.10 (lower bound) | §6.5 |
| 3.2-5 | T2 calibration | Separated: (1) precision (measured); (2) false-failure under equality (derived); (3) error at the margin (a TOST property); (4) operating characteristics at d = 3, 5, 7.5, 10% (derived, normal approximation). A three-way pass / fail / straddle outcome | §15.4.2 |
| 3.2-6 | D-c aggregation | An exact per-sample → per-clip → population procedure. One joint clip-cluster bootstrap that recomputes t*_dev in each replicate. Intersection–union combination; SS conditions are exploratory across four | §6.5 |
| 3.2-7 | T0 runtime | T0 executions made explicit: the controlled side reuses A0 (no extra); the upstream side adds 32 body + 64 hand; a new regenerated body-identity check adds 32 body. Body sequences 576 / 2,112; totals 32–37 / 56–64 min [E]. E2d's own T0 is counted in E2d | §15.3.1 |
| 3.2-8 | Research log; reward status | Metadata updated. **New reward-validity status table: every reward component is a measurable statistic with *no* perceptual validation** | `RESEARCH_LOG.md`; §6.1 |

**Unresolved assumptions identified (not silently chosen):** listed in §18 (U-A1 to U-A9).

### Revision 3.1

| # | Your point | Change | Where |
|---|---|---|---|
| 3.1-1 | Theorem 4 | Explicit assumptions T4-a to T4-d. Results stated per statistic: ratio of means S₁ = 1, geometric ratio S₂ = 1, mean of per-sample ratios S₃ ≥ 1 (all mean-type, proved). **The probability statistic S₄ = P(A_R > A_L) is not determined by the marginals**; only the *joint* profile is unattainable. The r_dom target is corrected to the reference mean log-ratio t* (not yet computed); −0.274 is illustrative only | App. G.6.1; §0, §5.3, §6.1 |
| 3.1-2 | T2 scope | T2 is renamed the **eight-metric generated-motion marginal check**. The text states what it and its calibration establish and what remains untested; it is not a proof of distributional equivalence | §15.3, §15.4.2 |
| 3.1-3 | E2e runtime | Reproducible accounting: body passes, hand passes, sequences, calibration, metrics, top-ups. Default ≈ 37 min, worst case ≈ 59 min [E]; the 1.5 h cap is justified; a pre-registered run order makes partial results interpretable | §15.3.1 |
| 3.1-4 | Dominance evaluation | Four separate levels: **D-a** movement toward the target, **D-b** target proximity, **D-c** genuine dominance without left-hand degradation, **D-d** perceptual dominance. Each has an aggregation level and thresholds. **E2e can establish at most D-a to D-c; D-d needs human ratings** | new §6.5; §15.3 T5-B |
| 3.1-5 | Semantic claims | "Semantic non-regression guard" is replaced by **"secondary checks: no regression detected"**. The text states explicitly that these checks do not establish semantic preservation or translation quality | §0.1, §6.3, §7.1.1, §17 |
| 3.1-6 | Terminology | Unified across the summary, specifications, decision log and checklist: P1a/P1b; M-C/κ, M-C/σ; S₁–S₄; D-a…D-d; "T2 eight-metric marginal check"; "secondary checks (no regression detected)" | throughout |

### Revision 3, integrated

| # | Your point | Change | Where |
|---|---|---|---|
| I1 | Integrate Appendix G | The whole report has been rewritten on the Gaussian default. The residual (additive f_φ) controller appears **only** as a labelled non-default alternative (§5.6), never in the default pseudocode, diagrams or estimates | §5, §8, §11, §12, §17, §19 |
| I2 | E2e | Body–hand and L–R coupling are tested separately. The roles of the projections U, V, the rank, the strength κ and the seeds are explained. A hypothesis-driven arm-channel projection is added. **A fixed random projection feasibility test is distinguished from evidence about a learned controller** | §15.3, App. G.3 |
| I3 | Coordination vs dominance | Separated throughout: separate components (M-C/κ, M-C/σ), rewards, constraints, metrics and human items. Side-scale mechanisms are stated as hypotheses. **Genuine dominance vs left-hand suppression** has a measurable definition. Left-hand protection constraints are added | §5.2, §6, §7.1, App. G.6 |
| I4 | Equivalence testing; precision | Explicit TOST procedures for the noise and generated-motion marginals: metrics, margins, CIs, sample-count calibration, pass/fail. **Precision corrected:** the baseline and controlled samplers must be the same implementation with identical numerical settings | §15.4, App. G.0 F6 |
| I5 | Paired advantage | **Corrected.** In the pathwise gradient it has *no effect* (it is not variance reduction). As a REINFORCE baseline it would be *biased*. It is retained only as a common-random-number improvement estimator, and the two outputs are **different samples** | §6.2, App. G.7 |
| I6 | Memory and runtime | Recalculated for the Gaussian controller with full 10-step backprop, from the Stage 3 probe. Every unmeasured value is labelled [E] | §11 |
| I7 | E2 order | **E2d → E2e → E2a → E2b → E2c**, each with its own scope, pass/fail, time cap and stop gate. **No automatic switch to the residual controller if E2e fails** | §15 |
| I8 | Research log | Rewritten status; stale MANO, GPU-rental and RTX-2050 items resolved or marked superseded | `RESEARCH_LOG.md` |
| I9 | Safeguards | Restated (§16) | §16 |

**Corrections to my own earlier text in this revision:**
- (a) **Paired advantage:** previously described as gradient variance reduction. That was wrong (see I5).
- (b) **Precision:** "train bf16 if close to fp32" is replaced by the same-implementation rule.
- (c) **TOST intervals:** TOST at α = 0.05 uses **90%** CIs, not 95%.
- (d) **Side-scale KL arithmetic** in the first revision-3 draft (fixed in App. G.4).
- (e) **Runtime** re-derived (§11).

### Earlier revisions (summary)
- **Revision 2:**
  - claim scope limited to perceptual coordination;
  - three human-evaluation constructs;
  - crossed-effects power;
  - exact-KL discussion;
  - 1-step gradient invalidity;
  - M-D vs M-C capabilities.
- **Revision 3, first draft:**
  - Appendix G;
  - Theorem 4;
  - the κ/σ split;
  - the E2e tests;
  - the simulation-based power specification.

---

## 0. Summary

1. **No reward computable today is valid for text-only generation (GF-T2P)** [V]:
   - reference-similarity rewards favour a static mean pose;
   - back-translation does not track pose quality within a sentence;
   - coordination and handedness *statistics* are reachable without RL (chance pair selection, side swap) (§1.2).
2. **The GF deficits are structural** (§1.3):
   - **handedness:** the shared hand network cannot produce dominance for any weights (Prop 1 [D]);
   - **coordination:** independent streams bound it by text-locked timing, which is nearly zero (Prop 2 [I], matches data).
3. **Research problem (P1)** [Pr]: perceived cross-articulator structure in GF-T2P, as **two separate objectives**:
   - **(P1a) coordination**: arm–hand and left–right temporal coupling;
   - **(P1b) dominance**: a dominant right hand without degrading the left.
   - The claim scope is perceptual motion only (§0.1).
4. **Primary method (M-C)** [Pr]: a KL-regularised conditional-Gaussian noise controller over the **frozen** samplers, a contextual bandit optimised by pathwise gradients through the full 10-step sampler.
   - **M-C/κ** (marginal-preserving coupling) targets P1a. It keeps every stream's output distribution exactly as the base [D].
   - **M-C/σ** (side-dependent noise scale) targets P1b.
     - Coupling alone keeps equal hand marginals. Theorem 4 then fixes the mean-type dominance statistics at parity: ratio of means = 1, geometric ratio = 1, mean of per-sample ratios ≥ 1. So **no mean-type dominance target below 1 (e.g. the reference 0.76) is attainable by coupling** [D].
     - The probability statistic P(A_R > A_L) is not determined by the marginals.
     - Whether scaling achieves dominance without left-hand degradation is [H]; the evaluation levels are in §6.5.
   - The KL is exact and closed form [D]. The optimum is the reverse-KL projection of the reward-tilted distribution onto the family [D].
5. **Direct fine-tuning comparator (M-D)** [Pr]: per-stream ORW-CFM-W2. It cannot learn dominance, and can couple streams only through text-locked timing (§5.5).
6. **Gates before any training:**
   - human validation of the rewards (E1, deferred by you; requires E0 renders);
   - the bounded feasibility experiments E2d → E2e → E2a → E2b → E2c, each separately approved (§15).
7. **H0** (RL adds nothing beyond selection, side assignment and the N5 cascade) remains an acceptable outcome.

## 0.1 Research objective and claim scope

**Objective:** determine whether a KL-regularised RL controller over the frozen, released SignSparK samplers can improve **(P1a) perceived cross-articulator coordination** and, separately, **(P1b) hand dominance without left-hand degradation**, in GF-T2P motion.
- It must not degrade per-stream motion quality.
- It is compared with non-RL alternatives at matched cost.

**What a positive result would license:**
- Outputs rated by fluent ASL signers as more natural or better coordinated **as motion** in SMPL-X avatar renders, under the stated conditions (released checkpoint, How2Sign, reference length as an oracle).
- **No regression detected** on the per-stream non-inferiority checks or on the secondary checks listed below.

**What it would NOT license:**
- **Semantic correctness, intelligibility, or better translation.** The A3 different-sentence null shows coordination statistics are reachable with hands from another sentence [V].
- Real-world ASL production quality.
- Any comparison with the SignSparK paper's results (R10).
- Signer-independent or out-of-How2Sign generalisation.
- **A dominance claim based only on a ratio change:** a ratio change alone may reflect left-hand suppression (§6.1, App. G.6.3).

**Secondary checks (rev. 3.1 wording)** [Pr]:
- corpus-level BT (never alone);
- DTW-JPE, if SMPL-X becomes available (with the collapse caveat);
- the exploratory comprehension 4AFC (§7.1).

The only claim these support is: **"no regression was detected on the specified secondary checks"** (each pre-registered margin, reported with CIs). A detected regression beyond its margin invalidates the method.

**These checks do not establish semantic preservation, semantic correctness, intelligibility or translation quality:**
- BT does not track pose quality within a sentence (R6) and has a GT ceiling of BLEU-4 3.5;
- DTW-JPE is reference-based and confounded by one-to-many generation (V1–V3);
- the comprehension task is expected near floor for GF and is underpowered.

Absence of a detected regression is not evidence of no regression.

---

## 1. Evidence base

### 1.1 Facts carried forward
- **Generator:** non-autoregressive, whole-sequence rectified flow (a 1D U-Net with a transformer bottleneck) [C].
- **Time convention:** t = 0 is noise, t = 1 is data. Path x_t = t·x₁ + (1−t)·x₀; target x₁ − x̃₀; t ~ U[10⁻³, 1] [C].
- **Sampler:** fixed-grid Euler, step 1/10, t_k = k/10; keyframes re-imposed inside each velocity evaluation; **deterministic given the noise** [C].
  - **Not differentiable as released:** `@torch.no_grad`, `odeint_adjoint` with `adjoint_params=()` [C `rflow.py:19, 62, 111–120`].
- **Conditioning per stream:** one pooled 640-d M-CLIP vector ("The sequential aspect of text is lost" [C]); keyframe mask/values; a length-mask channel. Optional text CFG (off in our runs).
- **Hands:** one side-agnostic network; L (index 2i) and R (2i+1) are interleaved with identical text, length and keyframe inputs [C].
- **Streams:** separate body/hand/face networks with independent noise; per-sample normalisation, no batch coupling [C].
- **Text dropout:** active in `train()` mode only [C], so every use here must be in `eval()`.
- **Stage 3 baseline (test, GF):**
  - body error 23.1°, hand error 22.1°;
  - coordination 0.026 (reference 0.47);
  - L/R activity 1.00 (reference 0.70);
  - face articulation 0.65;
  - BT BLEU-4 0.79 (reference 3.53) [V].

### 1.2 Design-validation analyses (dev, first 256 clips × 8 candidates; existing dumps) [V]

| ID | Question | GF-T2P | KF2P (positive control) |
|---|---|---|---|
| A1 | Coordination for matched vs mismatched (body_r, hand_s) pairs | **0.025 vs 0.022**: streams independent | 0.373 vs 0.372 |
| A2 | Same-text timing agreement: body / R-hand; generated body vs reference | **0.055 / 0.009; 0.014** | 0.815 / 0.760; 0.744 |
| A3 | Best coordination over n×n pairs, n = 1/2/4/8 | 0.022 / 0.189 / 0.310 / **0.408** (reference 0.474) | 0.377 / 0.444 / 0.496 / 0.536 |
| A3 null | Best 8×8 with hands from a **different sentence** | **0.452** | 0.204 |
| A3 | R-hand error, coordination-selected vs mean; within-clip Spearman | 21.58° vs 21.75°; ρ = 0.005 | 4.93° vs 5.04°; ρ = −0.17 |
| A4 | Fraction with the right hand more active (reference / generated) | 93.8% / **48.9%** | 93.8% / 90.6% |
| A4 | L/R activity ratio, mean per clip: reference / generated / side-assignment rule | 0.76 / 1.08 / 0.80 | 0.76 / 0.78 / 0.76 |
| V1 | DTW own vs length-matched other reference; % own lower | body 53.5%, R-hand 52.3% | 99.6%, 99.6% |
| V2 | Effect of DTW-best-of-8 selection on error and articulation | body error 23.0 → 20.5°, articulation 0.94 → **0.85** | 3.38 → 3.03°, 1.01 → 1.00 |
| V3 | DTW of a static pose vs samples | static beats samples in **100%** of clips (body) | samples win |

**Interpretation:**
- [V] The GF streams are independent, with noise-driven timing. GF samples carry ~no clip-specific content (V1).
- [V] Reference rewards favour collapse in GF (V2, V3).
- [V] Coordination statistics are satisfiable by chance alignment (A3 null), so they are **perceptual-motion targets only**.
- [I] Handedness statistics are restored by a trivial rule.

### 1.3 Two structural results
- **Prop 1** [D]: in GF, (x_L, x_R) is exchangeable for **any** hand-network weights. So P[R more active] = ½ and E[A_L] = E[A_R]. Measured 48.9% [V].
- **Prop 2** [I]: with independent streams, E[corr(s_b, s_h)] ≈ corr(m_b, m_h)·√(ρ_bρ_h) ≤ √(ρ_bρ_h), where ρ is the text-locked share of timing variance (≈ the same-text agreement).
  - GF prediction 0.023 vs observed 0.025 [V].
  - KF2P consistent: the implied corr(m_b, m_h) = 0.47 ≈ reference 0.474.
  - Raising coordination with independent streams needs ρ_bρ_h ≳ 0.22, i.e. text-locked or collapsed timing.

---

## 2. The research problem

### 2.1 Candidate problems

| Problem | Evidence | Can RL change it? | Valid reward today? | Verdict |
|---|---|---|---|---|
| **P1a coordination** | A1–A3, Prop 2 | joint noise controller: in principle (noise-level coupling exact; output transmission [H]); per-stream fine-tuning only via text-locked timing | statistics valid on real data, **chance-satisfiable**; perceptual validity unknown | **Primary**, gated on E1 |
| **P1b dominance** | A4, Prop 1, Thm 4 | coupling: **no** [D]; side-dependent marginal: [H]; shared-weight fine-tuning: **no** [D] | statistic valid on real data; risk of suppression hacking | **Primary, separate objective**, gated on E1 |
| P2 face under-articulation (0.65) | Stage 3 | yes, within one stream | gameable; rendering basis caveat | secondary, later |
| P3 semantic content | BT −78%; V1 ≈ chance | little to elicit; pooled text | none | not now |
| P4 reference fidelity in GF | 23° errors | yes | **invalid** (collapse) | evaluation only, with caveat |
| P5 KF2P | small headroom | yes | yes | deprioritised (your decision) |
| P6 length (oracle) | all GF | controller variable | none | deferred, disclosed |

### 2.2 Decision

| Item | Explanation |
|---|---|
| Problem | GF-T2P produces independent, noise-timed streams and exchangeable hands. Real signing has coupled articulators (0.47) and a dominant hand (94%) |
| Decision | P1 = **P1a and P1b as separate objectives**, each with its own controller component, reward, constraints, metrics and human items |
| Reason | the largest verified deficits, mechanistically explained, measurable without a reference; the theory determines which formulation can work |
| Alternatives | P2–P6 |
| Evidence | §1.2–1.3, Thm 4 |
| Risks | perceptual irrelevance; H0; no semantic gain; dominance hacked by suppression |
| Validation | E1 (Phase 1, §6.4) before RL; E2e feasibility |
| Status | **Proposed** (P1 and M-C supported by you in principle) |

---

## 3. Real control inventory

| # | Control | Exposed? | Notes |
|---|---|---|---|
| C1 | Initial noise per stream and side | yes [C] | determines timing (A2); the M-C action |
| C2 | Candidate selection / pairing | post-hoc | N3′ |
| C3 | Side assignment | post-hoc | N9 |
| C4 | Keyframes per stream | yes [C] | only conditioning channel across streams (N5) |
| C5 | Text CFG scale | yes [C] | per-side possible by separate calls [H] |
| C6 | Steps / sampler | yes [C] | not a coupling control |
| C7 | Length | yes [C] | oracle; P6 |
| C8 | Text string | yes [C] | — |
| C9 | Weights (LoRA / bottleneck) | by training | M-D |
| C10 | Per-step control added to x_k | via a sampler wrapper | F4; not in this design |
| C11 | Side token / cross-stream input | **architecture change** | N7; exploratory only |

---

## 4. Candidate formulations F1–F6

### 4.1 Classification
- **Genuine policy optimisation:**
  - F1-amortised (the noise policy, M-C);
  - F2 (multi-step SDE MDP);
  - F4 (KL-regularised SOC);
  - F3 (pathwise optimisation of a deterministic policy, DPG-like).
- **Reward-weighted supervised:** F5 (ORW-CFM-W2/RWR).
- **Inference-time search, no learned policy:** best-of-N, pair selection, per-sample noise optimisation. These are comparators.
- **F6 is a problem structure** (a cross-stream state and reward), realised by F1 (M-C) or by F2/F5 per stream (M-D).

### 4.2 Comparison (GF, no keyframes)

| | **F1: contextual bandit over the frozen sampler (M-C)** | F2: K-step SDE MDP | F3: one-step reward gradient | F4: KL-regularised SOC | F5: reward-weighted regression |
|---|---|---|---|---|---|
| State | (e(c), L, ε⁰) | (e(c), L, t_k, x_k) | (e(c), L, t, x_t) | (e(c), L, t, X_t) | (c, x₁) |
| Action | ε̃ = μ + DAε⁰ (Gaussian family, §5) | x_{k+1} ~ Gaussian | velocity | drift control | implicit |
| Transition | deterministic 10-step Euler, frozen | stochastic SDE | one-step map | memoryless SDE | n/a |
| Reward | terminal | terminal | on x̂₁ (differentiable) | terminal, differentiable | weight |
| Policy | N(μ, DΣD) per frame; generator frozen | Gaussian per step, θ trained | deterministic v_θ | controlled drift | v_θ |
| Optimiser | pathwise gradient; **exact closed-form KL** | GRPO/PPO-clip + KL | backprop + anchor | adjoint matching | weighted CFM + W2 |
| Target | reverse-KL projection of the tilted q* onto the family [D] | approximate tilted | none (collapse-prone) | exact tilted | collapses without W2 |
| P1a | noise-level coupling exact; transmission [H] | only via ρ (Prop 2) | same | same | same |
| P1b | **mean-type statistics S₁–S₃ not by κ (Thm 4)**; by σ [H] | **impossible (Prop 1)** | impossible | impossible | impossible |
| Capability preservation | weights frozen; κ: exact per-stream marginals | weights change | weak | KL | W2 |
| Compute (A4000) | §11: ≈ 10–11 GiB [E] at batch 4 | heaviest (G ≥ 24) | cheapest | complex | moderate |
| Role | **primary** | M-D option | ablation | deferred | **M-D default** |

**PPO on tokens or frames is rejected:** there are no tokens, the generator is not frame-autoregressive, and U4 found PPO importance ratios fragile for supervised-pretrained continuous-action transformers [P].

---

## 5. Recommended MDP: M-C, the conditional-Gaussian noise controller [Pr]

### 5.1 Formal definition (horizon-1 contextual bandit)

| Element | Definition | Justification |
|---|---|---|
| Context ρ₀ | (c, L) uniform over **How2Sign train** clips. e(c) is cached from the frozen M-CLIP; L is the reference length (oracle, disclosed) | dev for selection, test once |
| State s | (e(c), L, ε⁰), ε⁰ ∈ ℝ^{240×304} ~ N(0, I) | **fully observable**: the output is a deterministic function of (s, a) [C] |
| Policy parameters | h_φ(e(c), L) → (U_L, V_L, κ_L), (U_R, V_R, κ_R), (σ_L, σ_R). **Never a function of ε⁰** (App. G.1) | keeps q Gaussian and the KL exact |
| Action a | ε̃(τ) = D·A·ε⁰(τ) for active frames τ ≤ L; padded frames ε̃ = ε⁰. A is block lower-triangular coupling; D = diag(1, σ_L, σ_R). μ = 0 by default (mean shift deferred, App. G-c3) | App. G.1 |
| Transition P | **deterministic:** x = G₁₀(ε̃) = (g_b(ε̃_b), g_h(ε̃_L), g_h(ε̃_R)), the released networks, eval(), unrolled 10-step Euler with **the same numerical implementation for base and controlled runs** | App. G F6; §5.4 |
| Reward | component-specific (§6): r_coord for M-C/κ; r_dom + left-hand constraints for M-C/σ | P1a/P1b separation |
| Objective | J(φ) = E[r(G₁₀(ε̃))] − α_κ·KL_coupling − α_σ·KL_scale − λ·C (constraints) | App. G.4, G.7 |
| Face | base noise; reported unchanged | identifiability |

**Why horizon 1:** the controller acts once, before generation, with no intermediate feedback. Per-step control (C10/F4) would need a memoryless SDE and much more implementation.

### 5.2 Components

| Component | Parameters active | Objective | Guarantees [D] | Hypotheses [H] |
|---|---|---|---|---|
| **M-C/κ** (P1a) | U, V, κ (σ = 1) | r_coord − α_κ·KL_coupling | every per-stream noise and output marginal = base; body outputs sample-wise identical; exact KL | coupling transmits to output timing (E2e T3/T4) |
| **M-C/σ** (P1b) | σ_L, σ_R (K = 0) | r_dom − α_σ·KL_scale, s.t. left-hand protection (§6.1) | body marginal = base; right-hand marginal = base if σ_R = 1; exact KL | scale moves activity monotonically, and does so without suppression signatures (E2e T5-B/T6-B) |
| M-C/κσ | both | sum | as above | only after each has been evaluated alone |

### 5.3 Mathematical summary (full proofs in App. G)

**Joint law** [D]:
- ε̃(τ) ~ N(0, DΣD), with Σ = AAᵀ.
- **Σ blocks:**
  - Σ_bb = Σ_LL = Σ_RR = I;
  - Σ_Lb = K_L;
  - Σ_Rb = K_Rb;
  - Σ_RL = K_RbK_Lᵀ + K_RL S_L (the L–R dependence is partly *induced* by body coupling).

**Positive-definiteness** [D]:
- ‖K_L‖₂ < 1 and ‖K_R‖₂ < 1 (K_R = [K_Rb, K_RL] **jointly**), plus σ > 0.
- Guaranteed by K = U diag(κ) Vᵀ with Stiefel U, V and κ ≤ 0.95.
- This gives a closed-form S = I − U diag(1 − √(1 − κ²)) Uᵀ.

**Exact KL** [D] (per active frame, × L):
- KL_coupling = −½Σlog(1 − κ_{L,i}²) − ½Σlog(1 − κ_{R,i}²);
- KL_scale = ½Σ_hand channels(σ² − 1 − log σ²).
- **Exact iff** the parameters are ε-independent, ‖K‖₂ < 1, σ > 0, and the base noise is i.i.d. N(0, 1).

**Marginals** [D, Thms 2–3]:
- Under M-C/κ every stream's noise is exactly N(0, I), and its generated motion has exactly the base law given (c, L).
- **Conditions:** eval(), identical implementation, padded frames untouched.
- **Not guaranteed:** timing transmission; sample-wise invariance of the hands; finite-sample equality; perceptual or semantic quality; dominance.

**Dominance** [D, Thm 4; App. G.6.1].

*Assumptions:*
- T4-a: equal hand marginals per context (base; M-C/κ under eval and the same implementation);
- T4-b: the same activity functional for both sides;
- T4-c: A_s > 0;
- T4-d: integrability.

*Results:*

| Statistic | Under T4 | Unattainable by M-C/κ |
|---|---|---|
| S₁ ratio of means E[A_L]/E[A_R] | = 1 | any target ≠ 1 |
| S₂ geometric ratio exp E[log(A_L/A_R)] | = 1 | any target ≠ 1 |
| S₃ mean of per-sample ratios E[A_L/A_R] | ≥ 1 | any target < 1 (e.g. 0.76, dev-256; 0.70, Stage 3 test) |
| r_dom with log-target t | E[r_dom] ≤ −\|t\| | any value above −\|t\| |
| S₄ = P(A_R > A_L) | **not determined by the marginals** (= ½ only under exchangeability) | only the *joint* reference profile (S₄ ≈ 0.94 with S₃ ≤ 0.76) is unattainable (Prop 5); S₄ alone is [U] |

**Optimum** [D]:
- Over all q, the maximiser is q* ∝ p₀·e^{r∘G₁₀/α}, whose pushforward is the reward-tilted output distribution. This needs the same G₁₀ in training and deployment.
- Over the Gaussian family, the maximiser is argmin KL(q_φ‖q*) (reverse-KL projection). The gap is [U].

### 5.4 Ten-step gradient path

**(a) All ten steps are traversed** [D].
- ∂x₁₀/∂ε̃ = Π_{k=9}^{0}(I + h·J_v(x_k, t_k)).
- Every step appears, and dropping one drops the ε̃ dependence. There is no truncated variant in noise space.

**(b) The one-step shortcut is invalid** [D].
- Under the training objective, the ideal v*(ε, 0) = E[x₁|c, L] − ε.
- So G₁(ε) = E[x₁|c, L] is **constant in ε**, and the gradient is ≈ 0.
- Training through G₂ or G₄ optimises a *different* sampler, targeting p₀·e^{r∘G_K/α}, not the deployed tilted distribution.
- Paper Fig. 4's small 1-step error gap [P] is consistent with G₁ ≈ the conditional mean (good JPE, no noise-driven timing).

**(c) A differentiable sampler is required** [C].
- The upstream sampler is no_grad. An unrolled Euler loop must call the same `model(x, t, y, obs_x0, obs_mask)` on the same grid (t_k = k/10, h = 0.1).
- **E2d T0** verifies equivalence with upstream `decode` under identical settings.

**(d) Numerical implementation.**
- Base and controlled samples (and all comparisons) must use **one implementation with identical settings**: dtype fp32; the same TF32 flags as the Stage 3 runs (PyTorch defaults: matmul TF32 off, cuDNN TF32 on [I]; our scripts did not change them, and E2d will read and record the actual flags); the same device; eval().
- A different precision (e.g. bf16) is a *different* g. It could be adopted only for **all** arms (base and controlled), and only after E2d/E2a show agreement (speed-profile correlation ≥ 0.99, gradient cosine ≥ 0.95). The baseline would then be re-measured.
- Stage 3 dumps are not used as a comparison baseline inside E2 except for the T0 cross-check.

**(e) Activation checkpointing** [I, standard].
- Each Euler step is wrapped in `torch.utils.checkpoint` (non-reentrant).
- **Forward:** keep only x₀..x₉ (240 × 304 floats per sample, ≈ 0.3 MB).
- **Backward:** for k = 9..0, recompute step k from x_k, then backpropagate.
- SignSparK weights have requires_grad = False: input gradients only, no weight gradients or optimiser state.

**(f) Gradient health.** Log ‖∇_ε r‖ per step index (E2a). Gradient clipping on φ.

### 5.5 M-D: what per-stream fine-tuning can and cannot learn [Pr]

**Default:** ORW-CFM-W2 on the bottleneck or LoRA, per stream, with the other streams from base samples. Loss = E[w·‖v_θ − u_t‖²] + α_W·‖v_θ − v_ref‖², with w = exp(τ·Â) and Â a leave-one-out group-normalised reward.

| Capability | M-C | M-D (shared hand network) | Basis |
|---|---|---|---|
| Dominance | κ: not for mean-type statistics S₁–S₃ (Thm 4); σ: [H], evaluated at D-a to D-d | **no, for any weights** (Prop 1) | [D] |
| Cross-stream coupling | exact noise-level dependence; transmission [H] | only through text-locked timing (Prop 2); co-adaptation drives lower timing diversity | [D]/[I] |
| Per-stream quality beyond the base | no: reweights within the image of G | yes | [I] |
| Effect on other uses (KF2P) | none | possible; regression tests needed | — |

- **M-D′** (separate left/right hand copies) would break exchangeability. It is a pipeline change and **deferred** (needs your decision).
- **Pre-registered predictions:** M-D dominance ≈ 50%; any coordination gain comes with a higher same-text timing agreement ρ.

### 5.6 Non-default alternative: residual controller

- **Form:** T = id + f_φ(ε, e(c), L, side), as in Noise Hypernetworks.
- **Exact KL:** E½‖f‖² + E[tr J_f − log det(I + J_f)], valid if Lip(f) < 1.
- **½‖f‖² is exact only for ε-independent f.**
- There is no marginal-preservation guarantee and no closed-form KL (App. G.8).
- **It is not part of the default design and is not adopted automatically under any E2 outcome.** It would be one option among several presented to you after E2e/E2c (§15.2).

---

## 6. Reward design and validity: coordination and dominance separated

### 6.1 Components

| Component | Objective | Definition | Status today | Exploit | Protection / validation |
|---|---|---|---|---|---|
| **r_coord** = r_ah + r_lr | P1a (M-C/κ) | r_ah = −\|corr_τ(s_arm, s_hand) − 0.47\| per side (right arm–right hand; left arm–left hand); r_lr = −\|corr_τ(s_L, s_R) − 0.32\| | valid on real data; **chance-satisfiable** [V] | chance alignment; shared spikes; over-coupling (hence target-matching) | c_jerk; E1 coordination item; other-sentence null |
| **r_dom** | P1b (M-C/σ) | −\|log(A_L/A_R) − t*\|, where t* = the **reference mean log-ratio** from How2Sign train references (rev. 3.1 correction; value not yet computed [U]) | **E[r_dom] ≤ −\|t*\| under equal hand marginals** [D, Thm 4]; e.g. −0.274 if t* were log 0.76 (illustrative) | **left-hand suppression** | left-hand constraints below; evaluation levels D-a to D-d (§6.5) |
| **c_left** (constraints, M-C/σ only) | protect the left hand | (i) side calibration c_L ≥ log 0.8, where c_s = median log(A_s^gen / A_s^ref) at batch level using train references; (ii) left jerk ≤ base × 1.10; (iii) fraction of frames > 45°/frame up by ≤ 2 points; (iv) L–R coordination not below base − 0.03 | distribution-level reference statistics (train references, never at inference) | — | E2e T6-B; E1 |
| c_art, c_jerk (both components) | no collapse or exaggeration | articulation within ±10% of the base; jerk ≤ base × (1 + δ) | measured [V] | — | — |
| KL terms | stay near the pretrained distribution | exact (App. G.4); separate α_κ, α_σ | exact [D] | — | log each term separately |
| Excluded: BT, reference error / DTW | — | — | invalid in GF [V] | — | evaluation only, with caveats |

**D-c vs suppression:** defined in §6.5 (and App. G.6.3). D-c is "target-directed dominance without detected left-hand degradation"; the word "genuine" is no longer used.

**Reward-validity status (rev. 3.2).** Measurable statistics are distinguished from perceptually validated rewards.

| Component | Measurable statistic? | Valid as a statistic on real data? | Perceptually validated? |
|---|---|---|---|
| r_ah, r_lr (coordination) | yes | yes: GT 0.47 / 0.32 vs chance ≈ 0 [V] | **no.** Also chance-satisfiable (A3). Needs E1 Phase 1 #1 |
| r_dom (log-ratio to t*) | yes (t* not yet computed) | yes: reference right-dominant in 94% of clips [V] | **no.** Needs E1 Phase 1 #2, and D-d for any perceived-dominance claim |
| c_left, c_art, c_jerk (constraints) | yes | yes, as descriptive statistics | **no.** The thresholds (log 0.8, ±10%, +10%, +2 points) are conventions [U] |
| KL terms | exact [D] | n/a | n/a (a regulariser, not a quality measure) |

No component may be described as a quality reward until its perceptual validity criterion (§6.4) has passed.

**Side-scale mechanisms** (App. G.6.2):
- σ < 1 lowers activity; σ > 1 raises it (with an atypicality risk). Both [H].
- The base hand model is plausibly a mixture of dominant and non-dominant behaviour, so reaching D-c may need **both** σ_R > 1 and σ_L < 1 [I].
- A mean shift is deferred.

### 6.2 Aggregation, normalisation and the paired quantity [Pr]

**Aggregation:**
- Each component is optimised and reported **separately** first. A combined objective comes only after both are evaluated alone.
- Each reward term is z-normalised by base-model statistics on train.
- Constraints use dual ascent instead of hand-tuned weights (MotionRL reports weighted-sum instability [P]).
- Rewards are target-matching, not maximisation, to prevent over-coupling.

**Paired / common-random-number (CRN) quantity** (corrected; App. G.7). For a base noise ε⁰:

  Δ(ε⁰) = r(G₁₀(ε̃(ε⁰))) − r(G₁₀(ε⁰))

1. **Pathwise gradient:** the second term does not depend on φ, so **it has no effect on the gradient** and is not gradient variance reduction. It is not computed on training steps (saving one no-grad 10-step forward per step).
2. **Improvement estimation (monitoring and evaluation):**
   - Δ is a CRN estimator of the improvement.
   - Var(Δ) = Var r_ctrl + Var r_base − 2Cov, which is lower than unpaired estimation when the outputs are positively correlated. That holds near the identity and decays as the controller moves away.
   - **The two outputs are different samples** (only the body under M-C/κ is sample-wise identical). Δ estimates a distributional difference using correlated draws, not the improvement of one motion.
3. **REINFORCE fallback:** r(G₁₀(ε⁰)) is a function of the action (ε⁰ = T⁻¹ε̃), so as a baseline it **biases** the score-function estimator. Use leave-one-out group means over independent draws per context.

### 6.3 Independence of reward and evaluation
- **Rewards use** the coordination and dominance statistics.
- **Primary evaluation uses quantities not in the reward:**
  1. human ratings (separate coordination, handedness and left-hand-naturalness items);
  2. SMPL-X joint-space measures;
  3. distribution-level Fréchet distances (joint body+hand motion vs real; left-hand features vs reference-left);
  4. per-stream non-inferiority;
  5. corpus-level BT (a secondary check only: "no regression detected", §0.1).
- Reward statistics are reported and labelled as training objectives.
- Dominance is reported at the separate levels D-a to D-d (§6.5).

### 6.4 Validity criteria (two phases)

**Phase 1: pilot go/no-go, before any RL training.** Estimates with 80% CIs, not confirmatory tests.

| # | Criterion | Rule |
|---|---|---|
| 1 | Coordination relevance | 2AFC preference for coordination-selected over default ≥ 0.60, 80% CI lower bound > 0.50 |
| 2 | Dominance relevance | side-assigned ≥ default on handedness (≥ 0.55) **and** not worse on left-hand naturalness (≥ 0.45) |
| 3 | No hidden cost | coordination-selected not worse on per-stream naturalness (≥ 0.45) |
| 4 | Rubric reliability | Krippendorff's α ≥ 0.4 on the motion items |

- The other-sentence null (condition 6 vs 5) is reported; it sets the claim scope.
- **Failure of 1 ⇒ r_coord is not used. Failure of 2 ⇒ r_dom is not used.** That component is dropped (H0 for it).

**Phase 2: confirmatory, at Stage 6.** Sized by the §7.1.4 simulation.

---

### 6.5 Dominance evaluation levels (rev. 3.1)

Four levels are reported **separately**. Passing a lower level never implies a higher one.

**Common definitions.** Clip j (dev), noise k (shared across conditions, CRN).

| Quantity | Definition |
|---|---|
| Per-sample log-ratio | X_jk = log(A_L/A_R) |
| Per-clip | X̄_j = mean_k X_jk |
| Population estimate | mean over clips; **95% clip-cluster bootstrap CI** (2,000 resamples of clips; paired by clip across conditions) |
| Reference per clip | X_j^ref = log(A_L^ref/A_R^ref) from the dev reference of the same clip |
| Target (rev. 3.3: two distinct quantities, reconciled) | **t*₃₂ = mean_j X_j^ref over the same J = 32 E2e clips.** This is the D-a/D-b target, *estimated*, and its uncertainty is propagated by recomputing it in every bootstrap replicate (step 4 below). **t*₂₅₆ = the mean over all dev-256 references.** It is used **only** to fix the T5-A margin δ_S₂ and for the degenerate-target rule (§15.4.3). It is a pre-run design constant: computed once from references, before any generation, and treated as fixed (no uncertainty propagated into T5-A, which tests μ against 0, not against a target). In training, t* comes from train references |
| Side calibration | c_{s,j} = median_k log(A_{s,jk} / A_{s,j}^ref); c_s = mean_j c_{s,j} |
| Also reported (descriptive, with CIs) | S₄ = mean_j (fraction_k[A_R > A_L]) and S₃ |

| Level | Question | Aggregation | Threshold (pre-registered) | Evidence source |
|---|---|---|---|---|
| **D-a** movement toward the target | Did the condition shift the log-ratio in the target's direction? | δ = mean_j(X̄_j^cond − X̄_j^A0), paired by clip. Direction d = sign(t*₃₂ − m_A0) | **Assessable (rev. 3.3)** only if the 95% bootstrap CI of (t*₃₂ − m_A0) excludes 0; otherwise "direction not assessable". **Pass:** sign(δ) = d, \|δ\| ≥ 0.10, and the 95% CI of δ excludes 0 | E2e (T5-B); Stage 6 |
| **D-b** target proximity (rev. 3.2: test aligned with the 50% criterion) | How much closer to the reference? | gap ratio ρ_g = g_cond / g_A0, with g = \|mean_j X̄_j − t*₃₂\| (t*₃₂ recomputed in every replicate) | **Closer (≥ 50% gap reduction):** the one-sided 95% upper confidence bound of ρ_g (the 95th percentile of the paired clip-bootstrap distribution) is ≤ 0.50. **Assessable only if** the 95% CI lower bound of g_A0 is ≥ 0.10; otherwise D-b is "not assessable" (the base is already near the target). **At target (descriptive):** 90% CI of (mean_j X̄_j − t*₃₂) ⊂ [−δ_S₂, δ_S₂] (δ_S₂ from T5-A). **Over-shoot flag (rev. 3.3, direction-general):** d·(m_cond − t*₃₂) > 0.10, with d as in D-a. The rev. 3.2 form "m < t* − 0.10" silently assumed a negative target direction | E2e; Stage 6 |
| **D-c** target-directed dominance without detected left-hand degradation (rev. 3.2: renamed from "genuine dominance"; now requires D-b) | Is the shift toward the target achieved without detected suppression or degradation of the left hand? | the exact procedure is below | **D-a and D-b ("Closer") and no over-shoot flag**, and (i) for both sides, the change in e_s has a 95% upper bound ≤ +0.05; (ii) m_L ≥ log 0.8 (point) with a 95% lower bound ≥ log 0.75; (iii) all T6-B left-hand checks pass; (iv) the T6 right-hand checks pass. **Suppression** = D-a holds but (ii) or (iii) fails. **Not D-c ≠ suppression:** e.g. D-a without D-b is reported as "moved, not closer" | E2e; Stage 6 |
| **D-d** perceptual dominance | Do fluent signers perceive a dominant hand, without a less natural left hand? | human 2AFC, crossed rater × clip GLMM, marginal p_m | **Confirmatory (Stage 6):** handedness-item p_m ≥ SESOI 0.60 (Holm-adjusted; §7.1.4) **and** left-hand-naturalness p_m with lower 95% CI ≥ 0.45. **Pilot (Phase 1):** go/no-go estimates only (§6.4 #2), for non-RL side assignment | **E1 / confirmatory study only** |

**Exact aggregation procedure for D-a to D-c (rev. 3.2).** Dev clips j = 1..J (J = 32 in E2e); noises k = 1..n (the same ε⁰ list in every condition).

1. **Per sample (j, k), per condition:**
   - A_{L,jk}, A_{R,jk};
   - X_jk = log(A_{L,jk}/A_{R,jk});
   - left jerk J_{L,jk};
   - the fraction of left-hand frames with speed > 45°/frame, F_{L,jk};
   - left-right coordination ℓ_jk = corr_τ(s_L, s_R);
   - the 30-d left-hand joint-angle feature vector φ_{L,jk};
   - the same quantities for the right hand.
2. **Per clip:**
   - X̄_j = mean_k X_jk;
   - c_{s,j} = median_k log(A_{s,jk}/A^ref_{s,j});
   - J̄_{L,j}, F̄_{L,j}, ℓ̄_j = means over k.
   - Reference: X^ref_j = log(A^ref_{L,j}/A^ref_{R,j}).
3. **Population point estimates:**
   - m = mean_j X̄_j;
   - t*₃₂ = mean_j X^ref_j (the 32 E2e clips);
   - g = |m − t*₃₂|;
   - side-calibration error e_s = |mean_j c_{s,j}| (a population bias toward each hand's own reference);
   - m_L = mean_j c_{L,j};
   - left-jerk ratio = mean_j J̄_{L,j}^cond / mean_j J̄_{L,j}^A0;
   - extreme-frame difference = mean_j F̄_{L,j}^cond − mean_j F̄_{L,j}^A0;
   - coordination difference = mean_j ℓ̄_j^cond − mean_j ℓ̄_j^A0;
   - Fréchet distance FD between the pooled φ_{L,jk} (all j, k) and the dev-256 reference left-hand features. The criterion is FD_cond − FD_A0 ≤ q₉₅, where q₉₅ is the 95th percentile of FD_{A0′} − FD_{A0} over the bootstrap below.
4. **Uncertainty:** one joint clip-cluster bootstrap. In each of B = 2,000 replicates:
   - resample the J clips with replacement;
   - take each resampled clip's samples in **every** condition (cond, A0, A0′) together with its reference;
   - recompute all quantities in step 3, including t*₃₂ and therefore g, ρ_g and the D-a direction CI. So the target's sampling uncertainty enters D-a and D-b through the same replicates. (t*₂₅₆ is not resampled; it only fixes δ_S₂.)
   - Bounds are percentile bounds: two-sided 95% where stated, one-sided 95% for the D-b and "upper/lower bound" criteria.
5. **Combination:** D-c is an intersection of sub-criteria, each tested at its own level on the same replicates (an **intersection–union** test). The combined claim's error rate is ≤ the largest single level, so no multiplicity correction is needed *within* a condition.
6. **Across conditions:** the four SS conditions are reported individually. "M-C/σ feasible at D-c" (≥ 1 of 4) is **exploratory**: selection among four is not corrected, and E2e is a feasibility study, not confirmatory.

**Unresolved assumption [U]:** a percentile bootstrap with 32 clusters may be slightly anti-conservative. It is accepted for a feasibility study and must be revisited for any confirmatory use.

**E2e can establish at most D-a, D-b and D-c for fixed side scales on 32 dev clips. It cannot establish D-d (no raters), nor that a learned σ policy generalises.** Any statement about perceived dominance requires D-d.

## 7. Evaluator strategy

### 7.1 Human evaluation (design only; E1 deferred by you)

All raters are ASL-fluent humans, prioritising Deaf signers. No AI evaluator.

#### 7.1.1 Constructs

| Construct | Measured by renders? | Role |
|---|---|---|
| (A) Motion naturalness and cross-articulator structure: **coordination**, **handedness**, **left-hand naturalness** as separate items | yes, as perceived motion of an untextured avatar, compared relatively | the only basis for claims |
| (B) Semantic intelligibility | partially (comprehension 4AFC); expected near floor | secondary check only. Supports at most "no regression detected", **not** semantic preservation or intelligibility (§0.1) |
| (C) Real-world ASL quality | no | out of scope |

#### 7.1.2 Pilot (Phase 1: feasibility and variance estimation)
- **Participants:** 6–8 fluent raters; ethics review; consent; compensation; ASL instructions.
- **Stimuli:** 40 dev clips (4–10 s; excluding truncated and wrist-flip-flagged clips).
- **Conditions (all non-RL):**
  - (1) reference;
  - (2) KF2P;
  - (3) GF default;
  - (4) GF + side assignment;
  - (5) GF + coordination-selected pair;
  - (6) GF + other-sentence pairing.
- **Presentation:** neutral SMPL-X avatar, fixed camera, 20 fps, randomised, blinded, with attention checks.
- **2AFC items:** naturalness; coordination; handedness; left-hand naturalness (the last two for 3 vs 4).
- **Likert items:** the same constructs plus face. Then the comprehension 4AFC.
- **Analysis:** GLMMs with crossed rater/clip effects; estimates with 80% CIs.

#### 7.1.3 Analytic orientation (not a sample-size justification)
- The approximation Var(p̂) ≈ 0.25[(1 − ρ_i − ρ_r)/(IR) + ρ_i/I + ρ_r/R] shows that rater heterogeneity dominates.
- **No rater or clip number is a validated sample size.** The earlier "10–16 × 40–60" figure is withdrawn.
- Kenward–Roger does not apply to logistic GLMMs; see §7.1.4.

#### 7.1.4 Confirmatory power: simulation specification (to be run only after the pilot, with approval)

**Estimand and threshold:**
- **Estimand:** the marginal preference p_m. H0: p_m = 0.5.
- **SESOI:** p_m = 0.60 [Pr]. Sensitivity at 0.55 and 0.65.

**Generative model:** logit P(y_{rjk} = 1) = β₀ + β_pos·pos + u_r + w_j + v_{rj}, with:
- u_r ~ N(0, σ_r²): rater;
- w_j ~ N(0, σ_c²): clip;
- v_{rj} ~ N(0, σ_rc²): rater × clip, identifiable via a 10% repeat subset.
- β₀ is calibrated so that the **marginal** p_m equals the target (conditional ≠ marginal).

**Grids:**
- σ_r, σ_c ∈ {0.25, 0.5, 0.75, 1.0}, plus the pilot estimates and their upper 80% bounds;
- σ_rc ∈ {0, 0.3};
- β_pos ∈ {0, 0.2};
- R ∈ {6, 8, 10, 12, 16, 20, 24};
- I ∈ {30, 40, 60, 80};
- fully crossed and 50% incomplete-block designs.

**Missing data:**
- item-level MCAR at 5% / 10%;
- session-2 dropout at 15%;
- attention-check exclusion at 5%.

**Analysis per simulated dataset:**
- crossed-random-effects logistic GLMM;
- parametric-bootstrap LRT (≥ 500 draws);
- ≤ 2 confirmatory comparisons, Holm-adjusted at FWER 0.05;
- 95% CI for p_m by parametric bootstrap;
- non-convergence counted as non-rejection.

**Outputs:** ≥ 1,000 datasets per cell (Monte-Carlo SE ≤ 0.015). Report power at the SESOI, type-I error (must be ≤ 0.055), CI half-width, and convergence rate.

**Rule:**
- Choose the smallest (R, I) with power ≥ 0.80 under the **pilot upper-80% variance bounds** and type-I error ≤ 0.055.
- If none qualifies, report infeasibility and reduce the claim to estimation.

**Software:** [U]. R may be needed; installing it needs your approval.

### 7.2 SMPL-X (E0)
- **Licence:** personal, non-commercial research, no redistribution, cite [V, licence page]. You register; I cannot.
- **Enables:** renders for E1; FK joint metrics on released-checkpoint outputs (not paper reproduction); validation of the rotation-space metrics.
- **Does not provide:** semantics, a body shape or translation (not in the data), or FLAME-faithful faces.
- **Windows rendering:** the upstream visualiser uses EGL (Linux), so an alternative renderer is needed [I].
- **Effort:** 3–6 days [E].

### 7.3 Learned evaluator
- Deferred.
- A realism discriminator is the most viable option, as an evaluation-only metric.
- A semantic retrieval evaluator only if P3 is pursued.
- Acceptance only via agreement with human ratings on held-out conditions.

### 7.4 Minimum viable pathway [Pr]
1. Now: reference-free metrics + Fréchet statistics + corpus BT (secondary).
2. Before RL training: E0, then E1 Phase 1.
3. Later: the confirmatory study (simulation-sized); a learned evaluator only if needed.

---

## 8. Algorithm selection

### 8.1 For M-C

| Algorithm | Reward need | Variance | Bias vs target | Role |
|---|---|---|---|---|
| **Pathwise, exact-KL Gaussian family** | differentiable (all components are) | low | reverse-KL family projection [D]; gap [U] | **primary** |
| REINFORCE / RLOO over the same Gaussian policy | any | high (~73k-dim action) | unbiased with leave-one-out baseline (**not** the paired base, §6.2) | fallback |
| Low-dimensional action (noise time-shift) | any | low | restricted class | ablation if E2b supports it |
| Per-sample noise optimisation (unrestricted ε, or per-clip Gaussian-family parameters) | differentiable | — | not a policy | comparator N4 and family-capacity reference (E2c) |

### 8.2 For M-D

| Algorithm | Role |
|---|---|
| ORW-CFM-W2 | default |
| Flow-GRPO | if budget allows |
| DRaFT-1 | ablation, with an anchor |
| Adjoint Matching | deferred |

ReLIFT warning [P]: no naive same-batch SFT + RL mixing.

### 8.3 Pseudocode

**M-C training (default Gaussian family)** [Pr]
```
settings: frozen g_b, g_h (released weights, eval(), fp32, Stage-3 TF32 flags; requires_grad=False)
          cached E[c] (M-CLIP run once; encode_text bypassed), train contexts {(c,L)},
          base statistics B (z-normalisation, constraints, side calibration from train references),
          component ∈ {κ, σ};  α_κ, α_σ;  K = 10;  multipliers λ ≥ 0;  κ_max = 0.95;  σ ∈ [0.5, 1.5]
h_φ(e, L) → κ: {a_L, Ũ_L, Ṽ_L, a_R, Ũ_R, Ṽ_R}  |  σ: {b_L, b_R}       # identity at init:
          a → −∞ (κ≈0),  b = 0 (σ=1)
for step = 1..S:
    sample {(c_i, L_i)};  ε⁰_i ~ N(0, I_{240×304})
    κ: U = qr(Ũ), V = qr(Ṽ) (sign-fixed); κ = 0.95·sigmoid(a)
       K_L = U_L diag(κ_L) V_Lᵀ  (90×60);   K_R = U_R diag(κ_R) V_Rᵀ  (90×150)
       S_s = I − U_s diag(1 − √(1−κ_s²)) U_sᵀ
    σ: σ_s = exp(clip(b_s, log 0.5, log 1.5))
    for τ ≤ L_i:  z_b = ε_b;  z_L = K_L ε_b + S_L ε_L;  z_R = K_R[ε_b; ε_L] + S_R ε_R
                  ε̃ = (z_b, σ_L·z_L, σ_R·z_R)                      # padded frames: ε̃ = ε⁰
    x_i = G₁₀(ε̃_i)            # unrolled Euler t_k=k/10, per-step checkpoint, eval(), same settings
    r_i = r_coord(x_i)  if κ  else  r_dom(x_i)
    C_i = [c_art, c_jerk] (+ c_left if σ)                            # violations ≥ 0
    KL_i = L_i·(−½Σlog(1−κ_L²) − ½Σlog(1−κ_R²))   if κ
           L_i·(½Σ_ch(σ²−1−log σ²))              if σ               # exact (App. G.4)
    loss = mean_i( −r_i + λ·C_i + α·KL_i )        # no paired base term (no effect on the gradient)
    φ ← φ − η·clip(∇_φ loss);   λ ← max(0, λ + η_λ·mean_i C_i)
    every M steps (dev, same settings): reward metrics; CRN improvement Δ (base sample, no grad);
        held-out metrics; KL terms; min eig(Σ); ‖ε̃‖²/d; per-stream articulation/jerk;
        side calibration c_L, c_R; same-text timing agreement; ‖∇_ε r‖ per Euler step
select on dev; never test
```

**M-C inference**
```
ε⁰ ~ N(0,I); parameters = h_φ(E[c], L); ε̃(τ) = D·A·ε⁰(τ) for τ ≤ L (padded: ε⁰);
x = (g_b(ε̃_b), g_h(ε̃_L), g_h(ε̃_R)) with the same 10-step implementation (eval, fp32);
face from base noise. Overhead: one h_φ pass + per-frame 240×240 products.
```

**M-D (comparator)**
```
per step: G samples of the trained stream per text (others from base); r_j joint reward;
Â_j leave-one-out normalised; w_j = softmax(τÂ); loss = Σ w_j·CFM(θ; x_j) + α_W‖v_θ − v_ref‖²
```

---

## 9. Non-RL comparators

| ID | Comparator | Establishes | Needed? | Status |
|---|---|---|---|---|
| N1 | default sampler | baseline | yes | measured |
| N3′ | best-of-n×n pairing | what search achieves (coordination) | yes | [Pr] |
| N9 | side-assignment rule | trivial dominance fix (it changes marginals: max/min order statistics) | yes | [Pr] |
| N4 | per-sample noise optimisation | test-time alternative; upper reference for M-C | yes | E2c prototype |
| N5 | body→hand timing cascade via keyframes | explicit non-learned coupling | yes | approved for investigation; not implemented |
| N6 | SFT, same budget | separates training from RL (M-D) | for M-D | [Pr] |
| N7 | side token / cross-stream input | architectural ceiling | exploratory | deferred; no implementation |

## 10. Preserving pretrained capabilities
- **M-C:**
  - weights untouched;
  - KF2P unaffected;
  - KL(output joint ‖ base) ≤ the exact noise KL;
  - **M-C/κ preserves every per-stream output marginal exactly**;
  - M-C/σ changes hand marginals by design, so it is KL-bounded and left-hand quality is measured (§6.1).
- **M-D:** W2 anchor and regression tests. Original checkpoints stay read-only and SHA-verified.
- **Both:** report same-text timing agreement (diversity).

## 11. Computational feasibility: Gaussian controller, full 10-step backprop

**Measured inputs [V]** (`experiments/compute/out/memory_hand.json`; RTX A4000, 15.99 GiB; GiB = 2³⁰ bytes):
- full checkpoint weights 5.20 GiB fp32 (1.395B params; U-Net 834.8M = 3.11 GiB; M-CLIP ≈ 2.09 GiB);
- hand-stream unrolled reward-gradient probe (bottleneck trainable, default TF32 flags):
  - 1 step, batch 4: 5.96 GiB, 0.18 s;
  - 10 steps, batch 1: 7.14 GiB, 1.79 s;
  - 10 steps, batch 4: 10.74 GiB, 2.15 s.

**Derived per-unit activation cost [E]:** (10.74 − 5.96)/(9 × 4) ≈ **0.133 GiB per sample per stored Euler step**. A "sample-pass" = one U-Net call for one sample (body, or one hand).

**Gaussian-controller memory** [E] (per step: B contexts → B body + 2B hand sample-passes; controller ≈ 0.1–1M params, per-frame 240×240 transforms → negligible):

| Configuration | Weights resident | Activations | Estimated peak |
|---|---|---|---|
| body + hand U-Nets fp32, M-CLIP not resident, **no checkpointing**, B = 1 | 6.22 | 0.133 × 3 × 10 ≈ 4.0 | **≈ 10.7 GiB** (incl. ≈ 0.5 workspace) |
| same, B = 2 | 6.22 | ≈ 8.0 | ≈ 14.7 GiB (**exceeds the 14 GiB gate**) |
| **per-step checkpointing**, B = 4 | 6.22 | one recomputed step 0.133 × 12 ≈ 1.6, ×2 for backward transients ≈ 3.2 | **≈ 10–11 GiB** |
| checkpointing, B = 8 | 6.22 | ≈ 6.4 | ≈ 13–14 GiB (borderline) |
| any of the above with M-CLIP resident (no embedding bypass) | +2.09 | — | +2.1 GiB |

**Caveats [U]:**
- (i) The probe's gradients went to bottleneck weights. Input gradients through all layers may need more activation memory per step.
- (ii) The probe allocated bottleneck weight gradients (≈ 0.73 GiB) that M-C does not need, which pushes the other way.
- (iii) The body U-Net was not probed (same internal widths assumed).
- (iv) Fragmentation and cuDNN workspaces are not modelled.
- (v) Backward transients are assumed at 2× (an assumption).

**Runtime [E]:**
- The probe shows weak batch scaling at 10 steps: 1.79 s (B = 1) vs 2.15 s (B = 4), i.e. ≈ 1.67 s fixed + 0.12 s per sample per stream call.
- **Per M-C step at B = 4:**
  - body call (4) ≈ 2.2 s;
  - hand call (8) ≈ 2.6 s;
  - checkpoint recomputation ≈ +35%.
  - **Total ≈ 6.5 s, range 5–8 s.**
  - No paired base on training steps (§6.2); +≈ 1.5 s on logging steps only.
- 5,000 steps ≈ **7–11 h** [E].
- Dev evaluation (1,650 clips, body + hands, 10 steps) ≈ 20 min [E from V Stage 3 sampling].

**Other estimates [E]:**
- M-D ORW ≈ 8–10 GiB (bottleneck + bf16 reference).
- Flow-GRPO G = 24 is marginal.

**GPU rental:** not needed for any planned item. It is not requested.

**E2d measures the real figures; nothing above is treated as established.**

## 12. Architecture specifications

**D1: M-C training (Gaussian default):**
- **Inputs:** train text c → frozen M-CLIP (once, offline) → cached e(c) ∈ ℝ⁶⁴⁰; reference length L; ε⁰ ∈ ℝ^{240×304} ~ N(0, I) (body 60, L-hand 90, R-hand 90).
- **Trainable (only):** h_φ(e(c), L), a small MLP → coupling factors (Ũ, Ṽ, a) per hand and/or side scales b.
- **Deterministic parameter maps:** QR → Stiefel U, V; κ = 0.95·sigmoid(a); K = U diag κ Vᵀ; closed-form S; σ = exp(clip b).
- **Noise transform** (active frames only): z = Aε⁰ → ε̃ = Dz. Padded frames are passed through.
- **Exact KL block:** KL_coupling(κ), KL_scale(σ), logged separately. PD diagnostic: the min eigenvalue of Σ.
- **Frozen sampler** (eval, fp32, Stage 3 flags, requires_grad = False): an unrolled 10-step Euler loop (t_k = k/10). It calls g_b once per step (body batch B) and g_h once per step (hand batch 2B, L/R interleaved, identical text, obs_mask = 0, length mask), with per-step checkpointing.
- **Reward / constraint block:** speed profiles → r_coord (κ) or r_dom (σ); c_art, c_jerk, c_left (σ) against base and train-reference statistics.
- **Loss** = −r + λC + α·KL.
- **Gradient path:** reward → x₁₀ → all ten steps (activations only) → ε̃ → (K, S, σ) → φ.
- **Monitoring branch (no grad, logging steps only):** the base sample from the same ε⁰ → CRN improvement Δ.

**D2: M-C inference:** ε⁰ → h_φ(e(c), L) → ε̃ = DAε⁰ → the same frozen 10-step implementation (body, hands) + face from base noise → 6D rotations → D4.

**D3: M-D:** trainable bottleneck/LoRA of one stream; frozen bf16 reference v_ref; group samples → joint reward (other streams from base) → softmax weights → weighted CFM + W2.

**D4: Evaluation (independent of rewards):**
- held-out dev/test texts → rotations →
  - (a) SMPL-X FK metrics;
  - (b) renders → human items (coordination / handedness / left-hand naturalness / comprehension);
  - (c) Fréchet distances (joint motion; left-hand vs reference-left);
  - (d) per-stream non-inferiority;
  - (e) corpus BT;
  - (f) reward statistics, labelled.

## 13. Workflow (Stage 5–6, only after approval)
1. Freeze the protocol: dev selection, test once, seeds, oracle length disclosed, flagged-clip subsets.
2. Gates: E2 passes, then E0/E1 Phase 1 passes, then M-C/κ and M-C/σ trained **separately**. Then M-D at a matched GPU-hour budget. Then comparators at matched sample budgets.
3. Paired comparisons on identical clips and base noises (CRN), all through one implementation.
4. ≥ 3 seeds; bootstrap CIs; GLMMs for the human data.

## 14. MDP design audit

| Check | M-C | M-D |
|---|---|---|
| State sufficiency | pass (output deterministic in (s, a)); pooled text limits semantics, not P1 | pass |
| Action controllability | noise-level coupling exact [D]; **output transmission [H]** (E2e); gradients via 10 steps [H] (E2a); K = 1 invalid [D] | weights controllable; P1 reachability limited [D] |
| Transition implementability | **conditional:** the unrolled sampler must equal upstream (E2d T0) | pass |
| Reward validity | not established; P1a and P1b gated separately (§6.4) | same |
| Reward exploitation | chance alignment (human-validated only); spikes (c_jerk); **left-hand suppression** (c_left, genuine-vs-suppression test); off-manifold (exact KL, σ bounds) | + timing-diversity collapse |
| Episode suitability | horizon 1 exact | per algorithm |
| Data | train texts/lengths; train references only for distribution-level constraints | + references for CFM |
| Compute | estimated feasible [E]; **E2d gate** | feasible (ORW) [E] |
| Capability preservation | strongest; κ exact marginals [D] | anchor + regression tests |
| Independent evaluation | yes (§6.3) | yes |
| **Overall** | **conditionally valid**: E2e transmission, E1 reward validity, E2d feasibility | comparator with pre-registered predictions |

---

## 15. Validation plan

### 15.1 Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| FM1 | coordination improves; humans see no difference | E1 / final study | H0 for P1a |
| FM2 | other-sentence pairing preferred equally | E1 condition 6 vs 5 | perceptual-only scope (already the claim) |
| FM3 | fewer-step gradients don't transfer | E2a | K = 10 (default) |
| FM4 | noise steering cannot move timing | E2e, E2c | stop; options to you |
| FM5 | atypical noise artefacts (σ) | ‖ε̃‖²/d, articulation, jerk, renders | tighten σ bounds, raise α_σ |
| FM6 | M-D couples via timing collapse | same-text agreement ↑ | report (confirms Prop 2) |
| FM7 | comparators match M-C | paired comparison | H0 or amortisation-only claim |
| FM8 | test contamination | — | paired relative claims only |
| FM9 | rater noise | α < 0.4 | revise the rubric |
| FM11 | marginal guarantee silently broken (train mode, precision mismatch, padded frames) | E2e T1/T2; T0 | fix; Theorem-3 checklist |
| FM12 | dominance only by left-hand suppression | E2e T5-B/T6-B; E1 left-hand item | report; prefer N9 |
| FM13 | coupling does not transmit (E2e T3/T4 fail) | E2e | **stop and present options; no automatic switch** (§15.2) |
| FM14 | equivalence tests underpowered | calibration rule (§15.4) | report "inconclusive", not pass |

### 15.2 Sequence, dependencies and stop gates

**Nothing proceeds without your explicit go-ahead after each report.**

| Order | Step | Depends on | Scope summary | Pass → next decision | Stop gate | Cap |
|---|---|---|---|---|---|---|
| — | **E0** SMPL-X (independent track) | your registration | §15.5 | renders + FK usable → E1 can be designed | FK fails; rendering needs new software | 3–6 days of effort |
| 1 | **E2d** | — | T0 sampler equivalence; memory/time of the actual M-C step; M-CLIP hash check | T0 pass and a K = 10 configuration ≤ 14 GiB | T0 fail; no configuration fits | 45 min |
| 2 | **E2e** | E2d T0 (verified noise path) | §15.3 | transmission (T3/T4); dominance levels D-a to D-c (T5-B/T6-B), reported per component. No D-d | T0/T1/T2/T5-A fail (error); T3 and T4 fail (FM13) | 1.5 h (§15.3.1) |
| 3 | **E2a** | E2d (configuration) | gradient agreement: K ∈ {1, 2, 4, 10} outputs and ∇_ε r vs K = 10; gradient-norm profile; optional bf16 agreement for **both** arms | K_train confirmed (default 10); precision rule | non-finite gradients; norm ratio across steps > 10³ | 1 h |
| 4 | **E2b** | — | time-shift equivariance (δ ∈ ±4, ±8, ±16 frames) | low-dimensional action ablation viable (non-gating) | — | 1 h |
| 5 | **E2c** | E2d, E2a, E2e | (i) unrestricted per-sample noise optimisation (N4); (ii) per-clip optimisation of the **Gaussian-family parameters** (family capacity, U8) | whether amortised M-C is worth building; a family-gap reference | neither reaches the best-of-8×8 level within the typicality/KL bound | 2 h |

**If E2e fails** (T3 and T4 both fail, FM13), **I stop.** I present the evidence and these options for your decision; I do **not** switch to any of them automatically:
- (a) the E2c family-capacity test (can *learned/optimised* U, V find transmitting directions?);
- (b) the residual controller (§5.6);
- (c) per-step control (C10/F4, more implementation);
- (d) the N5 keyframe cascade;
- (e) accepting H0 for P1a via M-C.

Common constraints for all E2 steps:
- 32 fixed dev clips (the first 32 of the dev-256 subset) and dev references only;
- no test data; checkpoints read-only; no weight updates; no training of any network;
- fixed recorded seeds;
- one implementation and settings for all arms;
- outputs in `experiments/stage4/e2*/`.

### 15.3 E2e specification (pre-registered)

**Purpose:**
- Does the *Gaussian controller as derived* behave as the mathematics says (marginals, Theorem 4)?
- Does fixed coupling transmit to output timing, **separately** for body–hand and left–right?
- Do side scales reach dominance levels D-a to D-c (§6.5), or only shift the ratio by suppression? Perceptual dominance (D-d) is out of scope for E2e.

**Roles of the design variables** (App. G.3):

| Variable | Role in E2e |
|---|---|
| **U** (hand-side Stiefel, 90 × r) | which hand-noise directions receive the coupled signal |
| **V** (source-side Stiefel) | which source-noise directions (body 60, or left-hand 90) are copied |
| **r** | number of coupled directions; KL ∝ r |
| **κ** | per-direction correlation strength; KL per direction −½log(1 − κ²) |
| **Seeds** | each (U, V) seed is one arbitrary orientation. The networks' first layers mix channels in an unknown way, so transmission may depend on orientation; 3 seeds measure that sensitivity. **Noise seeds** (ε⁰) are fixed and shared across conditions (CRN) |

**Conditions** (32 clips × 8 base noises each unless stated; body sampled once per noise, reused because z_b = ε_b; hands resampled per condition):

| Group | Condition | Coupling | Tests |
|---|---|---|---|
| Base | A0, and A0′ (an independent base draw with different noise seeds, used for calibration) | none | reference, calibration |
| **Body–hand (BH)** | BH-r60-κ{0.3, 0.6, 0.9}-seed0 | K_L = κU_LV_Lᵀ, K_R = [κU_RV_Rᵀ, 0]; r = 60 (full body rank); K_RL = 0 | T3 transmission, monotonicity |
| | BH-r60-κ0.9-seed{1, 2} | as above, other orientations | T3 orientation sensitivity |
| | BH-arm12-κ0.9 | **hypothesis-driven V:** right-hand source = the 12 body channels of R_Elbow + R_Wrist; left-hand source = L_Elbow + L_Wrist (body channels are joint-major 6D blocks [C]); U random (seed 0); r = 12 | T3: does arm-specific coupling transmit more per nat of KL? |
| **Left–right (LR)** | LR-r90-κ{0.6, 0.9}-seed0 | K_L = 0, K_R = [0, κU Vᵀ]; r = 90; K_Rb = 0 | T4 transmission |
| | LR-r90-κ0.9-seed{1, 2} | other orientations | T4 orientation sensitivity |
| **Side scale (SS)** | (σ_L, σ_R) ∈ {(0.9, 1), (0.75, 1), (1, 1.15), (0.85, 1.15)} | K = 0 | T5-B, T6-B |

- **Count:** 16 conditions × 256 samples (+ the equivalence top-ups in §15.4).
- **Time:** default ≈ 32–37 min, worst case ≈ 56–64 min [E]; cap 1.5 h. Accounting in §15.3.1.

**Tests and pre-registered rules** (clip-cluster bootstrap with 2,000 resamples of the 32 clips; paired by clip across conditions):

| Test | Applies to | Metric | Rule |
|---|---|---|---|
| **T0** implementation | A0 | harness vs upstream `decode`, same ε⁰, same settings | max \|Δx\| ≤ 1e-4. Body under BH/LR identical to A0: max \|Δ\| ≤ 1e-5. **Fail ⇒ stop** |
| **T1** noise marginals | BH-r60-κ0.9-seed0, LR-r90-κ0.9-seed0 (strongest coupling) | §15.4.1 | all equivalence checks pass. **Fail ⇒ stop** |
| **T2** eight-metric generated-motion marginal check | the same two conditions (hands; the body is identical by T0) | the 4 metrics × 2 hands of §15.4.2 | all eight TOSTs pass ⇒ "equivalent within ±5% on these eight means". This is **not** full distributional equivalence (§15.4.2). Calibration failure (h > 1.5% at 32 noises) ⇒ calibration-inconclusive (FM14): **continue**, with theory-conditional wording (§15.4.4). **Fail or straddle ⇒ stop and report** |
| **T3** body–hand coordination | BH group | coord_arm_rhand and coord_arm_lhand (elbow + wrist vs finger speed), per sample | **Transmission:** Δ(κ0.9-seed0) ≥ 0.05 on at least one side, 95% CI lower bound > 0. **Monotone** in κ (tolerance 0.01). **Orientation robustness** reported (pass on how many of 3 seeds). **Efficiency:** Δcoord per KL nat, arm12 vs r60. **Specificity:** under the LR group, \|Δ arm–hand\| ≤ 0.02 |
| **T4** L–R coordination | LR group (direct) and BH group (induced, reported only) | coord_lr per sample | **Transmission:** Δ(LR-κ0.9-seed0) ≥ 0.05, 95% CI lower bound > 0. Orientation robustness reported. **Specificity:** under the LR group, arm–hand coordination unchanged (T3 specificity) |
| **T5-A** Theorem 4 check (rev. 3.2: genuine equivalence test) | all BH and LR conditions | μ = mean log(A_L/A_R) (S₂ = e^μ); S₁ via the ratio of mean activities; S₄ = P(A_R > A_L); S₃ (descriptive; may be infinite, App. G.6.1) | **TOST equivalence**, clip-cluster bootstrap with **90%** CIs. **S₂:** H₀: \|μ\| ≥ δ_S₂ vs H₁: \|μ\| < δ_S₂. **Pass** if the 90% CI of μ ⊂ (−δ_S₂, δ_S₂). **Fail** if the 90% CI lies entirely outside [−δ_S₂, δ_S₂]. **Inconclusive** otherwise. **S₁:** the same three-way rule with the 90% CI of S₁ against [0.95, 1.05]. **Stop** on any fail. Inconclusive results are reported, not treated as passes. **S₄ and S₃ are descriptive only** (S₄ is not pinned under asymmetric coupling, Prop 5) |
| **T5-B** dominance (SS group; rev. 3.2) | SS | the levels of §6.5 | Report **D-a** (movement), **D-b** (≥ 50% gap reduction; over-shoot flag), and **D-c** (target-directed without detected left-hand degradation) vs suppression, per condition, with the §6.5 thresholds and aggregation. **"M-C/σ feasible at D-c"** = at least one SS condition reaches D-c (exploratory). **D-d (perceptual dominance) is not assessed in E2e** |
| **T6** non-inferiority | BH/LR: via T2. SS: right hand (and body) | right hand with σ_R = 1: TOST ±5% (exact by theory). σ_R > 1: right jerk ≤ +10%, frames > 45°/frame ≤ +2 points | per condition |
| | SS: left hand | left jerk ≤ +10%; frames > 45°/frame ≤ +2 points; Fréchet distance of left-hand joint-angle features (15 joints × {mean, std} = 30-d) to **dev-256 reference left hands** not above A0's by more than the A0–A0′ 95th-percentile difference; coord_lr not below A0 − 0.03 | all four must hold for D-c (aggregation per §6.5) |

**What E2e can and cannot establish:**

| E2e outcome | Licenses | Does not license |
|---|---|---|
| T3/T4 pass (fixed random or arm-structured coupling transmits) | "some frame-local linear noise coupling raises output temporal coupling, at measured KL cost" (feasibility of the family) | that a *learned* controller will find useful, generalising, perceptually valid coupling; that the reward is valid; any perceptual or semantic claim |
| T3/T4 fail at all seeds and ranks | evidence against transmission for *these* orientations and ranks | impossibility for the family: learned U, V might find transmitting directions (U8). E2c (ii) tests family capacity directly, under its own approval |
| T5-B reaches D-c | "fixed side noise scaling shifted the log-ratio toward the dev reference and halved the gap (D-a, D-b), with no left-hand degradation detected on the specified checks (D-c), on 32 dev clips (exploratory)" | **perceptual dominance (D-d, needs human ratings)**; that a learned σ policy generalises; that the left hand is natural in any untested respect |
| T2 passes | "the eight hand-motion means are equivalent within ±5%" | full distributional equivalence (§15.4.2) |

### 15.3.1 E2e runtime accounting (rev. 3.1) [E]

**Throughput basis:** Stage 3 full-test sampling runs [V], 10 Euler steps, batch 32 clips, default flags, wall time including model load and I/O:
- **Body:** 2,183 sequences in 6.3–9.6 min ⇒ **0.17–0.26 s per body sequence** (the upper value came from a run overlapping other jobs).
- **Hands:** 4,366 hand sequences in 11.3–11.5 min ⇒ **0.16 s per hand sequence**.

E2e uses the same sampler and batch size, with noise injected before `decode`, so the same rates are assumed [E].

**Counts.** "Sequence" = one stream generated for one (clip, noise).

| Item | Rule | Default (8 noises/clip) | Worst case (top-ups to 32 noises/clip) |
|---|---|---|---|
| Base noise sets | A0 and A0′ (independent seeds) | 2 × 256 | 2 × 1,024 |
| **T0 executions (rev. 3.2, explicit)** | (a) **Controlled-harness side:** A0's first noise (k = 1) for each clip, i.e. existing A0 sequences, so no extra. (b) **Upstream side:** the same 32 noises through upstream `decode`: +32 body, +64 hand. (c) **Body-identity check:** the body for BH-r60-κ0.9-seed0, k = 1, regenerated through the controlled path (not reused), compared with A0's body: +32 body. *E2d's own T0 (unrolled vs upstream) is counted in E2d, not here* | +64 body, +64 hand | same |
| **Body sequences** | the body depends only on ε_b, so it is sampled once per distinct base noise (A0, A0′) and reused by the BH/LR/SS conditions sharing A0's noise; plus T0 (b) and (c) | 512 + 64 = **576** | 2,048 + 64 = **2,112** |
| **Hand sequences** | 2 per sample; 16 conditions × 256 samples (A0, A0′, 6 BH, 4 LR, 4 SS); plus T0 (b) | 16 × 512 + 64 = **8,256** | + top-ups for A0, A0′, BH-r60-κ0.9-seed0, LR-r90-κ0.9-seed0 (each +768 samples × 2 hands) = 8,256 + 6,144 = **14,400** |

**Time budget:**

| Component | Basis | Default | Worst case |
|---|---|---|---|
| Model load (body and hand models once, M-CLIP) | not measured separately; assumed | ≈ 2 min | ≈ 2 min |
| Body sampling | × 0.17–0.26 s | 1.6–2.5 min | 6.0–9.2 min |
| Hand sampling | × 0.16 s | 22.0 min | 38.4 min |
| Metric computation | per-sequence numpy rotation conversion, speeds, jerk, coordination; assumed ≈ 10 ms per sequence [E] | ≈ 1.5 min | ≈ 3 min |
| T1 noise statistics + synthetic calibration (1,000 null sets per stream, no model) | covariance of ≈ 30–60k × 90 matrices; assumed ≈ 0.1 s per set [E] | ≈ 2–5 min | ≈ 2–5 min |
| T2 calibration (A0 vs A0′) and bootstraps (2,000 clip resamples on precomputed clip means) | cheap; assumed | ≈ 1 min | ≈ 2 min |
| Energy-distance diagnostic (1,000 permutations; n ≤ 1,024; 30-d) | assumed | ≈ 1–2 min | ≈ 2–3 min |
| Fréchet left-hand features (dev-256 references, already in the dumps) | negligible | < 1 min | < 1 min |
| Step 0: t*₂₅₆ + its bootstrap CI (rev. 3.3) | 256 reference clips, no generation | < 1 min | < 1 min |
| **Total** | | **≈ 32–37 min** | **≈ 56–64 min** |

**Why a 1.5 h cap:**
- It leaves ≈ 40–60% headroom over the worst case for three things:
  - (i) the throughput assumption, since the Stage 3 rates include I/O overlap and E2e runs more, smaller condition batches;
  - (ii) the assumed (unmeasured) metric and calibration costs;
  - (iii) writing dumps.
- If the cap is reached, I stop and report the completed conditions.

**Pre-registered run order with stop rules** (rev. 3.3: reconciled with the T2 calibration fallback). Partial results stay interpretable at every step.

| Step | Action | Stop / branch rule |
|---|---|---|
| 0 | Compute t*₂₅₆ and its CI from existing dev-256 references; select branch R1/R2/R3 and δ_S₂ (§15.4.3); compute T1 synthetic null margins (§15.4.1). **No generation** | t*₂₅₆ not computable ⇒ stop. R3 ⇒ SS removed from step 7 |
| 1 | T0 (a)–(c) | any T0 failure ⇒ **stop** |
| 2 | Generate A0 and A0′ at n = 8 noises per clip; compute the T2 calibration half-width h | — |
| 3 | **Calibration loop (before any coupled condition):** if h > 1.5%, extend *A0 and A0′* to n = 16, recompute; if still > 1.5%, extend to 32. Fix n* = the smallest n with h ≤ 1.5%, or n* = 32 with T2 flagged **"calibration-inconclusive"** | no stop; n* is recorded **before** step 4 |
| 4 | Generate the gate conditions BH-r60-κ0.9-seed0 and LR-r90-κ0.9-seed0 at n* (the first n* noises of the shared list). Evaluate T1, T2 and T5-A | T1 fail ⇒ **stop**. T2 fail or straddle ⇒ **stop**. T5-A fail ⇒ **stop**. **T2 calibration-inconclusive ⇒ continue** (below). T5-A inconclusive ⇒ continue and report |
| 5 | Remaining BH conditions (n = 8) | — |
| 6 | Remaining LR conditions (n = 8) | — |
| 7 | SS conditions (n = 8), unless R3 | — |

**Why calibration-inconclusive continues while fail/straddle stops:**
- A fail or straddle is *evidence against* an implementation condition.
- A calibration-inconclusive result is *absence of sufficiently precise evidence*. It does not indicate a violation.
- T3/T4/T5-B, the actual feasibility questions, can still be answered.
- Every per-stream preservation statement in the E2e report is then labelled **"theory-conditional (Theorem 3); empirical eight-metric check inconclusive"** (see §15.4.4).

The cap still applies: at step 3, the n* = 32 path is already within the worst-case accounting above.

### 15.4 Equivalence-testing procedures for marginal preservation (pre-registered)

**Principle:** Theorems 2–3 predict *exact* equality. The tests detect implementation errors or violated conditions. Each check is a TOST at α = 0.05 per side, using a **90%** CI that must lie inside the margin.

#### 15.4.1 Noise level (T1)
**Data:** the realised ε̃ for all active frames of the 256 samples of the tested condition. The frame vectors are i.i.d. by construction, so n = Σ L_i, typically ≥ 30,000 per stream [E].

| Check | Statistic | Margin (equivalence region) |
|---|---|---|
| (a) **analytic** (deterministic) | the constructed Σ: diagonal blocks = I; min eigenvalue; closed-form vs numeric log-det | max \|Σ_ss − I\| ≤ 1e-5; λ_min ≥ 1e-3; relative log-det error ≤ 1e-6 |
| (b) per-channel mean | 90% CI of the mean, every channel of each stream | ⊂ [−0.03, 0.03] |
| (c) per-channel variance | 90% CI of the variance ratio (χ²-based) | ⊂ [0.95, 1.05] |
| (d) within-stream correlation | max over channel pairs \|r̂_ij\| | ≤ 0.035 |
| (e) cross-stream covariance vs design | max_ij \|Ĉ_{bs} − K_s\|_ij (BH) or \|Ĉ_{LR} − K_RL\| (LR) | ≤ 0.035 |
| (f) frame independence | per-channel lag-1 autocorrelation | 90% CI ⊂ [−0.03, 0.03] |

**Calibration (pre-run, synthetic only; no model is involved):**
- Simulate 1,000 sets of pure N(0, I) noise of the same size, and apply (b)–(f).
- The family-wise false-failure rate must be < 1%. If not, the margins are widened, but never beyond: mean 0.05, variance [0.90, 1.10], correlation 0.05.
- The final margins are recorded before the real run.
- **Pass = (a) and all of (b)–(f).**

#### 15.4.2 Generated-motion level: T2, the eight-metric generated-motion marginal check

**Scope (rev. 3.1).** T2 is a check of **eight pre-specified summary means** of the generated hand motion. It is **not a test of full distributional equivalence**: it is consistent with Theorem 3 but cannot prove it empirically.

**Unit and estimator:**
- Per sample (clip × noise): a scalar metric; per clip: the mean over its noises.
- **Ratio of means:** R = mean_clips(condition) / mean_clips(A0), with the same clips in both arms.
- **CI:** 90% clip-cluster bootstrap (2,000 resamples of the 32 clips, keeping each clip's samples in both arms).

**Metrics:** for each hand stream (L, R), four scalars (eight tests in total):
- (m1) mean angular speed (activity per frame);
- (m2) articulation (temporal std of joint angle, averaged over joints);
- (m3) jerk;
- (m4) mean joint angle.

The body is excluded because it is sample-wise identical (checked in T0).

**Margin:** **±5%** (a pre-registered convention [U]; not derived from perceptual thresholds).

**Three-way outcome per metric (rev. 3.2):**
- **Pass:** the 90% CI ⊂ [0.95, 1.05].
- **Fail:** the 90% CI lies entirely outside [0.95, 1.05].
- **Straddle:** otherwise.

T2 passes only if all eight metrics pass. **Any fail or straddle ⇒ stop and report**: Theorem 3 predicts exact equality, so even a straddle warrants inspection. The label distinguishes a confirmed deviation (fail) from an unresolved one (straddle).

**Sample-count calibration** (pre-registered, uses A0′):
- Compute the same statistics for A0′ vs A0, which are two independent base draws.
- Let h = the largest 90% CI half-width over the eight metrics.
- Use the smallest n_noise ∈ {8, 16, 32} per clip (32 clips fixed) with **h ≤ 1.5%**.
- This keeps the probability of a false failure under exact equality at ≈ 10⁻⁴ per metric (< 0.1% over eight) [D: if the estimate is ≈ normal with sd ≈ h/1.645, P(fail) ≈ 2Φ(−(5 − h)/(h/1.645))].
- If h > 1.5% even at 32 noises, T2 is reported **calibration-inconclusive** (FM14): neither pass nor fail. The run **continues** (§15.3.1 step 4). Per-stream preservation then rests on Theorem 3, *conditional on its assumptions*, together with the empirical assumption evidence in §15.4.4 (T0, T1, programmatic checks), and is labelled as such.
- Top-ups apply only to A0, A0′ and the two tested conditions (≈ +20–25 min [E], §15.3.1).

**Diagnostic (not gating):** energy distance between standardised per-sample feature vectors, with a within-clip permutation test (1,000 permutations), reported.

**What T2 and its calibration establish, and what remains untested (rev. 3.1):**

| | Statement |
|---|---|
| **(1) Precision: what calibration measures directly** | The 90% CI half-width h of each ratio at the chosen sample count, measured on A0 vs A0′ (equal in distribution by construction). The rule requires h ≤ 1.5%. This is an empirical measurement |
| **(2) False-failure (specificity) under exact equality: derived from (1)** | If the true deviation d = 0, P(not pass) ≈ 2Φ(−(5 − h)/(h/1.645)) ≈ 1.2 × 10⁻⁴ per metric at h = 1.5% (< 0.1% over eight) [D, normal approximation; bootstrap adequacy assumed]. This concerns *not wrongly stopping*, and says nothing about detecting deviations |
| **(3) Error control at the margin: a property of TOST, not of calibration** | If \|d\| = 5% exactly, P(pass) ≤ 5% per metric (TOST size). The procedure therefore wrongly declares equivalence for a deviation at the margin at most 5% of the time per metric [D] |
| **(4) Operating characteristics for deviations of practical size (rev. 3.2)** | At h = 1.5% (normal approximation [D]): **d = 3%:** P(pass) ≈ 0.71; otherwise mostly straddle, so it stops and reports. **d = 5%:** P(pass) ≈ 0.05. **d = 7.5%:** P(pass) ≈ 5 × 10⁻⁶; P(fail) ≈ 0.86; straddle ≈ 0.14. **d = 10%:** P(fail) ≈ 0.9999. "Meaningful" deviations are defined only by the ±5% convention; no perceptually derived threshold exists [U] |
| **What calibration does not establish** | that ±5% is scientifically adequate; that the 32-cluster percentile bootstrap attains its nominal coverage [U]; anything about metrics, moments or conditions outside the eight means and the two tested conditions |
| **T2 pass establishes** | the eight hand-motion **means** (mean angular speed, articulation, jerk and mean joint angle, for each hand) are equivalent to base within ±5%, for the two tested conditions, on 32 dev clips |
| **Untested by T2** | higher moments and tails (e.g. rare large motions); the joint distribution of channels and joints within a stream; per-joint (not averaged) behaviour; temporal structure beyond these summaries; pose-distribution distance (only the non-gating energy distance and, in T6-B, a left-hand Fréchet check); conditions other than the two tested (the other BH/LR conditions are covered only by Theorem 3 plus T0/T1 implementation checks); other clips, test data, and clip lengths not represented among the 32 clips |
| **Logical status** | the exact preservation claim is a **theoretical guarantee conditional on assumptions** (Theorem 3 with F1–F6). T2 is empirical evidence about a *consequence* (eight means), not about the assumptions themselves. Evidence for the assumptions is itemised in §15.4.4 |

#### 15.4.3 T5-A equivalence margin for S₂ (rev. 3.2; target and degenerate case reconciled in rev. 3.3)

**Which target sets the margin (rev. 3.3).**
- The margin uses **t*₂₅₆**, the mean of X^ref over **all dev-256 references**. It is a fixed design constant: no uncertainty is propagated, and T5-A tests μ against 0, not against a target.
- The D-a/D-b target is the different quantity **t*₃₂** (§6.5), estimated on the 32 E2e clips with bootstrap uncertainty.
- t*₂₅₆ is used for the margin because a design constant should come from the largest available reference set and should not move with the evaluation sample.
- (Rev. 3.2 called both "t*_dev"; that ambiguity is removed.)

**Rule (unchanged in its non-degenerate range):**

  δ_S₂ = min(0.05, |t*₂₅₆| / 4)   (log scale)

**Pre-run computation:**
- t*₂₅₆ and its 95% clip-bootstrap CI (2,000 resamples of the 256 clips) are computed from the dev-256 reference poses already in the existing dumps. No generation is involved.
- This happens **before any sample is generated in E2e**, and the results are recorded together with the branch selected below.

**Roles of the t*₂₅₆ estimate and its interval** (rev. 3.3a, wording clarification only):
1. The 95% bootstrap CI of t*₂₅₆ is used **only to determine the R1/R2/R3 branch** (table below). It has no other use.
2. The **point estimate** t*₂₅₆ is treated as a **fixed constant** when calculating the T5-A margin δ_S₂ = min(0.05, max(0.025, |t*₂₅₆|/4)).
3. **No uncertainty from t*₂₅₆ is propagated into the T5-A test.** T5-A tests whether μ = E[log(A_L/A_R)] differs from **zero** (Theorem 4's parity prediction), not whether it differs from t*₂₅₆. t*₂₅₆ enters T5-A only through the pre-fixed margin.

**Degenerate / near-zero case: pre-run branch rule (rev. 3.3).** The branch is chosen from the references only, before any generation. **After any E2e sample exists, neither δ_S₂ nor the branch may change.**

| Branch | Condition on t*₂₅₆ | δ_S₂ | Consequence |
|---|---|---|---|
| **R1** | \|t*₂₅₆\| ≥ 0.20 and 95% CI excludes 0 | 0.05 | normal |
| **R2** | 0.10 ≤ \|t*₂₅₆\| < 0.20 and 95% CI excludes 0 | \|t*₂₅₆\|/4 ∈ [0.025, 0.05) | normal. T5-A is more likely inconclusive; that is declared in advance |
| **R3 degenerate** | \|t*₂₅₆\| < 0.10, **or** its 95% CI includes 0 | **0.025 (fixed floor)** | (a) T5-A still runs: Theorem 4's parity prediction μ = 0 is meaningful regardless of the target, and the floor keeps the test non-vacuous. (b) **P1b is declared target-degenerate at this aggregation:** the SS conditions are removed from the run, D-a to D-c are not evaluated, and I report to you (P1b might need redefinition, e.g. via side calibration or S₄). (c) No other threshold changes |

**Why a floor is needed (a mathematical correction, documented):**
- As δ_S₂ → 0, the TOST pass probability → 0 for any finite sample, so the rev. 3.2 rule could make T5-A unpassable by construction.
- The floor 0.025 equals the R2 value at |t*₂₅₆| = 0.10, so δ_S₂ = min(0.05, max(0.025, |t*₂₅₆|/4)) is continuous across the branches.
- It is fixed **before** any controlled result exists, so it is not a post-hoc widening.

**If t*₂₅₆ cannot be computed** (e.g. a data error), E2e stops before generation.

#### 15.4.4 Theoretical guarantees vs empirical evidence that their assumptions hold (rev. 3.3)

**The guarantee (theory):** under F1–F6 and ε-independent controller parameters, every per-stream noise and generated-motion law equals the base exactly (Theorems 2–3, [D]). This holds *if* the assumptions hold; it is not itself an empirical finding.

**Evidence that the assumptions hold in our implementation:**

| Assumption | Content | Evidence type | How it is checked in E2e | Status if the check is absent or inconclusive |
|---|---|---|---|---|
| F1 | GF sampler deterministic given the noise; empty keyframe mask | code reading [C] + empirical | T0 (b): harness = upstream on identical noise | remains [C] only |
| F2 | one hand network, identical (c, L) inputs for both sides | code reading [C] + programmatic | assertion that L/R share text, length and mask tensors (no generation cost) | [C] |
| F3 | base noise i.i.d. N(0, 1), including padded frames | code reading [C] + empirical | T1 on the *realised* noise (moments, correlations, lag-1) | T1 fail ⇒ stop |
| F4 | no batch coupling (g_L independent of ε_R) | code reading only [C] | **not empirically tested in E2e** (it would need extra paired runs outside the proposed scope) | stays a code-reading assumption, stated as such |
| F5 | eval() mode | programmatic | assertion that `model.training == False` for every call; logged | — |
| F6 | same numerical implementation for base and controlled | empirical + programmatic | T0 (a)–(c); recorded dtype, device and TF32/cuDNN flags compared between arms | T0 fail ⇒ stop |
| Parameters ε-independent | controller parameters built from (c, L) only | by construction + programmatic | E2e uses fixed constants (U, V, κ, σ); assertion that no parameter tensor depends on ε⁰ | — |
| Padded frames untouched | ε̃ = ε⁰ for τ > L | programmatic | exact-equality assertion on padded frames | — |
| PD and diagonal identity | Σ ≻ 0, diagonal blocks = I | numerical | T1 (a) analytic checks | T1 fail ⇒ stop |

**Empirical evidence about consequences (not assumptions):** T2 (eight means) and T5-A (Theorem 4 parity).

**How the E2e report states marginal preservation:**

| Outcome | Wording |
|---|---|
| All assumption checks pass **and** T2 passes | "exact by Theorem 3; assumptions checked as listed (F4 by code reading only); the eight-metric consequence was confirmed within ±5%" |
| Assumption checks pass, T2 calibration-inconclusive | "exact by Theorem 3 *conditional on* its assumptions, checked as listed (F4 by code reading only); the empirical consequence check was inconclusive" |
| Any assumption check fails, or T2 fails or straddles | no preservation claim; stop |

**Justification:**

| # | Reason |
|---|---|
| 1 | **Below the smallest movement treated as meaningful.** D-a requires \|δ\| ≥ 0.10; δ_S₂ ≤ 0.05 is half of that. A condition that passes T5-A cannot also be counted as a D-a movement, so the two criteria cannot both claim the same data |
| 2 | **Comparable to the T2 margin.** δ = 0.05 corresponds to a geometric ratio within [0.951, 1.051], i.e. ±5%, the same convention as the T2 and S₁ margins |
| 3 | **Small relative to the reference gap.** The \|t*₂₅₆\|/4 term keeps the margin at most a quarter of the distance between parity and the reference in R1/R2. In R3 the reference is near parity, so the floor applies and P1b is handled as degenerate rather than letting the margin vanish |
| 4 | **The values are conventions, not empirically derived [U].** They are fixed before the run and are not tuned afterwards |

**Precision dependency [U]:**
- Whether a 90% CI can fit inside ±δ_S₂ at 32 clips × 8 noises depends on the unknown between-clip spread of X̄_j.
- **Pre-specified handling:** if A0's own 90% CI half-width for μ exceeds 0.8·δ_S₂, then T5-A for the BH/LR conditions at 8 noises is expected to be inconclusive.
  - It is reported as such (not a pass).
  - The two strongest-coupling conditions use the noise count n* fixed by the T2 calibration (§15.3.1, step 3).
  - **No margin is widened after seeing any generated data.** A0's half-width only predicts inconclusiveness; it never changes δ_S₂.

### 15.5 E0 scope (independent track)

| Step | Who | Scope |
|---|---|---|
| E0.1 | **You** | register at smpl-x.is.tue.mpg.de; download SMPL-X v1.1 NPZ (personal licence) |
| E0.2 | You | place it at `models/smplx/smplx/`; it never leaves this machine; licence note recorded (not the model) |
| E0.3 | Me | new `.venv-render` (existing environments untouched); pinned `smplx`, `trimesh`, renderer; lock file |
| E0.4 | Me | FK sanity on 5 dev GT clips (bone lengths, wrist attachment, left-hand flip, NaNs) |
| E0.5 | Me | Windows rendering feasibility; 3 dev clips × {reference, KF2P, GF} for **your review only**; a Blender install would need a separate approval |
| E0.6 | Me | joint-space metrics on existing dev dumps (released-checkpoint, not paper reproduction) |
| Stop | — | report; E1 stays deferred |
| Excluded | — | test-set renders; participants; FLAME downloads. **MANO is not required** (Stage 2 D12) |

---

## 16. Assumptions, constraints and safeguards
- **A1:** reference length is an oracle in all GF work (disclosed).
- **A2:** the face is excluded from P1.
- **A3:** the targets come from pseudo-GT How2Sign references, which include extraction errors (D4):
  - coordination 0.47 / 0.32;
  - the dominance log-ratio t* (train); for E2e, t*₃₂ (target) and t*₂₅₆ (margin constant);
  - side calibration.
  - The value 0.76 is the dev-256 mean of per-clip ratios (S₃), used only as a descriptive reference.
- **A4:** SMPL-X neutral renders; the face basis differs from the authors' SMPLFX.
- **Safeguards (unchanged):**
  - no test-set experiments;
  - no checkpoint modifications;
  - no training or fine-tuning;
  - no architecture changes;
  - no participant recruitment;
  - no author contact;
  - no GPU rental;
  - no Stage 5 work.
  - All E2 steps are inference or noise-gradient only on dev clips, each separately approved.

## 17. Decision log

| # | Decision | Status |
|---|---|---|
| D4.1 | P1 = P1a coordination + P1b dominance as **separate objectives**; perceptual-motion claim scope | **Supported by you in principle; pending approval** |
| D4.2 | Reference rewards rejected in GF (collapse) | Proposed |
| D4.3 | BT excluded as a reward | Proposed (consistent with your instruction) |
| D4.4 | M-C = conditional-Gaussian noise controller, horizon-1 bandit, frozen generators | **Supported by you; pending approval** |
| D4.5 | M-D = ORW-CFM-W2 comparator (capabilities per §5.5) | **Supported by you as comparator** |
| D4.5b | M-D′ side-specific hand copies | Deferred (needs your decision) |
| D4.6 | Exact-KL Gaussian family as default; residual controller only as a non-default alternative, **never adopted automatically** | Proposed (rev. 3) |
| D4.6b | K_train = 10, full backprop with checkpointing; the one-step shortcut is invalid | Proposed |
| D4.6c | Components M-C/κ (P1a) and M-C/σ (P1b) trained and reported separately; combined only afterwards | Proposed |
| D4.6d | Unrolled sampler; **one numerical implementation for all arms**; T0 equivalence | Proposed (corrected precision rule) |
| D4.6e | The paired base term is a CRN monitoring/evaluation estimator only; not in the gradient; not a REINFORCE baseline | Proposed (correction) |
| D4.6f | M-C/σ is scale-only by default; the mean shift is deferred | Proposed |
| D4.7 | Rewards: target-matching, separate components, dual-ascent constraints, left-hand protection | Proposed |
| D4.8 | Evaluator path: E0 → (your review) → E1 Phase 1 → simulation-sized confirmatory study; learned evaluator deferred | E0: you indicated willingness; E1: deferred |
| D4.8b | Human constructs: claims on (A) only, with separate coordination / handedness / left-hand items | Proposed |
| D4.8c | Confirmatory sample size only from the §7.1.4 simulation | Proposed |
| D4.9 | Comparators N1, N3′, N4, N5, N9 required; N6 for M-D; N7 exploratory | Proposed |
| D4.10 | Face excluded from P1 | Proposed |
| D4.11 | SLERP deferred | **Approved** |
| D4.12 | GF-T2P primary | **Approved** |
| D4.13 | No architecture implementation; N7 exploratory only | **Approved (scope)** |
| D4.14 | E2 order E2d → E2e → E2a → E2b → E2c; stop after each | Proposed (your order) |
| D4.15 | Equivalence procedures and pass/fail rules in §15.3–15.4 pre-registered. T2 = **eight-metric generated-motion marginal check** (not full distributional equivalence) | Proposed (rev. 3.1 wording) |
| D4.16 (rev. 3.1) | Theorem 4 stated per statistic with assumptions T4-a to T4-d. Mean-type S₁–S₃ fixed under equal hand marginals; S₄ not determined; T5-A gates only on S₁/S₂; r_dom target = reference mean log-ratio t* | Proposed |
| D4.17 (rev. 3.1) | Dominance reported at four separate levels D-a (movement), D-b (proximity), D-c (genuine, no left-hand degradation), D-d (perceptual, human only); E2e reaches at most D-c | Proposed |
| D4.18 (rev. 3.1) | Semantic wording: only "no regression detected on the specified secondary checks"; no semantic-preservation or translation-quality claim | Proposed |
| D4.19 (rev. 3.1; counts revised in 3.2) | E2e runtime accounting incl. explicit T0 executions, 1.5 h cap and pre-registered run order (§15.3.1) | Proposed |
| D4.20 (rev. 3.2; amended 3.3) | T5-A as a TOST for S₂ with δ_S₂ = min(0.05, max(0.025, \|t*₂₅₆\|/4)); t*₂₅₆ computed from existing dev-256 references before any generation; pre-run branches R1/R2/R3; three-way outcome; S₃ descriptive only | Proposed |
| D4.23 (rev. 3.3) | Two targets: t*₃₂ (D-a/D-b, estimated, bootstrap-propagated) vs t*₂₅₆ (margin constant, fixed). D-a "direction not assessable" if the CI of t*₃₂ − m_A0 includes 0. Over-shoot flag made direction-general | Proposed (corrections documented) |
| D4.24 (rev. 3.3) | Run order: step 0 (references only) → T0 → A0/A0′ → calibration loop fixing n* → gate conditions at n* → the rest. T2 calibration-inconclusive continues with theory-conditional wording; fail/straddle stops. Assumption-evidence table (§15.4.4) | Proposed |
| D4.21 (rev. 3.2) | D-c renamed and strengthened (requires D-a + D-b + no over-shoot + left-hand criteria); D-b tested on the gap ratio; exact aggregation and bootstrap procedure | Proposed |
| D4.22 (rev. 3.2) | All reward components labelled "measurable statistic, not perceptually validated" until §6.4 passes | Proposed |

## 18. Remaining uncertainties

**Unresolved assumptions and conventions (rev. 3.2).** These are named rather than silently chosen. All are fixed before any run and not tuned afterwards.

| # | Assumption / convention | Where | Status |
|---|---|---|---|
| U-A1 | T4-e (S₃ finite) | App. G.6.1 | not guaranteed; S₃ descriptive only |
| U-A2 | T2 margin ±5%; S₁ margin [0.95, 1.05] | §15.4 | convention, not perceptually derived |
| U-A3 | δ_S₂ rule min(0.05, max(0.025, \|t*₂₅₆\|/4)); R3 threshold \|t*₂₅₆\| < 0.10 or CI ∋ 0 | §15.4.3 | conventions with stated rationale; the floor is a documented correction (rev. 3.3) |
| U-A4 | D-a minimum movement 0.10; D-b 50% gap reduction; assessability g_A0 ≥ 0.10; over-shoot 0.10 | §6.5 | conventions |
| U-A5 | Left-hand thresholds: floor log 0.8 (lower bound log 0.75), jerk +10%, extreme frames +2 points, coordination −0.03, Fréchet q₉₅ | §6.5, §15.3 | conventions |
| U-A6 | Adequacy of the 32-cluster percentile bootstrap | §6.5, §15.4 | assumed; possibly slightly anti-conservative |
| U-A7 | Throughput rates and the unmeasured compute items in §15.3.1 | §15.3.1 | estimates [E] |
| U-A8 | Precision sufficient for T5-A at 8 noises | §15.4.3 | unknown; "inconclusive" handling pre-specified |
| U-A9 | t*₂₅₆, t*₃₂ and t* (train) values | §6.5, §15.4.3 | not yet computed. t*₂₅₆ and t*₃₂ come from existing dev references within E2e (step 0 and the bootstrap). t* (train) needs a separate approved analysis step |
| U-A10 (rev. 3.3) | F4 (no batch coupling) | §15.4.4 | code-reading evidence only; not tested empirically in E2e |

| # | Uncertainty | Type | Resolved by |
|---|---|---|---|
| Q1 | Does frame-local linear coupling transmit to output timing (body–hand; L–R)? | experimental | E2e T3/T4 |
| Q2 | Can a learned or optimised U, V find transmitting directions that random ones miss? | experimental | E2c (ii); Stage 5 |
| Q3 | Does side scaling reach D-a to D-c rather than suppression? | experimental | E2e T5-B/T6-B |
| Q3b (rev. 3.1) | Value of t* (train reference mean log-ratio); is S₄ movable alone under equal marginals? | factual / mathematical | t*: computable from train references (needs approval as an analysis step); S₄ alone: [U], not a goal |
| Q3c (rev. 3.1) | Perceptual dominance (D-d) | experimental (human) | E1 / confirmatory study only |
| Q4 | Size of the reverse-KL family gap to q* | mathematical/empirical | E2c reference only |
| Q5 | Is P(A_R > A_L) movable under equal marginals, and would that be desirable? | mathematical | not a goal |
| Q6 | Input-gradient activation memory; body U-Net memory | experimental | E2d |
| Q7 | Ten-step Jacobian-product health | experimental | E2a |
| Q8 | Condition-number bound for the three-block Σ | mathematical | numerical logging |
| Q9 | Rank, σ bounds, frame-varying parameters; whether to test μ | design | after E2e; μ needs approval |
| Q10 | Are the equivalence tests adequately powered at ≤ 32 noises per clip? | experimental | §15.4.2 calibration |
| Q11 | Are the three checkpoints' M-CLIP weights identical (one cached embedding)? | factual | E2d (hashing, read-only) |
| Q12 | Is the coordination statistic perceptually meaningful? Is D-c dominance perceived (D-d)? | experimental (human) | E1 |
| Q13 | Checkpoint provenance / contamination (D10) | factual | unresolved; no author contact without permission |
| Q14 | Software for the GLMM simulation | practical | your decision later |

## 19. Approval checklist

Each item is independent. Approving an experiment approves only that step. Each later step needs its own go-ahead after my report.

| # | Decision | Recommendation |
|---|---|---|
| 1 | Stage 4 **revision 3.3** as the design: P1a/P1b separated; M-C Gaussian default with M-C/κ and M-C/σ components; K = 10; the same-implementation rule; M-D comparator; rewards (as measurable statistics, not yet perceptually validated) and constraints; two-phase validity; evaluation constructs; dominance levels D-a to D-d (D-c as redefined); secondary checks worded as "no regression detected" | Approve |
| 2 | Appendix G (revision 3.3, including Theorem 4 with T4-a to T4-e) as the mathematical basis, with the open items and conventions in §18 | Approve after review |
| 3 | E0 as scoped in §15.5 (you register first) | Approve |
| 4 | E2d (§15.2) | Approve; run on your go-ahead |
| 5 | E2e (§15.3–15.4, pre-registered; T2 = eight-metric marginal check with pass / fail / straddle; T5-A = TOST with δ_S₂ rule; T5-B at D-a to D-c only; runtime, T0 counts and run order with stop rules §15.3.1; cap 1.5 h). Includes step 0: computing t*₂₅₆ (and the R1/R2/R3 branch) from existing dev-256 references before any generation | Approve in principle; go-ahead after the E2d report |
| 6 | E2a | Approve in principle; go-ahead after the E2e report |
| 7 | E2b | Approve in principle; go-ahead after the E2a report |
| 8 | E2c, including (ii) the family-capacity test | Approve in principle; go-ahead after the E2b report |
| 9 | M-D′; the mean-shift variant of M-C/σ | Defer |
| 10 | E1 human pilot | Remains deferred until you review the E0 renders and §7.1 |
| 11 | Confirmatory sample size | From the §7.1.4 simulation after the pilot; no decision now |

**Not requested:** Stage 5, training, fine-tuning, architecture changes, GPU rental, recruitment, author contact.
