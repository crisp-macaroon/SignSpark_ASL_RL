# Stage 2 Report: How2Sign dataset investigation (SignSparK release)

Date: 2026-11-02 · Scope: ASL / How2Sign only · Status: **awaiting approval** (Stage 3 not started)

Nothing in this report designs an MDP, selects an algorithm, or uses the checkpoints (not downloaded).

## Evidence labels

| Label | Meaning |
|---|---|
| **[V]** | Verified by our own computation on the downloaded data (scripts in `eda/`) |
| **[C]** | Verified by reading code |
| **[A]** | Author statement (repo docs, GitHub issue replies by the repository owner) |
| **[P]** | Paper |
| **[⚑]** | Outside knowledge, unverified |
| **[I]** | Inference |
| **[H]** | Hypothesis |

## Artefacts

| What | Where |
|---|---|
| Raw data (read-only) | `data/raw/SignSparK_data/` |
| Download manifest | `data/raw/SignSparK_data/MANIFEST.json` |
| EDA code | `eda/h2s_lmdb.py`, `eda/run_eda.py`, `eda/make_figures.py`, `eda/download_how2sign.py` |
| Outputs | `research/stage2/` (`summary.json`, `tables/per_clip.csv`, `tables/pooled_histograms.csv`, `key_stats*.txt`, `figures/F1–F7`) |
| Python environment | Isolated Python 3.12.10 venv `.venv-eda/`, versions pinned in `requirements-eda.lock.txt`. Python 3.15 was untouched. |

---

## 1. Dataset overview

| Property | Value | Evidence |
|---|---|---|
| Source | HF dataset `LionelLow/SignSparK_data`, commit `9fe7e04ef59204c787cd6094c747f889efff6ba0` (last modified 2026-09-19) | [V] |
| Underlying corpus | How2Sign (ASL, instructional videos), re-processed into SMPL-X/MANO/FLAME parameters by the SignSparK authors with global re-optimisation | [A] |
| Clips (train / dev / test) | **29,630 / 1,650 / 2,183** sentences. The meta `split` field for dev reads `"val"`. | [V] |
| Frames (train / dev / test) | 5,343,439 / 305,615 / 397,824 | [V] |
| Comparison with official How2Sign | Official counts are 31,128 / 1,741 / 2,357 [⚑, from memory, unverified]. If correct, ~5–7% of each split was dropped. Filter criteria are undocumented. Minimum length is exactly 25 frames in every split, suggesting a length filter [I]. | [V] + [⚑] |
| Language field | `"American"` for 100% of clips | [V] |
| Gloss field | Empty for 100% of clips (How2Sign has no glosses) | [V] |
| Translation | English sentence; median 15 words (p99 62, max 195) | [V] |
| Signer metadata | **Not present.** No signer field exists. | [V] |
| Frame rate | **Not recorded** in the LMDBs | [V] |

**Clip-id structure** [V]:
- Every id matches `<video>_<sentence>-<n>-rgb_front`.
- The `<n>` field takes the values 1, 2, 3, 4, 5, 8, 9, 10, 11. Its meaning is undocumented, so **I do not treat it as a signer id**.

**Record schema** [V], identical across all 33,463 clips:

| Field | dtype / shape | Content |
|---|---|---|
| `language`, `translation`, `gloss` | pickled object arrays of `str` (read with a whitelisting unpickler) | text |
| `segment` | int32 (T,) | values ⊂ {0, 1, 2} only |
| `left_features`, `right_features` | float32 (T, **90**) | 15 MANO joints × 6D |
| `body_features` | float32 (T, **126**) | 21 SMPL-X body joints × 6D; the loader keeps joints 11–20 |
| `face_features` | float32 (T, 56) | jaw 6D + 50 expression coefficients |

Differences from the docs [V]:
- DATA.md says hand features are "≥90" and FAST's README says "96 dims/hand". **The released How2Sign hands are exactly 90-d.**
- DATA.md describes text fields as `str`. They are stored as pickled object arrays, so the official loader needs `allow_pickle=True`.

