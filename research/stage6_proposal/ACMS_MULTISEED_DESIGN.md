# ACMS multi-seed replication: design (PROPOSAL, not approved, nothing run)

*2026-11-06. Draft for protocol approval. Released-checkpoint result, not a paper reproduction. Motion statistics only: no semantic, naturalness, intelligibility or ASL-quality claim.*

**Status:** analysis and protocol only. No training, evaluation, sampling or GPU work was done to prepare this document. Every number quoted below comes from existing Stage 4 / Stage 5 artifacts, which are unchanged.

---

## 1. Question

Is the Stage 5 result (seed-7000 run, final checkpoint update 125, paired R-space right arm–hand coordination **+0.00220 [+0.00144, +0.00312]**, 6/6 preservation checks pass, 0.5% gap closure) reproducible across independent training runs of the *identical* procedure?

This replication can establish only whether the procedure reliably produces a small positive change. **It cannot make that change practically meaningful.** The magnitude is reported separately against the existing 0.05 threshold and the frozen τ = 0.4514, exactly as in Stage 5.

## 2. What "seed" means here (verified against the code)

The Stage 5 run used **three independent random sources**, each with its own seed (`config_500ep.json`, `run.json`):

| Source | Code | Seed-7000 run |
|---|---|---|
| Policy initialisation (U_raw, W) | `acms_policy.py:24` `torch.Generator().manual_seed(init_seed)` | `init_seed = 7000` |
| Training clip sample (125 of 29,630 TRAIN) | `episode_sampler.py:16` `default_rng(seed).choice(..., replace=False)` | `train_clip_sampler = 5000` |
| Training noise per episode | `common5.py:174` `manual_seed(base + 1000·g + i)` | `train_noise_base = 50,000,000` (range 50,000,000 – 50,124,003) |
| Evaluation noise | same formula, `a` = dev clip j, `b` = k ∈ 1..4 | `eval_noise_base = 40,000,000` (range 40,000,001 – 40,255,004) |

"Seed 7000" is therefore only the policy-init seed. **Changing `init_seed` alone would not give independent runs**: they would see the same clips and the same training noise. An independent replication must change all three training sources, and must keep the evaluation noise fixed.

### 2.1 Proposed seed mapping (d = s − 7000)

| Run s | `init_seed` | `train_clip_sampler` | `train_noise_base` | Train-noise seed range | `eval_noise_base` |
|---|---|---|---|---|---|
| 7000 (reference, exists) | 7000 | 5000 | 50,000,000 | 50,000,000 – 50,124,003 | 40,000,000 |
| 7001 | 7001 | 5001 | 51,000,000 | 51,000,000 – 51,124,003 | 40,000,000 |
| 7002 | 7002 | 5002 | 52,000,000 | 52,000,000 – 52,124,003 | 40,000,000 |
| 7003 | 7003 | 5003 | 53,000,000 | 53,000,000 – 53,124,003 | 40,000,000 |
| 7004 | 7004 | 5004 | 54,000,000 | 54,000,000 – 54,124,003 | 40,000,000 |

**Disjointness, checked by arithmetic against every noise base found in `experiments/**/*.py`:**
- **Training ranges:** each spans 124,004 integers, and bases are 1,000,000 apart, so the five training ranges are pairwise disjoint.
- **Existing noise bases:** none of these ranges overlaps any of the following:
  - E2e A0 (10,000,000 + 1000j + k; j ≤ 31, k ≤ 32) and A0′ (20,000,000 + …);
  - E2b FRESH_BASE (30,000,000 + …);
  - E2d (20,261,103 / 20,261,104);
  - Stage 5 eval (40,000,001 – 40,255,004);
  - the proposed gate bases in `MC_REDESIGN_PROPOSAL.md` (60M / 61M).
- **Policy-init seeds:** 7001–7004 are used only for `torch.Generator` in `ACMS.__init__`. No other torch generator in the project uses them; the E2c family init uses 1000 + j, j ≤ 31.

**Must still be verified mechanically before any run** (CPU-only preflight, `check_seeds.py`, needs implementation approval):
1. Integer-set disjointness of all train/eval seeds across the five runs and all prior experiments, computed from the configs, not by hand.
2. Noise-tensor identity checks:
   - `noise(51e6, 0, 0)` differs from `noise(50e6, 0, 0)`;
   - `noise(40e6, j, k)` is bitwise identical to the seed-7000 evaluation noise for a sample of (j, k).
