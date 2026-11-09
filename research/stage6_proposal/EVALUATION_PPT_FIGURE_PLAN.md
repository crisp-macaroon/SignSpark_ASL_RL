# Evaluation-deck figure plan (PROPOSAL)

*2026-11-06. No figure in this plan may be drawn from fabricated or imputed values. Where data does not exist, the figure is marked **NEEDS RUN** and is not produced until an authorised run supplies it.*

**Note:** the evaluation PPT file itself is not in the workspace; no `.ppt` or `.pptx` was found. This plan follows the figure and metric groups listed in your request.

**Status key:**
- **AVAILABLE**: the figure already exists, or can be drawn on CPU from existing artifacts with no new experiment.
- **NEEDS RUN**: requires a new authorised training or evaluation run.
- **NEEDS SCRIPT**: data exists but a new plotting or analysis script is needed (implementation approval only).

**Common conventions:**
- **Palette** (as the existing plots): uncoupled #2a78d6, initial #eb6834, trained #1baf7a.
- **Footer on every figure:** "released-checkpoint result, not a paper reproduction · motion statistics only".
- **R and J are never drawn on one axis.**
- **Reward units:** r_ah = −|coord − τ| (dimensionless; coordination statistics are correlation-type values in [−1, 1]).
- **KL** is in nats per active frame.
- **CIs** are 95% clip-bootstrap (B = 2,000, seed 0) unless stated otherwise.

| # | Title | X-axis (units) | Y-axis (units) | Conditions / legend | Data source | Statistical summary | Status |
|---|---|---|---|---|---|---|---|
| **1a** | ACMS training return vs episodes (seed 7000) | episode (0–500) | return R = r_ah (dimensionless) | per-group mean (dots); 25-group running mean (line); uncoupled-twin return −\|coord_twin − τ\| (grey) | `stage5/out/train/groups.json`, `episodes.json` | running mean; first-25 vs last-25 group means (−0.420 → −0.438) | **AVAILABLE**: `plots_all/acms/a01_train_reward_coordination.png` (twin-return overlay NEEDS SCRIPT, from existing data) |
| **1b** | ACMS training return vs episodes, all seeds | episode | R | one line per seed (7000–7004); pooled mean ± across-seed SD band | multi-seed `groups.json` | per-episode-bin mean ± SD across seeds (seed = unit) | **NEEDS RUN** (MS-T1..T4) |
| **1c** | Controlled − twin return vs episodes | episode | R − R_twin | per seed | `episodes.json` | group-bootstrap CI per 100-episode bin | seed 7000 AVAILABLE (NEEDS SCRIPT); multi-seed NEEDS RUN |
| **2** | ACMS held-out evaluation return vs training progress | update (0, 25, 50, 75, 100, 125) = episodes (0–500) | held-out paired Δ coord_ah^R (R) vs uncoupled; and mean held-out r_ah | per seed; pooled | `evaluate.py --no-j` on intermediate checkpoints (OPT-C) | clip-bootstrap CI per point; across-seed t-interval for pooled | Only updates 0 and 125 exist (Δ −0.00057 and +0.00220) → **NEEDS RUN** (OPT-C). **No checkpoint selection from this curve** |
| **3a** | ACMS reward components and constraints during training | episode | clipped c_k (art, jerk, ext, act; ≤ 0 = satisfied); λ_k | one line per constraint | `groups.json` (`c_mean`, `lambda_after`) | per-group mean; max over episodes | **AVAILABLE**: `a03_train_constraints_kl_lambda.png`. All c_k < 0, λ ≡ 0 |
| **3b** | Same, all seeds | episode | c_k, λ_k | seed × constraint (small multiples) | multi-seed | across-seed band | **NEEDS RUN** |
| **4a** | ACMS held-out coordination: uncoupled vs initial vs trained (R) | condition | coord_ah^R, coord_ah^L, coord_lr, dominance (one panel each) | 3 conditions | `stage5/out/eval/eval_results.json` | clip-mean with CI; paired Δs | **AVAILABLE**: `a05`, `a06`, `a07`, `a08` |
| **4b** | Same in J (descriptive) | condition | coord_ah_J_R etc. | 3 conditions | `eval_results.json → J_space_descriptive` | as 4a | **AVAILABLE**: `smplx/s01–s03` |
| **4c** | Pooled across seeds | seed (7000–7004, pooled) | paired Δ coord_ah^R (R) | per-seed point + clip CI; pooled point + t-interval | multi-seed `eval_results.json` | §5 of the multi-seed design | **NEEDS RUN** |
| **5a** | ACMS preservation checks | check (6) | value relative to limit (ratio, or difference / limit) | trained vs uncoupled; limit lines | `eval_results.json → preservation_checks_trained_vs_uncoupled` | point values (all pass) | **AVAILABLE**: `a09_eval_preservation_checks.png` |
| **5b** | Preservation checks across seeds | check | value / limit | per seed (dots) | multi-seed | min / max across seeds | **NEEDS RUN** |
| **6a** | ACMS KL during training | episode | KL (nats/frame), log scale | mean per group; cap = 1 line | `groups.json → kl_mean`; `episodes.json` | per-group mean, max | **AVAILABLE**: in `a03`. 0.0012 → 0.0035 |
| **6b** | KL at evaluation | condition | KL (nats/frame) | initial, trained | `eval_results.json → kl_per_frame` | mean, max | **AVAILABLE**: `a11` |
| **6c** | KL across seeds | episode | KL | per seed | multi-seed | across-seed band | **NEEDS RUN** |
| **7a** | M-C historical feasibility: transmission vs κ (E2e, R) | κ (0.3, 0.6, 0.9) | Δ arm–R-hand, Δ arm–L-hand, Δ L–R vs A0 | BH-r60 seeds 0/1/2; LR-r90; 0.05 threshold line | `stage4/e2e/out/results.json` | paired clip CI, 32 clips × 8 noises | **NEEDS SCRIPT** (data AVAILABLE; values in `E2E_REPORT.md` §3.6) |
| **7b** | M-C reward on E2e dumps | condition | Δ reward components; constraints; reward vs KL | E2e conditions | `mc_reward/out/mc_reward_e2e.json` | clip CI | **AVAILABLE**: `mc_reward/out/plots/mc1–mc5` |
| **7c** | E2e in J (descriptive) | condition | J Δ | — | `stage4/e2e_j/out/e2ej_results.json` | clip CI | **AVAILABLE**: `smplx/s05`, `s06` |
| **7d** | E2c (ii): in-sample vs held-out per clip | iteration (0–29) / clip | coord_ah^R | in-sample trajectory; held-out; uncoupled; C-c2 level | `stage4/e2c/out_ii/e2c_ii_per_clip.json`, `e2c_ii_aggregate.json` | clip CI | **NEEDS SCRIPT** (data AVAILABLE) |
| **8** | M-C vs ACMS vs uncoupled: held-out right arm–hand Δ against KL | KL per active frame (nats, log scale) | held-out paired Δ coord_ah^R (R) vs that study's uncoupled baseline | ACMS (Stage 5); E2e BH κ 0.3–0.9 (fixed); E2c (ii) learned per clip; uncoupled = 0 line; 0.05 line | Stage 5 `eval_results.json`; E2e `results.json`; E2c (ii) aggregate | each study's own CI | **NEEDS SCRIPT** from AVAILABLE data, as a **descriptive, not like-for-like** figure (different clips: dev-256 vs dev 0–31; noises; budgets; amortised vs per-clip vs fixed). Caption must say so. A like-for-like version needs FG-1 (V0–V3 on common clips and noise) → **NEEDS RUN** |
| **9** | Across-seed stability | seed | paired Δ coord_ah^R; Δ dominance; KL; preservation | 5 seeds + pooled | multi-seed | across-seed SD, t-interval, I² | **NEEDS RUN** |
| **10a** | Training-like vs held-out, E2c (ii) | split (in-sample best, held-out, uncoupled) | coord_ah^R | per clip (lines) and mean | `e2c_ii_per_clip.json` | gap 0.704 [0.650, 0.759] | **NEEDS SCRIPT** (data AVAILABLE) |
| **10b** | Training-like vs held-out, ACMS | split (train clips + fresh noise; dev-256) | paired Δ coord_ah^R | per seed | OPT-G output; dev eval | clip CI per split; Δ gap | **NEEDS RUN** (OPT-G; needs a new evaluation script). The existing training-time controlled − twin (+0.00007) averages over intermediate policies and is **not** a valid train-split estimate of the final policy |
| **10c** | Training-like vs held-out, gate variants | split | Δ intended statistic | V1–V3 | FG-1 | clip CI | **NEEDS RUN** |
| **11** | Computational efficiency | experiment | wall-clock (s); peak GPU memory (GiB); trainable params; generated sequences | E2e; E2c (ii); Stage 5 training; Stage 5 evaluation (with J); multi-seed (when run) | `run.json`, `eval_results.json → run`, `E2E_REPORT.md` §2, `E2C_II_REPORT.md` §7 | measured values only | **NEEDS SCRIPT**, partly AVAILABLE (table below). E2e peak memory **was not logged** and must be shown as missing, not estimated |

