# Stage 4 closure and Stage 5 readiness assessment

*2026-11-03.*

## Update 2026-11-04 (latest): exploratory Stage 5 ACMS pilot run (your authorisation; `stage5/STAGE5_500EP_REPORT.md`)

- **Run:** 500 episodes (REINFORCE + RLOO; ACMS arm-conditioned mean shift; target matching to 0.4514).
- **Held-out result:** dev-256 × 4 right arm–hand coordination (R) **+0.0022 [0.0014, 0.0031]** over uncoupled. All motion-preservation checks pass.
- **Verdict:** **pre-registered POSITIVE, negligible in magnitude** (0.5% gap closure; 0.05 not reached).
- **Effect on the record:** the Stage 4 conclusions are unchanged. This pilot is exploratory and does not validate P1a. Further training is not justified on effect size without a capacity check.

## Update 2026-11-04 (later): E2c (ii) done, route A precondition NOT met (your authorisation; details in `stage4/E2C_II_REPORT.md`)

**Measured [V]:**
- Per-clip optimisation of the M-C Gaussian family (C-c4/C-c5, 32 dev clips) gave a mean held-out right arm–hand coordination of **0.034 [0.007, 0.063]**, against the primary best-of-8×8 level of **0.446**.
- That is no gain over uncoupled sampling: −0.003 [−0.017, 0.012].
- The in-sample objective reached 0.737, a 0.70 overfitting gap.
- All parameters stayed feasible, with KL ≤ 2.7 nats/frame (bound never binding).
- **C-c6: registered negative outcome (FM4), not comparator-sensitive.**

**Implication [D]:** an amortised h_φ(c, L) in this family is bounded by the per-clip optimum and has no measured headroom. Reaching the benchmark would need a mean gain of about +0.41, which is about 11× the largest gain seen in any E2e or E2c (ii) condition.

**Updated readiness verdict:**
- **The results do not support a Stage 5 pre-registration for an amortised M-C controller.** Route A's necessary precondition is not met.
- Remaining options are your decision:
  - route B (a new problem-selection revision);
  - route C (close P1a with H0, now supported by both fixed-orientation E2e and per-clip-optimised E2c (ii));
  - a separately pre-registered many-noise per-clip capacity test, which I do not recommend as a route to training.
- The §5–§10 content below for route A is retained as a historical record and is superseded on this point.

## Update 2026-11-04: J target verification and skinning leakage (your authorisation; details in `stage4/J_VERIFY_LEAKAGE_REPORT.md`)

**J targets [V]:** on all 29,630 train references,
- 0 invalid J streams;
- 0 definedness changes;
- J v1.1 is bitwise identical to v1.

**The frozen J targets remain valid under J v1.1, unchanged.** All eight frozen targets (R and J) are now verified under the validity layer; the earlier "Still unverified" item is resolved.

**Skinning leakage [V, REAL n = 2,963]:**
- **Size:** a median 1.9% (L) / 1.0% (R) of the actual hand signal.
- **Effect:** it inflates J arm–hand coordination by +0.001 (CIs exclude 0), with per-clip ranking unchanged (Spearman ≥ 0.9995).
- **Not material by the pre-stated criterion.**
- **Exception [D]:** near-static hands under arm motion, where J reads leakage-only coordination (0.30–0.40) while R is undefined. That is the suppression regime seen in E2e.
- **Requirement for any future J evaluation of generated motion:** report the per-sample leakage ratio. This is a reporting recommendation, not a threshold.

**J as a secondary measure:**
- Adequate as **descriptive, non-gating** evidence.
- It is a different metric on the same rotations, not independent replication.
- R remains the gating space.

**Unchanged:**
- **Stage 5 training is not justified on current evidence**; E2c (ii) remains the necessary precondition for route A.
- S-3/S-4 are specified but not implemented.
- Nothing trained, generated or implemented; no threshold or target changed. Stage 5 not started.

## Update 2026-11-03: Steps 0 and 1 done (your authorisation; details in `stage4/NUMERICAL_SAFEGUARDS_REPORT.md`)

**Step 0, implemented:** S-1, S-2 (R v1.1) and S-6 (J v1.1) as a versioned layer (`experiments/stage4/validity/validity.py`).
- v1 code is bitwise unchanged.
- Unit tests: **21/21**. Run 1 was 19/20 because of one test-design error, kept and documented.

