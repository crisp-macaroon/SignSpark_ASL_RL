# Appendix G: Gaussian noise controller, derivations (Stage 4, revision 4.0)

**Revision 4.0** (human verification removed from scope): **no derivation, theorem, assumption or proof changed.** The previous version is preserved at `research/archive/appendix_gaussian_controller_rev3.3.md`.
- §G.6.3: the reference to level D-d (perceptual dominance, human ratings) is removed. D-c is the highest dominance level.
- §G.6.1: a note on the measurement space was added after the activity functional. Theorem 4 holds for any one functional applied to both sides (T4-b), so it covers the rotation-space activity A^R. It also covers the SMPL-X joint-space activity A^J **provided** the left/right SMPL-X hand geometry is an exact mirror (report U-A11, unverified).
- "t*" in this appendix means the rotation-space train target t*^R (report §6.0).

**Revision 3.3:** no change to any derivation.
- The empirical evidence for assumptions F1–F6 is itemised in report §15.4.4. F4 (no batch coupling) is supported by code reading only.
- The report's dominance target is now split into t*₃₂ (estimated) and t*₂₅₆ (fixed margin constant), report §6.5 and §15.4.3. The appendix's t* refers to the train-reference target and is unaffected.

**Revision 3.2 change:** Theorem 4 statement (3) clarified.
- It holds as an extended-real expectation (S₃ ∈ [1, ∞]) under T4-a to T4-d.
- A finite S₃ needs the additional condition T4-e.
- S₃ is therefore descriptive only, and gating uses S₁/S₂.
- §G.6.3 "genuine dominance" is renamed to match report §6.5 level D-c.

**Revision 3.1 change:** §G.6.1 rewritten.
- Theorem 4 now has explicit assumptions T4-a to T4-d and states its result per dominance statistic S₁–S₄.
- It separates the mean-ratio results (proved) from probability-based dominance (not determined by marginals).
- The r_dom target is corrected to the reference mean log-ratio t* (not yet computed); −0.274 is now illustrative only.
- §G.6.3 is aligned with report §6.5 (dominance evaluation levels D-a to D-d).

**Status:** mathematical derivations. Nothing here has been run.

**Labels:**

| Label | Meaning |
|---|---|
| [D] | Derived here, with proof or derivation |
| [C] | Read from the upstream code |
| [H] | Hypothesis needing an experiment |
| [U] | Unresolved |

**Corrections in this integrated version** (relative to the first revision-3 draft):

| # | Change |
|---|---|
| G-c1 | **§G.7: the paired advantage.** In the pathwise estimator, subtracting the same-noise base reward **does not change the gradient at all**, so it is not a gradient variance-reduction device. In the REINFORCE fallback, using it as a baseline **biases** the estimator. It is retained only as a common-random-number (CRN) *estimator of improvement* for monitoring and evaluation. |
| G-c2 | **§G.5, F6: precision.** The baseline and controlled samplers must use the *same* numerical implementation. The earlier wording ("bf16 if close to fp32") is replaced. |
| G-c3 | **§G.1, §G.6: scope of M-C/σ.** The side-dependent component is scale-only by default. A mean shift μ is deferred (untested; separate approval needed). Both directions of the scale (left down, right up) are in scope. Genuine dominance is distinguished from left-hand suppression (§G.6.3). |
| G-c4 | **§G.9:** coupling ranks now match the E2e specification. |

---

## G.0 Setting and the facts used from the code

