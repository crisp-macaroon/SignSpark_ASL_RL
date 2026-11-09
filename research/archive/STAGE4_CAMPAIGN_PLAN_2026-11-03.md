# Stage 4 consolidated feasibility campaign: execution plan (for authorisation)

*2026-11-03.*

**Status: NOT authorised; nothing executed.** Revised after your decisions of 2026-11-03.

**Decisions so far:**
- **C-a1 to C-a5 (E2a), C-b1 to C-b3 (E2b) and C-j1 (E2e-J) approved by you** as new, explicitly labelled pre-registrations, subject to the existing registered gates.
- E2b non-gating.
- R0 concurrent on the CPU, with the safeguards R-1 to R-5.
- C-c3 revised (§2a).
- **Still awaiting approval:** C-c1, C-c2, C-c3 (revised), C-c4, C-c5, C-c6 and C-r1 to C-r6.

**Scope:** E2e → E2e-J → E2a → E2b → E2c → R0, under Stage 4 rev. 4.0 and the corrected E2e implementation (preflight corrections; self-test 42/42).

**Protocol note.** The project rule so far is a separate go-ahead after each step's report (report §19). If you authorise this campaign, that rule is replaced *for these six steps only* by the automatic stop rules in §5. I will record this in the research log as your decision. Every registered gate still stops the campaign. Nothing reaches Stage 5.

## 1. Readiness

| Step | Code | Specification | Ready to run on authorisation? |
|---|---|---|---|
| E2e | `experiments/stage4/e2e/` written; synthetic self-test 42/42 | fully registered (§15.3–15.4) + approved P-1 to P-14 | **yes** |
| E2e-J | **not written** | registered (§15.3.2): statistics, bootstrap, agreement table, FK check, cap | after Phase 0 |
| E2a | **not written** | **partly registered** (§15.2 l. 950; §5.4 (d) l. 472) | after Phase 0 + approval of C-a items |
| E2b | **not written** | **one line** (§15.2 l. 951: "time-shift equivariance (δ ∈ ±4, ±8, ±16 frames)"); no metric or threshold | after Phase 0 + approval of C-b items |
| E2c | **not written** | **partly registered** (§15.2 l. 952). "typicality/KL bound" has **no registered numeric value**; optimiser and budget unregistered | after Phase 0 + approval of C-c items |
| R0 | **not written** | registered (§6.0 rule iv; checklist R0): train refs, R and J targets with 95% CIs, U-A11, V-R3 | after Phase 0 + approval of C-r items |

**Phase 0 (part of the campaign, no execution risk):**
- implement E2e-J, E2a, E2b, E2c and R0 under `experiments/stage4/{e2e_j,e2a,e2b,e2c,r0}/`;
- extend the synthetic self-test (no model, no data);
- every new script gets a `--plan` mode that prints its frozen parameters.

I will not start any run until Phase 0's self-test passes.

## 2. Parameters that are NOT registered: proposed pre-registration (approve, edit or reject)

Where rev. 4.0 is silent, I must not invent values during the run. These are proposed now and would be frozen by your authorisation. **None changes a registered value.**

### E2a (registered: K ∈ {1, 2, 4, 10}; outputs and ∇_ε r vs K = 10; gradient-norm profile; stop on non-finite or a step-norm ratio > 10³; bf16 criteria: speed-profile correlation ≥ 0.99, gradient cosine ≥ 0.95; K = 1 invalid [D]; cap 1 h)

| # | Item | Proposal |
|---|---|---|
| C-a1 | Clips / noises | 32 E2e clips; A0 noise k = 1 (seed 10,000,000 + 1000·j + 1; CRN with E2e) |
| C-a2 | Scalar r | the target-free rotation-space coordination scalar used in E2d (corr(R-arm, R-hand) + corr(L-hand, R-hand), chordal speeds). There is no train target yet, so it doesn't depend on R0 |
| C-a3 | Agreement metrics | per clip: speed-profile correlation of G_K vs G_10 outputs (hands), and gradient cosine of ∇_ε r (K vs 10). Report mean and min over clips |
| C-a4 | "K_train confirmed" | **descriptive only. K_train stays 10** (App. G / §5.4 (b): K < 10 optimises a different sampler). No K < 10 is adopted in this campaign whatever the agreement |
| C-a5 | bf16 arm | **not run** (optional in the spec; fp32 fits memory per E2d; avoids any precision change) |

