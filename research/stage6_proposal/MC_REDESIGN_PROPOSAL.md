# M-C: failure analysis and redesign proposal (PROPOSAL, not approved, nothing run)

*2026-11-06. Released-checkpoint results, not a paper reproduction. Motion statistics only.*

**Labels:** [V] measured in an existing artifact · [D] mathematical implication · [H] hypothesis (not tested) · [N] new research direction requiring separate approval.

**Recommendation in one paragraph:**
- **Do not train an amortised M-C controller.** No M-C variant has shown fresh-noise headroom.
- The only defensible next M-C-related step is a **bounded per-clip feasibility gate** (§5). It asks whether *any* noise-space controller in three specified families can change held-out coordination by the registered 0.05 on fresh noise.
- One of those families, state-conditioned bilateral M-C (SC-MC, §4), is a **new research direction [N]** and needs its own approval.
- If the gate is negative, the evidence supports closing the M-C line under its registered scope (route C). It would **not** support a claim that RL or all controllers cannot improve SignSparK.

---

## 1. Evidence base (existing artifacts only)

| Experiment | Controller | Clips / noise | Held-out right arm–hand Δ vs uncoupled (R) | KL | Verdict |
|---|---|---|---|---|---|
| **E2e** T3 (`E2E_REPORT.md` §3.6) | Fixed random-orientation BH coupling z_R = Kε_body + Sε_R, r = 60, κ = 0.3 / 0.6 / 0.9 | dev 0–31 × 8 | κ 0.9: seed 0 **+0.017 [−0.014, 0.049]**, seed 1 +0.033 [0.006, 0.061], seed 2 +0.037 [0.013, 0.062] | 14,629 nats/sample (99.64/frame) | **FAIL** (FM13; ≥ 0.05 not reached on either side) [V] |
| **E2e** T4 | Fixed LR coupling, r = 90 | same | L–R: κ 0.9 seed 0 +0.035 [0.006, 0.066] | 10,972 nats/sample | **FAIL** [V] |
| **E2e** T5-B | Side scales (σ_L, σ_R) | same | dominance moved toward the target 4/4 (D-a); never closer by half (D-b 0/4) | 0.93–6.20/frame (exact, `mc_reward_e2e.json`) | D-c 0/4; left-hand suppression signatures (left jerk ratio 0.50–0.78) [V] |
| **E2c (ii)** (`E2C_II_REPORT.md`) | BH family with **learned** per-clip U, V, κ (~9,060 parameters/clip); Adam lr 0.05, 30 iterations; fit on 4 noises | dev 0–31; fit k 1–4, held-out k 5–8 | **−0.003 [−0.017, +0.012]**; in-sample best 0.737 vs held-out 0.034; gap **0.704 [0.650, 0.759]** | 1.19–2.71/frame (bound 49.82 never binding) | **NEGATIVE** (C-c6) [V] |
| E2e-J (`E2EJ_REPORT.md`) | as E2e, J space | same | T3 R 0.021, L 0.035; T4 0.036; seed 2 J R 0.058 (descriptive exception) | — | no effect on FM13 [V] |
| **Stage 5 ACMS** (`STAGE5_500EP_REPORT.md`) | Mean shift μ_φ(ŝ) on ε_R, conditioned on the **generated** right-arm speed; 433 parameters, amortised; REINFORCE + RLOO, 500 episodes | 125 train × 4 / dev-256 × 4 | **+0.0022 [0.0014, 0.0031]** | 0.0037/frame | positive by rule, negligible (0.5% gap closure) [V] |
| M-C reward on E2e dumps (`experiments/mc_reward/out/`) | registered §6.1 reward, fixed transforms | dev 0–31 × 8 | largest Δr_coord +0.075 (BH κ 0.9 seed 0); largest Δr_dom +0.21 (SS 1.0/1.15); SS 0.75/1.0 violates calib_L in 100% of episodes | as E2e | descriptive [V] |

Context:
- The registered 0.05 transmission threshold is from Stage 4.
- The C-c2 benchmark (best-of-8×8, 0.446) is a *selection* level, not a deployable mean (E2c (ii) §4.5).
- The uncoupled held-out level is ≈ 0.02–0.04, and the frozen target τ_ah_R is 0.4514.

## 2. Failure analysis

### 2.1 Why fixed-orientation Gaussian coupling transmitted too little (E2e)

