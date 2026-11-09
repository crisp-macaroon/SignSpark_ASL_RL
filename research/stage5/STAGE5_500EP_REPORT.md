# Stage 5: 500-episode exploratory RL pilot (ACMS). Final report

*2026-11-04. Released-checkpoint result, not a paper reproduction.*
- Motion statistics only: **no semantic, naturalness, intelligibility or ASL-quality claim.**
- Exploratory: this result does **not** validate or confirm the Stage 4 hypothesis. The Stage 4 results (E2e FM13; H0 for P1a under fixed-orientation M-C; E2c (ii) negative) stand unchanged.

## Outcome

**Pre-registered verdict: POSITIVE**, under the rule fixed before the run (design §4). The trained controller raises held-out right arm–right hand coordination (space R v1.1) over uncoupled sampling:
- **+0.0022 [95% CI +0.0014, +0.0031]** (256 dev clips × 4 common noises);
- all six motion-preservation checks pass;
- no undefined values.

**The effect is very small:**

| Quantity | Value |
|---|---|
| Gap closure toward the frozen target τ = 0.4514 | **0.5%** |
| **0.05 threshold** (reported separately) | **not reached**: the point estimate (0.0022) is about 23× below it, and so is the CI |
| Coordination, uncoupled → trained | 0.0207 → 0.0229 (reference level ≈ 0.45) |

**In one sentence:** a statistically detectable but practically negligible improvement, under the tested dataset, checkpoint, controller, noise allocation and evaluation protocol only.

**Labels:** [V] directly measured · [D] mathematical implication · [I] interpretation · [U] unresolved limitation.

---

## 1. What was run (as approved; nothing changed during execution)

| Item | Value |
|---|---|
| Design / approvals | `STAGE5_500EP_DESIGN.md` (A1–A7), `STAGE5_IMPLEMENTATION_AUDIT.md` (tests 15/15 unit, 6/6 integration); F2: τ = 0.4514 retained, by your decision |
| Controller | ACMS: ε_R = μ_φ(ŝ) + ξ, with μ_φ = β·U·tanh(W∗ŝ + c), where ŝ is the generated right-arm speed profile<br>r = 4, ±8-frame kernel, 433 parameters; KL < 1 nat/frame by construction<br>Right hand only (the body and left hand cannot be affected) |
| Reward | **target matching** r_ah = −\|coord_ah^R(right) − 0.4514\| (R v1.1), not unrestricted maximisation<br>Constraints art / jerk / ext / act via dual ascent<br>S-3: undefined → −1.4514; A3: undefined constraint → +1 |
| Training | **500 episodes = 125 TRAIN clips × 4**<br>REINFORCE with an RLOO baseline; Adam lr 0.01, clip 1.0; 125 updates<br>Seeds: clips 5000, noise 5e7 + 1000g + i, policy init 7000 |
| Evaluation | **dev-256 × 4** eval noises (4e7 + 1000j + k)<br>Conditions: uncoupled / initial (update 0) / trained (update 125, **no selection**), on **common noise**<br>Clip bootstrap 2,000, seed 0 |
| Data | train (episodes) and dev (evaluation) only; **test never opened** (logged: training `["train"]`, evaluation `["dev"]`) |

## 2. Directly measured results [V]

### 2.1 Training (500 episodes; `out/train/`)

| Quantity | Value |
|---|---|
| Status | completed, 500/500 episodes, exit 0, **283.8 s**<br>GPU peak 10.54 GiB allocated / 10.73 reserved |
| SignSparK weights | trainable parameters 0; checksum start = end (**unchanged**) |
| S-3 (undefined primary) | **0 / 500** |
| A3 (undefined constraint) | **0** for every constraint |
| Invalid streams | 0 (arm L/R, hand L/R, input finite: controlled and uncoupled twin) |
| Invalid arm features | 0 |
| Constraints | **never violated:** the maximum clipped c_k over all episodes is art −0.062, jerk −0.033, ext −0.020, act −0.165 (all < 0). **λ_k = 0 throughout** |
| KL per frame | 0.0012 (first group) → 0.0035 (last); max 0.0041; cap 1.0 |
| β | 0.0701 → 0.0755 |
| ‖μ_t‖ max | 0.149 |
| Gradients | norm before clipping: mean 0.44, max 1.10 (clipped in 3 of 125 updates); mean update norm 0.058; all finite |
| Parameter norm | 19.61 → 19.78 |
| RLOO | advantages summed to 0 in every group (max \|Σ\| 3.9e-16) |
| Group reward R (mean of 25 groups) | first 25: −0.420; last 25: −0.438 (clip-dependent; **no visible upward trend**) |
| Controlled − uncoupled twin coordination over all 500 training episodes | +0.00007 [−0.0005, +0.0006] (group bootstrap) |

