# Programme plan: experiment matrix, resources, open decisions, approval checklist (PROPOSAL)

*2026-11-06. Companion to `ACMS_MULTISEED_DESIGN.md`, `MC_REDESIGN_PROPOSAL.md`, `EVALUATION_PPT_FIGURE_PLAN.md` and `PPT_METRIC_COVERAGE.md`. Nothing listed here has been implemented or run.*

## 1. Experiment matrix

| ID | Purpose | Split / clips | Noise | Conditions | Unit / n | Code | GPU | Depends on |
|---|---|---|---|---|---|---|---|---|
| **PF-0** | Preflight: seeds, configs, hashes, reference immutability | — | — | — | — | new `check_seeds.py` | no | implementation approval |
| **MS-T1..T4** | ACMS training, seeds 7001–7004 | TRAIN, 125 clips each (`default_rng(5000 + d)`) | 51M – 54M + 1000g + i | ACMS, 500 episodes | 4 runs | existing `train_500ep.py` + 4 configs | yes | PF-0 pass |
| **MS-E1..E4** | Held-out evaluation of each run | dev-256 | 40M + 1000j + k, k = 1..4 (same as seed 7000) | uncoupled / initial (u000) / final (u125) | 1,024 samples × 3 per run | existing `evaluate.py` | yes | MS-T_d |
| MS-E0 | Reference run evaluation | dev-256 | 40M | as above | — | **reused**, not rerun | no | hash identity |
| **MS-P** | Pooled analysis and category | — | — | 5 runs | seed = unit | new `pooled_analysis.py` | no | MS-E1..E4 |
| **MS-F** | Multi-seed figures (groups 1b, 3b, 4c, 5b, 6c, 9) | — | — | — | — | new `plots_multiseed.py` | no | MS-P |
| OPT-C | Held-out Δ vs training progress | dev-256 | 40M | trained = u025 / u050 / u075 / u100 | 5 runs × 4 checkpoints, R only | existing `evaluate.py --no-j` | yes | MS-T; separate approval |
| OPT-G | Train-like vs held-out (ACMS) | each run's own 125 TRAIN clips | 45M + 1000g + k, k = 1..4 | uncoupled / final | 5 runs | **new** train-split evaluation script | yes | MS-T; separate approval |
| **FG-1** | Fresh-noise controllability gate | 16 TRAIN clips (`default_rng(5100)`, disjoint, length-stratified) | fit 60M + 1000j + k (k ≤ 16); held-out 61M + 1000j + k (k ≤ 16) | V0, V1 (M-C BH), V2 (ACMS-form), V3 (SC-MC **[N]**) | 16 clips × 16 held-out noises | **new** gate script reusing the E2c (ii) machinery | yes | separate approvals; V3 needs [N] approval |
| FIG-0 | Figures from existing data (7a, 7d, 8 descriptive, 10a, 11; 1a/1c overlays) | — | — | — | — | new plotting scripts | no | implementation approval |

**Seed and noise disjointness (all bases):**
- In use: 10M, 20M, 30M (E2b), 20,261,103/4 (E2d), 40M (eval), 45M (OPT-G), 50M–54M (ACMS training), 60M/61M (FG-1).
- Each range spans ≤ 255,032 integers within its 1M block, so all are pairwise disjoint.
- PF-0 asserts this mechanically.

## 2. Resource and runtime estimate (local RTX A4000 16 GB; no rental)

| Block | Basis | Estimate | Peak GPU | Disk |
|---|---|---|---|---|
| PF-0 | CPU hashing (incl. 523 MB dumps) | < 5 min | — | — |
| MS-T1..T4 | measured 283.8 s/run (≈ 1.96 s/group) | **≈ 19 min** total (cap 4 × 60 min) | 10.5 GiB (measured) | ~1 MB checkpoints + ~2.5 MB logs per run |
| MS-E1..E4 (R + J) | measured 1,638.9 s/run | **≈ 1.8 h** total (proposed cap 40 min/run) | 10.8 GiB (measured) | 4.2 MB samples per run; **+523 MB/run if `--save-dumps`** (U-A5) |
| MS-P, MS-F, FIG-0 | CPU | < 15 min | — | < 50 MB |
| **Core multi-seed programme** | | **≈ 2.2 h GPU, sequential** | ≤ 10.8 GiB | ≤ 2.2 GB with dumps |
| OPT-C (20 R-only evaluations) | R-only duration **unmeasured**; upper bound 1,639 s each | ≤ 9.1 h upper bound; measure the first one, then re-estimate and re-confirm | ≤ 10.8 GiB | 20 × ~4 MB |
| OPT-G (5 evaluations) | similar to evaluation | ≤ 2.3 h (with J); less R-only | ≤ 10.8 GiB | 5 × ~4 MB |
| FG-1 V0–V2 | measured E2c (ii) rate 0.39 s/context-iteration | **≈ 2.5 h** (hard cap 4 h) | ≈ 8.5–9 GiB | < 100 MB |
| FG-1 + V3 | V3 ≈ 2× hand rows [H] | ≈ 4 h, which conflicts with the per-variant cap (U-B4) | ≤ 14 GiB (abort above) | — |

All GPU blocks run **strictly sequentially** on one GPU; the 10.5 GiB peaks do not allow two at once.

## 3. Unresolved scientific decisions (yours)