1. **[D] The coupling acts in noise space, but coordination is defined in output space.**
   - K maps ε_body linearly into ε_R. Arm timing is a function of ε_body, x_b = G_body(ε_body, c), through a 10-step non-linear flow; hand timing is likewise G_hand(ε_R, c).
   - Linear correlation between the two *inputs* transfers to output timing only to the extent that both maps are locally linear and share a temporal frame.
   - Nothing in the construction guarantees that.
2. **[V] Transmission depended strongly on orientation.**
   - At the same κ and KL, the right-side Δ was 0.017 (seed 0), 0.033 (seed 1) and 0.037 (seed 2). Most random r = 60 subspaces of the 60-dim body noise carry little timing-relevant signal.
   - The effect was monotone in κ, but the largest κ (0.9, about 100 nats/frame) still gave < 0.05.
3. **[V] It was frame-local.** Both K and S act per frame (`noise_transform.py`). Any lag between arm motion and hand motion in the output (the reference statistics allow lag) cannot be represented.
4. **[V] Preservation held (T1, T2, T5-A), so failure is not "the transform broke the samples".** The transform was valid; it just did not move the target statistic enough.

### 2.2 Why per-clip optimisation overfitted (E2c (ii))

1. **[V] Few noises, many parameters.** With 4 fitting noises and ~9,060 parameters per clip, in-sample coordination rose from 0.052 to 0.737 and was still rising at iteration 30, while held-out stayed at the uncoupled level.
   - Spearman ρ(held-out, uncoupled) = 0.87: held-out ≈ the clip's uncoupled value.
   - ρ(gap, L) = −0.73: shorter clips overfit more.
2. **[D] The objective is realisation-specific.**
   - For a fixed ε_body, a hand-noise direction that aligns hand speed peaks with that realisation's arm peaks need not align them for another ε_body.
   - The arm-speed profile changes with ε_body, and K is the same for all draws.
   - With 4 draws, the optimiser can fit the 4 realisations rather than a draw-invariant rule.
3. **[V] KL was not the binding constraint:** 2.27 nats/frame mean, against a bound of 49.82, and no κ at the clamp.

### 2.3 Attribution: which limitation?

| Candidate | Evidence for | Evidence against | Status |
|---|---|---|---|
| **Output controllability per realisation** (can noise move coordination at all, for a given draw?) | E2c (ii) in-sample 0.737 (from 0.052) [V] | — | **Supported: yes**, for fixed draws |
| **Transferable (fresh-noise) controllability** | ACMS +0.0022 [V]; E2e BH seeds 1–2 +0.03 [V] | E2c (ii) −0.003 [V]; all < 0.05 [V] | **Open.** Only small transferable effects have been measured; the ceiling is unknown |
| **State representation** (M-C conditions on ε_body, a latent cause; ACMS conditions on the generated x_b, the realised arm motion) | ACMS is held-out positive with ~4 orders of magnitude less KL than E2e [V] | Confounded: different action class (mean vs covariance), clip set, budget, optimiser [V] | **Hypothesis [H1]**, plausible |
| **Action parameterisation** (frame-local covariance coupling vs temporal mean shift; per-frame vs sequence) | E2e frame-locality (§2.1.3) [D]; ACMS's 17-tap kernel can encode lag | Not isolated by any experiment | **Hypothesis [H2]** |
| **Controller capacity** | — | E2c (ii) had ~9k parameters/clip and overfit, so capacity was not short in-sample [V]. ACMS used ≈ 0.4% of its KL budget [V] | **Not supported** as the M-C failure cause.<br>For ACMS, "capacity unused" is an optimisation question |
| **Optimisation** | E2c (ii) still rising in-sample [V]; ACMS no visible training-reward trend, λ never active [V] | E2c (ii)'s failure is generalisation, not optimisation [V] | M-C: **not the cause**.<br>ACMS: **hypothesis [H3]**, low-powered (125 updates) |
| **Reward / statistic validity** | Coordination is chance-satisfiable (A3: best-of-8×8 0.408, other-sentence null 0.452) [V], so a high value need not mean correct ASL timing | The reward measures what was registered; the failure is not reaching it | **Limits interpretation**, not the cause of non-transmission [I] |
| **Sampler smoothing** (10-step flow contracts noise differences into similar timing) | Held-out ≈ uncoupled (ρ 0.87) [V] | In-sample controllability [V] | **Hypothesis [H4]**; testable only via the gate |

