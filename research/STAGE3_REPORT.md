# Stage 3 Report: RL literature review, measured baseline, and applicability to SignSparK

Date: 2026-11-03 (revised the same day with the R10 reproduction audit, §1.6, and §§11–13) · Scope: ASL / How2Sign · Status: **final, awaiting approval** (Stage 4 not started)

> **Reproduction status (R10).** We have **not** reproduced any generation result reported in the SignSparK paper. All generation numbers in this report are **released-checkpoint baseline results**. The authors state the released checkpoint differs from the paper's model [A]. The only published numbers we have reproduced are the **released back-translation scorer's README results**. See §1.6 and `research/stage3/reproduction_audit.md`.

**Not done in this stage:**
- No MDP was designed, no RL algorithm was chosen, and the architecture was not modified.
- No training or fine-tuning was run; the checkpoints are unchanged (read-only, SHA-verified).
- No licence registration and no GPU rental.

## Evidence labels

| Label | Meaning |
|---|---|
| **[V]** | Verified by our own runs (code and outputs under `experiments/`) |
| **[P]** | Stated in the paper |
| **[A]** | Author or repository statement |
| **[I]** | My inference |
| **[H]** | Hypothesis |
| **[⚑]** | Outside knowledge, unverified |
| **[Pr]** | Proposal awaiting your approval |

These map to your taxonomy:

| Our label | Your category |
|---|---|
| [V] | Verified |
| [P] | Paper-reported |
| [A] | Author-reported |
| [I] | Inference |
| [H] | Hypothesis |
| [Pr] | Proposal |

[C] marks a fact read directly from the upstream code (verified by inspection).

Per-paper extraction notes (full-text reads) are in `research/stage3/paper_notes.md`.

---

## 0. Setup work done in this stage

### 0.1 Downloads [V]
All files are pinned, and their SHA-256 hashes match the Hub LFS records (`models/MANIFEST.json`).

| Asset | Repository @ commit | Notes |
|---|---|---|
| hand / body / face `ema_0.9999_200000.pt` (5.58 GB each) | `LionelLow/SignSparK` @ `b907f25` | Read-only. Loaded with `weights_only=True`. |
| How2Sign back-translation model (`best.ckpt` 493 MB + config + vocabularies) | `LionelLow/SignSparK_BT` @ `0ced459` | Upstream loads it with `weights_only=False` (arbitrary pickle). We load it with `weights_only=True` plus a 2-class numpy allowlist. |
| M-CLIP + XLM-R **configs and tokenizer only** (~14 MB) | HF | Upstream would download ~4.5 GB of text-encoder weights that the checkpoint already bundles. We construct from config and load **all** weights from the verified checkpoint with `strict=True`. |

### 0.2 Complete versions of the three truncated papers [V]
- `2026.findings-emnlp.1353.pdf` **is RA-RFT** ("Learning to Reason by Analogy"). A complete preprint copy was already uploaded; the official ACL Anthology PDF is now saved as `*_COMPLETE.pdf`.
- RLP was saved as arXiv `2510.01265v2`.
- "Learning What RL Can't" was saved as arXiv `2506.07527v3`.
- Your truncated originals were left untouched.

### 0.3 Hardware correction [V]
The project context listed a local RTX 2050 (4 GB). **This machine actually has:**
- an NVIDIA **RTX A4000, 16 GB** (sm_86, driver 595.79, shared with the Windows display);
- 64 GB RAM;
- an Intel i7-8700.

All compute numbers below were measured on it.

### 0.4 Environment and platform adaptations [V]
- Environment: `.venv-infer` with Python 3.12, torch 2.10.0+cu128, and the upstream pins (`requirements-infer.lock.txt`).
- Upstream code lives in `third_party/` and is unmodified (`UPSTREAM.txt` records the commits).
- Four runtime adaptations were needed (in `experiments/common/`, applied without editing upstream files):

| # | Problem | Adaptation |
|---|---|---|
| 1 | Upstream initialisation downloads text-encoder weights the checkpoint already contains | Construct M-CLIP from config only |
| 2 | Upstream NCCL process-group initialisation is impossible on Windows | Replaced with single-GPU device selection (sampling uses no collectives) |
| 3 | `sample.py` appends a `:`-containing timestamp when its output folder exists (invalid on Windows) | One hard-linked checkpoint folder per run |
| 4 | Upstream loads the back-translation checkpoint with arbitrary pickle | Safe checkpoint loading |

### 0.5 Not obtainable [V]
- **AlignProp** (arXiv 2310.03739): the latest version is withdrawn and the earlier version returns 404. DRaFT covers the same method family.

---

## 1. Measured released-checkpoint baseline (not a paper reproduction)

