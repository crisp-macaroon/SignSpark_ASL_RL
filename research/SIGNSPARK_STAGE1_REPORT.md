# Stage 1 Report (SLP track): SignSparK as a pretrained base for RL improvement

Date: 2026-11-02 · Protocol: SLP research prompt, Stage 1 only. No EDA, MDP design, algorithm choice or code modification has been done.

## Evidence labels

| Label | Meaning |
|---|---|
| **[P]** | Stated in the SignSparK paper (arXiv 2603.10446v4, uploaded `papers/SignSpark.pdf`, 23 pp., main text only, **no supplementary**) |
| **[C]** | Verified by reading the official code (github.com/JianHe0628/SignSparK, tree sha `916402d`, downloaded read-only to the scratchpad) |
| **[R]** | Stated in repository docs or model/data cards (README, DATA.md, HF cards, companion-repo READMEs). These are not code-verified. |
| **[I]** | My own technical inference or arithmetic, with the reasoning shown |
| **[⚑]** | Outside knowledge not checked against an uploaded source |
| **[H]** | Hypothesis that requires experiment |

Nothing was executed: no checkpoint was loaded and no data was downloaded. All parameter and memory figures below are therefore **estimates**.

---

## 0. Before anything else: three blocking findings

### 0.1 The "existing project context" could not be verified
- The prompt describes an existing pipeline: text → gloss → pose, Transformer encoder-decoder gloss-to-pose, 152-d frames, CISLR word-level data, a reference-reward RL implementation, and a past stop-head failure.
- **None of this is on disk.** `rlproj/rlproj/src/` has been removed, and the working directory now holds only `papers/`, `research/` and one `PoseStich-SLT/` clone.
- I therefore treat all of that context as **unverified user-reported context**, as the prompt instructs.

### 0.2 Target-language conflict with the earlier research brief
- The earlier master instruction fixed scope to **ASL SLT** (POSESTITCH-SLT, WLASL/How2Sign).
- This prompt is **SLP**, and mentions **CISLR**. CISLR is an Indian Sign Language (ISL) isolated-sign dataset [⚑].
- These are different tasks, different languages and possibly different datasets.
- **SignSparK supports no ISL data at all** (§6.1). This is the decisive compatibility question.

### 0.3 The pasted prompt is truncated
- The prompt stops mid-sentence in §4.5 ("Is the transition function imp…").
- Stages 4.5 onward will be needed before Stage 4 starts. They are not needed now.

---

## 1. Detailed model explanation

### 1.1 Problem addressed [P]
SLP must satisfy two goals at once:
- **(i)** each sign must be articulated precisely;
- **(ii)** consecutive signs must join with natural co-articulation.

Existing methods trade one off against the other:
- **Direct text-to-pose regression (T2P)** regresses to the mean, producing under-articulated, "unintelligible" signing.
- **Dictionary retrieval (text → gloss → retrieved clips)** keeps articulation, but stitches clips by naive interpolation, which looks robotic.
- **Monocular 3D pseudo-ground-truth** (e.g. HaMeR) propagates estimation errors into trained models.

### 1.2 Core idea [P]
Train a generator to produce dense motion from **text plus sparse keyframes**:
- Keyframes act as hard anchors, so the model cannot regress to the mean at them.
- Because anchors are sparse, it must learn the *distribution of fluid motion* between them.

This makes the same network usable in four regimes:

| Regime | Name | Keyframe source |
|---|---|---|
| 1 | **G2P / sign stitching** | Retrieved per-gloss keyframes |
| 2 | **SR-T2P** | Text → gloss → retrieved keyframes |
| 3 | **GF-T2P** | Zero keyframes |
| 4 | **KF2P** | User-edited keyframes |

### 1.3 Components
1. **FAST segmenter** [P][C][R]
   - Transformer BIO tagger over WiLoR MANO hand rotations (6D, two parallel streams plus a "two-stream mixer").
   - Trained with frame-level cross-entropy plus sign-level CTC on MeineDGS (DGS).
   - Output labels: 0 = outside, 2 = onset, 1 = inside.
   - Shipped as an external pip package (`signlangtk==0.3.1`); **its training code is not in the repo** [C].
2. **Keyframe selection policy** [P][C]
   - For each detected sign segment, take its onset, its midpoint and its offset.
   - Implemented as `generate_keyframes(mode=3)` in [C]; also supports user-supplied keyframe files (mode 999).
3. **SignSparK generator** [P][C]
   - Conditional rectified-flow / CFM network: a 1D temporal U-Net with a Transformer bottleneck.
   - Conditioned on: time t, the keyframe-masked noisy sequence, the keyframe mask, the length mask and a sentence-level text embedding.
4. **Rendering** [P]
   - 3D Gaussian Splatting (HuGeDiff) for photorealistic avatars.
   - Not in the repo; irrelevant to RL.