**Supported conclusions:**
- Under the registered fixed orientations (E2e), and under per-clip learned orientations fitted on 4 noises (E2c (ii)), the M-C Gaussian coupling family produced **no held-out gain ≥ 0.05**, and per-clip learning produced **no detectable** held-out gain.

**Hypotheses only:**
- H1–H4 above.
- Whether more fitting noises would yield a transferable coupling (E2c (ii) limitation 1).
- Whether any noise-space controller can reach 0.05.

**Not claimed:**
- that RL, or any controller, cannot improve SignSparK;
- that M-C with a different state, action or noise budget would fail.

## 3. Controls actually exposed by SignSparK in this harness

The generation call is `common5.Ctx5.gen → unrolled_sampler.unrolled_decode(model, noise, c, e, n_steps=10)`.

| Control | Shape | Used as action so far? | Changing it would be |
|---|---|---|---|
| Initial noise, body stream | 60 × 304 | E2e: input to K only; never modified (z_b = ε_b) | — |
| Initial noise, left / right hand streams (separate rows) | 90 × 304 each | **Yes**: E2e, E2c, ACMS (right only) | — |
| Text embedding e, conditioning c | fixed per clip | no | **[N]** new control mechanism |
| Length L | oracle | no | [N] |
| Number of Euler steps | 10 (fixed) | no | [N]; it would also change the base distribution being preserved |
| Per-step noise or velocity edits | — | no | **[N] per-step actions** |
| Model weights | frozen | never | **forbidden** (weight-space fine-tuning) |

**Everything below acts only on the initial hand noise**, as M-C and ACMS do. That is the only action space licensed by existing approvals.

## 4. Candidate redesign: state-conditioned bilateral M-C (SC-MC) — [N], requires separate approval

**Why it is M-C-derived:**
- It keeps M-C's objective structure (both arm–hand terms and L–R), its exact-KL preservation and its initial-noise action space.
- It replaces M-C's fixed linear map from ε_body with ACMS's conditioning on the *generated* body motion. That conditioning is the only conditioning with any held-out positive evidence, but the evidence is confounded (H1).

**Why it is still new [N]:**
- the action now covers both hands;
- the state now includes the left arm;
- the objective is the coordination sum, not r_ah(R) alone.

Each of these is an architecture and objective change relative to approved ACMS.

### 4.1 Formal definition (one-step contextual bandit, like ACMS)

| Element | Definition |
|---|---|
| Context | clip c (text, conditioning, L), fixed |
| Pre-state | ε_b ~ N(0, I₆₀ₓ₃₀₄); x_b = G_body(ε_b, c) (frozen, no grad) |
| **State** s | ŝ_R, ŝ_L ∈ ℝ^L: z-scored right- and left-arm geodesic speed profiles of x_b. Right arm: `common5.arm_feature`; left arm: the same, using `arm_signals(...)[1]` |
| **Action** a | (ε_L, ε_R), with ε_h = μ_φh(ŝ_h) + ξ_h and ξ_h ~ N(0, I₉₀) per frame, h ∈ {L, R} |
| Controller | μ_φh(ŝ)[:, t] = β_h · U_h · tanh((W_h ∗ ŝ_h)(t) + c_h)<br>U_h 90 × 4 Stiefel; W_h 4 × 17; β_h = √(2/r) · sigmoid(b_h)<br>i.e. two independent ACMS heads, each driven by its own arm |
| **Trainable parameters** | 2 × 433 = **866**.<br>Optional scale variant SC-MC-σ: + 2 (log σ_L, log σ_R, bounded to [log 0.9, log 1.1]); **excluded from the gate** (§4.4) |
| **Transition** | x_L = G_hand(ε_L, c), x_R = G_hand(ε_R, c) (frozen, 10 Euler steps); terminal |
| **Reward** (intended statistic) | registered M-C r_coord = r_ah(L) + r_ah(R) + r_lr (target matching, frozen R targets, `mc_reward.py`)<br>r_dom only in the σ variant |
| **Preservation (KL)** | exact KL per active frame = ½ Σ_h ‖μ_h,t‖² < 1 nat/frame per hand, by construction (as ACMS) |
| **Motion constraints** | registered M-C coord-mode set: art_L, art_R, jerk_L, jerk_R (`mc_reward.CONSTRAINTS["coord"]`) via dual ascent; plus Stage 5's six preservation checks applied to **both** hands at evaluation |
| **Optimisation (if amortised training is ever approved)** | REINFORCE + RLOO over the joint Gaussian (exact log-prob is a sum over hands), as Stage 5 |
| **Optimisation (gate, per-clip)** | pathwise gradients through the frozen unrolled sampler (E2c (ii) machinery: checkpointing, chordal-speed surrogate); Adam |