## Existing measured values for figure 11 (no new runs)

| Experiment | Wall-clock | Peak GPU allocated / reserved | Trainable parameters | Generated output |
|---|---|---|---|---|
| E2e (fixed transforms) | 1,726 s | **not logged** | 0 | 224 dumps × 32 clips = 7,168 condition-samples |
| E2c (ii) (per-clip fit) | 1,614 s (30 iterations ≈ 1,510 s) | 8.53 / 8.70 GiB | ≈ 9,060 per clip × 32 | 3,840 context-iterations (pathwise) + 128 held-out |
| Stage 5 training (seed 7000) | 283.8 s (≈ 1.96 s per group, 125 groups) | 10.54 / 10.73 GiB | 433 | 500 body + 1,500 hand sequences |
| Stage 5 evaluation (R + J) | 1,638.9 s | 10.54 / 10.78 GiB | — | 1,024 body + 1,024 left + 3,072 right |

## Figures that can be generated now (CPU only, after implementation approval for the scripts)

- 1a (exists; twin overlay needs script);
- 1c (seed 7000);
- 3a, 4a, 4b, 5a, 6a, 6b, 7b, 7c (all exist);
- 7a, 7d, 8 (descriptive), 10a, 11 (need scripts).

## Figures requiring new data

- 1b, 3b, 4c, 5b, 6c, 9: multi-seed training and evaluation;
- 2: OPT-C;
- 10b: OPT-G;
- 10c, and the like-for-like 8: FG-1.
