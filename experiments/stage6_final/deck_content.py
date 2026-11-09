"""Final presentation (16:9, speaker notes on every slide). Numbers come from final_data.Data (measured JSON only).

  python -E -s experiments/stage6_final/deck_content.py
writes research/final/SignSparK_RL_presentation.pptx, .html and .pdf (Edge headless).
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deckgen as DG  # noqa: E402
from final_data import NA, ROOT, Data, est, f  # noqa: E402
from report_content import compute_rows, consolidated, fg_summary, fg_text, unavailable_rows  # noqa: E402

OUT = ROOT / "research" / "final"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
LABEL = "Released-checkpoint result, not a paper reproduction · motion statistics only"


def build():
    D = Data()
    p4, p5 = D.pool(), D.pool("pooled_secondary_all5")
    runs = D.runs()
    het = p4["heterogeneity"]
    mult = 1 / p4["magnitude"]["ratio_to_0.05"]
    S = []

    def fig(name, title, bullets, notes, alt=None):
        p = D.fig(name)
        if p:
            S.append({"kind": "figure", "title": title, "image": p, "image_alt": alt or title, "bullets": bullets, "notes": notes})
        else:
            S.append({"kind": "content", "title": title, "bullets": [f"Figure {name} unavailable: {D.figs['unavailable'].get(name, 'not produced')}"]
                      + bullets, "notes": notes + " The figure for this slide was not produced, so it is marked unavailable."})

    S.append({"kind": "title", "title": "Noise-space RL for arm–hand coordination in a frozen SignSparK",
              "subtitle": ["Final results: ACMS multi-seed replication and the FG-1 feasibility gate", "How2Sign (ASL) · 7 November 2026", LABEL],
              "notes": "This talk closes the SignSparK RL project. Everything I show is a released-checkpoint result on How2Sign, not a "
                       "reproduction of the paper, and every metric is a motion statistic. I make no claim about naturalness, "
                       "intelligibility, meaning or ASL quality."})
    S.append({"kind": "stats", "title": "Bottom line",
              "stats": [(f(p4["pooled_t"]["mean"], 4), "pooled Δ right arm–hand coordination, 4 new seeds"),
                        (p4["category"], "registered replication category"),
                        (f"≈1/{mult:.0f}", "of the registered 0.05 relevance threshold"),
                        ("all pass", "pre-registered preservation checks, 5 runs")],
              "bullets": [f"Pooled 95% CI across runs {est(p4['pooled_t'])} includes zero; I² = {het['I2']:.2f}.",
                          fg_summary(D),
                          "Conclusion: the amortised RL policy gives no practically relevant gain; per-clip control is feasible."],
              "notes": f"The headline. Across four new training seeds the ACMS effect averages {f(p4['pooled_t']['mean'], 4)} on right "
                       f"arm–hand coordination, with a run-level confidence interval that includes zero and very high heterogeneity, "
                       f"so the registered category is {p4['category']}. Even the best run is far below the 0.05 threshold we "
                       f"registered as the smallest relevant effect. Nothing broke: all preservation checks pass. The FG-1 gate "
                       f"results are summarised on the second bullet and detailed later."})
    S.append({"kind": "content", "title": "The problem: generated hands ignore the arms",
              "bullets": ["SignSparK samples body and each hand from independent noise in gloss-free text-to-pose generation.",
                          "Arm–hand coordination in generated How2Sign samples ≈ 0.02 vs ≈ 0.45 in references (chance level).",
                          "Goal: reduce this deficit with RL on top of the frozen released checkpoints, without changing per-stream motion.",
                          "Out of scope (user decisions): fine-tuning, test split, human evaluation, perceptual or semantic claims."],
              "notes": "Stage 3 established the deficit: coordination between arm speed and hand articulation in generated samples is at "
                       "the level expected from independent sampling, while references are around 0.45. The structural cause is that "
                       "the hand generator never sees the body noise. We were asked to try RL without touching the weights."})
    S.append({"kind": "content", "title": "Formulation: a contextual bandit over the initial noise",
              "bullets": ["Action: initial noise of the right-hand stream; one decode per episode; terminal reward.",
                          "Per-frame MDPs rejected: the 10-step rectified-flow generator is non-autoregressive.",
                          "Reward: −|coord_ah^R − 0.4514| (frozen train-reference target, metric R v1.1).",
                          "Constraints (articulation, jerk, extremes, activity) by dual ascent; λ stayed 0 in all runs.",
                          "Primary statistic: paired clip-mean Δ trained − uncoupled on dev-256 × 4 shared noises."],
              "notes": "Because the generator decodes the whole sequence at once, the right abstraction is a contextual bandit: the "
                       "context is the text and the generated body, the action is the hand noise, the reward is terminal. The reward "
                       "targets the train-reference coordination level rather than maximising it, so it cannot be gamed by "
                       "over-coupling. Constraints never became active."})
    S.append({"kind": "content", "title": "ACMS: arm-conditioned temporal mean shift",
              "bullets": ["ε_R = ξ + μ_φ(ŝ),  μ_φ = β · U · tanh(W ∗ ŝ + c); ŝ = generated arm speed profile.",
                          "Rank 4, 17-tap kernel, 433 parameters; KL = ½‖μ‖² per frame < 1 nat/frame by construction.",
                          "REINFORCE with leave-one-out baseline (G = 4), Adam 0.01, clip 1.0, 125 updates / 500 episodes.",
                          "Stage 5 run 7000: Δ = +0.0022 [+0.0014, +0.0031], pre-registered verdict positive but negligible."],
              "notes": "ACMS shifts the mean of the hand noise in time with the arm's speed profile. It is tiny, 433 parameters, and the "
                       "KL to the base sampler is exactly half the squared shift, so it is bounded. The original run gave a positive "
                       "but negligible effect, which is why replication across seeds was the next registered step."})
    S.append({"kind": "content", "title": "Protocol and safeguards",
              "bullets": ["Seeds 7001–7004 vary init, clip sampling (5000 + d) and training noise (50M + d·1M) independently; eval noise shared.",
                          "Runs = unit of inference: per-run CIs, t-interval across runs, clip and hierarchical bootstrap, Q / I² / τ².",
                          "Category rule fixed before running; update 125 primary; no best-run or best-checkpoint selection.",
                          "Checkpoint SHA-256 before/after; Stage 4/5 artifacts hash-snapshotted; TRAIN/DEV only, test split never opened.",
                          "Metrics, validity rules, targets, rewards and thresholds unchanged."],
              "notes": "The design was registered before any run. Each new seed changes three independent sources of randomness. The "
                       "unit of inference is the training run, so the main interval is a t-interval over four runs; clip bootstrap "
                       "intervals are shown separately because they only capture evaluation sampling."})
    S.append({"kind": "section", "title": "1 · ACMS multi-seed replication", "subtitle": ["Four new seeds, original configuration, frozen SignSparK"],
              "notes": "First block: the replication."})
    tab = [["Run", "Δ coord_ah^R [95% clip CI]", "Verdict", "KL mean", "Train s"]]
    for r in runs:
        tab.append([str(r["seed"]), est(r["primary"]), r["verdict_single_run"], f(r["kl_per_frame"]["trained"]["mean"], 4, False),
                    f"{r['train']['seconds']:.0f}"])
    tab.append(["Pooled 4 new (t)", est(p4["pooled_t"]), p4["category"], "", ""])
    tab.append(["Pooled all 5 (t)", est(p5["pooled_t"]), p5["category"], "", ""])
    S.append({"kind": "table", "title": "Per-run results (dev-256 × 4, space R)", "table": tab, "table_sz": 13,
              "bullets": ["All runs completed; weights unchanged; 0 undefined statistics; uncoupled samples bitwise identical across runs."],
              "notes": "Per run: three of the four new seeds are positive with clip intervals excluding zero; seed 7001 is slightly "
                       "negative. Pooled across runs the interval includes zero. The uncoupled baseline samples are bitwise identical "
                       "in every run, so the differences are due to training only."})
    fig("f04_coordination_multiseed.png", "Effect per run and pooled",
        [f"Pooled 4 new {est(p4['pooled_t'])}", f"Clip bootstrap {est(p4['eval_sampling_clip_bootstrap'])} (eval sampling only)",
         f"I² = {het['I2']:.2f}; Q = {het['Q']:.0f} (df {het['df']})", "Dominance and L–R: no consistent direction"],
        "The forest plot. Each run has a tight clip interval, but runs disagree with each other far more than their intervals "
        "allow, which is what I² near one says. The pooled t-interval is wide and crosses zero. Dominance and left–right "
        "coordination move in no consistent direction.")
    fig("f05_preservation_multiseed.png", "Preservation: nothing else changed",
        ["Articulation, jerk, extremes, activity, KL: all pass in all runs", "Ratios within 0.5% of 1",
         f"Max KL {max(r['kl_per_frame']['trained']['max'] for r in runs):.4f} nats/frame"],
        "Every pre-registered preservation check passes in every run, and the ratios are within half a percent of one. ACMS is "
        "a very small perturbation of the base sampler, which fits the very small effect.")
    fig("f01_training_return.png", "Training dynamics",
        ["Return is clip-dependent and noisy", "Training-time controlled − twin effect small in all runs", "No constraint ever active"],
        "Training curves for all five runs. The return is dominated by which clips are sampled. The controlled-minus-twin effect "
        "during training is in the thousandths throughout, matching the evaluation.")
    if D.optc_available():
        fig("f02_heldout_vs_progress.png", "OPT-C: held-out effect across checkpoints (monitoring)",
            ["Updates 0, 25, 50, 75, 100, 125 evaluated (R only)", "Update 125 stays primary; nothing selected"],
            "Intermediate checkpoints were evaluated as monitoring only. They show how the held-out effect develops; they were "
            "never used to choose a checkpoint.")
    else:
        S.append({"kind": "content", "title": "OPT-C: intermediate checkpoints", "bullets": ["OPT-C evaluation unavailable (not completed)."],
                  "notes": "The optional checkpoint-progress evaluation did not complete, so it is reported as unavailable."})
    fig("f09_seed_stability.png", "Stability across seeds",
        ["Effect, dominance, L–R, activity, KL and β per run", "Spread between seeds dominates evaluation noise"],
        "Controller statistics per run: seeds that learned larger shifts (higher KL) show larger effects, but all stay tiny.")

    S.append({"kind": "section", "title": "2 · FG-1 feasibility gate", "subtitle": ["Per-clip, like-for-like, fresh noise"],
              "notes": "Second block: can any controller family move coordination on clips it was fitted to, under fresh noise?"})
    S.append({"kind": "content", "title": "FG-1 design",
              "bullets": ["16 TRAIN clips (8 short, 8 long), disjoint from ACMS training clips; 16 fit + 16 held-out noises per clip.",
                          "V0 uncoupled · V1 learned M-C coupling · V2 per-clip ACMS · V3 bilateral SC-MC (new direction).",
                          "Pathwise gradients through the frozen unrolled sampler; Adam 0.05, 30 iterations.",
                          "Positive: CI lower > 0, point ≥ 0.05, preservation passes · Negative: CI upper < 0.05 · else inconclusive.",
                          "Operational decisions D1–D10 documented before running (e.g. V3 cap 120 min); protocol unchanged."],
              "notes": "FG-1 removes amortisation: each clip gets its own parameters, fitted on 16 noises and tested on 16 different ones. "
                       "This is an upper bound on what a per-clip controller of each family can do. All variants share clips and "
                       "noises, so this is the only like-for-like comparison in the project."})
    paras, rows = fg_text(D)
    S.append({"kind": "table", "title": "FG-1 results (right arm–hand, space R)", "table": rows, "table_sz": 11,
              "bullets": [fg_summary(D)],
              "notes": "The FG-1 table. " + " ".join(p.replace("**", "") for p in paras)})
    fig("f08_fg1_comparison.png", "FG-1: in-sample vs held-out", ["Grey: in-sample (fit noises)", "Coloured: held-out fresh noise",
                                                                 "Dashed: registered 0.05"],
        "In-sample against held-out for each variant. The gap between grey and coloured is how much of the fitted gain is specific "
        "to the noise draws used for fitting.")
    fig("f10_generalisation.png", "Generalisation across studies",
        ["E2c (ii): in-sample 0.74 vs held-out ≈ uncoupled", "ACMS: own TRAIN clips vs dev", "FG-1: in-sample vs fresh noise"],
        "Three views of the same question: does what is learned transfer to new noise? For per-clip M-C it clearly did not.")
    fig("f08b_cross_study_kl.png", "Gain vs KL across studies (descriptive)",
        ["Different clips, noises, budgets", "Only FG-1 is like-for-like"],
        "A descriptive overview of held-out gain against KL budget for every controller we ran. It is not a controlled comparison.")
    fig("f12_ablations.png", "Ablations actually run",
        ["Trained − initial vs initial − uncoupled (ACMS)", "State shuffle: ŝ from another noise draw (FG-1 V2/V3)"],
        "Only these ablations were run. Training versus random initialisation, and whether the conditioning signal matters.")
    fig("f11_compute.png", "Compute (single RTX A4000 16 GB)",
        ["ACMS training ≈ 5 min, evaluation ≈ 26–28 min per run", "No GPU rental; jobs run sequentially"],
        "Everything ran on one 16 GB card. ACMS training is cheap; evaluation dominates because of the full dev-256 × 4 decode.")
    S.append({"kind": "table", "title": "Consolidated results", "table": consolidated(D), "table_sz": 11,
              "notes": "All executed experiments in one table, from the Stage 4 coupling studies to the final gate."})
    S.append({"kind": "table", "title": "Metrics not reported, and why", "table": unavailable_rows(), "table_sz": 11,
              "bullets": ["Earlier slide deck not in workspace: deck-to-deck coverage verification unavailable."],
              "notes": "What we deliberately do not report. Pose-error metrics favour collapse in this regime, back-translation is "
                       "hackable, and success rate, regret and algorithm comparisons have no defined experiment here. The earlier "
                       "deck was not available, so coverage was checked against the written coverage plan instead."})
    S.append({"kind": "content", "title": "Limitations",
              "bullets": ["Four new runs: wide across-run interval; seed-sensitive reflects heterogeneity and low power.",
                          "R coordination is validated automatically only; no perceptual validity.",
                          "J includes SMPL-X skinning leakage (~1–2%); descriptive only.",
                          "FG-1: 16 TRAIN clips, one fit each, pathwise gradients; controllability, not an RL policy.",
                          "V2 misses the articulation bound narrowly (1.102 vs 1.10); applied as registered.",
                          "Checkpoint pretraining split usage undocumented (absolute levels only)."],
              "notes": "The main limits. Power is low with four runs, but the effect is also far below the threshold, so more seeds "
                       "would not change the practical conclusion."})
    S.append({"kind": "section", "title": "Conclusion",
              "subtitle": [f"ACMS gain {f(p4['pooled_t']['mean'], 4)} pooled, {p4['category']}, ≈1/{mult:.0f} of the threshold",
                           fg_summary(D),
                           "Per-clip control works on fresh noise; one shared RL policy does not. Project closed on this evidence."],
              "notes": "To conclude: the one positive training result replicates in direction but not robustly, and its size is "
                       "negligible. The gate shows that a small state-conditioned controller fitted to one clip can raise coordination "
                       "by more than the threshold on fresh noise, with preservation intact for the bilateral variant, and the "
                       "state-shuffle ablation shows it depends on the arm signal. So the frozen sampler is controllable; what failed "
                       "is learning one controller that works across clips. That gate used gradients, not RL, so it does not tell us "
                       "whether amortisation or the estimator is to blame. Fine-tuning or architectural coupling would be the next "
                       "questions, outside this project's scope."})
    return S


def main():
    S = build()
    OUT.mkdir(parents=True, exist_ok=True)
    pp = OUT / "SignSparK_RL_presentation.pptx"
    DG.write_pptx(S, pp, "SignSparK RL final presentation")
    print("check", DG.check_pptx(pp))
    hp = OUT / "SignSparK_RL_presentation.html"
    DG.write_html(S, hp, "SignSparK RL final presentation")
    pdf = OUT / "SignSparK_RL_presentation.pdf"
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", hp.as_uri()],
                   capture_output=True, timeout=180)
    print("slides", len(S), "pdf", pdf.exists() and pdf.stat().st_size)


if __name__ == "__main__":
    main()