3. **Clip overlap** between the five 125-clip training sets. It is reported, not prevented: the expected pairwise overlap under independent draws is 125²/29,630 ≈ 0.53 clips.
4. Config diff: each new config differs from `config_500ep.json` **only** in `name`, `design`, `policy.init_seed`, `seeds.train_clip_sampler` and `seeds.train_noise_base`. This is asserted by script.
5. **Code-hash identity:** `train_500ep.py`, `evaluate.py`, `acms_policy.py`, `rewards.py`, `common5.py`, `episode_sampler.py`, the metrics, the validity layer, `FROZEN_TARGETS_R0.json` (26f28f9a…) and the SignSparK checkpoints (body bf95bb02…, hand 5bb8e407…) must all match `out/env/environment.json` of the reference run. If they do not match, stop.

### 2.2 Deterministic settings (recorded, unchanged from the reference)

- fp32; matmul TF32 off; cuDNN TF32 on; `cudnn.benchmark` off; `cudnn.deterministic` off; `HF_HUB_OFFLINE=1`.
- These are the reference run's flags (`run.json → flags`). They are kept identical so that runs differ only in seeds. Bitwise rerun reproducibility is therefore not guaranteed; the Stage 5 integration mini-runs were bitwise reproducible.
- All flags and every seed are written to each run's `run.json` by the existing code.

## 3. Training protocol (identical to the reference; no tuning)

| Item | Value (all from `config_500ep.json`) |
|---|---|
| Episodes | **500 = 125 groups × 4** (asserted at `train_500ep.py:38`) |
| Controller | ACMS: r = 4, ±8 taps (17-tap kernel), 90 channels, **433 parameters** (U_raw 360 + W 68 + c 4 + b 1)<br>`init_beta_frac` 0.1, `init_w_std` 0.1 |
| Algorithm | REINFORCE with an RLOO baseline (G = 4); one Adam step per group<br>lr 0.01, betas (0.9, 0.999); global grad-norm clip 1.0 |
| Reward | r_ah = −\|coord_ah^R(right) − 0.4514\| (R v1.1; frozen τ)<br>S-3: undefined → −1.4514 |
| Constraints | art / jerk / ext / act, as configured; clip [−1, 1]; A3 → +1<br>Dual ascent η = 1.0, λ₀ = 0 |
| KL | cap 1 nat/frame by construction |
| SignSparK | frozen; checksum start = end asserted; trainable params = 0 |
| Checkpoints | updates 0, 25, 50, 75, 100, 125 (as configured).<br>**Primary = update 125, with no selection.** Intermediate checkpoints are used only for the optional progress curve (§6) |
| Cap | 3,600 s per run (configured); STOP-file honoured |
| Outputs | `experiments/stage5_multiseed/out/s700X/train/`: a **new directory**, so `experiments/stage5/out/` is never written |

**Code changes required: none to training or evaluation code.** Four new config files only, plus new CPU-only preflight, analysis and plot scripts (§8).

## 4. Evaluation protocol (identical to the reference)

For each new run, `evaluate.py` is run unchanged:
- `--ckpt-init <run>/update_000.pt --ckpt-final <run>/update_125.pt`;
- dev-256 × 4 eval noises (base 40,000,000);
- three conditions on **common noise**: uncoupled, initial, final;
- R v1.1 primary; J v1.1 descriptive (never combined with R);
- validity flags; the six preservation checks with the configured thresholds; clip bootstrap B = 2,000, seed 0.

Note on the conditions:
- **Uncoupled** is bitwise the same across all five runs, because it uses the same eval noise and μ = 0. The preflight asserts this on the reference samples.
- **Initial** differs per run, because `init_seed` differs.

**The seed-7000 evaluation is reused, not rerun**, provided the code-hash identity check (§2.1 item 5) passes.

**Per-seed report** (all already computed by `evaluate.py`, or derivable from `eval_samples.json` / `groups.json` / `run.json`):

