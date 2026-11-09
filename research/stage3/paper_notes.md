# Stage 3 working notes: per-paper extraction (full-text reads)

## Format

Each paper is read from its full extracted text (scratchpad/txt). Notes below cover:
- the problem, model, initialisation and RL algorithm;
- the state, action, reward and objective;
- exploration, stability, training procedure and evaluation;
- ablations, limitations and compute;
- **transfer to SignSparK**.

Evidence labels:

| Label | Meaning |
|---|---|
| [P] | Stated in the paper |
| [I] | My inference |

---

## U1. Tapered Off-Policy REINFORCE (TOPR)

**Citation:** Le Roux, Bellemare et al., NeurIPS 2025 (Mila / Reliant AI).

**Problem** [P]
- Stable off-policy RL fine-tuning of LLMs that uses both positive and negative samples without a KL penalty.

**Model and initialisation** [P]
- Llama 3 8B Instruct (also DeepSeek-R1 8B distil). Starts from the instruction-tuned base; no separate SFT stage.

**Algorithm** [P]
- REINFORCE family. Gradient per sample: stop-grad(α) · R · ∇log π(τ).
  - Positive reward: α = 1 (pure SFT on positives).
  - Negative reward: α = clip(π(τ)/µ(τ), 0, 1), i.e. truncated importance sampling.
- General form: Eq. 3 with truncation limits (a±, b±). TOPR canonical setting: a+ = b+ = 1, a− = 0, b− = 1.

**MDP view** [P]
- State: prompt plus prefix (tokens). Action: next token. Trajectory = full response.
- Reward: sequence-level, binary ±1 (answer correctness); no per-token reward.

**Objective** [P]
- Lower bound on J(π) through a "taper" function ρ (Eq. 6).
- Prop. 3.1: a REINFORCE baseline c acts as KL(µ‖π) regularisation towards or away from µ.
- Prop. 3.2: the objective is bounded above iff a− = 0.
  - **The proof uses π(τ) ≤ 1 (discrete trajectories).**

**Exploration** [P]
- Sampling from µ at T = 1, top-k 500; n = 16 (GSM8K) or 32 (MATH) candidates per prompt.

**Stability mechanisms** [P]
- Truncated IS on negatives; no KL; gradient clipping 1.0; loss divided by sequence length.
- The baseline / effective positive proportion is the key knob: the optimum is 10–20% effective positives.

**Training** [P]
- Fully offline single iteration: generate a dataset from µ = the start model, then one epoch.
- Multi-iteration variant with "Anna Karenina sampling" (keep the first positive, fill with negatives).

**Evaluation** [P]
- GSM8K / MATH-500 Pass@1 and Maj@K.
- Bootstrap CIs (2 SE) over resampled generations.
- Baselines: PPO (ε = 0.2), DPO, naive REINFORCE, TIS, positives-only SFT.

**Ablations** [P]
- TOPR vs TIS across effective positive rates.
- Positives-only vs all samples.
- Untruncated IS, which becomes unstable with clip 100 and 60% negatives.
- Learning-to-verify; query-expansion IoU improved only 35.03% → 35.83%.

**Limitations** [P]
- µ is always the start-of-iteration model; truly offline µ ≠ π "poses numerical challenges".
- Compute was not tracked.
- Code is proprietary.

**Compute** [P]
- Single H100 node, batch 1 per GPU, Adafactor, lr 5e-7.

**Transfer to SignSparK** [I]

What transfers:
- The idea of using negatives with *truncated* weights.
- The "baseline = dataset-composition knob" insight.
- Offline generate-then-train iterations. These suit an expensive sampler: SignSparK sampling is cheap (10 Euler steps), but rewards may be expensive.

What does **not** transfer directly:
1. **TOPR needs log π(τ).** SignSparK's sampler is a deterministic ODE given the initial noise, so there is no per-step likelihood. The exact likelihood via the ODE requires a divergence integral (costly, high-variance). A stochastic SDE re-formulation would be needed (cf. Flow-GRPO, external) to get Gaussian per-step log-probs.
2. **Prop. 3.2's boundedness relies on π(τ) ≤ 1.** This is false for continuous densities, so the positive-example SFT term (weight µR log π) is unbounded above in continuous action spaces. Variance can collapse towards a delta (mode collapse). Extra regularisation (KL or a fixed noise level) becomes necessary again.
3. **Binary rewards vs continuous rewards.** Our rewards would be continuous (pose error, BT score). The positive/negative split requires a baseline choice, which TOPR shows is critical.

Takeaway: useful conceptually for an *offline, sample-reuse* regime and for using bad generations. It needs a likelihood-bearing stochastic policy, plus re-derived stability for continuous actions.

## U2. CARFT: Contrastive Annotated-CoT Reinforced Fine-Tuning

**Citation:** Zhu, Liu et al., EMNLP 2025.

**Problem** [P]
- RL fine-tuning (ReFT/PPO) ignores annotated CoTs and suffers model collapse.
- SFT over-fits the single annotated CoT.

**Model and initialisation** [P]
- CodeLlama-7B and Qwen2.5-7B-Instruct (+14B).
- SFT warm-up for 4 epochs (lr 1e-5), then RL (lr 3e-7).

**Algorithm** [P]
- PPO with GAE (λ = 1, γ = 0.95, ε = 0.2, value-loss weight 5, U = 2), plus a token-level KL penalty to the reference (β = 0.05).
- Loss: L = L_RL + c·L_contrastive, with c = 1e-3.
- One on-policy sample per question per step (ReFT-style).

**MDP view** [P]
- State: question plus generated prefix. Action: token. Value head V_φ.

**Reward** [P]
- 1 if correct, 0 otherwise, 0.1 partial reward if a numeric answer can be extracted (from ReFT).
- "Embedding-enhanced partial reward" (Eq. 10): r = ⟨e_annot, e_rollout⟩·0.1 + 0.2 for wrong answers, giving a range of [0.1, 0.3].

**Contrastive signal** [P]
- CoT embedding e = Σ softmax(V_φ) ⊙ proj(H): value-weighted pooled token states, projected to 64-d.
- Positive signal: masked InfoNCE (τ = 0.2) pulling the rollout embedding toward the annotated-CoT embedding of the same question. Masked to correct rollouts only.
- Negative signal: LCS-based split of wrong rollout vs annotated; aligns the shared part and pushes away the non-shared part.

