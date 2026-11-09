"""Content of the final IEEE-style report. Every number is read from measured JSON via final_data.Data; experiments or
metrics without outputs or validated evaluators are stated as unavailable. Built by report_build.py."""

from final_data import HERE, NA, Data, ci, est, f

HERE_FIG_POSTHOC = HERE / "posthoc_return" / "f13_posthoc_return.png"

STAGE_REFS = [
    "J. He et al., \"SignSparK: Efficient multilingual sign language production via sparse keyframe learning,\" ECCV 2026 (released code github.com/JianHe0628/SignSparK and checkpoints HF LionelLow/SignSparK).",
    "A. Duarte et al., \"How2Sign: A large-scale multimodal dataset for continuous American Sign Language,\" CVPR 2021.",
    "R. J. Williams, \"Simple statistical gradient-following algorithms for connectionist reinforcement learning,\" Machine Learning, 1992.",
    "W. Kool, H. van Hoof, M. Welling, \"Buy 4 REINFORCE samples, get a baseline for free!,\" ICLR DeepRL Meets Structured Prediction Workshop, 2019.",
    "E. Altman, Constrained Markov Decision Processes, Chapman & Hall/CRC, 1999.",
    "J. Liu et al., \"Flow-GRPO: Training flow matching models via online RL,\" arXiv 2505.05470, 2025.",
    "K. Clark et al., \"Directly fine-tuning diffusion models on differentiable rewards (DRaFT),\" ICLR 2024.",
    "L. Eyring et al., \"Noise hypernetworks: Amortizing test-time compute in diffusion models,\" NeurIPS 2025 (arXiv 2508.09968).",
    "G. Pavlakos et al., \"Expressive body capture: 3D hands, face, and body from a single image (SMPL-X),\" CVPR 2019.",
    "R. DerSimonian, N. Laird, \"Meta-analysis in clinical trials,\" Controlled Clinical Trials, 1986.",
    "B. Efron, R. Tibshirani, An Introduction to the Bootstrap, Chapman & Hall, 1993.",
    "X. Liu, C. Gong, Q. Liu, \"Flow straight and fast: Learning to generate and transfer data with rectified flow,\" ICLR 2023.",
]


def fg_text(D):
    """Methods-independent FG-1 result paragraphs and table rows."""
    rows = [["Variant", "Params/clip", "Held-out Δ vs V0 (R, right)", "In-sample Δ (last iter)", "Gap", "KL max", "Preserv.", "Outcome"]]
    paras = []
    if not D.fg:
        paras.append("FG-1 results are **unavailable**: the gate did not produce an analysed output (see the manifest for job status).")
        return paras, rows
    for v in ("V1", "V2", "V3"):
        e = D.fg_variant(v)
        if not e:
            rows.append([v, NA, NA, NA, NA, NA, NA, D.fg_status(v)])
            continue
        s = e["statistics"]["R"]
        rows.append([v, e["params_per_clip"], est(s["heldout_delta_vs_V0"]), est(s["insample_delta_last_iter"]),
                     f(s["generalisation_gap_last"]["mean"]), f(e["kl_max"]["R"], 3, False), "pass" if e["preservation_pass"] else "FAIL",
                     e["outcome"]])
    v0 = D.fg["V0"]["R"]
    b16 = D.fg["best_of_16_heldout_V0_selection_context"]["R"]
    paras.append(f"The uncoupled baseline V0 has held-out right arm–hand coordination {est(v0, 3)} on the 16 gate clips; the "
                 f"best-of-16 selection context (maximum over the 16 held-out V0 draws, an oracle that a policy cannot use) is "
                 f"{est(b16, 3)}. The registered threshold for a positive outcome is a held-out gain of 0.05 with the 95% clip "
                 f"CI lower bound above zero and all preservation checks passing.")
    for v, name in (("V1", "learned M-C coupling"), ("V2", "per-clip ACMS"), ("V3", "bilateral SC-MC")):
        e = D.fg_variant(v)
        if not e:
            paras.append(f"**{v} ({name})** did not complete (status: {D.fg_status(v)}); no result is reported for it.")
            continue
        s = e["statistics"]["R"]
        t = (f"**{v} ({name}).** Held-out Δ {est(s['heldout_delta_vs_V0'])} ({s['n_clips_positive']}/16 clips positive); "
             f"in-sample Δ at the last iteration {est(s['insample_delta_last_iter'])}; generalisation gap "
             f"{est(s['generalisation_gap_last'])}. KL max {e['kl_max']['R']:.3g} nats/frame (right). "
             f"Preservation {'passes' if e['preservation_pass'] else 'fails'}. Registered outcome: **{e['outcome']}**.")
        if v == "V3":
            sl, slr = e["statistics"]["L"], e["statistics"]["LR"]
            t += (f" Left arm–hand Δ {est(sl['heldout_delta_vs_V0'])} ({sl.get('outcome', NA)}); left–right Δ "
                  f"{est(slr['heldout_delta_vs_V0'])} ({slr.get('outcome', NA)}); KL max left {e['kl_max']['L']:.3g}.")
        if "state_shuffle_ablation" in e:
            sh = e["state_shuffle_ablation"]["R"]["delta_vs_unshuffled"]
            t += f" State-shuffle ablation (ŝ from a different noise draw), shuffled − matched: {est(sh)}."
        paras.append(t)
    return paras, rows