### 1.4 Input and output representation [P][C]

| Stream | Content | Dims per frame | Model |
|---|---|---|---|
| hand | MANO, 15 finger joints × 6D rotation, **one hand at a time** | 90 | separate ~1.4B checkpoint |
| body | SMPL-X body joints 11–20 (neck, collars, head, shoulders, elbows, wrists) × 6D | 60 | separate checkpoint |
| face | FLAME: jaw 6D + 50 expression coefficients | 56 | separate checkpoint |
| (full) | concatenation of all streams, configurable but **no released checkpoint** | 296 | – |

- **Coordinate system** [C][I]:
  - Every value is a *joint-local rotation* (Zhou et al. row-based 6D) relative to the parent in the kinematic tree.
  - No global root orientation, no root translation and no body shape β are generated.
  - Joint *positions* exist only after SMPL-X/MANO forward kinematics with an assumed shape.
- **Left hand** [C][R]: stored in SMPL-X-left convention and converted to right-hand convention by conjugation with diag(1, −1, −1). The hand model is a single right-hand model trained on mirrored left hands as extra samples.
- **Text** [C]: the sentence is prefixed with a language tag `<{language}> ` (`specify_lang=True`) and embedded by frozen **M-CLIP XLM-RoBERTa-Large-ViT-B-16Plus**.
  - It is mean-pooled into **one 640-d vector**. The code comment says: "The sequential aspect of text is lost".
- **Length** [C]:
  - Clips are padded to `seq_len = 304` frames by repeating the last frame.
  - A binary length mask is fed as an **input channel**.
  - **The model never predicts length.** Length is always supplied from outside.
- **Glosses** [C][R]: glosses are *not* a model input. They are used only by the separate retrieval repo to fetch keyframes.

### 1.5 Architecture [C], [I] where marked

```
Wilor_UNET (signspark/unet_model.py)
 ├─ input  : concat_channels( M⊙x_kf + (1−M)⊙x_t ,  M ,  length_mask )      [B, 3·D, T]
 ├─ cond c : time_mlp( TimestepEmbed(t) + Linear_640→512( maskcond(MCLIP(text)) ) )
 └─ TemporalUnetLarge (signspark/unet_model_large.py)
      Encoder: 4 levels, channels D→512→1024→2048→2048, each 3×ResidualTemporalBlock
               (Conv1d k=5 → RMSNorm → Mish, AdaLN-Zero(c) gates), RoPE self-attn at levels 2,3,
               stride-2 downsampling ×3 (T: 304→152→76→38)
      Bottleneck: 1×1 proj 2048→1024, 8 × TransformerBottleneckBlock
               (RoPE self-attn 16 heads; cross-attn to ONE context token c; SwiGLU FFN; AdaLN-Zero on each)
      Decoder: mirrored, skip concatenations, transposed-conv upsampling
      Head: Conv1dBlock → 1×1 conv to D (zero-init)
 output: predicted velocity field v̂ ∈ R^{B×D×T}
```

- **Size** [R]: the model card states "~1.4B params each". Each `ema_0.9999_200000.pt` file is 5.58 GB [R], which matches 1.4B fp32 parameters [I].
- **Size breakdown** [I]: a rough count of the U-Net layers gives roughly 0.85–0.9B. The rest is very likely the frozen M-CLIP encoder (~0.56B [⚑]), which the code registers as a submodule and therefore stores in every checkpoint.
- **Temporal handling** [C]:
  - Generation is **non-autoregressive and bidirectional over the whole 304-frame window**.
  - Temporal structure comes from convolutions, RoPE self-attention at coarse resolutions and the bottleneck transformer over 38 tokens.
  - There is no causal ordering and no stop token.
- **Conditioning pathways** [C]:
  - Text and time enter only through AdaLN-Zero modulation and a single cross-attention token.
  - Keyframes enter through input-channel concatenation plus hard re-imposition during sampling.
  - The hand, body and face streams are **independent networks**. There is no cross-stream attention, and **left and right hands are sampled independently**: at inference they are interleaved as separate batch items that share only text and their own keyframes [C].
  - Bimanual and body–hand coordination is therefore **not modelled jointly** [I].

### 1.6 Training objective, mathematically
Notation: x₁ is the ground-truth sequence, M the keyframe mask, m the length mask, z the text embedding.

**Probability path** [P Eq.1, C]:

    x₀ ~ N(0, I),  t ~ U[ε, 1),  ε = 10⁻³
    x_t = t·x₁ + (1−t)·x₀                                 (linear / rectified-flow path)
    C_t = M ⊙ x₁ + (1−M) ⊙ x_t                            (keyframes clean, others noised)   [P Eq.2]

**Velocity target**: the paper and the code disagree.