| # | Fact | Source |
|---|---|---|
| F1 | In GF, each stream's sampler is a deterministic map x_s = g_s(ε_s; c, L), s ∈ {b, L, R}. The keyframe mask is empty, so the noise enters unmodified. | [C] `rflow.py:216`, `sample.py:141–145` |
| F2 | g_L = g_R = g_h: one hand network, identical (c, L) inputs for both sides. | [C] `sample.py:125–136` |
| F3 | Base noise is `torch.randn_like`: i.i.d. N(0, 1) over every (stream, channel, frame) entry, including padded frames. | [C] `sample.py:145` |
| F4 | Per-sample normalisation (RMSNorm/GroupNorm) and within-sample temporal attention; no batch-coupling operation. So g_L does not depend on ε_R although both hands share a batch. | [C] `unet_model_large.py`, `utils/nn.py` |
| F5 | Text-condition dropout is active only in `train()` mode, so every use of g must be in **`eval()`** or F1 fails. | [C] `unet_model.py:122–133` |
| F6 | "Same g" means the same code path, dtype, device flags (TF32 on/off, cuDNN determinism) and step grid. **Baseline and controlled samples must be produced by one implementation with identical settings.** A different precision is a different map g′. | [D, definitional] |

**Dimensions per frame τ:**
- n_b = 60, n_h = 90, n = 240.
- Active frames τ = 1..L. Padded frames τ > L keep the base noise.

**Notation:** ε(τ) = (ε_b(τ), ε_L(τ), ε_R(τ)) ~ N(0, I₂₄₀), i.i.d. over τ.

## G.1 The controller (default M-C family)

All parameters come from h_φ(e(c), L): **context only, never the noise.**

**Coupling block (marginal-preserving, M-C/κ):**

  z_b = ε_b
  z_L = K_L ε_b + S_L ε_L,                 K_L ∈ ℝ^{90×60},  S_L = (I − K_L K_Lᵀ)^{1/2}
  z_R = K_Rb ε_b + K_RL ε_L + S_R ε_R,     K_R = [K_Rb, K_RL] ∈ ℝ^{90×150},  S_R = (I − K_R K_Rᵀ)^{1/2}

**Side-marginal block (M-C/σ, default scale-only):**

  ε̃ = D z,  D = diag(1₆₀, σ_L, σ_R),  σ_s ∈ [σ_min, σ_max] ⊂ (0, ∞)

A mean shift μ = (0, μ_L, μ_R) is part of the general family (formulas below include it) but is **not** in the default component (G-c3).

**Matrix form:** z = Aε, with

  A = [ I₆₀    0     0  ]
      [ K_L    S_L   0  ]
      [ K_Rb   K_RL  S_R ]

and ε̃ = μ + D A ε.

**Sub-families:**
- **M-C/κ:** σ = 1, μ = 0.
- **M-C/σ:** K = 0.
- **M-C/κσ:** both (only after each has been evaluated alone).

## G.2 Joint distribution and covariance

**[D]** ε̃(τ) ~ N(μ, Σ̃) with Σ̃ = DΣD and Σ = AAᵀ, independent over τ.

| Block of Σ | Expression | Value |
|---|---|---|
| Σ_bb | I | I₆₀ |
| Σ_Lb | K_L | K_L |
| Σ_Rb | K_Rb | K_Rb |
| Σ_LL | K_LK_Lᵀ + S_L² | **I₉₀** |
| Σ_RL | K_Rb K_Lᵀ + K_RL S_L | K_Rb K_Lᵀ + K_RL S_L |
| Σ_RR | K_RK_Rᵀ + S_R² | **I₉₀** |

The upper blocks are the transposes.

**After side scaling:**
- Σ̃_sb = diag(σ_s)Σ_sb;
- Σ̃_ss = diag(σ_s²);
- Σ̃_RL = diag(σ_R)Σ_RL diag(σ_L).

**Induced L–R dependence:** Σ_RL = K_Rb K_Lᵀ ≠ 0 whenever both hands couple to the body, even with K_RL = 0.

## G.3 Positive-definiteness and parameterisation

**Lemma 1 [D].** If ‖K‖₂ < 1, then I − KKᵀ ≻ 0, and S = (I − KKᵀ)^{1/2} exists, is symmetric positive-definite and is nonsingular.
- *Proof:* the eigenvalues are 1 − κ_i² > 0, and 1 on the complement of range(K). ∎

