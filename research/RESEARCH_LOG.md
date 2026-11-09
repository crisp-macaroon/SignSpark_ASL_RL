# Project Research Log: RL-based improvement of pretrained SignSparK for ASL SLP

**Single active project.** Protocol:
- Stages run in order, and each ends with a report.
- The next stage starts only after explicit approval.
- Nothing in a report counts as approved until the user approves it.
- **"Approval in principle" (of a design or plan) is never execution authorisation.** Each experiment runs only after the user's explicit go-ahead for that specific step, given after the previous step's report (rev. 4.0 consistency rule).

*Last updated 2026-11-03 (**Stage 4 rev. 4.0**: human verification removed from scope, documentation only).*

*Current Stage 4 documents (all rev. 4.0):*
- `research/STAGE4_REPORT.md`;
- `research/stage4/appendix_gaussian_controller.md`;
- `research/stage4/E2_EXECUTION_CHECKLIST.md`;
- `research/stage4/REV4.0_DECISION_REPORT.md`.

*Previous versions are in `research/archive/`, with hashes in `ARCHIVE_MANIFEST.md`. A rev. 4.0 consistency pass on 2026-11-03 corrected the implementation status and the approval wording; no derivation, threshold or specification changed.*

*Status:*
- E0 is done (`research/stage4/E0_REPORT.md`).
- Rev. 4.0 awaits the user's approval.
- **E2d: authorised by the user's execution assignment (2026-11-03), run, PASS** (`research/stage4/E2D_REPORT.md`).
- **E2e and later steps:** awaiting an explicit go-ahead after the E2d report, as the assignment's §6 requires.
- E1 is deferred indefinitely.
- Not authorised: R0 (needs its own approval), Stage 5, training and fine-tuning.

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
| 4. MDP design and validation | **Rev. 4.0 delivered for approval** (2026-11-03). Rev. 3.3a was called "approved" in the user's E0 instruction. E0 done; E1 deferred indefinitely; E2/R0 not authorised | `research/STAGE4_REPORT.md`, `research/stage4/appendix_gaussian_controller.md` (+ `experiments/stage4/`) | 2026-11-03 |
| 5–9. Implementation → evaluation → analysis → IEEE report → defence | Not started; each gated on the previous stage's approval | – | – |

**Stage 4 revision history:**

| Revision | Content |
|---|---|
| Rev. 1 | Problem P1, formulations F1–F6, M-C/M-D, E2 plan |
| Rev. 2 | Claim scope (perceptual only); human constructs; crossed-effects power; KL exactness; one-step gradient invalidity; M-D vs M-C |
| Rev. 3 draft | Appendix G (Gaussian controller); Theorem 4; κ/σ split |
| **Rev. 4.0 (current)** | **Scope change by the user (2026-11-03): human verification removed.** E1 deferred indefinitely and no longer a prerequisite; D-d removed (levels D-a to D-c remain). Claim scope = measurable motion quality (P1a, P1b, per-stream preservation; secondary checks = "no regression detected"). Claim types G / M / PH; strongest automated claims S1–S6. Two measurement spaces: R (reward and gating) and J (SMPL-X, evaluation only). 0.47 / 0.32 retired as targets; train-reference targets per space via the new reference-only step R0. Automated validity V-R1 to V-R4. Non-gating E2e-J. Limitations §16.1. **Unchanged:** M-C design, Appendix G derivations, E2 order, every E2e threshold, margin, branch and the run order. Previous version archived |
| Rev. 3.3a | Wording-only clarification in §15.4.3: the 95% CI of t*₂₅₆ only selects the R1/R2/R3 branch; its point estimate is a fixed constant in the T5-A margin; no t*₂₅₆ uncertainty enters T5-A (which tests μ against 0). Nothing else changed. Not an approval to run any experiment |
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
  - The coordination statistic is representation-dependent (ρ ≈ 0.5; reference 0.44 → 0.23). This led to the space-specific targets in rev. 4.0.

**User decision (2026-11-03), human verification removed:**
- E1 is deferred indefinitely: no recruitment, rater contact, pilot or participant materials.
- D-d is removed.
- No perceptual naturalness, preference, semantic or intelligibility claims.
- The rotation-space 0.47 target is never reused in joint space.
- Prioritise documentation and the next executable plan.
- Do not run E2, generate samples, implement controllers, train or start Stage 5.

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
| M11 (cont.) | ~~**Power:** confirmatory human-study size by simulation only~~ (withdrawn in rev. 4.0: no human study) |

## Reward-validity status (rev. 4.0: automated validity; perceptual validation out of scope)

