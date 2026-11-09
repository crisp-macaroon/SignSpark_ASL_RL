# Stage 5: 500-episode exploratory RL pilot. Pre-implementation audit and design (FOR APPROVAL)

*2026-11-04. Nothing implemented, generated or trained. Released-checkpoint context; not a paper reproduction.*

**Status of the research record.** Stage 4's results are unchanged and are not reinterpreted here:
- E2e FM13;
- H0 accepted for P1a under fixed-orientation M-C;
- **E2c (ii) negative** (held-out 0.034 vs 0.446; no gain over uncoupled).

This pilot is **exploratory**. It sits outside route A (whose precondition failed), and **no result of it can validate or confirm the Stage 4 hypothesis.**

**Labels:** [V] verified in code or data · [D] derived · [I] interpretation · [P] proposal needing your approval · [U] unresolved.

---

## 1. Pre-implementation audit

### 1.1 What was inspected

| Component | File | Finding |
|---|---|---|
| Sampler | `experiments/stage4/e2d/unrolled_sampler.py` | 10-step Euler, bitwise = upstream `decode` (E2d) [V]. Model loaded with `eval().requires_grad_(False)` [V]. Inputs: initial noise, cond (text embedding, lengths, masks, keyframes), `obs_mask` (all False in GF) |
| Batch loading | `load_first_batch`, `subset` | Only the first dev batch is wired up. **Train-split and dev-256 loading need new loader code** (the same upstream `load_lmdb_dataset`, `split="train"` / `"dev"`, deterministic; R0 already used the train LMDB) [V] |
| GPU harness | `experiments/stage4/gpu_common.py` | caches M-CLIP embeddings for the 32 dev clips only. Train texts need per-clip M-CLIP encoding (the frozen encoder) |
| R metrics | `e2e/metrics.py` v1 (SHA 9930224c…) | coordination, activity A, articulation m2, jerk m3, extreme-frame fraction, arm speed profiles [V] |
| Validity layer | `validity/validity.py` (R v1.1, J v1.1) | `r_stats` returns NaN plus flags; never raises [V] |
| Frozen targets | `FROZEN_TARGETS_R0.json` | R: τ_ah(R) 0.451, τ_ah(L) 0.610, τ_lr 0.323, t* −0.392; all verified under v1.1 [V] |
| Reward spec | Stage 4 §6.1–6.2; readiness report §4, §5.4 | target-matching rewards; constraints c_art (±10%), c_jerk (≤ 1.10×), extreme frames (+2 points); dual ascent; RLOO baseline for REINFORCE (§6.2 item 3); **S-3 (undefined → worst-case reward) is specified but not yet authorised or implemented** |
| Evaluation | E2e dumps, `e2e/stats.py`, `jspace.py` | the E2e A0 uncoupled dumps exist for dev clips 0–31 × k = 1–32 |

### 1.2 What can be changed without touching SignSparK weights [V]

| Lever | Feasible? | Comment |
|---|---|---|
| **Initial noise of a stream** (240 × 304 per clip) | yes | the M-C lever; exact log-probabilities for Gaussian policies |
| Per-Euler-step perturbations of the state | yes, but it modifies the sampling procedure | large action space (10 × 90 × T); off-trajectory states; not covered by the E2d bitwise validation |
| Text embedding / conditioning | technically yes | changes the conditioning semantics. **Excluded:** it would act through meaning, which is out of scope |
| obs_mask / keyframes | no in GF | GF has no keyframes; hand keyframes are hand poses, not body |
| Step count / solver | yes | registered as fixed (K = 10). Excluded |

### 1.3 A controller genuinely distinct from M-C

**M-C** (tested and failed):
- z_R = K ε_body + S ε_R;
- zero-mean, so per-stream laws are preserved exactly (Theorem 3);
- **linear in the body noise**;
- frame-local (no temporal mixing);
- fixed or per-clip parameters.

**E2c (ii) finding [V/I]:** per-clip linear couplings fitted 4 noise draws in-sample (0.74), but gave nothing on fresh draws. My interpretation: the helpful hand-noise structure depends on the **generated body motion**, a non-linear function of ε_body through the frozen body sampler. A linear map from ε_body cannot express that.