Since no constraint was ever active, **R = r_ah in every episode.**

Training curves: `experiments/stage5/out/plots/training_curves.png`. The policy-loss values include the −½‖ξ‖² term of log π, so they are not an objective value (audit F5).

### 2.2 Held-out evaluation (dev-256 × 4 = 1,024 samples per condition; `out/eval/`)

**Status:** completed, exit 0, 1,638.9 s; GPU peak 10.54 GiB; weights unchanged; only `dev` opened.

**Space R v1.1 (primary):**

| Statistic | Uncoupled | Initial | **Trained** |
|---|---|---|---|
| Right arm–hand coordination: mean (median) | 0.0207 (0.0086) | 0.0201 (0.0083) | **0.0229 (0.0100)** |
| Clip-mean 95% CI | [0.0110, 0.0308] | [0.0104, 0.0302] | [0.0132, 0.0330] |
| Left arm–hand coordination | 0.0034 | 0.0034 | 0.0034 (**identical**) |
| L–R coordination | 0.0129 | 0.0132 | 0.0135 |
| Dominance log(A_L/A_R) | −0.0107 | −0.0101 | −0.0078 |
| Undefined (any statistic) | 0 | 0 | 0 |

**Paired differences** on common noise, clip-mean with 95% CI (n = 256 clips, 1,024 pairs):

| Statistic | Trained − uncoupled | Trained − initial | Initial − uncoupled |
|---|---|---|---|
| **Right arm–hand coordination** | **+0.00220 [+0.00144, +0.00312]** | +0.00277 [+0.00221, +0.00341] | −0.00057 [−0.00110, −0.00003] |
| Left arm–hand coordination | 0 (exact) | 0 | 0 |
| L–R coordination | +0.00056 [−0.00004, +0.00121] | +0.00029 [−0.00015, +0.00077] | +0.00027 [−0.00011, +0.00066] |
| Dominance | +0.00292 [+0.00129, +0.00494] | +0.00233 [+0.00128, +0.00365] | +0.00059 [−0.00034, +0.00157] |

**Per-clip distribution, trained − uncoupled** (right arm–hand, R):
- Quantiles: min −0.010, p10 −0.004, p25 −0.002, **median +0.0014**, p75 +0.005, p90 +0.009, max +0.079.
- **156 of 256 clips are positive.** Wilcoxon p = 2.7e-7 (descriptive).
- **Outlier sensitivity** (descriptive; the verdict uses the registered rule):
  - without the largest clip (dev 234, +0.079): +0.0019 [+0.0013, +0.0026];
  - 10% trimmed mean: +0.0017.

Panel: `out/plots/eval_R_space_coord_arm_rhand.png`.

**Per-stream statistics, right hand (means):**

| Statistic | Uncoupled | Initial | Trained |
|---|---|---|---|
| Activity A_R | 8.1339 | 8.1309 | 8.1203 |
| Mean speed m1 | 0.04514 | 0.04512 | 0.04506 |
| Articulation m2 | 0.23436 | 0.23438 | 0.23414 |
| Jerk m3 | 0.017929 | 0.017922 | 0.017900 |
| Mean angle m4 | 0.6262 | 0.6268 | 0.6274 |
| Extreme-frame fraction | 0 | 0 | 0 |

**Left hand:** all per-stream statistics are identical across the three conditions (verified), as derived.

**Pre-registered preservation checks** (trained vs uncoupled, paired per sample): **all PASS**.

| Check | Value | Limit |
|---|---|---|
| Mean articulation ratio | 0.9987 | [0.9, 1.1] |
| Mean jerk ratio | 0.9977 | ≤ 1.10 |
| Mean extreme-frame difference | 0.000 | ≤ 0.02 |
| \|mean log activity ratio\| | 0.0029 | ≤ 0.223 |
| Undefined fraction | 0 vs 0 | ≤ +0.005 |
| Max KL | 0.0048 nats/frame | ≤ 1 |

