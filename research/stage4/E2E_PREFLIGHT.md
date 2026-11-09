# E2e preflight report (Stage 4 rev. 4.0, Step 2)

*2026-11-03.*

**E2e has NOT been executed.** No model was loaded, no sample generated, no reference statistic computed, and no T1 calibration run for this preflight. The only things run were:
- a self-test on synthetic toy arrays;
- `--plan`;
- resource queries.

E2e waits for your separate explicit authorisation.

## Preflight checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | E2D_REPORT acceptance criteria re-verified from the output files | **PASS** | T0a recomputed from `t0_{body,hand}.npz`: max \|Δ\| = 0.0 (both). `t0.json` T0a/b/c/F all true. M-CLIP identical in 3/3 checkpoints. Design-path B = 1/2/4/8 peak reserved 7.41/7.39/7.46/8.80 GiB, all finite. Gradient-norm ratio 3.88 |
| 2 | E2e uses the validated sampler | **PASS** | `e2e_run.py` imports `e2d/unrolled_sampler.py` unchanged (`unrolled_decode`, `cache_text`, `build_cfg`, `load_model`, `load_first_batch`) |
| 3 | Identical numerical settings for all arms | **PASS** | One process, one harness, fp32, eval(), default flags (matmul TF32 off; cuDNN TF32 on; benchmark off), recorded at step 1. A module in training mode ⇒ stop (F5) |
| 4 | Fixed seeds and CRN | **PASS** | Noise seed = base + 1000·j + k (A0 base 10,000,000; A0′ base 20,000,000). Every coupled or scaled condition transforms **A0's** noise list (CRN). Bootstrap seed 0 (2,000 clip resamples, shared across conditions). T1 null seed 777. (U, V) orientation seeds 0/1/2 as specified |
| 5 | Implementation matches §15.3 and the checklist; thresholds unchanged | **PASS** (with the decisions P-1 to P-14 below, for your approval) | 16 conditions (2 base, 6 BH, 4 LR, 4 SS) and the gate pair are as registered. All margins, branches and stop rules are as registered (see the table below). Self-test 24/24 |
| 6 | All rotation dumps saved for E2e-J | **PASS** | `experiments/stage4/e2e/dumps/<condition>/kNN.npz`: `hand` [32, 2 (L, R), 90, 304] float32 for every condition and noise. `body` [32, 60, 304] for A0/A0′; coupled conditions reuse A0's body (z_b = ε_b, checked by T0 (c)). A write failure ⇒ stop |
| 7 | GPU memory | **PASS** | 14.9 GiB free (display 1.3 GiB). Planned peak ≈ 10 GiB [E]: both U-Nets 6.26 GiB (measured in E2d), plus one M-CLIP 2.09 GiB during T0 (b) only, plus no-grad batch-64 activations |
| 8 | Disk space | **PASS** | 112 GiB free on C:. Dumps ≈ 0.95 GB default, ≈ 1.7 GB worst case [E]. The script refuses to start below 10 GiB free and refuses to overwrite an existing `results.json` |
| 9 | Runtime within the 1.5 h cap | **PASS** [E] | Default ≈ 25–30 min; worst case (n* = 32) ≈ 45 min. Based on the E2d-measured harness: 5.1 s per 64 hand sequences, 2.7 s per 32 body sequences. 128 hand calls by default, 224 worst case; T1 null sets and SS bootstraps ≈ 10–12 min. Cap enforced before every generation call |
| 10 | Data and references | **PASS** | Clips = dev-256 clips 0–31 (names and lengths cross-checked in E2d; re-checked at run time, mismatch ⇒ stop). References: the existing dev-256 hand dump (`gt_poses`) for t*₂₅₆, t*₃₂ and the left-hand Fréchet reference. No test data, no train data |
| 11 | Safety scope | **PASS** | No learned controller; constants only (`noise_transform.py`). No optimiser, no `backward()` in E2e. Checkpoints read-only; `third_party/` untouched |

**Risk noted:** GPU utilisation was 25% at check time, from another process or the display. This affects runtime only, not results.

## Exact command (after your authorisation)

```
cd C:\Users\balaji\Downloads\rlproj\rlproj
$env:HF_HOME="$PWD\models\hf_cache"; $env:WANDB_MODE="disabled"; $env:HF_HUB_OFFLINE="1"
.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2e\e2e_run.py --out experiments\stage4\e2e\out --dumps experiments\stage4\e2e\dumps *> experiments\stage4\e2e\run.log
```

**Outputs:**
- `experiments/stage4/e2e/out/results.json`: every step, test, margin and status (`completed` / `stopped: <reason>` / `error`);
- `experiments/stage4/e2e/run.log`;
- the dumps above.

The report `research/stage4/E2E_REPORT.md` is written from these files after the run.

**Code:**
- `experiments/stage4/e2e/e2e_run.py` (orchestrator);
- `noise_transform.py` (fixed couplings and scales, T1 (a), KL);
- `metrics.py` (space-R statistics);
- `stats.py` (bootstrap, T1–T6, D-levels, Fréchet, energy distance);
- `selftest.py`.

