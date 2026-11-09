"""Stage 5 unit and integration tests (design §5). Results -> experiments/stage5/tests/out/{unit,integration}_tests.json.

  python -E -s experiments/stage5/tests/run_tests.py --unit
  python -E -s experiments/stage5/tests/run_tests.py --integration     (GPU; mini runs in subprocesses)

Unit (CPU, no SignSparK model): U1 log-prob, U2 beta=0 -> mu=0 and eps_R = xi bitwise, U3 padded frames, U4 KL cap and
formula, U5 Stiefel, U6 RLOO, U7 score-function unbiasedness (Monte Carlo z-test), U7b training-loss gradient =
analytic score estimator, U8 S-3 / A3 (synthetic NaN records and a real static-hand sample), U9 dual ascent, U10 frozen
target and registered thresholds, U11 sampler, U12 arm feature, U13 config guard, U14 split guard.
Integration (GPU): I1 loader equivalence vs unrolled_sampler.load_first_batch (dev 0..31; reference built in a
subprocess because LMDB cannot be opened twice per process), I2 reproduction of the E2e A0 k=1 dumps, I3 beta=0 ->
controlled right hand bitwise = uncoupled in one call, I4 two-group mini training (twice, subprocesses: logging
completeness, determinism, frozen weights, splits), I5 mini evaluation (2 dev clips x 1 noise, with J).
NOTE: the mini runs use tests/config_test.json (test_mode) and write only under tests/out/; they are not the
500-episode run.
"""

import argparse
import json
import math
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
S5 = HERE.parent
sys.path.insert(0, str(S5))
import common5 as C  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

import acms_policy as P  # noqa: E402
import episode_sampler as ES  # noqa: E402
import rewards as RW  # noqa: E402

OUT = HERE / "out"
PY = [sys.executable, "-E", "-s"]
RESULTS = []