**Proposed: the arm-conditioned temporal mean-shift policy (ACMS).** A stochastic policy on the right-hand initial noise, conditioned on the generated right-arm motion:

  ε_R[:, t] = μ_φ(s)[:, t] + ξ[:, t],  ξ ~ N(0, I),  t < L (padded frames unchanged)

  μ_φ(s)[:, t] = β · U · tanh( (W ∗ ŝ)(t) + c )

The components:
- **ŝ:** the per-sample z-scored **right-arm geodesic speed profile of the generated body** (registered `arm_signals`). It is computed after the body is sampled, padded to L.
- **W ∗ ŝ:** a 1-D temporal convolution, W ∈ ℝ^{r×17}, covering ±8 frames of lead and lag.
- **c ∈ ℝ^r:** a bias.
- **U:** a 90 × r Stiefel matrix (sign-fixed QR); **r = 4**.
- **β = β_max · sigmoid(b).**
- **Total:** about 433 trainable parameters, shared across all clips (amortised).

**It differs from M-C in four ways [D]:**
1. It conditions on generated **motion**, not noise. The map from ε_body to μ is non-linear: it passes through the frozen 10-step body sampler.
2. It is a **mean shift**, so it changes the right-hand per-stream law. This lever was untested in Stage 4 (listed as "deferred").
3. It is **temporal**: lead and lag over ±8 frames, whereas M-C is frame-local.
4. It is **amortised**: one φ for all clips, not per-clip parameters.

It is **not** M-C under another name: with β = 0 it is the uncoupled sampler, and no setting reproduces K ε_body.

**Policy-gradient interface [D]:**
- **Exact log-probability:** log π(ε_R | s) = −½ Σ_{t<L} ‖ε_R[:, t] − μ_φ(s)[:, t]‖² + const.
- **Score:** ∇_φ log π = Σ_t ξ_tᵀ ∂μ_t/∂φ.
- **No gradient through the sampler is needed,** so generation runs entirely under `no_grad`.
- **Exact KL** to the uncoupled policy per frame: ½‖μ_t‖² ≤ ½ β_max² r.

**Body and left hand are unaffected:**
- The body is generated before the hand without feedback. The left hand is a separate sequence with its own noise through the shared hand U-Net.
- So the policy **cannot change the body or the left hand at all** [D].
- Left arm–hand coordination and left activity are identical to uncoupled under common noise. Left suppression is impossible by construction; it is still measured.
- **Dominance and L–R coordination change only through the right hand.**

### 1.4 Alternatives considered and not proposed

| Alternative | Why not |
|---|---|
| Per-step stochastic control inside the Euler loop | modifies the validated sampling procedure; about 10× larger action space; off-trajectory risk; 500 episodes are far too few |
| Non-linear residual map of ε_body (Stage 4 option b) | still conditions on noise, which E2c (ii) suggests is the wrong input [I]; no exact KL |
| Pathwise (reparameterised) gradient through the unrolled sampler | lower variance, and the E2d harness supports it. But it optimises the chordal surrogate (S-7) and costs about 6 s per 8 contexts, versus about 2 s no-grad. **REINFORCE is kept, as you specified;** both are valid [D] |

### 1.5 Blocker check

- **No technical blocker.**
- **One authorisation blocker:** the undefined-value reward treatment (S-3) is specified but not authorised, and you instructed me to stop rather than invent one. It is item A2 below.

---

## 2. Reward equation [P]

**Per episode** (clip c, body noise ε_b, right-hand action ε_R):
- **Controlled sample:** x = G(ε_b, ε_L, ε_R).
- **Uncoupled CRN twin:** x⁰ = G(ε_b, ε_L, ξ), with the same ξ and the mean removed. It is used only inside constraint values, never as a baseline (§6.2 item 3).

  R = r_ah − Σ_k λ_k · c_k

**Primary term (target-matching, frozen R target, registered form §6.1):**

  r_ah = −| coord_ah^R(right; x) − 0.451 |   (geodesic, R v1.1)

**Constraints c_k** (per episode; c_k ≤ 0 means satisfied; all on the right hand, R v1.1):

| k | Constraint | Definition | Source |
|---|---|---|---|
| art | articulation | \|m2_R(x) / m2_R(x⁰) − 1\| − 0.10 | registered c_art (§6.1) |
| jerk | jerk | m3_R(x) / m3_R(x⁰) − 1.10 | registered c_jerk |
| ext | extreme frames | extreme_frac_R(x) − extreme_frac_R(x⁰) − 0.02 | registered +2 points (U-A5) |
| act | right-hand activity (suppression / inflation) | \|log(A_R(x) / A_R(x⁰))\| − log 1.25 | **new [P]:** the mirror of the registered left floor log 0.8 (U-A5), applied symmetrically to the right |

