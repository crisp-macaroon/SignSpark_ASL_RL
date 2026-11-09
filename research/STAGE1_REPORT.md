# Stage 1 Report — POSESTITCH-SLT: Analysis, Survey Comparison and Research Gaps

Project: RL-based enhancement of POSESTITCH-SLT (target: ASL; WLASL + How2Sign)
Stage: 1 of 9 — *awaiting approval*
Date: 2026-11-02

**Sources read in full**

| ID | Paper | File |
|---|---|---|
| [PS] | Joshi, Sharma, Singh, Modi. *POSESTITCH-SLT: Linguistically Inspired Pose-Stitching for End-to-End Sign Language Translation*. EMNLP 2025, pp. 13834–13853 | `papers/2025.emnlp-main.698.pdf` |
| [SV] | Rastgoo, Kiani, Escalera, Athitsos, Sabokrou. *A Survey on Recent Advances in Sign Language Production*. Expert Systems with Applications (preprint dated 3 June 2023; doi 10.1016/j.eswa.2023.122846) | `papers/ESWA-D-22-09727_R2.pdf …` |

**Notation used in this report**
- **[PS §x / Tab. x]** and **[SV §x / Tab. x]** point to the source.
- **⚑ Unverified** marks a claim from outside the two uploaded papers. It comes from my background knowledge and must be checked against the original paper before we rely on it.
- **(H)** marks a hypothesis. **(E)** marks an established finding, meaning it is directly supported by a source.

**Method note:** PDF text was extracted with `pypdf`. No page renderer was available, so I could not see the figures (PS Figs. 1–20, SV Figs. 1–16). They are described here from their captions and the surrounding text only.

---

## 0. Critical pre-finding: the uploaded survey is a *Production* survey, not a *Translation* survey

The instruction asks for "a survey paper covering existing Sign Language Translation methodologies". The uploaded survey covers **Sign Language Production (SLP)**, which is the text → sign direction. POSESTITCH-SLT is a **Sign Language Translation (SLT)** system, which goes sign (pose) → text.

The survey is still useful, but for a different half of POSESTITCH-SLT than intended:

| POSESTITCH-SLT component | Direction | Literature that is relevant | Covered by [SV]? |
|---|---|---|---|
| Synthetic data generator (text → stitched pose) | text → sign (production) | SLP: concatenative synthesis, motion graphs, avatars, co-articulation | **Yes, well covered** |
| Translator (pose → text Transformer) | sign → text (translation) | SLT: gloss-based and gloss-free, alignment, pretraining | **Only partly.** NSLT, HLSTM-attn, multi-channel transformers and Text2Gloss appear incidentally. 2023–2025 gloss-free SLT is absent because the survey only covers work up to 2022. |

**Consequences**
- Task 1.2 follows the survey's own SLP taxonomy, as instructed.
- Task 1.3 compares POSESTITCH-SLT against two groups of methods:
  - The **generator** is compared against SLP methods from [SV].
  - The **translator** is compared against the SLT methods that [SV] does mention, plus the SLT baselines that [PS] cites, each clearly labelled.
- There are known SLT works that bear directly on POSESTITCH-SLT's novelty and are in neither paper. These are listed in §3.5 as ⚑ Unverified. I recommend uploading them, or a recent SLT survey, before novelty claims are finalised (Decision D1, §6).

**Survey quality issues** (these matter when we cite it):
- **SLR is conflated with translation.** [SV §1] defines SLR as "a translation task from sign language into spoken language", so SLR and SLT are merged.
- **Table 9 mixes kinds of results.** [SV Tab. 9] puts SLT results (S2G2T, BLEU-4 18.13) next to SLP back-translation scores without separating them.
- **One SLT method is misfiled as SLP.** Camgoz et al. 2020 (multi-channel transformers, an SLT method) is listed under SLP "Others" with input modality "Text" [SV Tab. 4].
- **A section title misleads.** §4.2 is titled "Transformer" but mostly discusses RNNs.
- **Author names are garbled in the references.** For example, Ben Saunders is cited as "Ben, S.".

---

## 1. Task 1.1 — POSESTITCH-SLT in detail

### 1.1 Problem formulation

POSESTITCH-SLT does **gloss-free, pose-only, end-to-end SLT** [PS §3]:

- The input is a sequence of frame-wise pose vectors X = {x₁,…,x_T}, with x_t ∈ ℝ¹⁵².
- Each x_t is 76 two-dimensional keypoints taken from face, hands and upper body.
- The output is an English sentence Y = {y₁,…,y_N}.

Formally, as I've written it out (the paper states this in prose, not as an equation):

$$\hat{Y}=\arg\max_{Y} p_\theta(Y\mid X),\qquad p_\theta(Y\mid X)=\prod_{n=1}^{N}p_\theta(y_n\mid y_{<n},X)$$

The paper rules out two things explicitly:
- **Gloss annotations**, because they are costly.
- **RGB video**, because it identifies the signer and raises privacy concerns [PS §1, §3].

> **Equations caveat:** [PS] contains **no numbered equations**. Every formula in §1 is my formalisation of the paper's prose, written in its own terminology, so we can reason about it precisely. Where the prose is ambiguous I say so.

### 1.2 Motivation and existing challenges (as stated by [PS])

1. **Data scarcity.** Large sentence-aligned sign–text corpora are scarce [PS Abstract, §1].
2. **Gloss dependence.** Most prior SLT relies on intermediate glosses, which are expensive to annotate and "may strip away linguistic richness" [PS §2].
3. **Length mismatch.** Long frame sequences have to be mapped to short token sequences. Prior work handles this with CTC, frame clustering or "conceptual anchors" (GloFE) [PS §2].
4. **Privacy and fairness.** Raw video identifies the signer; pose is presented as the privacy-preserving alternative [PS §1].

The paper's central bet is to change the **data**, not the architecture. It deliberately uses a vanilla Transformer "to isolate and rigorously assess the impact of the proposed pretraining strategy" [PS §1].

### 1.3 Synthetic data generation

#### (a) BLiMP linguistic templates [PS §3, App. A.1, Tab. 2]

- **Source.** BLiMP [Warstadt et al., 2020] has 67 paradigms across 12 linguistic phenomena: anaphor agreement, argument structure, binding, control/raising, determiner–noun agreement, ellipsis, filler–gap, irregular forms, island effects, NPI licensing, quantifiers, and subject–verb agreement. The per-phenomenon counts in [PS Tab. 2] add up to 67.
- **Vocabulary.** Templates are filled only with words in the intersection of BLiMP and WLASL: **508 words** [PS Tab. 5]. For example, the Adjunct Island template is `Wh[] Aux_mat[] Subj[] V_mat[] Adv[] V_emb[] Obj[]`.
- **Output.** **BLIMP-ASL** has **2,880,008 sentences** [PS Tab. 3]. Only **456 unique words** actually occur in it, and 380 of those also occur in How2Sign-train [PS Tab. 5].
- **Rationale.** Sign-language grammar resources are lacking. The authors therefore ground generation in English grammar, "under the assumption that there exist underlying correlations between spoken and sign language grammars" [PS §3]. This is an **untested assumption** in the paper.

#### (b) WLASL vocabulary matching [PS §3, App. A, Tab. 5–6]

- **WLASL** has 2,000 isolated-sign glosses.
- **Overlaps:**
  - WLASL ∩ How2Sign-train = **1,501 of 7,430** How2Sign-train word types, about 20% of types. Token-level coverage is **not reported**.
  - WLASL ∩ BLiMP = 508.