**Lemma 2 [D].** If ‖K_L‖₂ < 1 and ‖K_R‖₂ < 1, then A is nonsingular, Σ ≻ 0 and det A = det S_L · det S_R. With σ > 0, Σ̃ ≻ 0.
- *Proof:* A is block lower-triangular with nonsingular diagonal blocks, and D is nonsingular. ∎

**Parameterisation (guarantees the lemmas):**
- For K ∈ ℝ^{90×p}, p ∈ {60, 150}, and rank r ≤ min(90, p):

  K = U diag(κ) Vᵀ,  U ∈ St(90, r),  V ∈ St(p, r),  κ_i = κ_max·sigmoid(a_i),  κ_max = 0.95

- U and V come from a differentiable QR map of unconstrained matrices, with the sign of diag(R) fixed.
- **Closed-form square root:** S = I − U diag(1 − √(1 − κ²)) Uᵀ, and log det S = ½ Σ_i log(1 − κ_i²).
- **The right hand must be parameterised as one 90×150 matrix.** Separate norm bounds on K_Rb and K_RL do not bound ‖K_R‖₂.
- **Conditioning:**
  - single body→hand block: eigenvalues 1 ± κ_i, so the condition number is ≤ (1 + κ_max)/(1 − κ_max) ≈ 39;
  - three-block case: no closed-form bound [U]; the smallest eigenvalue of Σ is logged numerically.
- **Scales:** σ = exp(clip(b, log σ_min, log σ_max)).

**Roles of the parameters** (used in the E2e design):

| Parameter | Meaning |
|---|---|
| **U** (90 × r, hand side) | which r directions of a hand's 90-channel noise receive coupled input |
| **V** (p × r, source side) | which r directions of the source noise (body 60, or body + left 150) are copied in |
| **r** | how many independent channel directions are coupled; KL cost grows linearly in r |
| **κ_i** | the correlation strength in direction i: Corr(⟨u_i, z_s⟩, ⟨v_i, source⟩) = κ_i |
| **Random seed** of (U, V) | fixes one orientation. Because the networks' first layers mix channels in unknown ways, a random orientation is agnostic but arbitrary: different seeds can transmit differently through g |

## G.4 Exact KL divergence

**Theorem 1 [D].** Per frame, by the standard Gaussian KL with diag(Σ) = 1:

  KL_frame = [−log det S_L − log det S_R] + ½ Σ_{i∈hands}(σ_i² − 1 − log σ_i²) + ½‖μ‖²
           = KL_coupling + KL_scale + KL_mean

with KL_coupling = −½Σ_i log(1 − κ_{L,i}²) − ½Σ_i log(1 − κ_{R,i}²).

- **Total:** KL(q(·|c, L) ‖ p₀) = Σ_{τ≤L} KL_frame = L·KL_frame for frame-shared parameters.
- **Policy penalty:** E_{(c,L)}[·].
- **Exact iff:** the parameters are ε-independent; ‖K‖₂ < 1; σ > 0; the base noise is i.i.d. N(0, 1) (F3).
- **Each term is ≥ 0 and zero only at the identity.**
- **Costs per coupled direction:** 0.047 / 0.223 / 0.830 / 1.164 nats at κ = 0.3 / 0.6 / 0.9 / 0.95.
- **Cost of a scalar σ applied to all 90 channels:** 90·½(σ² − 1 − log σ²) per frame. That is 0.93 nats per frame at σ = 0.9, 2.14 at 0.85, 6.20 at 0.75, 17.2 at 0.6, 1.93 at 1.15 and 5.23 at 1.25 (arithmetic checked numerically).
- **Comparison:** coupling all 60 body directions at κ = 0.9 costs 49.8 nats per frame per hand. Per *direction*, a scale change is cheap, but it acts on all 90 channels at once.

## G.5 Marginal preservation: noise level and generated-motion level

