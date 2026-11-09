# Project Research Log: RL-based improvement of pretrained SignSparK for ASL SLP

**Single active project.** Protocol:
- Stages run in order, and each ends with a report.
- The next stage starts only after explicit approval.
- Nothing in a report counts as approved until the user approves it.

*Last updated 2026-11-03 (E0 executed). Current Stage 4 documents: `research/STAGE4_REPORT.md` (rev. 3.3a), `research/stage4/appendix_gaussian_controller.md` (rev. 3.3). On 2026-11-03 the user instructed "Proceed with E0 (§15.5) only", referring to "the approved Stage 4 Report Revision 3.3a". E0 was run and stopped at its end gate (`research/stage4/E0_REPORT.md`). Not authorised: E1, E2, Stage 5, training and fine-tuning.*

## Confirmed scope (user decision, 2026-11-02)

| Item | Decision |
|---|---|
| Base model | SignSparK (ECCV 2026; github.com/JianHe0628/SignSparK) |
| Target language | American Sign Language (ASL) |
| Dataset | How2Sign, exclusively, for our experiments |
| Objective | Investigate and develop an appropriate RL approach to improve the generation quality of the pretrained SignSparK model |
| Checkpoint | Released checkpoints (HF `LionelLow/SignSparK`, `{hand,body,face}/ema_0.9999_200000.pt`). Their actual pretraining data must be documented accurately (open item below) |

**Open item: pretraining composition.** The sources disagree:

| Source | Lists |
|---|---|
| Repo README | CSL-Daily, How2Sign, BOBSL and CSL-News ("15x more data" than the paper's model; no PHOENIX) |
| HF model card | CSL-Daily, How2Sign and BOBSL |
| Paper (for the paper's model) | Phoenix14T, CSL-Daily, How2Sign and 10% of BOBSL |

The exact composition, proportions and How2Sign split usage are **not stated**. A possible How2Sign-test overlap remains an unresolved leakage risk (D10, R7). No author contact without the user's permission.

## Discontinued / out of scope

- **POSESTITCH-SLT (formerly "Track A")** was discontinued by user decision on 2026-11-02. No further stages, experiments or resources go to it.
- Its earlier report (`research/STAGE1_REPORT.md`) is archived and is **not** an input.

## Stage status

| Stage | Status | Report | Date |
|---|---|---|---|
| 1. SignSparK model, repo, compatibility | **Approved as completed stage** (2026-11-02); individual proposals not automatically approved | `research/SIGNSPARK_STAGE1_REPORT.md` | 2026-11-02 |
| 2. How2Sign EDA, provenance, evaluation feasibility | **Approved as completed stage** (2026-11-02) | `research/STAGE2_REPORT.md` (+ `research/stage2/`) | 2026-11-02 |
| 3. RL literature, released-checkpoint baseline, compute, reproduction audit (R10) | **Approved as completed** (2026-11-03) | `research/STAGE3_REPORT.md` (+ `stage3/paper_notes.md`, `stage3/reproduction_audit.md`) | 2026-11-03 |
| 4. MDP design and validation | **Rev. 3.3a; the user's E0 instruction (2026-11-03) calls it "approved"**. E0 is authorised and done; E1/E2 are not authorised | `research/STAGE4_REPORT.md`, `research/stage4/appendix_gaussian_controller.md` (+ `experiments/stage4/`) | 2026-11-03 |
| 5–9. Implementation → evaluation → analysis → IEEE report → defence | Not started; each gated on the previous stage's approval | – | – |

**Stage 4 revision history:**

| Revision | Content |
|---|---|
| Rev. 1 | Problem P1, formulations F1–F6, M-C/M-D, E2 plan |
| Rev. 2 | Claim scope (perceptual only); human constructs; crossed-effects power; KL exactness; one-step gradient invalidity; M-D vs M-C |
| Rev. 3 draft | Appendix G (Gaussian controller); Theorem 4; κ/σ split |
| **Rev. 3.3a (current)** | Wording-only clarification in §15.4.3: the 95% CI of t*₂₅₆ only selects the R1/R2/R3 branch; its point estimate is a fixed constant in the T5-A margin; no t*₂₅₆ uncertainty enters T5-A (which tests μ against 0). Nothing else changed. Not an approval to run any experiment |
| Rev. 3.3 | Target split: t*₃₂ (D-a/D-b target, bootstrap-propagated) vs t*₂₅₆ (fixed margin constant). D-a direction must be resolvable. Over-shoot flag made direction-general. Pre-run degenerate-target branches R1/R2/R3 with the δ_S₂ floor 0.025; under R3 the SS conditions are not run; margins are frozen once any sample exists. The calibration loop now precedes the gate conditions (n* fixed first); calibration-inconclusive continues with theory-conditional wording; fail/straddle stops. Guarantee-vs-evidence table (F4 by code reading only). Mathematical corrections are marked (MC); no other thresholds changed |
| Rev. 3.2 | Theorem 4: S₃ holds as an extended expectation; a finite S₃ needs T4-e (not guaranteed), so S₃ is descriptive only. T5-A is a TOST on S₂ with the pre-specified δ_S₂ = min(0.05, \|t*_dev\|/4) (renamed t*₂₅₆ in 3.3) and a three-way outcome. D-c renamed "target-directed dominance without detected left-hand degradation" and now requires D-b. D-b tested on the gap ratio (one-sided upper bound ≤ 0.5). T2 calibration separated into precision, false-failure and operating characteristics. Exact D-c aggregation and joint bootstrap. Explicit T0 execution counts (body 576 / 2,112). Reward-validity status table. Unresolved conventions U-A1 to U-A9 |
| Rev. 3.1 | Theorem 4 restated with assumptions T4-a to T4-d per statistic S₁–S₄ (the probability statistic is not determined by the marginals; T5-A gates only on S₁/S₂); r_dom target = reference mean log-ratio t* (not yet computed); T2 = eight-metric marginal check (not distributional equivalence); E2e runtime accounting (default ≈ 37 min, worst ≈ 59 min [E]; cap 1.5 h; run order); dominance levels D-a to D-d (E2e ≤ D-c); semantic wording narrowed to "no regression detected on the specified secondary checks" |
| Rev. 3 integrated | The whole report rebuilt on the Gaussian default. Residual controller non-default and never auto-adopted. E2e redesigned. Equivalence procedures. Paired-advantage and precision corrections. Recalculated compute. E2 order E2d → E2e → E2a → E2b → E2c |

**E0 (SMPL-X track), run 2026-11-03** — details in `research/stage4/E0_REPORT.md`:
- E0.1/E0.2: the user registered and supplied SMPL-X; NPZ files are in `models/smplx/smplx/`; licence note in `research/stage4/e0_licence_note.md`.
- E0.3: `.venv-render` (lock file `requirements-render.lock.txt`).
- E0.4: FK sanity passed C0–C4 on 5 dev GT clips. `flip_left_hand=True` is confirmed: without it the left-hand fingers bend backwards in 100% of frames.
- E0.5: pyrender/WGL works on Windows with no Blender; 3 review videos.
- E0.6, dev, released checkpoint (not DTW-JPE):
  - GF body / hand MPJPE 67.8 / ≈ 20.8 mm; KF2P 10.1 / 3.5–4.6 mm.
  - The dominance log-ratio is supported in joint space (ρ ≈ 0.96).
  - The coordination statistic is representation-dependent (ρ ≈ 0.5; reference 0.44 → 0.23). Flagged for the user; no Stage 4 change made.

**User positions on Stage 4 (before the E0 instruction):**
- Supports P1 and M-C (exact-KL conditional Gaussian) as primary, with coordination and dominance as separate objectives.
- Supports M-D as comparator.
- Willing to approve E0 (subject to the licence).
- E1 deferred.
- E2 steps each require separate approval.

**User decisions at Stage 3 approval (2026-11-03):**
- **Evaluator:** a staged strategy approved for investigation only (human feasibility → SMPL-X → learned evaluator). No recruiting, registration, licensed downloads or evaluator training.
- **Non-RL comparators:** in scope. N5 approved for investigation; N7 exploratory. **No implementation or architecture modification approved.**
- **SLERP:** deferred. **Primary regime:** GF-T2P.

**Standing rules** (from the user's execution instructions, 2026-11-03):
- Every generation result is a *released-checkpoint result*, never a paper reproduction (R10).
- BT is never the sole reward or evaluation criterion.
- **No:** implementation, training, fine-tuning, architecture change, test-set experiments, checkpoint modification, GPU rental, participant recruitment, author contact or Stage 5 work without explicit approval.

**Note on the Stage 1 report:** its ISL/CISLR and alternative-language sections are superseded by the ASL/How2Sign scope. Its compute estimate (S9) is superseded by R1/R8.

## Stage 1 findings (evidence, not decisions)

| # | Finding | Source |
|---|---|---|
| S1 | Velocity target: code (1−M)(x₁−x₀) vs paper x₁−C_t. The code is consistent with the paper's reconstruction Eq. 4 | code + algebra |
| S2 | Loss weights: code 0.5 : 1 : 0.5 (+ acceleration 0.1) vs paper 2 : 1 : 1. CFG: the code drops text only | code vs paper |
| S3 | No stop head; length is an external input. Evaluation uses ground-truth length (and ground-truth keyframes in KF2P) | code |
| S4 | Separate hand/body/face checkpoints (~1.4B params, 5.58 GB each). The two hands are sampled independently. Text is one pooled M-CLIP vector | code, model card |
| S5 | No text-to-gloss or retrieval pipeline exists for How2Sign. The usable regimes are KF2P and GF-T2P (length from the reference) | repo, paper |
| S6 | Joint-local 6D rotations (no root, translation or shape). Joint positions need SMPL-X FK | code |
| S7 | Released assets differ from the paper's, so the baseline must be measured by us | repo docs |
| S8 | How2Sign BT ground-truth BLEU-4 is 3.53 (released) vs 3.37 (paper); a weak, sparse signal | BT README, paper |
| S9 | ~~Compute estimate for T4 / RTX 2050~~ **Superseded** by R1 (the machine has an RTX A4000 16 GB) and R8 (measured) | — |

## Stage 2 findings (verified on data unless marked)

| # | Finding |
|---|---|
| D1 | **Data:** HF `LionelLow/SignSparK_data` @ `9fe7e04`; train / dev / test = 29,630 / 1,650 / 2,183; SHA-256 verified |
| D2 | **Metadata:** no signer, frame-rate or handedness metadata; glosses empty |
| D3 | **Body rotations:** body 6D not orthonormal (worst at the wrists); hand and jaw exact |
| D4 | **Wrist spikes:** wrist "flip" spikes > 45°/frame in 13–17% of clips |
| D5 | **Truncation:** ~14% of clips are truncated at 304 frames |
| D6 | **Keyframes:** dense (~17% of frames; median gap 5) |
| D7 | **Left-hand convention:** the left hand is stored in SMPL-X-left convention; `flip_left_hand=True` is required |
| D8 | **Data errors:** 5 identical pose pairs with different sentences; one 7,357-frame clip; 126 clips with zero segments |
| D9 | **Split disjointness:** splits are disjoint; 19 test clips share an exact translation with train |
| D10 | **Provenance:** checkpoint How2Sign split usage **UNRESOLVED** (leakage risk) |
| D11 | **Metric:** official DTW is an unnormalised accumulated cost; official evaluation uses ground-truth length and keyframes |
| D12 | **Licences:** **MANO is not needed** for this project. SMPL-X is needed only for joint-position metrics and rendering |

## Stage 3 findings (our runs unless marked)

| # | Finding |
|---|---|
| R1 | **Hardware:** RTX A4000 16 GB, 64 GB RAM, i7-8700 |
| R2 | **Assets:** checkpoints and BT model SHA-verified; strict loading; no text-encoder weight download |
| R3 | **BT pipeline:** reproduces the BT README exactly (test GT B4 3.53; KF2P 3.40 vs README 3.34) |
| R4 | **Baseline (test):** KF2P body error 4.0°, BT −4%. GF body error 23.1°, BT B4 0.79 (−78%), face articulation 0.65 |
| R5 | **Coordination (GF):** coordination at chance (0.026 / 0.015 vs GT 0.47 / 0.32); handedness lost; the cause is structural |
| R6 | **Best-of-8 (dev 256):** oracle 12–14%, BT-selected ≈ 0%; BT uncorrelated with pose error within text; BT hacked by selection |
| R7 | **Contamination probe:** inconclusive |
| R8 | **Compute (measured):** bottleneck/adapter fine-tuning and 1–10-step reward gradients fit in 16 GB; full fine-tuning with a frozen reference does not. **No GPU rental is needed for any planned item, and none is requested** |
| R9 | **Literature:** flow RL (Flow-GRPO, ORW-CFM-W2, DRaFT/ReFL, Adjoint Matching, ReinFlow), inference-time (DNO, ReNO, search, TDS), motion RL needs evaluators absent for ASL |
| R10 | **Reproduction audit:** no SignSparK paper generation result is reproduced; only the BT README is |

## Stage 4 findings (dev, first 256 clips × 8 candidates, existing dumps; `experiments/stage4/out/`)

| # | Finding |
|---|---|
| M1 | **Independence (GF):** matched vs mismatched body/hand coordination 0.025 vs 0.022 [V] |
| M2 | **Timing source:** same-text timing agreement body 0.055, R-hand 0.009; generated vs reference 0.014. KF2P 0.82 / 0.76 / 0.74 [V] |
| M3 | **Chance alignment:** best-of-n×n coordination 0.02 / 0.19 / 0.31 / 0.41; other-sentence hands 0.45. Selection does not change hand error [V] |
| M4 | **Handedness:** reference right-dominant 93.8%, GF 48.9%; side-assignment rule ratio 1.08 → 0.80 (reference 0.76) [V]. Prop 1: shared-hand exchangeability [D] |
| M5 | **DTW clip discrimination:** ≈ chance in GF (53.5% / 52.3%); 99.6% in KF2P [V] |
| M6 | **Collapse:** a static mean pose beats every GF sample under DTW; DTW selection lowers articulation [V] |
| M7 | **Prop 2:** independence bound on coordination; predicts 0.023 vs 0.025 observed [I + V] |
| M8 | **SMPL-X licence:** personal, non-commercial research, no redistribution, cite; the upstream visualiser uses EGL (Linux) [V/A] |
| M9 | **Noise Hypernetworks** (NeurIPS 2025, arXiv 2508.09968): KL-regularised noise policy for a frozen generator [P] |
| M10 | **Rev. 2 derivations:** the ideal 1-step map from noise = E[x₁ \| c, L] (constant in ε), so K_train = 10. Residual-form KL ½‖f‖² is exact only for ε-independent f [D] |
| M11 | **Rev. 3 (Appendix G, integrated)** [D unless marked] — **Gaussian controller:** Stiefel-SVD coupling (‖K‖₂ ≤ 0.95, joint over the right hand's 150 inputs); closed-form S; exact separable KL (coupling + scale [+ mean]) iff the parameters are ε-independent |
| M11 (cont.) | **Marginals:** under M-C/κ the per-stream noise *and* generated-motion laws equal the base exactly, given eval(), the same numerical implementation and untouched padded frames. The body is sample-wise identical |
| M11 (cont.) | **Thm 4 (rev. 3.1 statement):** under T4-a to T4-d, the ratio of means = 1, the geometric ratio = 1 and the mean of per-sample ratios ≥ 1, so mean-type targets < 1 (e.g. 0.76) are unattainable by coupling. P(A_R > A_L) is not determined by the marginals; only the joint reference profile is unattainable (Prop 5). Dominance needs M-C/σ [H] or N9 |
| M11 (cont.) | **Paired base reward:** no effect on the pathwise gradient; biased as a REINFORCE baseline. It is a CRN monitoring/evaluation estimator only; the outputs are different samples |
| M11 (cont.) | **Sampler:** the upstream sampler is non-differentiable [C], so an unrolled, checkpointed 10-step loop with equivalence test T0 is needed |
| M11 (cont.) | **Memory and runtime:** ≈ 10–11 GiB at batch 4 with checkpointing; ≈ 5–8 s/step [E], from the Stage 3 probe; gated by E2d |
| M11 (cont.) | **Power:** confirmatory human-study size by simulation only; no validated rater/clip number yet |

## Reward-validity status (measurable statistics vs perceptually validated rewards)

| Component | Measurable statistic | Valid as a statistic on real data | Perceptually validated |
|---|---|---|---|
| r_ah, r_lr (coordination) | yes | yes (GT 0.47 / 0.32 vs chance ≈ 0) [V] | **No.** Also chance-satisfiable (M3). Gate: E1 Phase 1 |
| r_dom (log-ratio to t*; t* not yet computed) | yes | yes (reference right-dominant 94%) [V] | **No.** Gate: E1 Phase 1; any perceived-dominance claim needs D-d |
| Left-hand and articulation/jerk constraints | yes | descriptive | **No**; thresholds are conventions |
| BT (excluded as reward) | yes | weak (GT BLEU-4 3.5) | **No**; fails within-text (R6) |

**Rule:** no component is called a quality reward until its perceptual criterion (Stage 4 §6.4) passes. All present evidence is statistical, not perceptual.

## Proposals and approval status

| ID | Proposal | Status |
|---|---|---|
| S1-D1 | Code authoritative where it conflicts with the paper | Proposed |
| S1-D2 | Measure our own baseline; never reuse paper numbers | Proposed (applied) |
| S1-D6 | Decision unit = sampler step / whole sequence, not frame | Incorporated in Stage 4 |
| S1-D7 | Best-of-N is a mandatory non-RL baseline | Proposed (N3′) |
| S2-E1–E7 | Evaluation protocol (dev selection, test once, paired claims, flagged-clip sensitivity, explicit oracles) | Proposed |
| D4.1–D4.10, D4.14–D4.24 | Stage 4 proposals (`STAGE4_REPORT.md` §17, rev. 3.3) | **Proposed; Stage 4 not approved** |
| D4.11–D4.13 | SLERP deferred; GF primary; no architecture implementation (N7 exploratory) | **Approved 2026-11-03** |

## Rejected or deprioritised approaches

| Approach | Status and reason |
|---|---|
| Per-frame or token MDP | Rejected: the generator is non-autoregressive, whole-sequence (Stage 4 §4) |
| Reference-similarity rewards in GF (pointwise, DTW) | Rejected as rewards: they favour collapse (M5–M6) |
| BT as reward or selector | Rejected as is (R6) |
| One-step (K = 1) training gradients | Rejected: the ideal one-step map is constant in the noise (M10) |
| Residual controller as default | Not default: no closed-form KL or marginal guarantee. Kept as an option, never auto-adopted |

## Pending items

| # | Item | Status |
|---|---|---|
| P1 | Data download | ✅ Done 2026-11-02 |
| P2 | Checkpoint How2Sign split usage | **Unresolved**; author contact needs permission |
| P3 | Full execution instructions | ✅ Received 2026-11-03 |
| P4 | Truncated PDFs | ✅ Resolved 2026-11-03 |
| P5 | Licence registration | **SMPL-X only** (MANO not needed, D12). The user registers personally for E0, if approved. FLAME is not planned |
| P6 | ~~Rented ≥ 40 GB GPU?~~ | **Resolved:** not needed for any planned item (R8, Stage 4 §11); not requested |
| P7 | Earlier gloss→pose code | Out of scope (POSESTITCH discontinued) |
| P8 | Checkpoint / BT downloads | ✅ Done 2026-11-02 |
| P9 | Evaluator gate | E0 (pending approval) → user review → E1 Phase 1 (deferred) → simulation-sized confirmatory study |
| P10 | Architecture changes as comparators | ✅ Resolved: N5/N7 investigation only; no implementation |
| P11 | E2 feasibility steps | **E2d → E2e → E2a → E2b → E2c** (Stage 4 §15.2). Each requires a separate go-ahead; report and stop after each; no automatic fallback to the residual controller |
| P12 | Stage 4 approval | **Revision 3.3** submitted for final review; not approved |

## Implementation status

- **Data:** `data/raw/SignSparK_data/` (read-only; manifest with URLs, sizes and SHA-256).
- **Environments:**
  - `.venv-eda` (Python 3.12.10, `requirements-eda.lock.txt`);
  - `.venv-infer` (Python 3.12, torch 2.10+cu128, `requirements-infer.lock.txt`).
  - Python 3.15 is untouched.
- **Models:** `models/` (SignSparK hand/body/face, How2Sign BT; read-only, SHA-verified). `models/hf_cache` has config and tokenizer files only.
- **Upstream code:** `third_party/SignSparK` (tree `916402d`) and `third_party/SignSparK_BT` (`8dd7cdf`), unmodified.
- **Experiments:** `experiments/`:
  - `common/`, `baseline/`, `contamination/`, `compute/`;
  - `stage4/` (analysis of existing dumps only: `coupling_analysis.py`, `dtw_reward_validity.py`).
- **Not run:** no training, fine-tuning, RL, E0 or E2 step. The checkpoints are unchanged.

## Experiment results

- Released-checkpoint baseline (Stage 3 §1).
- Stage 4 design analyses (§1.2 of the Stage 4 report).
- Outputs: `experiments/baseline/eval/`, `experiments/contamination/out/`, `experiments/compute/out/`, `experiments/stage4/out/`.