### 1.1 Protocol
- **Model and sampler:** official `sample.py`; 10 Euler steps (the paper's headline setting); no CFG (the author states the main tables used none [A]); seed 102.
- **Data handling:** `flip_left_hand=True` (Stage 2 D7); sequences truncated at 304 frames as upstream does.
- **Two regimes:**
  - **KF2P**: ground-truth mode-3 keyframes and ground-truth length.
  - **GF-T2P**: no keyframes, *but ground-truth length is still supplied*.
- **Metrics:** all licence-free.
  - Geodesic rotation error after Gram–Schmidt, on non-keyframe frames.
  - Articulation, speed and jerk ratios against the reference.
  - Coordination: correlation of right-arm vs right-hand angular speed, and of left- vs right-hand speed.
  - Back-translation (BT) via the **official** scoring path.
- **Scorer validation:** our ground-truth BT on test reproduces the README exactly (B1 23.07 / B4 3.53 / chrF 19.81 / ROUGE 23.58). Our KF2P result is within 0.11 of the README on every column (B4 3.40 vs 3.34; ROUGE 22.61 vs 22.59). Seed-to-seed variance was not measured, so "noise" is an inference [I]. My first BT pass skipped the official reference normalisation; it was found and fixed before any number was used.

### 1.2 Results [V]
Mean [bootstrap 95% CI]. Test: n = 2,183 clips. Dev results are in `experiments/baseline/eval/` and are very similar.

| Test metric | KF2P (GT keyframes + GT length) | GF-T2P (text + GT length) | Reference / chance |
|---|---|---|---|
| Body error, non-keyframe (deg) | 4.01 [3.91, 4.11] | **23.08** [22.95, 23.22] | 0 |
| Right-hand error (deg) | 6.07 [5.98, 6.17] | **22.11** [21.98, 22.24] | 0 |
| Left-hand error (deg) | 4.65 [4.57, 4.74] | 22.37 [22.23, 22.52] | 0 |
| Jaw error (deg) / expression L2 | 1.15 / 2.00 | 3.18 / 11.05 | 0 |
| Articulation ratio body / R-hand / face expression | 1.05 / 1.01 / 0.98 | 1.00 / 0.91 / **0.65** | 1 |
| Arm–hand speed coordination (r) | 0.385 [0.376, 0.393] | **0.026** [0.018, 0.034] | GT 0.471; chance 0.001 |
| Left–right hand coordination (r) | 0.310 | **0.015** | GT 0.323; chance −0.003 |
| Left/right hand activity ratio | 0.739 | **0.999** | GT 0.697 |
| BT BLEU-4 / chrF / ROUGE | 3.40 / 19.33 / 22.61 | **0.79** / 16.63 / 16.11 | GT 3.53 / 19.81 / 23.58 |

### 1.3 Findings
1. **KF2P has little headroom** [V]:
   - BT drops only 4% from the ceiling.
   - Errors are about 4–6°.
   - Articulation is at reference level.

   This confirms Stage 2 D6 (dense oracle keyframes).
2. **GF-T2P is where the model is weak** [V]:
   - BT BLEU-4 is −78% of the ceiling (dev −83%).
   - Body and hand errors are about 5× those of KF2P.
   - The face is clearly under-articulated (expression variation 0.65× the reference).
   - Body and right-hand articulation is only mildly reduced.

   Large reference error with near-normal articulation means GF produces *plausible-looking but different* motion. Part of that "error" is the legitimate one-to-many nature of text→sign, so **reference error alone overstates GF failure** [I].
3. **Independent streams break coordination in GF-T2P** [V]. This answers your direction 6.
   - Arm–hand and left–right timing coupling fall to essentially chance level (0.026 and 0.015, versus ground truth 0.47 and 0.32).
   - **Handedness is lost:** the two hands become statistically identical (activity ratio 1.00 vs 0.70).
   - Code explanation [C][I]:
     - the hand model is one network trained on both hands (the left mirrored into right convention) with **no side or handedness input**;
     - in GF both hands receive identical text conditioning and independent noise;
     - body, hands and face are separate networks with no shared latent.

   With KF2P, ground-truth keyframes carry the coordination (0.385 and 0.31 retained). This is a *structural* deficit, not sampling noise.
4. **Best-of-8 headroom exists, but the only available verifier cannot find it** [V] (256 dev clips × 8 candidates):

| Regime | Mean over candidates | Oracle best-of-8 (reference-based) | BT-selected (test-legal) | Spearman(BT chrF, error) within clip |
|---|---|---|---|---|
| KF2P body / R-hand (deg) | 3.91 / 5.86 | 3.44 / 5.09 (−12 / −13%) | 3.91 / 5.79 | −0.02 / −0.00 |
| GF body / R-hand (deg) | 23.00 / 21.75 | 20.23 / 18.77 (−12 / −14%) | 22.86 / 21.50 | −0.03 / −0.01 |

   - Choosing candidates by BT raises BT's own chrF by about 5–6 points (KF2P 19.8 → 24.9; GF 16.9 → 22.6) **without improving pose error**. This is direct **verifier hacking** at selection level.
   - Within a sentence, BT carries no measurable information about pose accuracy.
   - **Consequence:** with the current evaluators, an RL reward based on BT would very likely optimise BT artefacts rather than signing [I, strongly supported].

### 1.4 Measured compute (A4000 16 GB, fp32, upstream sampler) [V]

| Workload | Measured |
|---|---|
| Sampling the full test split, 10 steps, batch 32 | Body / face 6.3–9.6 min (the slower run overlapped with evaluation jobs); hand 11.3–11.5 min (2 hands per clip); peak 5.5–5.7 GB |
| One forward+backward, all 835M U-Net params (B = 1–8) | Peak 8.3–8.7 GB; + AdamW 6.2 GB (analytic) ≈ **14.9 GB, borderline**; no room for a frozen reference |
| Bottleneck-only (197M params) | Peak 6.0–6.6 GB (B ≤ 16); + AdamW 1.5 GB ≈ 8 GB; 0.14–0.27 s/step |
| Reward gradient through K Euler steps (bottleneck trainable) | K = 1: 6.0 GB, 0.17 s · K = 4, B = 4: 7.6 GB, 0.8 s · K = 10, B = 4: 10.7 GB, 2.2 s |

**Conclusion:**
- Inference-time methods, controllers, and adapter or bottleneck fine-tuning (including one-step and few-step reward gradients) are feasible on this machine.
- Full-parameter fine-tuning with a KL reference model is not feasible without memory tricks or a larger GPU. **A rented GPU is not needed for the recommended directions.**

### 1.5 Contamination probe [V], inconclusive as anticipated
- **Method:** the frozen checkpoint's own flow and reconstruction losses, at fixed t ∈ {0.1, …, 0.9} and fixed noise, on 397 length-matched clips per split, GF and KF2P, body and hand.
- **Result:** train, dev and test are statistically indistinguishable.
  - Body GF reconstruction ×10⁻³: train 11.65 [11.40, 11.89], dev 12.07 [11.82, 12.35], test 11.88 [11.61, 12.18].
  - Hand: test is lowest.
- **Interpretation** [I]: even *known* training clips show no loss gap, so the model has no measurable per-clip memorisation footprint. Loss-based membership inference therefore **cannot** detect test inclusion. The contamination risk remains **unresolved**; no claim of cleanliness is made.

### 1.6 Reproduction audit (R10) [V]
Full audit: `research/stage3/reproduction_audit.md`.

**Bounds on any comparison with the paper:**
- **Different model.** The released checkpoint is not the paper's model. It was trained on different data ("~15× more", no Phoenix14T) and on re-optimised parameters [A].
- **Different back-translation (B-T) model.** The paper used an unreleased SL-Transformer scorer; on real How2Sign poses (GT) it scores BLEU-4 3.37 [P]. The released scorer scores 3.53 [A][V].

| Paper item (How2Sign) | Status | Reason |
|---|---|---|
| Tab. 3 GF-T2P DTW-JPE / DTW-PA-JPE | **Not reproduced** | Needs SMPL-X/MANO plus SOKE eval code; would describe the released checkpoint anyway |
| Tab. 4 KF2P DTW-(PA-)JPE | **Not reproduced** | Same |
| Tab. 4 KF2P B-T BLEU-4 2.99 (−11%) | **Not comparable** | Different B-T model and checkpoint. Ours is 3.40 (−3.9%) with the released scorer; the two causes cannot be separated |
| Tab. 4 SLERP baseline | **Not run** | B-T part is licence-free and runnable; JPE part needs SMPL-X |
| Tab. 8 face PA-VPE 0.07 | **Not reproduced** | Needs the FLAME model (licence) |
| "0.01 s/vid" speed | **Not comparable** | Our 0.17–0.32 s/clip is whole-script wall time, including model load, I/O and output; the paper's hardware and timing scope are unstated |
| Tabs. 6–7 and Fig. 4 ablations | **Not reproducible** | Need retraining or unreleased variants |
| Tabs. 1, 2, 5 and Fig. 5 | **Out of scope** | Non-ASL data, the FAST segmentor, and BSL signers |

**Reproduced:** the released B-T scorer's README results only. GT matches exactly; KF2P is within 0.11 on every column.

**Consequence for later stages [I]:** every claimed improvement is paired against *our* released-checkpoint runs, never against paper numbers.

---

## 2. Uploaded RL papers: summaries (full-text reads)

| # | Paper | Problem | RL method | Key stability mechanism | Main evidence | Main limitation |
|---|---|---|---|---|---|---|
| U1 | **TOPR** (NeurIPS 25) | Off-policy LLM RL with negatives | REINFORCE: SFT weight on positives, truncated IS on negatives | Truncation (bounded objective); baseline = dataset-composition knob | GSM8K/MATH gains over PPO / DPO / naive REINFORCE | Boundedness proof uses π(τ) ≤ 1 (discrete); needs log π |
| U2 | **CARFT** (EMNLP 25) | RL collapse; unused annotated CoTs | PPO + KL + InfoNCE to annotated-CoT embedding | Contrastive anchor to reference; embedding-based partial reward | +0.5–2 points vs ReFT/Dr.GRPO | No variance reported; small margins |
| U3 | **SCoRe** (ICLR 25) | Intrinsic self-correction | Two-stage REINFORCE + KL; progress-shaped reward | Strong KL on turn 1 (Stage I); shaping against "behaviour collapse" | MATH Δ(t1, t2) +4.4 vs −11.2 | Binary verifier; closed models |
| U4 | **RL vitamin for ODT** (NeurIPS 24) | Online fine-tuning of supervised transformers on continuous control | Supervised loss − α·Q (TD3) | Supervised anchor; ‖a − a_old‖² as deterministic-policy KL | D4RL gains; **PPO "does not work at all" with the DT** (IS fragility) | Theory assumptions; critic needs environment returns |
| U5 | **1-shot RLVR** (NeurIPS 25) | Data needed for RLVR | GRPO + small KL + entropy | Policy-gradient loss drives gains; entropy helps | One example ≈ 1.2k examples | Test-set checkpoint selection; format confound |
| U6 | **RA-RFT** (Findings EMNLP 26) | RL bounded by parametric knowledge | GRPO with retrieved analogous traces | Retrieval quality as a first-class variable | +4.1 avg vs GRPO; RA-SFT ≈ SFT | Judge-labelled retriever; no CIs |
| U7 | **ReLIFT** (ICLR 26) | RL cannot learn beyond the base model | GRPO interleaved with SFT on hardest questions | Selective supervised steps; entropy term | 52.6 vs RL 46.9 / SFT 49.0 | **Same-batch RL+SFT every step collapsed (23.8)** |
| U8 | **RLP** (ICLR 26) | RL signal during pretraining | Info-gain reward vs EMA no-think baseline; clipped surrogate | Lagged EMA baseline to prevent reward collapse or hacking | Large gains at NVIDIA scale | No SLP analogue for "thoughts" |

---

## 3. External literature (RL for diffusion/flow, inference-time, motion, SLP)

| # | Paper | Family | Mechanism | Evidence | Relevance to SignSparK |
|---|---|---|---|---|---|
| E1 | **Flow-GRPO** (NeurIPS 25) | Online RL for **flow matching** | ODE→SDE with preserved marginals; Gaussian per-step policy; GRPO; closed-form KL in velocity space; 10 training steps; LoRA | SD3.5-M GenEval 0.63 → 0.95. Without KL: diversity collapse. G < 24 collapsed. 24 A800s. | **High.** SignSparK is a rectified flow. Masked keyframe states need checking. |
| E2 | **DDPO** (ICLR 24) | Diffusion RL | Denoising as a T-step MDP; REINFORCE / IS-PPO | > RWR. Visible reward exploitation (stylisation, noise). | Canonical MDP: the decision unit is the denoising step, not the frame |
| E3 | **DRaFT** (ICLR 24) | Differentiable-reward fine-tuning | Backprop the reward through the last K steps (K = 1 best); LoRA | 200× more sample-efficient than DDPO. Collapses without regularisation. Best-of-16 weak. | **High.** SignSparK's L_recon makes its one-step x̂₁ meaningful; measured cost 0.17 s/step |
| E4 | **ORW-CFM-W2** (ICLR 25) | Reward-weighted flow matching | w(x)·CFM loss on self-generated samples + α‖v − v_ref‖² | Theory: collapse to a delta without regularisation. Lost to Flow-GRPO in a head-to-head. | **Highest implementation fit** (per-sample weight plus an L2 anchor in existing code; any reward) |
| E5 | **Adjoint Matching** (ICLR 25) | Stochastic-optimal-control fine-tuning | Memoryless noise schedule is *necessary*; regression on a lean adjoint | Better consistency and diversity; 3-run SEs | **Theoretical warning:** KL-RL on a deterministic ODE is biased or ineffective |
| E6 | **DNO** (CVPR 24) | Inference-time noise optimisation for **motion** | Backprop through a 10-step ODE to the initial noise; unit-normalised gradients | Motion editing, completion, denoising without retraining; ~3 min per batch | **High.** Training-free; needs a test-time objective |
| E7 | **Inference-time scaling** (2025), **ReNO** (NeurIPS 24), **TDS** (NeurIPS 23) | Inference-time search / optimisation / SMC | Best-of-N, zero-order search, one-step noise optimisation, twisted SMC | "Verifier hacking" documented; reward ensembles and regularisers mitigate it | Cheapest baselines; we have already measured verifier hacking (§1.3 point 4) |
| E8 | **MotionRL, ReinDiffuse, MotionCritic, EasyTune, MotionRFT, No-MoCap** | RL / reward fine-tuning of motion generators | PPO-Pareto; RL with physics rewards; critic-based ReFL; step-wise reward gradients; DDPO with a TMR reward | Gains on HumanML3D / KIT; MotionRFT also on a rotation-based model | Methods transfer, but **all rely on a learned evaluator (TMR, MotionCritic, MotionReward) that does not exist for ASL** |
| E9 | **DPOK**, **Diffusion-DPO**, **ReinFlow**, **SignLLM** | KL policy gradient; DPO with ELBO; learnable-noise flow RL; "RL" in SLP | – | ReinFlow stable at 1–4 steps. SignLLM's "RL" is −MSE-weighted batch prioritisation, not policy optimisation. | Genuine RL fine-tuning of a pretrained SLP generator appears absent *in my search* (not an exhaustive novelty claim) |

---

## 4. Methodological comparison: techniques vs SignSparK

### 4.1 Comparative literature matrix

| Paper | RL method | Main contribution | Stability mechanism | Potential application to SLP | Limitations |
|---|---|---|---|---|---|
| TOPR | Off-policy REINFORCE | Negatives without KL | Truncated IS | Offline reuse of bad samples, *if* a likelihood exists (SDE) | Continuous densities break the bound |
| CARFT | PPO + contrastive | Reference-anchored RL | InfoNCE to reference | Embedding-similarity reward to the reference motion | Hackable; weak evidence |
| SCoRe | Multi-turn REINFORCE | Avoid "behaviour collapse" | Staged KL + progress shaping | Analogy: RL on GF may collapse to the mean; generate→refine via keyframes | Verifier-dependent |
| DT-vitamin | TD3 + supervised | RL for supervised continuous generators | Supervised anchor; action-L2 KL | Closest structural analogue: CFM anchor − α·reward gradient | Needs a critic or differentiable reward |
| 1-shot RLVR | GRPO | RL elicits existing behaviours | Entropy | Run a best-of-N headroom diagnostic first (**done**: 12–14% oracle headroom) | Test-set selection |
| RA-RFT | GRPO + retrieval | Utility-based retrieval | Context quality | Retrieve train-set motion exemplars as anchors for GF | Placement of retrieved segments |
| ReLIFT | GRPO + selective SFT | Combine RL and SFT by difficulty | Scheduled SFT | Interleave CFM on worst clips; **avoid same-batch mixing** | Teacher demonstrations (we have references) |
| RLP | Info-gain RL | Verifier-free dense reward | EMA baseline | Reward for conditioning choices = loss reduction on the reference | Training-only; mean-biased |
| Flow-GRPO | GRPO on SDE | Online RL for flows | KL (closed form), group size | Direct fine-tuning with any reward | Compute; masked conditioning |
| DDPO / DPOK | PG on a diffusion MDP (+KL) | Denoising-as-MDP | PPO clip; KL | Same as Flow-GRPO (via SDE) | Exploitation |
| DRaFT / ReFL | Reward backprop | Efficient differentiable fine-tuning | Truncation K = 1 | One-step x̂₁ reward fine-tuning | Collapse without anchor |
| ORW-CFM-W2 | Reward-weighted CFM | Likelihood-free flow RL | W2 bound ‖v − v_ref‖² | Minimal code change | Weaker than Flow-GRPO (1 comparison) |
| Adjoint Matching | SOC regression | Unbiased tilted distribution | Memoryless noise | Principled differentiable-reward fine-tuning | Complexity |
| DNO / ReNO / search / TDS | None (inference-time) | Optimise or search the noise | Noise regularisers; verifier ensembles | **No-training improvement of GF** | Per-sample cost; verifier hacking |
| Motion RL works | PPO / DDPO / ReFL / step-wise | Learned perceptual or semantic rewards | KL, Pareto, critic loss | Templates for rewards, *if* an ASL evaluator existed | Evaluator dependence |

### 4.2 Technique transfer table

| Technique | Why it may help SignSparK | Required modification | Evidence needed |
|---|---|---|---|
| ODE→SDE + GRPO (Flow-GRPO, ReinFlow) | Stochastic policy with exact per-step likelihood, so any reward can be used | Handle keyframe clamping in the SDE; reverse time convention; LoRA / bottleneck | Marginal-preservation check under masks; reward that tracks quality |
| One-step reward gradient on x̂₁ (DRaFT-1 / ReFL) | Cheap (0.17 s/step measured); the model is trained for one-step prediction | Differentiable reward; L2 / KL anchor to frozen velocity | Anchor prevents articulation and diversity collapse |
| Reward-weighted CFM + W2 (ORW-CFM-W2) | Reuses the existing loss; reward need not be differentiable | Per-sample weights; frozen reference copy (bottleneck fits) | Stability over epochs; diversity |
| KL / anchor regularisation (all) | Prevents collapse and hacking (Flow-GRPO, DRaFT, ORW) | Closed-form velocity-space KL or ‖v − v_ref‖² | Diversity and articulation monitoring |
| Group-relative advantages (GRPO) | Normalises reward scale per text | G samples per text (G ≥ 24 per Flow-GRPO) | Variance at small G |
| Selective supervised interleaving (ReLIFT) | Anchors to reference where RL fails | Schedule CFM steps on worst clips | Must not mix every step on the same batch (collapse) |
| Inference-time noise optimisation / search (DNO, ReNO, ITS) | No training; targets GF directly | Test-time objective that is valid | **A verifier that tracks quality (BT fails, §1.3 point 4)** |
| Retrieved exemplar anchors (RA-RFT / SR-T2P) | Turns GF into an anchored regime without oracles | Text-based retrieval over train clips; temporal placement | Retrieval utility; does it beat GF? |
| Learned perceptual / semantic reward (MotionCritic / TMR) | Removes dependence on BT | **Must be built for ASL** (none exists) | Validation against humans or JPE |

### 4.3 Technically incompatible or low value (as-is) [I]

| Technique | Reason |
|---|---|
| Token-level PPO / GRPO (U2, U5, U7, U8, MotionRL) | No tokens. The SignSparK equivalent is the SDE denoising step. |
| TOPR as-is | Needs log π, and its proof assumes discrete trajectories |
| CARFT's LCS negatives | Token-specific |
| RLP "thoughts" | No latent-reasoning analogue |
| SCoRe multi-turn | Only meaningful if a generate→refine loop is introduced |

---

## 5. Potential RL formulations
These are candidates only; the Stage 4 decision has not been made.

| ID | Formulation | Action | Reward timing | Fits | Note |
|---|---|---|---|---|---|
| F1 | **Contextual bandit over a frozen sampler** | ε choice / γ / steps / keyframe or retrieval choices per text | Episode-level | Inference-time; controller | Cheapest. Its value hinges on a reward that tracks quality. |
| F2 | **K-step denoising MDP** (DDPO / Flow-GRPO) | Next latent of the SDE sampler | Terminal | LoRA / bottleneck fine-tuning | Principled for non-differentiable rewards; G samples per text |
| F3 | **One-step bandit with differentiable reward** (DRaFT-1 / ReFL on x̂₁) | Velocity prediction | Immediate | Bottleneck fine-tuning | Biased w.r.t. the tilted target (E5); needs an anchor |
| F4 | **KL-regularised SOC** (Adjoint Matching) | Control on a memoryless SDE | Terminal | Fine-tuning | Unbiased target; complex |
| F5 | **Reward-weighted regression** (ORW-CFM-W2) | Implicit | Episode-level | Fine-tuning | Simplest; collapse theory known |
| F6 | **Cross-stream / coordination formulation** | Hand (or face) generation conditioned on the generated body's motion features, e.g. derived keyframe timing | Episode-level | Controller over the existing keyframe interface (no architecture change) | Targets finding §1.3 point 3. Needs a coordination reward and a check that it is not trivially satisfied. |

---

## 6. Reward-design considerations

| Signal | Available when | Evidence | Risk |
|---|---|---|---|
| Rotation geodesic error to reference | Training only | Measured; oracle best-of-8 −12% | **One-to-many:** in GF, minimising error to one reference favours mean motion (SignSparK's own GF regression-to-mean, Stage 1). Must be paired with articulation and diversity terms. |
| Velocity / jerk vs reference | Training only | – | References corrupted by wrist flips in 13–17% of clips (Stage 2 Q3) |
| SignSparK-BT (BLEU/chrF, or log-likelihood) | Train and test (uses input text only) | GT ceiling BLEU-4 3.5; **within-text correlation with pose error ≈ 0; selection-level hacking +5–6 chrF without pose gain** [V] | **Not usable as a reward or selector as-is** |
| Articulation / diversity ratios | Train and test (statistics) | GF face 0.65× | Easy to game (jitter); a constraint, not an objective |
| Coordination statistics (arm–hand coupling, L/R asymmetry) | Train and test (reference-free) | GF ≈ chance vs GT 0.47; L/R 1.00 vs 0.70 | Proxies of quality only; gameable (e.g. copy body speed into hands) |
| Learned ASL text–motion evaluator (TMR-style, trained on How2Sign train) | Would need building | None exists | Training it is a new component (needs approval); evaluator validity must be shown first |
| SMPL-X joint-position errors (paper metric) | After licence | – | Needed for comparability and to validate rotation-space rewards |

Principles carried forward from the literature:
- Anchor every reward to the frozen model (KL, W2 or L2), as in Flow-GRPO, ORW and DT-vitamin.
- Use group-normalised or multi-reward (Pareto) aggregation instead of hand-weighted sums (MotionRL).
- Monitor diversity and articulation explicitly (Flow-GRPO, DRaFT and DDPO all show collapse or hacking).
- Validate the reward against an independent metric *before* RL, which §1.3 point 4 shows is not optional here.

---

## 7. Research gaps (evidence-based)

| # | Gap | Evidence |
|---|---|---|
| G1 | **No validated automatic evaluator of ASL signing quality** usable as a reward | BT fails within-text (§1.3 point 4); motion-RL relies on evaluators that do not exist for ASL (E8) |
| G2 | **Cross-stream coordination and handedness in multi-stream SLP generators** are unmeasured in the literature and broken in GF | §1.3 point 3: timing coupling ≈ chance; L/R activity identical |
| G3 | **RL for keyframe-conditioned (masked) flow models** | Flow-GRPO, Adjoint Matching and ReinFlow theory assume unconstrained states. SignSparK clamps keyframes every step. |
| G4 | **Genuine RL fine-tuning of pretrained SLP generators** | Only SignLLM's loss re-weighting found (within my search) |
| G5 | **Oracle length** | Every GF number uses ground-truth length; realistic T2P needs a length decision, an obvious controller variable |

---

## 8. Recommended directions with supporting evidence
These are recommendations only, not decisions. They are ordered by evidence strength and dependency.

1. **Gate: establish an evaluation signal that tracks quality before any RL.**
   - **Evidence:** §1.3 point 4 (BT selection improves BT, not poses; within-text Spearman ≈ 0).
   - **Options:**
     - (a) SMPL-X registration, so JPE / DTW-JPE can validate everything;
     - (b) train an ASL text–motion retrieval evaluator on How2Sign train, validated on dev against references and JPE;
     - (c) a small human rating study.
   - Without one of these, any RL "improvement" is uninterpretable.
2. **Focus regime: GF-T2P,** where measured deficits are large (BT −78%, face articulation 0.65, coordination at chance). KF2P headroom is small (BT −4%).
3. **First research question: coordination and handedness in GF (G2).**
   - Measurable reference-free targets exist; they are structural and largely ignored in prior work.
   - **Strong non-RL alternatives must be compared**, since they may solve it without RL:
     - (i) cascade the generated body's timing into hand keyframes through SignSparK's existing keyframe interface;
     - (ii) add a handedness/side input (an architecture change, requires your approval).
4. **Method family order to evaluate in Stage 4–5** (all fit 16 GB):
   - (a) **Inference-time baselines** (best-of-N, ReNO/DNO-style noise optimisation through 1–2 steps). These are mandatory comparators.
   - (b) **ORW-CFM-W2:** minimal change, any reward.
   - (c) **One-step reward gradient (DRaFT-1 / ReFL on x̂₁) with velocity-space anchor:** cheapest fine-tuning; needs a differentiable reward.
   - (d) **Flow-GRPO-style SDE + GRPO + KL on bottleneck/LoRA:** most principled for non-differentiable rewards; needs the masked-SDE check (G3) and G ≥ ~24 samples per text.
   - Adjoint Matching is the theoretically cleanest option if the reward is differentiable, at higher implementation cost.
5. **Keep the protocol safeguards from Stage 2:**
   - paired comparisons on identical clips and noise;
   - dev for selection (the BT model itself was selected on dev: dev ground-truth BLEU-4 4.26 = its stored best score 4.27);
   - test once;
   - flagged-clip sensitivity;
   - explicit oracle disclosure (ground-truth length in GF).

## 9. Limitations of this stage
- Metrics are rotation-space and BT only; JPE needs SMPL-X.
- GF uses ground-truth length.
- Best-of-N used 256 dev clips, one seed per candidate set.
- The contamination question is unresolved.
- External papers outside the core set were read at method level (E7–E9 abstracts and methods), not line by line.
- AlignProp was unavailable.
- The literature search was targeted (2 web searches plus citations), not systematic.

## 10. Decisions needed before Stage 4
1. Approve Stage 3.
2. **Evaluator path** (gate 1): SMPL-X registration now; and/or building an ASL text–motion evaluator (a new trained component); and/or a human rating study.
3. Whether **architecture changes** (e.g. a handedness input, cross-stream conditioning) are in scope as non-RL comparators, or only controller and fine-tuning approaches.
4. ~~The rest of the research prompt from §4.5.~~ **Resolved:** the full execution instructions were received on 2026-11-03.
5. Whether to run the licence-free SLERP KF2P check with the released B-T scorer (§1.6). It is optional and gives a paper-anchored sanity check of the released checkpoint.

---

## 11. Candidate non-RL comparators

Any RL result must beat or complement these under the same clips, seeds and length oracle.

| ID | Comparator | Targets | Needs architecture change? | Cost on A4000 | Status |
|---|---|---|---|---|---|
| N1 | Released checkpoint, default sampler (10 Euler steps) | All | No | Measured | Baseline [V] |
| N2 | Sampler settings: steps, CFG scale, seed | Articulation, face under-articulation | No | Minutes per setting | [Pr] |
| N3 | Best-of-N with a validated selector | All (bounded by oracle −12–14%) | No | N× sampling | [Pr]; the selector is the open problem |
| N4 | Noise optimisation (ReNO/DNO-style) through 1–2 Euler steps | Reward-specified | No | ~6–8 GB | [Pr] |
| N5 | Body→hand cascade: derive hand keyframes or timing from the generated body via the existing keyframe interface | Coordination (G2) | No | Sampling only | [Pr] |
| N6 | Supervised fine-tuning of the bottleneck on How2Sign train (same budget as RL) | Separates "more How2Sign training" from "RL" | No (weights only) | ~8 GB | [Pr]; essential control for any fine-tuning RL |
| N7 | Handedness/side input or cross-stream conditioning | Handedness, coordination | **Yes** | Retraining part of the hand stream | Awaiting your scope decision |
| N8 | SLERP between keyframes (KF2P only) | KF2P reference | No | Trivial | [Pr], paper's own baseline |

## 12. Unresolved risks

| # | Risk | Effect | Current mitigation |
|---|---|---|---|
| K1 | No validated quality evaluator (G1) | RL improvements uninterpretable; reward hacking undetectable | Evaluator gate (§8.1); BT excluded as reward |
| K2 | Checkpoint provenance: How2Sign split usage and test contamination unknown [A][V] | Absolute test numbers may be optimistic | Paired comparisons only; dev for selection; disclosed. No issue raised with the authors without your permission |
| K3 | Released checkpoint ≠ paper's model [A] | No paper-anchored comparison | R10 labelling |
| K4 | One-to-many text→sign | Reference-error rewards push toward mean motion | Pair with articulation and diversity constraints; human or learned evaluator |
| K5 | Corrupted references (wrist flips in 13–17% of clips, Stage 2) | Corrupt reward targets and smoothness metrics | Flagged-clip sensitivity analysis |
| K6 | Oracle length in all GF results | Optimistic GF numbers | Disclosed; length is a candidate controller variable (G5) |
| K7 | Masked (keyframe-clamped) sampler vs SDE-RL theory (G3) | Flow-GRPO / Adjoint Matching assumptions may not hold in KF2P | Focus GF (no clamping); verify before use |
| K8 | 16 GB memory | Rules out full fine-tuning with a frozen reference | Bottleneck/LoRA, few-step gradients (§1.4) |
| K9 | Single seed in the baseline and best-of-N | CI covers clips, not seeds | Multi-seed runs in Stage 6 |

## 13. Decision log (Stage 3)

| # | Problem | Decision | Reason | Alternatives | Evidence | Risks | Validation | Status |
|---|---|---|---|---|---|---|---|---|
| D3.1 | Need a baseline to measure against | Use released checkpoints, official sampler, 10 steps, seed 102, both regimes, dev + test | Only available model; paper's model not released | Paper numbers (not comparable, R10) | §1, §1.6 | Single seed | Re-run with more seeds in Stage 6 | Done (measurement); protocol not final |
| D3.2 | Evaluate without SMPL-X | Rotation-space geodesic error, articulation, speed, jerk, coordination | Licence on hold; data is rotations | Wait for SMPL-X | §1.2 | Not comparable to JPE | Correlate with JPE once licensed | Done; [Pr] as interim metric |
| D3.3 | Is BT usable as a reward or selector? | **No, as-is** | Within-text Spearman ≈ 0; BT selection +5–6 chrF with no pose gain | BT log-likelihood; BT ensembles | §1.3 point 4 | Could reject a signal that is useful at corpus level | Re-test if a validated evaluator appears | [Pr] (consistent with your instruction) |
| D3.4 | Which regime to target | GF-T2P | Large measured deficits; KF2P headroom small | KF2P | §1.2–1.3 | GF one-to-many inflates reference error | Evaluator gate | [Pr] |
| D3.5 | First research question | Cross-stream coordination and handedness | Measured at chance; structural cause in code | Face articulation; semantics | §1.3 point 3 | Proxy metrics gameable | Compare with N5/N7 | [Pr] |
| D3.6 | Paper reproduction claims | None claimed; R10 labelling | Different checkpoint and B-T | — | §1.6 | — | — | Done |
| D3.7 | Compute | Stay on local A4000; no rental | Recommended families fit in 16 GB | Rent A100 | §1.4 | Full fine-tuning infeasible | Measured | [Pr] |
| D3.8 | Method families to carry into Stage 4 | F1–F6 as candidates, no selection | See §4–5 | PPO token MDP (rejected, §4.3) | §4–5 | — | Stage 4 audit | Candidates only |