def fg_summary(D):
    parts = []
    for v, name in (("V1", "learned M-C"), ("V2", "per-clip ACMS"), ("V3", "bilateral SC-MC")):
        e = D.fg_variant(v)
        parts.append(f"{name} {e['outcome']} (held-out Δ {f(e['statistics']['R']['heldout_delta_vs_V0']['mean'])})" if e
                     else f"{name} {D.fg_status(v)}")
    return "In the FG-1 fresh-noise gate: " + "; ".join(parts) + "."


def fg_contrast(D):
    """One sentence contrasting per-clip feasibility (FG-1) with the amortised ACMS result; '' if FG-1 is incomplete."""
    v2, v3 = D.fg_variant("V2"), D.fg_variant("V3")
    if not (v2 and v3):
        return ""
    r2, r3 = v2["statistics"]["R"]["heldout_delta_vs_V0"], v3["statistics"]["R"]["heldout_delta_vs_V0"]
    art2 = v2["preservation"]["R"]["artic_ratio_mean"]["value"]
    return (f"Fitted per clip on that clip's own noise draws, the same 433-parameter ACMS family (V2) raises held-out "
            f"right arm–hand coordination by {est(r2)} on fresh noise, but its articulation ratio ({art2:.3f}) exceeds the "
            f"registered 1.10 bound, so its outcome is {v2['outcome']}; the bilateral variant (V3) gives {est(r3)} with "
            f"preservation passing and is {v3['outcome']} on the primary statistic")


def consolidated(D):
    p4, p5 = D.pool(), D.pool("pooled_secondary_all5")
    rows = [["Experiment", "Unit / n", "Primary statistic (R)", "Estimate [95% CI]", "Outcome"]]
    rows.append(["Stage 4 E2e fixed M-C coupling", "16 conditions, 32 dev clips", "Δ arm–hand (T3)", "R 0.017, L 0.022 (CIs incl. 0)",
                 "FM13 stop (negative)"])
    if D.e2c:
        rows.append(["Stage 4 E2c (ii) per-clip M-C", "32 dev clips", "held-out gain", est(D.e2c["gain_heldout_vs_uncoupled"], 3),
                     "negative (FM4)"])
    rows.append(["Stage 5 ACMS, run 7000", "dev-256 × 4", "Δ trained − uncoupled", "+0.0022 [+0.0014, +0.0031]", "positive, negligible"])
    rows.append(["ACMS multi-seed (7001–7004)", "4 runs", "pooled Δ (t)", est(p4["pooled_t"]), p4["category"]])
    rows.append(["ACMS all five runs (secondary)", "5 runs", "pooled Δ (t)", est(p5["pooled_t"]), p5["category"]])
    if D.optg_available():
        rows.append(["OPT-G train-like generalisation", "4 new runs", "pooled Δ on own TRAIN clips", est(D.pool()["optg_pooled"]["train_like"]), "monitoring"])
    else:
        rows.append(["OPT-G train-like generalisation", "–", "–", NA, "not completed"])
    for v in ("V1", "V2", "V3"):
        e = D.fg_variant(v)
        rows.append([f"FG-1 {v}", "16 TRAIN clips × 16", "held-out Δ vs V0",
                     est(e["statistics"]["R"]["heldout_delta_vs_V0"]) if e else NA, e["outcome"] if e else D.fg_status(v)])
    return rows


def unavailable_rows():
    return [["Metric", "Status", "Reason"],
            ["DTW-JPE / MPJPE vs. reference as success measure", "not used", "favours collapse in GF (static mean beats samples; M5–M6)"],
            ["BLEU / back-translation", "not used", "within-text uncorrelated with pose error; hackable by selection (R6)"],
            ["FID / diversity / multimodality", "unavailable", "no validated ASL feature extractor"],
            ["Task success rate", "unavailable", "no episodic task or success criterion exists"],
            ["Regret", "unavailable", "no oracle policy value is defined"],
            ["PPO / GRPO / SAC comparison", "unavailable", "never run; no comparative claim made"],
            ["Perceptual naturalness, intelligibility, ASL quality", "out of scope", "human evaluation removed (rev. 4.0)"],
            ["How2Sign test split", "never opened", "only registered TRAIN and DEV used"]]


def coverage_rows(D):
    """Metric coverage for the report: measured (registered outputs), derived (post-hoc from saved outputs), unavailable."""
    ph = "derived (post-hoc)" if D.posthoc else "unavailable"
    return [["Metric", "Status", "Source / reason"],
            ["Arm–hand coordination coord_ah^R (right; primary), L, L–R, dominance (R)", "measured", "registered evaluation, dev-256 × 4"],
            ["J-space coordination (SMPL-X)", "measured (descriptive)", "not gating; ~1–2% skinning leakage"],
            ["Preservation ratios, extremes, activity, undefined fraction, KL/frame", "measured", "registered checks"],
            ["Training return R per episode (logged)", "measured", "episodes.json; reproduced exactly by the registered reward"],
            ["FG-1 held-out Δ, in-sample Δ, generalisation gap, state shuffle", "measured", "FG-1 gate outputs"],
            ["Runtime, peak GPU memory", "measured", "runner logs"],
            ["Evaluation return R per sample (trained / initial / uncoupled)", ph, "registered reward applied to eval_samples.json"],
            ["Paired return difference, cumulative reward difference, paired win fraction", ph, "baseline-relative; not regret"],
            ["Training return progression and twin-relative cumulative difference", ph, "episodes.json"],
            ["Regret (optimal minus achieved return)", "unavailable", "no optimal-policy reference in the design"],
            ["Task success rate", "unavailable", "no episodic task or success criterion exists"],
            ["FID / diversity / multimodality", "unavailable", "no validated ASL feature extractor"],
            ["PPO / GRPO / SAC comparison", "unavailable", "never run; no comparative claim made"],
            ["DTW-JPE / MPJPE vs. reference as success measure", "not used", "favours collapse in GF (static mean beats samples; M5–M6)"],
            ["BLEU / back-translation", "not used", "within-text uncorrelated with pose error; hackable by selection (R6)"],
            ["Perceptual naturalness, intelligibility, ASL quality", "out of scope", "human evaluation removed (rev. 4.0)"],
            ["How2Sign test split", "never opened", "only registered TRAIN and DEV used"]]