| Quantity | Source |
|---|---|
| Paired Δ right arm–hand coordination (R), trained − uncoupled; trained − initial; initial − uncoupled | `R_space.coord_arm_rhand` |
| Δ left arm–hand (expected exactly 0), Δ L–R, Δ dominance | `R_space.*` |
| Articulation ratio, jerk ratio, extreme-frame difference, \|mean log activity ratio\|, undefined fraction, max KL | `preservation_checks_trained_vs_uncoupled` |
| Right-hand activity ratio (A_R trained / uncoupled) | `per_stream.hand_R.A` |
| KL per frame (mean, max) | `kl_per_frame` |
| Validity-flag counts, S-3 / A3 counts, invalid arm features | `validity_flags_false_counts`, `groups.json` |
| J-space Δ (descriptive), leakage ratio | `J_space_descriptive` |
| Training return: group mean R, first-25 vs last-25 groups | `groups.json` |
| Controlled − uncoupled-twin coordination over training | `episodes.json` |
| Constraint statistics: max clipped c_k; final λ | `groups.json`, `run.json` |
| β trajectory, parameter norm, gradient norm, clip count | `groups.json` |
| Training time, eval time, peak GPU allocated / reserved | `run.json`, `eval_results.json → run` |
| Gap closure, 0.05 attainment (reported separately) | `verdict` |

## 5. Pooled analysis and interpretation

### 5.1 Unit of inference

**The training run is the unit.** Evaluation samples (1,024 per condition) and clips (256) are *not* independent training replicates. They measure each run's effect precisely, conditional on the shared dev-256 × 4 evaluation set.

### 5.2 Estimands and intervals

For run s, define:
- **Δ_s** = the clip-mean paired improvement (trained − uncoupled, R, `coord_arm_rhand`) on the shared evaluation set, with its clip-bootstrap 95% CI. Δ_7000 = 0.00220.

The pooled statistics are:

| Quantity | Definition | Role |
|---|---|---|
| **Pooled mean** Δ̄ | (1/n) Σ_s Δ_s | point estimate |
| **Across-seed SD** | SD_s(Δ_s) | training variability |
| **Across-seed 95% t-interval** | Δ̄ ± t₀.₉₇₅,ₙ₋₁ · SD/√n<br>n = 5 (t = 2.776) or n = 4 (t = 3.182) | **primary interval** (seed = unit) |
| Evaluation-sampling interval | clip bootstrap (B = 2,000, seed 0) of the seed-averaged per-clip Δ | evaluation component; reported, not used for the category |
| Hierarchical bootstrap | resample runs, then clips jointly (clips are shared); B = 2,000 | descriptive cross-check; coarse at n ≤ 5 |
| Heterogeneity | Cochran's Q, I², DerSimonian–Laird τ² on {Δ_s, SE_s}, with SE_s from each clip bootstrap | descriptive; feeds "seed-sensitive" |
| Run-vs-run paired difference | Δ_s − Δ_7000 per clip (common noise), clip bootstrap | descriptive |

**Primary pooling set:**
- Recommended: the **four new runs**. Run 7000's result was known before this design, so including it in the confirmatory set mixes discovery and replication.
- The five-run pool is reported alongside.
- This is decision **U-A2** in `PROGRAMME_PLAN.md`.

The same pooled table is produced for every secondary quantity in §4. Only the primary statistic drives the category.

**Precision check, from existing data [D]:**
- The within-run clip-bootstrap SE of Δ_7000 is ≈ (0.00312 − 0.00144)/3.92 ≈ 0.00043.
- For the t-interval to exclude 0 at Δ̄ = 0.0022, the across-seed SD must be below ≈ 0.00177 (n = 5) or ≈ 0.00138 (n = 4).
- Whether training variability is that small is exactly what is unknown.

### 5.3 Category rule (proposed; must be fixed before any run)

The rule is applied in order:

1. **Inconclusive (validity):**
   - any run failed to complete 500 episodes;
   - or SignSparK weights changed;
   - or a non-train/dev split was opened;
   - or any run fails any of its six preservation checks.

   The failing runs and checks are reported.
2. **Negative:** Δ̄ ≤ 0.
3. **Reproducible positive:**
   - the across-seed t-interval lower bound is > 0;
   - **and** no run has its own clip-bootstrap CI upper bound < 0.