**Step 1, S-5 done:** on all 29,630 train references,
- **0 invalid streams**;
- v1.1 is bitwise identical to v1 on every per-clip value;
- **the frozen space-R targets remain valid under R v1.1, unchanged** (§3 and the §9 risk 2 below are now resolved).

**New finding [V]:** in J, a static hand pose under a moving arm still shows about 5.6e-5 m/frame of wrist-local hand motion. This is SMPL-X skinning leakage, about 2% of a moving hand.
- J arm–hand coordination therefore contains a small mechanical arm-to-hand component.
- Its size in real data is unmeasured [U]. It weakens how far J can serve as fully independent evidence for P1a.

**Still unverified:** the J targets under J v1.1 (an FK pass, not authorised).

**E2c (ii) remains the necessary next experiment for route A.** The safeguards change no statistic on any real data, so the capacity argument of §5.2 is unchanged.

**Scope:** documentation and analysis only.
- Nothing was trained, generated or implemented.
- No checkpoint, threshold or frozen target was changed. No test data was used.
- The only computation was a read-only analysis of existing arrays (§4, `experiments/stage4/speed_floor_analysis.py`).

**Labels:** [V] measured · [D] derived · [I] inference · [E] estimate · [U] unresolved.

**Bottom line:**
- **Stage 5 training is not scientifically justified on the current evidence and within your stated scope** (frozen base model; no further controller-design exploration; H0 accepted for P1a under the current design; P1b not feasible with side scaling).
- No defensible training objective remains in that scope. I have not invented a replacement.
- §5 states exactly what evidence would make training justified, and §10 gives the minimal plan if you choose to obtain it.

---

## 1. Stage 4 final status and evidence

| Step | Result | Evidence |
|---|---|---|
| E0 | PASS | FK validated; Windows renders; dev joint-space metrics (`stage4/E0_REPORT.md`) |
| E2d | PASS | unrolled sampler bitwise equal to upstream; M-CLIP shared; K = 10 gradient pass ≤ 8.80 GiB at B = 8; gradients finite (`stage4/E2D_REPORT.md`) |
| **E2e** | **FAIL (registered FM13)** | **T3** Δ arm–hand at κ0.9-seed0: R 0.017, L 0.022 (CIs include 0; needs ≥ 0.05). **T4** Δ L–R 0.035 [0.006, 0.066] < 0.05. T0, T1, T5-A: no fail; T2 calibration-inconclusive, so theory-conditional (`stage4/E2E_REPORT.md`) |
| E2e-J (non-gating) | completed | J analogues at the registered conditions < 0.05 (R 0.021, L 0.035; L–R 0.036). Orientation seed 2: J right arm–hand 0.058 [0.031, 0.086], descriptive (`stage4/E2EJ_REPORT.md`) |
| R0 | completed | frozen train targets in R and J (§3); U-A11 approximate mirror; V-R3 numerical-validity findings (`stage4/R0_REPORT.md`) |
| E2a, E2b, E2c | not run | stopped by FM13; E2c (ii) declined by you |

### Closure statement (your decision, 2026-11-03)

**P1a, coordination:**
- The tested **fixed-orientation M-C Gaussian noise-coupling design** failed the registered P1a transmission criteria. It is below the 0.05 threshold at the registered conditions, in rotation space (gating) and in joint space (descriptive).
- **H0 is accepted for P1a under this design.**

**P1b, dominance:** recorded separately.
- **Fixed side noise scaling** moved the log-ratio toward the reference direction (D-a 4/4 in R and J).
- It did not close the gap (D-b 0/4), and did not reach D-c (0/4).
- Left-scale reductions showed **suppression signatures** (left jerk 0.50–0.78×; left-hand Fréchet distance above the A0′ null). Right-scale increases raised right jerk ×1.39.

**What this does NOT establish:**
- **It does not establish that RL cannot improve SignSparK.** It concerns one controller family (frame-local linear Gaussian noise coupling and scaling over the frozen samplers), with fixed random or arm-structured orientations and fixed scales, on 32 dev clips.
- Untested within the family: learned orientations (U8), the mean shift, frame-varying parameters.
- Untested outside it: weight-space RL (M-D), architecture changes (M-D′, N7), per-step control, the N5 keyframe cascade.
- **No perceptual, semantic, intelligibility or ASL-quality claim is made in either direction.**

## 2. Accepted H0: scope and limitations