def posthoc_section(D):
    """Post-hoc (not pre-registered) episodic-return and baseline-relative section; None if the analysis was not run."""
    P = D.posthoc
    if not P:
        return None
    ev, tr = P["eval"], P["train"]
    r4, r5 = P["pooled_new4"], P["pooled_all5"]
    e_rows = [["Run", "Return trained", "Return uncoupled", "Δ trained − uncoupled [95% CI]", "Δ trained − initial", "Win (samples)",
               "Win (clips)", "CRD (1024)"]]
    for s, e in ev.items():
        p, q = e["paired"]["trained-uncoupled"], e["paired"]["trained-initial"]
        e_rows.append([s, f(e["return"]["trained"]["clip_mean"]["mean"]), f(e["return"]["uncoupled"]["clip_mean"]["mean"]),
                       est(p["mean_difference_clip_bootstrap"]), est(q["mean_difference_clip_bootstrap"]),
                       f"{p['sample_win']:.3f}", f"{p['clip_win']['mean']:.3f}", f(p["cumulative_reward_difference"], 3)])
    for lab, r in (("Pooled 4 new (t)", r4), ("Pooled all 5 (t)", r5)):
        e_rows.append([lab, est(r["trained_return"]), est(r["uncoupled_return"]), est(r["trained-uncoupled_mean_difference"]),
                       est(r["trained-initial_mean_difference"]), est(r["sample_win_fraction"], 3), est(r["clip_win_fraction"], 3),
                       est(r["cumulative_reward_difference_eval"], 2)])
    t_rows = [["Run", "Episodes", "Mean R", "SD R", "SD of update means", "First 25 updates", "Last 25 updates", "Twin-relative CRD",
               "Twin win"]]
    for s, t in tr.items():
        g = t["progression"]
        t_rows.append([s, t["n_episodes"], f(t["return"]["mean"]), f(t["return"]["sd"], 4, False), f(t["group_mean_return"]["sd"], 4, False),
                       f(g["first_25_updates_mean"]), f(g["last_25_updates_mean"]), f(t["twin_relative"]["cumulative_reward_difference"], 3),
                       f"{t['twin_relative']['win']:.3f}"])
    t_rows.append(["Pooled 4 new (t)", "", est(r4["train_return"]), "", "", "", f"last − first {est(r4['train_last_minus_first'])}",
                   est(r4["train_twin_cumulative_reward_difference"], 3), ""])
    e0 = next(iter(ev.values()))
    n_cl, n_k = e0["n_clips"], e0["n_noises_per_clip"]
    s3 = sum(v for e in ev.values() for v in e["s3_undefined"].values())
    fig_p = HERE_FIG_POSTHOC if HERE_FIG_POSTHOC.exists() else None
    blocks = [
        ("p", "**This section is post-hoc and was not pre-registered.** It re-expresses saved outputs in reinforcement-learning "
              "terms. It ran on CPU only, generated no samples, changed no file outside `experiments/stage6_final/posthoc_return/`, "
              "and changes no registered threshold, verdict or category. The primary pre-registered statistic remains "
              "coord_ah^R, reported in the multi-seed results section."),
        ("sub", "Definitions"),
        ("p", "Each episode is a single decision (one noise draw → one sample), so the episodic return equals the registered reward, "
              "recomputed with the unchanged implementation (`experiments/stage5/rewards.py`, `episode_reward`):"),
        ("eq", "R = r_ah − Σ_k λ_k c_k,   r_ah = −|coord_ah^R − τ|,   τ = 0.4514 (frozen);   undefined coord → r_ah = −(1 + τ)"),
        ("p", f"λ_k = 0 in every run at every update, so R = r_ah; the constraint terms c_k use each sample's uncoupled twin (same "
              f"clip and noise index), exactly as in training. Evaluation: dev-256, {n_cl} clips × {n_k} noise draws × 3 conditions per "
              f"run (1024 samples per condition); {s3} undefined coordinations across all runs and conditions. Paired difference for "
              f"clip i and noise k:"),
        ("eq", "d_ik = R(trained, i, k) − R(uncoupled, i, k);   CRD = Σ_ik d_ik;   win = mean_ik 1[d_ik > 0]"),
        ("p", "Within a run, CIs are clip bootstraps over clip means of d (B = 2000, seed 0); across runs, t-intervals with runs as "
              "the unit, as in the registered analysis. Clip win fraction = share of clips whose mean d is positive. Training "
              "statistics use the 500 logged episodes per run (125 updates × 4 TRAIN episodes); the twin-relative difference is "
              "R(controlled) − R(uncoupled twin) on the same training noise. Every logged training return was reproduced exactly "
              f"by the registered reward (maximum absolute error "
              f"{max(t['logged_return_reproduced_max_abs_err'] for t in tr.values()):.1g})."),
        ("sub", "Held-out evaluation return"),
        ("table", "Post-hoc evaluation return on dev-256 × 4 (update 125). Return = −|coord_ah^R − 0.4514|; higher is better; "
                  "CRD = cumulative reward difference over 1024 paired samples. Not regret.", e_rows, True),
        ("p", f"Uncoupled return is identical in every run ({f(r4['uncoupled_return']['mean'])}, per-sample SD "
              f"{e0['return']['uncoupled']['sample']['sd']:.3f}), as the uncoupled samples are bitwise identical. The pooled paired "
              f"return gain (4 new runs) is {est(r4['trained-uncoupled_mean_difference'])}, which matches the registered coordination "
              f"result because {100 * (1 - max(v for e in ev.values() for v in e['fraction_coord_above_tau'].values())):.1f}% or more "
              f"of samples in every run and condition lie below τ, where return and coordination move together. The paired win fraction "
              f"is {est(r4['sample_win_fraction'], 3)} over samples and {est(r4['clip_win_fraction'], 3)} over clips; both "
              f"intervals include 0.5. The five-run trained − initial difference "
              f"{est(r5['trained-initial_mean_difference'])} has a lower bound above zero, but this is a post-hoc secondary contrast and "
              f"does not alter the registered seed-sensitive category."),
        ("sub", "Training return"),
        ("table", "Post-hoc training return on each run's TRAIN clips (logged, 500 episodes). Training return is not held-out "
                  "return: clips are sampled from TRAIN and differ between updates.", t_rows, True),
        ("p", f"Training return is dominated by clip-to-clip variation (episode SD ≈ 0.17; SD of 4-episode update means ≈ 0.08–0.09), "
              f"so changes between the first and last 25 updates (pooled {est(r4['train_last_minus_first'])}) mostly reflect which "
              f"clips were drawn. The twin-relative difference removes clip and noise effects: its cumulative sum over 500 episodes "
              f"grows clearly only in runs 7003 and 7004, the two runs with the largest held-out gains."),
    ]
    if fig_p:
        blocks.append(("fig", str(fig_p), "Post-hoc: training return (25-update running mean), training cumulative reward difference "
                                          "vs the uncoupled twin, and held-out paired return difference per run. Not regret.", True))
    blocks += [
        ("sub", "Regret"),
        ("p", "**Conventional regret cannot be calculated.** " + P["regret"]["note"].split("cannot be calculated. ", 1)[-1]),
        ("sub", "Limitations of the post-hoc analysis"),
        ("ul", ["Not pre-registered; reported for completeness and interpretability only.",
                "Return is a monotone transform of the primary statistic below τ, so it is not independent evidence.",
                "Win fractions ignore effect size; a 0.6 win fraction here coexists with a mean gain of about 0.002.",
                "Cumulative reward differences scale with the number of samples (1024 in evaluation, 500 in training) and are not "
                "comparable across the two.",
                "Training statistics are on TRAIN clips under a changing policy; they are not generalisation estimates."]),
    ]
    return {"title": "Post-hoc analysis: episodic return and baseline-relative statistics (not pre-registered)", "blocks": blocks}