- **Not specified in the paper:**
  - How inflected English forms (*filing*, *wears*) map to citation-form WLASL glosses (*FILE*, *WEAR*).
  - Which of the several WLASL video instances per gloss is used.

#### (c) BPCC corpus integration [PS §3, App. A.2–A.4]

1. **Source.** BPCC [Gala et al., 2023] has 230M English bitext pairs; only the English side is used.
2. **Filter.** Keep sentence S if at least 90% of its words are in the WLASL vocabulary V:
   $$\frac{|\{w\in S : w\in V_{\text{WLASL}}\}|}{|S|}\ \ge\ 0.9$$
3. **Length matching.** Short sentences are merged so the length distribution matches How2Sign. For ASL, "different combinations of sentence merging" are used [PS App. A.3].
4. **Post-processing.** Person names become `<PERSON>`, and words with frequency below 3 become `<UNKNOWN>`. This is applied to both BPCC-ASL and How2Sign-train [PS App. A.4].
5. **Output.** **BPCC-ASL** has **1,173,536 sentences** containing **4,613 unique words**. Only **1,943** of these are WLASL words [PS Tab. 6].

> **(E) Text–pose mismatch.** 4,613 − 1,943 = **2,670 word types in BPCC-ASL have no WLASL sign.** The 90% threshold allows up to 10% unmatched tokens per sentence. The paper does not say what pose, if any, is stitched for these tokens. If none is, the target text contains words with no visual evidence, which plausibly trains hallucination (H). This must be checked in the repository (Q4).

### 1.4 Pose extraction and representation [PS §3, App. B.2]

- **Extractor.** MediaPipe Holistic is applied to every WLASL and How2Sign video.
  - The paper says MediaPipe "gives 576 key points", but its own breakdown (21 + 21 + 33 + 468) sums to **543**. This is a minor internal inconsistency.
- **Selected keypoints (76), following GloFE:**
  - Hands: all 42 (21 per hand).
  - Body: 11 of 33. Legs, hips, eye-corner, mouth and finger-proxy landmarks are dropped.
  - Face: 23 of 468. Mouth corners, lips, eyebrows, eye contours and nose top.
- **Feature vector.** (x, y) for each keypoint gives x_t ∈ ℝ¹⁵². There is no z coordinate and no confidence channel.
- **Missing data.** A keypoint with confidence below 0.8 is replaced by the value from the nearest (left or right) frame where it is confident.
- **Normalisation.** Sequences are "normalized to reduce inter-signer variance" [PS §3]. **The method is not specified.**

### 1.5 Pose stitching: Same Word Order and Random Word Order [PS §3, App. C, D.4]

For a generated sentence w₁…w_K, let P_k ∈ ℝ^{T_k×152} be the WLASL pose sequence for word w_k. The stitched sequence is:

$$X^{\text{syn}}=\mathrm{Sub}_s\!\Big(\mathrm{Smooth}\big(P_{\pi(1)}\oplus P_{\pi(2)}\oplus\cdots\oplus P_{\pi(K)}\big)\Big)$$

| Variant | Permutation π | Purpose stated in [PS] |
|---|---|---|
| **SWO** (Same Word Order) | identity, so the English order is kept | Preserve "syntactic structure and compositional cues" |
| **RWO** (Random Word Order) | uniform random permutation | Inject "syntactic noise", encourage "flexible and robust representations" |

- **Choice of order.** English order is used as a proxy for ASL order because ASL parsers and corpora are lacking.
- **What this produces.** The synthetic sequences are closer to *signed English* (function words signed, in English order) than to ASL. ASL is topic–comment, drops many function words, and uses space, classifiers and non-manual grammar. This is my characterisation, though it follows from [PS]'s own limitation statement.

### 1.6 Boundary-aware temporal smoothing [PS §3]

The **entire specification** in the paper is one sentence: "we apply boundary-aware temporal smoothing (Bulas-Cruz et al.)".

- The citation, *A temporal smoothing technique for real-time motion detection* (CAIP), is a motion-detection paper, not a pose-interpolation method.
- **No formula, window size, boundary length or parameters are given.**
- **No ablation** with and without smoothing is reported.

> **(E) Stitching is underspecified.** The boundary operator is the part of POSESTITCH-SLT that most directly determines realism, and it is unspecified and unevaluated. Recovering it from the code is a Stage-6 priority (Q1).

### 1.7 Frame-rate / temporal matching [PS App. B.1, App. C]

Dictionary signs are slow citation forms, so stitched sequences are much longer than real ones. The paper handles this as follows:

- **Global subsampling.** Every s-th frame is kept, with
  $$s=\frac{\bar T_{\text{syn}}}{\bar T_{\text{real}}}$$
  The extracted text renders this as "xy", which is x/y. For How2Sign, s = 3; for iSign, s = 4 [PS Tab. 9].
- **Random skip.** A random frame skip in [1, 3] is added "to support generalization".
- **Truncation.** Sequences are cut at 300 frames [PS Tab. 9].

Matching is done **at the dataset level, on the mean only**. There is no per-sign duration modelling, no trimming of the rest pose at the start and end of each WLASL clip (not mentioned), and no transition timing.

### 1.8 Transformer architecture [PS App. C.1, Tab. 9]

| Component | How2Sign setting |
|---|---|
| Encoder | BERT (Hugging Face), 2 layers, hidden size 512, 4 heads. Pose features are fed "directly"; the projection 152 → 512 is *not described* (Q9). |
| Decoder | GPT-2 with cross-attention, 2 layers, hidden size 512, 4 heads |
| Tokeniser | BPE, vocabulary 15,000, trained on synthetic and real text |
| Optimiser | AdamW, learning rate 1e-4, weight decay 0.01, batch size 16, dropout 0.3 |
| Schedule | constant with warm-up (warm-up ratio 0.1) |
| Decoding | beam size 3, maximum length 128 |
| Input limit | 300 frames, sampling step s = 3 |

The model is small; I estimate tens of millions of parameters at most, to confirm in Stage 6. It uses no pretrained language-model weights, no CTC and no auxiliary loss.

### 1.9 Synthetic-to-real blending (linear annealing) [PS §3, App. C, C.2]

At training step t, draw u ~ U(0, 1). Take a **real** How2Sign sample if u < p(t), otherwise a **synthetic** sample, where

$$p(t)=0.85\cdot\min\!\left(1,\ \frac{t}{60{,}000}\right)$$

So training starts fully synthetic, the real share ramps linearly to 85% at step 60k, and after that 15% of samples are still synthetic.

- **Training loss** (my formalisation): token-level cross-entropy under the time-varying mixture
  $$\mathcal L(\theta)=-\,\mathbb E_{(X,Y)\sim p(t)\mathcal D_{\text{real}}+(1-p(t))\mathcal D_{\text{syn}}}\sum_{n}\log p_\theta(y_n\mid y_{<n},X)$$
- **Claim without evidence.** The authors say this works better than disjoint pre-training followed by fine-tuning and prevents catastrophic forgetting [PS §3]. **No numbers are given for that comparison**, and the 0.85 / 60k values are not ablated.

### 1.10 Training procedure: end-to-end data flow