### E2b (registered: δ ∈ {±4, ±8, ±16}; non-gating; cap 1 h)

| # | Item | Proposal |
|---|---|---|
| C-b1 | Shift | ε′(τ) = ε(τ − δ) inside the active frames. Vacated frames get fresh N(0, 1) noise (seed offset recorded). Padded frames unchanged. Applied to body and both hands together |
| C-b2 | Metric | equivariance index E(δ) = correlation between the shifted-noise output's speed profile and the base output's profile shifted by δ, over the overlapping frames, per stream (body arm, L, R), mean over 32 clips with 95% bootstrap CI. References: E at δ = 0 with identical noise (= 1), and with independent noise (≈ same-text agreement) |
| C-b3 | "Viable" (non-gating) | E(δ) ≥ 0.5 for \|δ\| ≤ 8 in every stream, reported as "low-dimensional time-shift action viable / not viable". **No architecture or action change follows from it** |

### E2c (registered: (i) unrestricted per-sample noise optimisation N4; (ii) per-clip optimisation of the Gaussian-family parameters; outcome: "whether amortised M-C is worth building"; negative outcome = "neither reaches the best-of-8×8 level within the typicality/KL bound"; cap 2 h)

| # | Item | Proposal |
|---|---|---|
| C-c1 | Objective | maximise the **right arm–right hand** coordination (rotation space), the same statistic as the A3 best-of-n×n analysis, so the comparison level is like-for-like. Target-free; no R0 dependence |
| C-c2 (revised) | Comparison level | **Primary:** typical-only best-of-8×8 for these 32 clips, from E2e A0 (k = 1–8; candidates with a right-hand noise failing the C-c3 check are excluded, not projected). **Secondary:** all-candidate best-of-8×8 (E2e A0) and the existing dev-256 N = 8 dumps (clips 0–31). The registered A3 figure (0.408, 256 clips) is reported alongside. A verdict that differs between primary and secondary is reported as "comparator-sensitive" (§2a) |
| C-c3 (revised) | (i) N4 typicality bound | **Five constraints:**<br>• overall norm preservation;<br>• channel-wise mean;<br>• channel-wise variance (second moment);<br>• per-channel lag-1;<br>• pooled lag-1.<br>Each bound is a null quantile of the base N(0, I) law. Full specification, justification and synthetic validation in **§2a**. The earlier norm-only proposal is **withdrawn** |
| C-c4 | (ii) family KL bound | per-clip Stiefel U, V (QR parametrisation), κ = 0.95·sigmoid(a), BH structure (r = 60). Exact KL per frame **≤ 99.64 nats** (= the largest E2e condition, BH-r60-κ0.9), enforced by κ ≤ 0.9 |
| C-c5 | Optimiser and budget | Adam on noise / family parameters only (model weights frozen, `requires_grad = False`, never updated):<br>• lr 0.05;<br>• (i) 40 iterations, 1 noise per clip;<br>• (ii) 30 iterations, expectation over 4 training noises per clip, evaluated on 4 held-out noises (A0 k = 5–8).<br>K = 10, checkpointing, B = 8 contexts per pass (E2d: 8.8 GiB) |
| C-c6 | Outcome | "reaches the best-of-8×8 level" = mean held-out (ii), or final (i), right arm–hand coordination ≥ the C-c2 level. Both fail ⇒ the registered negative outcome (FM4: stop, options to you) |

### 2a. C-c3 revised: typicality constraints for E2c (i) N4 (new pre-registration; replaces the norm-only proposal)

**What is and is not registered:**
- **Registered (unchanged):** the negative outcome "neither reaches the best-of-8×8 level within the typicality/KL bound" (§15.2, l. 952).
- **Not registered:** "typicality" had no numeric definition.

The proposal below **defines** typicality for (i); it does not weaken anything registered. The (ii) KL bound (C-c4, ≤ 99.64 nats/frame) is unchanged.

**Constraint set** (per sample, per hand; x ∈ ℝ^{90×L} over active frames; base law i.i.d. N(0, 1); code `experiments/stage4/e2c/typicality.py`):

