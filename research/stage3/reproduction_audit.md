# SignSparK paper vs our runs: reproduction audit (2026-11-03)

Labels:
- **[P]** paper (arXiv 2603.10446, main text; the supplementary is not available to us)
- **[A]** author statement (README, model card, GitHub issues)
- **[V]** verified by our own runs
- **[I]** my inference

Our runs:
- `experiments/baseline/eval/{dev,test}_{kf2p,gf}`
- `experiments/baseline/eval/bestofn_dev256_*`

Summary:
- **Nothing in the paper's tables was reproduced as reported.**
- The one result reproduced is the **released back-translation scorer's README numbers**, which is a different evaluation from the paper's.

## 0. Reproduction is bounded

**Different model.** The released checkpoint is not the paper's model [A, issues #5/#7]:

| | Paper's model | Released checkpoint |
|---|---|---|
| Training data | Phoenix14T + CSL-Daily + How2Sign + 10% BOBSL [P] | CSL-Daily, How2Sign, BOBSL (+ CSL-News per README; model card omits it); "~15× more data" [A] |
| Parameters | raw, Savgol-smoothed | re-optimised |

Even a perfect re-run of the paper's protocol therefore measures *this* checkpoint, not the paper's.

**Different back-translation model.**
- The paper's B-T is an SL-Transformer with How2Sign GT BLEU-4 3.37 [P].
- The released SignSparK-BT gives GT 3.53 [A][V].
- Only *relative* drops are comparable, and even those depend on the B-T model.

## 1. What the paper reports

| # | Experiment | Data | Metrics | ASL / How2Sign relevant? |
|---|---|---|---|---|
| T1 | FAST segmentation vs SOTA | MeineDGS (DGS) | F1, IoU, segment ratio | No |
| T5 | FAST architecture ablation | MeineDGS | F1, IoU | No |
| T2 | Sign stitching (G2P/T2P) vs Sign Stitcher | Phoenix14T, MeineDGS, BSLCorpus | DTW-JPE; B-T BLEU-4 and % drop | No (no How2Sign) |
| T3 | GF-T2P vs Prog.Trans., Text2Mesh, T2S-GPT, S-MotionGPT, SOKE | How2Sign, CSL-Daily, Phoenix14T | DTW-PA-JPE and DTW-JPE, body and hand. No B-T ("evaluation model and GT baselines publicly unavailable") | **Yes**. How2Sign: PA body 7.26, PA hand 2.72, JPE body 6.30, JPE hand 11.43 |
| T3 | SR-T2P (T2G2P, 3 retrieved keyframes per gloss) vs SOKE | CSL-Daily, Phoenix14T | same | How2Sign omitted (no glosses) |
| T4 | KF2P vs SLERP | How2Sign, CSL-Daily, Phoenix14T | DTW-PA-JPE, DTW-JPE (body, hand); B-T BLEU-4 and % drop | **Yes**. SignSparK 2.11 / 0.86 / 1.68 / 2.80, B-4 2.99 (−11%). SLERP 4.18 / 0.98 / 4.36 / 3.76, B-4 2.78 (−18%). GT 3.37 |
| F4 | Diffusion vs CFM vs SignSparK at 1/10/100/1000 steps | unspecified | avg PA-JPE | Partly |
| T6 | Keyframe-policy and loss ablations | unspecified (likely mixed) | body/hand PA-MPJPE, MPJPE (± std) | Indirect |
| T7 | Dataset mix and language-token ablation | Ph-T/CSL/H2S/BSL mixes | same | Indirect |
| F5 | Forced-choice user study, 16 BSL signers (6 Deaf) | BSL | preference % (86.68 / 72.63 / 73.33) | No (BSL) |
| T8 | Face PA-VPE | How2Sign 0.07 ± 0.02; CSL-Daily 0.06 | PA-VPE (FLAME) | Yes |
| Text | Inference speed: "0.01 s/vid" at 10 steps vs SOKE 1.55 s | — | seconds per video | Yes |

General caveats on the paper's numbers:
- JPE units are never stated [P].
- Metric code is SOKE's, which needs SMPL-X and MANO forward kinematics [A, README].

## 2. What we ran

All runs are on How2Sign only, with the released checkpoint at 10 Euler steps, seed 102, `flip_left_hand=True`, ground-truth length, dev 1,650 / test 2,183 clips.

| Our run | Closest paper experiment | Comparable? |
|---|---|---|
| KF2P, test, released BT | T4 How2Sign B-T column; SignSparK-BT README table | B-T: only vs README (same scorer). JPE: no |
| GF-T2P, test | T3 How2Sign GF row | No: paper reports only DTW-(PA-)JPE; we have no SMPL-X |
| Rotation-space errors, articulation, coordination | none | New measurements; no paper counterpart |
| Best-of-8, dev 256 | none | New |
| Compute and sampling time | "0.01 s/vid" claim | Not like-for-like (see §4) |