## Run order and stop conditions (frozen, §15.3.1)

| Step | Action | Stop / branch |
|---|---|---|
| 0 | t*₂₅₆ + 95% CI from dev-256 references; branch R1 / R2 / R3; δ_S₂ = min(0.05, max(0.025, \|t*₂₅₆\|/4)) (R3: 0.025); T1 (a) analytic for all 16 conditions; T1 null calibration (1,000 sets) for both gate conditions | not computable ⇒ stop; T1 (a) fail ⇒ stop; calibration impossible within caps ⇒ stop (P-1); R3 ⇒ no SS |
| 1 | T0: A0 k = 1 through the harness vs upstream `decode` (≤ 1e-4); the BH body regenerated through the controlled path vs A0 body (≤ 1e-5); F2 shared inputs; F5 eval | any failure ⇒ stop |
| 2 | A0, A0′ at n = 8; T2 calibration half-width h | — |
| 3 | n ∈ {8, 16, 32} on A0/A0′ until h ≤ 1.5%; n* frozen (32 + "calibration-inconclusive" if never) | none; n* recorded before step 4 |
| 4 | Gate conditions BH-r60-κ0.9-seed0 and LR-r90-κ0.9-seed0 at n*: T1 (b)–(f), T2 (eight metrics, ±5%, 90% CI), T5-A (S₂ against ±δ_S₂; S₁ against [0.95, 1.05]) | T1 fail, T2 fail/straddle, or T5-A fail ⇒ stop. Calibration-inconclusive ⇒ continue with theory-conditional wording |
| 5–6 | Remaining 4 BH and 3 LR conditions at n = 8, with T5-A each | T5-A fail ⇒ stop |
| 7 | 4 SS conditions at n = 8 (unless R3) | — |
| analysis | T3 (transmission Δ ≥ 0.05 with CI > 0; monotone in κ, tolerance 0.01; orientation count; efficiency per nat; specificity ≤ 0.02). T4 (same for L–R). T5-B D-a/D-b/D-c and T6 (§6.5). Energy distance (non-gating) | if T3 and T4 both fail: report options (a)–(e) of §15.2; **no automatic switch** |
| cap | 1.5 h wall clock | stop and report completed conditions |

## Implementation decisions where the specification is silent (for your approval with the authorisation)

**Approved corrections implemented (2026-11-03):** see `E2E_PREFLIGHT_CHANGELOG.md`. The self-test now passes 42/42.

**Superseded by `E2E_PREFLIGHT_DECISIONS.md` (2026-11-03).** That file classifies each decision (explicit / implied / new), quotes the specification, and **withdraws the 0.05 lag-1 cap in P-1**. The table below is kept as originally written.

| # | Decision |
|---|---|
| P-1 | T1 widening schedule:<br>• each check whose own null false-failure rate is ≥ 0.25% is widened by 0.005 per round, until the family-wise rate is < 1%;<br>• caps as registered (mean 0.05, variance ±0.10, correlations 0.05);<br>• **lag-1 cap set to 0.05** (none was registered);<br>• calibration impossible within the caps ⇒ stop before generation.<br>Analytic expectation [E] at n ≈ 37,600 frames: the mean and lag-1 margins widen once, to 0.035 |
| P-2 | "Frames > 45°/frame" counts a frame if **any** hand joint exceeds 45°/frame |
| P-3 | T6/D-c plain thresholds are tested as one-sided 95% bounds:<br>• jerk-ratio upper ≤ 1.10;<br>• extreme-frame difference upper ≤ 0.02;<br>• coord_lr difference lower ≥ −0.03.<br>The Fréchet criterion uses the point FD_cond − FD_A0 ≤ q₉₅(FD_A0′ − FD_A0), as written |
| P-4 | T3 monotonicity and transmission are reported per side; T3 transmission passes if either side passes (as written) |
| P-5 | T1 uses the first 8 noises (256 samples) of each gate condition, as written, even when n* > 8; T2 and T5-A use n* |
| P-6 | A0's k = 1 sample is produced by the harness at step 1 and serves as T0's controlled side (same as "existing A0 sequences") |
| P-7 | S₁'s three-way outcome labels a straddle "inconclusive" (as for S₂) |
| P-8 | Seeds as listed in check 4 |
| P-9 | T5-A runs for every BH/LR condition (gate at n*, the rest at n = 8); any fail stops |
| P-10 | T3, T4 and T5-B use the first 8 noises for all conditions, paired with A0's first 8 |
| P-11 | KL per sample = exact per-frame KL × mean clip length |
| P-12 | Energy-distance features = the eight T2 metrics, standardised by pooled mean and SD |
| P-13 | S₃ and S₄ are reported with descriptive 95% CIs |
| P-14 | Coupled conditions reuse A0's body (z_b = ε_b, exact by construction; checked bitwise at k = 1 by T0 (c)) |

## Not done (by instruction)

- E2e execution;
- E2e-J, E2a, E2b, E2c, R0;
- any controller implementation or training.