```
INPUTS                      INTERMEDIATE REPRESENTATIONS                         OUTPUT
BLiMP templates ─┐
WLASL vocab (2k) ┼─► V = BLiMP∩WLASL (508) ─► template filling ─► BLIMP-ASL text (2.88M)
BPCC (230M EN) ──┴─► ≥90% WLASL-word filter ─► length merging ─► <PERSON>/<UNKNOWN> ─► BPCC-ASL text (1.17M)
                                                                       │
WLASL videos ─► MediaPipe Holistic ─► 76 kp × (x,y) = 152-d ─► conf<0.8 fill ─► normalise ─► per-word pose bank
                                                                       │
            for each sentence: look up P_k per word ─► order π (SWO|RWO) ─► concatenate ─► boundary smoothing
                                ─► subsample every s-th frame (+ random skip 1–3) ─► truncate 300 ─► X_syn ∈ ℝ^{T×152}
How2Sign videos ─► same pose pipeline ─► X_real ;  How2Sign text ─► Y_real
                                                                       │
Sampler: real with prob p(t)=0.85·min(1,t/60k), else synthetic ─► (X, Y) batches of 16
   ─► BERT encoder (2L, 512) ─► GPT-2 decoder w/ cross-attn (2L, 512, BPE-15k) ─► CE loss ─► AdamW
Inference: X_test (How2Sign pose) ─► beam search (3) ─► English sentence Ŷ
```

### 1.11 Evaluation methodology [PS §4]

- **Metrics.** BLEU-1 to BLEU-4 and ROUGE-1/2/L, following the GloFE protocol. SacreBLEU is given for the best model only [PS Tab. 13].
- **Datasets.** How2Sign (ASL) and iSign (ISL), dev and test splits.
- **Baselines.** GloFE (Lin et al., 2023) and Álvarez (a How2Sign Transformer thesis), plus their own "w/o Pose Stitched" model: the same architecture trained on real data only.
- **Additional analyses:**
  - Accuracy on unseen *synthetic* sentences [PS Fig. 19].
  - SBERT-similarity subsets, run on iSign only [PS Tab. 7].
  - Qualitative examples [PS Tab. 10–11].
- **Not reported:** multiple seeds, variance, confidence intervals, significance tests, human evaluation, or smoothing and annealing ablations.

### 1.12 Reported results (ASL / How2Sign only)

[PS Tab. 1] (BLEU) and [PS Tab. 12] (ROUGE-L):

| Model | Dev B-1 | Dev B-4 | Test B-1 | Test B-2 | Test B-3 | Test B-4 | Test ROUGE-L |
|---|---|---|---|---|---|---|---|
| Álvarez | 17.73 | 2.24 | 17.40 | 7.69 | 3.97 | 2.21 | – |
| GloFE | 14.92 | 2.27 | 14.86 | 6.99 | 3.64 | 1.97 | 13.27 (GloFE-VN) |
| w/o Pose Stitched (own baseline) | 22.19 | 3.37 | 18.16 | 7.96 | 4.33 | **2.62** | 13.98 |
| RWO + BPCC | 26.25 | 4.62 | 26.70 | 12.90 | 7.23 | 4.32 | 17.53 |
| RWO + BLiMP | 26.22 | 5.04 | 25.17 | 12.26 | 7.15 | 4.53 | 16.83 |
| SWO + BPCC | **27.35** | 4.95 | **26.74** | 12.86 | 7.26 | 4.44 | **17.94** |
| SWO + BLiMP | 26.89 | **5.04** | 25.98 | 12.55 | 7.25 | **4.56** | 16.96 |

**What these numbers actually support (my analysis):**

1. **(E) Their own baseline already beats GloFE.** "w/o Pose Stitched" scores 2.62 test BLEU-4 against GloFE's 1.97. Of the headline +2.59 over GloFE (1.97 → 4.56):
   - about **+0.65 comes from the baseline setup**: architecture, preprocessing, tokenisation and BLEU implementation;
   - about **+1.94 comes from stitched data**: 2.62 → 4.56, which is +74% relative.

   The paper acknowledges it could not fully reproduce GloFE [PS Limitations].
2. **(E) The bracketed "improvements" in [PS Tab. 1] use different baselines in different columns.** Each one is measured against whichever prior system was strongest in that column (Álvarez or GloFE). The abstract's "1.97 → 4.56" uses GloFE.
3. **(E) SWO and RWO are nearly indistinguishable on How2Sign** (test B-4 4.56 vs 4.53 for BLiMP). With one run per cell, **the data cannot show that the word order of the stitched signs matters for ASL.** BLiMP-ASL (456 word types) ≈ BPCC-ASL (4,613 types) on test B-4 is equally inconclusive.
   - **(H)** The gain may come mostly from *pose-dynamics pretraining and regularisation* rather than from lexical or syntactic transfer. This is testable (G-O3).
4. **(E) The SacreBLEU table is consistent with the BLEU table, but its labels mislead.**
   - The "SacreBLEU1–4" values in [PS Tab. 13] are **n-gram precisions**, not cumulative BLEU-n.
   - Check: the geometric mean of (25.97, 6.06, 2.41, 1.13)% is **4.55**, which matches test BLEU-4 = 4.56. Dev reconstructs to 5.03 vs the reported 5.04.
   - **Implication:** test **4-gram precision is ≈1.1%**. Almost no predicted 4-gram matches the reference, so **sentence-level BLEU-4 will be 0 for most test sentences.** This is directly relevant to any future reward design (§4, gap Tr-2).
5. **(E) Absolute quality is very low.** Test BLEU-4 is about 4.6 and BLEU-1 about 26. Differences of a few tenths of BLEU between variants are within plausible seed noise, and no variance is reported.
6. **Synthetic "generalisation".** BLEU-4 of 97 and 47 on unseen synthetic sentences [PS §4, Fig. 19] is **in-distribution**: same templates and vocabulary. The authors themselves attribute it to "enormous dataset size with less vocabulary". It does not show real-world generalisation.
7. **Similarity analysis.** Sentences more similar to the synthetic data score higher (4.00 vs 2.88 test BLEU-4 for the most vs least similar BPCC-ISL subsets) [PS Tab. 7]. This was measured **on iSign only**. It suggests data selection matters, but it is correlational and not shown for ASL.
8. **Qualitative failures.** Repetition ("magic magic magic") and hallucination [PS Tab. 10, §4] are attributed by the authors to "synthetic data noise".

### 1.13 Limitations

**Stated by [PS]:**
- Vocabulary coverage is limited (2k–4.5k words).
- No sign-language grammar; English order is used instead.
- The architecture is deliberately simple, and GloFE could not be fully reproduced.
- Generality to other languages depends on word-level datasets existing.

**Not stated, identified here** (each traced to evidence above):
1. The boundary smoothing is unspecified and unablated (§1.6).
2. Co-articulation is not modelled: each sign is a citation form, with probable rest poses between signs (§1.7).
3. Sign identity changes at every word: each WLASL word comes from a different signer, camera set-up and scale, and the normalisation is unspecified (§1.4).
4. The text–pose mismatch in BPCC-ASL (2,670 types with no sign) and the unspecified lemma/inflection mapping (§1.3).
5. The synthetic data is open-loop: it is generated once, with no feedback from the translator about which data helps.
6. The data pipeline is set by hand: 90% match, s, 0.85, 60k, the [1, 3] skip. None of it was tuned or ablated.
7. Statistical reporting is weak: one seed, no CIs, no significance tests.
8. The comparison is narrow: only GloFE and Álvarez for ASL. Large-scale pose pretraining approaches are not compared (§3.5).
9. Pre-training without paired data is not tested, so it is unclear whether the gain is linguistic.
10. Minor reporting inconsistencies: MediaPipe 576 vs 543; Tab. 13 labels; the iSign "w/o" test ROUGE-1 of 1.49 vs dev 9.23, which is implausible and probably a typo; ISL is outside our scope anyway.