| Component | Measurable statistic | Valid as a statistic on real data (V-R1) | Cross-space (V-R2, E0) | Perceptually validated |
|---|---|---|---|---|
| r_ah, r_lr (coordination, space R) | yes | yes (reference 0.44–0.47 / 0.32 vs GF ≈ 0.02) [V] | deficit present in J; ρ ≈ 0.5; levels differ | **out of scope.** Also chance-satisfiable (M3) |
| r_dom (log-ratio to t*^R; not yet computed) | yes | yes (reference right-dominant 94%) [V] | ρ ≈ 0.96 | **out of scope** |
| Left-hand and articulation/jerk constraints | yes | descriptive | J left-hand error available | **out of scope**; thresholds are conventions |
| BT (excluded as reward) | yes | weak (GT BLEU-4 3.5) | — | **out of scope**; fails within-text (R6) |

**Rule (rev. 4.0):**
- Components are "motion-statistic rewards", never "quality" or "naturalness" rewards.
- Claims are type G or type M only.
- Targets are space-specific and come from train references (R0). 0.47 / 0.32 are historical descriptive values, not targets.

## Proposals and approval status

| ID | Proposal | Status |
|---|---|---|
| S1-D1 | Code authoritative where it conflicts with the paper | Proposed |
| S1-D2 | Measure our own baseline; never reuse paper numbers | Proposed (applied) |
| S1-D6 | Decision unit = sampler step / whole sequence, not frame | Incorporated in Stage 4 |
| S1-D7 | Best-of-N is a mandatory non-RL baseline | Proposed (N3′) |
| S2-E1–E7 | Evaluation protocol (dev selection, test once, paired claims, flagged-clip sensitivity, explicit oracles) | Proposed |
| D4.1–D4.10, D4.14–D4.31 | Stage 4 proposals (`STAGE4_REPORT.md` §17, rev. 4.0; D4.8b/D4.8c withdrawn) | **Proposed; rev. 4.0 awaits approval** |
| D4.25 | E1 deferred indefinitely; no human gate | **User decision 2026-11-03** |
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
| P5 | Licence registration | ✅ **SMPL-X registered by the user** (2026-11-03; NPZ in `models/smplx/smplx/`). MANO not needed (D12). FLAME is not planned |
| P6 | ~~Rented ≥ 40 GB GPU?~~ | **Resolved:** not needed for any planned item (R8, Stage 4 §11); not requested |
| P7 | Earlier gloss→pose code | Out of scope (POSESTITCH discontinued) |
| P8 | Checkpoint / BT downloads | ✅ Done 2026-11-02 |
| P9 | Evaluator gate | ✅ E0 done. Rev. 4.0: E1 deferred indefinitely; evaluation is automated only (spaces R and J) |
| P10 | Architecture changes as comparators | ✅ Resolved: N5/N7 investigation only; no implementation |
| P11 | E2 feasibility steps | **E2d → E2e (+ E2e-J) → E2a → E2b → E2c** (Stage 4 §15.2; `stage4/E2_EXECUTION_CHECKLIST.md`). Each requires a separate go-ahead; report and stop after each; no automatic fallback. **E2d: PASS (2026-11-03). Next: E2e**, awaiting an explicit go-ahead after the E2d report |
| P12 | Stage 4 approval | **Revision 4.0** submitted for approval |
| P13 | R0 reference-only targets (rev. 4.0) | Train-reference targets in R and J; SMPL-X hand mirror check; V-R3. Not authorised |

## Implementation status

- **Data:** `data/raw/SignSparK_data/` (read-only; manifest with URLs, sizes and SHA-256).
- **Environments:**
  - `.venv-eda` (Python 3.12.10, `requirements-eda.lock.txt`);
  - `.venv-infer` (Python 3.12, torch 2.10+cu128, `requirements-infer.lock.txt`);
  - `.venv-render` (Python 3.12, CPU torch 2.10.0, smplx 0.1.28, pyrender 0.1.45; `requirements-render.lock.txt`; created for E0).
  - Python 3.15 is untouched.
- **Models:** `models/` (SignSparK hand/body/face, How2Sign BT; read-only, SHA-verified). `models/hf_cache` has config and tokenizer files only. `models/smplx/smplx/` holds the SMPL-X NPZ files (licensed, user-registered); the source zip is unmodified.
- **Upstream code:** `third_party/SignSparK` (tree `916402d`) and `third_party/SignSparK_BT` (`8dd7cdf`), unmodified.
- **Experiments:** `experiments/`:
  - `common/`, `baseline/`, `contamination/`, `compute/`;
  - `stage4/` (analysis of existing dumps: `coupling_analysis.py`, `dtw_reward_validity.py`);
  - `stage4/e0/` (E0: `fk_sanity.py`, `render_review.py`, `joint_metrics.py`).
