"""R0: reference-only train targets in space R and space J (Stage 4 rev. 4.0 §6.0 rule iv; campaign C-r1..C-r6).

How2Sign TRAIN references only (29,630 clips; no dev, no test), read-only, upstream loader (flip_left_hand=True,
seq_len 304 truncation); clips with L < 8 excluded. CPU only. No generation, no model other than SMPL-X FK.

Targets (each: mean over clips of the per-clip reference statistic, 95% clip-bootstrap CI, 2,000 resamples, seed 0):
  space R: tau_ah_R(L), tau_ah_R(R), tau_lr_R, t*_R (mean log(A_L/A_R))     [e2e/metrics.py definitions]
  space J: tau_ah_J(L), tau_ah_J(R), tau_lr_J, t*_J                          [jspace.py definitions]
U-A11: SMPL-X left/right hand rest-geometry mirror check (max |p_L - M p_R|, M = diag(-1, 1, 1)), and dom_J of
       synthetic identical-pose hands (expected 0 if mirror-symmetric).
V-R3 synthetic checks, expected values stated BEFORE the run:
  static pose (all frames identical)   -> every speed 0 -> coordination undefined (NaN) in R and J; dominance
                                          undefined (log 0/0 -> NaN). A static sequence cannot be scored, so a
                                          target-matching reward cannot be satisfied by it.
  train mean pose (static)             -> same as static.
  shared spike (one frame where both arms and both hands rotate by 0.3 rad, otherwise static)
                                       -> coord_ah (L, R) = coord_lr = 1.0 in R and J (the statistic is maximised
                                          by a shared spike: why rewards are target-matching and c_jerk exists);
                                          dom_R = 0 (equal spikes); dom_J ~ 0 (exactly 0 iff mirror-symmetric).
Safeguards R-1..R-5: run at BelowNormal priority with 4 threads (set by the launcher / below); checks the STOP file
between chunks of 500 clips; per-chunk checkpoints allow an exact resume; 3 h running-time cap (paused time excluded).

Environment note (campaign deviation, recorded): runs in .venv-infer (CUDA hidden) because .venv-render lacks the
upstream loader's packages (lmdb, hydra, omegaconf); the pure-Python smplx package is imported read-only from
.venv-render's site-packages (appended last to sys.path). No environment is modified.

    python -E -s experiments/stage4/r0/r0_run.py --out experiments/stage4/r0/out
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
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK"))
sys.path.insert(0, str(ROOT / "experiments" / "stage4"))
sys.path.insert(0, str(ROOT / "experiments" / "stage4" / "e2e"))
sys.path.append(str(ROOT / ".venv-render" / "Lib" / "site-packages"))  # smplx only (absent from .venv-infer)
import metrics as MR  # noqa: E402  (space R)
import jspace as JS  # noqa: E402  (space J)

CHUNK = 500
CAP_S = 3 * 3600
BOOT, BOOT_SEED = 2000, 0
LMDB = ROOT / "data" / "raw" / "SignSparK_data" / "train" / "How2Sign_reopt_train.lmdb"
KEYS = ["coord_ah_R_L", "coord_ah_R_R", "coord_lr_R", "dom_R", "coord_ah_J_L", "coord_ah_J_R", "coord_lr_J", "dom_J"]


def cfg_for(stream):
    from hydra import compose, initialize_config_dir
    ov = [f"data_v2={stream}", "data_v2/common@common=inference", f"base_path={ROOT / 'data' / 'raw' / 'SignSparK_data'}",
          "train_data=[How2Sign]", "eval.split=train", "flip_left_hand=True"]
    with initialize_config_dir(config_dir=str(ROOT / "third_party" / "SignSparK" / "configs"), version_base=None):
        return compose(config_name="default", overrides=ov)


def dataset():
    """One upstream dataset with dataset_feat = "full": [left 90 | right 90 | body 60 | face] per frame, left hand
    flipped (flip_left_hand=True). (LMDB forbids opening the same environment twice in one process, so the body and
    hand streams cannot be two datasets; campaign fix.)"""
    from signspark.pose_datasets_lmdb import PoseDataset_Lmdb
    return PoseDataset_Lmdb(cfg_for("full"), split="train", seq_len=304, data=str(LMDB), concat_hands=False)


def clip_stats(ctx, b, h, L):
    xb, xl, xr = b[:L], h[:L, :90], h[:L, 90:180]
    r = MR.sample_record(xb.T, xl.T, xr.T, L)
    j = JS.jstats(ctx, xb, xl, xr)
    return {"coord_ah_R_L": r["coord_arm_lhand"], "coord_ah_R_R": r["coord_arm_rhand"], "coord_lr_R": r["coord_lr"],
            "dom_R": r["X"], "coord_ah_J_L": j["coord_ah_J_L"], "coord_ah_J_R": j["coord_ah_J_R"],
            "coord_lr_J": j["coord_lr_J"], "dom_J": j["dom_J"], "fk_finite": j["fk_finite"],
            "fk_bone": j["fk_bone_max_rel_dev"]}


def boot_ci(v, rng_idx):
    v = np.asarray(v, float)
    ok = np.isfinite(v)
    v = v[ok]
    if len(v) == 0:
        return None
    idx = rng_idx(len(v))
    m = v[idx].mean(1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(v))}


def rot6d_from_axis_angle(axis, angle):
    from scipy.spatial.transform import Rotation
    R = Rotation.from_rotvec(np.asarray(axis, float) * angle).as_matrix()
    return np.concatenate([R[0], R[1]])  # rows b1, b2 as in rot6d_to_matrix (stack of b1, b2, b3 as rows)


def synthetic_checks(ctx, mean6):
    """U-A11 and V-R3 on synthetic sequences (no data)."""
    model, rest, parents, _ = ctx
    M = np.diag([-1.0, 1.0, 1.0])
    pL, pR = rest[JS.L_HAND], rest[JS.R_HAND]
    wL, wR = rest[JS.L_WRIST], rest[JS.R_WRIST]
    ua11 = {"max_abs_mm": float(np.abs(pL - pR @ M.T).max() * 1000),
            "max_abs_wrist_relative_mm": float(np.abs((pL - wL) - (pR - wR) @ M.T).max() * 1000),
            "wrist_mirror_mm": float(np.abs(wL - M @ wR).max() * 1000)}
    ident = np.tile(rot6d_from_axis_angle([1, 0, 0], 0.0), 10)
    rng = np.random.default_rng(7)
    doms = []
    for _ in range(20):  # identical smooth random hand pose sequences on both hands, identity body
        L = 120
        aa = np.cumsum(rng.normal(0, 0.03, (L, 15, 3)), axis=0)
        h6 = np.stack([np.concatenate([rot6d_from_axis_angle(a / max(np.linalg.norm(a), 1e-12), np.linalg.norm(a))
                                       for a in aa[t]]) for t in range(L)])
        b6 = np.tile(ident, (L, 1))
        doms.append(JS.jstats(ctx, b6, h6, h6)["dom_J"])
    ua11["dom_J_identical_hands"] = {"mean": float(np.mean(doms)), "max_abs": float(np.max(np.abs(doms)))}

    def both(b6, h6l, h6r):
        L = b6.shape[0]
        try:
            r = MR.sample_record(b6.T, h6l.T, h6r.T, L)
            rr = {"coord_ah_L": r["coord_arm_lhand"], "coord_ah_R": r["coord_arm_rhand"], "coord_lr": r["coord_lr"],
                  "dom": r["X"]}
        except ZeroDivisionError:
            # resume-run fix (2026-11-03): the registered R-space metric divides A_L / A_R in plain Python and raises
            # for a frozen hand (A = 0) instead of returning NaN; recorded as "undefined (raises)". Registered metric
            # code unchanged.
            hl, hr = MR.hand_stats(h6l.T, L), MR.hand_stats(h6r.T, L)
            arm_r, arm_l = MR.arm_signals(b6.T, L)
            rr = {"coord_ah_L": MR.corr(arm_l, hl["s"]), "coord_ah_R": MR.corr(arm_r, hr["s"]),
                  "coord_lr": MR.corr(hl["s"], hr["s"]), "dom": "undefined: ZeroDivisionError (A_R = 0)"}
        j = JS.jstats(ctx, b6, h6l, h6r)
        return {"R": rr,
                "J": {"coord_ah_L": j["coord_ah_J_L"], "coord_ah_R": j["coord_ah_J_R"], "coord_lr": j["coord_lr_J"],
                      "dom": j["dom_J"]}}

    L = 100
    hid = np.tile(rot6d_from_axis_angle([1, 0, 0], 0.0), 15)
    static = both(np.tile(ident, (L, 1)), np.tile(hid, (L, 1)), np.tile(hid, (L, 1)))
    mb, mh = mean6
    meanpose = both(np.tile(mb, (L, 1)), np.tile(mh[:90], (L, 1)), np.tile(mh[90:], (L, 1)))
    b6, hl, hr = np.tile(ident, (L, 1)), np.tile(hid, (L, 1)), np.tile(hid, (L, 1))
    spike = rot6d_from_axis_angle([1, 0, 0], 0.3)
    for j in (6, 7, 8, 9):  # elbows and wrists
        b6[50, 6 * j:6 * j + 6] = spike
    hl[50] = np.tile(spike, 15)
    hr[50] = np.tile(spike, 15)
    shared = both(b6, hl, hr)
    return {"U-A11": ua11,
            "V-R3": {"expected": {"static": "all NaN (undefined)", "train_mean_pose": "all NaN (undefined)",
                                  "shared_spike": "coord = 1.0 (R, J); dom_R = 0; dom_J ~ 0"},
                     "static": static, "train_mean_pose": meanpose, "shared_spike": shared}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "chunks").mkdir(parents=True, exist_ok=True)
    stop_file = out.parent / "STOP"
    t_start = time.time()
    ctx = JS.load_model()
    ds = dataset()
    N = len(ds)
    n_chunks = (N + CHUNK - 1) // CHUNK
    status = {"N_train": N, "chunks": n_chunks, "status": "running"}
    run_time = sum(float(np.load(p)["seconds"]) for p in (out / "chunks").glob("chunk_*.npz"))
    msum_b, msum_h, mcount = np.zeros(60), np.zeros(180), 0
    for ci in range(n_chunks):
        cpath = out / "chunks" / f"chunk_{ci:03d}.npz"
        if cpath.exists():
            continue
        if stop_file.exists():
            status["status"] = f"paused by STOP file before chunk {ci}"
            (out / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
            print(status["status"], flush=True)
            return
        if run_time > CAP_S:
            status["status"] = "stopped: R0 3 h running-time cap (C-r6)"
            (out / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
            return
        t0 = time.time()
        rows, names, Ls, excl = [], [], [], 0
        sb, sh, sc = np.zeros(60), np.zeros(180), 0
        for i in range(ci * CHUNK, min(N, (ci + 1) * CHUNK)):
            ff, Lf, _, _, nb = ds[i]
            f = ff.numpy().astype(np.float64)
            if f.shape[1] < 240:
                status["status"] = f"stopped: unexpected full-feature width {f.shape[1]} at index {i}"
                (out / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
                raise SystemExit(status["status"])
            L = int(Lf)
            if L < 8:
                excl += 1
                continue
            h, b = f[:, :180], f[:, 180:240]  # [L 90 | R 90], body 60 (same slices as the hand / body streams)
            s = clip_stats(ctx, b, h, L)
            if not s["fk_finite"] or s["fk_bone"] > 1e-4:
                status["status"] = f"stopped: FK health failure at {nb} (finite={s['fk_finite']}, bone={s['fk_bone']})"  # noqa: E501
                (out / "status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
                raise SystemExit(status["status"])
            rows.append([s[k] for k in KEYS] + [s["fk_bone"]])
            names.append(nb); Ls.append(L)
            sb += b[:L].sum(0); sh += h[:L, :180].sum(0); sc += L
        dt = time.time() - t0
        run_time += dt
        np.savez(cpath, rows=np.array(rows, float), names=np.array(names), L=np.array(Ls), excluded=excl,
                 sum_b=sb, sum_h=sh, count=sc, seconds=dt)
        print(f"chunk {ci + 1}/{n_chunks} clips={len(rows)} excl={excl} {dt:.0f}s run_time={run_time / 60:.1f}min",
              flush=True)
    # ---------------------------------------------------------------- aggregate
    parts = [np.load(out / "chunks" / f"chunk_{ci:03d}.npz") for ci in range(n_chunks)]
    rows = np.concatenate([p["rows"] for p in parts if len(p["rows"])])
    n_excl = int(sum(int(p["excluded"]) for p in parts))
    msum_b = sum(p["sum_b"] for p in parts); msum_h = sum(p["sum_h"] for p in parts); mcount = sum(int(p["count"]) for p in parts)
    brng = np.random.default_rng(BOOT_SEED)

    def rng_idx(n):
        return brng.integers(0, n, (BOOT, n))

    targets = {k: boot_ci(rows[:, i], rng_idx) for i, k in enumerate(KEYS)}
    names_map = {"coord_ah_R_L": "tau_ah_R(L)", "coord_ah_R_R": "tau_ah_R(R)", "coord_lr_R": "tau_lr_R", "dom_R": "t*_R",
                 "coord_ah_J_L": "tau_ah_J(L)", "coord_ah_J_R": "tau_ah_J(R)", "coord_lr_J": "tau_lr_J", "dom_J": "t*_J"}
    res = {"label": "R0 reference-only targets, How2Sign TRAIN references; frozen before Stage 5",
           "N_train_items": N, "clips_used": int(rows.shape[0]), "clips_excluded_L_lt_8": n_excl,
           "targets": {names_map[k]: v for k, v in targets.items()},
           "nan_counts": {k: int((~np.isfinite(rows[:, i])).sum()) for i, k in enumerate(KEYS)},
           "fk_bone_max_rel_dev": float(np.nanmax(rows[:, -1])),
           "per_clip_R_vs_J_spearman": {}, "run_time_min": round(run_time / 60, 1),
           "wall_time_this_session_min": round((time.time() - t_start) / 60, 1)}
    from scipy.stats import spearmanr
    for a, bk in (("coord_ah_R_R", "coord_ah_J_R"), ("coord_ah_R_L", "coord_ah_J_L"), ("coord_lr_R", "coord_lr_J"), ("dom_R", "dom_J")):
        ia, ib = KEYS.index(a), KEYS.index(bk)
        ok = np.isfinite(rows[:, ia]) & np.isfinite(rows[:, ib])
        res["per_clip_R_vs_J_spearman"][f"{a} vs {bk}"] = float(spearmanr(rows[ok, ia], rows[ok, ib]).correlation)
    mean6 = (msum_b / mcount, msum_h / mcount)
    res["synthetic"] = synthetic_checks(ctx, mean6)
    res["status"] = "completed"
    (out / "r0_results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    (out / "status.json").write_text(json.dumps({"status": "completed"}, indent=1), encoding="utf-8")
    print(json.dumps(res["targets"], indent=1))


if __name__ == "__main__":
    main()