**Theorem 2 [D]: noise marginals under M-C/κ.**
- For every (c, L): ε̃_b, ε̃_L, ε̃_R are each exactly N(0, I) over all 304 frames.
- *Proof:* active frames are linear Gaussian maps with mean 0 and per-frame covariance equal to a diagonal block of Σ = I, independent over τ. Padded frames are untouched base noise, independent of the active frames. ∎

**Theorem 3 [D]: generated-stream marginals under M-C/κ.**
- law(x_s | c, L) = g_s # N(0, I) = the base law.
- *Proof:* by F1 and F4, x_s depends on the noise only through ε̃_s, and by F6 it is the same g_s. ∎
- **Conditions:** F5 (eval) and F6 (identical implementation and precision for base and controlled runs); padded frames untouched; ε-independent parameters.
- **Corollary [D]:** the body stream is not just equal in law but **sample-wise identical** to the base for the same ε⁰ (z_b = ε_b).

**Guaranteed:**
- exact per-stream noise and output laws (hence per-stream statistics equal *in expectation*);
- an exact KL;
- KL(output joint ‖ base output joint) ≤ KL_coupling (data processing).

**Not guaranteed:**
1. output timing coupling [H];
2. sample-wise invariance for the hands;
3. finite-sample equality (hence the equivalence tests in report §15);
4. perceptual or semantic quality of the joint;
5. any dominance effect (§G.6);
6. robustness to implementation deviation (F5/F6 violations).

## G.6 Coordination versus dominance

Let A_s = Σ_τ mean_j ω_{s,j}(τ) > 0 (total angular speed of hand s), with E|log A_s| < ∞.

### G.6.1 Dominance statistics under equal hand marginals (rev. 3.1: assumptions and statistics made explicit)

**Activity functional.** A_s = Σ_τ mean_j ω_{s,j}(τ): the total over active frames of the mean finger-joint angular speed of hand s, computed **by the same function for both sides** (as in the A4 analysis).

**Measurement-space note (rev. 4.0; no change to the theorem).**
- The A_s above is the rotation-space activity A^R.
- Theorem 4 uses only T4-b (one measurable functional a applied to both sides), so it applies verbatim to any other activity functional with that property.
- For the SMPL-X joint-space activity A^J (report §6.0), the left hand is mapped by flip-conjugation F R F (F = diag(1, −1, −1)) and posed on the left-hand kinematic chain. A^J_L = a(x_L) and A^J_R = a(x_R) use the same a **if and only if** the left-hand rest geometry is the exact mirror of the right-hand geometry: F R F = M R M with M = diag(−1, 1, 1), so mirrored positions have equal speed norms.
- That symmetry is not verified [U] (report U-A11). If it fails, dom^J can deviate from 0 under equal marginals by a model-geometry bias, and Theorem 4 applies to A^R only.

**Assumptions of Theorem 4:**

| # | Assumption | When it holds |
|---|---|---|
| T4-a | **Equal marginals:** for a given context (c, L), x_L and x_R have the same law | base (F2 + i.i.d. noise); M-C/κ (Thm 3 + F2), under F5/F6; **not** M-C/σ with σ_L ≠ σ_R |
| T4-b | **Same functional:** A_L = a(x_L) and A_R = a(x_R) for one measurable a | by construction |
| T4-c | **Positivity:** A_s > 0 almost surely | any non-static motion; violated only by an exactly frozen hand |
| T4-d | **Integrability:** E[A_s] < ∞ for (1); E\|log A_s\| < ∞ for (2)–(4) | bounded speeds over ≤ 304 frames ⇒ E[A_s] < ∞ [I]; the log moment is assumed (it fails only if A_s has mass arbitrarily near 0) |
| T4-e (rev. 3.2) | **For a finite S₃:** E[A_L/A_R] < ∞. A sufficient condition: A_R ≥ a > 0 almost surely (the hand is never exactly frozen) together with E[A_L] < ∞ | **not guaranteed** [U]; nothing prevents A_R from being arbitrarily small in principle. See the note under (3) |

