# Stage 4 rev. 4.0: decision report

*2026-11-03.*

**What triggered it:** your instruction to remove human verification from the scope because of time constraints.

**What it is:** documentation only. Nothing was run, generated, implemented or trained for this revision.

**Previous versions preserved** in `research/archive/`:
- `STAGE4_REPORT_rev3.3a.md`;
- `appendix_gaussian_controller_rev3.3.md`;
- `RESEARCH_LOG_pre_rev4.0.md`.

## What changed

| Area | Before (rev. 3.3a) | Now (rev. 4.0) |
|---|---|---|
| Human evaluation | E1 pilot gated reward use; D-d perceptual dominance; GLMM power simulation | **E1 deferred indefinitely**; not a prerequisite for anything; design not carried forward; D-d removed |
| Claim scope | "rated by fluent signers as more natural / better coordinated as motion" | **measurable motion quality only**: P1a coordination, P1b dominance without detected left-hand degradation, per-stream preservation; secondary checks give "no regression detected" only |
| Claim discipline | evidence labels only | plus claim types **G** (conditional theorem), **M** (automated measurement), **PH** (perceptual hypothesis, never asserted); strongest automated claims S1–S6 (§0.2) |
| Measurement spaces | rotation statistics; SMPL-X "if available" | **two distinct spaces:** R (reward and gating) and J (SMPL-X, evaluation only); every statistic, target and claim names its space |
| Coordination target | fixed 0.47 (arm–hand), 0.32 (L–R) | **retired as targets** (0.47 came from test / dev-256; E0 found 0.439 on full dev in R and 0.232 in J). Replaced by train-reference targets per space, computed in R0 and frozen before Stage 5 |
| Reward validity | perceptual Phase-1 criteria | **automated criteria V-R1 to V-R4:** discrimination and cross-space consistency met (E0); chance satisfiability reported; non-triviality pending R0 |
| Evaluation | humans + J + Fréchet + non-inferiority + BT | J statistics + Fréchet + non-inferiority / equivalence + secondary checks (BT; SMPL-X frame-aligned MPJPE) |
| E2e | rotation space only | unchanged gating; **plus non-gating E2e-J** (joint-space T3/T4/T5-B from saved dumps) |
| New step | — | **R0:** reference-only train targets in R and J; SMPL-X hand mirror-symmetry check; V-R3 synthetic checks |
| Limitations | scattered | consolidated in §16.1 (L1–L10, R1–R2) |

## What did not change

- the M-C Gaussian design and all Appendix G derivations;
- K = 10; the same-implementation rule;
- E2 order E2d → E2e → E2a → E2b → E2c, with separate approvals;
- every E2e threshold, margin (±5%, δ_S₂ rule and floor), branch (R1/R2/R3) and the run order;
- D-a / D-b / D-c definitions;
- M-D comparator; safeguards.

## E0 findings used

- **Dominance agrees across spaces** (per-clip ρ ≈ 0.96). P1b is therefore robust to the choice of space, but J is **not independent evidence** for it.
- **Coordination agrees only moderately** (ρ ≈ 0.5) and has different reference levels. This is why the targets are now space-specific.

## What remains unresolved

1. **Perceptual relevance** of every statistic. Not resolvable in scope (L1); never claimed.
2. **Train-reference target values** in R and J (U-A13), and the J left-side / L–R statistics (U-A14). These need R0.
3. **SMPL-X left/right hand mirror symmetry** (U-A11). If it fails, Theorem 4 covers dom^R only.
4. **The J coordination construct** is one defensible choice among several (U-A12).
5. Unchanged from rev. 3.3a:
   - F4 (code reading only);
   - the adequacy of the 32-cluster bootstrap;
   - throughput estimates;
   - checkpoint provenance (D10).
6. **Weak independence for P1b:** without humans, the only check outside the reward is a near-duplicate statistic (L2).

## Decisions requested from you

1. Approve **Stage 4 rev. 4.0** (report checklist item 1) and **Appendix G rev. 4.0** (item 2).
2. **Go-ahead for E2d**: the next step in order; cap 45 min; GPU; no training. The plan is in `E2_EXECUTION_CHECKLIST.md`, Step 1. It runs only on your separate, explicit go-ahead.
3. **In principle (specification only):**
   - E2e with dump saving, plus E2e-J;
   - R0 (CPU, reference-only; any time before Stage 5).

   Approval in principle is **not** execution authorisation. Each of these needs its own explicit go-ahead.