| Covered by H0 | Not covered |
|---|---|
| frame-local linear noise coupling with **random** (seeds 0–2) or **arm-structured** orientations, r ∈ {12, 60, 90}, κ ≤ 0.9, KL ≤ ≈ 14,600 nats per sample | **learned / optimised** orientations (U8; E2c (ii) declined) |
| fixed side scales σ ∈ {0.75, 0.85, 0.9, 1.0, 1.15} | learned per-context scales; the mean shift (deferred) |
| dev clips 0–31, GF, oracle length, released checkpoints | other clips, lengths, test data, other checkpoints |
| rotation-space registered criteria (gating); joint space descriptive | perceptual relevance (out of scope) |

**Limitations:**
- 32 clips; 8 noises for most conditions.
- T2 was calibration-inconclusive at n = 32, so per-stream preservation is theory-conditional (Theorem 3).
- The 0.05 transmission threshold is a convention [U].
- Small but significant orientation-dependent effects exist: R seeds 1–2: 0.033, 0.037; J seed 2: 0.058. So "the family cannot transmit" is **not** established [I].

## 3. Frozen reference targets (R0; `stage4/FROZEN_TARGETS_R0.json`)

These are frozen and never retuned. The source `r0_results.json` has SHA-256 427dd363…41d1e.

| Target | **Space R** (metric v1) | **Space J** (jspace v1) |
|---|---|---|
| left arm–hand τ_ah(L) | **0.610** [0.608, 0.612] | **0.422** [0.420, 0.424] |
| right arm–hand τ_ah(R) | **0.451** [0.449, 0.454] | **0.249** [0.247, 0.252] |
| left–right τ_lr | **0.323** [0.320, 0.325] | **0.320** [0.317, 0.322] |
| dominance t* | **−0.392** [−0.397, −0.388] | **−0.415** [−0.420, −0.410] |

**Rules:**
- **Never mix spaces.** A target is compared only with a statistic of the same space and metric version.
- The R targets were computed with R metric v1. Their equivalence under the proposed validity layer (§4, S-5) on the train references is **not yet verified** [U].

## 4. Required numerical safeguards

**The problem (R0 V-R3 [V]):**
- (a) The registered R-space dominance raises `ZeroDivisionError` for a frozen hand (A_R = 0).
- (b) For a static non-identity pose, Gram–Schmidt plus arccos near 1 gives frame speeds at the floating-point noise floor. Correlations and log-ratios of that noise are finite but meaningless (coordination −1.0, dominance −0.09).
- J space returns NaN correctly in both cases.

**Evidence for thresholds** (`experiments/stage4/speed_floor_analysis.json`, read-only on existing arrays) [V]:

| Quantity (rad/frame, R space) | Static non-identity noise floor | Minimum over 4,096 generated streams (E2e dumps) | Minimum over 256 dev reference streams |
|---|---|---|---|
| mean frame speed (activity / (L − 1)) | ≤ 1.3e-8 (max frame speed) | 5.7e-3 | 3.4e-3 |
| std of the frame-speed signal | ≈ 3e-24 | 1.4e-3 | 5.9e-3 |

**Proposed safeguards (none modifies a registered value on any input where the old code produced a valid result):**

| # | Safeguard | Kind | Effect on existing results |
|---|---|---|---|
| S-1 | Dominance: if A_L or A_R ≤ 0 (or non-finite), return **undefined (NaN)** instead of raising | **numerical validity check**, no new metric version (it only replaces an exception) | none: no existing result raised (R0: 0 NaN over 29,630 clips; E2e: no exception) |
| S-2 | **Near-static validity floor:** a stream is invalid if its mean frame speed < **1e-5** or its speed-signal std < **1e-6** rad/frame. Any statistic using an invalid stream is undefined | **new metric version R v1.1** (it changes outputs, from spurious finite to undefined, for near-static inputs) | **0 of 4,096** generated and **0 of 256** dev reference streams fall below the floors. The margins are ≈ 300× above the smallest real values and ≈ 1,000× above the noise floor. So v1.1 = v1 on every existing E2e and dev result [V] |
| S-3 | **Reward treatment of undefined:** an undefined statistic gets the **worst-case reward** for its term (−(1 + \|τ\|) for coordination; −(\|t*\| + 3) for dominance, bounded by clipping log-ratios to [−3, 3]). The sample is **counted, never dropped** | training rule (new pre-registration) | — |
| S-4 | **Evaluation treatment:** report the undefined fraction per condition. Primary statistics over defined samples plus a worst-case sensitivity analysis. Acceptance requires an undefined fraction ≤ the base model's + 0.5 percentage points | evaluation rule (new pre-registration) | E2e/R0 base: 0% undefined |
| S-5 | **R0 v1.1 equivalence check:** re-scan the train references with the S-2 validity layer (CPU, no FK, ≈ 10–15 min [E]). If 0 invalid streams, the frozen R targets hold under v1.1. If not, report the count and compute **separately versioned** v1.1 targets; **never overwrite v1** | verification (**needs your approval**) | — |
| S-6 | **J space:** the same structure (S-1 guard; a std floor in m/frame, proposed 1e-7, J positions being exactly static for static poses) | validity check | J was already NaN-correct in V-R3 |
| S-7 | **Training surrogate vs registered metric:** any training reward uses differentiable chordal speeds (as E2d). Evaluation uses the registered geodesic metric (R v1.1). Their per-clip agreement is to be reported | disclosure rule | — |

