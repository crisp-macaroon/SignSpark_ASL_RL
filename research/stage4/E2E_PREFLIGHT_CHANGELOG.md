# E2e preflight corrections: change log (2026-11-03)

These changes implement the corrections you approved in `E2E_PREFLIGHT_DECISIONS.md`.
- **No registered threshold changed.**
- **No model, dataset, generation, reference statistic or E2e step was run.**
- The synthetic self-test passes **42/42** (twice, identical).

| P | Change | Files |
|---|---|---|
| P-1 | Registered initial T1 margins kept: mean 0.03, variance ±0.05, (d) 0.035, (e) 0.035, lag-1 0.03.<br>Registered caps kept: mean 0.05, variance ±0.10, correlation 0.05. (e) is under the correlation cap by interpretation.<br>**The lag-1 cap is removed; lag-1 is never widened.**<br>The widening schedule is labelled in code, in the saved results and in the `--plan` output as "pre-run calibration procedure (preflight P-1; NOT a registered criterion)".<br>A calibration shortfall stops the run before generation.<br>Saved results include the registered initial margins, the caps and the per-round history | `experiments/stage4/e2e/stats.py` (`T1_CAPS`, `T1_PROCEDURE`, `t1_calibrate`); `e2e_run.py` (`plan`) |
| P-2 | Added the **descriptive** mean-over-joints extreme-frame fraction (`extreme_frac_meanjoint_{L,R}`), reported per SS condition as a paired difference with a 95% CI. **Gating still uses any-joint** (`extreme_frac`) | `metrics.py`; `e2e_run.py` (`analyse`) |
| P-3 | No code change. The bound-based tests were already implemented as approved | — |
| P-4 | New `t3_verdict`:<br>• per-side transmission, Δ and CI;<br>• **existence** (the registered either-side criterion) kept separate from **bilateral**;<br>• a side-naming verdict ("R only" / "L only" / "both" / "neither");<br>• monotonicity per side, with the verdict judged on the transmitting side(s);<br>• orientation pass counts per side | `stats.py`; `e2e_run.py` (`analyse`) |
| P-5 | No change (as specified) | — |
| P-6 | No change | — |
| P-7 | No change | — |
| P-8 | No change (seeds as listed) | — |
| P-9 | **Wording only:** run-order steps 5–6 now read "T5-A fail ⇒ stop", restating the registered T5-A rule and the §15.2 stop gate. Documented in the rev. 4.0 change log; no revision bump. The code already stopped on any T5-A fail | `research/STAGE4_REPORT.md` (§15.3.1 table, change log); `research/stage4/E2_EXECUTION_CHECKLIST.md`; the preflight report already had it |
| P-10 | Added a **descriptive** block `gate_at_n_star_descriptive`: T3/T4 paired Δ at n* for the two gate conditions. The registered T3/T4 verdicts still use n = 8 | `e2e_run.py` (`analyse`) |
| P-11 | New `efficiency`: Δ per KL nat for arm12 and r60 and their ratio, each with a 95% bootstrap CI. KL = exact per-frame KL × L_j, averaged over the resampled clips. Labelled descriptive | `stats.py`; `e2e_run.py` |
| P-12 | No change | — |
| P-13 | `S3_caveat` attached to every T5-A output: "descriptive only; may be infinite (App. G.6.1); CI unstable if T4-e fails" | `stats.py` |
| P-14 | No change | — |

## Self-test

- **18 new checks.** These cover:
  - registered margins and caps unchanged;
  - lag-1 never widened, with a lag-1 null shortfall leading to a stop;
  - the mean widening once to 0.035, and stopping at the 0.05 cap;
  - the P-2 field;
  - P-4 side naming, bilateral vs existence, monotonicity and per-side counts;
  - the P-11 ratio and CI;
  - the P-13 caveat;
  - the orchestrator's analysis stage run end to end on synthetic records, carrying all the new fields;
  - the plan labelling.
- **Self-test fix:** torch is now seeded, so the self-test is deterministic. The empirical covariance sanity check reads 0.044 against its 0.05 self-test tolerance on every run. This tolerance belongs to the self-test only; it is not a registered threshold.
- **Command:** `.venv-infer\Scripts\python.exe -E -s experiments\stage4\e2e\selftest.py` gives **42/42 PASS**.