**Stability** [P]
- The contrastive auxiliary loss acts as a regulariser anchored to annotated (reference) data.
- PPO clipping, KL to the reference.

**Evaluation and results** [P]
- SVAMP and GSM8K accuracy; baselines SFT, ReFT, Dr.GRPO (G = 2).
- Qwen GSM8K: SFT 80.67 / ReFT 66.11 (collapse) / CARFT 84.31.
- CodeLlama SVAMP: CARFT 64.2 vs Dr.GRPO 63.7 vs ReFT 62.5. Dr.GRPO takes 24.5 h vs CARFT 17.0 h on 8×H100.

**Ablations** [P]
- Positive vs negative signal: 64.8 vs 62.9 vs ReFT 62.5.
- Coefficient c ∈ {5e-4, 1e-3, 1.5e-3}.
- Partial reward: +0.5.
- Batch size 64 vs 96.

**Limitations and caveats** [P/I]
- Single runs; no CIs or seeds reported [I].
- Several gains are 0.4–1.7 points with no variance estimate [I].
- "Up to 10.15%" is the relative average vs ReFT including ReFT's collapse run [I].
- Compute: 8×H100-80GB, DeepSpeed ZeRO-3.

**Transfer to SignSparK** [I]

What transfers:
- The *structural idea*: we have exactly one annotated reference per input. The reference pose sequence plays the role of the annotated CoT. The concern "pure reward optimisation drifts and collapses, so anchor to the reference with an auxiliary supervised or contrastive term" maps directly. SignSparK's own CFM loss on train data is a natural anchor, much like CARFT keeps annotated data in the loop.
- **Embedding-similarity partial reward → a dense reward in a learned motion-embedding space.** For example, use the SignSparK-BT encoder or a contrastive text–motion embedding. This gives graded credit instead of sparse BLEU.

Caveats:
- Embedding rewards are hackable: they reward embedding similarity, not correctness.
- CARFT's own evidence is weak (no variance).
- Text–motion embedding models for ASL do not exist off the shelf.

What does not transfer:
- The LCS split (token sequences).
- The value-weighted pooling (no value head in a flow model; we could pool over frames instead).

## U3. SCoRe: Training LMs to Self-Correct via RL

**Citation:** Kumar, Zhuang et al., Google DeepMind, ICLR 2025.

**Problem** [P]
- Intrinsic self-correction: a second attempt that improves the first without external feedback.
- SFT on correction traces fails in two ways: (1) distribution shift between offline first attempts and the model's own; (2) **behaviour collapse**, where the model learns the best first attempt and makes no edits.

**Model and initialisation** [P]
- Gemini 1.5 Flash (MATH) and Gemini 1.0 Pro (code); Gemma-2 2B in the appendix. Starts from the base model.

**Algorithm** [P]
- REINFORCE with a KL penalty to a fixed reference (RLOO-style, Ahmadian et al. 2024). Two-turn episodes; γ = 0 (instantaneous reward).

**MDP view** [P]
- State: problem plus previous attempt(s) plus instruction. Action: a whole response, per turn.
- Reward: binary oracle correctness. Used only in training; not available at test time.

**Stage I** [P]
- Maximise second-attempt reward while a *strong* KL (β2 = 0.1–0.25) keeps the first attempt at the base model.
- Purpose: decouple the attempts, producing an initialisation less prone to collapse.

**Stage II** [P]
- Jointly maximise both attempts.
- Shaped bonus on attempt 2: α·(r(y2) − r(y1)), with α = 10. This rewards *progress* and heavily penalises correct→incorrect flips.

**Stability** [P]
- KL β1 = 0.01, plus the stage split, plus progress shaping.
- Mixing offline base-model first attempts into Stage II helps.

**Evaluation** [P]
- MATH500: Acc@t2 64.4%, Δ(t1, t2) +4.4%, vs base −11.2%.
- HumanEval: Δ +12.2%.
- MBPP-R offline repair: 60.6%.
- Ablations: no Stage I → Δ 2.2; no shaping → Δ 2.6; STaR instead of RL → worse; no online turn-1 samples → Δ 0.2.
- Greedy evaluation; checkpoint chosen by highest training reward.

**Limitations** [P]
- Two separate runs (stages).
- Plateau beyond ~2 turns.
- Closed models; no seeds or CIs reported for the main tables.

**Compute** [P]
- Not stated (Gemini infrastructure). Batch 512, 3,000 steps, lr 5e-6 (MATH).

**Transfer to SignSparK** [I]