| Source | Target |
|---|---|
| Paper Eq. 3 | u_t = x₁ − C_t |
| Code (`rflow.py`) | u_t = x₁ − (M⊙x₁ + (1−M)⊙x₀) = (1−M) ⊙ (x₁ − x₀) |

The code's target is the standard rectified-flow velocity, zeroed on keyframes [C]. I checked algebraically which one is self-consistent with the paper's own reconstruction Eq. 4, x̂₁ = x_t + (1−t)·v [I]:
- With the code's target on non-keyframe entries: x_t + (1−t)(x₁ − x₀) = x₁ exactly. ✔
- With the paper's target: C_t + (1−t)(x₁ − C_t) ≠ x₁ for t < 1. ✘

Conclusion: **the code is consistent and paper Eq. 3 is a notational error** (it would need a 1/(1−t) factor). For RL work, the code defines the model.

**Losses** [P Eqs. 3–7, C]: all are masked by the length mask m and averaged over valid frames.

    L_flow  = ‖ m ⊙ ( f_θ(C_t, t, M, m, z) − u_t ) ‖²
    x̂₁      = C_t + (1−t) · f_θ(·)                         (one-step Euler estimate of x₁)
    L_recon = ‖ m ⊙ ( x̂₁ − x₁ ) ‖²
    L_vel   = ‖ m ⊙ ( Δx̂₁ − Δx₁ ) ‖²,      Δx_f = x_{f+1} − x_f
    L_acc   = ‖ m ⊙ ( Δ²x̂₁ − Δ²x₁ ) ‖²                    (code only, not in paper)
    L       = λ_flow L_flow + λ_recon L_recon + λ_vel L_vel + λ_acc L_acc

**Weights**: the paper and the code disagree again [P vs C].

| Source | (flow : recon : vel) | Acceleration term |
|---|---|---|
| Paper | 2 : 1 : 1 | none |
| Code (`configs/data_v2/common/train.yaml`) | 0.5 : 1.0 : 0.5 (i.e. 1 : 2 : 1) | λ_acc = 0.1 |

The released checkpoints were presumably trained with the code configuration, but this is **unconfirmed**.

**Classifier-free guidance (CFG)** [P vs C]:
- Paper: during training both C and z are dropped with ρ = 0.1, and at inference v^(γ) = v(∅, ∅) + γ (v(C, z) − v(∅, ∅)).
- Code, at training:
  - The text embedding is zeroed with p = 0.1 (`text_mask_prob`).
  - Separately, the *whole keyframe mask* is zeroed with p = 0.1 (`train_keyframe_mask_prob`).
- Code, at inference (`classifier_free.py`):
  - Only **text** is dropped in the unconditional branch. Keyframes stay present in both branches.
  - So the implemented guidance is v = v(C, ∅) + γ (v(C, z) − v(C, ∅)).
- **Keyframe guidance strength is not exposed** [C].
- γ can be a **per-sample tensor** (`text_scale.view(-1,1,1)`) [C].

**Optimisation** [C]:
- AdamW, lr 1e-5 with linear anneal to 0, weight decay 0.01, gradient clip 1.0.
- EMA rate 0.9999; batch 64; fp32 (autocast disabled); 1M-step budget in the config.
- The released checkpoints are at 200k steps.
- Seeds: 102 for training. `accelerate.set_seed(666, device_specific=True)` overrides it, so runs are not seed-identical across GPU counts [I].

### 1.7 Inference and sampling [C]
```
x ← M ⊙ x_kf + (1−M) ⊙ ε                      (ε ~ N(0,I); x_kf = keyframe values)
for k = 0 … N−1, t_k = k/N:                   (torchdiffeq fixed-step Euler, N = eval.ode_stepnum, default 50)
    x ← M ⊙ x_kf + (1−M) ⊙ x                  (keyframes re-imposed before every evaluation)
    x ← x + (1/N) · ṽ(x, t_k)                  (ṽ = CFG-combined field if γ ≠ −1)
return x
```
- A "heun" sampler alternative exists.
- The whole sampler is wrapped in `@torch.no_grad` and is **deterministic given ε**.
- **The only stochasticity is the initial noise.**
- The paper claims good quality in < 10 steps and an extra 3% advantage at 1 step thanks to L_recon (Fig. 4) [P].

**How evaluation is actually conducted** [C][I]. This matters for later reward and leakage design:
- `sample.py` takes the **keyframes from the ground-truth test clip's own segment labels** and the **ground-truth length**.
- KF2P numbers are therefore oracle-keyframe, oracle-length results.
- The "no-KF" GF-T2P mode (`keyframes_mask_all=True`) still uses **ground-truth length**.
- The paper does not state this. Any comparison we make must reproduce it exactly or remove the oracle.
- In SR-T2P, length and keyframe timing come from retrieval: keyframes are padded "at a fixed 8-frame interval" [P].
- **Ad-hoc parts of the pipeline** [I]:
  - That fixed 8-frame interval is a heuristic.
  - The retrieval repo uses "naive interpolation" placeholders between signs [R].