---

## 2. Download and integrity verification [V]

| File | Size (bytes) | SHA-256 (matches Hub LFS oid) | Status |
|---|---|---|---|
| `train/How2Sign_reopt_train.lmdb/data.mdb` | 7,898,869,760 | `7950807733e7…6739426` | ok |
| `dev/How2Sign_reopt_dev.lmdb/data.mdb` | 451,575,808 | `79f37363d008…d605c23e` | ok |
| `test/How2Sign_reopt_test.lmdb/data.mdb` | 587,984,896 | `fd34d6b3b11a…2d61850e` | ok |

- **Pinned URLs**: `https://huggingface.co/datasets/LionelLow/SignSparK_data/resolve/9fe7e04…/<path>`.
- **No failed or partial downloads.**
- **Repo history**: the dataset repo shows the train LMDBs added 2026-06-26 and only README/PHOENIX commits since.
- **LMDB integrity**:
  - Every `__meta__.clip_ids` list matches the LMDB keys exactly (no missing or extra keys).
  - `num_clips` equals the id count.
  - All ids are unique.
- **Read-only handling**:
  - Files are marked read-only.
  - The LMDBs are opened read-only with no lock file.
  - Pickled content is never executed: the meta is read with a no-globals unpickler, and text arrays with a numpy-only whitelist.
- **Layout**: preserved as `train/`, `dev/`, `test/`. Hugging Face adds a `.cache/huggingface/` metadata folder next to the data.

---

## 3. EDA results

All statistics are computed in the 6D/rotation space. Angles are geodesic distances after Gram–Schmidt.

### 3.1 Sequence length (Fig. F1)

| | train | dev | test |
|---|---|---|---|
| Median frames (mean) | 136 (180) | 148 (185) | 140 (182) |
| p99 / max | 763 / **7,357** | 730 / 1,392 | 731 / 1,425 |
| Clips > 304 frames (SignSparK window, truncated by loader) | 4,137 (14.0%) | 251 (15.2%) | 324 (14.8%) |
| Fraction of all frames beyond frame 304 | 13.8% | 12.3% | 13.3% |
| Clips > 300 frames (SignSparK-BT truncation) | 4,252 | 256 | 329 |

- **Length vs translation** (train): Pearson r = 0.66 between frames and words (F6). Median 8.8 frames per word, with wide spread.

### 3.2 Segmentation and keyframes (Fig. F2)

| | train | dev | test |
|---|---|---|---|
| Segments per clip, median (p99) | 8 (42) | 9 (38) | 9 (41) |
| Segment length, median (p95) | 7 (26) frames | 7 (25) | 7 (26) |
| Mode-3 keyframes per clip, median | 23 | 25 | 24 |
| **Keyframe density** (keyframes / T), median | **0.169** | 0.172 | 0.170 |
| Gap between keyframes, median (p95) | 5 (15) frames | 4 (15) | 5 (15) |
| Gaps ≤ 8 frames | 80.5% | 80.4% | 80.0% |
| Fraction of frames labelled sign | 0.53 | 0.53 | 0.55 |
| Clips with **zero** segments (hence no keyframes) | 120 | 1 | 5 |
| Segments starting with label 1 (no onset), per clip | 0.91 | 0.92 | 0.89 |
| Onset label directly after a sign frame (adjacent signs merged by the loader), per clip | 0.24 | 0.24 | 0.23 |

- **Segments in the truncated tail**: segments cut or lost by the 304-frame truncation average 1.3 per clip, concentrated in long clips.
- **Keyframes are not very sparse on How2Sign** [V]. About 17% of frames are anchors, and the median anchor gap is 5 frames.
- **Weak KF2P headroom** [I]. In KF2P with oracle keyframes, most of the sequence is therefore short-range in-betweening. This explains the strength of the SLERP baseline in the paper (Tab. 4) and limits the room for improvement in that regime.

### 3.3 Motion statistics (Figs. F3, F4, F7)

Per-joint angular speed, in degrees per frame [V]:

| Stream | mean speed, clip median | sign frames | non-sign frames | max speed, clip median (p99) | jerk proxy\*, clip median |
|---|---|---|---|---|---|
| Body, 10 kept joints | 1.90 | 1.67 | 2.18 | 27.2 (156) | 0.83 |
| Right hand (15 joints) | 3.09 | 2.70 | 3.59 | 20.9 (27.7) | 1.58 |
| Left hand | 2.12 | – | – | – | – |
| Jaw | 0.34 | – | – | – | – |
| Body legs/spine (11 joints) | 0.11 | – | – | – | – |

\*Jerk proxy: the norm of the frame-to-frame change in body-frame angular velocity.

- **Speed by segment type**: motion is *faster in non-sign (transition) frames than inside sign segments*, for both body and hands [V]. This is consistent with signs containing holds [I].
- **Right vs left hand**: the right hand moves ~45% more than the left. This is consistent with a right-dominant majority, but **handedness is not annotated** [I].
- **Face**: the first 10 expression coefficients have std 0.69–1.89 (train). The maximum |coefficient| over all clips is 10.7. Per-coefficient values for all 50 are in `summary.json` [V].
- **Representative clips** (F7): randomly drawn with seed 0, not cherry-picked. They show smooth hand and elbow trajectories and dense keyframes, with sign segments aligned to wrist and finger motion.

### 3.4 Left/right hand convention (Fig. F5) [V]
- The per-joint mean rotation of the *stored* left hand differs from the right hand by 11–111° (median ≈ 60°).
- After the official `flip_left_hand` conjugation, the difference is 0.3–8.4°.
- **Conclusion**: the stored left hand is in SMPL-X-left convention, so **`flip_left_hand=True` is required**. The repo's `inference.yaml` default (`False`) would feed un-flipped left hands to a right-hand model.

### 3.5 Text [V]

| | train | dev | test |
|---|---|---|---|
| Word types / tokens | 15,368 / 543k | 3,205 / 30k | 3,655 / 40k |
| OOV token rate vs train | – | 2.0% | 2.3% |

- **Duplicate translations within a split** (mostly short phrases such as "Okay"): 472 in train, 197 in dev, 341 in test.
- **Language token**: the loader builds the prompt as `f"<{language}> {translation}"`, which here yields **`"<American> …"`**. The paper's Tab. 7 example writes `<ASL>`. The actual token string differs from the paper's description [V][C].

---

## 4. Data-quality findings

| # | Finding | Evidence | Why it matters later |
|---|---|---|---|
| Q1 | **Body 6D values for the 10 kept joints are not valid orthonormal 6D in any frame.** Mean deviation 0.033; max up to 0.99, largest at the wrists. Hand and jaw 6D are exact (≤ 1.6e-7). | [V] | The model is trained and evaluated on these raw values. Any rotation-based measure must apply Gram–Schmidt first. MSE in 6D space ≠ rotation error. |
| Q2 | Legs/feet joints are exact identity in every frame. Spine1–3 vary (std comparable to the neck), but the loader discards them, and the official FK (`tools/visualize.py`) zeroes them. | [V][C] | Torso lean present in the data is never modelled or evaluated. |
| Q3 | **Wrist "flip" spikes** in the body stream. 4,016 train / 283 dev / 380 test clips (13–17%) contain a body-joint jump > 45°/frame; 1,079 / 42 / 77 exceed 90°/frame. In the 20 worst train clips, all maxima are at L/R wrists, lasting 1–10 frames. Hands never exceed 34°/frame. | [V] | Consistent with the author's note that the re-optimised data "would occasionally produce body poses in extremely unnatural positions" [A]. Reference-based velocity/jerk targets are corrupted in these clips. |
| Q4 | Extreme lengths: one train clip has 7,357 frames for an 11-word sentence; 139 train clips exceed 1,000 frames. | [V] | Probable temporal misalignment of sentence boundaries [I]. |
| Q5 | **Identical pose sequences attached to different sentences**: 4 pairs in train, 1 pair in dev, each within the same source video (e.g. "Okay?" vs "So Jonsey go ahead, pop up into your plank position."). | [V] | Mislabelled pairs. A text-conditioned reward or evaluator would be inconsistent on them. |
| Q6 | Segmentation irregularities: clips with no segments (126 total); adjacent signs merged into one segment by the official `_segment_bounds`; segments without onset labels. | [V][C] | KF2P on zero-segment clips is silently unconditional. Merged segments get only 3 keyframes for 2+ signs. |
| Q7 | ~14% of clips are truncated to 304 frames by both training and `sample.py`; metrics are computed on truncated sequences. | [V][C] | Evaluation silently ignores ~13% of frames. |
| Q8 | **R_Shoulder distribution shift**: 128 test clips exceed the train 99.9th-percentile shoulder rotation, vs 29 dev clips. | [V] | Test is not identically distributed with dev for this joint. Cause unknown (likely a specific video or signer, unverifiable without metadata). |
| Q9 | Within-split duplicate translations; 19 test clips (and 14 dev) have an exact translation that also occurs in train. | [V] | Negligible lexical overlap, but these clips should be flagged in evaluation. |

