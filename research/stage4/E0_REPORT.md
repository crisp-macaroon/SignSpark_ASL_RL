# E0 report: SMPL-X track (Stage 4 rev. 3.3a, §15.5)

*2026-11-03. Scope: E0 only, as authorised by the user. No E1, E2, Stage 5 work, training or fine-tuning was done. Nothing was sampled; all generated poses come from the existing dev dumps of the released checkpoints (R10: released-checkpoint results, not a paper reproduction). No test-set data was touched.*

## Status per step

| Step | Status | Evidence |
|---|---|---|
| E0.1 registration and download | Done by the user | user statement, 2026-11-03 |
| E0.2 placement and licence note | Done: NPZ files extracted to `models/smplx/smplx/`; zip left unmodified | `research/stage4/e0_licence_note.md` |
| E0.3 environment | Done: new `.venv-render` (Python 3.12, CPU torch 2.10.0, smplx 0.1.28, trimesh 4.8.3, pyrender 0.1.45); `.venv-eda`, `.venv-infer` and Python 3.15 untouched | `requirements-render.lock.txt` |
| E0.4 FK sanity, 5 dev GT clips | **Pass (C0–C4)** | `experiments/stage4/out/e0/fk_sanity/` |
| E0.5 Windows rendering | **Feasible** with pyrender + pyglet/WGL (no Blender); 3 review videos | `experiments/stage4/out/e0/renders/` |
| E0.6 joint-space metrics, dev | see §E0.6 | `experiments/stage4/out/e0/joint_metrics/` |
| Stop | Report; E1 stays deferred | this file |

## E0.4 FK sanity (`experiments/stage4/e0/fk_sanity.py`)

**Clips** (pre-specified): dev GT clips 0–4 (157, 56, 139, 171 and 189 frames).

**Setup:** SMPL-X neutral, betas 0, `flat_hand_mean`, no PCA. The input is built by upstream `build_smplx_input`, called directly, with `flip_left_hand=True`.

| Check | Criterion (fixed before the run) | Result |
|---|---|---|
| C0 conversion | our call path = upstream builder exactly | max \|diff\| = 0 (trivially, since the upstream function is used; this confirms determinism, not independence) |
| C1 finite | no NaN/Inf in inputs, joints, vertices | 0 non-finite values |
| C2 bone lengths | max relative deviation from rest < 1e-4 over 54 edges, all frames | max 1.54e-5 (float32 level) |
| C3 wrist attachment | 10 wrist→finger-base edges rigid; hand root = SMPL-X joints 20/21 | 10/10 edges per clip; max relative deviation 2.0e-6 |
| C4 left-hand flip | right hand and flipped left hand put ≥ 90% of frames on the same flexion side | right hand: 100% of frames flex towards −y (palm side in T-pose) in all 5 clips. Flipped left: 100%. **Unflipped left: 0%** (fingers bend backwards). The test is discriminative, and D7 (`flip_left_hand=True`) is confirmed |

**C3 diagnostics** (not pass/fail):
- forearm–hand angle p95 32–60°, never above 90°;
- 0 frames with wrist speed > 45°/frame in these 5 clips. D4 spikes exist corpus-wide, but none fall in these clips.

## E0.5 Windows rendering (`experiments/stage4/e0/render_review.py`)

**Feasibility:**
- pyrender offscreen runs on this Windows machine through pyglet/WGL. The upstream EGL default is removed at import.
- `bg_color` is not honoured in this context, so the background is composited using the depth buffer.
- Speed: ≈ 18–20 frames/s for a 3-panel 448 px frame on CPU FK.
- **No Blender install is needed.**

**Review videos** (for the user only; they contain SMPL-X meshes and must not be redistributed):
- clips: dev clips 0, 1 and 2;
- panels: reference | KF2P | GF (released checkpoint, repetition 0);
- KF2P keyframe frames are marked;
- fixed upper-body camera; neutral face (A2, A4); 20 fps (upstream default; the How2Sign frame rate is not in the metadata, D2).

| Clip | Text | Frames | File |
|---|---|---|---|
| 0 | "We're going to work on a arm drill that will help you have graceful hand movements in front of you." | 157 | `e0_review_clip0_-d5dN54tH2E_0-1-rgb_front.mp4` |
| 1 | "So we're going to go up and down; let's switch hands, down and up; down and up." | 56 | `e0_review_clip1_-d5dN54tH2E_10-1-rgb_front.mp4` |
| 2 | "And just let those fingers relax." | 139 | `e0_review_clip2_-d5dN54tH2E_11-1-rgb_front.mp4` |

**First render pass** (one iteration, presentation only): the first render had a black background, over-exposed lighting and a cropped head. It was re-rendered at half the upstream light intensity with the camera raised. No data or metric is affected.

## E0.6 joint-space metrics (`experiments/stage4/e0/joint_metrics.py`)

**Data:** all 1,650 dev clips (all have length ≥ 8). GF and KF2P released-checkpoint dumps, 1 candidate. Runtime 21 min on CPU.

**Not comparable with the paper (R10).** These are frame-aligned measures under the oracle length (A1), in mm. They are **not** DTW-JPE / DTW-PA-JPE: the SOKE protocol is not reimplemented, and it is unnormalised (D11).