### 1.8 Reported results (paper numbers; **not reproducible with released assets**, see §5)

| Regime | Paper result |
|---|---|
| FAST, MeineDGS | F1 0.860, IoU 0.772 vs Hands-On 0.857/0.760 (+0.3% F1) |
| G2P stitching vs Sign Stitcher | DTW-J 9.01 vs 57–59 on Phoenix14T; B-T BLEU-4 11.70 vs GT 14.77 |
| GF-T2P, How2Sign | DTW-PA-JPE body/hand 7.26/2.72 vs SOKE 7.91/3.10 |
| SR-T2P, CSL-Daily | 4.87/1.37 vs SOKE 6.24/1.71 (How2Sign omitted: no glosses) |
| KF2P, How2Sign | Beats SLERP on every metric. B-T BLEU-4: 2.99 vs GT 3.37 |
| Efficiency | 10-step sampling 0.01 s/video vs SOKE 1.55 s ("100×") |
| User study | 16 BSL signers (6 Deaf). Preferred over SOTA 86.7%, over pseudo-GT 72.6%, over interpolation 73.3% |

**Critical notes** [I]:
- **No seeds, confidence intervals or significance tests** are reported for the SLP numbers. Only ablation std-devs over samples are given.
- **The loss-ablation differences are within noise.**
  - Table 6: L_CFM+L_recon vs all three losses are identical to 2 d.p. for body.
  - The paper itself keeps L_vel for a *qualitative* reason (micro-jitter), not a measured one.
- **Back-translation scores are tiny.** How2Sign has a GT ceiling of BLEU-4 3.37 (paper) and 3.53 (released BT model) [R]. This is the same sparsity problem identified for POSESTITCH-SLT (F4 in the earlier log).
- **The user study measures preference, not comprehension.** It was run on BSL only, and its 72.6% "better than pseudo-GT" result reflects estimator jitter in the GT.
- **JPE units are not stated** in the paper.

---

## 2. Architecture diagram specification
Nodes are listed with shapes for a figure. B = batch, T = 304, D ∈ {90, 60, 56}.

```
[Video] ──WiLoR/NLF/TEASER + re-optimisation (unreleased)──► [6D features  T×(90|60|56)]
[Video] ──WiLoR──► [FAST BIO tagger] ──► segment∈{0,1,2}^T ──► [Selection: onset/mid/offset] ──► M∈{0,1}^{T}
[Sentence] ──prefix "<LANG>"──► [M-CLIP (frozen)] ──mean-pool──► z∈R^640 ──Linear──► R^512 ─┐
[t ~ U] ──sinusoid──► MLP ──► R^512 ──────────────────────────────────────────────────────────┼─(+)─► time_mlp ─► c∈R^512
[x₁, x₀, t] ──► C_t = M⊙x₁+(1−M)⊙x_t ──concat[C_t, M, m_len]──► [Temporal U-Net + 8-layer Transformer bottleneck, AdaLN-Zero(c), cross-attn(c)] ─► v̂ ∈ R^{D×T}
Training: v̂ → {L_flow, L_recon(x̂₁), L_vel, L_acc}
Inference: Euler ODE N steps with keyframe re-imposition, optional text-CFG(γ) ─► x̂ ∈ R^{D×T} per stream
Streams: hand(L), hand(R), body, face sampled independently ─► SMPL-X FK ─► mesh / 3DGS render
Evaluation: SOKE code (DTW-JPE, DTW-PA-JPE, needs SMPL-X) · SignSparK-BT (body+hands 240-d → text, BLEU/chrF/ROUGE)
```

---

## 3. Repository map ([C] unless noted)