---

## 2. Task 1.2 — The survey's taxonomy and methods

### 2.1 Survey taxonomy (reconstructed from [SV §5] text; Fig. 3 is an image I could not view)

```
SLP taxonomy [SV §5]
├── 5.1 Input modalities
│     ├── Visual: RGB (image/video), Skeleton
│     └── Lingual: Text (and audio/speech)
├── 5.2 Datasets  (Tab. 1: ASLLVD, ATIS, Dicta-Sign, ASL-LEX, PHOENIX14T, Deep JSLC, KETI, Content4All, How2Sign …)
├── 5.3 Applications & technologies
│     ├── Projects (TEAM, SASL-MT, ViSiCAST, WebSign, SignSynth …)
│     └── Assistive tech (hearing technology, alerting devices, communication support)
└── 5.4 Proposed models
      ├── 5.4.1 Avatar approaches
      ├── 5.4.2 NMT approaches
      ├── 5.4.3 Motion Graph (MG) approaches
      ├── 5.4.4 Conditional image/video generation
      └── 5.4.5 Other models
```

[SV] adds two more organising devices:
- **Backbones** [SV §4]: CNN, Transformer/RNN, generative models, motion capture and avatars.
- **General SLP pipeline** [SV §6, Fig. 13]: text/speech → gloss → skeleton → image/video.

### 2.2 Methods by the survey's own categories

The year, category, input, dataset, metrics and pros/cons come from [SV Tab. 4, 5, 9] and the body text. A cell marked "n/s" means the survey does not state it. Bracketed notes in *italics* are my clarifications.

**5.4.1 Avatar approaches**

| Method | Year | Input | Architecture / technique | Gloss | Pose vs video | Strategy | Dataset | Metrics | Strengths [SV] | Limitations [SV] |
|---|---|---|---|---|---|---|---|---|---|---|
| Kipp et al. | 2011 | gloss / RGB video | procedural avatar plus "torso" and "noise" methods | yes (gloss-based tool) | avatar (3D) | rule- or parameter-driven animation | ViSiCAST | new avatar-vs-human comparison metric | content-evaluation metric | lacks non-manual features |
| McDonald et al. | 2016 | RGB video | spine and shoulder IK (Eq. 1–3: V_R, V_L, V_reach) | n/s | avatar | procedural realism layer | own | n/s | automatic realism, low compute | shoulder/torso placement issue |
| Gibet et al. (Sign3D) | 2016 | mocap | mocap-driven avatar | n/s | avatar (mocap) | data-driven animation | own | n/s | high viewer acceptance | small phrase set; not scalable |
| Parametrised-gloss avatars (ViSiCAST, Tessa, eSign, Dicta-Sign, JASigning, WebSign) | 2000–2022 | HamNoSys / SigML transcription | rule-based synthesis | yes (transcription) | avatar | symbolic | – | – | controllable | robotic motion, missing non-manuals, uncanny valley, need expert annotation |

**5.4.2 NMT approaches**

| Method | Year | Input | Architecture | Gloss | Pose vs video | Strategy | Dataset | Metrics | Strengths | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| Othman & Jemni | 2011 | English text | statistical IBM models 1/2 (Eq. 4–5) | ASL gloss-text target | – | word alignment | n/s | n/s | explicit alignment | statistical, word-level |
| Camgoz et al. (NSLT) | 2018 | RGB video | CNN + attention seq2seq (Eq. 7) | variants with and without gloss (S2G2T) | video | *SLT direction* | PHOENIX14T | BLEU, ROUGE (S2G2T B-4 18.13) | joint align / recognise / translate | needs spatial alignment |
| Guo et al. (HLSTM-attn) | 2018 | RGB video | 3D-CNN + hierarchical LSTM encoder–decoder | n/s | video | *SLT direction* | own | Acc, CIDEr, METEOR, WER, BLEU | handles word order vs visual content | generalisation to other datasets |
| Stoll et al. (Text2Sign) | 2020 | text | NMT (text→gloss) + MG + GAN | yes | pose → video | text→gloss→pose→video | PHOENIX14T | BLEU-4 15.26 (Text2Gloss), SSIM 0.727, FID 64.01 | minimal annotation | high complexity |

**5.4.3 Motion Graph approaches** (closest SLP category to stitching)

| Method | Year | Input | Technique | Transition handling | Notes |
|---|---|---|---|---|---|
| Kovar et al. | 2002 | mocap | directed graph over clips; frame distance = point-cloud distance; path cost f(w) = Σᵢ g([e₁…e_{i−1}], eᵢ) (Eq. 8); branch-and-bound search | alignment + interpolation at transitions | general graphics; cited by [SV] as a foundation |
| Arikan & Forsyth | 2002 | mocap | score S = w_c Σ cost(eᵢ) + w_f F + w_b B + w_j J (Eq. 9) over position / velocity / acceleration; random search | smoothing function at clip discontinuities | **multi-term, weighted transition objective** |
| Lee & Shin | 1999 | mocap | two-layer representation: first-order Markov transitions on joint-angle and velocity distances, plus cluster forest | curve fitting | |
| Stoll et al. (MG in SLP) | 2020 | gloss | glosses embedded as MG nodes; **transition probabilities given by the NMT decoder** at each step | learned transition prior | links translation to motion selection |

[SV] gives these MG limitations:
- Data access.
- Graph scalability and branching factor.
- Pruning should use sign-specific features such as duration and speed of motion [SV §8].

**5.4.4 Conditional image/video generation**

| Method(s) | Year | Technique | Notes |
|---|---|---|---|
| VAE+GAN for people/sign video (Ma 2017; Siarohin 2018; Stoll 2018; Vasani 2020; Saunders 2020d; Natarajan 2022) | 2017–2022 | hybrid VAE/GAN pose-to-video | photorealism; mode collapse and instability noted |
| EDN, vid2vid, Pix2PixHD (as SLP renderers) | 2018–2019 | video synthesis | SSIM 0.737–0.750, FID 41.5–56.2 [SV Tab. 9] |

**5.4.5 Other models**

| Method | Year | Input | Architecture | Gloss | Output | Dataset | Metrics [SV Tab. 9] | Strengths | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| Progressive Transformers (Saunders) | 2020 | text / gloss | Transformer with counter decoding; adversarial training (Eq. 10) | both | continuous skeleton | PHOENIX14T | back-translation B-4 10.43 (text); Symbolic Transformer 19.10 | dynamic output length | non-manuals, realism |
| Zelinka & Kanis (NSLS) | 2020 | text | feed-forward + recurrent transformer, attention-weighted loss (Eq. 11) | n/s | skeleton | Czech news | MSE 11.94 | robust to missing skeleton parts | facial expression |
| SignGAN (Saunders, Everybody Sign Now) | 2020 | text | Transformer + MDN → pose → GAN video (Eq. 12) | n/s | photo-real video | PHOENIX14T | B-4 12.18, SSIM 0.759, FID 27.75 | non-manual production | realism |
| Tornay et al. | 2020 | produced sign | KL-HMM lexeme- and form-level **assessment** (Eq. 13–14) | – | score | SMILE DSGS | S_lex, S_form | **linguistic quality metric for produced signs** | correct lexeme, wrong form |
| SGSA (Saunders) | 2021 | text | skeletal-graph self-attention | n/s | skeleton | PHOENIX14T | +7% relative | skeleton inductive bias | – |
| Multi-channel transformers (Camgoz) | 2020 | *(listed as text; actually an SLT method)* | multi-articulatory transformer | no gloss | – | PHOENIX14T | – | no gloss needed | complexity |
| Kissel et al. | 2021 | pose | Soft-Gated Warping-GAN | n/s | video | MS-ASL | – | signer-independent | realism |
| DualSign (Huang) | 2022 | text | MM-T2G + MT-G2P, dual transformation (BM3T-DT) | partial gloss | pose | PHOENIX14T | – | semi-supervised, uses unlabelled data | modality imbalance |
| GEN-OBT (Tang) | 2022 | gloss | Transformer gloss encoder + pose decoder + **online CTC back-translation** | yes | pose | PHOENIX14T | – | semantic preservation via back-translation | complexity |
| SynLibras (Silveira) | 2022 | pose | appearance/gesture disentanglement | n/s | image | Libras + PHOENIX | – | controllable factors | complexity |