## 5. Training objective: assessment

**Question:** is there a defensible objective to optimise with a controller over the **frozen** SignSparK checkpoint, without claiming that M-C solves P1a or P1b?

### 5.1 What a frozen-base noise controller can change at all [D]

- **Coupling (M-C/κ):** preserves every per-stream output law exactly (Theorem 3).
  - It **cannot** change any per-stream statistic in expectation (articulation, jerk, activity, per-stream Fréchet distance).
  - It can change **only cross-stream structure**: P1a.
- **Scaling or mean shift (M-C/σ, μ):** change per-stream laws.
  - This is the only lever on per-stream activity and dominance: P1b.
- Therefore, in this controller class, every objective is either **P1a**, **P1b**, or a per-stream statistic reachable only through σ/μ.

### 5.2 Candidate objectives

| Candidate | Status | Defensible now? |
|---|---|---|
| P1a with fixed-orientation coupling | H0 accepted | **no** |
| P1a with **learned** coupling (amortised h_φ) | untested (U8). **Bound [D]:** for any clip c, an amortised controller outputs one member θ = h_φ(c) of the family, so its expected objective is ≤ the per-clip optimum sup_θ F_c(θ). E2c (ii) estimates (a lower bound on) that per-clip optimum. Without it there is **no evidence that any amortised controller can reach the target**; the only hint is the sub-threshold orientation dependence | **no**: the necessary capacity evidence is absent (E2c (ii) declined) |
| P1b with learned per-context σ | the E2e grid shows over-shoot or suppression at every tested scale. A per-context choice within the same family inherits the left-suppression mechanism of σ_L < 1 [I] | **no** |
| Per-stream quality (articulation, jerk, Fréchet) as the **objective** | κ cannot change it [D]. σ changes it, but with the trade-offs above. **The identity controller already satisfies the preservation criteria, so optimising them alone has the trivial optimum "do nothing"** [D] | **no** (they are constraints, not objectives) |
| Reference fidelity (DTW / MPJPE) | rejected in Stage 4: favours collapse to the mean pose (V2, V3) | **no** |
| BT / semantic reward | rejected (R6; weak; not a sole reward) | **no** |
| Face articulation (P2, Stage 4 §2.1) | listed as "secondary, later; gameable"; face excluded from P1 (A2); no validity analysis done | **no**: would need a new Stage 4-style problem analysis, not a substitution here |
| Weight-space RL (M-D, per-stream ORW) | changes model weights (outside "frozen base"). By Prop 1 it cannot produce dominance; coupling only through timing collapse (Prop 2) | outside your stated scope |

**Conclusion:**
- **No defensible training objective remains** within the frozen-base controller scope and your exclusions.
- Per-stream motion preservation and quality measures **can and should serve as hard constraints and evaluation-only metrics** for any future controller. They cannot be the objective.

### 5.3 What would make training justified (for your decision; nothing started)

| Route | What it needs | Then Stage 5 would train |
|---|---|---|
| **A. Capacity evidence for learned coupling** | E2c (ii) (per-clip family optimisation, C-c4, ≈ 40 min GPU, implemented and approved as a specification) reaching the C-c2 level. Because of the bound in §5.2, this is a **necessary** condition (strong, not conclusive: the per-clip optimiser is local) | an amortised M-C/κ for P1a (formulation §5.4) |
| B. Reopen problem selection | a new Stage 4 revision: e.g. M-D′ side-specific hand copies (P1b; changes weights), a keyframe-cascade controller (N5), or a validated per-stream objective | whatever that revision justifies |
| C. Close with H0 | none | no training. Stages 7–8 report the feasibility study and the negative result ("H0 remains an acceptable outcome", Stage 4 §0) |