| File | Purpose | RL relevance |
|---|---|---|
| `train.py` | Hydra entry. Builds model + RFlow, LMDB loaders, AdamW, Accelerate, then `TrainLoop_Flow` | Template for an RL training entry point |
| `flow_train_util.py` | `TrainLoop_Flow`: microbatching, keyframe-mask construction, t sampling, EMA, checkpointing, lr anneal | Hook point for RL updates; the EMA is kept on GPU (memory cost) |
| `basic_utils.py` | `create_model_and_flow`, stream→dim map, batch-size probe | |
| `signspark/unet_model.py` | `Wilor_UNET` wrapper: text encoder (CLIP/Gemma/Qwen options), CFG masking, input-channel concat | `embed_text`, `TimestepEmbedder`: small fine-tunable heads |
| `signspark/unet_model_large.py` | `TemporalUnetLarge`: ResBlocks, RoPE attention, 8 bottleneck Transformer blocks, AdaLN-Zero | **Main candidate for LoRA / partial fine-tuning** (bottleneck `to_qkv`, `q_ca`, `kv_ca`, `ff_*`, `AdaLNZero.proj`, `final_conv`) |
| `signspark/rflow.py` | `RFlow.training_losses_poses` (all losses), `sflow_sampler` (Euler/Heun), `decode` | **Sampler = the generative "policy rollout"**; loss function = where an RL/reward term would be added |
| `signspark/sampling_rflow.py` | Legacy RK45 sampler; partly `NotImplementedError` | Not used |
| `signspark/keyframes.py` | `get_keyframes_mask` (+ random joint subset masking) | **Controller action surface** (which frames/joints are anchored) |
| `signspark/pose_datasets_lmdb.py` | LMDB dataset, left-hand flip, padding to 304, `generate_keyframes` (mode 3 / custom 999) | Custom keyframe files allow per-clip keyframe control without code changes |
| `classifier_free.py` | Text-only CFG wrapper with per-sample scale | **Controller action: γ per sample** |
| `sample.py`, `sample_all.py` | Sampling of one stream / three streams; writes `.npy` dumps with GT, mask, text | Baseline generation; uses **GT length + GT keyframes** |
| `configs/` | Hydra configs (train, inference, splits, per-stream) | Loss weights and probabilities listed in §1.6 |
| `fast/segment.py`, `fast/visualize.py` | Wrappers around external `signlangtk` FAST | Keyframe extraction for new data needs WiLoR + MANO licence |
| `tools/download_*.py`, `inspect_lmdb.py`, `visualize.py` | HF downloads, LMDB inspection, SMPL-X rendering (needs licence-gated SMPL-X) | |
| `signspark/helper.py` | Hard-coded clip `skip_list` (imported but **unused** in the loader) | Data-quality signal for EDA |
| External: SignSparK_Retrieval [R] | mBART text-to-gloss + isolated-sign dictionary (from Spoken2Sign) + stitching. **CSL-Daily and PHOENIX-2014T only** | SR-T2P pipeline. Retrieval choices = controller surface |
| External: SignSparK_BT [R] | Back-translation (JoeyNMT/SLT-based, 240-d body+hands) | Only available learned "linguistic" evaluator |
| External: SOKE eval code [R] | DTW-JPE / DTW-PA-JPE | Official metric implementation (not inspected) |

**Not released** [C][R]:
- FAST training code;
- the SMPL-X/MANO/FLAME **re-optimisation** step used to build the LMDBs;
- the 3DGS renderer;
- the BOBSL/CSL-News LMDBs used for the released checkpoint.

**Code-level issues found** [C]:
1. **Unset variable in a non-default path.** In `rflow.training_losses_poses`, if `x_0` is passed in, `keyframed_x0` is never defined. This is latent; the default path is fine.
2. **Inconsistent `flip_left_hand` defaults** across the inference config, `sample_all.py` and DATA.md:
   - `inference.yaml` sets `False`;
   - `sample_all.py` and DATA.md set `True` for released LMDBs.
   - This silently mis-orients one hand if set wrong.
3. **Training-data list inconsistency.** The README says the official checkpoint was trained on CSL-Daily, How2Sign, BOBSL **and CSL-News**. The HF model card lists only CSL-Daily, How2Sign and BOBSL.
4. **Paper ≠ code** on the velocity target, loss weights, the acceleration loss and CFG semantics (§1.6).

---

## 4. Pretrained checkpoint and data availability [R]

| Asset | Availability | Size | Licence |
|---|---|---|---|
| hand / body / face checkpoints (EMA, step 200k, `unet_large`) | HF `LionelLow/SignSparK` | 5.58 GB each, **16.7 GB total** | Non-commercial research |
| LMDBs: CSL-Daily, How2Sign, PHOENIX-2014T (train/dev/test) | HF `LionelLow/SignSparK_data` | How2Sign train 7.9 GB, dev 0.45, test 0.59; CSL-Daily 3.3/0.2/0.23; Phoenix 1.28/0.09/0.10 GB | Non-commercial, plus source-dataset licences |
| Back-translation models (Phoenix, CSL-Daily, How2Sign) | HF `LionelLow/SignSparK_BT` | not checked | Non-commercial |
| Text-to-gloss and retrieval dictionary | SignSparK_Retrieval | not checked | Non-commercial; **CSL-Daily & PHOENIX only** |
| SMPL-X, MANO model files | Licence-gated registration | – | **You must register personally**; I cannot create accounts |

Important caveats:
- **The released assets do not reproduce the paper's numbers** [R]:
  - The checkpoints use "15× more data".
  - The LMDBs were "re-optimised".
  - The BT models were retrained.
  - The retrieval README already reports different numbers (CSL-Daily body worse, hands better).
  - **Our baseline must be measured by us** with the released assets. Paper numbers cannot serve as the baseline.
- **PHOENIX-2014T data is released, but the checkpoint was not trained on it** [R].
- **No ISL data, checkpoint, text-to-gloss model, dictionary or BT model exists** for SignSparK.