| ID | Decision | Options | My recommendation |
|---|---|---|---|
| **U-A1** | Which training randomness varies per seed | (a) init + clips + training noise; (b) init + training noise, same 125 clips; (c) init only | **(a):** an independent replication of the whole procedure. (b) isolates optimisation variance; (c) is not independent |
| **U-A2** | Primary pooling set | 4 new runs; all 5 | **4 new runs primary**, 5-run pool reported (7000 was a known result) |
| **U-A3** | Category rule when the across-seed CI includes 0 | literal ("seed-sensitive"); refined (seed-sensitive only with heterogeneity, else inconclusive-precision) | **Refined** (design §5.3) |
| U-A4 | J in every multi-seed evaluation | yes (≈ +20 min/run, unmeasured split); no | **Yes:** J is the required secondary |
| U-A5 | Save dumps in the multi-seed evaluations | yes (+2.1 GB); no | **Yes, if disk allows:** it enables later video and pose-metric analysis without regeneration |
| U-A6 | Run OPT-C / OPT-G | each yes/no | OPT-C yes, R-only, after measuring one; OPT-G yes (the only valid ACMS generalisation gap) |
| U-A7 | Preservation requirement | every run passes; pooled means pass | **Every run passes** |
| U-A8 | Evaluation runtime cap | 40 min/run; other | 40 min |
| **U-B1** | Approve SC-MC (V3) as a new research direction | yes; gate with V0–V2 only | **V0–V2 first; V3 only if V2 is not negative.** V2 tests the ACMS family ceiling, which V3 extends |
| U-B2 | Gate clips | 16 TRAIN (new); dev 0–31 (comparable to E2c (ii)) | **TRAIN:** avoids more dev reuse; the held-out axis is noise |
| U-B3 | Gate optimiser | E2c (ii) settings (Adam 0.05, 30 iterations); a longer budget | **E2c (ii) settings:** comparability; any change must be fixed before the run |
| U-B4 | V3 runtime vs the 75 min cap | reduce to 12 clips; raise the cap to 110 min; drop V3 | decide with U-B1 |
| U-B5 | Gate threshold | registered 0.05 for every intended statistic (coord_ah^R; for V3 also coord_ah^L and coord_lr) | **0.05**, unchanged, per statistic |
| U-C1 | Substitutes for success rate and regret | "paired win fraction", "cumulative shortfall vs uncoupled twin"; omit | **Report the substitutes with those names**, never as success rate or regret |
| U-C2 | Cross-study figure 8 | descriptive with a non-comparability caption; omit until FG-1 | **Descriptive, captioned** |
| U-C3 | Standard pose metrics (FID, MPJPE, DTW) | define and add (descriptive); omit | Only if the deck requires them; definitions need approval first |
| U-C4 | PPT file | provide it so the figure and metric lists can be checked against the deck itself | please provide it |

## 4. Risks and stop conditions (programme level)

- **Any preflight failure** (seed overlap, hash mismatch, config diff beyond the five fields): stop before any GPU work.
- **Any write attempted under `experiments/stage4/` or `experiments/stage5/`**, or a change in a reference artifact's SHA-256: stop. Outputs go only to `experiments/stage5_multiseed/` and `experiments/stage6_gate/`.
- **SignSparK checksum change**, trainable params ≠ 0, non-train/dev split opened, test opened: stop and report.
- **Cap exceeded** (training 60 min, evaluation 40 min, gate 4 h / 75 min per variant, memory 14 GiB): stop and report. No automatic rerun.
- **Failed run:** reported; no silent re-seeding or replacement.
- **No adaptive changes:** no change of lr, architecture, reward, KL cap, constraints, clips or checkpoint after seeing any result. No best-seed or best-checkpoint selection.
- **Interpretive risk:** a reproducible positive at ≈ 0.002 remains practically negligible, and the decks must say so. No ASL-quality claim.

## 5. Approval checklist

Each tier needs its own explicit "approved", per item. Approval in principle is not execution authorisation.

### 5.1 Protocol approval (the designs as written, with the U-decisions resolved)

- [ ] ACMS multi-seed design (`ACMS_MULTISEED_DESIGN.md`), including the seed mapping and the category rule. Needs U-A1, U-A2, U-A3, U-A7.
- [ ] Optional OPT-C and OPT-G protocols (U-A6).
- [ ] FG-1 gate protocol V0–V2 (U-B2, U-B3, U-B5).
- [ ] SC-MC (V3) as a new research direction **[N]** (U-B1, U-B4).
- [ ] Figure plan and metric coverage, including the substitutes for success rate and regret (U-C1, U-C2, U-C3).

### 5.2 Implementation approval (code written and tested; no GPU, no data generation)

- [ ] 4 multi-seed config files.
- [ ] `check_seeds.py` (PF-0) and a run of it (CPU).
- [ ] `pooled_analysis.py`, `plots_multiseed.py`, with unit tests on synthetic arrays.
- [ ] FIG-0 plotting scripts for figures from existing data, and their CPU execution.
- [ ] OPT-G train-split evaluation script (if OPT-G is approved).
- [ ] FG-1 gate script (V0–V2; V3 only if [N] is approved), with self-tests at a test-mode size on CPU or GPU (to be specified at that time).

### 5.3 Training approval (GPU)

- [ ] MS-T1..T4 (4 × 500 episodes, sequential, caps as above).
- [ ] FG-1 fitting, V1 and V2 (and V3 if approved). The per-clip fits are optimisation runs and are approved as training.

### 5.4 Evaluation approval (GPU; dev only; test never opened)

- [ ] MS-E1..E4 (dev-256 × 4, R + J; dumps per U-A5).
- [ ] OPT-C (20 R-only checkpoint evaluations; re-confirm after the first is timed).
- [ ] OPT-G (5 train-split evaluations).
- [ ] FG-1 held-out evaluation (16 × 16 per variant).
- [ ] MS-P pooled analysis and category (CPU; runs automatically after MS-E only if this box is ticked).