**Survey-level conclusions relevant to us** [SV §4.4, §7.2, §8]:
- "Motion edition operations, such as concatenation and mixing, are applied to mocap data to compose new utterances… However, manipulating existing movements **does not guarantee the semantic consistency** of the reconstructed signs" [SV §4.4]. This is a direct statement of the risk in pose stitching.
- Future directions [SV §8]: multi-signer generation, structured spatio-temporal modelling (GNNs), domain priors, and MG pruning that uses duration and speed of motion.
- Evaluation of SLP is dominated by BLEU (via back-translation) plus SSIM, PSNR, MSE and FID [SV §7.1, Tab. 3, 9].

---

## 3. Task 1.3 — Comparative analysis

### 3.1 Matrix A: translator side (sign → text)

Rows marked † come from [PS]'s related work, not from [SV].

| System | Gloss | Input | Intermediate representation | Temporal alignment | Architecture | Synthetic data | Augmentation / pre-training | Low-resource handling | Linguistic modelling | Compute |
|---|---|---|---|---|---|---|---|---|---|---|
| **POSESTITCH-SLT** | **free** | **2D pose (152-d)** | none | implicit (cross-attention); 300-frame truncation; global subsampling | vanilla BERT-enc / GPT2-dec, 2+2 layers | **yes: 4M stitched pose–text pairs** | blended synthetic→real curriculum | synthetic pairs from isolated-sign data | English grammar templates (BLiMP); English order | very low (small model, 152-d input) |
| NSLT (Camgoz 2018) [SV] | gloss-free and gloss-based variants | RGB video | CNN features (± gloss) | attention | CNN + RNN attention seq2seq | no | ImageNet CNN | – | gloss as intermediate in S2G2T | high (video CNN) |
| HLSTM-attn (Guo 2018) [SV] | n/s | RGB video | 3D-CNN clip features | hierarchical LSTM | 3D-CNN + LSTM | no | – | – | – | high |
| Sign Language Transformers (Camgoz 2020, CVPR)† | gloss (CTC) jointly | RGB video | gloss-level CTC | **CTC** | Transformer | no | pretrained CNN | – | gloss supervision | high |
| Multi-channel transformers (Camgoz 2020) [SV]† | free | multi-articulator features | per-channel | attention | multi-channel Transformer | no | – | – | articulatory channels | medium–high |
| STMC-Transformer (Yin & Read 2020)† | gloss-based | video → gloss | gloss | gloss recognition | STMC + Transformer | no | – | – | gloss | high |
| GloFE (Lin 2023)† | free | **pose** | **conceptual anchors** from text tokens | anchor-based weak alignment | Transformer + anchor modules | no | – | – | weak semantic anchors | low–medium |
| Moryossef et al. 2021 (data augmentation for gloss translation)† | gloss | text-like glosses | gloss | – | NMT | **yes (rule-based gloss augmentation)** | yes | yes | rule-based | low |

### 3.2 Matrix B: generator side (text → sign), POSESTITCH's synthesiser vs SLP methods

| System | Unit retrieved / produced | Transition / co-articulation handling | Learned? | Linguistic modelling | Uses gloss | Purpose | Evaluation of produced signs |
|---|---|---|---|---|---|---|---|
| **POSESTITCH generator** | **isolated WLASL pose clip per English word** | "boundary-aware temporal smoothing" (unspecified) + global subsampling | **no** | BLiMP templates / BPCC; English or random order | no (English words as keys) | **data augmentation for SLT** | **none directly**; only downstream BLEU |
| Avatar concatenation / mocap editing [SV §4.4, §5.4.1] | mocap segments / parametrised signs | concatenation + mixing, IK realism layers | no (procedural) | rule grammars (TEAM, ViSiCAST) | transcription | production for Deaf users | viewer acceptance |
| Motion graphs (Kovar; Arikan & Forsyth) [SV §5.4.3] | mocap clips as graph edges | **explicit transition cost** over position, velocity, acceleration (Eq. 8–9); search over paths | no (search) | none / user constraints | – | motion synthesis | path cost |
| Text2Sign MG (Stoll 2020) [SV] | motion primitives per gloss | MG transitions with **NMT-decoder probabilities** | partly | text→gloss NMT | yes | SLP | BLEU, SSIM, FID |
| Progressive Transformers / SignGAN [SV] | continuous skeleton (generated) | learned in the model | yes | text/gloss → pose | both | SLP | back-translation BLEU, FID |
| GEN-OBT [SV] | pose (generated) | learned | yes | gloss → pose, CTC back-translation | yes | SLP | back-translation |
| Signing at Scale (Saunders 2022)⚑ | dictionary signs + **learned co-articulation** | learned stitching / co-articulation model | yes | – | yes | large-scale SLP | ⚑ |

*Signing at Scale appears only in [SV]'s reference list (cited at [SV §5.4.4]); [SV] does not discuss it. Its description here is ⚑ Unverified.*

### 3.3 Dimension-by-dimension comparison

1. **Gloss-based vs gloss-free.** POSESTITCH-SLT is fully gloss-free in both data generation and training. It shares this with GloFE and the gloss-free variants of NSLT and multi-channel transformers. Its distinctive move is to use **English words as keys into an isolated-sign lexicon**, which acts as a *gloss proxy* during data generation without any gloss annotation.
2. **Video vs pose.** It is pose-only, like GloFE. Most systems in [SV] (NSLT, HLSTM-attn) use RGB video. Pose input gives privacy and low compute, at the cost of losing hand-shape detail and depth (2D only, 76 points).
3. **Intermediate representations.** There are none, by design. Compare CTC glosses (Sign Language Transformers), conceptual anchors (GloFE), and the gloss → skeleton → video pipeline in SLP [SV §6].
4. **Temporal alignment.** This is the weakest dimension. Alignment is left entirely to cross-attention. The synthetic data imposes clean, monotone, one-sign-per-word segmentation that real How2Sign signing does not have, and there is no CTC or anchor loss to use that structure.
5. **Transformer architectures.** POSESTITCH-SLT deliberately uses the plainest option. It contributes nothing architecturally, by design.
6. **Synthetic data generation.** This is the core contribution. The closest analogue inside [SV] is concatenative / MG synthesis, but there it is used for *production*, not for *augmenting translation*. The closest analogue overall is likely sign back-translation (⚑ SignBT, §3.5).
7. **Augmentation and pre-training.** The blended curriculum is a known multi-domain sampling idea applied to SLT. It is not compared against pretrain-then-finetune in the paper.
8. **Low-resource settings.** POSESTITCH-SLT exploits the fact that isolated-sign datasets are relatively plentiful. It only reaches about 20% of How2Sign word types.
9. **Linguistic modelling.** English templates and English order. [SV §3.2] lists sign grammar and "synchronised multi-modal" (manual + non-manual) structure as core challenges, and POSESTITCH-SLT does not address either: synthetic non-manuals are whatever appears in the isolated clips.
10. **Computational efficiency.** Very cheap: 152-d input and a small model. Practical concern (estimate): storing about 4M pre-stitched sequences would cost on the order of hundreds of GB, assuming about 100 frames × 152 floats × 4 bytes each. **On-the-fly stitching from a per-word pose bank** is the feasible design for our hardware. To check in Stage 6.