def check(name, fn):
    t = time.time()
    try:
        detail = fn()
        ok = True if not isinstance(detail, dict) or "pass" not in detail else bool(detail["pass"])
    except Exception as e:  # recorded as failure
        detail, ok = {"error": repr(e), "traceback": traceback.format_exc()[-2000:]}, False
    RESULTS.append({"test": name, "pass": ok, "seconds": round(time.time() - t, 2), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {json.dumps(detail, default=str)[:300]}", flush=True)


def policy(**kw):
    return P.ACMS(**kw)


# --------------------------------------------------------------------------------------------- unit tests
def u1():
    torch.manual_seed(0)
    eps, mu, L = torch.randn(3, 90, 304), torch.randn(3, 90, 304) * 0.3, [50, 304, 10]
    lp = P.ACMS.log_prob(eps, mu, L)
    ref = torch.stack([torch.distributions.Normal(mu[i, :, :L[i]], 1.0).log_prob(eps[i, :, :L[i]]).sum() for i in range(3)])
    d = float((lp - ref).abs().max())
    return {"max_abs_diff": d, "pass": d < 1e-2 and float(((lp - ref).abs() / ref.abs()).max()) < 1e-6}


def u2():
    p = policy()
    with torch.no_grad():
        p.b.fill_(-1e4)
    s = torch.randn(4, 304)
    mu = p.mu(s, [304, 100, 50, 7])
    xi = torch.randn(4, 90, 304)
    return {"beta": float(p.beta()), "mu_all_zero": bool((mu == 0).all()), "eps_equals_xi_bitwise": bool(torch.equal(xi + mu, xi)),
            "pass": float(p.beta()) == 0.0 and bool((mu == 0).all()) and bool(torch.equal(xi + mu, xi))}


def u3():
    p = policy()
    with torch.no_grad():
        p.b.fill_(3.0)
    L = [30, 304, 1, 150]
    s = torch.randn(4, 304)
    for i, l in enumerate(L):
        s[i, l:] = 0
    mu = p.mu(s, L)
    pad_zero = all(bool((mu[i, :, l:] == 0).all()) for i, l in enumerate(L))
    active_nonzero = all(bool((mu[i, :, :l] != 0).any()) for i, l in enumerate(L))
    return {"padded_zero": pad_zero, "active_nonzero": active_nonzero, "pass": pad_zero and active_nonzero}


def u4():
    p = policy()
    with torch.no_grad():
        p.W.mul_(1e3); p.c.fill_(50.0); p.b.fill_(30.0)
    s = torch.randn(3, 304)
    L = [304, 120, 40]
    mu = p.mu(s, L)
    kl = P.ACMS.kl_per_frame(mu, L)
    direct = torch.stack([0.5 * (mu[i, :, :L[i]] ** 2).sum(0).mean() for i in range(3)])
    per_frame_max = float((0.5 * (mu ** 2).sum(1)).max())
    return {"kl": kl.tolist(), "max_per_frame_kl": per_frame_max, "beta_max": p.beta_max,
            "formula_max_abs_diff": float((kl - direct).abs().max()),
            "pass": per_frame_max <= 1.0 + 1e-6 and float(kl.max()) <= 1.0 + 1e-6 and float((kl - direct).abs().max()) < 1e-5}


def u5():
    p = policy()
    U = p.U()
    e = float((U.T @ U - torch.eye(p.rank)).abs().max())
    return {"orth_err": e, "shape": list(U.shape), "pass": e < 1e-5 and list(U.shape) == [90, 4]}


def u6():
    R = np.array([-0.5, -0.2, -0.9, -0.4])
    b, a = RW.rloo(R)
    R2 = R.copy(); R2[0] = 5.0
    b2, _ = RW.rloo(R2)
    expected_b0 = R[1:].mean()
    return {"adv_sum": float(a.sum()), "b0_matches_others_mean": bool(abs(b[0] - expected_b0) < 1e-12),
            "b0_independent_of_R0": bool(b2[0] == b[0]),
            "pass": abs(a.sum()) < 1e-12 and abs(b[0] - expected_b0) < 1e-12 and b2[0] == b[0]}


def u7():
    """Score-function estimator with RLOO is unbiased: synthetic reward f(eps) = -sum_{c<3,t<L} (eps - 0.5)^2."""
    torch.manual_seed(1)
    T, L, G, N = 16, 16, 4, 120_000
    p = policy()
    with torch.no_grad():
        p.b.fill_(2.0)
    s = torch.randn(1, T)
    with torch.no_grad():
        mu = p.mu(s, [L])[0]                                   # [90, T]
    g_true = torch.zeros(90, T)
    g_true[:3, :L] = -2 * (mu[:3, :L] - 0.5)                   # d E f / d mu
    acc, acc2, n = torch.zeros(90, T), torch.zeros(90, T), 0
    gen = torch.Generator().manual_seed(2)
    while n < N:
        xi = torch.randn(N // 10 // G, G, 90, T, generator=gen)
        eps = mu + xi
        f = -((eps[:, :, :3, :L] - 0.5) ** 2).sum((2, 3))      # [B, G]
        b = (f.sum(1, keepdim=True) - f) / (G - 1)
        A = f - b
        contrib = (A[:, :, None, None] * xi).reshape(-1, 90, T)  # score of log N(eps; mu, I) w.r.t. mu is xi
        acc += contrib.sum(0); acc2 += (contrib ** 2).sum(0); n += contrib.shape[0]
    g_hat = acc / n
    se = torch.sqrt((acc2 / n - g_hat ** 2) / n)
    z = (g_hat - g_true) / se
    # parameter level: chain rule through the policy Jacobian
    p.zero_grad()
    p.mu(s, [L])[0].backward(g_hat)
    gp_hat = torch.cat([q.grad.flatten() for q in p.parameters()]).clone()
    p.zero_grad()
    p.mu(s, [L])[0].backward(g_true)
    gp_true = torch.cat([q.grad.flatten() for q in p.parameters()]).clone()
    cos = float(torch.nn.functional.cosine_similarity(gp_hat, gp_true, dim=0))
    zmax = float(z.abs().max())
    return {"n": n, "max_abs_z": zmax, "mean_z": float(z.mean()), "param_grad_cosine": cos,
            "pass": zmax < 5.0 and abs(float(z.mean())) < 0.1 and cos > 0.95}


def u7b():
    """The training loss -(1/G) sum A_i log pi_i has gradient -(1/G) sum A_i xi_i^T dmu/dphi (exact)."""
    torch.manual_seed(3)
    p = policy()
    G, L = 4, [304] * 4
    s = torch.randn(G, 304)
    with torch.no_grad():
        mu = p.mu(s, L)
    xi = torch.randn(G, 90, 304)
    eps = mu + xi
    A = torch.tensor([0.3, -0.1, -0.5, 0.3])
    p.zero_grad()
    loss = -(A * P.ACMS.log_prob(eps, p.mu(s, L), L)).mean()
    loss.backward()
    g1 = torch.cat([q.grad.flatten() for q in p.parameters()]).clone()
    p.zero_grad()
    p.mu(s, L).backward(-(A[:, None, None] * xi) / G)
    g2 = torch.cat([q.grad.flatten() for q in p.parameters()]).clone()
    d = float((g1 - g2).abs().max() / g2.abs().max())
    return {"rel_max_diff": d, "pass": d < 1e-4}


def _rec(coord, valid_hand=True, finite=True, h=None):
    h = h or {"A": 1.0, "m1_speed": 0.01, "m2_artic": 0.2, "m3_jerk": 0.01, "m4_angle": 0.3, "extreme_frac": 0.0}
    return {"coord_arm_rhand": coord, "valid": {"input_finite": finite, "hand_R": valid_hand}, "hand_R": h}


def u8():
    lam = {k: 0.5 for k in RW.CONSTRAINTS}
    t1 = RW.episode_reward(_rec(float("nan")), _rec(0.1), lam)          # undefined primary
    t2 = RW.episode_reward(_rec(0.3, valid_hand=False), _rec(0.1), lam)  # invalid controlled hand -> constraints undefined
    t3 = RW.episode_reward(_rec(0.3), _rec(0.1, h={"A": 0.0, "m1_speed": 0, "m2_artic": 0.0, "m3_jerk": 0.0, "m4_angle": 0, "extreme_frac": 0}), lam)
    t4 = RW.episode_reward(_rec(0.3), _rec(0.1), lam)                   # all defined, identical stats -> c = -tol
    # real arrays: a static right hand (identity 6D) under random-walk body and left hand -> R v1.1 hand_R invalid
    rng = np.random.default_rng(0)
    L = 80
    ident = np.tile(np.array([1, 0, 0, 0, 1, 0], np.float32), 15)[:, None].repeat(304, 1)
    xb = (np.tile(np.array([1, 0, 0, 0, 1, 0], np.float32), 10)[:, None] + np.cumsum(rng.normal(0, 0.02, (60, 304)), 1)).astype(np.float32)
    xl = (ident + np.cumsum(rng.normal(0, 0.02, (90, 304)), 1)).astype(np.float32)
    rec_static = RW.r_record(xb, xl, ident, L)
    rec_moving = RW.r_record(xb, xl, (ident + np.cumsum(rng.normal(0, 0.02, (90, 304)), 1)).astype(np.float32), L)
    t5 = RW.episode_reward(rec_static, rec_moving, lam)
    ok = (t1["r_ah"] == RW.S3_WORST and t1["s3_undefined_primary"] and not any(t1["a3_undefined"].values())
          and all(t2["a3_undefined"].values()) and all(v == 1.0 for v in t2["c"].values())
          and t3["a3_undefined"]["art"] and t3["a3_undefined"]["jerk"] and t3["a3_undefined"]["act"] and not t3["a3_undefined"]["ext"]
          and abs(t4["c"]["art"] + 0.10) < 1e-12 and abs(t4["c"]["jerk"] + 0.10) < 1e-12 and abs(t4["c"]["act"] + math.log(1.25)) < 1e-12
          and rec_static["valid"]["hand_R"] is False and t5["s3_undefined_primary"] and all(t5["a3_undefined"].values())
          and abs(t5["R"] - (RW.S3_WORST - 4 * 0.5)) < 1e-12)
    return {"S3_worst": RW.S3_WORST, "t1": t1, "t2_c": t2["c"], "t3_undefined": t3["a3_undefined"], "t4_c": t4["c"],
            "static_hand_valid": rec_static["valid"], "t5_R": t5["R"], "pass": bool(ok)}


def u9():
    lam = {k: 0.0 for k in RW.CONSTRAINTS}
    cb = [{"art": 0.2, "jerk": -0.5, "ext": 1.0, "act": -0.1}, {"art": 0.4, "jerk": -0.3, "ext": 1.0, "act": 0.1}]
    l1 = RW.dual_update(lam, cb, 1.0)
    l2 = RW.dual_update(l1, [{"art": -1.0, "jerk": -1.0, "ext": -0.5, "act": -1.0}], 1.0)
    ok = (abs(l1["art"] - 0.3) < 1e-12 and l1["jerk"] == 0.0 and l1["ext"] == 1.0 and abs(l1["act"]) < 1e-12
          and l2["art"] == 0.0 and abs(l2["ext"] - 0.5) < 1e-12)
    return {"l1": l1, "l2": l2, "pass": ok}


def u10():
    ft = C.frozen_targets()
    ok = (RW.TAU == ft["R_space"]["tau_ah_R"]["value"] == 0.4514 and abs(RW.S3_WORST + 1.4514) < 1e-12
          and (RW.ART_TOL, RW.JERK_MAX, RW.EXT_TOL) == (0.10, 1.10, 0.02) and abs(RW.ACT_LOG - math.log(1.25)) < 1e-15
          and C.V.R_MEAN_FLOOR == 1e-5 and C.V.R_STD_FLOOR == 1e-6 and C.V.VERSION_R == "R v1.1")
    return {"tau": RW.TAU, "s3": RW.S3_WORST, "frozen_sha256": C.sha256(C.FROZEN), "pass": ok}


def u11():
    a, b = ES.train_clips(125, 5000), ES.train_clips(125, 5000)
    n1, n2, n3 = ES.train_noise(50_000_000, 3, 1), ES.train_noise(50_000_000, 3, 1), ES.train_noise(50_000_000, 3, 2)
    r = ES.seed_ranges(125, 4, 256, 4, 50_000_000, 40_000_000)
    disjoint = r["eval"][1] < r["train"][0] and r["e2e"][1] < r["eval"][0]
    ok = (a == b and len(set(a)) == 125 and min(a) >= 0 and max(a) < ES.N_TRAIN and torch.equal(n1, n2)
          and not torch.equal(n1, n3) and list(n1.shape) == [240, 304] and disjoint)
    return {"first_clips": a[:5], "seed_ranges": r, "pass": ok}


def u12():
    from scipy.spatial.transform import Rotation
    rng = np.random.default_rng(4)
    L = 120
    rv = np.cumsum(rng.normal(0, 0.05, (L, 10, 3)), 0)
    mats = Rotation.from_rotvec(rv.reshape(-1, 3)).as_matrix().reshape(L, 10, 3, 3)
    xb = np.zeros((60, 304), np.float32)
    xb[:, :L] = np.concatenate([mats[:, :, 0, :], mats[:, :, 1, :]], -1).reshape(L, 60).T
    xb[:, L:] = xb[:, L - 1: L]
    f, ok1 = C.arm_feature(xb, L)
    static = np.repeat(xb[:, :1], 304, 1)
    f2, ok2 = C.arm_feature(static, L)
    bad = xb.copy(); bad[0, 5] = np.nan
    f3, ok3 = C.arm_feature(bad, L)
    ok = (ok1 and abs(float(f[:L].mean())) < 1e-5 and abs(float(f[:L].std()) - 1) < 1e-4 and bool((f[L:] == 0).all())
          and not ok2 and bool((f2 == 0).all()) and not ok3 and bool((f3 == 0).all()))
    return {"mean": float(f[:L].mean()), "std": float(f[:L].std()), "static_valid": ok2, "nan_valid": ok3, "pass": ok}


def u13():
    import train_500ep as TR
    cfg = TR.load_config(S5 / "config_500ep.json")
    bad = dict(cfg); bad["episodes"], bad["n_groups"] = 400, 100
    p = OUT / "bad_config.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    try:
        TR.load_config(p)
        rejected = False
    except AssertionError:
        rejected = True
    return {"main_config_ok": cfg["episodes"] == 500, "non_500_rejected": rejected, "pass": cfg["episodes"] == 500 and rejected}


def u14():
    try:
        C.lmdb_path("test")
        return {"pass": False}
    except ValueError as e:
        return {"error_message": str(e), "opened": list(C.OPENED_SPLITS), "pass": "test" not in C.OPENED_SPLITS}


# ------------------------------------------------------------------------------------- integration tests
def i1(ctx):
    res = {}
    for s in ("body", "hand"):
        p = OUT / f"ref_{s}.pt"
        if not p.exists():
            subprocess.run(PY + [str(Path(__file__)), "--dump-ref", str(p), "--stream", s], check=True)
        ref = torch.load(p, weights_only=False)[s]
        embed, cond = ctx.batch("dev", range(32))[s]
        y = cond["y"]
        res[s] = {"embed_equal": bool(torch.equal(embed.cpu(), ref["embed"])), "mask_equal": bool(torch.equal(y["mask"], ref["mask"])),
                  "lengths_equal": bool(torch.equal(y["lengths"], ref["lengths"])), "text_equal": list(y["text"]) == ref["text"],
                  "keyframes_equal": [list(k) for k in y["keyframes"]] == ref["keyframes"],
                  "names_equal": list(y["video_names"]) == ref["video_names"]}
    return {**res, "pass": all(all(v.values()) for v in res.values())}


def i2(ctx):
    sys.path.insert(0, str(C.ROOT / "experiments" / "stage4" / "e2e"))
    import e2e_run as E2E
    same_noise = all(torch.equal(C.noise(10_000_000, j, 1), E2E.base_noise("A0", j, 1)) for j in (0, 7, 31))
    prep = ctx.batch("dev", range(32))
    nz = torch.stack([C.noise(10_000_000, j, 1) for j in range(32)]).cuda()
    xb = ctx.gen("body", prep, list(range(32)), nz[:, :60]).cpu().numpy()
    hn = torch.stack([nz[:, 60:150], nz[:, 150:240]], 1).reshape(64, 90, 304)
    xh = ctx.gen("hand", prep, list(range(64)), hn).cpu().numpy().reshape(32, 2, 90, 304)
    a0 = np.load(C.ROOT / "experiments/stage4/e2e/dumps/A0/k01.npz")
    db, dh = float(np.abs(xb - a0["body"]).max()), float(np.abs(xh - a0["hand"]).max())
    return {"same_noise_formula": same_noise, "body_max_abs": db, "hand_max_abs": dh, "tolerance": 1e-4,
            "bitwise_body": db == 0.0, "bitwise_hand": dh == 0.0, "pass": same_noise and db <= 1e-4 and dh <= 1e-4}


def i3(ctx):
    p = policy().cuda()
    with torch.no_grad():
        p.b.fill_(-1e4)
    prep = ctx.batch("dev", [0, 1])
    nz = torch.stack([C.noise(40_000_000, j, 1) for j in (0, 1)]).cuda()
    Ls = [ctx.meta("dev", j)["L"] for j in (0, 1)]
    xb = ctx.gen("body", prep, [0, 1], nz[:, :60]).cpu().numpy()
    s_hat = torch.as_tensor(np.stack([C.arm_feature(xb[a], Ls[a])[0] for a in range(2)])).cuda()
    with torch.no_grad():
        mu = p.mu(s_hat, Ls)
    xi = nz[:, 150:240]
    xh = ctx.gen("hand", prep, [0, 2, 1, 3, 1, 3], torch.cat([nz[:, 60:150], xi + mu, xi]))
    eq = bool(torch.equal(xh[2:4], xh[4:6]))
    return {"mu_zero": bool((mu == 0).all()), "controlled_equals_uncoupled_bitwise": eq, "pass": eq and bool((mu == 0).all())}


REQUIRED_EPISODE_KEYS = ("episode", "group", "clip", "seed", "noise_id", "action", "log_prob", "controlled", "uncoupled_twin",
                         "r_ah", "s3_undefined_primary", "c_raw", "c", "a3_undefined", "lambda_used", "R", "baseline", "advantage")
REQUIRED_GROUP_KEYS = ("loss", "grad_norm_pre_clip", "grad_norm_post_clip", "param_norm", "update_norm", "seconds", "gpu_peak_alloc_GiB",
                       "lambda_after", "beta_after", "kl_mean")


def numeric_diff(a, b, path=""):
    """Max abs difference over matching numeric leaves; structural mismatch -> inf."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return float("inf")
        return max([numeric_diff(a[k], b[k], path + "." + k) for k in a if k not in ("seconds", "gpu_peak_alloc_GiB")] or [0.0])
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return float("inf")
        return max([numeric_diff(x, y) for x, y in zip(a, b)] or [0.0])
    if isinstance(a, bool) or isinstance(b, bool):
        return 0.0 if a == b else float("inf")
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) and math.isnan(b):
            return 0.0
        return abs(a - b)
    return 0.0 if a == b else float("inf")


def i4():
    runs = {}
    for tag in ("a", "b"):
        d = OUT / f"mini_train_{tag}"
        r = subprocess.run(PY + [str(S5 / "train_500ep.py"), "--config", str(HERE / "config_test.json"), "--out", str(d)],
                           capture_output=True, text=True)
        (OUT / f"mini_train_{tag}.log").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr[-5000:], encoding="utf-8")
        runs[tag] = {"rc": r.returncode, "dir": d}
    ra = json.loads((runs["a"]["dir"] / "run.json").read_text(encoding="utf-8"))
    ea = json.loads((runs["a"]["dir"] / "episodes.json").read_text(encoding="utf-8"))
    ga = json.loads((runs["a"]["dir"] / "groups.json").read_text(encoding="utf-8"))
    eb = json.loads((runs["b"]["dir"] / "episodes.json").read_text(encoding="utf-8"))
    ga_b = json.loads((runs["b"]["dir"] / "groups.json").read_text(encoding="utf-8"))
    ckpts = sorted(p.name for p in (runs["a"]["dir"] / "checkpoints").glob("*.pt"))
    keys_ok = all(all(k in e for k in REQUIRED_EPISODE_KEYS) for e in ea) and all(all(k in g for k in REQUIRED_GROUP_KEYS) for g in ga)
    finite = all(math.isfinite(e["R"]) and math.isfinite(e["log_prob"]) and math.isfinite(e["advantage"]) for e in ea)
    det = numeric_diff(ea, eb)
    det_g = numeric_diff(ga, ga_b)
    sec_per_group = float(np.mean([g["seconds"] for g in ga]))
    ok = (runs["a"]["rc"] == 0 and runs["b"]["rc"] == 0 and ra["status"] == "completed" and len(ea) == 8 and keys_ok and finite
          and ra["model_weights_unchanged"] and ra["model_trainable_params"] == 0 and ra["opened_splits"] == ["train"]
          and ckpts == ["update_000.pt", "update_001.pt", "update_002.pt"] and det <= 1e-4 and det_g <= 1e-4
          and (OUT / "mini_train_a" / "episodes.csv").exists())
    return {"return_codes": [runs["a"]["rc"], runs["b"]["rc"]], "status": ra["status"], "episodes": len(ea), "keys_ok": keys_ok,
            "finite": finite, "weights_unchanged": ra["model_weights_unchanged"], "trainable": ra["model_trainable_params"],
            "opened_splits": ra["opened_splits"], "checkpoints": ckpts, "determinism_max_abs_diff_episodes": det,
            "determinism_max_abs_diff_groups": det_g, "seconds_per_group": sec_per_group,
            "projected_500ep_minutes": sec_per_group * 125 / 60 + ra["seconds"] / 60 - sec_per_group * 2 / 60,
            "gpu_peak_alloc_GiB": ra["gpu_peak_alloc_GiB"], "gpu_peak_reserved_GiB": ra["gpu_peak_reserved_GiB"],
            "run_seconds": ra["seconds"], "S3_count": sum(e["s3_undefined_primary"] for e in ea),
            "A3_count": sum(sum(e["a3_undefined"].values()) for e in ea), "pass": ok}


def i5():
    d = OUT / "mini_eval"
    ck = OUT / "mini_train_a" / "checkpoints"
    r = subprocess.run(PY + [str(S5 / "evaluate.py"), "--config", str(HERE / "config_test.json"), "--ckpt-init", str(ck / "update_000.pt"),
                             "--ckpt-final", str(ck / "update_002.pt"), "--out", str(d)], capture_output=True, text=True)
    (OUT / "mini_eval.log").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr[-5000:], encoding="utf-8")
    res = json.loads((d / "eval_results.json").read_text(encoding="utf-8"))
    recs = json.loads((d / "eval_samples.json").read_text(encoding="utf-8"))
    left_same = res["per_stream"]["hand_L.A"]["left_identical_across_conditions"]
    by = {(x["clip"], x["cond"]): x for x in recs}
    unc_vs_init_differ = any(by[(j, "uncoupled")]["R"]["hand_R"]["A"] != by[(j, "initial")]["R"]["hand_R"]["A"] for j in (0, 1))
    ok = (r.returncode == 0 and len(recs) == 6 and "pre_registered" in res["verdict"] and left_same and unc_vs_init_differ
          and all("J" in x for x in recs) and res["run"]["opened_splits"] == ["dev"] and res["run"]["model_weights_unchanged"]
          and "coord_ah_J_R" in res["J_space_descriptive"] and res["kl_per_frame"]["uncoupled"]["max"] == 0.0)
    return {"rc": r.returncode, "records": len(recs), "verdict_field": res["verdict"]["pre_registered"], "left_identical": left_same,
            "uncoupled_vs_initial_differ": unc_vs_init_differ, "opened_splits": res["run"]["opened_splits"],
            "kl": res["kl_per_frame"], "eval_seconds": res["run"]["seconds"], "pass": ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", action="store_true")
    ap.add_argument("--integration", action="store_true")
    ap.add_argument("--dump-ref")
    ap.add_argument("--stream")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.dump_ref:
        us = C.us
        embed, cond = us.load_first_batch(a.stream, us.build_cfg(a.stream))
        y = cond["y"]
        torch.save({a.stream: {"embed": embed.cpu(), "mask": y["mask"], "lengths": y["lengths"], "text": list(y["text"]),
                               "keyframes": [list(k) for k in y["keyframes"]], "video_names": list(y["video_names"])}}, a.dump_ref)
        return
    if a.unit:
        for name, fn in (("U1 log-prob exact", u1), ("U2 beta=0 -> mu=0, eps=xi bitwise", u2), ("U3 padded frames", u3),
                         ("U4 KL cap + formula", u4), ("U5 Stiefel", u5), ("U6 RLOO", u6), ("U7 score-function unbiased (MC z-test)", u7),
                         ("U7b training-loss gradient", u7b), ("U8 S-3 / A3", u8), ("U9 dual ascent", u9),
                         ("U10 frozen target + thresholds", u10), ("U11 sampler + seeds", u11), ("U12 arm feature", u12),
                         ("U13 config guard (500 = 125 x 4)", u13), ("U14 split guard (no test)", u14)):
            check(name, fn)
        tag = "unit"
    else:
        ctx = C.Ctx5({"dev": list(range(32))})
        check("I1 loader equivalence vs load_first_batch", lambda: i1(ctx))
        check("I2 reproduces E2e A0 k=1 dumps", lambda: i2(ctx))
        check("I3 beta=0 -> controlled = uncoupled bitwise", lambda: i3(ctx))
        check("I3b dev only opened, weights frozen", lambda: {"opened": list(C.OPENED_SPLITS), "trainable": ctx.n_trainable(),
                                                             "pass": C.OPENED_SPLITS == ["dev"] and ctx.n_trainable() == 0})
        del ctx
        torch.cuda.empty_cache()
        check("I4 mini training x2 (logging, determinism, frozen weights, splits)", i4)
        check("I5 mini evaluation (3 conditions, R + J)", i5)
        tag = "integration"
    summary = {"tests": RESULTS, "passed": sum(r["pass"] for r in RESULTS), "total": len(RESULTS)}
    (OUT / f"{tag}_tests.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(f"{tag}: {summary['passed']}/{summary['total']}")


if __name__ == "__main__":
    main()
