# Stage 4 Report: research problem, MDP design and validation

**Revision 4.0** (human verification removed from scope; automated measurable-motion-quality scope) · 2026-11-03 · Scope: ASL / How2Sign / released SignSparK checkpoints · Status: **for your approval**. E0 is complete. No E2 step is authorised. Stage 5 has not started.

**Previous revision:** preserved unchanged at [archive/STAGE4_REPORT_rev3.3a.md](archive/STAGE4_REPORT_rev3.3a.md).

**This revision is documentation only.** No experiment, sampling or training took place while writing it. It uses the E0 results (run 2026-11-03 under your E0 authorisation; [E0 report](stage4/E0_REPORT.md)). The derivations are in [Appendix G](stage4/appendix_gaussian_controller.md) (rev. 4.0). The executable E2 plan is in [E2_EXECUTION_CHECKLIST.md](stage4/E2_EXECUTION_CHECKLIST.md).

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

**Claim-type labels (rev. 4.0).** Every claim in §0.1, §6 and §15 is one of three types:

| Type | Meaning | Example |
|---|---|---|
| **G** theoretical guarantee | a [D] result, true *conditional on* stated assumptions | Theorem 3 marginal preservation under F1–F6 |
| **M** automated measurement | a statistic computed by code, with a CI, on named clips, in a named **measurement space** (rotation or SMPL-X joint) | rotation-space coordination Δ = 0.06 [0.02, 0.10] on 32 dev clips |
| **PH** unvalidated perceptual hypothesis | a statement about how motion would look to people. **Not tested in this project; never asserted as a result** | "higher coordination looks more natural" |

---

## Change log

### Revision 4.0 (scope change: human verification removed; your instruction 2026-11-03)

**Why:** you removed human verification from the current scope because of time constraints. The project now claims only measurable motion quality.