---

## 5. Compatibility assessment

| Dimension | Our stated project (unverified, §0.1) | SignSparK | Compatible? |
|---|---|---|---|
| Sign language | ISL (CISLR) [⚑] | ASL (How2Sign), CSL, BSL (BOBSL), DGS (data only) | **No.** ISL is unseen. A `<ISL>` language token would be untrained. |
| Unit of production | Isolated words (CISLR) | Continuous sentences (≤ 304 frames) | **Partial.** A single word yields 1 segment → 3 keyframes. With GT keyframes, KF2P on an isolated sign is close to trivial in-betweening [I]. |
| Conditioning | Gloss sequence | Sentence text (pooled embedding) + keyframes; glosses only via retrieval | **Partial.** Gloss→pose maps onto *retrieval-based G2P*, which requires an ISL sign dictionary in SMPL-X form. |
| Pose representation | 152-d per frame. Plausibly 76 keypoints × (x, y) from MediaPipe, as in POSESTITCH [⚑, unverified for this project] | 6D joint-local rotations, 3D, separate streams (90/90/60/56), no root/translation/shape | **No.** See below. |
| Reference annotations | Pose sequences | SMPL-X/MANO/FLAME fits + FAST segments | Requires re-extraction from **raw video** |
| Sequence end | Learned stop head (with past instability) | No stop head; length is an external input | Different. Termination becomes a **length decision outside the generator** [I] |
| Compute | RTX 2050 4 GB; Kaggle P100/T4 16 GB; Colab; optional cloud | ~1.4B params per stream, fp32, EMA on GPU during training | See §7 |

**Why 152-d keypoints and SignSparK's representation are not interchangeable** [I]:
- **Rotations to keypoints is possible.** Run forward kinematics on SignSparK output (SMPL-X + MANO with an assumed shape β and camera) and project, giving 2D keypoints comparable to MediaPipe.
  - But: different skeleton topology (MediaPipe face mesh points ≠ FLAME expression basis), unknown camera, and no global orientation. Comparison is therefore only approximate, and only after Procrustes alignment.
- **Keypoints to rotations is ill-posed.** 2D keypoints do not determine 3D joint rotations, especially for finger twist and depth. Training SignSparK on our data would need the full 3D extraction pipeline on **raw videos**:
  - WiLoR + NLF + TEASER, plus the **unreleased** re-optimisation;
  - MANO and SMPL-X licences.
  - The resulting feature distribution would differ from the released LMDBs, creating a domain gap the pretrained weights were not trained for.
- **Consequence.** Any RL reward defined in our 152-d space cannot be computed on SignSparK outputs without an FK + projection bridge whose own error must be quantified.

**What adapting SignSparK to ISL would take** [I]:
1. Raw CISLR videos.
2. A 3D extraction pipeline approximating theirs.
3. FAST segments (trained on DGS hands; behaviour on ISL isolated clips is unknown).
4. Fine-tuning three ~1.4B models on ~thousands of isolated clips with ≈ 1 example per word [⚑ CISLR statistics, to verify in EDA].
5. A new ISL back-translation or recognition model for any linguistic evaluation.

This is a research project in itself. It would also make any later RL result uninterpretable: gains could come from adaptation, not RL.

**Alternative bases** (only those supported by sources we have):

| Option | What it is | Assessment |
|---|---|---|
| (a) Our existing gloss→pose Transformer (152-d, CISLR) | Matches language, data and representation | Weaker generator, and code currently missing. Its stop-head instability is a known RL failure mode |
| (b) SignSparK on a language it supports | ASL/How2Sign or CSL-Daily/PHOENIX | Strong pretrained prior, released data, evaluator and (for CSL/Phoenix) a full text→gloss→retrieval pipeline. Language changes away from ISL |
| (c) SOKE | Multilingual SLP baseline cited by SignSparK [P] | Not uploaded; no ISL either [⚑] |
| (d) Sign Stitching (Walsh et al. 2024) | Cited by SignSparK [P] | Not uploaded; no ISL either [⚑] |

---

## 6. Computational feasibility ([I] estimates; to be measured empirically before any commitment)

| Workload | Rough memory need | RTX 2050 4 GB | Kaggle T4 / P100 16 GB | A100 40–80 GB (cloud) |
|---|---|---|---|---|
| Inference, one stream, fp32 (weights 5.6 GB incl. M-CLIP) | ~6–7 GB | ✘ | ✔ | ✔ |
| Inference, fp16 + text embeddings precomputed / CLIP on CPU (**needs code change**) | ~2–2.5 GB | ⚠ possibly, batch 1 | ✔ | ✔ |
| Full fine-tuning, one stream, fp32 AdamW + on-GPU EMA (~0.9B trainable U-Net: weights + grads + 2 Adam moments + EMA ≈ 5 × 3.5 GB) + CLIP + activations | ~20+ GB | ✘ | ✘ | ✔ (40 GB tight, 80 GB comfortable) |
| LoRA / partial FT (bottleneck only), fp16 base, gradient checkpointing | ~6–10 GB | ✘ | ⚠ plausible | ✔ |
| Reward backprop through K sampler steps | Activation memory × K (K ≤ 4 likely affordable thanks to few-step sampling) | ✘ | ⚠ K small | ✔ |
| Controller (policy over sampling/keyframe parameters, generator frozen) | Inference cost × rollouts | ✘ | ✔ | ✔ |

