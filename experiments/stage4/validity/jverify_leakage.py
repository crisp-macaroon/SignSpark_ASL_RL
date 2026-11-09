"""Task 1: J v1.1 verification of the frozen R0 space-J targets. Task 2: SMPL-X skinning-leakage quantification.
Read-only; How2Sign TRAIN references only (exact R0 loader, clip order, settings; CPU, 4 threads); synthetic re-posing.
No generation, no dev/test data, no model other than SMPL-X FK; metric definitions and frozen targets unchanged.

Task 1 (all 29,630 clips): J v1.1 (validity.j_stats) per clip; four signals (arm L, arm R, hand L, hand R) checked;
  values compared with R0's stored J v1 per-clip values (chunk rows, columns 4..7). No target recomputed.

Task 2 (pre-specified subset: every 10th train clip, index i % 10 == 0, 2,963 clips; plus 50 synthetic sequences):
  re-posing per clip, same definitions (validity.j_signals):
    actual       body and hands as recorded
    arm-static   body held at its frame-0 pose, hands as recorded   -> hand signal without arm-induced leakage
    hand-static  hands held at their frame-0 pose, body as recorded  -> leakage-only hand signal
  measures per side s: leakage = mean hand-static hand signal (m/frame); ratio = leakage / mean actual hand signal;
    coord_actual = corr(arm_s, hand_s actual); coord_noleak = corr(arm_s, hand_s arm-static);
    coord_leakonly = corr(arm_s, hand_s hand-static); same for L-R coordination.
  PRE-STATED materiality criterion (fixed before the run): the leakage materially influences J arm-hand coordination
    if, for either side, the paired mean difference coord_actual - coord_noleak has a 95% bootstrap CI excluding 0
    AND |mean difference| >= 0.02, OR the per-clip Spearman between coord_actual and coord_noleak is < 0.90.
  Descriptive only: no target is computed or adopted from the arm-static variant.
Synthetic part: 50 random-walk sequences (arm moving, hands static identity; arm static, hands moving) for a
  controlled leakage-per-arm-speed figure; clearly labelled synthetic.

    python -E -s experiments/stage4/validity/jverify_leakage.py --out experiments/stage4/validity/jverify
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""
for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[_k] = "4"

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(4)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "experiments" / "stage4"))
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "r0"))
import r0_run as R0  # noqa: E402  (same dataset construction; appends .venv-render site-packages last for smplx)
import validity as V  # noqa: E402
import jspace as JS  # noqa: E402

CHUNK = 500
SUB = 10
JCOLS = {"coord_ah_J_L": 4, "coord_ah_J_R": 5, "coord_lr_J": 6, "dom_J": 7}


def corr(a, b):
    return V.MR.corr(a, b)


def leak_rows(ctx, b, hl, hr):
    """Three re-posings -> per-side leakage and coordination measures."""
    act = V.j_signals(ctx, b, hl, hr)
    arm_static = V.j_signals(ctx, np.repeat(b[:1], len(b), 0), hl, hr)
    hand_static = V.j_signals(ctx, b, np.repeat(hl[:1], len(hl), 0), np.repeat(hr[:1], len(hr), 0))
    if act is None or arm_static is None or hand_static is None:
        return None
    r = {}
    for s in ("L", "R"):
        r[f"leak_{s}"] = float(hand_static[f"hand_{s}"].mean())
        r[f"actual_{s}"] = float(act[f"hand_{s}"].mean())
        r[f"armstatic_{s}"] = float(arm_static[f"hand_{s}"].mean())
        r[f"coord_actual_{s}"] = corr(act[f"arm_{s}"], act[f"hand_{s}"])
        r[f"coord_noleak_{s}"] = corr(act[f"arm_{s}"], arm_static[f"hand_{s}"])
        r[f"coord_leakonly_{s}"] = corr(act[f"arm_{s}"], hand_static[f"hand_{s}"])
        r[f"armspeed_{s}"] = float(act[f"arm_{s}"].mean())
    r["lr_actual"] = corr(act["hand_L"], act["hand_R"])
    r["lr_noleak"] = corr(arm_static["hand_L"], arm_static["hand_R"])
    return r


def synthetic(ctx):
    from scipy.spatial.transform import Rotation
    rng = np.random.default_rng(31)

    def seq(J, T, step):
        rv = np.cumsum(rng.normal(0, step, (T, J, 3)), axis=0) if step > 0 else np.zeros((T, J, 3))
        M = Rotation.from_rotvec(rv.reshape(-1, 3)).as_matrix().reshape(T, J, 3, 3)
        return np.concatenate([M[..., 0, :], M[..., 1, :]], axis=-1).reshape(T, J * 6)

    out = []
    for _ in range(50):
        T = 120
        b, h = seq(10, T, 0.05), seq(15, T, 0.05)
        hs = seq(15, T, 0)
        leak = V.j_signals(ctx, b, hs, hs)          # arm moving, hands static
        real = V.j_signals(ctx, np.repeat(b[:1], T, 0), h, h)  # arm static, hands moving
        out.append({"leak_mean": float(leak["hand_R"].mean()), "arm_speed": float(leak["arm_R"].mean()),
                    "hand_mean_armstatic": float(real["hand_R"].mean()),
                    "coord_leakonly": corr(leak["arm_R"], leak["hand_R"])})
    a = {k: np.array([o[k] for o in out]) for k in out[0]}
    return {"n": 50, "label": "SYNTHETIC random-walk poses (0.05 rad/frame steps), not real data",
            "leak_mean_m_per_frame": float(a["leak_mean"].mean()), "arm_speed_m_per_frame": float(a["arm_speed"].mean()),
            "leak_per_unit_wrist_speed": float((a["leak_mean"] / a["arm_speed"]).mean()),
            "hand_signal_mean_armstatic": float(a["hand_mean_armstatic"].mean()),
            "leak_ratio_vs_moving_hand": float(a["leak_mean"].mean() / a["hand_mean_armstatic"].mean()),
            "coord_leakonly_mean": float(np.nanmean(a["coord_leakonly"]))}


def boot_mean_diff(d, seed=0, B=2000):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    idx = np.random.default_rng(seed).integers(0, len(d), (B, len(d)))
    m = d[idx].mean(1)
    return {"mean": float(d.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(d))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "chunks").mkdir(parents=True, exist_ok=True)
    stop_file = out / "STOP"
    t0 = time.time()
    ctx = JS.load_model()
    chunks_r0 = [np.load(ROOT / "experiments/stage4/r0/out/chunks" / f"chunk_{ci:03d}.npz") for ci in range(60)]
    v1_rows = np.concatenate([c["rows"] for c in chunks_r0])
    v1_names = np.concatenate([c["names"] for c in chunks_r0])
    ds = R0.dataset()
    N = len(ds)
    assert N == len(v1_names) == 29630
    n_chunks = (N + CHUNK - 1) // CHUNK
    for ci in range(n_chunks):
        cpath = out / "chunks" / f"chunk_{ci:03d}.npz"
        if cpath.exists():
            continue
        if stop_file.exists():
            print("paused by STOP", flush=True)
            return
        tc = time.time()
        jrows, valid, names, leak = [], [], [], []
        for i in range(ci * CHUNK, min(N, (ci + 1) * CHUNK)):
            ff, Lf, _, _, name = ds[i]
            if str(name) != str(v1_names[i]):
                raise SystemExit(f"clip order mismatch at {i}")
            f = ff.numpy().astype(np.float64)
            L = int(Lf)
            hl, hr, b = f[:L, :90], f[:L, 90:180], f[:L, 180:240]
            s = V.j_stats(ctx, b, hl, hr)
            jrows.append([s[k] for k in JCOLS])
            vv = s["valid"]
            valid.append([vv.get("fk_finite", False)] + [vv.get(k, False) for k in ("arm_L", "arm_R", "hand_L", "hand_R")])
            names.append(str(name))
            if i % SUB == 0:
                lr = leak_rows(ctx, b, hl, hr)
                leak.append([i] + ([lr[k] for k in sorted(lr)] if lr else [np.nan] * 16))  # 7 per side x 2 + 2 L-R
                leak_keys = sorted(lr) if lr else None
        np.savez(cpath, jrows=np.array(jrows, float), valid=np.array(valid, bool), names=np.array(names),
                 leak=np.array(leak, float), leak_keys=np.array(leak_keys if leak_keys else []), seconds=time.time() - tc)
        print(f"chunk {ci + 1}/{n_chunks} {time.time() - tc:.0f}s total {(time.time() - t0) / 60:.1f}min", flush=True)

    parts = [np.load(out / "chunks" / f"chunk_{ci:03d}.npz") for ci in range(n_chunks)]
    jrows = np.concatenate([p["jrows"] for p in parts])
    valid = np.concatenate([p["valid"] for p in parts])
    names = np.concatenate([p["names"] for p in parts])
    keys = [str(k) for k in parts[0]["leak_keys"]]
    leak = np.concatenate([p["leak"] for p in parts if len(p["leak"])])
    # ---------------- Task 1
    t1 = {"clips": int(len(names)), "order_matches_R0": bool((names == v1_names).all()),
          "fk_nonfinite_clips": int((~valid[:, 0]).sum()),
          "invalid_streams_by_signal": {k: int((~valid[:, i + 1]).sum()) for i, k in enumerate(("arm_L", "arm_R", "hand_L", "hand_R"))}}
    t1["invalid_streams_total"] = sum(t1["invalid_streams_by_signal"].values())
    t1["definedness_changes_v1_to_v1.1"] = {k: int((np.isnan(jrows[:, j]) != np.isnan(v1_rows[:, c])).sum()) for j, (k, c) in enumerate(JCOLS.items())}
    both = {k: np.isfinite(jrows[:, j]) & np.isfinite(v1_rows[:, c]) for j, (k, c) in enumerate(JCOLS.items())}
    t1["max_abs_diff_where_defined"] = {k: float(np.abs(jrows[both[k], j] - v1_rows[both[k], c]).max()) for j, (k, c) in enumerate(JCOLS.items())}
    t1["v1.1_means_vs_frozen_J_targets"] = {k: {"v1.1_mean": float(np.nanmean(jrows[:, j])), "v1_mean": float(np.nanmean(v1_rows[:, c]))}
                                            for j, (k, c) in enumerate(JCOLS.items())}
    t1["conclusion"] = ("No invalid J streams; v1.1 equals v1 on all clips: frozen J targets remain valid under J v1.1 unchanged."
                        if t1["invalid_streams_total"] == 0 and t1["fk_nonfinite_clips"] == 0
                        and all(v == 0 for v in t1["definedness_changes_v1_to_v1.1"].values())
                        and all(v == 0.0 for v in t1["max_abs_diff_where_defined"].values())
                        else "Differences or invalid streams found: see counts (no replacement target computed).")
    # ---------------- Task 2
    L = {k: leak[:, i + 1] for i, k in enumerate(keys)}
    t2 = {"subset": f"every {SUB}th train clip (i % {SUB} == 0)", "n_clips": int(len(leak)), "real_data": {}}
    from scipy.stats import spearmanr
    material = False
    for s in ("L", "R"):
        ratio = L[f"leak_{s}"] / L[f"actual_{s}"]
        d = L[f"coord_actual_{s}"] - L[f"coord_noleak_{s}"]
        ok = np.isfinite(L[f"coord_actual_{s}"]) & np.isfinite(L[f"coord_noleak_{s}"])
        sp = float(spearmanr(L[f"coord_actual_{s}"][ok], L[f"coord_noleak_{s}"][ok]).correlation)
        md = boot_mean_diff(d)
        mat = (not (md["ci95"][0] <= 0 <= md["ci95"][1]) and abs(md["mean"]) >= 0.02) or sp < 0.90
        material |= mat
        t2["real_data"][s] = {
            "leakage_m_per_frame": {"median": float(np.nanmedian(L[f"leak_{s}"])), "mean": float(np.nanmean(L[f"leak_{s}"])),
                                    "p95": float(np.nanpercentile(L[f"leak_{s}"], 95))},
            "actual_hand_signal_m_per_frame": {"median": float(np.nanmedian(L[f"actual_{s}"]))},
            "leakage_ratio_vs_actual": {"median": float(np.nanmedian(ratio)), "p95": float(np.nanpercentile(ratio, 95)),
                                        "mean": float(np.nanmean(ratio))},
            "coord_actual_mean": float(np.nanmean(L[f"coord_actual_{s}"])), "coord_noleak_mean": float(np.nanmean(L[f"coord_noleak_{s}"])),
            "coord_leakonly_mean": float(np.nanmean(L[f"coord_leakonly_{s}"])),
            "paired_diff_actual_minus_noleak": md, "spearman_actual_vs_noleak": sp, "material_by_prestated_criterion": bool(mat)}
    dlr = L["lr_actual"] - L["lr_noleak"]
    t2["real_data"]["LR"] = {"lr_actual_mean": float(np.nanmean(L["lr_actual"])), "lr_noleak_mean": float(np.nanmean(L["lr_noleak"])),
                             "paired_diff": boot_mean_diff(dlr)}
    t2["material_overall"] = bool(material)
    t2["synthetic"] = synthetic(ctx)
    res = {"task1_J_v1.1_verification": t1, "task2_skinning_leakage": t2, "minutes": round((time.time() - t0) / 60, 1)}
    (out / "jverify_leakage_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