1. **Behaviour collapse → regression-to-the-mean.** RL can find a degenerate solution that scores well on the training reward but lacks the desired behaviour. For GF-T2P, a reward like DTW-JPE or MSE is *minimised by near-average poses*, which the authors themselves report for GF-T2P [A, issue #5]. RL with such a reward would amplify under-articulation. This directly motivates rewards or regularisers that penalise mean-collapse (articulation and diversity terms).
2. **Progress-style shaping** (reward the improvement over a baseline sample) maps onto an *improvement-over-reference-sampler* reward, or onto refinement. SignSparK is a natural *refiner*: its keyframe interface lets a first-pass output be re-anchored and regenerated, which is a two-step generate→refine structure. This could be a "multi-turn" formulation, but whether refinement helps is an **open hypothesis**.
3. **Strong KL on part of the behaviour** (Stage I) corresponds to anchoring the pretrained flow's velocity field (or its CFM loss) while optimising a small controller or adapter.

What does not transfer:
- Turn-structured text prompts.
- The binary verifier. No verifier exists for signing correctness.

## U4. RL Gradients as Vitamin for Online Fine-tuning Decision Transformers

**Citation:** Yan, Schwing, Wang, NeurIPS 2024.

**Problem** [P]
- Online fine-tuning of Decision Transformers (ODT) fails when pretrained on low-return data.
- The DT learns ∂a/∂RTG, but local improvement needs ∂RTG/∂a.
- Theory, using Brandfonbrener et al.'s bound: conditioning on an out-of-distribution high RTG degrades real return. 1/α_f grows as Ω(RTG²) for discrete RTG and Ω(RTG^1.5) for Lipschitz-continuous RTG.

**Model and initialisation** [P]
- ODT: 4 layers, 4 heads, ~13M params. Offline pretraining by supervised action regression, then online fine-tuning.

**Algorithm** [P]
- Actor loss = supervised MSE to the dataset action − α·Q_φ1(s, µ_DT(·)).
- α ∈ {0, 0.1} offline; α = 0.1 online.
- TD3 critics: twin Q, target policy smoothing, delayed updates (critic 600 / actor 300 steps per rollout).

**MDP view** [P]
- Continuous control (D4RL: Adroit, AntMaze, MuJoCo, Maze2D).
- Deterministic policy; MLP critic on the current (s, a) only (a "reflexive" critic averaging over context lengths). A recurrent LSTM critic was unstable.

**Stability** [P]
- TD3 tricks.
- LayerNorm in critics for hard environments.
- The supervised loss acts as a behaviour anchor.
- Optional KL-like regulariser c0·‖a − a_old‖² for deterministic policies (c0 = 0.05). It fixes forgetting on expert data but can hinder improvement from low-return data.

**Exploration** [P]
- Online rollouts; JSRL and RTG curriculum were tried and failed.

**Evaluation** [P]
- D4RL normalised return; 5 seeds; mean ± std; rliable bootstrap (10k).
- MuJoCo average 88.38 (TD3+ODT) vs 55.14 (ODT), 87.64 (pure TD3), 68.52 (TD3+BC).
- Fails on AntMaze-large, where IQL is best.

**Ablations** [P]
- RL gradient type, Appendix C:
  - TD3 ≈ SAC > AWAC, AWR.
  - **PPO "does not work at all" with the DT, because of importance ratios with tiny denominators under off-policy-ness.**
- α, context length, LayerNorm, recurrent critic, architecture (TD3+BC with the transformer works but is worse).

**Limitations** [P]
- Theory relies on strong assumptions.
- Extra compute ~20% over ODT.

**Compute** [P]
- One RTX 2080Ti; 6–8 h per MuJoCo run.

**Transfer to SignSparK** [I] (most structurally relevant of the uploaded papers)

1. **The structural analogy is close.** Both are a pretrained transformer-style generator trained only by supervised regression, producing **continuous actions deterministically**. SignSparK given the noise is deterministic, like µ_DT, and it emits continuous pose vectors. The paper's evidence is:
   - mixing a supervised anchor with a deterministic-policy RL gradient (∂Q/∂a, or ∂R/∂a if R is differentiable) works;
   - **PPO-style importance ratios are fragile in this regime.**

   This argues for **reward-gradient / DPG-type updates or reward-weighted regression over PPO** for direct fine-tuning. It is a hypothesis to test.
2. **Supervised + RL mixing** (L = L_sup − α·Q) maps directly to **L_CFM(+recon, vel) − α·R(x̂₁)** on SignSparK. The CFM loss on train data is the anchor.
3. **The ‖a − a_old‖² regulariser** maps to an L2 penalty to the frozen model's prediction: a KL proxy for deterministic generators.
4. **Differences**:
   - Our "episode" is a one-shot generation: a contextual bandit over the whole sequence, or K ODE steps. It is not a long-horizon TD problem, so a critic Q(text, motion) is only needed if the reward is non-differentiable (e.g. BT BLEU).
   - Their critic is learned online from environment returns. Ours would learn from reward-model outputs, so the hackability of a learned critic adds risk.

## U5. RL for Reasoning in LLMs with One Training Example (1-shot RLVR)

**Citation:** Wang et al., NeurIPS 2025 (UW / Microsoft).

**Problem** [P]
- How much data does RL with verifiable rewards need?
- Finding: one example can match a 1.2k-example dataset.

**Model and initialisation** [P]
- Qwen2.5-Math-1.5B/7B, Llama-3.2-3B-Instruct, DeepSeek-R1-Distill-Qwen-1.5B. Starts from base models.

**Algorithm** [P]
- GRPO in verl: group-normalised advantages, 8 samples per prompt.
- KL β = 0.001; entropy bonus coefficient −0.001; rollout temperature 0.6; batch 128.
- PPO also works.

**MDP and reward** [P]
- Token MDP. Binary outcome reward (answer match); no format reward except as a baseline.

**Data selection** [P]
- "Historical variance score": the variance over epochs of per-example training accuracy.

**Key findings** [P]
- π1 alone: MATH500 36.0 → 73.6; 6-benchmark average 17.6 → 35.7, versus 35.9 with the 1.2k subset.
- **Post-saturation generalisation:** test accuracy keeps improving long after training accuracy saturates. Eventually the model overfits, producing gibberish on the training example while test outputs stay normal.
- Ablations:
  - The gain comes mainly from the policy-gradient loss, not weight decay or KL (so it is not grokking).
  - The entropy bonus adds +4.0 on MATH500.
  - **Entropy-only training (no reward) still improves results**, via format correction.
- Label robustness: a slightly wrong label is fine. A wrong-but-overfittable label is worse than an unguessable one.

**Evaluation** [P]
- Six maths benchmarks, avg@8 for the small ones.
- The checkpoint is selected by best test performance per benchmark: "best model performance on each benchmark separately".
  - **[I] This is test-set model selection, which inflates the reported numbers.**
- A format-reward baseline is included to separate format fixing from reasoning gains.

**Limitations** [P/I]
- The base models are strong (Qwen-Math), so "latent capability elicitation" may not hold for weaker models. Llama gains are small and unstable.
- The format confound is acknowledged.

**Transfer to SignSparK** [I]

1. **The "elicitation, not new capability" lesson.** RL gains here come largely from re-weighting behaviours the base model *already* produces with some probability. For SignSparK, the analogue question is whether the pretrained sampler already produces good samples sometimes. This can be measured directly: generate N candidates per clip and look at the spread of the evaluator score.
   - If best-of-N ≫ mean, there is headroom for RL (or simply reranking) to exploit.
   - If not, RL fine-tuning has little to amplify.

   **This is a concrete pre-RL diagnostic I recommend running.**
2. **Format-correction confound → "easy-metric" confound.** Gains can come from fixing superficial properties rather than the target capability. The SLP analogue is improving smoothness or jitter statistics without improving sign correctness. We need a control baseline analogous to their format-reward run, for example a smoothing-only post-filter.
3. **Test-set checkpoint selection is a methodological flaw to avoid**, consistent with our E1/E3.
4. **Entropy / exploration.** For a continuous flow there is no token entropy. Exploration comes from noise level, or SDE stochasticity in Flow-GRPO-style methods (to be verified in the external literature).

## U6. RA-RFT: Learning to Reason by Analogy via Retrieval-Augmented RFT

**Citation:** Xiao et al., Findings of EMNLP 2026 (Meta / Rice). Read from the complete ACL Anthology version; the uploaded `2026.findings-emnlp.1353.pdf` was truncated, but the separate preprint file was complete.

**Problem** [P]
- RLVR is bounded by parametric knowledge; hard problems give sparse rewards.
- Similarity-based RAG retrieves surface-similar but reasoning-irrelevant context.

**Method** [P], in three stages:
1. **Gold-relevance distillation.** A GPT-4o judge labels (query, trace) pairs for "transferable reasoning pattern". Labels are restricted to the same coarse problem type for tractability.
2. **Reasoning-aware retriever.** Reason-ModernColBERT fine-tuned with InfoNCE, τ = 0.05.
3. **GRPO with the top-1 retrieved trace in the prompt.** 16 rollouts, no KL, AdamW lr 1e-6, full-parameter training on 64 H100s, max length 32k.

**MDP view** [P]
- Token MDP; the state is augmented by the retrieved context. Binary outcome reward. The update conditions on the retrieved context, which keeps the importance-sampling identity consistent.

**Results** [P]
- Qwen3-1.7B: average over 4 benchmarks 47.4 vs GRPO 43.3 vs QuestA 43.3.
- Qwen3-4B: 67.0 vs 64.4.
- Step-0 accuracy is *lower* with retrieved context (a distraction effect); RL teaches the model to use it.

**Ablations** [P]
- RA-SFT ≈ SFT (40.5 vs 39.7), so retrieval helps only under RL.
- Retriever quality matters: a random trace gives 37.6, below GRPO.
- Per-problem spread across retrieved contexts is large.

**Limitations** [P]
- Needs a judge annotation pass and a retriever.
- Maths only.
- **Evaluation is avg@32 with temperature 1. No seeds or CIs; single training run per configuration** [I].

**Transfer to SignSparK** [I] (conceptually very relevant)

1. **Retrieval augmentation already exists in SLP, but not for How2Sign.** SignSparK's SR-T2P is literally retrieval-augmented generation: retrieve dictionary keyframes, then generate. It does not exist for How2Sign, which has no glosses or dictionary (Stage 2).
   - An RA-RFT-like idea for How2Sign: **retrieve train-set motion exemplars** (segments or keyframes from clips whose translations share content) and supply them as keyframe conditioning for GF-T2P.
   - Then learn, by feedback from an evaluator, *which* exemplars help ("utility, not surface similarity").
   - This turns GF-T2P (no anchors, regression to the mean) into an anchored regime without oracle keyframes. **[H] Promising but unverified.**
   - Obstacles: temporal placement of retrieved segments within a new sentence; signer and style mismatch; lexical-to-sign mismatch in English (no glosses).
2. **"Retrieval helps only under RL, not SFT."** If true for SLP, a controller or fine-tune that learns to *use* retrieved anchors could beat naively inserting them.
3. **Context quality drives reward density.** Retrieval quality is a first-class variable; random exemplars hurt.

## U7. ReLIFT: Learning What RL Can't, via Interleaved Online Fine-Tuning

**Citation:** Ma et al., ICLR 2026 (PKU). Read from the complete arXiv v3; the uploaded PDF was truncated.

**Problem** [P]
- RLVR mostly reinforces existing behaviours and cannot solve questions beyond the base model's capability.
- SFT can add new patterns but degrades easy questions and generalises worse out of distribution.

**Analysis** [P]
- Questions bucketed by base-model accuracy over 8 samples (easy, medium, hard, hardest).
- RL improves easy and medium questions without regressions. SFT wins on the "hardest" (0/8) questions but regresses some easy ones.

**Method** [P]
- GRPO for general training.
- Hardest questions (rollout accuracy = 0) get verified high-quality CoTs from a stronger model (DeepSeek-R1), placed in an FT buffer.
- When the buffer reaches the batch size M, take one SFT step: cross-entropy plus a small entropy bonus, α = 1e-4.
- The interleaving frequency is adaptive: more frequent early.

**Evaluation** [P]
- Qwen2.5-Math-7B: overall 52.6 vs RL 46.9, SFT 49.0, LUFFY 50.9, SFT→RL 50.8.
- Uses 8k demonstrations and 52×8 GPU-hours, vs 46k and 57–113×8 for the alternatives.
- Also on Qwen2.5-Math-1.5B, Qwen2.5-7B and Llama-3.1-8B (small gains on Llama).
- avg@32 / avg@8 at temperature 0.6.

**Ablations** [P]
- ReLIFT(all), with FT after every RL step on the same batch: **collapses to 23.8**, attributed to conflicting objectives.
- Uniform schedule 49.1; random (non-hardest) buffer 45.5.
- The entropy coefficient is sensitive.

**Limitations** [P/I]
- Requires a stronger teacher for demonstrations.
- **No seeds or CIs** [I].
- Gains over the best hybrid are ~1.7 points [I].

**Transfer to SignSparK** [I]

1. **A ready-made demonstration for every training input.** Unlike LLM RL, every How2Sign training clip has its reference motion, so SFT "demonstrations" are free. ReLIFT's principle then becomes: **apply RL updates where the model is already competent, and supervised CFM updates where it fails badly** (lowest evaluator score).
   - This is a principled way to schedule the anchor loss: *selective* rather than uniform supervision.
   - Caveat: the CFM loss *is* the pretraining objective, so "learning new knowledge" just means continued supervised training on the hard clips.
2. **Warning from ReLIFT(all): mixing the RL and supervised losses on the same batch every step collapsed training.** This is a concrete risk for the "L_CFM − α·R" mixing idea from U4. The weighting and scheduling must be tuned and monitored.
3. **Difficulty bucketing from multi-sample accuracy** maps to bucketing clips by best-of-N evaluator score. This links to the diagnostic recommended under U5.

## U8. RLP: Reinforcement as a Pretraining Objective

**Citation:** Hatamizadeh, Akter et al., NVIDIA, ICLR 2026. Read from the complete arXiv v2; the uploaded PDF was truncated.

**Problem** [P]
- Bring RL-style exploration into pretraining on ordinary text without verifiers.

**Method** [P]
- Before predicting token x_t, sample a CoT c_t from the same model.
- Reward = information gain r(c_t) = log p_θ(x_t | x<t, c_t) − log p̄_φ(x_t | x<t), where p̄_φ is an EMA "no-think" teacher (τ = 0.999, lazily initialised).
- Dense, verifier-free, computed under teacher forcing.
- Group-relative advantages with an unbiased inclusive-mean correction G/(G−1).
- PPO-style clipped surrogate on thought tokens only.
- No NTP loss term.

**Theory** [P]
- The expected reward equals the cross-entropy reduction versus the EMA baseline (Prop. 1).
- The CoT-conditioned objective lower-bounds the marginalised improvement (Prop. 2).
- The EMA lag is deliberately chosen to avoid reward collapse or hacking: a frozen baseline drifts; one with no lag gives zero reward.

**Results** [P]
- Qwen3-1.7B-Base: overall 30.3 → 36.0 (CPT 30.9). After identical SFT + RLVR: 42.5 vs 39.9.
- Nemotron-Nano-12B: 42.8 → 61.3, using 250M tokens.
- Beats RPT under token- and FLOP-matched comparisons.
- Gains across corpora: 7–9% for web, academic and maths text.

**Limitations** [I]
- Applied to *one token per document* in experiments.
- Benchmark averages; no seeds reported.
- Very large compute (NVIDIA scale).

**Transfer to SignSparK** [I]
- **The information-gain idea transfers as a dense, verifier-free, reference-based reward for *conditioning decisions*.**
  - Example: a controller chooses which keyframes or exemplars to supply (action). The reward is the reduction in SignSparK's own reconstruction or CFM error on the reference clip, relative to an EMA or no-conditioning baseline.
  - It is computable at training time from data we have, and needs no external evaluator.
- **Caveats:**
  1. It measures fit to the single reference, so it inherits the regression-to-mean bias of likelihood-type objectives for GF-T2P.
  2. It must never feed reference information into inference-time inputs (leakage). It is a training reward only.
  3. RLP's own success concerns *latent reasoning*, which has no direct SLP analogue.
- The **EMA-baseline design** (a lagged reference to stop reward hacking) is a transferable stabiliser for any relative reward.

---
# External literature (full-text reads; arXiv IDs verified via the arXiv API on 2026-11-02)

## E1. Flow-GRPO: Training Flow Matching Models via Online RL

**Citation:** Liu et al., NeurIPS 2025, arXiv 2505.05470v5.

**Problem** [P]
- Online policy-gradient RL for *deterministic* flow-matching samplers. There is no stochasticity for exploration, and no tractable per-step likelihood.

**Method** [P]
- **ODE→SDE conversion** that preserves the marginals at all t (Eq. 7–9). For rectified flow:
  - x_{t+Δt} = x_t + [v_θ + σ_t²/(2t)·(x_t + (1−t)v_θ)]Δt + σ_t√Δt·ε
  - σ_t = a·√(t/(1−t)), with a = 0.7.
  - The paper's convention is t = 1 noise, t = 0 data.
- Each denoising step is then an isotropic Gaussian policy with **closed-form KL to the reference**:
  - KL = Δt/2·(σ_t(1−t)/(2t) + 1/σ_t)²·‖v_θ − v_ref‖².
- **MDP** (from DDPO):
  - state (prompt, t, x_t); action x_{t−1}; deterministic transition;
  - reward only at the final step.
- **GRPO** group-normalised advantages, PPO clip, KL β. G = 24 samples per prompt.
- **"Denoising Reduction":** 10 SDE steps for training rollouts, 40 at inference.
- LoRA r = 32, α = 64.

**Results** [P]
- SD3.5-M on GenEval: 0.63 → 0.95.
- OCR: 0.59 → 0.92.
- PickScore improves.
- Quality metrics on DrawBench preserved **with KL**. Without KL: quality degrades (GenEval/OCR) or **diversity collapses** (PickScore: "different seeds producing nearly identical results").

**Ablations** [P]
- Noise level: a = 0.1 under-explores; > 0.7 gives no gain; too high fails.
- Group size: G = 6 or 12 collapsed; G = 24 stable.
- Different initial noise per rollout helps.
- Beats SFT-on-best, online/offline Flow-DPO, Flow-RWR (no gain), DDPO (slower, later collapse), ReFL (reward backprop) and ORW-CFM-W2.

**Compute** [P]
- 24 A800 GPUs; hundreds to thousands of GPU-hours per task.

**Limitations** [P]
- Reward design for video and temporal tasks is open.
- Multi-reward balancing.
- Scalability.
- KL slows training; occasional hacking.

**Compatibility with SignSparK** [I] (high)
- SignSparK *is* rectified flow with a linear path and velocity prediction (verified in code; time convention reversed, t = 0 noise). The ODE→SDE conversion applies directly to its velocity field, with σ_t re-parameterised for the reversed time.
- **Keyframe masking:** SignSparK re-imposes keyframes at each step. The SDE noise would act only on non-keyframe entries. Whether marginal preservation holds under this masked conditioning is **plausible but unproven** (needs derivation or empirical check).
- The **closed-form KL in velocity space** is an attractive anchor to the frozen pretrained model.
- **Group sampling G per text:** sampling is cheap for us (Stage 1 measurement: 16 clips × 10 steps in 2.7 s on an A4000). The cost is in backprop through the 0.83B U-Net, so LoRA (as they did) or partial fine-tuning is required on 16 GB.
- **Their evidence that small groups collapse** implies we need large G. Fixed compute then means fewer clips per step.

## E2. DDPO: Training Diffusion Models with RL

**Citation:** Black, Janner, Du, Kostrikov, Levine, ICLR 2024, arXiv 2305.13301v4.

**Method** [P]
- The denoising chain is formulated as a T-step MDP: s_t = (c, t, x_t), a_t = x_{t−1}, deterministic transition, reward r(x_0, c) only at the end.
- Each step is an isotropic Gaussian, so exact per-step log-likelihoods are available.
- Two variants: DDPO_SF (REINFORCE) and DDPO_IS (importance-sampled with PPO clip).
- Contrasted with **RWR** as a one-step MDP (reward-weighted denoising loss). RWR is "not theoretically justified" because the diffusion loss is only a variational bound.

**Rewards** [P]
- JPEG (in)compressibility, LAION aesthetic predictor, and VLM prompt alignment (LLaVA description + BERTScore).

**Results** [P]
- SD v1.4: DDPO_IS > DDPO_SF > RWR variants on all tasks.
- Generalises to unseen prompts.
- **Reward exploitation is visible:** "aesthetic" → stylised artwork; incompressibility → high-frequency noise; prompt alignment → cartoon style. Over-optimisation is explicitly *not* studied.

**Limitations** [P]
- No KL / overoptimisation study.
- Narrow prompt sets.

**Compute** [P]
- TPUs (TRC); not detailed in the main text.

**Transfer to SignSparK** [I]
- The **canonical MDP for whole-sequence iterative generators**: the decision unit is the denoising step, not the frame. This supports Stage 1 observation S1-D6.
- **The RWR comparison is directly relevant.** SignSparK's own training loss is a regression on the velocity field, so "reward-weighted CFM" is RWR-style and inherits its theoretical weakness. In Flow-GRPO's comparison, RWR also gave no gain.
- **The reward-exploitation examples are a direct warning for us.** An SLP smoothness or jerk reward is exactly the kind of "compressibility" objective a policy can satisfy degenerately, e.g. by freezing motion, unless other terms prevent it.

## E3. DRaFT: Directly Fine-Tuning Diffusion Models on Differentiable Rewards

**Citation:** Clark, Vicol, Swersky, Fleet, ICLR 2024, arXiv 2309.17400v2.

**Method** [P]
- Backpropagate a *differentiable* reward through the sampler into LoRA weights, with gradient checkpointing.
- **DRaFT-K** truncates backprop to the last K steps. **K = 1 is best**: full backprop has exploding gradients and is slower per step.
- **DRaFT-LV** re-noises the final sample n times for lower variance.
- ReFL (reward on the one-step predicted x̂_0 at a random late step) is a special case.

**Results** [P]
- SD 1.4: LAION aesthetics roughly **200× more sample-efficient than DDPO**; DRaFT-LV about 2× faster than ReFL.
- HPSv2: 0.354 vs SD1.4 0.271. **Best-of-16 sampling baseline: only 0.276.**
- LoRA weights can be scaled to interpolate and combined linearly across rewards.

**Failure mode** [P]
- **Reward hacking / collapse:** "eventually collapsed to producing very similar high-reward images" (aesthetic reward 11 = collapsed).

**Limitations** [P]
- Requires a differentiable reward.
- Hacking.
- No KL in the base method.

**Compute** [P]
- Stated in the appendix (TPU/JAX); not needed here.

**Transfer to SignSparK** [I] (high technical fit)
- **SignSparK was explicitly trained for one-step reconstruction** (L_recon on x̂₁ = x_t + (1−t)v). Its one-step estimate x̂₁ is therefore meaningful at any t. **ReFL / DRaFT-1-style reward gradients on x̂₁ are cheap**: a single U-Net forward and backward per sample, with no unrolling.
- **Differentiable rewards exist for us:**
  - rotation-space reference errors (training only);
  - smoothness and jerk;
  - **the SignSparK-BT log-likelihood of the reference sentence given the generated poses**, a differentiable, dense alternative to sparse BLEU [H]. It is adversarially hackable, as any learned evaluator is.
- **Caveats:**
  - Collapse and hacking are documented, so a KL or anchor term is needed. DRaFT itself has none; Flow-GRPO shows KL prevents diversity collapse.
  - **Best-of-N was weak for them (0.276 vs 0.271).** For us, best-of-N headroom must be measured, not assumed.

## E4. ORW-CFM-W2: Online Reward-Weighted Fine-Tuning of Flow Matching with Wasserstein Regularisation

**Citation:** Fan et al., ICLR 2025, arXiv 2502.06061v1.

**Problem** [P]
- RL fine-tuning of continuous flows without likelihoods (expensive for CNFs), without differentiable rewards and without filtered datasets.

**Method** [P]
- **Reward-weighted CFM** (Thm 1): weighting the CFM loss by w(x1) ∝ r(x1) learns p_new ∝ w·q.
- **Online variant**: samples come from the current model. After N epochs, q_N ∝ w^N·q, which **collapses to a delta at the reward maximiser** (Lemma 1).
- **W2 bound** (Thm 3): W2²(p_θ1, p_θ2) ≤ e^{2L}·∫E‖v_θ1 − v_θ2‖² ds. This gives the regulariser α‖v_θft(x, t) − v_ref(x, t)‖².
- Loss (Eq. 10): E[w(x1)‖v_θ − u_t(x|x1)‖² + α‖v_θ − v_ref‖²], with w = exp(τ·r).
- Induced distribution (Thm 5): q_N ∝ exp(τN·r − β·ΣD_n)·q. The trade-off is controlled by τ and α.

**Experiments** [P]
- MNIST (even digits), CIFAR-10 compression, SD3 CLIP-score alignment.
- Without W2, collapse; with it, a controllable reward/diversity trade-off.

**Comparison** [P, from Flow-GRPO's Appendix C]
- On SD3.5-M PickScore, ORW's test reward peaked and then **fell (28.79 → 29.15 → 23.05 at step 960)**.
- Flow-GRPO kept improving (29.89).

**Transfer to SignSparK** [I] (very high implementation fit)
- **The simplest RL method that fits SignSparK's existing code.**
  - It needs only a per-sample weight on the existing CFM loss (`RFlow.training_losses_poses` already returns per-sample losses) plus an L2 penalty to a frozen copy's velocity.
  - No ODE→SDE conversion, no likelihoods, any (non-differentiable) reward. BT-BLEU and DTW-type rewards are usable.
- **Collapse theory applies directly.** Without the anchor it converges to a delta (one motion per text). With the anchor, the result interpolates.
- **Weaker than Flow-GRPO in the only head-to-head (a single run), which is evidence to weigh.** It is a natural *baseline* RL method for us.
- **Memory:** a frozen reference model doubles the weight memory (2 × 3.3 GB U-Net). This is feasible on 16 GB with LoRA, or with an fp16/bf16 reference.

## E5. Adjoint Matching: Fine-tuning Flow and Diffusion Models with Memoryless SOC

**Citation:** Domingo-Enrich, Drozdzal, Karrer, Chen (FAIR), ICLR 2025, arXiv 2409.08861v5.

**Key theory** [P]
- Target of reward fine-tuning: the **tilted distribution** p* ∝ p_base·exp(r).
- Naive KL-regularised (MaxEnt / SOC) fine-tuning gives p*(X0, X1) ∝ p_base·exp(r(X1) + V(X0, 0)). This is the **initial value function bias**.
- **With noiseless (ODE) sampling, σ = 0, "fine-tuning naïvely will not have any effect because X0 completely determines X1."**
- Theorem 1: fine-tuning must use the **memoryless noise schedule σ(t) = √(2η_t)** (necessary and sufficient). Sampling *after* fine-tuning can use any schedule, including σ = 0.
- **Adjoint Matching:** an SOC solver cast as least-squares regression of the control onto a "lean adjoint". It requires a **differentiable reward**.

**Results** [P]
- Flow-matching text-to-image model: better ClipScore / PickScore / HPSv2 consistency and generalisation, with diversity retained compared with DRaFT, ReFL and DPO-style baselines.
- Standard errors over 3 runs are reported (a rarity).

**Transfer to SignSparK** [I]
- **A theoretical warning that applies directly.** SignSparK samples deterministically given ε. Any KL- or entropy-regularised RL on its ODE is biased unless fine-tuning uses a memoryless SDE.
  - Flow-GRPO's marginal-preserving SDE (σ_t = a·√(t/(1−t))) is a practical, not exactly memoryless, choice.
  - Reward-gradient methods (DRaFT/ReFL) on the ODE optimise reward but **do not** target the tilted distribution, so they are prone to collapse. This is consistent with DRaFT's own observation.
- Adjoint Matching is the principled option if the reward is differentiable, at the cost of implementation complexity: lean adjoint ODE and memoryless SDE rollouts.
- **Keyframe-conditioned states** (masked entries clamped) complicate SOC theory; an extension is needed [H].

## E6. DNO: Optimizing Diffusion Noise Can Serve as Universal Motion Priors

**Citation:** Karunratanakul et al., CVPR 2024, arXiv 2312.11994v2.

**Method** [P]
- Freeze a pretrained text-to-motion diffusion model (MDM, HumanML3D 263-d).
- Optimise the **initial noise x_T** by backprop through a deterministic DDIM ODE solver (10 steps) for any differentiable criterion L(motion).
- **Unit-normalised gradients** (raw gradient norms span orders of magnitude) with Adam and momentum.
- A decorrelation regulariser on the noise keeps it Gaussian-like.

**Uses** [P]
- Editing (trajectory, pose, joint targets, obstacles), denoising, and completion from partial inputs. No retraining.

**Cost** [P]
- 300–500 optimisation steps, about **3 min per batch on an RTX 3090**.
- 18 GB for batch 16 with DDIM-10.

**Limitations** [P]
- Slow (not interactive).
- Cannot always project to realistic motion.
- Bounded by the base model.

**Transfer to SignSparK** [I]
- **A strong, training-free alternative to RL fine-tuning: inference-time optimisation of SignSparK's initial noise ε.** SignSparK's sampler is a deterministic Euler ODE of 1–10 steps, so it is cheap to backprop through.
- **The objective must be available at test time without the reference.** Candidates:
  - (a) smoothness or jerk;
  - (b) SignSparK-BT log-likelihood of the *input* sentence given the generated poses. This uses only the input text, so there is no leakage, but it is an adversarial-attack risk [H];
  - (c) plausibility priors.
- **Directly targets GF-T2P's mean-collapse.** For a fixed text, optimising ε trades towards higher evaluator score while staying on the model's manifold.
- **Cost per test clip is high** (hundreds of forward and backward passes). It is a test-time compute trade, comparable to best-of-N.
- **Mandatory non-RL baseline** for any learned approach, alongside best-of-N.

## E7. Inference-time search, optimisation and sampling family (read at method level)

### E7a. Inference-Time Scaling for Diffusion Models beyond Denoising Steps
**Citation:** Ma et al., arXiv 2501.09732v1, 2025.

**Method** [P]
- Search over sampling noises along two axes:
  - **verifiers**: oracle, supervised (e.g. CLIP/DINO classifiers) or self-supervised;
  - **algorithms**: Random Search (= best-of-N), Zero-Order Search (local search around a pivot noise), Search over Paths.

**Findings** [P]
- Extra inference compute spent on search keeps improving results beyond the denoising-step plateau.
- **"Verifier hacking":** random search over all of Gaussian space quickly overfits verifier biases. Different verifiers' biases conflict (aesthetic vs CLIP). Ensembles help.
- No single configuration is optimal across tasks.

**Transfer** [I]
- Best-of-N and zero-order search over SignSparK's ε with a test-time verifier are the **cheapest non-RL baselines**.
- How2Sign's only learned verifier (BT, BLEU-4 ceiling 3.5) is likely highly hackable, so verifier hacking is a first-order risk for us.

### E7b. ReNO: Reward-based Noise Optimization for one-step text-to-image models
**Citation:** Eyring et al., NeurIPS 2024, arXiv 2406.04312v2.

**Method** [P]
- Gradient ascent on the initial noise (~50 iterations, 20–50 s) through **one-step** distilled models, which avoids exploding gradients from multi-step backprop.
- Hacking is mitigated with:
  - a combination of reward models;
  - a noise-norm regulariser keeping the noise in-distribution;
  - gradient clipping;
  - limited steps.
- One-step models + ReNO beat SDXL and match SD3 in user studies.

**Transfer** [I]
- SignSparK is trained for **one-step sampling** (L_recon; 1-step quality only ~3% worse than 10-step per paper Fig. 4).
- A ReNO-style ε-optimisation through 1–2 Euler steps is cheap and avoids DNO's 10-step backprop.

### E7c. TDS: Twisted Diffusion Sampler
**Citation:** Wu, Trippe et al., NeurIPS 2023, arXiv 2306.17775v2.

**Method** [P]
- Sequential Monte Carlo with twisting for **asymptotically exact** conditional sampling p(x | y) from an unconditional diffusion model.
- Improves over heuristics with as few as 2 particles.
- Applied to inpainting, class-conditional generation and protein motif scaffolding.

**Transfer** [I]
- A principled alternative to SignSparK's hard keyframe re-imposition. Keyframe conditioning is an inpainting-type constraint.
- Also a principled way to sample from a reward-tilted distribution at inference with a particle budget.
- Requires per-step stochasticity (an SDE sampler) and likelihood weights, so implementation cost is moderate.

## E8. RL / reward fine-tuning for human motion generation (read at method level)

| Paper | Generator | Optimiser | Reward | Key points |
|---|---|---|---|---|
| **MotionRL** (Liu et al., arXiv 2410.06513, preprint) | AR VQ-VAE + GPT (T2M-GPT) | PPO (token level) with **batch-wise Pareto-set selection** across rewards; reward-specific preference tokens | (i) text adherence: −‖f_text − f_motion‖ with TMR / Guo encoders; (ii) motion quality: −‖f_gt − f_pred‖ (reference embedding, training only); (iii) human-perception model (MotionCritic) | Multi-reward weighted sums are unstable, so Pareto selection is used. Notes that diffusion/mask models need the **length as input** (as SignSparK does). |
| **ReinDiffuse** (Han et al., arXiv 2410.07296) | MDM diffusion, re-parameterised to output a Gaussian action distribution | PPO-style RL | Physical plausibility: foot sliding/skating, floating, ground penetration, foot clipping | Physics rewards without a simulator. **Shows that heuristic plausibility rewards are usable but domain-specific** (lower body; irrelevant to upper-body signing). |
| **MotionCritic** (Wang et al., ICLR 2025, arXiv 2407.02272) | MDM | Fine-tune with **critic loss on a single-step prediction at a random timestep** (ReFL-like) + KL to the previous prediction | Learned critic trained on MotionPercept (large human pairwise perceptual dataset) | Shows GT-error metrics and FID align poorly with human perception. A small number of fine-tuning steps suffices. **No sign-language equivalent of MotionPercept exists.** |
| **EasyTune** (Tan et al., ICLR 2026, arXiv 2602.07967) | Motion diffusion (MLD, MDM, ...) | **Step-wise** differentiable-reward fine-tuning that decouples the recursive dependence across denoising steps; dense, low-memory updates | Motion reward model + **Self-refinement Preference Learning** (mines preference pairs automatically) | +8.2% MM-Dist vs DRaFT-50, 31% of its extra memory, 7.3× faster. Directly addresses DRaFT's memory problem for motion. |
| **MotionRFT** (Tan et al., IEEE TPAMI, arXiv 2603.27185v2) | Diffusion **and flow** text-to-motion, incl. a **rotation-based** model (HY-Motion) | EasyTune | **MotionReward**: heterogeneous-representation, multi-dimensional reward anchored in a text-semantic space | FID 0.132 on MLD at 22.1 GB peak. Gains on joint- and rotation-based models. Closest published analogue of "RL fine-tuning a rotation-space motion generator". |
| **No MoCap Needed** (Macaluso et al., WACV 2026, arXiv 2510.06988) | Latent- and joint-space motion diffusion | **DDPO-IS** with replay buffer | Pretrained **text–motion retrieval (TMR) embedding distance**; no motion ground truth | Cross-dataset and leave-one-out adaptation with prompts only. Reports preserved original-distribution performance. |

**Transfer to SignSparK** [I]
- The motion field has converged on **(a)** differentiable reward fine-tuning with step-wise or one-step tricks (MotionCritic, EasyTune), or **(b)** DDPO/PPO with learned text–motion or perception rewards.
- **All rely on a learned evaluator (TMR, MotionCritic, MotionReward). None exists for ASL**; SignSparK-BT is our only candidate, and it is weak (Stage 2).
- **This evaluator gap is the main research gap** that RL methods themselves cannot fix.
- Physical-plausibility rewards (ReinDiffuse) target the lower body. The SLP analogues would be:
  - joint-limit and self-penetration terms (these need SMPL-X meshes);
  - hand–body coordination;
  - 6D-validity terms (Stage 2 Q1).

## E9. Other diffusion/flow RL methods and SLP-specific RL (read at abstract and method level)

### DPOK (Fan et al., NeurIPS 2023, arXiv 2305.16381)
- Online policy gradient on the multi-step diffusion MDP with **KL regularisation** to the pretrained model, using ImageReward.
- Analyses KL for both RL and reward-weighted supervised fine-tuning. Online RL beats supervised reward fine-tuning on alignment *and* image quality.
- Supervised fine-tuning on a fixed pretrained-generated set causes quality deterioration (over-saturation).
- **Transfer** [I]: DDPO + KL. This is the template for KL-anchored policy-gradient fine-tuning of SignSparK, together with Flow-GRPO's closed-form KL.

### Diffusion-DPO (Wallace et al., CVPR 2024, arXiv 2311.12908)
- DPO re-derived with the diffusion ELBO as likelihood surrogate.
- Trained on Pick-a-Pic's 851k human pairwise preferences on SDXL.
- Beats SDXL (+refiner) in human evaluation; an AI-feedback variant is comparable.
- **Transfer** [I]: needs preference pairs. We have none from humans, but pairs could be mined from evaluator scores over multiple SignSparK samples per text, offline.
- Preference methods avoid reward scale issues, but inherit evaluator bias.
- Flow-GRPO reports online DPO as the second-best method in its comparison.

### ReinFlow (Zhang et al., arXiv 2505.22094v7)
- Online RL for **flow-matching robot policies** (Rectified Flow, Shortcut models).
- **Learnable noise injected** into the deterministic flow path gives a discrete-time Markov process with exact likelihoods.
- Stable even with **very few or one denoising step**.
- Results: +135% episode reward on locomotion; saves 82.6% wall time vs DPPO.
- **Transfer** [I]: a second, independently validated way to make a few-step rectified-flow policy stochastic for policy gradients. A learnable noise network is an alternative to Flow-GRPO's fixed SDE schedule. It is relevant because SignSparK runs at 1–10 steps.

### SignLLM (Fang et al., arXiv 2405.10718v3): the only SLP paper found that uses "RL"
- The "RL loss" uses reward r = −MSE to the ground-truth pose, and a **Priority Learning Channel** that prioritises high-value batches to speed up training.
- The authors state their RL strategy "is not a typical one, but rather only partially applied to component modules."
- **Assessment** [I]: this is a loss-based sample re-weighting / prioritisation of supervised regression, not policy optimisation of a generator against an evaluator.
- **Prior art on genuine RL fine-tuning of a pretrained SLP generator therefore appears thin.** This holds *within my search* (2 web searches plus the uploaded survey). It is **not** an exhaustive novelty claim.

### Not obtained
- **AlignProp** (arXiv 2310.03739): v5 is listed as withdrawn and v4 returned 404. DRaFT covers the same reward-backprop family.