4. **Seed-sensitive:**
   - the t-interval lower bound is > 0 but at least one run is individually negative (CI upper < 0);
   - **or** the t-interval includes 0 with clear heterogeneity: Cochran's Q p < 0.05, or runs with CIs excluding 0 in opposite directions.
5. **Inconclusive (precision):** the t-interval includes 0 without evidence of heterogeneity.

Rule 5 refines the request's wording, in which "across-seed interval includes zero" would always mean seed-sensitive. Under the literal wording, a homogeneous but imprecise set of runs would be called seed-sensitive. The choice is decision **U-A3**.

**Magnitude (reported separately, never part of the category):**
- pooled gap closure Δ̄ / (τ − uncoupled mean);
- the ratio to 0.05;
- per-run 0.05 attainment.

**Even "reproducible positive" means only:**
- a reproducible, statistically detectable change in one automated motion statistic, with the measured motion statistics preserved;
- not perceptual naturalness, intelligibility, semantic correctness or ASL quality.

## 6. Optional add-ons (separately approvable; not needed for §5)

| ID | What | Why | Cost / risk |
|---|---|---|---|
| **OPT-C** | Evaluate intermediate checkpoints (updates 25, 50, 75, 100) of all five runs with the unchanged `evaluate.py --no-j` on dev-256 × 4.<br>The trained condition = that checkpoint | The "evaluation return vs training progress" figure.<br>**Monitoring only; no checkpoint selection** | 20 evaluations. R-only duration unmeasured: upper bound 1,639 s each (the reference run with J); measure the first one and re-estimate before continuing |
| **OPT-G** | Evaluate each final policy on its own 125 TRAIN clips with fresh noise (proposed base 45,000,000 + 1000·g + k, k = 1..4; range 45,000,001 – 45,124,004, disjoint from all of the above) | Training-like vs held-out generalisation gap | Needs a **new script**: `evaluate.py` hard-codes the dev split.<br>Implementation approval required.<br>~5 evaluations |

## 7. Risks and stop conditions

| Risk | Mitigation / stop |
|---|---|
| Accidental reuse of training noise | Preflight disjointness and tensor checks (§2.1); stop on any failure |
| Writing into Stage 5 outputs | New output root `experiments/stage5_multiseed/`; preflight asserts the reference artifacts' SHA-256 before and after every step |
| Silent code drift since the reference run | Code-hash identity check; stop on mismatch |
| GPU OOM / contention | Runs strictly sequential (peak 10.54–10.78 GiB on the 16 GB A4000); nothing else on the GPU |
| Runtime overrun | Existing 3,600 s training cap.<br>Proposed evaluation cap 2,400 s each (the reference took 1,639 s).<br>Stop the programme and report if exceeded |
| Non-finite gradient | Existing `FloatingPointError` stop; the run is reported as failed, not rerun with changes |
| A failed run | **Not replaced or re-seeded silently.** Reported as failed; any rerun needs your decision |
| Temptation to pick the best run or checkpoint | Forbidden by protocol: update 125 for all runs; all runs reported |
| Dev reuse | Dev clips 0–31 were used in Stage 4. Dev is not used for training or selection here. Test is never opened (logged `opened_splits`) |

## 8. Implementation needed (requires implementation approval; none written)

1. `experiments/stage5_multiseed/configs/config_500ep_s700{1..4}.json`: copies of `config_500ep.json` with the five fields of §2.1 changed.
2. `experiments/stage5_multiseed/check_seeds.py`: CPU-only preflight (§2.1 checks 1–5) plus reference-artifact hashing.
3. `experiments/stage5_multiseed/pooled_analysis.py`: CPU-only; reads the five `eval_results.json` / `eval_samples.json` / `groups.json` / `run.json`; writes `pooled_results.json` and the category.
4. `experiments/stage5_multiseed/plots_multiseed.py`: CPU-only figures (`EVALUATION_PPT_FIGURE_PLAN.md`, groups 1, 3, 4, 5, 6, 9).
5. Unit tests for 2–3 on synthetic per-seed tables. These are not "test data": synthetic arrays only; How2Sign test is never touched.

**Not changed:**
- `train_500ep.py`, `evaluate.py`, `acms_policy.py`, `rewards.py`;
- metrics, validity, targets, thresholds;
- `third_party/`, checkpoints;
- all Stage 4 / Stage 5 outputs.