| ID | Constraint | Bound | Null law | Per-hand null family rate |
|---|---|---|---|---|
| N | Overall norm | ‖x‖² = its initial value (exact projection) | χ²_{90L} | keeps the base sample's own norm |
| M | Channel mean | \|mean_τ x_c\| ≤ z_c/√L | exact N(0, 1/L) | 0.5% |
| V | Channel second moment | mean_τ x_c² ∈ [χ²_L(a_c/2)/L, χ²_L(1 − a_c/2)/L] | exact χ²_L/L | 0.5% |
| A | Channel lag-1 | \|r_c\| ≤ z_c/√L, with r_c = Σ x_{c,τ}x_{c,τ+1} / Σ x_{c,τ}² | asymptotic N(0, 1/L); validated by simulation | 0.5% |
| P | Pooled lag-1 | \|mean_c r_c\| ≤ z_p/√(90(L − 1)) | asymptotic; validated | 0.1% |

**Constants:**
- a_c = 0.005/90 (a Bonferroni split over the 90 channels), so z_c = Φ⁻¹(1 − a_c/2) = 4.03;
- z_p = Φ⁻¹(0.9995) = 3.29.
- Example bounds at L = 146:
  - mean ≤ 0.334;
  - second moment ∈ [0.596, 1.543];
  - lag-1 ≤ 0.334;
  - pooled lag-1 ≤ 0.0288.

**Monitored, reported, not constrained:**
- pooled lag-2, lag-3 and lag-4 autocorrelation;
- the maximum \|correlation\| between hand-noise channels and the fixed body noise;
- the χ² position of ‖x‖².

Each is compared with its null quantile, and any excursion is flagged "atypical".

**Justification:**
1. **Every bound is a property the base noise itself has with high probability.** The constrained set is a *typical set* of the base law, not an arbitrary box. The family-wise levels (0.5% each for M, V, A; 0.1% for P; ≤ 1.6% per hand) mirror the T1 philosophy (null false-failure ~1%).
2. **M and V use exact finite-L laws.** A and P use asymptotic laws, checked by simulation below.
3. **Why lag-1 matters here.** The output timing is noise-driven (A2). Smoothing the noise in time is the most direct, and most atypical, route by which an optimiser could impose timing. Constraining lag-1 closes it.
4. **Why the channel mean matters.** It excludes the mean-shift mechanism, which is explicitly deferred (App. G.6.2, "μ_s ≠ 0 … deferred").
5. **The constraints make (i) and (ii) comparable.** Every member of the Gaussian family in (ii) with σ = 1 keeps every channel exactly N(0, 1) and its frames i.i.d. (Thm 2), so (ii)'s samples satisfy the same constraints with the same null probability. Both arms then live in the base-typical set:
   - (i) is free within it, per sample;
   - (ii) is restricted to a KL-bounded joint law.

**Synthetic validation** (`experiments/stage4/e2c/validate_typicality.py` → `typicality_validation.json`; pure N(0, 1) arrays only, 4,000 null samples per length, seed 424242; no model, data or campaign seed):

| Check | Result |
|---|---|
| Null rate of "any violation" per hand over the 32 E2e clip lengths (nominal 1.59%) | first run (4,000 per length): mean 1.30%, max 1.88%. **Final review (16,000 per length, `typicality_review.json`): max 1.57%; no length significantly above nominal (all z ≤ −0.19; Bonferroni one-sided over 30 lengths). The 1.88% was Monte-Carlo noise (SE 0.2% at n = 4,000).** The A bound is conservative (per-channel tail 0 to 4.7e-5 vs nominal 5.6e-5, most conservative at short L); P is within MC error of 0.1%. Expected ≈ 0.9 of the 64 initial hand-noises need the initial projection (E-4) |
| AR(1) ρ = 0.15 on all channels | detected 100% (L = 56, 150, 304), mainly by P |
| AR(1) ρ = 0.5 on 10 channels | detected 98.6% / 100% / 100% |
| Moving average, w = 3, unit variance | detected 100% |
| 10 channels scaled ×1.5 | detected 100% (V) |
| 10 channels offset +0.3 | detected **30%** at L = 56, 99% at L = 150, 100% at L = 304. **A known limitation:** small mean offsets are hard to detect on short clips, an inherent finite-L limit of the mean bound |