**Not found** [V]:
- no NaN or Inf values;
- no frozen (bit-identical consecutive) frames;
- no labels outside {0, 1, 2};
- no stream-length mismatches.

---

## 5. Checkpoint training-data provenance (high priority)

**Sources examined**:
- the paper (v4, 2026-06-25);
- the GitHub README and its full commit history (12 commits, incl. 7b9b483 "Clarify checkpoints");
- the HF model card and its history (initial version and the 2026-09-19 edit);
- HF discussions (none);
- all 7 GitHub issues with owner replies;
- the SignSparK_BT config;
- the training code.

### 5.1 What is verified

| Claim | Source | Status |
|---|---|---|
| Paper's model: PHOENIX14T + CSL-Daily + How2Sign + 10% BOBSL, trained on raw (non-re-optimised, Savgol-smoothed) parameters | [P], owner reply issue #5 [A] | Author-stated |
| Released checkpoint ≠ paper's model; retrained on re-optimised data; "almost 15× more data (more BOBSL and CSL-News)" | owner reply #5, #7 [A] | Author-stated |
| Released checkpoint data: "CSL-Daily, How2Sign, BOBSL, and CSL-News"; PHOENIX excluded | README commit 7b9b483, 2026-09-17 [A] | Author-stated |
| More detail: "all of BOBSL and 60% of CSLNews" extracted | owner reply #5 [A] | Author-stated, but whether *all* of that went into training is not explicit |
| HF model card says "CSL-Daily, How2Sign and BOBSL" (no CSL-News) in both versions | HF card [A] | **Inconsistent with README** |
| Released public training code trains only on the `train` LMDB split and validates on `dev` | `train.py`, `pose_datasets_lmdb.py` [C] | Verified, but the public config lists CSL-Daily only, so it is **not** the configuration used for the release |
| Released How2Sign LMDB splits are mutually disjoint: no shared clip ids, no identical feature sequences, no shared video prefixes across train/dev/test | [V] | Verified for the LMDBs, not for what the checkpoint saw |

### 5.2 What is NOT verifiable
- **Which How2Sign splits were used to train the released checkpoint.** No training config, log, data manifest or split list for the release is published. The owner's replies describe datasets, not splits.
- **The paper's own split use.** The paper says its corpus was constructed "following SOKE by merging Phoenix14T, CSLDaily, and How2Sign" [P]. Standard practice is train-split only [⚑], but the paper does not state it.
- Exact proportions per dataset, and whether How2Sign was subsampled.
- **Conclusion: whether the released checkpoint saw the How2Sign test split is UNRESOLVED.** I make no claim that the test set is uncontaminated. This is an **open reproducibility and data-leakage risk**.

### 5.3 Can a defensible evaluation protocol still be built? Yes, with explicit caveats [I]