### 4.2 Expected failure modes

1. **Small effect, as in ACMS:** smooth, low-rank mean shifts may barely move output timing (H4). This is the most likely outcome given Stage 5 [I].
2. **Per-clip overfitting**, as in E2c (ii), if the fitting noises are too few. The gate uses 4× the E2c (ii) count, but overfitting may persist.
3. **Surrogate–metric mismatch:** chordal-speed surrogate vs registered geodesic metric. E2c (ii) tracked it to ≤ 6e-4 for the right side; the left side and L–R are untested.
4. **Left-hand activity drift.** M-C SS showed suppression when left activity changed. The c_left constraints exist only in σ mode, so the gate monitors left activity and the preservation checks on both hands.
5. **L–R term coupled only indirectly:** each head sees only its own arm, so r_lr can move only through arm–arm correlation in x_b.
6. **Short clips dominating per-clip gains** (E2c (ii) ρ = −0.73 with L).

### 4.3 Computational feasibility [D, from measured E2c (ii) cost]

- E2c (ii) cost ≈ 1,510 s for 32 clips × 4 noises × 30 iterations, i.e. ≈ **0.39 s per context-iteration** (B = 8, pathwise, checkpointed), with a peak of 8.53 GiB.
- SC-MC per-clip fitting doubles the hand rows per context (left and right), so ≈ 0.6–0.8 s per context-iteration [H: unmeasured]. Memory should be ≤ 14 GiB at B = 8 [H; measured first in the preflight].

### 4.4 Why the σ (dominance) variant is excluded from the gate

- E2e T5-B [V]: scales move dominance but never got it closer to target by half (D-b 0/4), and they produced left-hand suppression signatures and ×1.39 right jerk.
- The evidence is against the σ action as a preservation-compatible dominance control. Re-testing it would need its own justification.

## 5. Feasibility gate FG-1 (bounded; DO NOT RUN without approval)

**Question:**
- Can any of three initial-noise families produce, **on fresh noise**, a paired held-out increase in its intended coordination statistic of at least the registered 0.05, with motion preserved?
- Or is the ceiling, as all evidence so far suggests, well below 0.05?

**Logic:**
- **Per-clip fitting is an upper-bound proxy.** An amortised controller in the same family is, for each clip, one member of the per-clip family (E2c (ii) §4.2).
- So a **negative** gate is evidence against amortised training in that family. It is weak evidence, because the per-clip fit is itself a lower estimate of the per-clip optimum.
- A **positive** gate is necessary, not sufficient, for amortised training.

### 5.1 Design

| Item | Specification |
|---|---|
| Clips | **16 TRAIN clips**, drawn with `default_rng(5100).choice(29,630, 16, replace=False)`<br>Excludes every clip in the five ACMS training sets; stratified 8 with L < 100 and 8 with L ≥ 100 (E2c (ii) length effect)<br>TRAIN, not dev: the held-out axis here is *noise*, and this avoids further dev reuse. Decision U-B2 |
| Fitting noise | N_fit = **16** per clip (4× E2c (ii)): seed 60,000,000 + 1000·j + k, k = 1..16 (j = clip position 0..15) |
| Held-out noise | N_ho = **16** per clip: seed 61,000,000 + 1000·j + k, k = 1..16.<br>Never used in fitting; **common to all variants** (paired) |
| Variants | **V0** uncoupled (μ = 0, κ = 0): baseline<br>**V1** M-C BH learned per clip: the E2c (ii) family unchanged (r = 60, Stiefel U, V, κ ≤ 0.9), now fit on 16 noises. Tests whether more noises remove E2c (ii)'s overfitting<br>**V2** ACMS form per clip (433 parameters, right hand, KL < 1 nat/frame): the ACMS-family ceiling (Stage 5 recommendation b)<br>**V3** SC-MC per clip (866 parameters, both hands) **[N]** |
| Objective (fitting) | V1, V2: maximise the clip-mean surrogate of coord_ah^R (E2c C-c1 surrogate).<br>V3: sum of the surrogates of coord_ah^L, coord_ah^R, coord_lr.<br>Maximisation equals target matching while below target: uncoupled ≈ 0.02 ≪ τ = 0.45 [D].<br>Registered geodesic metric logged every iteration |
| Optimiser | Adam, lr 0.05, 30 iterations, full 16-noise batch per iteration (E2c (ii) settings, kept for comparability). Decision U-B3 |
| Preservation | exact KL logged; the six Stage 5 checks (applied to both hands for V3) on held-out samples vs V0; validity flags; typicality monitor (descriptive) |
| Primary measurement | per clip, held-out mean over 16 noises of the intended statistic, minus V0 on the same noises; clip-bootstrap 95% CI (B = 2,000, seed 0) over 16 clips |
| Also reported | in-sample best, generalisation gap, per-clip table, length split, J-space held-out (descriptive) |