### 5.4 Formulation of the only candidate (route A), for completeness. **NOT proposed for training now**

**Objective**, over train contexts (c, L) with base noise ε⁰ ~ N(0, I):

  J(φ) = E[ r(G₁₀(T_{h_φ(c, L)} ε⁰)) ] − α_κ · E[ L · KL_frame(h_φ(c, L)) ],  subject to E[c_k] ≤ 0 (dual ascent)

**Components:**
- **Reward:** r = −\|coord_ah^R(R) − 0.451\| − \|coord_ah^R(L) − 0.610\| − \|coord_lr^R − 0.323\|.
  - **Frozen R targets only**; S-3 for undefined values; chordal surrogate in training (S-7).
- **Transform:** T_θ = the Gaussian coupling family (App. G; BH structure; κ ≤ 0.9).
- **KL:** exact closed form, −½Σ log(1 − κ²) per frame.
- **Constraints c_k:** articulation ratio within ±10% of base, jerk ≤ 1.10 × base, extreme-frame increase ≤ 2 percentage points (§6.1). These hold in expectation by Theorem 3 for κ, so they act as monitored hard checks.
- **Evaluation-only:** J-space coordination vs frozen J targets; per-stream T2-type equivalence; joint Fréchet distance; A3 other-sentence null; BT and MPJPE as secondary checks.

## 6. Training architecture and parameter scope (route A only)

- **Frozen:** the body, hand and face U-Nets and M-CLIP (`requires_grad = False`, eval(), fp32). The checkpoint is never written.
- **Trainable:** only the controller h_φ(e(c), L). Input: the cached 640-d M-CLIP embedding plus a length feature.
  - **Output option 1, arm-structured (r = 12):** V is fixed (selection), so the outputs are U and κ per hand, ≈ 2.2k outputs; with a 2 × 256 MLP, ≈ 0.6M parameters.
  - **Output option 2, full (r = 60):** ≈ 18k outputs, ≈ 4.7M parameters.
- **Gradient path:** reward → 10 unrolled Euler steps (E2d harness, per-step checkpointing) → coupled hand noise → (U, V, κ) → φ. The body needs no gradient (z_b = ε_b).

## 7. Minimum baselines and evaluation (for any future controller)

**Baselines** (same clips, common noises, matched budget):
- N1, the base sampler;
- fixed random coupling at matched KL (E2e conditions);
- N3′, best-of-n×n pairing at a matched sample budget;
- N4, per-sample noise optimisation under C-c3 typicality (upper reference);
- E2c (ii) per-clip family optimum (upper bound for any amortised controller in the family);
- N5, the keyframe cascade (non-learned coupling);
- the A3 other-sentence null (chance satisfiability);
- for P1b work only, N9 side assignment.

**Primary metrics:**
- R coordination gap-closure toward the frozen R targets (held-out dev, clip bootstrap);
- J coordination vs the frozen J targets (independent space, never mixed);
- per-stream preservation (eight-mean TOST, exact by Theorem 3 for κ);
- exact KL;
- the undefined fraction (S-4).

**Secondary:** joint Fréchet distance, BT, frame-aligned MPJPE ("no regression detected" only).

Test data only at Stage 6, once, under explicit approval.

## 8. Compute and memory (measured vs estimated)

| Item | Value | Status |
|---|---|---|
| One K = 10 forward + backward, B = 8 contexts (body no grad + 16 hand sequences), checkpointing | **5.93 s, 8.80 GiB peak reserved** | **[V] E2d** |
| B = 4 | 3.77 s, 7.46 GiB | [V] E2d |
| No-grad generation, 32 clips × 2 hands | ≈ 5.1 s per call; ≈ 45 s per condition of 256 samples | [V] E2d/E2e |
| GPU / free | RTX A4000 16 GiB; ≈ 14.9 GiB free | [V] |
| Controller forward/backward and QR maps | negligible vs the U-Net | [E] |
| One training step, B = 8 | ≈ 6–7 s | [E] from E2d |
| 5,000 steps | ≈ 8–10 h | [E] |
| Dev evaluation per checkpoint (32 clips × 8 noises) | ≈ 1 min | [E] from E2e |
| GPU rental | not needed | [I] |

## 9. Risks, unresolved assumptions, acceptance criteria