**Stream isolation:**
- Body error = generated body with reference hands, over 7 body joints (head, shoulders, elbows, wrists).
- Hand error = reference body with generated hands, over 15 joints + 5 fingertips per side, wrist-relative.

**Amendment before the full run (disclosed):**
- A 10-clip debug run (scratch output, discarded) showed a confound: in the world frame, wrist-relative finger positions also move when the forearm or wrist rotates, and those rotations come from the body stream.
- V2/V3 finger speeds are therefore taken in the wrist's local frame.
- J1–J4 and V1 were unaffected.

### Error (mean over clips, 95% bootstrap CI over clips)

| Measure | GF | KF2P (all frames) | KF2P (non-keyframe frames) |
|---|---|---|---|
| J1 body MPJPE (mm) | 67.8 [67.1, 68.6] | 10.1 [9.8, 10.4] | 11.7 [11.4, 12.0] |
| J2 body PA-MPJPE (mm) | 52.7 [52.1, 53.4] | 8.1 [7.9, 8.4] | 9.5 [9.2, 9.7] |
| J3 left-hand MPJPE (mm) | 20.9 [20.7, 21.0] | 3.5 [3.4, 3.5] | 4.0 [3.9, 4.1] |
| J3 right-hand MPJPE (mm) | 20.7 [20.6, 20.9] | 4.6 [4.5, 4.7] | 5.4 [5.3, 5.5] |
| J4 left-hand PA-MPJPE (mm) | 16.4 [16.3, 16.6] | 2.8 [2.7, 2.8] | 3.2 [3.2, 3.3] |
| J4 right-hand PA-MPJPE (mm) | 16.7 [16.6, 16.8] | 3.9 [3.8, 3.9] | 4.5 [4.5, 4.6] |
| Rotation-space geodesic error, body / left / right (°) | 23.1 / 22.2 / 22.0 | 3.4 / 3.9 / 5.1 | – |

### Validation of the rotation-space statistics (descriptive; no pass/fail rule was pre-registered)

| | GF | KF2P |
|---|---|---|
| **V1** per-clip Spearman, geodesic error vs MPJPE: body / left hand / right hand | 0.66 / 0.90 / 0.91 | 0.92 / 0.97 / 0.96 |
| **V2** coordination, per-clip Spearman rotation vs joint: reference / generated | 0.52 / 0.47 | 0.52 / 0.55 |
| V2 corpus mean, reference: rotation / joint | 0.439 / 0.232 | (same reference) |
| V2 corpus mean, generated: rotation / joint | 0.022 / 0.025 | 0.357 / 0.200 |
| **V3** dominance log(A_L/A_R), per-clip Spearman rotation vs joint: reference / generated | 0.96 / 0.97 | 0.96 / 0.96 |
| V3 corpus mean, reference: rotation / joint | −0.400 / −0.423 | (same reference) |
| V3 corpus mean, generated: rotation / joint | 0.006 / 0.010 | −0.329 / −0.362 |

### Reading [my inference]

1. **Error measures (V1).**
   - Rotation-space hand error ranks clips almost as joint-space error does.
   - For the GF body, agreement is only moderate (0.66). This is consistent with the lever-arm effect predicted in Stage 2: equal angles at the shoulder and the wrist move the hand by different amounts.
   - For body-level claims, the SMPL-X joint measures should be preferred over the rotation-space body error.
2. **Dominance statistic (V3): supported in joint space.**
   - The per-clip log-ratio agrees closely across representations (ρ ≈ 0.96).
   - GF parity (≈ 0, Prop 1) appears in both spaces.
   - The reference left-hand deficit appears in both spaces (≈ −0.40 vs −0.42).
   - Caveat: this full-dev reference mean is descriptive only. It is **not** t* (train), t*₃₂ or t*₂₅₆, and it fixes no target or margin.
3. **Coordination statistic (V2): representation-dependent.**
   - The direction of the GF deficit holds in joint space (generated ≈ 0.02 vs reference 0.23), so it is not an artefact of rotation space.
   - However, per-clip agreement is only moderate (ρ ≈ 0.5), and the reference level roughly halves (0.44 → 0.23).
   - The r_coord target value 0.47 is therefore specific to the rotation-space statistic. It should not be described as a representation-free "coordination level".
   - This is a flag for your decision. **Nothing in Stage 4 was changed.**
4. **KF2P:** the right hand has a larger error than the left (rotation 5.1° vs 3.9°; MPJPE 4.6 vs 3.5 mm). This is noted descriptively only.

## Blockers and open items

- **No blockers for E0.**
- **Items for your decision (no action taken):**
  1. Review the three videos.
  2. Decide whether the V2 finding should change how r_coord is described or validated. This would be a Stage 4 documentation change and needs your instruction. **Addressed in Stage 4 rev. 4.0** (§6.0: space-specific train targets; 0.47 retired as a target).
  3. Confirm the Stage 4 status. Your E0 message calls revision 3.3a "approved". The log records that statement, but it does not extend it to anything beyond E0.
- **Not done (out of scope):**
  - E1 and any participant work;
  - E2 and any generation;
  - test-set renders or metrics;
  - FLAME;
  - DTW-JPE per SOKE.
