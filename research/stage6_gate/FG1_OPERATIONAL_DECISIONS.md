# FG-1: operational decisions, fixed before running

*2026-11-07, written before any FG-1 GPU work, under the final execution authorisation.*

**Scope of these decisions:** they resolve points the proposal (`research/stage6_proposal/MC_REDESIGN_PROPOSAL.md` §5) left open, without changing the scientific protocol:
- 16 TRAIN clips;
- 16 fitting noises and 16 held-out noises per clip;
- Adam lr 0.05, 30 iterations;
- the registered 0.05 threshold;
- the outcome rule.

## Decisions

| # | Point | Decision | Why |
|---|---|---|---|
| D1 | **V3 runtime-cap conflict** (estimated 80–100 min against the 75 min per-variant cap) | The V3 operational cap is raised to **120 min**; V1 and V2 keep 75 min. The total wall-clock budget is 5 h (proposal: 4 h).<br>The protocol (clips, noises, iterations, lr) is **not** reduced | A cap is an operational safeguard, not a scientific parameter. Reducing clips or noises for V3 alone would make V3 non-comparable with V1 and V2. If V3 still hits 120 min, it is **aborted and reported as not completed**, not shortened and rerun |
| D2 | Hand rows per forward/backward pass | **8 rows** for all variants: 8 contexts for V1/V2, and 4 contexts × 2 hands for V3 | Keeps peak memory at the measured E2c (ii) level (B = 8, 8.5 GiB). The gradient is accumulated over the full 16-noise batch per clip, so it is mathematically identical to one pass |
| D3 | KL bound in the preservation check | V2, V3: **1 nat/frame per hand** (the ACMS cap by construction).<br>V1: the registered M-C right-hand bound **49.82 nats/frame** (E2c (ii) C-c4).<br>V1's KL against 1 nat/frame is also reported | Each family is checked against its own registered bound. Applying 1 nat/frame to M-C would fail V1 by definition (E2c (ii) used 1.2–2.7) |
| D4 | V3 outcome over its three statistics | The rule is applied to each of coord_ah^R, coord_ah^L and coord_lr separately.<br>V3 is **positive** if at least one statistic is positive and the preservation checks pass for both hands; **negative** if all three are negative; otherwise **inconclusive** | U-B5: 0.05 per statistic, unchanged |
| D5 | Preservation for V3 | The six Stage 5 checks are applied to **both** hands vs V0. V1/V2 change only the right hand, so their left-hand outputs are V0's by construction (the same left noise; V0 left outputs are reused) | As proposed |
| D6 | Policy init seeds | V2 head: 8000 + a. V3: right head 8000 + a, left head 8100 + a. V1: the E2c family init seed 1000 + a (gate clip index a = 0..15) | Recorded. The seeds do not collide with any other torch seed use in the project |
| D7 | Clip selection | `fg1_select.py`: `default_rng(5100).permutation`, excluding all clips of the five ACMS training sets (3 skipped), first 8 with L < 100 and first 8 with L ≥ 100 | As proposed; result in `experiments/stage6_gate/out/gate_clips.json` |
| D8 | Run order | After the multi-seed GPU jobs: smoke test (`--test`: 2 clips, 4 noises, 2 iterations, output `out_test/`; its numbers are not results), then prep → V2 → V1 → V3, one process each, then OPT-G and OPT-C (`run_stage6.py`).<br>A failed smoke test skips the full FG-1 (reported) | Sequential GPU; no concurrent jobs |
| D9 | No adaptive changes | No setting changes after any FG-1 result is seen. An aborted variant is reported, not rerun | Authorisation §4 |
| D10 | J space | Held-out J statistics (J v1.1, `evaluate.j_record`) are computed for every variant, descriptive only | As proposed |