**Enforcement** (new pre-registrations; noise variables only, model frozen):

| # | Rule |
|---|---|
| E-1 (rev. 2) | After each Adam step, the **exact one-shot M/V/N projection** `project_mvn_exact`:<br>• clamp channel means into the M band;<br>• keeping the means, set every channel's centred energy by one common log-scale t, clipped to the V band, with t chosen by bisection so that Σ second moments = the required norm.<br>Targets lie 1e-9 (relative) inside each band, so floating-point error cannot leave it; **the bounds are unchanged**. It returns `ok = False` if the M/V/N set is empty (impossible for base noise, whose norm is inside [90·lo, 90·hi]). **Replaces** the alternating 5-iteration scheme, which the review showed does **not** guarantee feasibility (as low as 0%; table below) |
| E-2 | A and P (non-convex): penalty λ·Σ_c max(0, \|r_c\| − b_A)² + λ·max(0, \|r̄\| − b_P)², **λ = 100**, added to the negative objective. **The penalty is a search aid only; it guarantees nothing** |
| E-3 (rev. 2) | **Hard feasibility gate.** Every candidate result passes `feasible()`: N within 1e-6 relative, and M, V, A, P each within their bound, recomputed from the stored noise in float64. **An iterate that fails is never reported, stored as a result or used in any aggregate.** The reported result per sample is the best objective among iterates that pass, including the feasible start. A failed check is logged with which constraint failed |
| E-4 (rev. 2) | **Feasible start.** If the base noise fails `feasible()`: E-1, then a repair by penalty descent on the noise alone (no model; minimise ‖y − x‖²/‖x‖² + penalty, with E-1 after each of ≤ 300 steps), stopping at the first iterate that passes `feasible()`. The projected start is recorded with its relative change |
| E-5 (new) | **No feasible point:** if E-4 finds no feasible start, the sample is marked "no feasible start", is **not optimised**, and enters the aggregate **at its unprojected base objective** (zero gain; conservative, labelled). If more than 3 of the 32 clips (> 10%) have no feasible start, N4 is reported **"inconclusive (feasibility)"**, not pass or fail. A feasible-only aggregate is also reported |

**Final review results** (`experiments/stage4/e2c/review_typicality.py` → `typicality_review.json`; synthetic only, seed 97531):

| Test | Result |
|---|---|
| Joint M/V/N projection, **alternating 5 iterations** (old E-1): share feasible | null violators: 0% (L = 28, 56), 27% (146), 38% (304). Channel-scale perturbation: 6–29%. Combined perturbation: 11–33%. **Does not guarantee feasibility** |
| Joint M/V/N projection, **exact one-shot** (new E-1) | **100% feasible in all 10,000 cases** (4 lengths × 5 perturbation types × 500) |
| A/P repair (E-4), null violators | 100% success (n = 240), median 1 step, median relative change 0.2–1.0% (max 2.8%) |
| A/P repair, AR(1) ρ = 0.3 on all channels (strong perturbation) | 100% success at L = 28, 56, 146; **0% at L = 304 within 300 steps**. So repair **can** fail, and E-3/E-5 are required |
| Projection bias on base noise (19,200 hands at the 32 real lengths) | **1.34% of hands modified**; among those, median relative change 0.14% (p95 1.0%, max 1.7%); population mean relative change 3.2e-5; KS distance pre vs post ≤ 0.0055 on every statistic; 0 unrepaired |

**Projection bias and fairness of the best-of-8×8 comparison (no equivalence claimed):**
- The projection changes about 1.3% of starting hand-noises, by about 0.1–1% in norm.
- The resulting population shift in the noise statistics is small (KS ≤ 0.0055). But **its effect on generated coordination is not measured**, and synthetic arrays cannot measure it, so equivalence is **not** claimed.
- Raw base candidates are typical only with probability ≈ 98.7% per hand. With 8 candidates, P(at least one atypical right-hand noise) ≈ 10%, so the raw best-of-8×8 could select an atypical sample.
- **Proposed C-c2 revision for a like-for-like comparison:**
  - **Primary comparator:** "typical-only best-of-8×8", computed from E2e's A0 samples (k = 1–8; noise reconstructible from the registered seeds). Candidates whose right-hand noise fails `feasible()` are **excluded, not projected**, so every comparator output is a genuine sample.
  - **Secondary comparators:** the all-candidate best-of-8×8 (E2e A0) and the existing dev-256 dump value.
  - If the N4 verdict differs between primary and secondary, it is reported as **"comparator-sensitive"**.
  - N4's gain is reported relative to its projected start, and also relative to the raw start.