What T4 does **not** assume:
- independence of x_L and x_R;
- exchangeability (needed only for the probability statement in Prop 1, not here);
- any property of g_h beyond T4-a.

**Theorem 4 [D].** Under T4-a to T4-d, for each context (c, L), and hence also after averaging over contexts (a mixture of equal laws is equal):

| # | Statistic | Definition | Result | Unattainable targets |
|---|---|---|---|---|
| (1) | **Ratio of means** | S₁ = E[A_L] / E[A_R] | **= 1 exactly** (equal laws ⇒ equal means) | **any target ≠ 1** |
| (2) | **Geometric-mean ratio** | S₂ = exp E[log(A_L/A_R)] | **= 1 exactly** (E log A_L = E log A_R) | **any target ≠ 1**, including the reference geometric ratio if it is ≠ 1 |
| (3) | **Mean of per-sample ratios** | S₃ = E[A_L/A_R] | **≥ 1** (Jensen: E e^X ≥ e^{E X} with E X = 0) | **any target < 1**, including the dev-256 reference value 0.76 (mean of per-clip ratios, A4) and the Stage 3 test value 0.70 |
| (4) | **Log-ratio reward** | E[r_dom], r_dom = −\|log(A_L/A_R) − t\| | **≤ −\|t\|** (E\|X − t\| ≥ \|E X − t\|) | any value above −\|t\| |

**Note on (3): extended expectation (rev. 3.2).**
- e^X is non-negative, so E[A_L/A_R] = E[e^X] is always well defined in [0, ∞]. With E[X] = 0 and E|X| < ∞ (T4-d), Jensen's inequality gives E[e^X] ≥ e^0 = 1 in the **extended reals**.
- **Statement (3) therefore holds under T4-a to T4-d alone, with S₃ possibly = +∞.**
- If T4-e also holds, S₃ is finite and ≥ 1. Finiteness matters for *estimation*: a sample mean of per-sample ratios and its bootstrap CI are meaningful only when S₃ < ∞ (and in practice, when the ratio has a finite variance).
- **Consequence for the design:**
  - S₃ is reported only descriptively.
  - All gating and evaluation statistics use the log-ratio (S₂, needing only T4-d) or the ratio of means (S₁, needing only E[A_s] < ∞).
  - Neither depends on T4-e.

**On the target t for r_dom (rev. 3.1 correction):**
- r_dom is a log-scale statistic, so its target is t* = the **reference mean of log(A_L/A_R)**: the log of the reference geometric ratio, computed on How2Sign *train* references.
- That number has **not been computed yet** [U]. Earlier drafts used log 0.76, which is the log of an *arithmetic* mean ratio (S₃), a mismatch.
- **−0.274 = −|log 0.76| is illustrative only.**

**Not covered by Theorem 4: probability-based dominance.**
- S₄ = P(A_R > A_L) is **not determined by the marginals**.
  - Under **exchangeability** (base, Prop 1; M-C/κ with a coupling whose law is symmetric in L and R), S₄ = ½.
  - Under asymmetric coupling, (x_L, x_R) can have equal marginals without being exchangeable, so S₄ ≠ ½ is **not excluded**.

**Proposition 5 [D].** Let X = log(A_L/A_R). Under T4, E[X] = 0. If S₄ = p, then:

  E[X | X > 0] · (1 − p) = E[−X | X < 0] · p   (assuming P(X = 0) = 0)

- So the mean magnitude of the "reversals" (left more active) must be p/(1 − p) times that of the majority.
- For p = 0.94 this factor is 15.7: a heavy-tailed, reference-unlike pattern.
- **Hence the joint reference profile is unattainable under T4:** S₄ ≈ 0.94 *together with* S₃ ≤ 0.76 (or S₂ = the reference geometric ratio < 1).
- **S₄ alone is not proven unattainable [U].** It is not a design goal, because any gain in S₄ under equal marginals comes with S₁ = S₂ = 1 and S₃ ≥ 1, i.e. no mean dominance.