### 3.4 Novelty decomposition of POSESTITCH-SLT

This assesses POSESTITCH-SLT's novelty, not ours.

| Component | Classification | Evidence / prior art |
|---|---|---|
| Using **linguistic minimal-pair templates (BLiMP)** as a sentence source for SLT pre-training | **Genuinely new** relative to both uploaded papers | No analogue in [SV]; [PS] presents it as new |
| **Pose-level synthesis from public isolated-sign datasets for gloss-free pose-based SLT, at multi-million scale** | **New in this combination.** Partly anticipated (⚑ SignBT splices *feature-level* segments via glosses) | [SV §4.4] concatenation; ⚑ Zhou et al. 2021 |
| **Blended progressive synthetic→real sampling** in SLT | New *application* of a standard curriculum / mixture idea | Multi-domain NMT practice; not ablated |
| **SWO vs RWO sensitivity probe** | New analysis; inconclusive for ASL | [PS Tab. 1] |
| Concatenating sign units into sentences | **Adaptation** | Avatars / mocap concatenation [SV §4.4]; motion graphs [SV §5.4.3]; ⚑ Signing at Scale |
| Boundary smoothing | **Adaptation** (classical signal smoothing) | Bulas-Cruz et al. |
| Synthetic parallel data from monolingual text | **Adaptation** of back-translation | ⚑ Sennrich et al. 2016; ⚑ SignBT |
| BERT / GPT-2 encoder–decoder, BPE, beam search | **Established** | Vaswani 2017; Devlin 2019; Radford 2019 |
| 76-keypoint selection, MediaPipe | **Adopted** from GloFE | [PS App. B.2] |
| Similarity-based diagnostic (SBERT) | Established tool, new diagnostic use | [PS Tab. 7] |

**Limitations POSESTITCH-SLT shares with existing methods:**
- Data scarcity.
- Absence of sign grammar and non-manual modelling, which is shared with avatars and SLP [SV §5.4.1, §3.2].
- Very low absolute BLEU on How2Sign.
- BLEU-only automatic evaluation.
- Signer variability.

**Limitations that are insufficiently addressed, in POSESTITCH-SLT and in the uploaded literature:**
1. Transition and co-articulation realism of *synthetic training data*. SLP addresses it for production only.
2. **No closed loop** between the data generator and the downstream translator.
3. Selection of which synthetic data to generate or use.
4. Statistical rigour of evaluation.

### 3.5 ⚑ Prior art missing from both papers (verify before any novelty claim)

| Work | Why it matters | Status |
|---|---|---|
| Zhou et al., *Improving SLT with Monolingual Data by Sign Back-Translation* (SignBT), CVPR 2021 | Builds synthetic sign–text pairs by **splicing per-gloss feature segments** from a sign bank. This is the closest conceptual predecessor of pose stitching for SLT, and [PS] does not cite it. | ⚑ Please upload |
| Saunders, Camgoz, Bowden, *Signing at Scale: Learning to Co-Articulate Signs…*, CVPR 2022 | **Learned co-articulation between stitched dictionary signs**. This is a direct baseline for any improved stitching. | In [SV] references only; ⚑ upload |
| Walsh, Saunders, Bowden, *Sign Stitching* (2024) | Stitching with normalisation, frame selection and smoothing, for production | ⚑ Please upload |
| Uthus et al., *YouTube-ASL* (NeurIPS 2023 D&B); Rust et al., *SSVP-SLT* (ACL 2024) | Large-scale ASL pre-training that reports **much higher How2Sign BLEU** than [PS]. This sets the realistic ceiling, and [PS] does not compare against it. | ⚑ Numbers not verified; please upload |
| Ranzato et al. 2016 (MIXER); Shen et al. 2016 (MRT); Edunov et al. 2018; Choshen et al. 2020 (*On the Weaknesses of RL for NMT*) | Sequence-level and RL training for NMT, including **known negative results** | ⚑ Stage 2/3 relevance |
| Graves et al. 2017 (*Automated Curriculum Learning*); Wang et al. 2020 (*Differentiable Data Selection*) | Bandit or learned data scheduling and selection | ⚑ Stage 2/3 relevance |

---

## 4. Task 1.4 — Preliminary research gap report

**Format.** Each gap gives:
- **Evidence:** what supports it.
- **Papers:** relevant work.
- **Why it matters.**
- **Hypothesis**, marked **(H)**.
- **Evaluation:** how it would be tested.

**Scope.** Gaps are tagged by category. I've deliberately left out MDP, algorithm and reward design (Stage 4/5). Where RL might plausibly apply, I only note *whether a feedback signal exists*.

### Data generation gaps

**D-1. Target-unaware data selection**
- **Evidence (E):**
  - BPCC sentences are chosen only by the 90% vocabulary match plus length merging.
  - Higher similarity to the target set correlates with higher BLEU [PS Tab. 7, iSign].
  - BLiMP vs BPCC gives different winners on How2Sign vs iSign [PS Tab. 1].
- **Papers:** [PS]; ⚑ DDS, Moore–Lewis-style selection.
- **Why it matters:** with millions of candidate sentences and a fixed compute budget, *which* synthetic pairs are used may matter more than how many.
- **(H)** At equal synthetic budget, selecting or weighting synthetic sentences by their utility for How2Sign improves test SacreBLEU over uniform sampling.
- **Evaluation:**
  - Equal-budget comparisons on How2Sign test, with ≥3 seeds and paired bootstrap.
  - Strong non-RL baselines: SBERT-similarity top-k, cross-entropy-difference selection, importance resampling.
- **Feedback signal:** dev-set performance or a proxy exists, but it is **expensive and delayed**.

**D-2. Text–pose mismatch and lexical mapping noise**
- **Evidence (E):**
  - 2,670 BPCC-ASL word types have no WLASL sign [PS Tab. 6].
  - Low-frequency words are mapped to `<UNKNOWN>`.
  - Inflection mapping is unspecified.
  - Hallucinations and repetition appear in outputs [PS Tab. 10].
- **Why it matters:** targets containing words that are not signed teach the decoder to produce unsupported content.
- **(H)** Removing or flagging unsigned tokens lowers the hallucination rate without hurting BLEU.
- **Evaluation:**
  - Hallucination rate, i.e. output words absent from the reference and from any signed lexeme.
  - Repetition rate.
  - SacreBLEU.

**D-3. Hand-set, non-adaptive synthetic→real schedule**
- **Evidence (E):**
  - The linear p(t) with 0.85 / 60k is not ablated.
  - The claimed superiority over pretrain-then-finetune comes without numbers [PS §3, App. C.2].
- **Papers:** [PS]; ⚑ Graves et al. 2017.
- **(H)** A schedule that adapts to the learner's state outperforms the fixed linear schedule at equal steps. Sub-hypothesis to test *first*: a tuned fixed schedule may already capture most of the gain.
- **Evaluation:**
  - Schedule sweeps (linear, step, exponential, pretrain-then-finetune) vs an adaptive schedule.
  - SacreBLEU and convergence speed.