## 3. What matches

Released BT scorer vs README (How2Sign test, 2,183 clips) [V]:

| | B1 | B2 | B3 | B4 | chrF | ROUGE |
|---|---|---|---|---|---|---|
| GT: README | 23.07 | 10.33 | 5.73 | 3.53 | 19.81 | 23.58 |
| GT: ours | 23.07 | 10.33 | 5.73 | 3.53 | 19.81 | 23.58 |
| KF2P: README | 22.26 | 9.69 | 5.39 | 3.34 | 19.36 | 22.59 |
| KF2P: ours | 22.33 | 9.77 | 5.50 | 3.40 | 19.33 | 22.61 |

- **Ground truth matches exactly.** This confirms our data, scorer install and normalisation.
- **KF2P is within 0.11 on every column.** The README's sampling seed and per-stream versus `sample_all.py` setup are unknown, so a small stochastic gap is expected [I]. I have *not* measured seed-to-seed variance, so "within noise" is an inference, not a test.

## 4. What differs, and why

1. **KF2P relative B-T drop.**
   - Paper: −11% (2.99 / 3.37).
   - Ours: −3.9% (3.40 / 3.53). README: −5.5%.
   - Causes: a different B-T model and a different checkpoint [A]. They cannot be separated with what is released [I].
   - This is not evidence against the paper. It just is not the same experiment.
2. **Inference speed.**
   - Paper: 0.01 s/video [P]; hardware and what was timed are unstated.
   - Ours: full-split runs on an A4000, fp32, batch 32. Whole-script wall time works out to about 0.17–0.26 s/clip for body or face, and about 0.32 s/clip for hands (two per clip).
   - Our time includes model load, LMDB I/O and dumping. That is an upper bound, not a pure sampler timing.
   - I did not isolate the ODE loop, so this neither confirms nor refutes the 0.01 s figure [V for our number; comparison not valid].
3. **GF-T2P length.**
   - The code takes length from the reference clip [C][V].
   - The paper's "zero-keyframe inference" does not say whether it used the reference length or a predicted one [P].
   - Our GF numbers therefore include oracle length. Whether the paper's do is unknown.
4. **Language token.** The loader produces `"<American> …"`; the paper's text writes `<ASL>` [V][P]. This is cosmetic unless the paper's model used a different string.
5. **Training loss weights.** The code uses 0.5 : 1 : 0.5 plus 0.1 acceleration; the paper says 2 : 1 : 1 [C][P]. This does not affect inference, but it is another sign that the released code and checkpoint are a later version.

## 5. Not reproducible as things stand

| Paper item | Blocker |
|---|---|
| T3, T4 DTW-JPE / DTW-PA-JPE (the paper's main SLP metrics) | Need the SMPL-X/MANO licence (registration on hold by your instruction) plus SOKE eval code. Even then, numbers describe the released checkpoint, not the paper's model |
| T3 GF-T2P comparison to SOKE / S-MotionGPT etc. | As above; baselines' outputs not released (their numbers are copied from SOKE) |
| T4 SLERP baseline | **Partly reproducible now:** SLERP between the same keyframes plus the released B-T needs no licence. Not run. JPE columns still need SMPL-X |
| T4 B-T absolute numbers | Paper's SL-Transformer B-T model and its GT baseline are not released |
| T8 face PA-VPE | Needs the FLAME model (separate licence); not attempted. We only have jaw-rotation error and expression L2, which are not comparable |
| T6, T7 ablations, F4 diffusion/CFM comparison | Need retraining or unreleased model variants, and the multilingual data mixes |
| T2 stitching, T1/T5 FAST, F5 user study | Out of scope (non-ASL data, the FAST segmentor, and BSL signers) |
| Exact test set | LMDB test has 2,183 clips. The official How2Sign test count (≈2,357) is from memory, unverified. The filtering is undocumented, so the paper's evaluation set cannot be confirmed to be identical [V/⚑] |

## 6. Implications for the RL project [I]

- **The baseline is the released checkpoint, not the paper's model.** Every improvement claim must be paired against our own runs, never against paper numbers.
- **Without SMPL-X, we can compare to the paper only on relative B-T drop, and that comparison is confounded.**
- **Cheapest paper-anchored check available now:** a SLERP KF2P baseline under the released B-T. It would show whether the paper's ordering (SignSparK > SLERP) holds for the released checkpoint.