- **Completed (as of 2026-11-03, rev. 4.0):**
  - **E0 is complete**, run on 2026-11-03 under the user's E0-only authorisation (`research/stage4/E0_REPORT.md`).
  - E0 used existing dev reference poses and existing released-checkpoint dumps only. **No new samples were generated.**
  - **E2d is complete: PASS** (2026-11-03), under the user's go-ahead in the execution assignment (`research/stage4/E2D_REPORT.md`). Results:
    - T0 is bitwise exact (harness = upstream decode).
    - M-CLIP is identical in all three checkpoints.
    - One K = 10 gradient pass at B = 8 takes 8.80 GiB peak reserved and 5.9 s.
    - Gradients are finite; the step-norm ratio is 3.9.
    - Harness: `experiments/stage4/e2d/`. No optimiser, no parameter update.
  - **E2e preflight complete (2026-11-03)**, with E2e **not executed** (`research/stage4/E2E_PREFLIGHT.md`):
    - E2e code is written in `experiments/stage4/e2e/`;
    - the synthetic self-test passes 24/24;
    - checks 1–11 PASS;
    - implementation decisions P-1 to P-14 were resolved (`E2E_PREFLIGHT_DECISIONS.md`) and the approved corrections implemented (`E2E_PREFLIGHT_CHANGELOG.md`): lag-1 never widened; P-2, P-4, P-10, P-11 and P-13 reporting; P-9 wording;
    - the self-test passes 42/42;
    - no registered threshold changed;
    - **E2e is still not executed**; it awaits the user's explicit authorisation.
  - **Consolidated campaign plan prepared (2026-11-03), not authorised** (`research/stage4/STAGE4_CAMPAIGN_PLAN.md`): E2e → E2e-J → E2a → E2b → E2c → R0.
    - E2e-J, E2a, E2b, E2c and R0 code is not yet written.
    - Unregistered parameters for E2a, E2b, E2c and R0 are proposed as C-items for approval.
    - **Revised the same day:** the user approved C-a, C-b and C-j as new labelled pre-registrations; E2b is non-gating; R0 runs concurrently with safeguards R-1 to R-5.
    - C-c3 was revised: N4 typicality is now defined by five constraints (norm, channel mean, channel second moment, per-channel lag-1, pooled lag-1). The synthetic null violation rate is 1.30% mean (1.88% max) per hand. Code: `experiments/stage4/e2c/typicality.py`, `validate_typicality.py` (synthetic only).
    - Awaiting the exact approval statement. **Nothing executed.**
    - **C-c3 final review (synthetic only; `experiments/stage4/e2c/review_typicality.py`):**
      - null calibration OK (max 1.57% vs nominal 1.59% at 16,000 per length; the earlier 1.88% is consistent with MC noise (z = 1.45; not significant); per-length detectability ≈ 0.29 percentage points, so ≤ ≈ 1.9%, not exact calibration) [wording corrected under D8];
      - the alternating 5-iteration projection does not guarantee feasibility, and is replaced by an exact one-shot projection (100% feasible);
      - A/P repair can fail, so a hard feasibility gate and a no-feasible-point rule (E-3, E-5) were added;
      - projection bias: 1.34% of hands modified, median 0.14%; a typical-only best-of-8×8 primary comparator is proposed (C-c2 revised);
      - the short-clip offset limitation is retained;
      - **bounds unchanged.**
    - **C-c3 implementation audit accepted; amendment 2 executed (2026-11-03)**, authorised for B1/B2, D1–D8 and synthetic tests A–C only (`research/stage4/C_C3_FINAL_VALIDATION_REPORT.md`):
      - **B1 [VERIFIED]:** `feasible()` rejects non-finite arrays; `project_mvn_exact()` rejects non-finite input, constant or degenerate channels and unbracketable targets, and returns ok only after verifying N/M/V on its output.
      - **B2 [VERIFIED]:** internal M/V inward margin 1e-5 (registered bounds unchanged); new `to_model_input` checks the exact float32 model-input array, re-projecting if needed; `repair_ap` accepts only model-input arrays.
      - **Test A** PASS: 21/21; the pre-fix code accepted NaN in 12/21. Run 1 flagged an extra 1e39 case whose expectation was my test-design error; it was corrected and run 1 is kept.
      - **Test B** PASS: 10,000/10,000; 0 post-cast violations; max norm error 7.1e-9; M/V deviations ≤ −9.9e-6.
      - **Test C** PASS: 0 unsafe ok.
      - **D1–D8 applied:** plan archived at `research/archive/STAGE4_CAMPAIGN_PLAN_2026-11-03.md`; amendment record in plan §2b; checklist updated; pre-fix code at `research/archive/typicality_pre_B1B2.py`.
      - **Unresolved:** the E2c runner (E-3 loop gate, E-5, comparator, monitoring) is not written; the effect on generated motion is unmeasured; marginal shape (spikes) is unconstrained.
      - C-c3 amendment 2 **awaits approval**. **Nothing in the campaign was executed.**
  - **CAMPAIGN AUTHORISED by the user (2026-11-03)** with the exact §6 statement of `research/stage4/STAGE4_CAMPAIGN_PLAN.md`:
    - Phase 0, then E2e → E2e-J → E2a → E2b → E2c, with R0 concurrent on the CPU (R-1 to R-5);
    - **for these six steps the §5 automatic stop rules replace the per-step go-ahead (user decision)**;
    - approved pre-registrations: C-a1 to C-a5, C-b1 to C-b3, C-j1, C-c1, C-c2 (revised), C-c3 (amendment 2), C-c4, C-c5 (amended), C-c6 (amended), C-r1 to C-r6;
    - no threshold relaxation, no fallback controller, no test data, no Stage 5 work, no controller training, no human evaluation.
  - **Campaign execution (2026-11-03): STOPPED at E2e by the registered gate FM13** (`research/stage4/STAGE4_EXECUTION_SUMMARY.md`, `E2E_REPORT.md`):
    - **Phase 0** PASS: code written; synthetic self-tests 19/19 + 42/42; checkpoint SHA re-verified.
    - **Launch 1** crashed before any work (a disk-check path bug; R0 opened the LMDB twice). Fixed and relaunched; crash logs kept.
    - **E2e** ran 28.8 min:
      - R1 branch, t*₂₅₆ = −0.310 [−0.345, −0.275], δ_S₂ = 0.05;
      - T1 margins calibrated (mean 0.035; lag-1 0.03);
      - T0 bitwise;
      - T2 calibration-inconclusive (h = 1.88% at n* = 32), so theory-conditional wording; both gate conditions passed T1, T2 and T5-A;
      - T5-A: no fail (4 inconclusive).
    - **T3 FAIL:** Δ arm–hand R 0.017, L 0.022, CIs include 0.
    - **T4 FAIL:** Δ L–R 0.035 [0.006, 0.066] < 0.05.
    - **T5-B:** D-c 0/4; suppression signatures.
    - **⇒ FM13 stop:** E2e-J, E2a, E2b and E2c were not run. R0 was paused at 30/60 chunks (resumable) through the STOP file. No automatic switch.
    - Options (a)–(e) of §15.2 are presented, not chosen.
    - A plan wording inconsistency was found: §5 says E2a depends on E2e, whereas §15.2 says E2d only. Flagged for the user.
  - **User decision (2026-11-03):** acknowledged FM13; no threshold change, no fallback, no continuation. **Separately authorised only E2e-J and the R0 resume.**
    - **Pre-run integrity:** dumps complete; R0 chunks 0–29 valid and code unchanged; manifest `experiments/stage4/resume_manifest_2026-11-03.json`.
    - **E2e-J COMPLETED** (`research/stage4/E2EJ_REPORT.md`): J analogues of T3/T4 < 0.05 (R 0.021, L 0.035; L–R 0.036). Seed 2 J right arm–hand 0.058 [0.031, 0.086] (descriptive). Dominance D-a 4/4, D-b 0/4. No effect on FM13.
    - **R0 COMPLETED** (`research/stage4/R0_REPORT.md`); resumed at chunk 31, first 30 bitwise unchanged; 60.2 min running time.
      - **R targets:** 0.610 / 0.451 / 0.323 / −0.392.
      - **J targets:** 0.422 / 0.249 / 0.320 / −0.415.
      - **U-A11:** approximate mirror; J dominance bias ≤ 0.002.
      - **V-R3:** R-space statistics unstable on static non-identity poses, and they raise on a frozen hand. A pre-Stage-5 risk; the final synthetic step crashed on it, was wrapped in R0 only, and the aggregation was rerun without recomputing any chunk.
    - E2a, E2b, E2c not run. **Awaiting the user's decision (E2c (ii) not authorised).**
  - **User decision (2026-11-03): H0 accepted for P1a under the tested fixed-orientation M-C Gaussian coupling design.**
    - No E2c (ii), residual controller, per-step control or further controller-design exploration.
    - P1b recorded separately: fixed side scaling did not reach D-c; suppression signatures.
    - **This does not establish that RL cannot improve SignSparK.** No perceptual, semantic or quality claim.
  - **Stage 4 closure and Stage 5 readiness (documentation and read-only analysis only)** — `research/STAGE5_READINESS_REPORT.md`; frozen targets `research/stage4/FROZEN_TARGETS_R0.json` (source SHA 427dd363…):
    - **Safeguards S-1 to S-7.** S-2 is a new R metric version v1.1: the near-static floor (mean speed ≥ 1e-5 or speed std ≥ 1e-6 rad/frame). It affects 0/4,096 generated and 0/256 dev reference streams (`experiments/stage4/speed_floor_analysis.json`); its effect on R0 train targets is unverified (S-5).
    - **Objective assessment:** no defensible training objective remains in the frozen-base controller scope. Coupling cannot change per-stream statistics (Theorem 3), so they are constraints only. Learned coupling lacks capacity evidence (an amortised controller is bounded by the per-clip optimum = E2c (ii)). P1b failed.
    - **Recommendation:** Stage 5 training is not scientifically justified now. Options: route A (E2c (ii) as the necessary precondition), B (a new problem-selection revision), C (close with H0).
    - **Awaiting the user's decision.** Nothing implemented, trained or generated.
  - **User authorised Steps 0–1 only (toward route A; no training) — done 2026-11-03** (`research/stage4/NUMERICAL_SAFEGUARDS_REPORT.md`):
    - **Step 0:** `experiments/stage4/validity/validity.py` implements R v1.1 (S-1 zero-activity / non-finite guard; S-2 near-static floors: mean ≥ 1e-5, std ≥ 1e-6 rad/frame) and J v1.1 (S-6; std ≥ 1e-7 m/frame). v1 code is bitwise unchanged. Unit tests 21/21 (run 1 19/20 because of a test-design error; kept).
    - **Finding:** SMPL-X skinning leaks forearm motion into J wrist-local hand signals (≈ 5.6e-5 m/frame, ≈ 2% of a moving hand). J arm–hand coordination is therefore not a pure articulation measure; real-data magnitude unmeasured.
    - **Step 1 (S-5, train only, read-only, 159 s):** 0 invalid streams of 118,520; v1.1 bitwise = v1 on all 29,630 clips. **Frozen R targets remain valid unchanged.** Train left-hand floor margin only 10×. J targets under J v1.1 not verified (FK pass not authorised).
    - E2c (ii) remains the necessary next experiment for route A. **Awaiting the user's decision.**
  - **User authorised two read-only analyses (Task 1 J verification, Task 2 skinning leakage) — done 2026-11-04** (`research/stage4/J_VERIFY_LEAKAGE_REPORT.md`; `experiments/stage4/validity/jverify_leakage.py`, 68.9 min CPU):
    - **Task 1 (all 29,630 train clips, R0 order):** 0 invalid J streams; 0 definedness changes; J v1.1 bitwise = v1. **Frozen J targets remain valid unchanged.** All 8 frozen targets are now verified under v1.1.
    - **Task 2 (every 10th train clip, n = 2,963 [REAL]; plus 50 synthetic):**
      - Leakage is 3.7e-5 (L) / 3.0e-5 (R) m/frame, a median 1.9% / 1.0% of the actual hand signal (synthetic: 4.9e-5, 1.8%).
      - Arm–hand coordination is inflated by +0.0009 / +0.0013 (CIs exclude 0); Spearman 0.9995 / 0.9999; L–R unaffected.
      - **Not material by the pre-stated criterion.**
      - Material only for near-static hands: 12 left-hand clips have leakage > 10% of the hand signal, max coordination shift 0.47. A frozen hand under a moving arm is valid in J (leakage-only coordination 0.30–0.40) but undefined in R.
    - **Recommendation:** J remains adequate as a secondary, descriptive (non-gating) measure. Report the leakage ratio for near-static/suppressed hands. J is a different metric on the same data, not independent replication.
    - Stage 5 verdict unchanged; nothing else run. **Awaiting the user's review.**
  - **User authorised E2c (ii) only (route A precondition) — done 2026-11-04** (`research/stage4/E2C_II_REPORT.md`; `experiments/stage4/e2c/e2c_ii_run.py`, outputs in `e2c/out_ii/`; 26.9 min GPU, peak 8.5 GiB, exit 0; weights unchanged):
    - **Four approved corrections** vs `e2c_run.py` (which is unchanged): (i) skipped; B = 8 contexts per pass; per-clip logging; "best training objective" defined without a new feasibility rule.
    - **Benchmarks (fixed before optimisation):** primary typical-only best-of-8×8 0.446 = all-candidate 0.446; dev-256 0.455; A3 0.408.
    - **Result:**
      - Mean held-out (k = 5–8) is **0.034 [0.007, 0.063]**; uncoupled 0.036; gain −0.003 [−0.017, 0.012]. 0/32 clips reach their level.
      - In-sample training (k = 1–4) is 0.737 (still rising at iteration 30): an overfitting gap of 0.70.
      - κ ≈ 0.26, KL 1.2–2.7 nats/frame (bound 49.82 never binding); 32/32 feasible.
    - **C-c6: registered negative outcome for (ii) (FM4), not comparator-sensitive.** Route A precondition not met. The results do **not** support a Stage 5 pre-registration for an amortised M-C controller.
    - **Awaiting the user's decision** (route B or C, or a separately pre-registered many-noise capacity test). Nothing else run.
  - **User requested a Stage 5 500-episode exploratory RL pilot (2026-11-04): audit and design only so far** (`research/stage5/STAGE5_500EP_DESIGN.md`):
    - **Proposed controller:** an arm-conditioned temporal mean-shift policy (ACMS) on the right-hand noise, conditioned on the generated arm speed profile. It is distinct from M-C. REINFORCE with an RLOO baseline.
    - **Reward:** target-matching to 0.451, plus the registered constraints via dual ascent.
    - **Evaluation:** dev-256 × 4 new noises.
    - **Stopped before implementation:** S-3 reward treatment and new design values need authorisation (A1–A7). Stage 4 record unchanged.
    - **User approved A1–A7 (implementation + tests only). Done 2026-11-04** (`research/stage5/STAGE5_IMPLEMENTATION_AUDIT.md`; code in `experiments/stage5/`):
      - Unit tests 15/15. Integration tests 6/6; run 1 was 5/6, kept.
      - **Fix:** M-CLIP batch-composition sensitivity (1e-6 embedding → 2.4e-3 output). The text cache now follows the E2e convention; A0 dumps are reproduced bitwise.
      - The 8-episode mini-runs are deterministic. Stage 4 hashes unchanged.
      - **Open item F2:** τ = 0.4514 (frozen) vs 0.451 (approval text).
      - **The 500-episode run is NOT started; awaiting approval.**
    - **User approved the run (τ = 0.4514 retained). Done 2026-11-04** (`research/stage5/STAGE5_500EP_REPORT.md`; outputs `experiments/stage5/out/`):
      - **Training:** 500 episodes, 4.7 min, weights unchanged; 0 S-3 / 0 A3; constraints never active (λ = 0); KL 0.001 → 0.004 nats/frame.
      - **Evaluation** (dev-256 × 4, common noise): **pre-registered verdict POSITIVE**. Trained − uncoupled right arm–hand R = **+0.0022 [0.0014, 0.0031]**; all preservation checks pass; 0 undefined.
      - **But negligible:** 0.5% gap closure; 0.05 threshold not reached (about 23× below). J agrees in sign (+0.0026, descriptive).
      - Dominance moved +0.003, away from t*.
      - **Recommendation:** no further training on effect size; an ACMS capacity check or multi-seed replication would need new pre-registration. **Awaiting the user's review.**
  - **User asked for the M-C reward code only, no training (2026-11-04). Done:** `experiments/mc_reward/mc_reward.py` (b4dd73e7…), tests `test_mc_reward.py` (515a77f9…), 33/33 pass on synthetic 6D sequences (no models, data or generation).
    - Implements Stage 4 §6.1–6.2 as registered: r_coord = r_ah(L) + r_ah(R) + r_lr and r_dom = −|dom − t*| (target matching, frozen R targets, SHA 26f28f9a… unchanged); art/jerk both hands; c_left (calib_L batch-level vs train A_L^ref, jerk_L, ext_L, lr_floor) only in the σ / combined modes; exact separate KL_κ, KL_σ from `noise_transform.kl_per_frame`; dual ascent; RLOO; CRN paired Δ for monitoring only. Combined mode refused unless explicitly allowed (§6.2).
    - Undefined: S-3 worst case for coordination terms; A3 (+1) for constraints. **r_dom has no bounded worst case:** its undefined value must be set explicitly (no default) [U].
    - **Applied descriptively to the existing E2e dumps (user asked for plots; 2026-11-04)**: `experiments/mc_reward/apply_e2e.py` → `out/mc_reward_e2e.json` (no generation; fixed transforms; λ = α = 0, no z-norm; calib_L vs each dev clip's own reference, a deviation from "train references"). 0 undefined. Largest Δr_coord: BH-r60-k0.9-seed0 +0.075; largest Δr_dom: SS-1.0-1.15 +0.21; SS-0.75-1.0 violates calib_L in 100% (left suppression). Plots: `experiments/mc_reward/out/plots/` (5), `experiments/stage5/out/plots_all/acms/` (11: training + eval) and `smplx/` (6: Stage 5 J + E2e-J).
    - **Unregistered settings** (reported by `MCRewardConfig.unresolved()`): α_κ, α_σ, train z-normalisation statistics (not computed), the r_dom undefined value, η. Not wired to any controller or sampler; nothing trained.
  - **Stage 6 proposal drafted (2026-11-06; analysis and documents only, nothing implemented or run):** `research/stage6_proposal/`
    - `ACMS_MULTISEED_DESIGN.md`: seeds 7001–7004, each varying init, clip sampler (5000 + d) and training-noise base (50M + d·1M); eval noise 40M shared; unchanged code; seed = unit (t-interval); category rule.
    - `MC_REDESIGN_PROPOSAL.md`: failure analysis (E2e, E2c (ii), ACMS); no amortised M-C training recommended; per-clip gate FG-1 (V0–V2; V3 SC-MC is a new direction [N]).
    - `EVALUATION_PPT_FIGURE_PLAN.md`, `PPT_METRIC_COVERAGE.md`, `PROGRAMME_PLAN.md` (matrix, resources, U-decisions, four-tier approval checklist).
    - **Awaiting the user's approval.**
  - **FINAL PROJECT EXECUTION AUTHORISATION (user, 2026-11-07)**: multi-seed replication, FG-1 (V0–V3; V3 authorised as a new direction), OPT-C/OPT-G as monitoring, final evaluation, report and presentation, closure. No per-stage approvals; conservative documented operational decisions; close on the evidence.
    - **Preflight PASS** (`experiments/stage5_multiseed/out/preflight.json`): seed/noise-base disjointness, config and code hashes, checkpoint SHA, Stage 4/5 immutability snapshot.
    - **ACMS multi-seed (7001–7004), all 8 jobs exit 0** (`experiments/stage5_multiseed/out/`, `pooled_results.json`): per-run Δ coord_ah^R (update 125, dev-256 × 4) 7001 −0.0003 [−0.0007, +0.0001] (single-run negative), 7002 +0.0011, 7003 +0.0041, 7004 +0.0039. **Pooled (4 new, t) +0.0022 [−0.0013, +0.0056], SD 0.0022; I² 0.97; category SEED-SENSITIVE.** Five-run secondary +0.0022 [−0.0001, +0.0045], seed-sensitive. Ratio to 0.05: 0.044. All preservation checks pass in every run; 0 undefined; 0 validity flags; λ ≡ 0 in all groups; uncoupled samples bitwise identical across runs; weights unchanged.
    - FG-1 operational decisions D1–D10 documented before running (`research/stage6_gate/FG1_OPERATIONAL_DECISIONS.md`). Smoke test (all four phases, `out_test/`) PASS; analyser validated on smoke outputs (values meaningless, 2 clips).
    - Closure test suites (`experiments/stage6_final/test_out/`): stage5 unit 15/15, stage6 unit 21/21, mc_reward 33/33, validity 21/21 (run 1 failed only because `.venv-infer` lacks smplx; rerun in `.venv-render`, the suite's original environment), c_c3 fixes, phase0 19/19, e2e 42/42.
    - **FG-1 full run, all phases exit 0** (`experiments/stage6_gate/out/`, `fg1_results.json`; 16 TRAIN clips, fit noises 60M, held-out 61M; weights unchanged in every phase; peak reserved 10.5 GiB; V1 3197 s, V2 3180 s, V3 6201 s, all under cap). V0 held-out R 0.062. Held-out Δ vs V0 (space R, 95% clip CI):
      - V1 learned M-C (9060 params/clip): +0.0034 [−0.0121, +0.0166]; in-sample +0.494; preservation pass → **NEGATIVE**.
      - V2 per-clip ACMS (433): +0.1016 [+0.0753, +0.1288], 15/16 clips positive; preservation **FAILS** (articulation ratio 1.1022 > registered 1.10; all other checks pass) → **INCONCLUSIVE**. Bound applied as registered, not revisited.
      - V3 bilateral SC-MC (866): R +0.0893 [+0.0703, +0.1091] (16/16 positive, positive), L +0.1071 [+0.0795, +0.1352] (positive), LR +0.0333 [+0.0049, +0.0594] (inconclusive); preservation passes for R and L; KL max 0.112 / 0.126 → **POSITIVE** (registered V3 rule: any statistic positive).
      - State-shuffle ablation (shuffled − matched, R): V2 −0.085 [−0.109, −0.061]; V3 −0.073 [−0.095, −0.050]. J descriptive Δ: V2 +0.061, V3 R +0.059 / L +0.053, V1 +0.006.
      - Interpretation (not a tested claim): per-clip state-conditioned noise control is feasible on fresh noise; amortised ACMS captures only a few per cent of it. FG-1 uses pathwise gradients, not RL, on TRAIN clips with one fit per clip.
    - **OPT-G (5 runs) and OPT-C (5 runs × updates 25/50/75/100, `--no-j`), all 25 jobs exit 0** (monitoring only; TRAIN and DEV only). OPT-G pooled train-like Δ (4 new) +0.0019 [−0.0015, +0.0053], gap train − dev −0.0003 [−0.0018, +0.0011]. OPT-C pooled Δ by update: 0 +0.0002, 25 +0.0006, 50 +0.0008, 75 +0.0011, 100 +0.0019, 125 +0.0022; all CIs include 0. No checkpoint selected; update 125 stays primary.
    - **Closure (2026-11-07):**
      - All 8 test suites pass, including stage5 integration 6/6 on GPU (`experiments/stage6_final/test_out/summary.json`).
      - Stage 4/5 immutability snapshot re-verified: 548 files, 0 changed or missing (`experiments/stage6_final/closure_verify/`).
      - Both SignSparK checkpoint SHA-256 values match.
      - `research/final/EXPERIMENT_MANIFEST.json`: 337 files and 42 jobs.
      - Bundle `final_bundle/SignSparK_RL_final_bundle.zip` (99.5 MB; 236 large sample dumps hashed in the manifest but not zipped).
      - Final report, deck, and `LIMITATIONS_AND_REPRODUCIBILITY.md` are in `research/final/`.
      - The test split was never opened. **Project closed on the evidence.**
  - **Post-hoc return / baseline-relative analysis (user request, 2026-11-08; CPU only, not pre-registered).** `experiments/stage6_final/posthoc_return.py` → `posthoc_return/posthoc_return_results.json`, `f13_posthoc_return.png`.
    - Episodic return = registered reward (`rewards.episode_reward`, unchanged; single-step episodes; λ ≡ 0 so R = r_ah). Logged training returns were reproduced exactly (max abs error 0). 0 undefined.
    - Eval (dev-256 × 4, update 125), paired trained − uncoupled return: 7000 +0.0023, 7001 −0.0003, 7002 +0.0011, 7003 +0.0042, 7004 +0.0039. Pooled 4 new +0.0022 [−0.0012, +0.0057]; sample win fraction 0.573 [0.441, 0.705]; clip win fraction 0.641 [0.434, 0.847]; CRD (1024 samples) +2.26 [−1.26, +5.79]. Five-run trained − initial +0.0022 [+0.0002, +0.0042] is post-hoc and secondary; it does not change the seed-sensitive category.
    - Training (500 episodes per run): mean R −0.411 to −0.428, SD ≈ 0.17; first-to-last-25-update change pooled +0.022 [−0.049, +0.093] (dominated by clip draws); twin-relative CRD grows only in 7003 (+0.91) and 7004 (+1.19).
    - **Conventional regret not computable:** there is no optimal-policy reference in the design. Baseline-relative statistics are not labelled as regret.
    - Report: a new post-hoc section; the coverage table now distinguishes measured / derived / unavailable. Deck unchanged.
- **Not run:**
  - **E2e, E2e-J, E2a, E2b, E2c and R0 have not been run.**
  - No controller has been implemented.
  - **No training or fine-tuning (and no RL) has occurred.**
  - The checkpoints are unchanged.

## Experiment results

- Released-checkpoint baseline (Stage 3 §1).
- Stage 4 design analyses (§1.2 of the Stage 4 report).
- E0: FK sanity, Windows renders (researcher inspection only), dev joint-space metrics (Stage 4 §1.4; `research/stage4/E0_REPORT.md`).
- Outputs:
  - `experiments/baseline/eval/`;
  - `experiments/contamination/out/`;
  - `experiments/compute/out/`;
  - `experiments/stage4/out/` (including `out/e0/`).