| # | Risk / assumption | Status |
|---|---|---|
| 1 | No capacity evidence for learned coupling (U8) | **blocking for route A** |
| 2 | R targets under metric v1.1 not verified on train (S-5) | [U]; ≈ 15 min CPU check, needs approval |
| 3 | Small effect sizes: the best observed Δ is ≈ 0.04–0.06 against reference−base gaps of ≈ 0.43 (R right arm–hand: 0.451 vs ≈ 0.02) | strong prior against large gains [I] |
| 4 | Very large KL for small effects (≈ 11,000–14,600 nats per sample at κ = 0.9) | the efficiency CIs were uninformative |
| 5 | Chance satisfiability (A3 null): coordination is reachable with other-sentence hands | evaluation must report the A3 null |
| 6 | Surrogate (chordal) vs registered (geodesic) metric | S-7 |
| 7 | T2 calibration-inconclusive at n = 32 | per-stream preservation is theory-conditional |
| 8 | Pseudo-GT references; oracle length; possible test contamination (D10) | unchanged limitations |

**Acceptance criteria for any future training (to be pre-registered before it starts):**
- held-out dev R gap-closure ≥ 50% with the 95% CI excluding 0;
- the same sign in J;
- better than N3′ and better than fixed coupling at matched KL;
- per-stream preservation equivalence;
- undefined fraction within S-4;
- the A3 null reported.

## 10. Minimal sequential plan (each step needs your explicit approval; nothing started)

| Step | Content | Cost | Gate |
|---|---|---|---|
| 0 | Implement S-1, S-2, S-6 as a versioned validity layer (R v1.1); unit tests on synthetic arrays | ≈ 1 h of work, CPU | tests pass |
| 1 | S-5: verify R0 targets under v1.1 on the train references | ≈ 15 min CPU | 0 invalid streams, or separately versioned targets |
| 2 | **Decision point:** route A (E2c (ii) capacity check), B (new Stage 4 revision) or C (close with H0) | — | your decision |
| 3 (A only) | E2c (ii) as pre-registered (C-c1 to C-c6) | ≈ 40 min GPU | reaches the C-c2 level, otherwise H0 for the family |
| 4 (A only, if 3 is positive) | pre-register the Stage 5 objective (§5.4), acceptance (§9), baselines (§7); then a short training pilot (≈ 500 steps, ≈ 1 h) | ≈ 1 h GPU | pilot health: finite, KL bounded, constraints hold |
| 5 (A only) | full training (≈ 8–10 h) and dev evaluation; test only at Stage 6 | ≈ 10 h | §9 acceptance |

## Recommendation

**Stage 5 training is not scientifically justified at this point.**
- Within the frozen-base controller scope, P1a has accepted H0 for the tested design and P1b failed D-c.
- The only remaining candidate (learned coupling) lacks the necessary capacity evidence.
- Per-stream quality measures can only be constraints.

If you still want to move toward training, the defensible minimum is Steps 0–1 (safeguards; cheap) and then, at the Step 2 decision point, **route A's E2c (ii)** as the single necessary precondition. If you prefer not to run it, the scientifically consistent option is **route C**: report Stage 4 as a rigorous negative feasibility result.

## Closure addendum (2026-11-07, final project execution authorisation)

This report is historical; the addendum records how the project closed. Full details: `research/RESEARCH_LOG.md`, `research/final/`.

| Item | Outcome |
|---|---|
| ACMS multi-seed replication (seeds 7001–7004, update 125) | pooled Δ coord_ah^R +0.0022 [−0.0013, +0.0056] (t, 4 runs), I² 0.97, **seed-sensitive**; ≈ 1/23 of the 0.05 threshold; preservation passes in all runs |
| FG-1 V1 learned M-C (per clip) | held-out +0.0034 [−0.0121, +0.0166] → **negative** |
| FG-1 V2 per-clip ACMS | held-out +0.1016 [+0.0753, +0.1288], articulation ratio 1.102 > 1.10 → **inconclusive** (preservation fail) |
| FG-1 V3 bilateral SC-MC | R +0.0893 [+0.0703, +0.1091], L +0.1071, preservation passes → **positive** (per-clip, pathwise gradients, TRAIN clips) |
| OPT-G / OPT-C | monitoring only; all CIs include 0; no checkpoint selected |
| Test split | never opened |

**Readiness verdict at closure:** amortised noise-space RL on the frozen checkpoint is not ready for (and does not justify) further training under the registered objective; per-clip state-conditioned control is feasible on fresh noise. Any next step (amortising V3-style control, fine-tuning, architectural coupling) needs new pre-registration. The project is closed on this evidence.