**Other measurements:**
- **S-4 worst-case sensitivity:** with no undefined values it is identical to the primary result, +0.0022 [+0.0014, +0.0031].
- **KL per frame:** initial mean 0.0011 (max 0.0013); trained mean 0.0037 (max 0.0048).
- **C-c3 typicality monitor** (descriptive): violation fractions identical in all three conditions (M 0.49%, V 0.39%, A 0.49%, P 0.10%).
- **Validity flags:** 0 false flags of any kind in any condition.

**Space J v1.1 (descriptive only; never combined with R):**

| Statistic | Trained − uncoupled | Trained − initial |
|---|---|---|
| Right arm–hand coordination | **+0.00262 [+0.00187, +0.00337]** (0.0215 → 0.0241) | +0.00225 [+0.00176, +0.00281] |
| Left arm–hand coordination | 0 (identical) | — |
| L–R coordination | +0.00037 [−0.00029, +0.00104] | — |
| Dominance | +0.00399 [+0.00216, +0.00618] | — |
| Right-hand skinning-leakage ratio, median (p95) | 0.99% (1.96%), the same in all conditions; 0 samples > 10% | — |

Panel: `out/plots/eval_J_space_descriptive_coord_ah_J_R.png`.

## 3. Mathematical implications [D]

1. **The verdict follows mechanically from the pre-registered rule.** The CI lower bound is > 0 (0.00144) and all six checks pass, so the verdict is **positive**. A rule with a magnitude requirement would not have passed; magnitude is reported separately, as you instructed.
2. **Left-hand invariance is exact.** The policy acts only on the right-hand noise, and hands are generated as separate sequences. Left arm–hand coordination and left per-stream statistics are therefore exactly identical across conditions, as verified. Any change in dominance or L–R coordination comes from the right hand alone.
3. **The dominance shift is directionally away from the reference.** The trained controller lowers right activity by 0.17% (A_R 8.134 → 8.120), so dominance log(A_L/A_R) rises by +0.0029, toward 0. The frozen reference t* = −0.392 is right-dominant, so this small shift is **away** from the reference direction. It is far inside the activity constraint, and it is not part of the reward.
4. **Effect size relative to the gap:**
   - gain / (τ − uncoupled) = 0.0022 / (0.4514 − 0.0207) = **0.51%**;
   - reaching 0.05 would need about 23× this effect;
   - reaching τ would need about 196×.
5. **KL budget:** the trained mean shift uses KL ≈ 0.0037 nats/frame, about 27,000× below the per-frame KL of the registered E2e κ = 0.9 conditions (99.64). That E2e condition gave a larger but also sub-threshold Δ (0.017–0.037 on 32 clips). This is a descriptive contrast only: the controllers, clip sets and noise designs differ.

## 4. Interpretation [I]

- **What the result supports:** a learned, body-motion-conditioned temporal mean shift on the right-hand noise produces a **small, reproducible, held-out increase** in R-space right arm–hand coordination. The increase holds without the largest clip, has the same sign in J (descriptive, +0.0026), and comes with no detected change in per-stream motion statistics.
- **What it does not support:** any practically meaningful coordination gain. At 0.5% of the gap and about 23× below Stage 4's transmission threshold, the effect is negligible against the reference–generated gap.
- **The optimisation moved very little:**
  - the controller parameters barely changed (β +8%, KL from 0.001 to 0.004);
  - the training reward showed no visible improvement trend;
  - no constraint was ever approached.
  - 125 REINFORCE updates over a roughly 10⁴-dimensional Gaussian action with Adam at lr 0.01 are low-powered. Within the KL budget, almost all of the capacity was unused.
  - Whether more updates or a larger learning rate would yield larger gains is **untested** and was not authorised.
- **Training and evaluation tension:** over training, the controlled-minus-twin difference was +0.00007 [−0.0005, +0.0006], while evaluation shows +0.0022.
  - The training figure averages over all intermediate policies, most of them close to the initial one. That initial policy *lowers* coordination slightly (−0.0006 [−0.0011, −0.00003]).
  - The training figure also uses different (train) clips.
  - The difference is not a contradiction, but it means **the improvement is visible only for the final policy, and not as a training-reward trend.**