| # | Your point | Change | Where |
|---|---|---|---|
| 4.0-1 | E1 removed as a dependency | E1 is **deferred indefinitely**: no recruitment, rater contact, pilot or participant-facing material. It is removed as a prerequisite for E2 and for any later automated validation. The human-evaluation design (old §7.1.1–7.1.4) is **not** carried forward; it survives only in the archived rev. 3.3a | §0, §2, §6.4, §7.1, §13–15, §17, §19 |
| 4.0-2 | D-d removed | Perceptual dominance (D-d) is removed from the objectives, the success criteria and the dominance levels. Three levels remain: D-a, D-b, D-c, all automated | §6.5, §15.3, App. G.6.3 |
| 4.0-3 | No perceptual, preference, semantic or intelligibility claims | §0.1 is rewritten around **measurable motion quality**: P1a, P1b, per-stream preservation, and secondary regression checks. New claim-type labels G / M / PH. The previously licensed claim ("rated by fluent signers as more natural") is withdrawn | §0.1, labels above |
| 4.0-4 | Two measurement spaces | Rotation space (R) and SMPL-X joint space (J) are defined as **distinct measurement spaces**, each with its own statistics and targets. The rotation-space coordination value 0.47 is **never** used as a joint-space target. All targets are re-specified as **train-reference** values per space (not yet computed). 0.47 / 0.32 are retained only as historical descriptive values | new §6.0; §6.1; §6.5 |
| 4.0-5 | E0 findings retained and used | E0.4–E0.6 results are summarised and drive the target revision. The cross-space agreement for dominance is high (ρ ≈ 0.96, so joint space adds little *independent* evidence for P1b). For coordination it is moderate (ρ ≈ 0.5), and the reference level differs (0.44 vs 0.23) | new §1.4; §6.0 |
| 4.0-6 | Reward validity without humans | The two-phase perceptual validity criteria (old §6.4) are replaced by **automated validity criteria** V-R1 to V-R4. These state what each statistic is valid *as* (a measurable property of the motion), not as perceived quality | §6.4 |
| 4.0-7 | Evaluation framework | Primary evaluation is now automated only. The joint-space statistics are evaluation-only (never in the reward), which keeps reward and evaluation independent in measurement space. New **non-gating E2e-J** post-hoc analysis computes T3/T4/T5-B in joint space from the E2e dumps (CPU, `.venv-render`, separate cap) | §6.3, §15.3, §15.3.2 |
| 4.0-8 | Strongest automated claims; limitations | New §0.2 (strongest claims automated evaluation alone can support) and §16.1 (remaining limitations and risks) | §0.2, §16.1 |
| 4.0-9 | E2 order and gates kept | E2d → E2e → E2a → E2b → E2c is unchanged, each a separate technical feasibility experiment with its own approval. All E2e thresholds, margins, branches and the run order are **unchanged**. The only E2e additions are the joint-space secondary outputs (non-gating) and saving the dumps they need | §15.2–15.4; checklist |
| 4.0-10 | Secondary checks | The comprehension 4AFC is removed. DTW-JPE "if SMPL-X becomes available" is replaced by our frame-aligned SMPL-X MPJPE / PA-MPJPE (E0.6 definitions; not the paper's DTW-JPE). Secondary checks still support only "no regression detected" | §0.1 |
| 4.0-11 | Logs | Decision log D4.25–D4.31; D4.8, D4.8b, D4.8c, D4.17 and D4.22 amended or withdrawn; §18 updated (Q3c, Q12, Q14 closed as out of scope; U-A11 to U-A14 added); approval checklist rewritten; research log updated | §17–19; `RESEARCH_LOG.md` |

**Rev. 4.0 wording-consistency fix (2026-11-03, E2e preflight P-9, on your instruction):**
- The §15.3.1 run-order table now shows "T5-A fail ⇒ stop" for steps 5–6.
- This restates the already-registered T5-A rule ("Stop on any fail", all BH and LR conditions) and the §15.2 stop gate.
- No criterion, threshold or decision changed. The revision number stays 4.0.

**Unchanged in rev. 4.0:**
- the M-C design and Appendix G derivations (only wording in G.6.3 and a T4-b note for joint space);
- K = 10; the same-implementation rule;
- every numeric threshold, margin and branch in §6.5 (D-a to D-c) and §15.3–15.4;
- the E2e run order;
- M-D as comparator;
- the safeguards.

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
3. **Research problem (P1)** [Pr]: measurable cross-articulator structure in GF-T2P motion (rev. 4.0), as **two separate objectives**:
   - **(P1a) coordination**: arm–hand and left–right temporal coupling, measured in rotation space and, separately, in SMPL-X joint space;
   - **(P1b) dominance**: a dominant right hand without detected left-hand degradation.
   - Per-stream motion quality must be preserved.
   - The claim scope is measurable motion statistics only; no perceptual claim (§0.1).
4. **Primary method (M-C)** [Pr]: a KL-regularised conditional-Gaussian noise controller over the **frozen** samplers, a contextual bandit optimised by pathwise gradients through the full 10-step sampler.
   - **M-C/κ** (marginal-preserving coupling) targets P1a. It keeps every stream's output distribution exactly as the base [D].
   - **M-C/σ** (side-dependent noise scale) targets P1b.
     - Coupling alone keeps equal hand marginals. Theorem 4 then fixes the mean-type dominance statistics at parity: ratio of means = 1, geometric ratio = 1, mean of per-sample ratios ≥ 1. So **no mean-type dominance target below 1 (e.g. the reference 0.76) is attainable by coupling** [D].
     - The probability statistic P(A_R > A_L) is not determined by the marginals.
     - Whether scaling achieves dominance without left-hand degradation is [H]; the evaluation levels are in §6.5.
   - The KL is exact and closed form [D]. The optimum is the reverse-KL projection of the reward-tilted distribution onto the family [D].
5. **Direct fine-tuning comparator (M-D)** [Pr]: per-stream ORW-CFM-W2. It cannot learn dominance, and can couple streams only through text-locked timing (§5.5).
6. **Gates before any training (rev. 4.0):**
   - E0 (done: FK validated; cross-space agreement measured);
   - the bounded feasibility experiments E2d → E2e → E2a → E2b → E2c, each separately approved (§15);
   - the train-reference targets per measurement space (an approved, reference-only analysis step, §6.0);
   - **no human gate:** E1 is deferred indefinitely.
7. **H0** (RL adds nothing beyond selection, side assignment and the N5 cascade) remains an acceptable outcome.

## 0.1 Research objective and claim scope

**Objective (rev. 4.0):** determine whether a KL-regularised RL controller over the frozen, released SignSparK samplers can change GF-T2P motion in four respects:
- **(P1a) cross-articulator coordination:** arm–hand and left–right temporal coupling, toward the train-reference level, in each measurement space;
- **(P1b) right-hand dominance without left-hand degradation:** the left/right activity log-ratio toward the train-reference value, with the left-hand checks passing;
- **per-stream motion quality preserved:** per-stream marginal statistics equivalent to base or non-inferior (articulation, jerk, extreme frames, pose-distribution distance);
- all of this compared with non-RL alternatives at matched cost.

All four are **automated measurements (type M)** with stated measurement spaces. Nothing in the objective is perceptual.

**What a positive result would license (type M, plus type G where stated):**
- "On held-out How2Sign clips, with the released checkpoints and the oracle length, the controller moved the **rotation-space** coordination (and/or dominance) statistic toward its train-reference target by Δ [CI], at measured KL cost."
- "The independent **joint-space** statistic moved in the same direction by Δ_J [CI]" (or did not, reported either way).
- "Per-stream marginal statistics were preserved": exact by Theorem 3 for M-C/κ (type G, conditional on F1–F6), and empirically within the pre-registered margins (type M).
- "**No regression detected** on the secondary checks."

**What it would NOT license:**
- **Perceptual naturalness, human preference, or "looks better / more natural / more coordinated" (type PH; untested).**
- **Semantic correctness, semantic preservation, ASL intelligibility or better translation.** The A3 different-sentence null shows coordination statistics are reachable with hands from another sentence [V], so a coordination gain does not mean the coupling is content-appropriate.
- Real-world ASL production quality.
- Any comparison with the SignSparK paper's results (R10).
- Signer-independent or out-of-How2Sign generalisation.
- **A dominance claim based only on a ratio change:** a ratio change alone may reflect left-hand suppression (§6.1, App. G.6.3). The dominance claim is D-c at most.
- A claim in one measurement space presented as holding in the other.

**Secondary checks (rev. 4.0)** [Pr]:
- corpus-level BT (never alone);
- SMPL-X frame-aligned MPJPE / PA-MPJPE (E0.6 definitions; not the paper's DTW-JPE), with the collapse caveat.

The only claim these support is: **"no regression was detected on the specified secondary checks"** (each pre-registered margin, reported with CIs). A detected regression beyond its margin invalidates the method.

**These checks do not establish semantic preservation, semantic correctness, intelligibility or translation quality:**
- BT does not track pose quality within a sentence (R6) and has a GT ceiling of BLEU-4 3.5;
- reference-based joint error is confounded by one-to-many generation and favours mean poses (V1–V3).

Absence of a detected regression is not evidence of no regression.

## 0.2 Strongest claims automated evaluation alone can support (rev. 4.0)

These are the ceilings. Any actual claim is weaker if its evidence is weaker.

| # | Claim (ceiling) | Type | Required evidence | Why it cannot go further |
|---|---|---|---|---|
| S1 | M-C/κ leaves every per-stream output distribution exactly unchanged | G (conditional on F1–F6) + M (T0/T1/T2 consistent) | §15.4.4 assumption table; T2 pass | F4 is supported by code reading only; T2 tests eight means, not full distributions |
| S2 | The controller raises temporal arm–hand / L–R coupling **as measured by the rotation-space statistic**, toward its train-reference target, on held-out clips, at a stated KL | M | Stage 6 paired evaluation, CIs, ≥ 3 seeds | the statistic is chance-satisfiable (A3 null); perceptual relevance untested (PH) |
| S3 | The same change is visible in an independently computed joint-space statistic | M | E2e-J / Stage 6 joint-space evaluation | the spaces agree only moderately for coordination (ρ ≈ 0.5, E0); a joint-space target is not yet computed |
| S4 | Side scaling moves the activity log-ratio toward and substantially closer to the reference, without detected left-hand degradation (D-c) | M | §6.5 D-a + D-b + left-hand checks | the left-hand checks are a finite list of statistics; "no degradation detected" ≠ "the left hand is natural" (PH) |
| S5 | The controller beats or matches non-RL comparators on these statistics at matched cost | M | §9 comparators under CRN | comparators are evaluated on the same statistics only |
| S6 | No regression detected on BT and SMPL-X joint error | M | secondary checks | absence of detection ≠ absence of regression; neither is semantic |

**Not supportable by any automated evidence in this project:** perceptual naturalness, preference, perceived dominance, semantic correctness or preservation, intelligibility, ASL quality.

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
  - coordination 0.026 (reference 0.47), rotation space, test set: a descriptive value, not a target (rev. 4.0);
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
- [V] Coordination statistics are satisfiable by chance alignment (A3 null), so they are **measurable-motion targets only**, not evidence of content-appropriate coupling (rev. 4.0 wording; previously "perceptual-motion targets only").
- [I] Handedness statistics are restored by a trivial rule.

### 1.3 Two structural results
- **Prop 1** [D]: in GF, (x_L, x_R) is exchangeable for **any** hand-network weights. So P[R more active] = ½ and E[A_L] = E[A_R]. Measured 48.9% [V].
- **Prop 2** [I]: with independent streams, E[corr(s_b, s_h)] ≈ corr(m_b, m_h)·√(ρ_bρ_h) ≤ √(ρ_bρ_h), where ρ is the text-locked share of timing variance (≈ the same-text agreement).
  - GF prediction 0.023 vs observed 0.025 [V].
  - KF2P consistent: the implied corr(m_b, m_h) = 0.47 ≈ reference 0.474.
  - Raising coordination with independent streams needs ρ_bρ_h ≳ 0.22, i.e. text-locked or collapsed timing.

### 1.4 E0 findings carried forward (rev. 4.0; [V], [E0 report](stage4/E0_REPORT.md))

All of these are released-checkpoint results on dev and are not paper reproductions.

| Finding | Value | Consequence for the design |
|---|---|---|
| FK pipeline (5 dev GT clips) | C0–C4 pass. `flip_left_hand=True` is required: unflipped left fingers bend backwards in 100% of frames | the joint space is usable; the left-hand convention is fixed |
| Rendering on Windows | pyrender/WGL works; no Blender | renders are available for **researcher inspection only** (not evidence; §7.1) |
| GF joint error, body / hands (1,650 dev clips) | MPJPE 67.8 / ≈ 20.8 mm; KF2P 10.1 / 3.5–4.6 mm | secondary-check baselines (frame-aligned; not DTW-JPE) |
| V1: rotation error vs joint error, per clip | Spearman: hands 0.90–0.97; GF body **0.66** | body-level error claims use joint space |
| **V3: dominance** log(A_L/A_R), rotation vs joint | per-clip ρ ≈ 0.96–0.97; reference mean −0.400 (R) vs −0.423 (J); GF ≈ 0 in both | P1b is robust to the choice of space. **But joint space is then nearly a re-measurement of the reward, not independent evidence** |
| **V2: coordination**, rotation vs joint | per-clip ρ ≈ 0.47–0.55. Reference mean **0.439 (R) vs 0.232 (J)**. GF 0.022 vs 0.025. KF2P 0.357 vs 0.200 | the GF deficit is present in both spaces. But the two statistics measure different constructs (angular arm speed vs linear wrist speed; finger angular vs wrist-local finger linear speed), so **targets are space-specific** and 0.47 is not a joint-space target (§6.0) |
| Reference coordination depends on the clip set | rotation space: 0.474 (dev-256, §1.2), 0.439 (full dev, E0), 0.47 (Stage 3 test) | target values must come from **train** references, with the set named (§6.0) |

---

## 2. The research problem

### 2.1 Candidate problems

| Problem | Evidence | Can RL change it? | Valid reward today? | Verdict |
|---|---|---|---|---|
| **P1a coordination** | A1–A3, Prop 2 | joint noise controller: in principle (noise-level coupling exact; output transmission [H]); per-stream fine-tuning only via text-locked timing | statistics valid on real data, **chance-satisfiable**; space-specific (E0 V2); perceptual validity out of scope | **Primary**, gated on E2e (rev. 4.0; was E1) |
| **P1b dominance** | A4, Prop 1, Thm 4 | coupling: **no** [D]; side-dependent marginal: [H]; shared-weight fine-tuning: **no** [D] | statistic valid on real data, robust across spaces (E0 V3); risk of suppression hacking | **Primary, separate objective**, gated on E2e (rev. 4.0; was E1) |
| P2 face under-articulation (0.65) | Stage 3 | yes, within one stream | gameable; rendering basis caveat | secondary, later |
| P3 semantic content | BT −78%; V1 ≈ chance | little to elicit; pooled text | none | not now |
| P4 reference fidelity in GF | 23° errors | yes | **invalid** (collapse) | evaluation only, with caveat |
| P5 KF2P | small headroom | yes | yes | deprioritised (your decision) |
| P6 length (oracle) | all GF | controller variable | none | deferred, disclosed |

### 2.2 Decision

| Item | Explanation |
|---|---|
| Problem | GF-T2P produces independent, noise-timed streams and exchangeable hands. Reference signing has coupled articulators (rotation-space 0.44–0.47 depending on the clip set; joint-space 0.23, full dev) and a dominant hand (94%) |
| Decision | P1 = **P1a and P1b as separate objectives**, each with its own controller component, reward, constraints and automated metrics in two measurement spaces (rev. 4.0: human items removed) |
| Reason | the largest verified deficits, mechanistically explained, measurable without a reference; the theory determines which formulation can work |
| Alternatives | P2–P6 |
| Evidence | §1.2–1.3, Thm 4 |
| Risks | perceptual irrelevance (untestable in this scope, PH); Goodhart effects on the statistics; H0; no semantic gain; dominance hacked by suppression |
| Validation | automated validity V-R1 to V-R4 (§6.4); E2e feasibility; joint-space cross-check (rev. 4.0; E1 removed) |
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
| Dominance | κ: not for mean-type statistics S₁–S₃ (Thm 4); σ: [H], evaluated at D-a to D-c (rev. 4.0) | **no, for any weights** (Prop 1) | [D] |
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

### 6.0 Measurement spaces and target specification (new in rev. 4.0)

**Two distinct measurement spaces.** They measure related but different constructs. A statistic, its target and any claim about it always name their space.

| | **R: rotation space** | **J: SMPL-X joint space** |
|---|---|---|
| Input | the 6D joint-local rotations as generated | positions from SMPL-X FK: neutral, betas 0, `flat_hand_mean`, no PCA, `flip_left_hand=True`, root fixed (E0.4 setup) |
| Arm signal s_arm | mean angular speed of elbow + wrist (body stream) | linear speed of the wrist joint (world frame) |
| Hand signal s_hand | mean finger-joint angular speed (hand stream) | mean linear speed of 15 hand joints + 5 fingertips **in the wrist's local frame** (forearm and wrist rotation removed; E0.6 amendment) |
| Arm–hand coordination | coord_ah^R(s) = corr_τ(s_arm, s_hand), s ∈ {L, R} | coord_ah^J(s), same form |
| Left–right coordination | coord_lr^R = corr_τ(s_hand,L, s_hand,R) | coord_lr^J, same form |
| Activity, dominance | A_s^R = Σ_τ s_hand,s(τ); dom^R = log(A_L^R / A_R^R) | A_s^J, dom^J, same form |
| Role | **reward and constraint statistics** (M-C training; E2e gating tests) | **evaluation only**: never in a reward, constraint or gating test. This keeps reward and evaluation separate in measurement space |
| E0 status | coord_ah (right), dom: computed on dev (E0.6) | coord_ah (right) and dom computed on dev (E0.6). **coord_ah (left) and coord_lr in J are defined here but not yet computed** [U] |

**Why the reward stays in R:**
- it is the space of the generator's output, with no licensed model in the training loop;
- it is cheap and directly differentiable;
- E2e/E2a are specified in it.

Moving the reward to J would need differentiable SMPL-X FK inside the 10-step backprop. That is not proposed.

**Agreement between the spaces (E0, §1.4):**
- **Dominance:** per-clip ρ ≈ 0.96. J is a robustness check for P1b, but provides little *independent* evidence (§16.1).
- **Coordination:** ρ ≈ 0.5, and the reference levels differ (0.44 vs 0.23). J is a partly independent check for P1a, and **no target transfers between spaces**.

**Target specification (replaces the fixed values 0.47 / 0.32 and the single t*):**

| Target | Space | Definition | Source set | Status |
|---|---|---|---|---|
| τ*_ah^R(s), s ∈ {L, R} | R | mean over clips of the per-clip reference coord_ah^R(s) | How2Sign **train** references | not computed [U] |
| τ*_lr^R | R | mean of the per-clip reference coord_lr^R | train | not computed |
| t*^R (= t* in Appendix G) | R | mean of the per-clip reference dom^R | train | not computed |
| τ*_ah^J(s), τ*_lr^J, t*^J | J | the same, in J | train | not computed |
| t*₃₂, t*₂₅₆ | R | §6.5 / §15.4.3 (unchanged) | dev E2e clips / dev-256 | computed at E2e step 0 / bootstrap |
| t*₃₂^J | J | the J analogue of t*₃₂ | dev E2e clips | computed in E2e-J (non-gating) |

**Rules:**
- (i) A target is compared only with a statistic of the **same space and definition**.
- (ii) Training targets come only from **train** references, never dev or test. The previous 0.47 was a test-set and dev-256 figure and is retired as a target.
- (iii) Each train target is reported with a 95% clip-bootstrap CI and **frozen before Stage 5**.
- (iv) Computing them is a **reference-only analysis step, "R0"**: no generation, CPU, J needs SMPL-X. It also covers the left-side and L–R joint-space statistics and the V-R3 synthetic checks. It needs your approval (checklist item 6).
- (v) **0.47 / 0.32 are retained only as historical descriptive values** for the rotation-space statistic on the stated dev/test sets.

E2e does **not** need the train targets: T3/T4 test changes vs A0, and D-a/D-b use t*₃₂.

### 6.1 Components

| Component | Objective | Definition | Status today | Exploit | Protection / validation |
|---|---|---|---|---|---|
| **r_coord** = r_ah + r_lr (space R) | P1a (M-C/κ) | r_ah = −\|coord_ah^R(s) − τ*_ah^R(s)\| per side (right arm–right hand; left arm–left hand); r_lr = −\|coord_lr^R − τ*_lr^R\|. **Rev. 4.0:** train-reference targets per §6.0 replace the fixed 0.47 / 0.32 | valid on real data; **chance-satisfiable** [V]; space-specific (E0 V2) | chance alignment; shared spikes; over-coupling (hence target-matching) | c_jerk; joint-space coord^J (evaluation only); other-sentence null |
| **r_dom** (space R) | P1b (M-C/σ) | −\|dom^R − t*^R\|, where t*^R = the **train-reference mean log-ratio** (rev. 3.1; value not yet computed [U]) | **E[r_dom] ≤ −\|t*\| under equal hand marginals** [D, Thm 4]; e.g. −0.274 if t* were log 0.76 (illustrative) | **left-hand suppression** | left-hand constraints below; evaluation levels D-a to D-c (§6.5); dom^J (evaluation only) |
| **c_left** (constraints, M-C/σ only) | protect the left hand | (i) side calibration c_L ≥ log 0.8, where c_s = median log(A_s^gen / A_s^ref) at batch level using train references; (ii) left jerk ≤ base × 1.10; (iii) fraction of frames > 45°/frame up by ≤ 2 points; (iv) L–R coordination not below base − 0.03 | distribution-level reference statistics (train references, never at inference) | — | E2e T6-B; joint-space left-hand error and Fréchet distance (evaluation) |
| c_art, c_jerk (both components) | no collapse or exaggeration | articulation within ±10% of the base; jerk ≤ base × (1 + δ) | measured [V] | — | — |
| KL terms | stay near the pretrained distribution | exact (App. G.4); separate α_κ, α_σ | exact [D] | — | log each term separately |
| Excluded: BT, reference error / DTW | — | — | invalid in GF [V] | — | evaluation only, with caveats |

**D-c vs suppression:** defined in §6.5 (and App. G.6.3). D-c is "target-directed dominance without detected left-hand degradation"; the word "genuine" is no longer used.

**Reward-validity status (rev. 4.0; replaces rev. 3.2).** What each component is valid *as*. Perceptual validation is out of scope, not pending.

| Component | Measurable statistic? | Valid as a statistic on real data? | Cross-space check (E0) | Perceptually validated? |
|---|---|---|---|---|
| r_ah, r_lr (coordination, R) | yes | yes: reference 0.44–0.47 / 0.32 vs GF ≈ 0.02 [V] (V-R1) | the GF deficit is present in J; per-clip ρ ≈ 0.5; levels differ | **out of scope** (PH). Also chance-satisfiable (A3) |
| r_dom (log-ratio to t*^R) | yes (t*^R not yet computed) | yes: reference right-dominant in 94% of clips [V] | ρ ≈ 0.96; means agree | **out of scope** (PH) |
| c_left, c_art, c_jerk (constraints) | yes | yes, as descriptive statistics | J left-hand error available | **out of scope.** The thresholds (log 0.8, ±10%, +10%, +2 points) are conventions [U] |
| KL terms | exact [D] | n/a | n/a | n/a (a regulariser, not a quality measure) |

**Wording rule (rev. 4.0):** components are called "**motion-statistic rewards**", never "quality rewards" or "naturalness rewards". Results about them are type M.

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
- **Primary evaluation uses quantities not in the reward (rev. 4.0: automated only):**
  1. SMPL-X joint-space statistics (coord^J, dom^J, joint error; §6.0), never in the reward;
  2. distribution-level Fréchet distances (joint body+hand motion vs real; left-hand features vs reference-left);
  3. per-stream non-inferiority / equivalence;
  4. corpus-level BT and SMPL-X MPJPE (secondary checks only: "no regression detected", §0.1).
- Reward statistics (space R) are reported and labelled as training objectives.
- Dominance is reported at the separate levels D-a to D-c (§6.5). D-d is removed (rev. 4.0).
- Human ratings are removed (E1 deferred indefinitely).

### 6.4 Automated validity criteria (rev. 4.0; replaces the two-phase human criteria of rev. 3.3a)

These establish that each reward statistic is a **valid measurement of a motion property**. They do not establish perceptual relevance (out of scope).

| # | Criterion | Rule | Status |
|---|---|---|---|
| V-R1 | **Discrimination:** the statistic separates reference motion from the GF base | reference vs GF base differ, with non-overlapping 95% CIs, on dev | **met** for coordination (R: 0.439 vs 0.022) and dominance (−0.400 vs 0.006) [V, E0.6] |
| V-R2 | **Cross-space consistency:** the deficit direction is the same in R and J | same sign of (reference − GF base) in both spaces | **met** for both [V, E0.6]. Agreement strength is reported: coordination ρ ≈ 0.5, dominance ρ ≈ 0.96 |
| V-R3 | **Non-triviality:** the statistic is not maximised by a degenerate motion | the static-pose, mean-pose and shared-spike cases are checked analytically or on synthetic inputs; the constraints c_art, c_jerk and c_left are in place | design: target-matching rewards plus constraints (§6.1–6.2). **Synthetic check not yet run** [U]. It belongs to the reference-only analysis step R0 (§6.0 rule iv; checklist item 6), not to E2e |
| V-R4 | **Scope honesty:** chance satisfiability is quantified | the A3 other-sentence null is reported alongside any coordination gain | **met** as a reporting rule (A3: best-of-8×8 0.408 vs other-sentence 0.452 [V]) |

- **Consequence:** P1a and P1b proceed to E2 without a human gate.
- **What remains PH (not claimed):**
  - that a higher coordination statistic is perceived as better coordinated;
  - that D-c dominance is perceived as handedness;
  - that "no detected left-hand degradation" means a natural left hand.

**Confirmatory evaluation at Stage 6** is automated only: paired CRN comparisons, ≥ 3 seeds, clip-bootstrap CIs, both spaces, and the pre-registered margins.

---

### 6.5 Dominance evaluation levels (rev. 3.1; D-d removed in rev. 4.0)

**Rev. 4.0:** three levels (D-a, D-b, D-c) are reported **separately**. Passing a lower level never implies a higher one. The former fourth level, D-d (perceptual dominance by human 2AFC), is removed from the objectives and success criteria; its definition survives only in the archived rev. 3.3a.

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

**E2e can establish at most D-a, D-b and D-c for fixed side scales on 32 dev clips. It cannot establish that a learned σ policy generalises.** D-d (perceived dominance) is **removed from scope** (rev. 4.0). Any statement about perceived dominance is type PH and is not made.

**Measurement space of D-a to D-c (rev. 4.0 clarification):** D-a to D-c are computed in **rotation space**, as pre-registered (gating). E2e-J (§15.3.2) reports the same D-a/D-b computations in joint space with t*₃₂^J, as a **non-gating** robustness check. Since E0 found per-clip ρ ≈ 0.96 for dominance, agreement is expected and is **not** counted as independent confirmation.

## 7. Evaluator strategy

### 7.1 Human evaluation: deferred indefinitely (rev. 4.0)

- **E1 is deferred indefinitely** by your decision (time constraints). This means:
  - no recruitment;
  - no rater contact;
  - no pilot;
  - no ethics submission;
  - no participant-facing materials.
- Human evaluation is **not a prerequisite** for any E2 step, for R0, or for Stage 5–6 automated validation.
- The rev. 3.3a design (constructs, pilot, GLMM power simulation; old §7.1.1–7.1.4) is **not carried forward**. It survives only in [archive/STAGE4_REPORT_rev3.3a.md](archive/STAGE4_REPORT_rev3.3a.md) and would need a new revision and your approval to revive.
- **Renders:** SMPL-X renders may be produced for **researcher inspection only**, to spot pipeline bugs such as a wrong flip or a detached hand. They are **not evidence** for any claim, are never scored, and never leave this machine (licence).

### 7.2 SMPL-X (E0): done
- **Licence:** personal, non-commercial research, no redistribution, cite. Registered by you ([licence note](stage4/e0_licence_note.md)).
- **Delivered** (E0, [report](stage4/E0_REPORT.md)):
  - validated FK (C0–C4);
  - Windows rendering without Blender;
  - joint-space metrics on the dev dumps;
  - rotation-vs-joint validation (§1.4).
- **Role now:** the second measurement space J (§6.0) and the secondary joint-error check. Renders for inspection only.
- **Does not provide:** semantics, a body shape or translation (not in the data), or FLAME-faithful faces.

### 7.3 Learned evaluator
- Deferred.
- If revived, it would be an evaluation-only metric. Without human ratings it **cannot be validated perceptually**; it could only be validated as a discriminator of real vs generated motion (type M).

### 7.4 Minimum viable pathway [Pr] (rev. 4.0)
1. **Done:** E0.
2. **Next:** E2d → E2e (+ E2e-J) → E2a → E2b → E2c, each separately approved; R0 (train-reference targets, V-R3) on its own approval, before Stage 5.
3. **Stage 6:** automated evaluation in both measurement spaces, comparators, secondary checks. No human study.

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
  - (a) space-R reward statistics, labelled as training objectives;
  - (b) SMPL-X FK → space-J statistics (coord^J, dom^J) and joint error (rev. 4.0: evaluation only);
  - (c) Fréchet distances (joint motion; left-hand vs reference-left);
  - (d) per-stream non-inferiority / equivalence;
  - (e) corpus BT (secondary);
  - (f) renders for researcher inspection only (not evidence; no human items, rev. 4.0).

## 13. Workflow (Stage 5–6, only after approval)
1. Freeze the protocol: dev selection, test once, seeds, oracle length disclosed, flagged-clip subsets.
2. Gates (rev. 4.0): E2 passes and R0 (train targets frozen), then M-C/κ and M-C/σ trained **separately**. Then M-D at a matched GPU-hour budget. Then comparators at matched sample budgets. No human gate.
3. Paired comparisons on identical clips and base noises (CRN), all through one implementation.
4. ≥ 3 seeds; clip-bootstrap CIs; both measurement spaces reported; claims typed G / M (§0.2).

## 14. MDP design audit

| Check | M-C | M-D |
|---|---|---|
| State sufficiency | pass (output deterministic in (s, a)); pooled text limits semantics, not P1 | pass |
| Action controllability | noise-level coupling exact [D]; **output transmission [H]** (E2e); gradients via 10 steps [H] (E2a); K = 1 invalid [D] | weights controllable; P1 reachability limited [D] |
| Transition implementability | **conditional:** the unrolled sampler must equal upstream (E2d T0) | pass |
| Reward validity | valid as measurable motion statistics (V-R1, V-R2, V-R4 met; V-R3 pending R0); perceptual validity out of scope (rev. 4.0) | same |
| Reward exploitation | chance alignment (reported via the A3 null; cannot be ruled out without humans); spikes (c_jerk); **left-hand suppression** (c_left, D-c test); off-manifold (exact KL, σ bounds); space-specific gaming (checked by J evaluation) | + timing-diversity collapse |
| Episode suitability | horizon 1 exact | per algorithm |
| Data | train texts/lengths; train references only for distribution-level constraints | + references for CFM |
| Compute | estimated feasible [E]; **E2d gate** | feasible (ORW) [E] |
| Capability preservation | strongest; κ exact marginals [D] | anchor + regression tests |
| Independent evaluation | yes (§6.3) | yes |
| **Overall** | **conditionally valid**: E2e transmission, E2d feasibility, R0 targets (rev. 4.0: the E1 condition removed) | comparator with pre-registered predictions |

---

## 15. Validation plan

### 15.1 Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| FM1 (rev. 4.0) | the R statistic improves but the J statistic does not (space-specific gain) | E2e-J; Stage 6 J evaluation | report the claim as R-only (S2 without S3); no cross-space claim |
| FM1b (rev. 4.0) | the statistics improve but the motion would not look better | **undetectable in this scope** | stated limitation (§16.1); never claimed otherwise |
| FM2 | coordination gain no larger than chance alignment | A3 other-sentence null reported with every gain | measurable-motion-only scope (already the claim) |
| FM3 | fewer-step gradients don't transfer | E2a | K = 10 (default) |
| FM4 | noise steering cannot move timing | E2e, E2c | stop; options to you |
| FM5 | atypical noise artefacts (σ) | ‖ε̃‖²/d, articulation, jerk, renders | tighten σ bounds, raise α_σ |
| FM6 | M-D couples via timing collapse | same-text agreement ↑ | report (confirms Prop 2) |
| FM7 | comparators match M-C | paired comparison | H0 or amortisation-only claim |
| FM8 | test contamination | — | paired relative claims only |
| ~~FM9~~ | ~~rater noise~~ | — | removed in rev. 4.0 (no raters) |
| FM11 | marginal guarantee silently broken (train mode, precision mismatch, padded frames) | E2e T1/T2; T0 | fix; Theorem-3 checklist |
| FM12 | dominance only by left-hand suppression | E2e T5-B/T6-B; J left-hand error and Fréchet distance (rev. 4.0: the E1 item removed) | report; prefer N9 |
| FM13 | coupling does not transmit (E2e T3/T4 fail) | E2e | **stop and present options; no automatic switch** (§15.2) |
| FM14 | equivalence tests underpowered | calibration rule (§15.4) | report "inconclusive", not pass |

### 15.2 Sequence, dependencies and stop gates

**Nothing proceeds without your explicit go-ahead after each report.**

| Order | Step | Depends on | Scope summary | Pass → next decision | Stop gate | Cap |
|---|---|---|---|---|---|---|
| — | **E0** SMPL-X (independent track) | your registration | §15.5 | **done 2026-11-03**: FK valid; joint space available (§1.4) | — | done |
| — | **R0** reference-only targets (rev. 4.0) | E0 | §6.0 rule (iv): train-reference targets in R and J with CIs; J left-side and L–R statistics; V-R3 synthetic checks. No generation | targets frozen before Stage 5; independent of the E2 order | data error ⇒ stop | 2 h CPU [E]: 29,630 train references; J FK at ≈ 0.15 s per clip, from E0.6 |
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
- Do side scales reach dominance levels D-a to D-c (§6.5), or only shift the ratio by suppression? (D-d was removed from scope in rev. 4.0.)
- **Rev. 4.0:** E2e is a **technical feasibility** experiment. Its gating tests are unchanged and are computed in rotation space. Joint-space results come from the separate, non-gating E2e-J analysis (§15.3.2).

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
| **T5-B** dominance (SS group; rev. 3.2) | SS | the levels of §6.5 | Report **D-a** (movement), **D-b** (≥ 50% gap reduction; over-shoot flag), and **D-c** (target-directed without detected left-hand degradation) vs suppression, per condition, with the §6.5 thresholds and aggregation. **"M-C/σ feasible at D-c"** = at least one SS condition reaches D-c (exploratory). (D-d removed from scope, rev. 4.0) |
| **T6** non-inferiority | BH/LR: via T2. SS: right hand (and body) | right hand with σ_R = 1: TOST ±5% (exact by theory). σ_R > 1: right jerk ≤ +10%, frames > 45°/frame ≤ +2 points | per condition |
| | SS: left hand | left jerk ≤ +10%; frames > 45°/frame ≤ +2 points; Fréchet distance of left-hand joint-angle features (15 joints × {mean, std} = 30-d) to **dev-256 reference left hands** not above A0's by more than the A0–A0′ 95th-percentile difference; coord_lr not below A0 − 0.03 | all four must hold for D-c (aggregation per §6.5) |

**What E2e can and cannot establish:**

| E2e outcome | Licenses | Does not license |
|---|---|---|
| T3/T4 pass (fixed random or arm-structured coupling transmits) | "some frame-local linear noise coupling raises output temporal coupling **in rotation space**, at measured KL cost" (feasibility of the family). With E2e-J agreement, also "...and in joint space" (non-gating, descriptive) | that a *learned* controller will find useful or generalising coupling; any perceptual or semantic claim |
| T3/T4 fail at all seeds and ranks | evidence against transmission for *these* orientations and ranks | impossibility for the family: learned U, V might find transmitting directions (U8). E2c (ii) tests family capacity directly, under its own approval |
| T5-B reaches D-c | "fixed side noise scaling shifted the log-ratio toward the dev reference and halved the gap (D-a, D-b), with no left-hand degradation detected on the specified checks (D-c), on 32 dev clips (exploratory)" | **any perceptual dominance claim (out of scope, rev. 4.0)**; that a learned σ policy generalises; that the left hand is natural in any untested respect |
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
| 5 | Remaining BH conditions (n = 8) | T5-A fail ⇒ **stop** (wording consistency only: this restates the registered T5-A rule "Stop on any fail" for all BH and LR conditions, §15.3, and the §15.2 stop gate; preflight P-9, 2026-11-03) |
| 6 | Remaining LR conditions (n = 8) | T5-A fail ⇒ **stop** (same; P-9) |
| 7 | SS conditions (n = 8), unless R3 | — |

**Why calibration-inconclusive continues while fail/straddle stops:**
- A fail or straddle is *evidence against* an implementation condition.
- A calibration-inconclusive result is *absence of sufficiently precise evidence*. It does not indicate a violation.
- T3/T4/T5-B, the actual feasibility questions, can still be answered.
- Every per-stream preservation statement in the E2e report is then labelled **"theory-conditional (Theorem 3); empirical eight-metric check inconclusive"** (see §15.4.4).

The cap still applies: at step 3, the n* = 32 path is already within the worst-case accounting above.

### 15.3.2 E2e-J: joint-space secondary analysis (new in rev. 4.0; non-gating)

**Purpose:** report T3, T4 and the T5-B D-a/D-b computations in SMPL-X joint space (§6.0), so that every E2e coordination and dominance result states whether it also holds in the second measurement space.

| Item | Specification |
|---|---|
| Input | E2e's generated rotations for every sample of every condition (body, left hand, right hand; active frames). **The only change to E2e itself:** these arrays are saved to `experiments/stage4/e2e/dumps/`, ≈ 1.2 GB default, ≈ 2.2 GB worst case [E]. Writing is within the 1.5 h cap's I/O headroom (§15.3.1 (iii)) |
| When | after E2e finishes (or stops), as a separate run. **It never feeds back into any E2e decision** |
| Environment | `.venv-render` (CPU); SMPL-X neutral; the E0.4 FK setup; `flip_left_hand=True` |
| Statistics | coord_ah^J(L), coord_ah^J(R), coord_lr^J, dom^J per sample; the §6.5 aggregation (per sample → per clip → population); 2,000-replicate clip-cluster bootstrap paired by clip, 95% CIs |
| Outputs | **T3-J / T4-J:** Δ vs A0 per BH/LR condition, with CI. **T5-J:** D-a and D-b in J using t*₃₂^J (recomputed per replicate), per SS condition. **Agreement table** per condition: "both" (same sign, both CIs exclude 0), "R only", "J only", "neither" |
| Interpretation | descriptive. A1 (oracle length) and pseudo-GT caveats apply. For dominance, agreement is expected (E0 ρ ≈ 0.96) and is not counted as independent confirmation |
| Runtime | default 4,096 samples × ≈ 0.15–0.2 s FK ≈ 10–15 min; worst ≈ 7,168 samples ≈ 20–25 min; plus bootstrap [E]. **Cap 1 h** |
| Stop | an FK failure (non-finite values, C2-type bone check > 1e-4) ⇒ stop and report; no E2e result is affected |

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

### 15.5 E0 scope (independent track): **completed 2026-11-03**

| Step | Who | Scope | Outcome ([E0 report](stage4/E0_REPORT.md)) |
|---|---|---|---|
| E0.1 | **You** | register at smpl-x.is.tue.mpg.de; download SMPL-X v1.1 NPZ (personal licence) | done |
| E0.2 | You / me | place it at `models/smplx/smplx/`; it never leaves this machine; licence note recorded (not the model) | done (NPZ extracted from your zip) |
| E0.3 | Me | new `.venv-render` (existing environments untouched); pinned `smplx`, `trimesh`, renderer; lock file | done |
| E0.4 | Me | FK sanity on 5 dev GT clips (bone lengths, wrist attachment, left-hand flip, NaNs) | pass C0–C4 |
| E0.5 | Me | Windows rendering feasibility; 3 dev clips × {reference, KF2P, GF} for **your review only**; a Blender install would need a separate approval | feasible, no Blender. Rev. 4.0: renders are for inspection only, never evidence |
| E0.6 | Me | joint-space metrics on existing dev dumps (released-checkpoint, not paper reproduction) | done; §1.4 |
| Stop | — | report; E1 stays deferred | rev. 4.0: E1 deferred **indefinitely** |
| Excluded | — | test-set renders; participants; FLAME downloads. **MANO is not required** (Stage 2 D12) | respected |

---

## 16. Assumptions, constraints and safeguards
- **A1:** reference length is an oracle in all GF work (disclosed).
- **A2:** the face is excluded from P1.
- **A3:** the targets come from pseudo-GT How2Sign references, which include extraction errors (D4):
  - rev. 4.0: train-reference targets per measurement space (§6.0). 0.47 / 0.32 are historical R-space descriptive values only;
  - the dominance log-ratio t*^R (train) and t*^J; for E2e, t*₃₂ (target) and t*₂₅₆ (margin constant);
  - side calibration.
  - The value 0.76 is the dev-256 mean of per-clip ratios (S₃), used only as a descriptive reference.
- **A4:** SMPL-X neutral body, betas 0, root fixed (no shape or translation in the data); the face basis differs from the authors' SMPLFX. Joint-space statistics inherit these choices.
- **A5 (rev. 4.0):** no human evaluation; all claims are type G or type M (§0.2).
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

### 16.1 Remaining limitations and risks without human verification (rev. 4.0)

| # | Limitation / risk | Consequence | Mitigation in this design | Residual |
|---|---|---|---|---|
| L1 | **No perceptual validation** of any statistic | an improved statistic may not look better, and may look worse | claims restricted to type M; per-stream non-inferiority; jerk, extreme frames and Fréchet distance; renders for inspection only | **unmitigable in scope:** "looks better" stays PH |
| L2 | **Goodhart risk:** the reward statistic is optimised directly | gains may be specific to the statistic's definition | target-matching (not maximisation); constraints; evaluation in J, never in the reward | for **P1b**, J nearly re-measures R (E0 ρ ≈ 0.96), so J offers little protection; for P1a, ρ ≈ 0.5 offers partial protection |
| L3 | **Chance satisfiability** of coordination (A3 null) | coupling may be content-unspecific | the A3 null is reported with every gain; no content claim | cannot be ruled out automatically |
| L4 | **Space dependence** of coordination (E0 V2) | R and J gains may diverge | separate targets; the agreement table in E2e-J and Stage 6 | a claim may end up R-only (FM1) |
| L5 | **Pseudo-GT references** (extraction errors, D4 wrist spikes) | targets are biased by extraction noise | train-set targets with CIs; flagged-clip subsets reported | the bias size is unknown |
| L6 | **Left-hand protection is a finite checklist** | undetected left-hand degradation is possible | five statistics plus J left-hand error and Fréchet distance | "no degradation detected" only |
| L7 | **Oracle length; released checkpoint; How2Sign only; possible test contamination (D10)** | external validity | disclosed; paired relative claims | unchanged |
| L8 | **Conventions** (±5%, δ_S₂, the D-a/D-b/D-c thresholds) not derived from perception | thresholds could be too lax or too strict | pre-registered and frozen; operating characteristics reported (§15.4.2) | not perceptually grounded; without humans this cannot change |
| L9 | **Joint space depends on SMPL-X choices** (neutral, betas 0, no root) | J statistics are model-dependent | fixed and recorded (A4) | another body model could give other values |
| L10 | **T4-b in J** relies on SMPL-X left/right hand mirror symmetry | if asymmetric, dom^J could be biased away from 0 even under equal marginals | U-A11: a numerical symmetry check in R0; E0 GF dom^J = 0.010 [−0.013, 0.031] is consistent with no bias | unverified analytically |
| R1 | **Over-reach in reporting** | readers may infer perceptual quality | the claim-type labels; §0.2 ceilings; mandatory "type M" wording | — |
| R2 | **Time pressure** (4-hour constraint on this revision) | documentation errors | change log; archived previous revision for diffing | your review |

## 17. Decision log

| # | Decision | Status |
|---|---|---|
| D4.1 | P1 = P1a coordination + P1b dominance as **separate objectives**; rev. 4.0: measurable-motion claim scope (was perceptual-motion) | **Scope set by you (2026-11-03); pending approval of rev. 4.0** |
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
| D4.8 | Evaluator path. Rev. 4.0: E0 (done) → automated evaluation in spaces R and J; E1 deferred indefinitely; learned evaluator deferred | **E0 done; E1 deferred indefinitely by you (2026-11-03)** |
| ~~D4.8b~~ | ~~Human constructs~~ | **Withdrawn** (rev. 4.0) |
| ~~D4.8c~~ | ~~Confirmatory sample size from the GLMM simulation~~ | **Withdrawn** (rev. 4.0) |
| D4.9 | Comparators N1, N3′, N4, N5, N9 required; N6 for M-D; N7 exploratory | Proposed |
| D4.10 | Face excluded from P1 | Proposed |
| D4.11 | SLERP deferred | **Approved** |
| D4.12 | GF-T2P primary | **Approved** |
| D4.13 | No architecture implementation; N7 exploratory only | **Approved (scope)** |
| D4.14 | E2 order E2d → E2e → E2a → E2b → E2c; stop after each | Proposed (your order) |
| D4.15 | Equivalence procedures and pass/fail rules in §15.3–15.4 pre-registered. T2 = **eight-metric generated-motion marginal check** (not full distributional equivalence) | Proposed (rev. 3.1 wording) |
| D4.16 (rev. 3.1) | Theorem 4 stated per statistic with assumptions T4-a to T4-d. Mean-type S₁–S₃ fixed under equal hand marginals; S₄ not determined; T5-A gates only on S₁/S₂; r_dom target = reference mean log-ratio t* | Proposed |
| D4.17 (rev. 3.1; amended 4.0) | Dominance reported at three separate levels D-a (movement), D-b (proximity), D-c (target-directed, no detected left-hand degradation); **D-d removed** (rev. 4.0) | Proposed |
| D4.18 (rev. 3.1) | Semantic wording: only "no regression detected on the specified secondary checks"; no semantic-preservation or translation-quality claim | Proposed |
| D4.19 (rev. 3.1; counts revised in 3.2) | E2e runtime accounting incl. explicit T0 executions, 1.5 h cap and pre-registered run order (§15.3.1) | Proposed |
| D4.20 (rev. 3.2; amended 3.3) | T5-A as a TOST for S₂ with δ_S₂ = min(0.05, max(0.025, \|t*₂₅₆\|/4)); t*₂₅₆ computed from existing dev-256 references before any generation; pre-run branches R1/R2/R3; three-way outcome; S₃ descriptive only | Proposed |
| D4.23 (rev. 3.3) | Two targets: t*₃₂ (D-a/D-b, estimated, bootstrap-propagated) vs t*₂₅₆ (margin constant, fixed). D-a "direction not assessable" if the CI of t*₃₂ − m_A0 includes 0. Over-shoot flag made direction-general | Proposed (corrections documented) |
| D4.24 (rev. 3.3) | Run order: step 0 (references only) → T0 → A0/A0′ → calibration loop fixing n* → gate conditions at n* → the rest. T2 calibration-inconclusive continues with theory-conditional wording; fail/straddle stops. Assumption-evidence table (§15.4.4) | Proposed |
| D4.21 (rev. 3.2) | D-c renamed and strengthened (requires D-a + D-b + no over-shoot + left-hand criteria); D-b tested on the gap ratio; exact aggregation and bootstrap procedure | Proposed |
| D4.22 (rev. 3.2; amended 4.0) | All reward components are "motion-statistic rewards"; perceptual validation is out of scope (not pending); automated validity criteria V-R1 to V-R4 | Proposed |
| D4.25 (rev. 4.0) | E1 deferred indefinitely; no human gate for E2, R0 or Stage 5–6; human-evaluation design not carried forward | **Your decision** (2026-11-03) |
| D4.26 (rev. 4.0) | Two distinct measurement spaces, R (reward and gating) and J (evaluation only); targets are space-specific; 0.47 / 0.32 retired as targets | Proposed (your instruction) |
| D4.27 (rev. 4.0) | All training targets from train references per space, with CIs, frozen before Stage 5 (R0, reference-only) | Proposed |
| D4.28 (rev. 4.0) | Claim-type labels G / M / PH; strongest automated claims S1–S6 (§0.2) | Proposed |
| D4.29 (rev. 4.0) | E2e-J: non-gating joint-space secondary analysis; E2e saves its generated rotations | Proposed |
| D4.30 (rev. 4.0) | Secondary checks: corpus BT + SMPL-X frame-aligned MPJPE (the 4AFC removed; not DTW-JPE) | Proposed |
| D4.31 (rev. 4.0) | E2 order and all E2e thresholds, margins, branches and the run order unchanged | Proposed (unchanged from 3.3a) |

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
| U-A11 (rev. 4.0) | T4-b in joint space: the SMPL-X left/right hand geometry is an exact mirror, so dom^J uses "the same functional" for both sides | §6.0, §16.1 L10, App. G.6.1 | unverified; numerical check in R0. E0 GF dom^J ≈ 0 is consistent |
| U-A12 (rev. 4.0) | The J coordination construct (wrist linear speed vs wrist-local finger linear speed) is one of several defensible definitions | §6.0 | fixed by E0.6, before any E2 data; alternatives not explored |
| U-A13 (rev. 4.0) | Train-reference target values τ*^R, τ*^J, t*^R, t*^J | §6.0 | not computed; R0 |
| U-A14 (rev. 4.0) | J statistics not yet computed: left-side arm–hand and L–R coordination | §6.0 | R0 (references), E2e-J (generated) |

| # | Uncertainty | Type | Resolved by |
|---|---|---|---|
| Q1 | Does frame-local linear coupling transmit to output timing (body–hand; L–R)? | experimental | E2e T3/T4 |
| Q2 | Can a learned or optimised U, V find transmitting directions that random ones miss? | experimental | E2c (ii); Stage 5 |
| Q3 | Does side scaling reach D-a to D-c rather than suppression? | experimental | E2e T5-B/T6-B |
| Q3b (rev. 3.1) | Value of t* (train reference mean log-ratio); is S₄ movable alone under equal marginals? | factual / mathematical | t*: computable from train references (needs approval as an analysis step); S₄ alone: [U], not a goal |
| ~~Q3c~~ | ~~Perceptual dominance (D-d)~~ | — | **closed as out of scope** (rev. 4.0) |
| Q4 | Size of the reverse-KL family gap to q* | mathematical/empirical | E2c reference only |
| Q5 | Is P(A_R > A_L) movable under equal marginals, and would that be desirable? | mathematical | not a goal |
| Q6 | Input-gradient activation memory; body U-Net memory | experimental | E2d |
| Q7 | Ten-step Jacobian-product health | experimental | E2a |
| Q8 | Condition-number bound for the three-block Σ | mathematical | numerical logging |
| Q9 | Rank, σ bounds, frame-varying parameters; whether to test μ | design | after E2e; μ needs approval |
| Q10 | Are the equivalence tests adequately powered at ≤ 32 noises per clip? | experimental | §15.4.2 calibration |
| Q11 | Are the three checkpoints' M-CLIP weights identical (one cached embedding)? | factual | E2d (hashing, read-only) |
| Q12 | Is the coordination statistic perceptually meaningful? Is D-c dominance perceived? | experimental (human) | **not resolvable in scope** (rev. 4.0); stated as limitation L1 |
| Q13 | Checkpoint provenance / contamination (D10) | factual | unresolved; no author contact without permission |
| ~~Q14~~ | ~~Software for the GLMM simulation~~ | — | **closed** (rev. 4.0; no human study) |
| Q15 (rev. 4.0) | Do R-space coordination gains appear in J? | experimental | E2e-J; Stage 6 |

## 19. Approval checklist

Each item is independent.

**Approval vs execution (rev. 4.0 consistency rule):**
- Approving an item here, whether "Approve" or "Approve in principle", approves the **specification only**. It is **never execution authorisation**.
- An experiment runs only after your separate, explicit go-ahead naming that step.
- For every step after E2d, that go-ahead is given after my report on the previous step.
- As of rev. 4.0, **no experiment (E2d, E2e, E2e-J, E2a, E2b, E2c, R0) is authorised to run.**

| # | Decision | Recommendation |
|---|---|---|
| 1 | Stage 4 **revision 4.0** as the design: measurable-motion scope (§0.1); claim types and ceilings (§0.2); P1a/P1b separated; two measurement spaces with space-specific targets (§6.0); automated validity V-R1 to V-R4 (§6.4); M-C Gaussian default with M-C/κ and M-C/σ; K = 10; the same-implementation rule; M-D comparator; dominance levels D-a to D-c; secondary checks worded as "no regression detected"; limitations §16.1 | Approve |
| 2 | Appendix G (revision 4.0: wording only in G.6.3; T4-b note for J) | Approve after review |
| 3 | E0 | **Done** (2026-11-03) |
| 4 | **E2d** (§15.2; [checklist](stage4/E2_EXECUTION_CHECKLIST.md) §E2d) | Approve the specification. It is the next step in order; it **runs only on your separate explicit go-ahead** |
| 5 | E2e (§15.3–15.4 unchanged; plus saving the dumps for E2e-J) | Approve in principle (specification only); execution needs a separate go-ahead after the E2d report |
| 5b | E2e-J (§15.3.2; non-gating, CPU) | Approve in principle (specification only); execution needs an explicit go-ahead, which you may give in the same message as the E2e go-ahead |
| 6 | **R0** reference-only train targets and V-R3 checks (§6.0) | Approve in principle (specification only); execution needs its own explicit go-ahead, schedulable any time before Stage 5 (CPU, no generation) |
| 7 | E2a | Approve in principle (specification only); execution needs a separate go-ahead after the E2e report |
| 8 | E2b | Approve in principle (specification only); execution needs a separate go-ahead after the E2a report |
| 9 | E2c, including (ii) the family-capacity test | Approve in principle (specification only); execution needs a separate go-ahead after the E2b report |
| 10 | M-D′; the mean-shift variant of M-C/σ | Defer |
| 11 | E1 human evaluation | **Deferred indefinitely** (your decision); no action |

**Not requested:** Stage 5, training, fine-tuning, architecture changes, GPU rental, recruitment, rater contact, author contact.