- **Feedback signal:** learning progress or dev loss is cheap and frequent, which makes this a **natural candidate for a bandit-style formulation** (to be argued in Stage 3/4, not assumed).

### Pose stitching gaps

**P-1. No modelling of transitions or co-articulation; smoothing unspecified and unevaluated**
- **Evidence (E):**
  - [PS §3] gives a single sentence on smoothing.
  - [SV §4.4] notes that concatenation "does not guarantee the semantic consistency".
  - MG work defines explicit position / velocity / acceleration transition costs [SV Eq. 8–9].
  - ⚑ Signing at Scale learns co-articulation.
- **Why it matters:** real How2Sign signing is co-articulated. Stitched data has unnatural boundaries, so at test time the model sees boundary statistics it has never been trained on.
- **(H)** Synthetic data whose boundary kinematics are closer to real signing (lower position, velocity and acceleration discontinuity) improves downstream translation.
- **Evaluation:**
  - Boundary discontinuity metrics (Δposition, Δvelocity, Δacceleration at joins) vs the same statistics on real How2Sign.
  - Smoothing ablation: none vs [PS] vs principled.
  - Downstream SacreBLEU.
- **Critical caveat for Stage 3/4.** If the transition cost is *additive and known* (as in [SV Eq. 8]), choosing transitions for a *fixed* word sequence is solvable exactly by **dynamic programming or graph search**. RL is justified only if the objective is non-decomposable, for example downstream translation utility, or if the action space is too large for exact search. *Any RL stitching proposal must beat a motion-graph / DP baseline.*

**P-2. Unspecified WLASL instance selection and per-word signer heterogeneity**
- **Evidence (E):**
  - WLASL has multiple instances per gloss; the selection policy is not stated.
  - Each word comes from a different signer.
  - Normalisation is unspecified [PS §3].
- **(H)** Choosing instances for intra-sentence signer consistency, or for controlled diversity, affects both boundary discontinuity and translation quality.
- **Evaluation:** a fixed vs random vs consistency-matched instance-selection ablation.
- **Feedback signal:** pose-level quality metrics are **dense and cheap**; downstream utility is sparse and expensive.

**P-3. Word order: SWO ≈ RWO on How2Sign**
- **Evidence (E):** test B-4 4.56 vs 4.53 [PS Tab. 1], single runs.
- **Why it matters (critical):** this is **evidence against** expecting large gains from optimising the *order* of stitched signs for How2Sign. It challenges the intuition that smarter ordering is the obvious RL target.
- **(H)** Within seed noise, word order of stitched data has no significant effect on How2Sign SacreBLEU.
- **Evaluation:** SWO vs RWO vs an ASL-heuristic order (function-word dropping, topic–comment), ≥3 seeds each.
- **This should be validated *before* investing in any ordering intervention.**

### Temporal modelling gaps

**T-1. Global, mean-only temporal matching**
- **Evidence (E):**
  - A single sampling rate s = T̄_syn / T̄_real plus a random skip in [1, 3].
  - No per-sign duration modelling.
  - Rest-pose trimming is unmentioned [PS App. B.1, C].
- **(H)** Per-sign temporal normalisation (rest-segment trimming, duration matching to real signing speed) reduces the synthetic–real distribution gap and improves BLEU.
- **Evaluation:**
  - Distribution distance (frame-length and velocity histograms, e.g. Wasserstein) between synthetic and real.
  - Downstream SacreBLEU.

**T-2. No alignment inductive bias**
- **Evidence (E):**
  - Length mismatch is acknowledged as central [PS §2].
  - POSESTITCH-SLT uses no CTC or anchors.
  - Synthetic data contains *free* word-segment boundaries that are never used.
  - 300-frame truncation.
- **(H)** Using the known segment boundaries of stitched data as an auxiliary alignment signal (e.g. CTC on synthetic only) improves real-data translation.
- **Evaluation:** an auxiliary-loss ablation; this is a strong non-RL alternative.

### Linguistic gaps

**L-1. Synthetic data is signed English, not ASL**
- **Evidence (E):**
  - English order and function words are kept [PS §3, Limitations].
  - Non-manual and spatial grammar are absent [SV §3.2].
- **(H)** Modest ASL-motivated transformations (dropping articles and copulas, topicalisation) bring synthetic data closer to real ASL and improve BLEU more than random permutation does.
- **Evaluation:** controlled variants vs SWO/RWO. An expert check on a sample would be ideal; this needs a resource decision.

**L-2. Template domain mismatch**
- **Evidence (E):**
  - BLiMP targets syntactic acceptability phenomena, not instructional discourse.
  - BLIMP-ASL uses 456 types, of which only 380 are in How2Sign-train [PS Tab. 5].
  - Synthetic BLEU-4 of 97 indicates the template space is **nearly saturated**: the data is "too easy".
- **(H)** Difficulty- or diversity-aware generation helps more than additional template samples.
- **Evaluation:** learning curves vs synthetic data size and diversity.

### Translation gaps

**Tr-1. Token-level cross-entropy only; exposure bias; repetition and hallucination**
- **Evidence (E):** qualitative repetition ("magic magic magic") and hallucination [PS Tab. 10]; the training objective is teacher-forced cross-entropy [PS App. C].
- **Papers:** ⚑ MIXER, MRT, Edunov 2018, and **Choshen et al. 2020 (a negative result: RL gains in NMT can come from making the output distribution more peaked)**.
- **(H)** Sequence-level fine-tuning on a semantic-similarity objective reduces repetition and improves semantic adequacy.
- **Evaluation:**
  - SacreBLEU, chrF, BLEURT/COMET-style or SBERT similarity, repetition rate.
  - **Strong non-RL baselines:** label-smoothing tuning, n-gram blocking, repetition penalty, MBR decoding.

**Tr-2. Reward sparsity at current quality levels**
- **Evidence (E):** test 4-gram precision is about 1.1% [PS Tab. 13, verified in §1.12 above], so sentence-level BLEU-4 is ≈ 0 for most outputs.
- **Why it matters:** this is a **hard constraint for any translation-quality reward**. Sentence-BLEU rewards would be almost all zeros.
- **(H)** Dense semantic rewards (embedding similarity, chrF) have a usable variance on How2Sign outputs where BLEU-4 does not.
- **Evaluation:** measure reward distributions (mean, variance, fraction of zeros) of candidate metrics on baseline dev outputs. This is a cheap empirical check to do *before* any RL design.

### Generalisation gaps

**G-1. Vocabulary coverage**
- **Evidence (E):** WLASL covers 1,501 / 7,430 How2Sign-train types [PS Tab. 6]. No OOV analysis is given for How2Sign test.
- **(H)** Translation errors concentrate on sentences with low WLASL token coverage.
- **Evaluation:** BLEU stratified by token coverage, by sentence length and by synthetic similarity, for How2Sign (the paper only did iSign).

**G-2. Evaluation rigour**
- **Evidence (E):**
  - Single seed, no CIs.
  - Differences of 0.03–0.3 BLEU are presented as rankings.
  - Synthetic "generalisation" is in-distribution.
  - No signer-level analysis.
- **(H)** Some reported orderings (SWO vs RWO, BLiMP vs BPCC) are not statistically significant.
- **Evaluation:** reproduce the baseline with ≥3 seeds plus paired bootstrap. **This is a prerequisite for claiming any improvement.**