**Population vs finite sample.** Theorem 4 concerns expectations. Finite-sample estimates fluctuate around them; that is what E2e T5-A tests, with tolerances.

**Consistency check:** the base's measured mean of per-clip ratios is 1.08 ≥ 1 [V], consistent with (3).

### G.6.2 How side-dependent scale and mean could act on activity [H]

| Mechanism | Hypothesis | Basis | Status |
|---|---|---|---|
| σ_s < 1 (noise contraction) | lowers hand s's activity monotonically. Contracting the noise toward the origin is the "temperature" reduction commonly used to trade diversity for typicality in flow/diffusion samplers; at small σ the output tends toward a less varied, more average motion | [I] general practice; **not established for SignSparK** | [H], E2e T5-B |
| σ_s > 1 (noise expansion) | raises hand s's activity; risks atypical noise (‖ε̃‖²/d > 1) and artefacts | [I] | [H], E2e T5-B |
| μ_s ≠ 0 (mean shift) | the effect direction is unknown: it depends on how g_h maps a constant offset, possibly a static pose bias rather than activity | none | **deferred** (not in E2e; separate approval) |

Because the base hand model is trained on both hands (the left mirrored into the right convention, Stage 2 D7), its marginal is plausibly a *mixture* of dominant and non-dominant behaviour [I]. So reaching level D-c plausibly needs **both** the right hand to move up and the left hand to move down relative to the base, which motivates testing σ_R > 1 as well as σ_L < 1.

### G.6.3 Target-directed dominance (D-c) vs left-hand suppression [D: definitions; thresholds are proposals]

**Per-clip side calibration** (dev references only; never used at inference):

  c_s = median over samples of log(A_s^gen / A_s^ref), s ∈ {L, R}

where A_s^ref is the reference activity of side s for the same clip. Normalising by the clip's own reference controls for content and length. It is a distribution-level comparison, not a per-sample target, because text→sign is one-to-many.

| Outcome | Signature |
|---|---|
| **Target-directed dominance without detected left-hand degradation** (report §6.5 level D-c; renamed in rev. 3.2 from "genuine dominance") | the mean log(A_L/A_R) moves toward **and** substantially closer to the reference mean log-ratio of the same clips (D-a and D-b), **and** neither hand's side-calibration error increases, **and** the specified left-hand checks detect no degradation. **Thresholds and aggregation: report §6.5. It is not a perceptual claim.** Rev. 4.0: perceptual dominance (former level D-d) is out of scope |
| **Left-hand suppression** | the ratio improves **but** c_L falls below the reference (c_L < log 0.8), **or** left-hand quality degrades: jerk up, a less natural pose distribution, or L–R coordination down |

**Left-hand quality protection.** Constraints in training; the same quantities are non-inferiority checks in evaluation.
- (i) **Activity floor:** c_L ≥ log 0.8 (batch level; the left hand is not pushed below 80% of its reference activity).
- (ii) **Jerk:** ≤ base × 1.10.
- (iii) **Extreme speed:** the fraction of frames with speed > 45°/frame is not up by more than 2 percentage points.
- (iv) **Pose distribution:** the Fréchet distance between generated left-hand pose features and *reference left-hand* features is not increased.
- (v) **L–R coordination:** not reduced.
- (vi) **Bounds:** σ_L ≥ 0.5, plus the KL_scale cost.
- The floor uses train references at training time (a distribution-level constraint), consistent with keeping rewards reference-free per sample [Pr].

## G.7 Optimisation and the paired (common-random-number) quantity

**Pathwise objective.** J(φ) = E_{(c,L)} E_{ε⁰}[r(G(T_φ ε⁰))] − α_κ KL_coupling − α_σ KL_scale, with T_φ ε⁰ = μ_φ + D_φ A_φ ε⁰.