| # | Element | Rationale |
|---|---|---|
| E1 | Report on **both dev (1,650) and test (2,183)**. dev is the selection set; test is touched only for final numbers. | dev is used for model selection by SignSparK-BT (early stopping on dev BLEU [C]), so it is no "cleaner" than test |
| E2 | **Primary claims are relative**: baseline vs RL-improved, from the same checkpoint, on the same clips, same seeds, paired tests. Absolute numbers are reported only as secondary, with the contamination caveat. | Contamination would inflate the baseline and RL variants alike. It still threatens claims about *generalisation*, which must be worded accordingly. |
| E3 | Our own RL training uses **train only**; dev for all tuning; test once at the end. | Prevents *our* leakage regardless of the checkpoint's |
| E4 | **Contamination probe** (requires the checkpoint, so not done now): compare the per-clip CFM/reconstruction loss of the frozen checkpoint at fixed (t, noise) across length-matched train/dev/test samples. If test losses look like train rather than dev, contamination is likely. | A membership-inference-style check. Caveat: a null result does not prove cleanliness. |
| E5 | **Ask the authors** which How2Sign splits were used, e.g. on the GitHub issue tracker. | Posting is an outward action; **you** would need to authorise or do it |
| E6 | Report results with and without flagged clips: Q3 spikes, Q4 extreme length, Q5 duplicates, Q6 zero-segment, Q9 text overlap. Also report on ≤ 304-frame clips vs all clips. | Quality issues should not drive conclusions |
| E7 | State the oracle inputs explicitly. `sample.py` takes **ground-truth length and ground-truth keyframes** from the test clip [C]. GF-T2P still uses ground-truth length. | Required for honest comparison with the paper and with each other |