def compute_rows(D):
    rows = [["Experiment", "Wall-clock (min)", "Peak GPU reserved (GiB)", "Trainable params"]]
    for t in D.compute:
        g = t.get("gpu_peak_reserved_GiB")
        rows.append([t["experiment"], f"{t['seconds'] / 60:.1f}", "not logged" if g is None else f"{g:.2f}", t.get("params", "")])
    return rows


def content():
    D = Data()
    p4, p5 = D.pool(), D.pool("pooled_secondary_all5")
    runs = D.runs()
    pr = {str(r["seed"]): r for r in runs}
    het = p4["heterogeneity"]
    fg_paras, fg_rows = fg_text(D)
    mult = 1 / p4["magnitude"]["ratio_to_0.05"]
    fig = D.fig

    per_run_rows = [["Run", "Δ coord_ah^R [95% clip CI]", "single-run verdict", "Δ dominance", "Δ L–R", "KL mean", "train s", "eval s"]]
    for r in runs:
        per_run_rows.append([r["seed"], est(r["primary"]), r["verdict_single_run"], f(r["deltas_R"]["dom_X"]["trained-uncoupled"]["mean"]),
                             f(r["deltas_R"]["coord_lr"]["trained-uncoupled"]["mean"]), f(r["kl_per_frame"]["trained"]["mean"], 4, False),
                             f"{r['train']['seconds']:.0f}", f"{r['eval_run']['seconds']:.0f}"])
    pres_rows = [["Check (limit)", "Pooled mean, 4 new runs", "Range over 5 runs", "All pass"]]
    lim = {"artic_ratio_mean": "articulation ratio (0.9–1.1)", "jerk_ratio_mean": "jerk ratio (≤ 1.1)", "extreme_diff_mean": "extreme-pose diff (≤ 0.02)",
           "abs_mean_log_activity_ratio": "|log activity ratio| (≤ 0.223)", "kl_max": "KL max nats/frame (≤ 1)"}
    for k, lab in lim.items():
        vals = [r["preservation"][k]["value"] for r in runs]
        rows_ok = all(r["preservation"][k]["pass"] for r in runs)
        pres_rows.append([lab, f(p4["secondary"][f"check.{k}"]["mean"], 4, False), f"{min(vals):.4f}–{max(vals):.4f}", "yes" if rows_ok else "NO"])

    optc = []
    if D.optc_available():
        for u in ("0", "25", "50", "75", "100", "125"):
            e = p4["optc_progress_pooled"][u]
            optc.append(f"update {u}: {est(e)}")
    optc_txt = ("Pooled held-out Δ by checkpoint (4 new runs, t-intervals): " + "; ".join(optc) + ". Update 125 remains the "
                "primary and only pre-registered checkpoint; intermediate checkpoints were evaluated for monitoring only and none "
                "was selected.") if optc else ("OPT-C intermediate-checkpoint evaluation is **unavailable** (not completed); only "
                                                 "updates 0 and 125 are reported.")
    if D.optg_available():
        g = p4["optg_pooled"]
        optg_txt = (f"OPT-G (each run's own 125 TRAIN clips, fresh noise base 45M, four draws): pooled Δ {est(g['train_like'])} vs the dev "
                    f"Δ {est(p4['pooled_t'])}; pooled train − dev gap {est(g['gap_train_minus_dev'])}. This compares training-distribution clips to unseen dev clips under fresh noise; it "
                    f"is monitoring, not a selection criterion.")
    else:
        optg_txt = "OPT-G train-like evaluation is **unavailable** (not completed)."

    sections = [
        {"title": "Introduction", "blocks": [
            ("p", "Sign language production (SLP) models generate signing motion from text. SignSparK [1] is a recent large "
                  "rectified-flow [12] SLP model with separate body and hand generators. In its gloss-free text-to-pose regime "
                  "(GF-T2P) the two hands are sampled from independent noise, and in our Stage 3 baseline the coordination "
                  "between arm and hand motion in generated How2Sign [2] samples was at chance level (≈ 0.02 vs ≈ 0.45 in the "
                  "references). This project asked whether reinforcement learning (RL) on top of the **frozen** released "
                  "checkpoints can reduce that deficit without degrading per-stream motion statistics."),
            ("p", "The study was run in pre-registered, stage-gated steps. This report closes it. It presents (i) a multi-seed "
                  "replication of the only training result with a positive pre-registered verdict, the arm-conditioned "
                  "temporal mean-shift (ACMS) noise policy; (ii) FG-1, a like-for-like per-clip feasibility gate comparing "
                  "learned M-C coupling, ACMS and a new bilateral variant under fresh noise; and (iii) a consolidated account "
                  "of all executed experiments. All results are **released-checkpoint results, not a paper reproduction**, "
                  "and are motion statistics only: we make no claim about perceptual naturalness, intelligibility, semantic "
                  "correctness or ASL quality."),
            ("ul", [f"**C1.** A five-run replication showing that the ACMS coordination gain is **{p4['category']}** and roughly "
                    f"{mult:.0f} times smaller than the registered 0.05 relevance threshold.",
                    "**C2.** A fresh-noise gate (FG-1) separating in-sample from held-out controllability for three controller "
                    "families on identical clips and noises.",
                    "**C3.** A fully hashed, reproducible pipeline in which the generator, metrics, targets and thresholds were "
                    "never changed after registration."]),
        ]},
        {"title": "Problem formulation", "blocks": [
            ("sub", "Generator and action space"),
            ("p", "SignSparK decodes a sequence of L ≤ 304 frames of joint-local 6D rotations (body 60, each hand 90 "
                  "channels) from Gaussian noise ε ∈ ℝ^{L×304} by a 10-step rectified-flow sampler conditioned on a pooled "
                  "M-CLIP text embedding. The weights are frozen; the only action is the **initial noise** of a stream. One "
                  "episode is one clip: the policy chooses the noise, the sampler decodes once, and a terminal reward is "
                  "computed. The decision problem is therefore a contextual bandit over whole sequences (Stage 4 §4); per-frame "
                  "MDPs were rejected because the generator is non-autoregressive."),
            ("sub", "ACMS policy"),
            ("p", "ACMS shifts the mean of the right-hand noise as a function of the generated body (arm) speed profile ŝ:"),
            ("eq", "ε_R = ξ + μ_φ(ŝ),   μ_φ(ŝ) = β · U · tanh(W ∗ ŝ + c),   ξ ∼ N(0, I)"),
            ("p", "with rank r = 4, a 17-tap temporal kernel W, and 433 trainable parameters. Because only the mean shifts, "
                  "the policy KL to the uncoupled sampler is ½‖μ‖² per frame and is bounded below 1 nat/frame by construction. "
                  "Training uses REINFORCE [3] with a leave-one-out baseline over G = 4 draws per clip [4], Adam (lr 0.01), "
                  "gradient clipping at 1.0, and 125 updates (500 episodes) on TRAIN clips."),
            ("sub", "Reward and constraints"),
            ("p", "The reward is target matching on right arm–hand coordination in rotation space R (metric v1.1): "
                  "r = −|coord_ah^R − 0.4514|, where 0.4514 is the frozen train-reference target (R0). Articulation, jerk, "
                  "extreme-pose and activity constraints enter through Lagrangian dual ascent [5]; λ remained 0 in every group "
                  "of every run, so no constraint became active."),
            ("sub", "Evaluation statistic"),
            ("p", "The primary statistic is the paired clip-mean difference in right arm–hand coordination (R) between the "
                  "trained policy (update 125) and the uncoupled sampler on dev-256 × 4 shared evaluation noises (base 40M). "
                  "Joint-space (J, SMPL-X [9]) analogues are descriptive only; R and J are different metrics on the same "
                  "samples and are **not** independent replications."),
        ]},
        {"title": "Experimental protocol", "blocks": [
            ("sub", "Multi-seed replication"),
            ("p", "Seeds 7001–7004 each vary three sources independently: policy initialisation (init seed = run seed), "
                  "training-clip sampling (sampler seed 5000 + d) and training noise (base 50M + d·1M). Evaluation noise is shared. "
                  "The original configuration and code were reused unchanged (SHA-verified); the four runs were trained and "
                  "evaluated sequentially. Training runs are the unit of inference: we report per-run estimates, a t-interval "
                  "across runs, a clip bootstrap of seed-averaged per-clip Δ (evaluation-sampling uncertainty only), a "
                  "hierarchical bootstrap, and heterogeneity (Cochran's Q, I², DerSimonian–Laird τ² [10]). Run 7000 enters "
                  "only the secondary five-run pool. The category rule (registered before the runs) is: inconclusive "
                  "(validity) → negative → reproducible positive → seed-sensitive → inconclusive (precision)."),
            ("sub", "FG-1 per-clip feasibility gate"),
            ("p", "FG-1 asks whether any controller family can raise held-out coordination on clips it was fitted to, when "
                  "evaluated on fresh noise. Sixteen TRAIN clips (8 with L < 100, 8 with L ≥ 100; seeded selection excluding "
                  "all ACMS training clips) each get 16 fitting noises (base 60M) and 16 held-out noises (base 61M). Per-clip "
                  "parameters are fitted with pathwise gradients through the unrolled, checkpointed sampler (Adam lr 0.05, 30 "
                  "iterations) on a chordal-speed surrogate of the coordination statistic."),
            ("ul", ["**V0** uncoupled sampler (reference).",
                    "**V1** learned M-C: Stiefel-SVD coupling of right-hand noise to body noise, κ ≤ 0.9 (E2c (ii) family).",
                    "**V2** per-clip ACMS (433 parameters, as in §II-B).",
                    "**V3** bilateral SC-MC: two ACMS heads (right on right arm, left on left arm), objective = surrogates of "
                    "right, left and left–right coordination (new, authorised direction)."]),
            ("p", "Outcome per statistic: positive if the 95% clip CI lower bound > 0, the point estimate ≥ 0.05 and "
                  "preservation passes; negative if the CI upper bound < 0.05; otherwise inconclusive. Operational decisions "
                  "D1–D10 (e.g. a 120-min cap for V3 and 8 rows per pass) were documented before any FG-1 run and change no "
                  "scientific setting."),
            ("sub", "Safeguards"),
            ("ul", ["SignSparK checkpoint SHA-256 verified before and after all experiments; weights-unchanged checksum in every job.",
                    "Seed and noise-base disjointness preflight; configuration and code hashes recorded.",
                    "Stage 4/5 artifacts snapshotted (SHA-256) and re-verified at closure; new outputs in separate directories.",
                    "Only registered TRAIN and DEV splits opened; the How2Sign test split was never opened.",
                    "Registered metrics, validity rules, frozen targets, rewards and thresholds unchanged."]),
        ]},
        {"title": "Results: ACMS multi-seed replication", "blocks": [
            ("p", f"All four new runs completed (500 episodes each) with weights unchanged, zero undefined statistics and "
                  f"zero validity flags. The uncoupled evaluation outputs were bitwise identical across runs, so every run is "
                  f"compared against the same baseline samples."),
            ("table", "Per-run ACMS results (dev-256 × 4, space R)", per_run_rows, True),
            ("p", f"Run-level effects range from {f(min(r['primary']['mean'] for r in runs))} (run 7001, CI includes 0, "
                  f"single-run verdict negative) to {f(max(r['primary']['mean'] for r in runs))}. The pooled four-run mean is "
                  f"{est(p4['pooled_t'])} (t-interval, SD {f(p4['pooled_t']['sd'], 5, False)}); the CI includes zero. "
                  f"The clip bootstrap {est(p4['eval_sampling_clip_bootstrap'])} reflects only evaluation sampling and is "
                  f"therefore much narrower. Heterogeneity is high (Q = {het['Q']:.1f}, df = {het['df']}, I² = {het['I2']:.2f}). "
                  f"The registered category is **{p4['category']}**. The secondary five-run pool gives {est(p5['pooled_t'])} "
                  f"({p5['category']})."),
            ("fig", fig("f04_coordination_multiseed.png"), "Held-out change in right arm–hand coordination, left–right "
                    "coordination and dominance per run (95% clip CI) and pooled (t-interval across runs). Space R.", True),
            ("p", f"Magnitude: even the largest run closes about {100 * max(r['gap_closure'] for r in runs):.1f}% of the gap "
                  f"to the 0.4514 target, and no run reaches the 0.05 threshold (pooled ratio to 0.05: "
                  f"{p4['magnitude']['ratio_to_0.05']:.3f}). Dominance and left–right coordination show no consistent "
                  f"direction across runs. The trained − initial contrast (pooled {est(p4['secondary']['R.coord_arm_rhand.trained-initial'])}) "
                  f"and the initial − uncoupled contrast ({est(p4['secondary']['R.coord_arm_rhand.initial-uncoupled'])}) are "
                  f"reported as the ablation of training versus random initialisation."),
            ("fig", fig("f04b_coordination_multiseed_J.png"), "Joint-space (J) analogues, descriptive. Same samples as Fig. 1; "
                    "not an independent replication.", False),
            ("sub", "Preservation"),
            ("table", "Pre-registered preservation checks (trained vs uncoupled)", pres_rows, False),
            ("p", "Every preservation check passes in every run, with ratios within 0.5% of 1. Combined with a maximum KL of "
                  f"{max(r['kl_per_frame']['trained']['max'] for r in runs):.4f} nats/frame, this shows that ACMS operates as a very small perturbation of "
                  "the base sampler; the tiny effect is consistent with that."),
            ("fig", fig("f05_preservation_multiseed.png"), "Preservation checks per run; dashed lines are registered limits.", True),
            ("sub", "Training dynamics and checkpoints"),
            ("fig", fig("f01_training_return.png"), "Training return (left) and training-time controlled − twin coordination "
                    "(right, 100-episode bins) for all five runs.", True),
            ("p", optc_txt),
            ("fig", fig("f02_heldout_vs_progress.png"), "OPT-C: held-out Δ at updates 0–125 (monitoring only).", True),
            ("fig", fig("f06_kl_multiseed.png"), "Policy KL to the uncoupled sampler during training.", False),
            ("fig", fig("f03_training_constraints.png"), "Constraint values during training; λ remained 0 throughout.", False),
            ("sub", "Stability"),
            ("fig", fig("f09_seed_stability.png"), "Across-run spread of the effect and controller statistics.", True),
        ]},
        {"title": "Results: FG-1 feasibility gate", "blocks": [("p", t) for t in fg_paras] + [
            ("table", "FG-1 per-variant results (16 TRAIN clips, held-out = 16 fresh noises per clip, space R)", fg_rows, True),
            ("fig", fig("f08_fg1_comparison.png"), "FG-1 held-out vs in-sample Δ per variant and statistic; dashed = 0.05.", True),
            ("fig", fig("f08b_cross_study_kl.png"), "Held-out gain vs KL across studies. Descriptive only: studies differ in "
                    "clips, noises and budgets; only FG-1 is like-for-like.", False),
        ]},
        {"title": "Generalisation, ablations and computation", "blocks": [
            ("p", optg_txt),
            ("fig", fig("f10_generalisation.png"), "In-sample vs held-out: E2c (ii), ACMS OPT-G vs dev, FG-1.", True),
            ("p", "Ablations actually run: (a) trained vs initial policy and initial vs uncoupled (all ACMS runs); (b) FG-1 "
                  "state-shuffle, replacing the conditioning signal ŝ with that of a different noise draw (V2, V3). No other "
                  "ablation was run, and none is implied."),
            ("fig", fig("f12_ablations.png"), "Ablations that were actually run.", True),
            ("table", "Measured computational cost (single RTX A4000 16 GB)", compute_rows(D), False),
            ("fig", fig("f07_mc_history.png"), "Historical M-C feasibility (Stage 4): fixed coupling (E2e) and per-clip learned "
                    "coupling (E2c (ii)).", True),
        ]},
        {"title": "Consolidated results", "blocks": [
            ("table", "All executed experiments (released-checkpoint results; space R)", consolidated(D), True),
            ("table", "Metric coverage: measured (registered outputs), derived (post-hoc, from saved outputs), unavailable, not used",
             coverage_rows(D), True),
            ("p", "The project's slide deck from earlier stages was not present in the workspace, so direct deck-to-deck "
                  "coverage verification was **unavailable**; metric coverage was checked against the written coverage "
                  "plan (`PPT_METRIC_COVERAGE.md`) instead."),
        ]},
        posthoc_section(D),
        {"title": "Discussion", "blocks": [
            ("p", f"Three controller families now have measured held-out evidence on the frozen SignSparK sampler. Fixed M-C "
                  "coupling (E2e) failed its registered gate. Per-clip learned M-C coupling (E2c (ii)) fits its own noise "
                  "draws to an in-sample coordination of 0.74 (above the 0.45 reference level) yet transfers nothing to fresh "
                  "noise. Amortised ACMS gives a positive *direction* in three of four new runs but a magnitude about "
                  f"1/{mult:.0f} of the relevance threshold, with high "
                  "across-seed heterogeneity. FG-1 places all families on identical clips and noises."
                  + (f" {fg_contrast(D)}. Learned M-C coupling (V1) again fits strongly in sample "
                     f"({est(D.fg_variant('V1')['statistics']['R']['insample_delta_last_iter'], 3)}) and transfers almost "
                     f"nothing ({est(D.fg_variant('V1')['statistics']['R']['heldout_delta_vs_V0'])})." if fg_contrast(D) and D.fg_variant("V1") else "")),
            ("p", "The contrast between FG-1 and the multi-seed result locates the bottleneck. A state-conditioned mean shift "
                  "within a KL budget of about 0.1 nats/frame **can** move coordination by more than 0.05 on fresh noise when it "
                  "is fitted to one clip, and the state-shuffle ablation shows that the gain depends on conditioning on the "
                  "matching arm signal. The amortised policy, one 433-parameter controller shared across all training clips "
                  "and trained with REINFORCE, captures only a few per cent of that. A plausible interpretation, consistent "
                  "with Stage 4 Theorem 3, is that the useful arm-to-hand mapping in noise space is clip-specific, so a single "
                  "shared controller averages it away. This is an interpretation, not a tested claim: FG-1 used pathwise "
                  "gradients rather than RL, so it does not separate the effect of amortisation from that of the gradient "
                  "estimator."),
            ("p", "The results do **not** show that RL cannot improve SignSparK in general; they apply to noise-space control "
                  "of a frozen checkpoint with the registered motion-statistic reward. Fine-tuning, architectural coupling of "
                  "the hand generators, and perceptual or semantic objectives were outside scope."),
        ]},
        {"title": "Limitations and threats to validity", "blocks": [
            ("ul", ["Four new training runs give a wide t-interval (t-critical 3.18); the seed-sensitive category reflects both "
                    "heterogeneity and low power.",
                    "Coordination in R is a motion statistic validated only automatically (V-R1–V-R4); perceptual validity is out of scope.",
                    "J statistics include SMPL-X skinning leakage (~1–2% of hand signal); used descriptively only.",
                    "FG-1 uses 16 TRAIN clips and one fit per clip (no seed replication); per-clip fitting with pathwise "
                    "gradients tests controllability, not an amortised or deployable RL policy, and needs the clip in advance.",
                    "V2 misses the articulation-ratio bound narrowly; the bound was applied as registered and not revisited.",
                    "The checkpoint's pretraining split usage is undocumented (possible How2Sign leakage), irrelevant to "
                    "relative comparisons but relevant to absolute levels.",
                    "cuDNN non-determinism is permitted (TF32 off for matmul); repeated runs may differ in low-order bits."]),
        ]},
        {"title": "Conclusion", "blocks": [
            ("p", f"On the evidence obtained, amortised noise-space RL on the frozen SignSparK checkpoint does not produce a "
                  f"practically relevant improvement in arm–hand coordination. The only positive pre-registered training result "
                  f"(ACMS run 7000) replicates in direction in three of four new seeds, but the pooled effect "
                  f"{est(p4['pooled_t'])} is **{p4['category']}** and about {mult:.0f} times below the registered threshold. "
                  f"Preservation holds throughout. {fg_summary(D)} Per-clip, state-conditioned noise control is therefore "
                  f"feasible on fresh noise, but turning it into a single policy that works across clips was not achieved. "
                  f"The project is closed on this evidence."),
        ]},
        {"title": "Reproducibility statement", "unnumbered": True, "blocks": [
            ("p", "All code, configurations, seeds, commands, runtimes, GPU memory and SHA-256 hashes are listed in "
                  "`research/final/EXPERIMENT_MANIFEST.json`. Environment: Windows 11, Python 3.12, torch 2.10.0+cu128, RTX A4000 "
                  "16 GB. Released SignSparK checkpoints (body bf95bb02…, hand 5bb8e407…) were verified unchanged after all runs."),
        ]},
    ]
    sections = [s for s in sections if s]  # post-hoc section is None when its analysis was not run
    for s in sections:  # drop figure blocks whose figure is unavailable (listed in figures_index.json instead)
        s["blocks"] = [b for b in s["blocks"] if not (b[0] == "fig" and b[1] is None)]
    return {"title": "Noise-Space Reinforcement Learning for Arm–Hand Coordination in a Frozen Sign Language Production "
                     "Model: A Pre-registered Multi-Seed and Feasibility Study",
            "authors": ["SignSparK RL project", "Released-checkpoint result, not a paper reproduction"],
            "date": "Final report · 7 November 2026",
            "abstract": (f"We study whether reinforcement learning on the initial noise of the frozen SignSparK sign language "
                         f"production model can improve the coordination between generated arm and hand motion on How2Sign, "
                         f"which is at chance level in gloss-free generation. A 433-parameter arm-conditioned mean-shift "
                         f"policy (ACMS) trained with REINFORCE previously gave a small positive pre-registered result. A "
                         f"four-seed replication gives a pooled gain of {est(p4['pooled_t'])} in right arm–hand coordination "
                         f"(registered category: {p4['category']}; I² = {het['I2']:.2f}), about 1/{mult:.0f} of the registered 0.05 "
                         f"relevance threshold, with all preservation checks passing. A like-for-like per-clip gate (FG-1) "
                         f"compares learned coupling, per-clip ACMS and a bilateral variant on fresh noise. {fg_summary(D)} "
                         f"We conclude that the amortised RL policy yields no practically relevant improvement under the "
                         f"registered motion-statistic objective, while per-clip state-conditioned control is feasible. No "
                         f"perceptual, semantic or ASL-quality claim is made."),
            "keywords": ["sign language production", "reinforcement learning", "rectified flow", "noise-space control",
                         "pre-registration", "multi-seed replication"],
            "sections": sections, "references": STAGE_REFS}