### 5.2 Outcome rule (to be fixed before running)

| Outcome | Rule (per variant, on its primary statistic) |
|---|---|
| **Positive** | held-out Δ CI lower bound > 0 **and** point estimate ≥ 0.05 **and** all preservation checks pass |
| **Negative** | held-out Δ CI upper bound < 0.05 (0.05 is excluded) |
| **Inconclusive** | anything else, including failed preservation checks |

Consequences:
- **Positive V2 or V3:** a new pre-registration for amortised training of that family may be proposed.
- **Positive V1 only:** M-C's E2c (ii) negative is shown to be sample-size-limited; report this, and propose nothing automatically.
- **All negative:** recommend closing the M-C line (route C) and treating ACMS as ceiling-limited for this statistic.

**Precision [D]:** E2c (ii)'s held-out gain CI over 32 clips had a half-width of ≈ 0.015. With 16 clips, expect ≈ 0.02, so the negative rule is decidable if the true gain is ≲ 0.03.

### 5.3 Stop criteria and caps

- **Hard caps:**
  - total wall-clock **4 h**;
  - per learned variant **75 min**;
  - GPU memory **14 GiB** (abort above).
- **Abort conditions:**
  - any non-finite output or gradient;
  - SignSparK checksum change;
  - any split other than TRAIN opened;
  - STOP file.
- **Ordering:** V0 → V2 → V1 → V3.
  - V3 runs only if separately approved as [N].
  - **No adaptive changes** between variants: no lr, iteration or clip changes after seeing results.

### 5.4 Runtime / memory estimate

| Variant | Context-iterations | Estimate | Peak memory |
|---|---|---|---|
| V0 | generation only, 16 × 16 held-out | < 3 min | < 9 GiB |
| V1 | 16 × 16 × 30 = 7,680 | ≈ 50 min (0.39 s × 7,680, measured rate) | ≈ 8.5 GiB [V-based] |
| V2 | 7,680 | ≈ 40–50 min [H] | ≤ 9 GiB [H] |
| V3 | 7,680 × 2 hand rows | ≈ 80–100 min [H]; exceeds the 75 min cap → **N_fit or the clip count must be reduced, or the cap raised: decision U-B4** | ≤ 14 GiB [H] |
| Held-out evaluation and comparators | 16 × 16 × 4 | < 10 min | — |

**Total ≈ 2.5 h** without V3, **≈ 4 h** with it, on the local RTX A4000. No rental.

### 5.5 Baselines and ablations within the gate

- **Baselines:**
  - V0 (uncoupled, paired);
  - per-clip "best-of-16 held-out" (selection, context only; not a deployable mean).
- **Ablations (all cost-free, from the fitted parameters):**
  - V2 vs V3 on the right-hand statistic: does the left head change anything on the right? It should not by construction, which serves as a check.
  - V3 with the state shuffled across noises (ŝ from a different ε_b): tests whether state conditioning matters (H1).
  - V1 at 4 vs 16 noises, using the existing E2c (ii) (n = 32 dev clips) as a non-paired descriptive reference only.

### 5.6 Independent evaluation protocol (only if a variant passes and amortised training is later approved)

- Amortised training on TRAIN clips disjoint from the gate clips.
- Evaluation on dev-256 × 4 with base 40,000,000 noise, on common noise vs uncoupled, using the multi-seed design of `ACMS_MULTISEED_DESIGN.md` (≥ 4 seeds).
- Test remains closed until a separately approved final confirmation.

## 6. What is explicitly NOT proposed

- Repeating E2e / E2c (ii) with more episodes or a different lr as a "new experiment".
- Per-step actions, guidance or step-count control, text or length control, weight-space fine-tuning, new objectives beyond the registered M-C terms. All of these would be [N] and would need separate proposals.
- Any change to thresholds (0.05, preservation bands), frozen targets or metric definitions.