- **Relation to Stage 4:**
  - This is a different controller class: a mean shift conditioned on generated motion, temporal and amortised.
  - It does **not** revisit or alter the Stage 4 conclusions about M-C. It does not show that M-C could have worked, and it does not validate the P1a hypothesis as registered: the 0.05 transmission threshold is not reached.

## 5. Unresolved limitations [U]

1. **Scope:**
   - one released checkpoint;
   - How2Sign only; 125 train clips seen once each;
   - 256 dev clips × 4 noises; oracle length; GF mode.
   - No claim beyond this protocol. **No generalisation is established by 500 episodes.**
2. **Single training seed:** policy init, clip sample and noise each used one seed. Variability across seeds is unmeasured, so the result may be seed-specific.
3. **Dev reuse:** the dev clips 0–31 are the Stage 4 E2-family clips. Dev was never used for training or selection here, but it is not untouched by the overall research programme. Test data was not used.
4. **Measurement:**
   - The coordination statistics are chance-satisfiable (A3: best-of-8×8 0.408, other-sentence null 0.452).
   - The effect is far below any perceptual relevance, and that relevance is out of scope (PH).
   - J space shares the same rotations and is not independent replication.
5. **The magnitude criterion was not pre-registered for this pilot.** "Positive" here means statistically detectable with motion preserved, not practically important.
6. **GPU determinism:** default cuDNN flags were used, as in E2d. The integration mini-runs were bitwise reproducible, but the full run was executed once.
7. **The evaluation's joint-space step took longer than estimated** (27 min in total). No effect on results.

## 6. Recommendation

- **Is further training justified on this evidence?** Not on effect size. The pilot shows a real but negligible effect in its most favourable statistic.
- **Possible next steps** (each would need a new pre-registration and your explicit approval; **none was run**):
  - (a) a multi-seed replication of this exact pilot, to establish whether +0.002 is stable;
  - (b) a capacity-style check of ACMS, analogous to E2c, to establish whether the family can produce gains of order 0.05 at all, before investing in longer training;
  - (c) closing with the current evidence: the Stage 4 negative results plus a negligible Stage 5 exploratory effect.
- My view [I]: (b) is the informative next question. Without it, more episodes risk optimising an effect whose ceiling is unknown.

**Stopped for your review. No further training, experiments or evaluation were run.**

## 7. Reproducibility

| Item | Value |
|---|---|
| Commands | exactly as in audit §6 (`record_env.py --lmdb`; `train_500ep.py`; `evaluate.py --save-dumps`; `plots.py`), all with `.venv-infer\Scripts\python.exe -E -s`, launched via `Start-Process` |
| Environment | Python 3.12.10; torch 2.10.0+cu128; RTX A4000 16 GB (driver 595.79); `HF_HUB_OFFLINE=1`<br>`out/env/environment.json` and `pip_freeze.txt`: **all code, Stage 4, checkpoint and LMDB hashes are identical to the audit record** |
| Config | `config_500ep.json` (ccf2112c…) |
| Checkpoint SHA-256 (SignSparK, unchanged) | body bf95bb02…, hand 5bb8e407… |
| Controller checkpoints | `update_000.pt` 4ea1d3b1…<br>`update_025.pt` 02ed3df0…<br>`update_050.pt` 2b2aceb2…<br>`update_075.pt` 1cba4239…<br>`update_100.pt` 00fb0165…<br>**`update_125.pt` 22d5bf57… (evaluated)** |
| Training outputs | `episodes.json` 2ad57982…, `episodes.csv` 77296fbd…, `groups.json` 70640e32…, `run.json` 28a17fa7…, `train_log.txt` |
| Evaluation outputs | `eval_results.json` 94467b9d…, `eval_samples.json` f0db2a46… (3,072 per-sample records, R and J, with all validity flags), `eval_dumps.npz` (523 MB: body, left hand and the three right-hand conditions) |
| Runtime / GPU | training 283.8 s (10.54 / 10.73 GiB peak); evaluation 1,638.9 s (10.54 / 10.78 GiB) |
| Exit status | 0 for every step |
| Plots | `out/plots/training_curves.png`, `eval_R_space_coord_arm_rhand.png`, `eval_J_space_descriptive_coord_ah_J_R.png` |