**How the constraints change the N4 experiment:**
- N4 becomes "per-sample noise optimisation **constrained to the base-typical set**", not "unrestricted". Its role as an upper reference is now the upper reference among typical noises.
- Raw base samples are **not** typical by construction (≈ 1.3% of hands fall outside the set). Hence the typical-only primary comparator above.
- **Routes that remain open to the optimiser:**
  - redistributing energy across time and channels within the bands;
  - phase and timing patterns not visible at lag 1;
  - correlation with the fixed body noise. This is the coupling mechanism that (ii) parametrises with exact KL; it is monitored, not blocked.
- **Routes that are closed (or strongly limited):**
  - temporal smoothing;
  - channel amplitude inflation or deflation beyond the null band.
- **Routes only partly closed (retained limitation):**
  - **Static offsets are NOT all excluded.** The mean bound is z_c/√L, so small offsets on short clips pass: +0.3 on 10 channels is detected only **30% at L = 56** (99% at 150, 100% at 304), and the shortest E2e clip has L = 28.
  - The lag-1 bound is also most conservative at short L.
  - N4 on short clips can therefore exploit small static offsets. Results are additionally reported split by clip length (L < 100 vs ≥ 100), and the per-channel mean excursions of the final noise are reported.
- **Interpretation:**
  - A positive (i) result is stronger evidence that typical noise can carry the timing signal.
  - A negative (i) result is evidence only for this constrained set. It cannot show that an unconstrained optimiser would fail, and it is not evidence against (ii).
  - Higher-lag structure (lags 2–4) is monitored. If the optimiser exploits it, the excursion is reported, and the result is labelled "typical at lag 1 only".
- **Cost:** the projection and penalty add negligible compute. The budget (C-c5: 40 iterations) is unchanged.

### R0 (registered: train references only; R and J targets τ*_ah(L), τ*_ah(R), τ*_lr, t* with 95% clip-bootstrap CIs; U-A11 mirror check; V-R3 synthetic checks; ≈ 2 h CPU [E])

| # | Item | Proposal |
|---|---|---|
| C-r1 | Data | `data/raw/SignSparK_data/train/How2Sign_reopt_train.lmdb` (29,630 clips), read-only, the upstream loader (`flip_left_hand=True`, seq_len 304 truncation as in all runs). **No dev or test data.** Clips with L < 8 are excluded (as E0) |
| C-r2 | J space | E0.4 FK setup; J statistics exactly as §6.0 (wrist-local finger speeds) |
| C-r3 | Bootstrap | 2,000 clip resamples, seed 0 |
| C-r4 | U-A11 | max \|p_L − M·p_R\| over the SMPL-X rest hand joints and fingertips (M = diag(−1, 1, 1)); report in mm; plus dom^J of synthetic identical-pose hands |
| C-r5 | V-R3 | static pose, global mean pose, and shared-spike sequences scored by every reward statistic (R and J); expected values stated before the run |
| C-r6 | Cap | 3 h CPU (the [E] figure was 2 h; the 29,630-clip FK is the uncertain part) |

### E2e-J (registered; one implementation detail)

| # | Item | Proposal |
|---|---|---|
| C-j1 | Bootstrap seed | 0 (as E2e) |

## 3. Execution order and commands

**Order (your decision):** E2e → E2e-J → E2a → E2b → E2c, with **R0 concurrently on the CPU**. R0 touches no GPU, no E2 data and no E2 results.