- **Dual ascent** (registered §6.2): λ_k ← max(0, λ_k + η_λ · mean_batch c_k), with λ_k starting at 0 and η_λ = 1.0 [P]. Each c_k is clipped to [−1, 1] in the reward [P].
- **KL (excessive deviation):** a hard cap by construction, ‖μ_t‖ ≤ β_max √r, giving KL ≤ 1 nat per frame (β_max = √(2/r) = 0.707) [P].
  - That is below the E2c (ii) level (≈ 2.3) and below the registered per-hand bound 49.82.
  - At the cap, the expected noise norm stays inside the C-c3 norm band for every L ≤ 304 [D].
  - Logged per episode. Not a reward term.
- **Undefined values:**
  - **A2 (S-3 as specified):** if coord_ah^R is undefined (an invalid stream under R v1.1, or non-finite), r_ah = −(1 + 0.451) = **−1.451**, the worst case of the term. The episode is **counted, never dropped**, and flagged.
  - **A3 (an extension of the same principle, new):** an undefined c_k (for example A_R = 0, or an invalid x⁰) takes its clipped worst case, **+1**.
  - Both are logged per episode.

**Not used anywhere:** semantic, naturalness, intelligibility, preference or ASL-quality signals; J space in training; dev or test data in training.

## 3. Training protocol [P]

| Item | Proposal |
|---|---|
| Episodes | **exactly 500** = 125 groups × G = 4 |
| Group | one train clip, 4 independent draws of (ε_b, ε_L, ξ). Baseline: **RLOO**, b_i = mean_{j≠i} R_j (unbiased; registered §6.2 item 3) |
| Clips | 125 train clips, sampled without replacement from the 29,630 R0 train clips (numpy seed 5000). Indices recorded |
| Noise seeds | train base 50,000,000 + 1000·g + i (disjoint from E2e 10M/20M and the evaluation seeds) |
| Update | one Adam step per group (125 updates), lr 0.01, global gradient-norm clip 1.0. Loss = −(1/G) Σ_i A_i log π_i |
| Init (the frozen initial controller) | torch seed 7000: U = QR(N(0, I)); W ~ N(0, 0.1²); c = 0; β = 0.1 β_max |
| Logged per episode | index, clip id/name, L, seeds; the action summary (‖μ‖ mean/max, β, KL/frame); log π; raw R v1.1 statistics for x and x⁰ (all coordination, activity, m1–m4, extreme, dom); validity flags; r_ah, c_k, λ_k, R; baseline, advantage; loss; gradient norm (before and after clipping); parameter norm; wall time; GPU memory |
| Checkpoints | controller state at updates 0, 25, 50, 75, 100, 125 (initial and final included). **The final one is evaluated; there is no checkpoint selection** |
| Environment | `.venv-infer`, fp32, flags as E2d. `HF_HUB_OFFLINE=1` [P], so M-CLIP loads from the local cache with no hub query (E2c (ii) showed hub warnings) |
| Estimated cost [E] | about 2–3 s per group of 4 → **about 6–10 min** for 500 episodes |

## 4. Evaluation protocol [P]

- **Set:** **dev**, the first 256 clips (dev-256, Stage 3 order). **4 evaluation noises per clip**, seeds 40,000,000 + 1000·j + k, never used in training. Total 1,024 samples per condition.
- **Conditions:**
  - (1) **uncoupled** (μ = 0);
  - (2) the **frozen initial controller**;
  - (3) the **trained controller** (final).
- **Common noise:** identical clips, ε_b, ε_L and ξ across all three.
- **No test data. No selection.**
- **Reported, all in R v1.1 (primary space):**
  - mean and median right arm–hand coordination;
  - left arm–hand coordination, L–R coordination, dominance;
  - per-stream activity, m1–m4, extreme frames (both hands);
  - KL per frame;
  - undefined and invalid counts (S-4);
  - paired differences (trained − uncoupled, trained − initial, initial − uncoupled), with 95% clip-bootstrap CIs (per-clip means over the 4 noises; 2,000 resamples, seed 0);
  - per-clip distributions;
  - training curves: R, r_ah, c_k, λ_k, loss, gradient norm, KL;
  - the A3 null figure (0.408) as context.
