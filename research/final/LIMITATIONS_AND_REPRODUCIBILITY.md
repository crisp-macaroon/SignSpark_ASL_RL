# Limitations and reproducibility statement

SignSparK RL project · How2Sign (ASL) · closed 2026-11-07 · **released-checkpoint result, not a paper reproduction**

## What the evidence supports

- **Amortised RL (ACMS, REINFORCE):** four new seeds give a pooled gain in right arm–hand coordination (space R) of +0.0022 [−0.0013, +0.0056]. The registered category is **seed-sensitive**, and the gain is about 1/23 of the registered 0.05 relevance threshold. Preservation passes in all runs.
- **Per-clip feasibility (FG-1, pathwise gradients, not RL):**
  - V3 bilateral control is **positive** (R +0.089, L +0.107 on fresh noise, preservation passes).
  - V2 per-clip ACMS is **inconclusive**. Its gain was +0.102, but its articulation ratio of 1.102 exceeds the registered 1.10 bound.
  - V1 learned M-C coupling is **negative**.
- **Interpretation (not tested):** the frozen sampler is controllable per clip; a single shared policy did not capture this.

## Limitations

1. **Power.** Four new training runs (t-critical 3.18) give a wide across-run interval. "Seed-sensitive" reflects both heterogeneity (I² 0.97) and low power.
2. **Metric scope.** R coordination is a motion statistic validated automatically (V-R1 to V-R4). We claim nothing about perceptual naturalness, intelligibility, semantic correctness or ASL quality. R is primary. J (SMPL-X joints, with about 1–2% skinning leakage) is descriptive only, and R and J are not independent replications.
3. **FG-1 scope:**
   - 16 TRAIN clips with one fit per clip and no seed replication of the gate.
   - Per-clip fitting needs the clip in advance and uses pathwise gradients through the unrolled sampler. It shows controllability, not a deployable or RL-trained policy.
   - It does not separate amortisation from the gradient estimator as the cause of the ACMS shortfall.
4. **V2 preservation.** V2 misses the articulation bound by 0.002. The bound was applied exactly as registered.
5. **Monitoring analyses.** OPT-C and OPT-G are monitoring only; no checkpoint was selected and update 125 is primary.
6. **Pretraining data.** Whether the released checkpoints were pretrained on How2Sign test data is undocumented. This affects absolute levels only, not paired comparisons.
7. **Determinism.** cuDNN non-determinism is permitted (matmul TF32 off), so reruns may differ in low-order bits.
8. **Unavailable metrics.** DTW/MPJPE, BLEU or back-translation, FID, success rate, regret, other RL algorithms (PPO/GRPO/SAC), perceptual or human evaluation, and test-split results are **unavailable**: none were run.
9. **Coverage check.** The earlier slide deck was not in the workspace, so a direct deck-to-deck coverage check was unavailable.

## Reproducibility

- **Environment:** Windows 11 Pro, Python 3.12, torch 2.10.0+cu128, one NVIDIA RTX A4000 16 GB. `.venv-infer` is used for generation and R; `.venv-render` (with smplx) for J and the validity suite.
- **Checkpoints:** read-only.
  - body `ema_0.9999_200000.pt` SHA-256 bf95bb02…a380;
  - hand SHA-256 5bb8e407…16c2.
  - Hashes are verified before and after all experiments (see `EXPERIMENT_MANIFEST.json`).
- **Seeds:**
  - ACMS run d (1–4): init 700d, sampler 5000+d, training noise 50M+d·1M, evaluation noise 40M (shared);
  - OPT-G noise 45M;
  - FG-1 fit noise 60M, held-out noise 61M; init seeds 8000+a / 8100+a (V3), 1000+a (V1).
  - The preflight checks every seed and noise base for disjointness (`experiments/stage5_multiseed/out/preflight.json`).
- **Frozen inputs (unchanged):** `FROZEN_TARGETS_R0.json` (SHA 26f28f9a…), R/J metric code, validity rules, rewards and thresholds. Stage 4 and Stage 5 artifacts were re-verified against the preflight snapshot at closure.
- **Commands:**
  - `experiments/stage5_multiseed/run_multiseed.py` (training and evaluation);
  - `experiments/stage6_gate/run_stage6.py` (FG-1, OPT-G, OPT-C);
  - analysis with `pooled_analysis.py` and `fg1_analyse.py`;
  - figures, report and deck with `experiments/stage6_final/{make_figures,report_build,deck_content}.py`;
  - tests with `run_all_tests.py --integration`;
  - manifest and bundle with `manifest.py --bundle`.
  - Each job's exact command, exit code, runtime and GPU memory are in its `runner_status.json` and the manifest.
- **Bundle:** `research/final/` holds the report (PDF/HTML/LaTeX), the deck (PPTX/PDF), the manifest and the zip bundle. Sample dumps over 50 MB are hashed in the manifest but left out of the zip.