Other constraints:
- **Disk.** Three checkpoints are 16.7 GB; How2Sign data is ~9 GB. This approaches typical Kaggle and Colab working-disk limits [⚑ verify].
- **Software.** The pinned stack is torch 2.10 + CUDA 12.8. I believe recent CUDA-12.8 PyTorch wheels dropped Pascal (sm_60) support, which would exclude the **P100** [⚑ must verify]. T4 (sm_75) has no bf16 support [⚑].
- **Evaluation tooling.**
  - Joint-position metrics need **SMPL-X model files** (licence registration by you) and the SOKE evaluation code.
  - Rotation-space errors need neither, but are not what the paper reports.

**Feasibility verdict** [I]:
- **Controller-style RL** with a frozen SignSparK is feasible on free T4s.
- **Direct RL fine-tuning** realistically needs either parameter-efficient methods on T4 or a rented ≥ 40 GB GPU.
- **Nothing beyond small inference tests runs on the local RTX 2050.**

---

## 7. Possible RL integration points (where, not how; no MDP is proposed here)

**A. Direct fine-tuning of the generator** (policy = sampler + network)

| # | Integration point | Location | Observation |
|---|---|---|---|
| A1 | Parameters to adapt | Bottleneck transformer blocks, AdaLN-Zero projections, `embed_text`, `final_conv` (`unet_model_large.py`, `unet_model.py`) | Natural LoRA targets; zero-init gates make adapters start as identity [I] |
| A2 | Stochasticity | `rflow.sflow_sampler` is a deterministic ODE | Policy-gradient methods need a stochastic policy. Options to compare at Stage 3/4: ODE→SDE reformulation, reward-weighted / preference objectives on sampled candidates, or differentiable reward back-propagated through few sampler steps [⚑ e.g. DDPO, Flow-GRPO, Diffusion-DPO, DRaFT/ReFL: **not uploaded, must be read before use**] |
| A3 | Loss hook | `RFlow.training_losses_poses` | Where a KL/anchor-to-reference regulariser plus reward term would live; the existing CFM loss is a ready "supervised anchor" [I] |
| A4 | Unit of decision | ODE integration step over the *whole sequence*, **not frames** | Per-frame MDP formulations from autoregressive models do **not** match this architecture [I] |

**B. Controller over a frozen generator**

| # | Exposed control (verified in code) | Location | Type |
|---|---|---|---|
| B1 | Text-CFG scale γ, per sample | `classifier_free.py` | continuous |
| B2 | Which frames are anchored (keyframe subset/timing), incl. custom per-clip files | `keyframes.py`, `generate_keyframes(mode=999)` | discrete / combinatorial |
| B3 | Which joints are anchored at a keyframe | `get_keyframes_mask(joint_prob)` | discrete |
| B4 | Sequence length / inter-sign spacing (replaces the fixed 8-frame heuristic) | `y['mask']`, `lengths`; retrieval stitching | discrete / continuous |
| B5 | Number of ODE steps, sampler type | `eval.ode_stepnum`, `eval.sampler` | discrete |
| B6 | Initial noise / best-of-N candidate selection | `candidate_num`, seed | discrete. **This is also the key non-RL baseline (rerank)** [I] |
| B7 | Retrieval choices: which dictionary exemplar per gloss, placeholder length | SignSparK_Retrieval [R] | discrete. **Only for CSL-Daily/PHOENIX** |

- **Not exposed**: keyframe-guidance scale, cross-stream coupling, stream-specific text guidance [C].
- **Already measured headroom** [R]:
  - In the retrieval README, `train`-mode retrieval vs the `best_case` upper bound differs by ~2.4 PA-body and ~0.4 PA-hand on CSL-Daily.
  - This gap is a measured, bounded target for a controller over B2/B4/B7 [H].

**Evaluators available for any reward** [R][I]:
- DTW-JPE / PA-JPE against the reference (reference-based, training only).
- SignSparK-BT back-translation. Ground-truth BLEU-4 ceilings: 15.0 (Phoenix), 7.0 (CSL), 3.5 (How2Sign), so it is very sparse and noisy for How2Sign.
- Velocity, acceleration and jitter statistics (reference-free).
- **No naturalness evaluator exists. No ISL evaluator exists.**

---