Two further protocol facts constrain our evaluation design:
- **DTW is unnormalised** [A]. Per the owner (issue #7), the reported DTW-JPE/PA-JPE are **unnormalised accumulated DTW path costs**, "a flaw … we decided not to change for comparability's sake". These scores therefore scale with sequence length.
- **Evaluation details are ambiguous** [A]. Third parties disagree on `flat_hand_mean` (issue #5 used `False`, issue #7 `True`, and the viz code uses `True`), which changes hand JPE. The owner says the viz implementation matches theirs.

---

## 6. Data-leakage and evaluation risks (summary)

| Risk | Severity | Status / mitigation |
|---|---|---|
| Checkpoint may have seen How2Sign test | **High** (unknown) | Unresolved: E2, E4, E5 |
| Our own train→test leakage | Controllable | E3 |
| Lexical overlap train↔test | Very low (19 clips) | Flag (E6) |
| Video-level overlap train↔test | None found | [V] Assumes `<video>` prefix identifies the source video [I] |
| Signer overlap | **Unknown**; no signer metadata | Signer-independent evaluation cannot be established from this release. How2Sign's official splits are, to my knowledge, not signer-independent [⚑]. |
| Oracle length and keyframes in the official evaluation | High for interpretation | E7 |
| Length-dependent DTW metric; truncation at 304 | Medium | Report length-normalised variants alongside (later decision) |
| Corrupted references (Q1–Q5) | Medium | E6; robust handling needed before any reference-based signal |

---

## 7. SMPL-X / MANO dependency analysis

| Analysis / metric | Needs SMPL-X | Needs MANO | Status |
|---|---|---|---|
| Everything in §3–4 (lengths, segments, text, 6D validity, rotation angles, angular speed/jerk, left/right convention, outliers, duplicates) | No | No | **Done** |
| Rotation-space errors vs reference (per-joint geodesic error, DTW over rotations) | No | No | Possible now |
| Back-translation scores (SignSparK-BT reads 240-d body+hand 6D directly) | No | No | Possible, but needs the BT checkpoint download (493 MB), **not yet approved** |
| **DTW-JPE / DTW-PA-JPE** (paper's main metric, SOKE protocol) | **Yes**: FK to joint positions with SMPL-X NEUTRAL; hands via SMPL-X hand regressor (per issue #7) | No | Not reproducible without the licence |
| Face PA-VPE (paper Tab. 8) | **Yes** (SMPL-X/FLAME mesh vertices) | No | Not reproducible |
| Mesh rendering / visual inspection (`tools/visualize.py`) | **Yes** | No | Not reproducible |
| Physical plausibility (self-penetration, hand contact, bone-length) | **Yes** | No | Not possible |
| FAST segmentation / WiLoR extraction from raw video | No | **Yes** | Not needed (segments are in the LMDB) |

**Conclusion**: MANO is **not needed** for our How2Sign work, because the LMDBs already contain the segments. SMPL-X (one registration) is needed **only** to compute the paper-comparable joint-position metrics and to render.

**Are licence-free alternatives scientifically meaningful?** [I]
- **Rotation-space geodesic errors and DTW** are valid, well-defined *internal* measures for comparing two of our systems. But:
  - they are **not comparable** to published numbers;
  - they weight all joints equally regardless of lever arm (10° at the shoulder moves the hand far more than 10° at a finger joint), so they are not equivalent to JPE.
- **Back-translation** is the only available linguistic proxy. Its How2Sign ceiling is low: BLEU-4 3.53 on ground truth [A], making it weak and noisy at clip level.
- **An approximate FK with a self-built skeleton** (public anthropometric bone lengths) would add lever-arm weighting without licensed files. But it is non-standard, so it is useful only as a sanity measure.

**Recommendation**: plan for one SMPL-X registration *before* final evaluation, so that headline results are in the community's metric. Rotation-space and BT metrics can carry development work in the meantime. **Do not register yet**, as you instructed.

---

## 8. Limitations and unresolved questions
1. **Checkpoint How2Sign split usage is unresolved** (§5.2). It also remains unresolved whether CSL-News is in the release: README says yes, model card says no.
2. **No signer, frame-rate or handedness metadata.** Signer-independent claims are impossible from this release.
3. **Undocumented dataset construction:** official-vs-released count differences [⚑], the min-25-frame filter [I], and the re-optimisation procedure are all undocumented.
4. The meaning of the `<n>` field in clip ids is unknown.
5. **The analysis is entirely in rotation space.** Joint-position statistics (bone-length-weighted motion, hand–face distances) need SMPL-X.
6. **Q3 is an inference.** Wrist spikes are measured, but whether each is an estimation artefact or real fast motion is not established without rendering. The spike magnitudes (up to 180°/frame) and the author's statement make artefacts likely.
7. **Supplementary material.** The SignSparK supplementary (cited for dataset statistics) is on the Springer page [A] but was not available to me.

## 9. Recommended next steps for Stage 3 (literature review)

The literature review should be read *against these data facts*. Specifically, check for each RL paper whether its technique tolerates the following:

| Data fact | Consequence for evaluating each RL paper |
|---|---|
| **Weak, sparse learned rewards** | BT ceiling BLEU-4 3.5. Check sample-efficiency and stability claims under weak rewards. |
| **Corrupted references in ~15% of clips** | Q3/Q5: assess robustness to noisy reference signals. |
| **Non-autoregressive, few-step flow generator** | Most uploaded papers are token-level LLM RL. **I recommend adding RL-for-diffusion/flow-model papers** (e.g. DDPO, DPOK, Diffusion-DPO, Flow-GRPO, DRaFT/ReFL [⚑ names from memory; please upload the ones you want reviewed]). |
| **Small selection/eval sets** | dev 1,650 and test 2,183: favour methods with paired evaluation and few hyperparameters. |

Before Stage 3 I also need:
- **the three truncated PDFs, re-downloaded**;
- the rest of the research prompt from §4.5 (needed before Stage 4).

**Pending decisions** (no decision is treated as approved):

| Decision | Note |
|---|---|
| E1–E7 protocol | Proposed |
| Downloading the BT checkpoint (493 MB) | For evaluation-feasibility checks |
| Downloading the SignSparK checkpoints (3 × 5.58 GB) | For the contamination probe E4 and a measured baseline (needs a GPU ≥ 16 GB) |
| Asking the authors about splits | Proposed |
| SMPL-X registration timing | Proposed |