The gradient is ∇_φ J = E[ (∂T_φε⁰/∂φ)ᵀ J_G(T_φε⁰)ᵀ ∇_x r ] − ∇_φ KL. This is unbiased by reparameterisation, with an exact KL gradient.

**Paired quantity** [D, correcting G-c1]. Define Δ(ε⁰) = r(G(T_φ ε⁰)) − r(G(ε⁰)).

1. **Pathwise gradient:** ∇_φ Δ = ∇_φ r(G(T_φ ε⁰)), because r(G(ε⁰)) does not depend on φ. **Subtracting it changes nothing in the gradient.** It is not a gradient variance-reduction device here, and computing it every step only costs time.

2. **Improvement estimation (monitoring and evaluation):**
   - Δ is a common-random-number (CRN) estimator of the improvement E[r(G(T_φε⁰))] − E[r(G(ε⁰))]. Both terms use the same ε⁰.
   - Var(Δ) = Var(r_ctrl) + Var(r_base) − 2·Cov(r_ctrl, r_base), which is smaller than the unpaired variance when Cov > 0.
   - At the identity Cov = Var, so Δ ≡ 0. As T_φ departs from the identity the correlation decays, and so does the benefit.
   - **G(T_φε⁰) and G(ε⁰) are different samples** (except the body under M-C/κ, by the Corollary to Thm 3). Δ measures a difference in distributions estimated with correlated draws. It is **not** "the same motion, improved".

3. **REINFORCE fallback (score function):**
   - The action is ε̃ = T_φε⁰. A baseline b must satisfy E[∇_φ log q_φ(ε̃)·b] = 0, which holds if b does not depend on ε̃ given the context.
   - b = r(G(ε⁰)) = r(G(T_φ⁻¹ε̃)) **depends on ε̃, so it biases the estimator in general.**
   - **Use instead:** a leave-one-out group mean over independent draws for the same context (RLOO/GRPO-style), or a context-only learned baseline.

**Restricted family.** Maximising J over {q_φ} = minimising KL(q_φ ‖ q*) (reverse KL, mode-seeking). q* itself is generally non-Gaussian, so the gap is [U].

## G.8 The residual (Noise Hypernetworks) form: non-default alternative

T = id + f_φ(ε, e(c), L, side).

- **Exact KL:** E½‖f‖² + E[tr J_f − log det(I + J_f)], valid if Lip(f) < 1 and Stein's lemma applies (matches NH Eq. 8).
- ½‖f‖² is exact only for ε-independent f. Otherwise the omitted term is ≥ 0 (for real Jacobian eigenvalues in (−1, 1)).
- There is no marginal guarantee and no closed form.
- **It is not adopted automatically under any outcome.** If E2e fails, the residual form is one of several options presented for your decision (report §15.2).

## G.9 Unresolved items

| # | Item | Route |
|---|---|---|
| U1 | Does frame-local linear coupling transmit to output timing? With random orientation, and with a hypothesis-driven arm-channel orientation? | [H] → E2e T3/T4 |
| U2 | Does σ_s move hand activity monotonically, and does it do so without suppression signatures? | [H] → E2e T5-B/T6-B |
| U3 | The size of the reverse-KL gap to q* | [U]; E2c gives an empirical reference |
| U4 | Should P(A_R > A_L) move under equal marginals? | [U]; not a goal |
| U5 | σ bounds; whether μ is worth testing | [U]; after E2e; μ needs approval |
| U6 | Frame-shared vs frame-varying parameters | [U]; frame-shared by default |
| U7 | Coupling rank | [U]. E2e uses r = 60 (full body rank) and r = 12 (arm-channel structured) for body→hand, and r = 90 for direct L–R |
| U8 | Whether a learned U, V can find coupling that random ones miss, and vice versa | [U]. E2e cannot answer this (report §15.2.3) |
| U9 | Three-block condition-number bound | [U]; numerical logging |