## 8. Decision: retain SignSparK as our base?

**Decision (proposed): retain SignSparK *conditionally*.** It is retained only if the target language is one it supports. If the project must remain ISL/CISLR with the 152-d representation, SignSparK should **not** be the pretrained base.

| | |
|---|---|
| **Evidence** | No ISL assets (§4) · representation is 3D 6D rotations vs our 152-d keypoints, a one-way bridge only (§5) · full FT exceeds free compute (§6) · rich control surface and released evaluators for ASL/CSL/DGS (§7) |
| **Reasoning** | RL on top of a pretrained model is only interpretable if the base is in-distribution. Adapting to ISL first would confound "RL helped" with "adaptation helped" |
| **Alternatives** | (1) ISL + our own gloss→pose Transformer as base (needs the code back). (2) SignSparK + **How2Sign/ASL** (continuity with the earlier ASL scope; KF2P/GF-T2P only, no retrieval pipeline, very weak BT signal). (3) SignSparK + **CSL-Daily or PHOENIX-2014T** (full text→gloss→retrieval→SignSparK pipeline, glosses, stronger BT signal, measured retrieval headroom; not ASL/ISL). (4) SignSparK adapted to ISL (rejected for now: cost, unreleased tooling, confounding) |
| **Trade-offs** | (2)/(3) give a strong, reproducible base and genuine RL integration points, but change language. (1) keeps language but uses a weaker base and an AR stop-head |
| **Assumptions** | CISLR facts in §5 [⚑]; the released checkpoints load and run as documented (untested) |
| **Validation** | Before Stage 2: download one stream + one test LMDB on Kaggle, sample with the released config, and confirm (i) it runs, (ii) peak memory, (iii) our own baseline DTW-PA-JPE on a fixed subset. Stage 2 EDA then confirms data statistics |
| **Confidence** | **High** that SignSparK is unsuitable as-is for ISL/152-d. **Medium** on which supported language is best for RL (depends on your goals) |

My recommendation:
- If ISL is not mandatory, **option (3) (CSL-Daily or PHOENIX-2014T in the SR-T2P regime) is the strongest RL testbed**. It is the only regime where SignSparK runs end-to-end from text without oracle keyframes or length. It also has a measured gap to an upper bound and a usable back-translation evaluator.
- **Option (2) How2Sign** is the choice if ASL continuity with POSESTITCH is the priority.

---

## 9. Decision log (Stage 1)

| ID | Decision | Status | Confidence |
|---|---|---|---|
| S1-D1 | Treat code, not paper, as the authoritative model definition where they differ (velocity target, loss weights, CFG) | Proposed | High: algebraic check §1.6 |
| S1-D2 | Treat paper numbers as non-reproducible; establish our own baseline with released assets | Proposed | High: authors state this [R] |
| S1-D3 | Treat the "existing project" (CISLR, 152-d, RL code) as unverified until the code/data are provided | Proposed | High |
| S1-D4 | Do not adapt SignSparK to ISL as the first step | Proposed | High |
| S1-D5 | Retain SignSparK if the target language is ASL/CSL/DGS; otherwise revert to our own base | **Needs your decision** | Medium |
| S1-D6 | The unit of RL decision for direct fine-tuning is the ODE step over the whole sequence, not the frame (for Stage 4) | Recorded observation, not a design | Medium-high |
| S1-D7 | Best-of-N reranking with the same reward is a mandatory non-RL baseline for any controller | Proposed | High |

## 10. Open questions for you
1. **Target language and dataset.** Is ISL (CISLR) mandatory, or may we use ASL (How2Sign), CSL-Daily or PHOENIX-2014T? This decides S1-D5.
2. **Does this SLP prompt replace the POSESTITCH-SLT (ASL SLT) project, or run alongside it?** The RL-paper study is shared by both.
3. **Restore the existing code and data.** Where are the existing gloss-to-pose code, the 152-d data, the RL implementation and the reports of the earlier "metrics improved / termination deteriorated" experiments? `rlproj/src` is no longer on disk.
4. **Paste the rest of the prompt.** Please paste it from §4.5 onward.
5. **Licences.** Are you willing to register for the SMPL-X and MANO licences? They are needed for joint-position metrics and rendering.
6. **Compute.** Is a rented ≥ 40 GB GPU acceptable for direct fine-tuning, or should we restrict to controller and parameter-efficient approaches?
7. **Three truncated RL PDFs remain truncated** (sizes unchanged): `2026.findings-emnlp.1353.pdf`, `2650_RLP_…pdf`, `Learning What RL Can't…pdf`. Stage 3 needs them, plus papers on RL for diffusion/flow models if direct fine-tuning stays in scope.
8. **Optional.** The SignSparK supplementary material (FAST details, dataset statistics, sparsity ablation, retrieval details) is referenced but not in the PDF. Upload it if you can obtain it.