- **J space** (descriptive, separate): SMPL-X FK on all evaluation samples. J v1.1 coordination, dominance and leakage ratio (the earlier recommendation), never combined with R.
- **Cost:** about 6 min of GPU generation plus about 6 min of CPU FK [E].

**Interpretation rules (fixed before the run) [P]:**
- **Positive:** trained − uncoupled right arm–hand coordination (R) has a 95% CI > 0, **and** every motion-preservation check passes on evaluation:
  - mean articulation ratio within ±10%;
  - mean jerk ratio ≤ 1.10;
  - extreme frames +≤ 2 points;
  - |mean log activity ratio| ≤ log 1.25;
  - undefined fraction ≤ uncoupled + 0.5 points (S-4);
  - KL ≤ 1 nat per frame.
- **Also reported** (not a criterion change): whether the gain reaches **0.05**, Stage 4's T3 transmission threshold, and the % gap closure toward 0.451.
- **Negative:** CI includes or is below 0. **Inconclusive:** CI > 0 but a preservation check fails, or the undefined fraction is exceeded.
- **No claim of generalisation** beyond this checkpoint, the dev-256 clips, this controller and these 1,024 noises.

## 5. Tests (before the run)

**Unit tests:**
1. log π matches `torch.distributions.Normal`.
2. β = 0 gives **bitwise** the uncoupled output.
3. μ = 0 on padded frames.
4. KL ≤ 1 at extreme parameters.
5. U is orthonormal.
6. The RLOO advantage sums to 0 and is independent of the episode's own reward.
7. The score-function gradient is unbiased on a synthetic quadratic reward: a Monte-Carlo vs analytic gradient check.
8. S-3 / A3: NaN statistics give −1.451 / +1 and are flagged, never dropped.
9. Dual-ascent update.
10. Model `requires_grad` is False and the checksum is unchanged.

**Integration test:**
- 2 groups on 2 train clips: logging complete and determinism under fixed seeds.
- A loader assertion that only `split ∈ {train, dev}` is ever opened.

## 6. Deliverables (separate tree; Stage 4 untouched)

**`experiments/stage5/`:**
- `acms_policy.py` (controller);
- `episode_sampler.py`;
- `train_500ep.py`;
- `evaluate.py`;
- `config_500ep.json`;
- `tests/`;
- `out/`: training log, episodes JSON/CSV, checkpoints, evaluation JSON, plots, environment and pip freeze, SHA-256 of inputs, code and checkpoints, commands, runtime and GPU memory.

**`research/stage5/`:** this design, and `STAGE5_500EP_REPORT.md` after the run.

## 7. Expected-outcome honesty [I]

- The prior is unfavourable. Every Stage 4 noise-space intervention gave mean coordination gains ≤ 0.04 on fresh noise. 125 REINFORCE updates over a ~10⁴-dimensional Gaussian action are low-powered.
- The evaluation can resolve paired gains of roughly **≥ 0.02–0.03** (E2e paired CIs had half-widths of about 0.03 at 256 samples; 1,024 here).
- A negative or inconclusive result is the most likely outcome, and a valid one.

---

## 8. Items requiring your approval before any implementation

| # | Item |
|---|---|
| A1 | the ACMS controller (§1.3): r = 4, ±8-frame kernel, right hand only, KL cap 1 nat/frame |
| A2 | **S-3 as specified** (undefined coordination → −1.451; counted, flagged) |
| A3 | the extension: an undefined constraint value → its clipped worst case +1 |
| A4 | the new right-activity constraint (\|log ratio\| ≤ log 1.25) alongside the registered c_art, c_jerk and extreme-frame constraints; dual ascent with η_λ = 1.0 and clipping to [−1, 1] |
| A5 | the training protocol (§3): 125 × G = 4, RLOO, Adam 0.01, clip 1.0, seeds, `HF_HUB_OFFLINE=1` |
| A6 | the evaluation protocol and the interpretation rules (§4), fixed before the run |
| A7 | new loader code for train and dev-256 batches (the upstream loader, imported unmodified) |

After approval, I would implement the code and run the tests. I would then report the test results and **wait for a separate go-ahead before the 500-episode run**, unless you authorise the run together with this design.