**R0 concurrency safeguards** (so that R0 cannot threaten E2e's 1.5 h cap):

| # | Safeguard |
|---|---|
| R-1 | R0 runs as a **separate process** at Windows **BelowNormal** priority, with torch/OMP/MKL threads limited to **4 of 12**. E2e keeps normal priority and the remaining threads |
| R-2 | **Independently stoppable:** R0 checks for `experiments/stage4/r0/STOP` between chunks of 500 clips and exits cleanly. Progress is checkpointed per chunk (`r0/out/chunks/`), so a stopped R0 resumes from the last chunk with identical results (deterministic; the bootstrap runs only at the end) |
| R-3 | **Watchdog on E2e's cap:** if E2e's elapsed time exceeds **60 min** (two-thirds of its 1.5 h cap) while R0 is running, I create the STOP file. R0 resumes after E2e ends. The E2e default estimate is 25–30 min, worst case 45 |
| R-4 | R0 never writes to any E2 directory and never reads dev or test data. A failure stops only R0; the E2 sequence is unaffected |
| R-5 | R0's own cap (C-r6, 3 h) counts its running time only (paused time excluded) |

**Environment for every command:**
```
cd C:\Users\balaji\Downloads\rlproj\rlproj
$env:HF_HOME="$PWD\models\hf_cache"; $env:WANDB_MODE="disabled"; $env:HF_HUB_OFFLINE="1"
```

| Order | Step | Command | Env |
|---|---|---|---|
| 0 | Phase 0 self-test | `.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2e\selftest.py` (+ the new self-tests) | infer / render |
| 1 | E2e | `.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2e\e2e_run.py --out experiments\stage4\e2e\out --dumps experiments\stage4\e2e\dumps *> experiments\stage4\e2e\run.log` | infer (GPU) |
| 1‖ | R0 (concurrent) | `.\.venv-render\Scripts\python.exe -E -s experiments\stage4\r0\r0_run.py --out experiments\stage4\r0\out *> experiments\stage4\r0\run.log` | render (CPU) |
| 2 | E2e-J | `.\.venv-render\Scripts\python.exe -E -s experiments\stage4\e2e_j\e2ej_run.py --dumps experiments\stage4\e2e\dumps --e2e experiments\stage4\e2e\out --out experiments\stage4\e2e_j\out` | render (CPU) |
| 3 | E2a | `.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2a\e2a_run.py --out experiments\stage4\e2a\out` | infer (GPU) |
| 4 | E2b | `.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2b\e2b_run.py --out experiments\stage4\e2b\out` | infer (GPU) |
| 5 | E2c | `.\.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2c\e2c_run.py --out experiments\stage4\e2c\out` | infer (GPU) |

E2e-J (CPU) can overlap E2a/E2b (GPU) because neither depends on the other.

**Reports:**
- `research/stage4/E2E_REPORT.md` (with an E2e-J section), `E2A_REPORT.md`, `E2B_REPORT.md`, `E2C_REPORT.md`, `R0_REPORT.md`;
- the consolidated `research/stage4/STAGE4_EXECUTION_SUMMARY.md`;
- `RESEARCH_LOG.md` updated after each step.

## 4. Runtime and resources [E]

| Step | Basis | Estimate | Cap |
|---|---|---|---|
| Phase 0 | implementation + synthetic tests | ≈ 2–3 h of my work (not compute) | — |
| E2e | E2d-measured harness speed | 25–30 min (worst 45) | 1.5 h (registered) |
| E2e-J | 4,096–7,168 FK calls at ≈ 0.15–0.2 s | 15–30 min | 1 h (registered) |
| E2a | 4 K × 4 batches of 8, one gradient pass each (≈ 5.9 s at K = 10) | ≈ 5–10 min incl. model load | 1 h (registered) |
| E2b | 7 body + 7 hand calls | ≈ 5 min | 1 h (registered) |
| E2c | (i) 40 iter × 4 passes × 5.9 s ≈ 16 min; (ii) 30 iter × 16 passes × 5.9 s ≈ 47 min; + held-out evaluation | ≈ 70–80 min | 2 h (registered) |
| R0 | 29,630 clips; J FK ≈ 0.15 s per clip ≈ 75 min + loading + bootstrap | ≈ 1.5–2.5 h CPU | 3 h (C-r6) |
| **Total compute** | | **sequential ≈ 4.5–6 h; with R0 concurrent ≈ 2.5–3.5 h**; worst case under all caps ≈ 10.5 h | — |

**Resources:**
- **GPU:** peak ≈ 10 GiB (E2e T0 (b) with one M-CLIP); E2c ≈ 8.8 GiB at B = 8 (E2d-measured). The 14.9 GiB free leaves headroom.
- **CPU:** R0 and E2e-J use CPU cores (6 cores / 12 threads); E2e's metrics also use CPU. Expect slower metric steps while R0 runs (runtime only).
- **RAM:** < 10 GB at any time (the dev-256 dump ≈ 1.4 GB; train LMDB streamed).
- **Disk:** E2e dumps ≤ 1.7 GB; others < 0.5 GB; 110 GiB free.
- **Data:**
  - dev clips 0–31 and existing dev-256 dumps (E2e, E2e-J, E2a, E2b, E2c);
  - the train LMDB (R0 only);
  - **no test data in any step**.
- **Models:** released checkpoints read-only (SHA re-verified at campaign start); SMPL-X NPZ (E2e-J, R0).

## 5. Stop conditions

**Campaign-level rule:** a registered gate failure stops the campaign at once; outputs are saved and a failure report is written. There is **no threshold relaxation and no fallback controller** in any case.

| Step | Stops the campaign | Continues (reported) |
|---|---|---|
| Start | checkpoint SHA mismatch; Phase 0 self-test fail; < 10 GiB disk | — |
| E2e | t*₂₅₆ not computable; T1 (a) fail; T1 calibration shortfall (P-1); T0 fail; T1 fail; T2 fail or straddle; T5-A fail (any BH/LR condition); dump write failure; 1.5 h cap; **T3 and T4 both fail (FM13)**: E2a and E2c depend on E2e (§15.2), so the campaign stops with the options (a)–(e) of §15.2 and no automatic switch | T2 calibration-inconclusive (theory-conditional wording); T5-A inconclusive; R3 branch (SS removed; P1b target-degenerate, reported); T5-B any outcome |
| E2e-J | — (non-gating) | FK failure ⇒ E2e-J stops and is reported; the campaign continues, because E2a–E2c do not depend on it |
| E2a | non-finite gradients; step-norm ratio > 10³; 1 h cap | any agreement values (descriptive, C-a4) |
| E2b | — (non-gating) | crash or cap ⇒ reported; the campaign continues (E2c does not depend on E2b) |
| E2c | 2 h cap (report completed parts) | both (i) and (ii) below the best-of-8×8 level ⇒ the registered **negative outcome** (FM4), reported with options; it is the last GPU step |
| R0 | data error; L/R mismatch; non-finite FK; 3 h cap ⇒ R0 stops and is reported | E2 steps are unaffected (independent) |

**At the end, in every case:**
- the consolidated summary;
- **no Stage 5 work, no controller implementation or training, no test data, no human evaluation**.
- Then I stop and wait for your decision.

## 6. Exact approval statement required

Authorisation is valid only if you send the following statement, verbatim or with explicit edits:

> I authorise the Stage 4 consolidated feasibility campaign as specified in `research/stage4/STAGE4_CAMPAIGN_PLAN.md` (revised 2026-11-03): Phase 0 implementation and synthetic self-tests, then E2e → E2e-J → E2a → E2b → E2c, with R0 running concurrently on the CPU under safeguards R-1 to R-5.
> For these six steps only, the automatic stop rules in §5 replace the per-step go-ahead.
> I approve as new, explicitly labelled pre-registrations: C-c1, C-c2 (revised: typical-only primary comparator), C-c3 (final, §2a: constraints N, M, V, A, P with unchanged bounds; the monitored quantities; enforcement rules E-1 rev. 2 (exact projection), E-2, E-3 rev. 2 (hard feasibility gate), E-4 rev. 2, E-5 (no-feasible-point handling); the retained short-clip offset limitation), C-c4, C-c5, C-c6, and C-r1 to C-r6, in addition to the already approved C-a1 to C-a5, C-b1 to C-b3 and C-j1.
> All registered thresholds, margins, sample counts, seeds and acceptance criteria of Stage 4 rev. 4.0 and the approved E2e preflight decisions remain in force. There is no threshold relaxation and no fallback controller. A registered gate failure stops the campaign with saved outputs and a failure report.
> E2e-J and E2b are non-gating. R0 uses train references only and computes separate R-space and J-space targets. No test data, no Stage 5 work, no controller training, no human evaluation.
> At completion, produce one consolidated Stage 4 report and stop.

If you want to change any item, edit the statement; I will treat only the items in your statement as approved.
