"""E2e-J: joint-space secondary analysis of the saved E2e dumps (Stage 4 rev. 4.0 §15.3.2; C-j1). NON-GATING.

Analysis of existing E2e outputs only: no generation. .venv-render, CPU. SMPL-X E0.4 FK (flip_left_hand=True).
Per sample: space-J statistics (jspace.py). Aggregation as §6.5 (sample -> clip mean -> population), paired by clip
with A0, first 8 noises for every condition (as the registered R-space T3/T4/T5-B, P-10), clip-cluster bootstrap
2,000 resamples, seed 0 (C-j1), 95% CIs.
  T3-J  BH conditions: delta coord_ah_J (R, L) vs A0          T4-J  LR conditions: delta coord_lr_J vs A0
  T5-J  SS conditions: D-a and D-b in J with t*_32^J (dev references of the 32 clips, recomputed per replicate)
  Agreement table per condition and statistic: "both" (same sign, both 95% CIs exclude 0) / "R only" / "J only" /
  "neither" / "opposite" (both exclude 0 with opposite signs)
FK health: every FK finite and bone lengths within 1e-4 relative; otherwise E2e-J stops and reports.
Partial-stop rule: conditions without complete k = 1..8 dumps are reported unavailable; nothing is generated.
Released-checkpoint results, not a paper reproduction; no perceptual claims.

    python -E -s experiments/stage4/e2e_j/e2ej_run.py --dumps experiments/stage4/e2e/dumps --e2e experiments/stage4/e2e/out --out experiments/stage4/e2e_j/out
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "stage4"))
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2e"))
import jspace as JS  # noqa: E402
import noise_transform as NT  # noqa: E402
import stats as S  # noqa: E402

J, NK, CAP_S = 32, 8, 3600
DEV256 = {s: ROOT / f"experiments/baseline/runs/{s}/h2s_dev256_gf_s10_N8/debug0_eulerstepsize10_can8_anchor0_samples/seed102_clampstep0_h2s_dev256_gf_s10_N8.npy"
          for s in ("body", "hand")}
KEYS = ("coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J")


class Stop(Exception):
    pass


def da_db(cond, a0, ref_x, idx, delta_s2):
    """D-a and D-b (§6.5) applied to the J-space log-ratio; t*_32^J recomputed in every replicate."""
    xc, xa = np.nanmean(cond, 1), np.nanmean(a0, 1)

    def q(rows):
        t = float(np.nanmean(ref_x[rows]))
        mc, ma = np.nanmean(xc[rows]), np.nanmean(xa[rows])
        return {"t": t, "gap": t - ma, "delta": mc - ma, "g_a": abs(ma - t), "rho": abs(mc - t) / max(abs(ma - t), 1e-12),
                "m_minus_t": mc - t}
    pt = q(np.arange(J))
    R = {k: np.array([q(r)[k] for r in idx]) for k in pt}
    d = np.sign(pt["gap"])
    assess_a = not (np.percentile(R["gap"], 2.5) <= 0 <= np.percentile(R["gap"], 97.5))
    ci = [float(np.percentile(R["delta"], 2.5)), float(np.percentile(R["delta"], 97.5))]
    da = {"assessable": bool(assess_a), "t32_J": pt["t"], "direction": float(d), "delta": pt["delta"], "delta_ci95": ci,
          "pass": bool(assess_a and np.sign(pt["delta"]) == d and abs(pt["delta"]) >= 0.10 and not (ci[0] <= 0 <= ci[1]))}
    assess_b = float(np.percentile(R["g_a"], 2.5)) >= 0.10
    db = {"assessable": bool(assess_b), "rho_g": pt["rho"], "rho_g_upper95": float(np.percentile(R["rho"], 95)),
          "closer": bool(assess_b and np.percentile(R["rho"], 95) <= 0.50),
          "overshoot": bool(d * pt["m_minus_t"] > 0.10),
          "at_target_ci90": [float(np.percentile(R["m_minus_t"], 5)), float(np.percentile(R["m_minus_t"], 95))]}
    db["at_target"] = bool(-delta_s2 <= db["at_target_ci90"][0] and db["at_target_ci90"][1] <= delta_s2)
    return {"D_a_J": da, "D_b_J": db}


def agree(r, j):
    def sig(x):
        lo, hi = x["ci95"]
        return 0 if lo <= 0 <= hi else (1 if lo > 0 else -1)
    sr, sj = sig(r), sig(j)
    if sr and sj:
        return "both" if sr == sj else "opposite"
    return "R only" if sr else ("J only" if sj else "neither")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--e2e", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    dumps, out = Path(args.dumps), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    e2e = json.loads((Path(args.e2e) / "results.json").read_text(encoding="utf-8"))
    s0 = e2e["steps"]["0"]
    lengths, names, delta_s2 = s0["ref32_lengths"], s0["ref32_names"], s0["delta_S2"]
    res = {"label": "E2e-J (non-gating), space J; released-checkpoint results, not a paper reproduction",
           "e2e_status": e2e.get("status"), "conditions": {}, "unavailable": [], "fk": {"calls": 0, "max_bone": 0.0}}
    ctx = JS.load_model()

    def stat(b6, l6, r6, L):
        s = JS.jstats(ctx, b6[:, :L].T, l6[:, :L].T, r6[:, :L].T)
        res["fk"]["calls"] += 1
        res["fk"]["max_bone"] = max(res["fk"]["max_bone"], s["fk_bone_max_rel_dev"])
        if not s["fk_finite"] or s["fk_bone_max_rel_dev"] > 1e-4:
            raise Stop(f"FK health failure (finite={s['fk_finite']}, bone={s['fk_bone_max_rel_dev']})")
        return s

    try:
        # references (dev clips 0..31) for t*_32^J
        db = np.load(DEV256["body"], allow_pickle=True).item()  # our own dumps (dict pickled by np.save)
        dh = np.load(DEV256["hand"], allow_pickle=True).item()
        assert [str(v) for v in db["video_names"][0, :J]] == names
        ref_x = np.array([stat(db["gt_poses"][0, j], dh["gt_poses"][0, 2 * j], dh["gt_poses"][0, 2 * j + 1], lengths[j])["dom_J"]
                          for j in range(J)])
        res["t32_J_point"] = float(np.nanmean(ref_x))
        bodies = {}
        for base in ("A0", "A0p"):
            if all((dumps / base / f"k{k:02d}.npz").exists() for k in range(1, NK + 1)):
                bodies[base] = {k: np.load(dumps / base / f"k{k:02d}.npz")["body"] for k in range(1, NK + 1)}
        data = {}
        for c in NT.CONDITIONS:
            name = c["name"]
            files = [dumps / name / f"k{k:02d}.npz" for k in range(1, NK + 1)]
            if not all(f.exists() for f in files) or "A0" not in bodies:
                res["unavailable"].append(name)
                continue
            if time.time() - t0 > CAP_S:
                raise Stop("1 h cap reached")
            arr = {k: np.full((J, NK), np.nan) for k in KEYS}
            for ki, f in enumerate(files):
                hand = np.load(f)["hand"]
                body = bodies["A0p" if name == "A0p" else "A0"][ki + 1]
                for j in range(J):
                    s = stat(body[j], hand[j, 0], hand[j, 1], lengths[j])
                    for k in KEYS:
                        arr[k][j, ki] = s[k]
            data[name] = arr
            print(f"[{time.time() - t0:6.0f}s] {name}", flush=True)
        idx = S.boot_idx(J, 0)
        an = e2e.get("analysis", {})
        if "A0" in data:
            a0 = data["A0"]
            for c in NT.CONDITIONS:
                n = c["name"]
                if n not in data or c["kind"] == "base":
                    continue
                row = {}
                if c["kind"] in ("BH", "BH_arm", "LR"):
                    for k in ("coord_ah_J_R", "coord_ah_J_L", "coord_lr_J"):
                        row[k] = S.paired_delta(data[n], a0, k, idx)
                    rgrp = an.get("T3" if c["kind"] != "LR" else "T4", {}).get(n)
                    if rgrp:
                        row["agreement"] = {kj: agree(rgrp[kr], row[kj]) for kr, kj in
                                            (("coord_arm_rhand", "coord_ah_J_R"), ("coord_arm_lhand", "coord_ah_J_L"),
                                             ("coord_lr", "coord_lr_J"))}
                        row["R_space"] = {kr: rgrp[kr] for kr in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr")}
                else:  # SS
                    row = da_db(data[n]["dom_J"], a0["dom_J"], ref_x, idx, delta_s2)
                    row["delta_dom_J"] = S.paired_delta(data[n], a0, "dom_J", idx)
                    rss = an.get("T5B", {}).get(n)
                    if rss:
                        rd = {"delta": rss["D_a"]["delta"], "ci95": rss["D_a"]["delta_ci95"]}
                        row["agreement_D_a_delta"] = agree(rd, row["delta_dom_J"])
                        row["R_space_D_a"] = rss["D_a"]
                res["conditions"][n] = row
        res["status"] = "completed"
    except Stop as e:
        res["status"] = f"stopped: {e}"
    res["seconds"] = round(time.time() - t0)
    (out / "e2ej_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(res["status"], res["seconds"], "s")


if __name__ == "__main__":
    main()