**G-3. Narrow comparison scope**
- **Evidence (E):** only GloFE and Álvarez are compared; ⚑ large-scale ASL pre-training methods are omitted.
- **Why it matters:** our improvements must be framed honestly. We are improving a *low-resource, pose-only, no-external-pretraining* regime, not state-of-the-art How2Sign overall.

### Optimisation gaps

**O-1. Open-loop generator**
- **Evidence (E):** synthetic data is generated once, independent of the translator; the stitching, selection and schedule decisions are non-differentiable [PS §3].
- **Why it matters:** this is the most natural place where a *learned decision-maker driven by translator feedback* could add something POSESTITCH-SLT lacks.
- **(H)** Closing the loop, so that generator and selection decisions are conditioned on translator feedback, outperforms the best fixed pipeline.
- **Status:** the hypothesis that most strongly motivates an RL contribution, and also the **most expensive to evaluate**, because the reward needs translator training. It needs cheap proxies, and it must beat non-RL selection and curriculum baselines.

**O-2. Untuned pipeline hyperparameters**
- **Evidence (E):** the 90% threshold, s, the [1, 3] skip, 0.85 / 60k and the 300-frame cap are all fixed without sensitivity analysis.
- **(H)** A modest hyperparameter search (non-RL) yields part of any gain we would otherwise attribute to RL.
- **Evaluation:** this search is a **mandatory baseline** for any RL claim.

**O-3. Source of the gain is unidentified**
- **Evidence (E):** SWO ≈ RWO, and BLiMP (456 types) ≈ BPCC (4,613 types), on How2Sign.
- **(H)** A substantial part of the benefit comes from exposure to sign *pose dynamics*, not lexical or syntactic supervision.
- **Evaluation:**
  - Pre-train on stitched poses with **mismatched or shuffled text**, and with pose-only self-supervision.
  - Compare against matched pairs.
  - If H holds, RL interventions on *linguistic* properties of synthetic data are unlikely to pay off, and *kinematic* properties become the priority.

### 4.1 Summary: gaps ranked by evidence strength (not yet by intervention merit; that is Stage 3)

| Gap | Category | Evidence strength | Feedback signal available? | Cheap validation possible? |
|---|---|---|---|---|
| G-2 Evaluation rigour | Generalisation | Strong | – | **Yes, prerequisite** |
| Tr-2 Reward sparsity | Translation | Strong (numerical) | – | **Yes** |
| P-1 Transitions / smoothing | Stitching | Strong (underspecified) | dense pose metrics + sparse downstream | Yes |
| D-2 Text–pose mismatch | Data | Strong (Tab. 6) | – | Yes |
| O-1 Open-loop generator | Optimisation | Structural | expensive / delayed | Partly |
| D-1 Target-aware selection | Data | Moderate (correlational, ISL) | expensive | Partly |
| D-3 Schedule | Data | Moderate (no ablation) | cheap, frequent | Yes |
| O-3 Source of gain | Optimisation | Moderate | – | Yes |
| P-3 Word order | Stitching | Weak / negative | – | Yes |
| T-1 / T-2 Temporal | Temporal | Moderate | dense | Yes |
| L-1 / L-2 Linguistic | Linguistic | Moderate | needs expertise | Partly |
| G-1 / G-3 Coverage / scope | Generalisation | Strong | – | Yes |
| P-2 Instance selection | Stitching | Moderate | dense | Yes |
| Tr-1 Sequence-level training | Translation | Moderate (qualitative) | sparse at current quality | Yes |

---

## 5. Unresolved questions and assumptions requiring validation

### Questions answerable from the repository (Stage 6)

| # | Question |
|---|---|
| Q1 | Exact boundary-smoothing algorithm and parameters |
| Q2 | WLASL instance selection per word |
| Q3 | Inflection / lemma → WLASL gloss mapping |
| Q4 | Treatment of the ≤10% unsigned tokens in BPCC sentences |
| Q5 | Is the rest pose at the start and end of each WLASL clip trimmed? |
| Q6 | Normalisation method |
| Q7 | BLEU implementation used for [PS Tab. 1] |
| Q8 | Checkpoint selection rule (best dev?) |
| Q9 | 152 → 512 input projection |
| Q10 | Is stitching precomputed or on-the-fly, and what are the storage requirements? |

### Assumptions to validate empirically, before or early in Stage 6–7

| # | Assumption |
|---|---|
| A1 | The [PS] How2Sign numbers reproduce, within seed variance, on our hardware |
| A2 | SWO vs RWO and BLiMP vs BPCC differences are significant (G-2) |
| A3 | A candidate dense reward (semantic similarity, chrF) has non-trivial variance on baseline outputs (Tr-2) |
| A4 | Stitched sequences differ measurably from real How2Sign in boundary kinematics (P-1); otherwise stitching interventions are moot |
| A5 | The 2,670 unsigned BPCC-ASL word types reach the training targets (D-2) |

---

## 6. Decisions needed from you, approaches and trade-offs, and recommended next step

**D1. The survey mismatch**

| Option | Trade-off |
|---|---|
| (a) Accept [SV] plus the [PS] related work as the Stage 1 survey basis | Fastest. Novelty claims for the translator side stay weaker. |
| (b) **(Recommended)** Also upload SignBT (CVPR 2021), Signing at Scale (CVPR 2022), Walsh et al. Sign Stitching (2024), YouTube-ASL (2023), and ideally a 2023–2025 SLT survey. I'd then add a short Stage 1 addendum. | Small cost. It protects us from claiming novelty that already exists. |

**D2. Scope**
- I recommend **ASL only**: WLASL for the lexicon and How2Sign for evaluation.
- iSign/CISLR numbers are reference only.
- This matches your instruction and halves the compute.

**D3. Evaluation standard (proposed)**
- **Primary metric:** corpus SacreBLEU, with the signature reported.
- **Also report:** BLEU-1 to BLEU-4 using the [PS] protocol, for comparability.
- **Statistics:** ≥3 seeds, paired bootstrap.

**D4. Existing `rlproj/src/` folder** (`data/`, `models/`, `rl/`, `utils/`, with compiled `__pycache__`)
- I have **not opened it**.
- Please tell me what it is: your earlier code, or something from another source.
- Under the protocol it should not be built on before Stage 6/7. I propose we log it as "pre-existing, unaudited" and review it in Stage 6.

**D5. Stage-2 papers**
- Three PDFs in `papers/` are **truncated downloads** and cannot be parsed:
  - `2026.findings-emnlp.1353.pdf` (178 KB)
  - `2650_RLP_Reinforcement_as_a_Pr.pdf` (98 KB)
  - `Learning What Reinforcement Learning Can't…2506.07527v3.pdf` (140 KB)
- Each file ends in the middle of a PDF stream. Please re-download them before Stage 2.
- There are also two copies of the PoseStich-SLT repo: `rlproj/PoseStich-SLT` and `rlproj/rlproj/PoseStich-SLT`. To reconcile in Stage 6.

**Recommended next step**
1. Approve this Stage 1 report, with any corrections.
2. Decide D1–D4.
3. Fix the truncated PDFs (D5).
4. Then proceed to **Stage 2 (RL-for-Transformer literature)**.

Stage 2 should be read with three findings from this report in mind. They are constraints, not designs:
- **Tr-2:** translation rewards are sparse.
- **P-1 caveat:** DP or graph search is the baseline any stitching RL must beat.
- **O-1:** the open-loop generator is the most structurally motivated intervention point.
