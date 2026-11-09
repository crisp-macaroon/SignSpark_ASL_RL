"""Stage 4 E2e: Gaussian noise-controller technical feasibility (rev. 4.0 §15.3–15.4; checklist Step 2).

Fixed couplings / side scales over the frozen released samplers; no learned controller, no training,
no optimiser. Dev clips 0..31 of the dev-256 subset, GF regime, reference length (oracle, A1).
Sampler: the E2d-validated unrolled harness (bitwise equal to upstream decode), no grad, fp32, default flags.
Every generated rotation is saved to --dumps for E2e-J. Released-checkpoint results, not a paper reproduction.

Run order (frozen, §15.3.1):
  0 references only: t*_256 + 95% CI -> branch R1/R2/R3 and delta_S2; T1 (a) analytic; T1 synthetic margins
  1 T0 (a) harness vs upstream decode (A0 noise k=1), (b) [same call], (c) BH body regenerated vs A0 body
  2 A0, A0' at n = 8; T2 calibration half-width h
  3 calibration loop n in {8, 16, 32} on A0/A0' only; n* frozen before step 4
  4 gate conditions at n*: T1, T2, T5-A          (stop rules below)
  5 remaining BH (n = 8)   6 remaining LR (n = 8)   7 SS (n = 8) unless R3
Stops: T0 fail; T1 fail; T2 fail/straddle; T5-A fail (any BH/LR condition); cap 1.5 h; dump write failure.
T2 calibration-inconclusive (h > 1.5% at n = 32) continues with theory-conditional wording.

    python -E -s experiments/stage4/e2e/e2e_run.py --out experiments/stage4/e2e/out --dumps experiments/stage4/e2e/dumps
    (--plan prints the frozen plan and exits without loading any model or data)
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "e2d"))
import metrics as M  # noqa: E402
import noise_transform as NT  # noqa: E402
import stats as S  # noqa: E402

ROOT = HERE.parents[2]
J = 32
N_DEFAULT, N_LIST = 8, (8, 16, 32)
H_MAX = 1.5  # % T2 calibration half-width
CAP_S = 90 * 60
NOISE_BASE = {"A0": 10_000_000, "A0p": 20_000_000}  # seed = base + 1000*j + k  (j clip 0..31, k noise 1..32)
BOOT_SEED = 0
DEV256_HAND = ROOT / "experiments/baseline/runs/hand/h2s_dev256_gf_s10_N8/debug0_eulerstepsize10_can8_anchor0_samples/seed102_clampstep0_h2s_dev256_gf_s10_N8.npy"
T1_NULL_SETS = 1000


class Stop(Exception):
    pass


def jdump(p, obj):
    p.write_text(json.dumps(obj, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)), encoding="utf-8")


def base_noise(set_name, j, k):
    g = torch.Generator().manual_seed(NOISE_BASE[set_name] + 1000 * j + k)
    return torch.randn(240, 304, generator=g)


def step0_references():
    """t*_256 and its CI from existing dev-256 reference hands (no generation); refs for the 32 E2e clips."""
    d = np.load(DEV256_HAND, allow_pickle=True).item()  # our own dump (dict pickled by np.save)
    gt, lens, names = d["gt_poses"][0], d["lengths"][0], d["video_names"][0]
    recs = [M.reference_record(gt[2 * i], gt[2 * i + 1], int(lens[2 * i])) for i in range(256)]
    X = np.array([r["X"] for r in recs])
    tb = np.mean(X[S.boot_idx(256, BOOT_SEED)], 1)
    t256, lo, hi = float(X.mean()), S.pct(tb, 2.5), S.pct(tb, 97.5)
    excl0 = not (lo <= 0 <= hi)
    if abs(t256) >= 0.20 and excl0:
        branch, delta = "R1", 0.05
    elif 0.10 <= abs(t256) < 0.20 and excl0:
        branch, delta = "R2", abs(t256) / 4
    else:
        branch, delta = "R3", 0.025
    ref32 = {"X": X[:J], "A_L": np.array([r["A_L"] for r in recs[:J]]), "A_R": np.array([r["A_R"] for r in recs[:J]]),
             "names": [str(names[2 * i]) for i in range(J)], "lengths": [int(lens[2 * i]) for i in range(J)]}
    phi_ref = np.stack([r["phi_L"] for r in recs])
    return {"t256": t256, "t256_ci95": [lo, hi], "branch": branch, "delta_S2": delta,
            "formula_delta": min(0.05, max(0.025, abs(t256) / 4))}, ref32, phi_ref


def frame_structure(lengths, n):
    """Indices of active frames and of consecutive active-frame pairs for n noises x 32 clips (sample-major)."""
    rows, pa, pb, off = [], [], [], 0
    for _k in range(n):
        for L in lengths:
            pa.append(np.arange(off, off + L - 1)); pb.append(np.arange(off + 1, off + L))
            off += L
    return off, np.concatenate(pa), np.concatenate(pb)


def t1_layout(spec):
    blocks = {"b": slice(0, 60), "L": slice(60, 150), "R": slice(150, 240)}
    m = NT.build(spec)
    if spec["kind"] == "LR":
        cross = [(slice(150, 240), slice(60, 150), m["K_RL"])]
    else:
        cross = [(slice(60, 150), slice(0, 60), m["K_L"]), (slice(150, 240), slice(0, 60), m["K_Rb"])]
    return blocks, cross


def t1_null(spec, lengths, sets=T1_NULL_SETS, seed=777):
    blocks, cross = t1_layout(spec)
    cross0 = [(r, c, None) for r, c, _ in cross]
    n, pa, pb = frame_structure(lengths, N_DEFAULT)
    pa, pb = torch.as_tensor(pa, device="cuda"), torch.as_tensor(pb, device="cuda")
    g = torch.Generator(device="cuda").manual_seed(seed)
    out = []
    for _ in range(sets):
        X = torch.randn(n, 240, generator=g, device="cuda", dtype=torch.float64)
        out.append(S.t1_stats(X, pa, pb, blocks, cross0))
    return out


class Runner:
    def __init__(self, out, dumps):
        self.out, self.dumps = out, dumps
        self.t_start = time.time()
        self.res = {"label": "released-checkpoint results, dev clips 0..31 (GF, oracle length); not a paper reproduction",
                    "steps": {}, "status": "running"}
        self.data = {}   # condition -> {metric: [J, n]} ; phi_L [J, n, 30]
        self.body = {}   # set name -> {k: np.array [J, 60, 304]}

    def log(self, *a):
        msg = f"[{time.time() - self.t_start:7.1f}s] " + " ".join(str(x) for x in a)
        print(msg, flush=True)

    def check_cap(self, what):
        if time.time() - self.t_start > CAP_S:
            raise Stop(f"1.5 h cap reached before {what}")

    def save(self):
        self.res["elapsed_s"] = round(time.time() - self.t_start, 1)
        jdump(self.out / "results.json", self.res)

    # ------------------------------------------------------------ models
    def load_models(self):
        import unrolled_sampler as us
        self.us = us
        self.m, self.flow, self.cond, self.embed = {}, {}, {}, {}
        for s in ("body", "hand"):
            cfg = us.build_cfg(s)
            self.m[s], self.flow[s] = us.load_model(s, cfg)
            self.embed[s], self.cond[s] = us.load_first_batch(s, cfg)
            self.m[s].text_enc_model.to("cpu")
        self.orig_encode = {s: self.m[s].encode_text for s in self.m}  # bound upstream methods, kept for T0
        torch.cuda.empty_cache()
        self.lengths = [int(v) for v in self.cond["body"]["y"]["lengths"]]
        names = self.cond["body"]["y"]["video_names"]
        ch = self.cond["hand"]["y"]
        # F2 programmatic: L/R rows share text, length, mask; GF obs_mask all False
        f2 = all(ch["text"][2 * i] == ch["text"][2 * i + 1] and int(ch["lengths"][2 * i]) == int(ch["lengths"][2 * i + 1])
                 and torch.equal(ch["mask"][2 * i], ch["mask"][2 * i + 1]) for i in range(J))
        f2 = f2 and not self.cond["hand"]["obs_mask"].any().item() and not self.cond["body"]["obs_mask"].any().item()
        return names, f2

    def with_text_encoder(self, s, fn):
        """Run fn with stream s's M-CLIP on the GPU and the original encode_text (upstream path)."""
        m = self.m[s]
        m.text_enc_model.to("cuda")
        try:
            return fn()
        finally:
            m.text_enc_model.to("cpu")
            torch.cuda.empty_cache()

    def cache_texts(self):
        """Cache each stream's batch text embedding (one M-CLIP, identical in all checkpoints: E2d-H)."""
        for s in ("body", "hand"):
            self.m[s].encode_text = self.orig_encode[s]
            self.with_text_encoder(s, lambda s=s: self.us.cache_text(self.m[s], self.cond[s]["y"]["text"]))

    def flags(self):
        return {"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32, "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                "float32_matmul_precision": torch.get_float32_matmul_precision(), "cudnn_benchmark": torch.backends.cudnn.benchmark,
                "cudnn_deterministic": torch.backends.cudnn.deterministic, "dtype": "float32", "device": torch.cuda.get_device_name(0),
                "torch": torch.__version__,
                "training_any": any(mod.training for s in self.m for mod in self.m[s].modules())}

    # ------------------------------------------------------------ generation
    @torch.no_grad()
    def gen_body(self, eps_b):
        return self.us.unrolled_decode(self.m["body"], eps_b, self.cond["body"], self.embed["body"])

    @torch.no_grad()
    def gen_hand(self, eps_l, eps_r):
        hn = torch.stack([eps_l, eps_r], dim=1).reshape(2 * J, 90, 304)
        out = self.us.unrolled_decode(self.m["hand"], hn, self.cond["hand"], self.embed["hand"])
        return out.reshape(J, 2, 90, 304)

    def eps_tilde(self, spec, set_name, k):
        eps0 = torch.stack([base_noise(set_name, j, k) for j in range(J)]).cuda()
        m = NT.build(spec)
        et = NT.apply(m, eps0, self.lengths)
        T = eps0.shape[-1]
        pad = torch.arange(T, device="cuda")[None, None, :] >= torch.as_tensor(self.lengths, device="cuda")[:, None, None]
        assert torch.equal(et.expand_as(eps0)[pad.expand_as(eps0)], eps0[pad.expand_as(eps0)]), "padded frames changed"
        return eps0, et

    def generate(self, spec, ks):
        """Generate condition `spec` for noise indices ks; save dumps; append per-sample records."""
        name = spec["name"]
        set_name = "A0p" if name == "A0p" else "A0"
        ddir = self.dumps / name
        ddir.mkdir(parents=True, exist_ok=True)
        dat = self.data.setdefault(name, {})
        for k in ks:
            self.check_cap(f"{name} k={k}")
            eps0, et = self.eps_tilde(spec, set_name, k)
            if spec["kind"] == "base":
                xb = self.gen_body(et[:, :60]).cpu().numpy()
                self.body.setdefault(set_name, {})[k] = xb
            else:
                xb = self.body["A0"][k]  # z_b = eps_b: body sample-wise identical to A0 (T0 (c))
            xh = self.gen_hand(et[:, 60:150], et[:, 150:]).cpu().numpy()
            try:
                arr = {"hand": xh.astype(np.float32)}
                if spec["kind"] == "base":
                    arr["body"] = xb.astype(np.float32)
                np.savez(ddir / f"k{k:02d}.npz", **arr)
            except OSError as e:
                raise Stop(f"dump write failed: {e}")
            recs = [M.sample_record(xb[j], xh[j, 0], xh[j, 1], self.lengths[j]) for j in range(J)]
            for key in recs[0]:
                if key == "L":
                    continue
                v = np.array([r[key] for r in recs])
                dat.setdefault(key, {})[k] = v
        self.log("generated", name, "k =", list(ks))

    def arrays(self, name, ks):
        """Per-condition data restricted to noises ks: metric -> [J, len(ks)] (phi_L -> [J, n, 30])."""
        d = self.data[name]
        return {key: np.stack([d[key][k] for k in ks], axis=1) for key in d}

    # ------------------------------------------------------------ steps
    def run(self):
        self.out.mkdir(parents=True, exist_ok=True)
        self.dumps.mkdir(parents=True, exist_ok=True)
        st = self.res["steps"]
        specs = {c["name"]: c for c in NT.CONDITIONS}
        idx = S.boot_idx(J, BOOT_SEED)

        # step 0 ------------------------------------------------------------------------------
        try:
            s0, ref32, phi_ref = step0_references()
        except Exception as e:  # noqa: BLE001
            raise Stop(f"t*_256 not computable: {e}")
        if not np.isfinite(s0["t256"]):
            raise Stop("t*_256 not finite")
        s0["T1a_analytic"] = {c["name"]: NT.analytic_checks(NT.build(c)) for c in NT.CONDITIONS}
        s0["KL_per_frame"] = {c["name"]: NT.kl_per_frame(NT.build(c)) for c in NT.CONDITIONS}
        s0["ref32_names"], s0["ref32_lengths"] = ref32["names"], ref32["lengths"]
        st["0"] = s0
        self.save()
        self.log("step0", s0["branch"], "t256", round(s0["t256"], 4), s0["t256_ci95"], "delta_S2", s0["delta_S2"])
        if not all(v["pass"] for v in s0["T1a_analytic"].values()):
            raise Stop("T1 (a) analytic check failed")
        delta = s0["delta_S2"]
        run_ss = s0["branch"] != "R3"

        names, f2 = self.load_models()
        if names != ref32["names"] or self.lengths != ref32["lengths"]:
            raise Stop("loaded clips differ from the dev-256 references")
        cal = {}
        for g in NT.GATE:
            nulls = t1_null(specs[g], self.lengths)
            cal[g] = S.t1_calibrate(nulls)
            if not cal[g]["calibrated"]:
                raise Stop(f"T1 synthetic calibration for {g} cannot reach < 1% within the caps (P-1)")
        s0["T1_calibration"] = {g: {k: v for k, v in c.items()} for g, c in cal.items()}
        self.save()
        self.log("step0 T1 margins", {g: c["margins"] for g, c in cal.items()})

        # step 1 ------------------------------------------------------------------------------
        self.cache_texts()
        flags = self.flags()
        if flags["training_any"]:
            raise Stop("a module is in training mode (F5)")
        eps0, et = self.eps_tilde(specs["A0"], "A0", 1)
        self.generate(specs["A0"], [1])
        up = {}
        for s in ("body", "hand"):  # T0 (b): upstream decode, its own M-CLIP, same noise
            def run_up(s=s):
                self.m[s].encode_text = self.orig_encode[s]
                noise = et[:, :60] if s == "body" else torch.stack([et[:, 60:150], et[:, 150:]], 1).reshape(2 * J, 90, 304)
                with torch.no_grad():
                    r, _ = self.flow[s].decode(self.m[s], noise=noise, keyframe_mask=self.cond[s]["obs_mask"],
                                               x_embed=self.embed[s], model_kwargs=self.cond[s],
                                               ode_package="torchdiffeq", ode_stepnum=10)
                return r.cpu().numpy()
            up[s] = self.with_text_encoder(s, run_up)
        self.cache_texts()  # back to cached embeddings for all harness generation
        hand_a0 = np.load(self.dumps / "A0" / "k01.npz")["hand"].reshape(2 * J, 90, 304)
        t0a = {"body": float(np.abs(up["body"] - self.body["A0"][1]).max()), "hand": float(np.abs(up["hand"] - hand_a0).max())}
        _, etb = self.eps_tilde(specs[NT.GATE[0]], "A0", 1)
        xb_bh = self.gen_body(etb[:, :60]).cpu().numpy()
        t0c = float(np.abs(xb_bh - self.body["A0"][1]).max())
        st["1"] = {"T0a_max_abs": t0a, "T0c_body_identity_max_abs": t0c, "F2_shared_inputs": f2, "flags": flags,
                   "pass": max(t0a.values()) <= 1e-4 and t0c <= 1e-5 and f2}
        self.save()
        self.log("step1 T0", st["1"]["pass"], t0a, t0c)
        if not st["1"]["pass"]:
            raise Stop("T0 failed")

        # steps 2-3 ---------------------------------------------------------------------------
        self.generate(specs["A0"], range(2, N_DEFAULT + 1))
        self.generate(specs["A0p"], range(1, N_DEFAULT + 1))
        calib = []
        n_star, inconclusive = None, False
        for n in N_LIST:
            if n > N_DEFAULT:
                prev = calib[-1]["n"]
                self.generate(specs["A0"], range(prev + 1, n + 1))
                self.generate(specs["A0p"], range(prev + 1, n + 1))
            ks = list(range(1, n + 1))
            t2c = S.t2(self.arrays("A0p", ks), self.arrays("A0", ks), idx)
            calib.append({"n": n, "h_pct": t2c["_h_pct"], "detail": t2c})
            self.log("calibration n", n, "h%", round(t2c["_h_pct"], 3))
            if t2c["_h_pct"] <= H_MAX:
                n_star = n
                break
        if n_star is None:
            n_star, inconclusive = 32, True
        st["2_3"] = {"calibration": calib, "n_star": n_star, "calibration_inconclusive": inconclusive,
                     "A0_T5A_precision": None}
        a0_t5 = S.t5a(self.arrays("A0", list(range(1, N_DEFAULT + 1))), idx, delta)
        st["2_3"]["A0_T5A_precision"] = {"half_width_mu_n8": a0_t5["half_width_mu"], "threshold_0.8_delta": 0.8 * delta,
                                          "T5A_expected_inconclusive_at_n8": a0_t5["half_width_mu"] > 0.8 * delta}
        self.save()

        # step 4: gate conditions at n* ---------------------------------------------------------
        ks_star = list(range(1, n_star + 1))
        st["4"] = {}
        for g in NT.GATE:
            self.generate(specs[g], ks_star)
            blocks, cross = t1_layout(specs[g])
            n_fr, pa, pb = frame_structure(self.lengths, N_DEFAULT)
            frames = []
            for k in range(1, N_DEFAULT + 1):
                _, et = self.eps_tilde(specs[g], "A0", k)
                for j in range(J):
                    frames.append(et[j, :, : self.lengths[j]].T.double())
            X = torch.cat(frames)
            t1s = S.t1_stats(X, torch.as_tensor(pa, device="cuda"), torch.as_tensor(pb, device="cuda"), blocks, cross)
            t1p = S.t1_pass(t1s, cal[g]["margins"])
            t2r = S.t2(self.arrays(g, ks_star), self.arrays("A0", ks_star), idx)
            t5 = S.t5a(self.arrays(g, ks_star), idx, delta)
            st["4"][g] = {"T1_stats": t1s, "T1_margins": cal[g]["margins"], "T1_pass": all(t1p.values()), "T1_detail": t1p,
                          "T2": t2r, "T5A": t5, "n": n_star}
            self.save()
            self.log("step4", g, "T1", all(t1p.values()), "T2", t2r["_overall"], "T5A", t5["S2_outcome"], t5["S1_outcome"])
            if not all(t1p.values()):
                raise Stop(f"T1 failed for {g}")
            if t2r["_overall"] in ("fail", "straddle"):
                raise Stop(f"T2 {t2r['_overall']} for {g}")
            if "fail" in (t5["S2_outcome"], t5["S1_outcome"]):
                raise Stop(f"T5-A fail for {g}")
        st["4"]["T2_wording"] = ("theory-conditional (Theorem 3); empirical eight-metric check inconclusive"
                                 if inconclusive else "eight-metric check confirmed within +-5%")

        # steps 5-7 -----------------------------------------------------------------------------
        ks8 = list(range(1, N_DEFAULT + 1))
        rest = [c for c in NT.CONDITIONS if c["kind"] in ("BH", "BH_arm") and c["name"] not in NT.GATE] + \
               [c for c in NT.CONDITIONS if c["kind"] == "LR" and c["name"] not in NT.GATE]
        st["5_6"] = {}
        for c in rest:
            self.generate(c, ks8)
            t5 = S.t5a(self.arrays(c["name"], ks8), idx, delta)
            st["5_6"][c["name"]] = {"T5A": t5}
            self.save()
            if "fail" in (t5["S2_outcome"], t5["S1_outcome"]):
                raise Stop(f"T5-A fail for {c['name']}")
        st["7"] = {"run": run_ss}
        if run_ss:
            for c in [c for c in NT.CONDITIONS if c["kind"] == "SS"]:
                self.generate(c, ks8)
        else:
            st["7"]["note"] = "R3: SS conditions removed; P1b target-degenerate; report to the user"
        self.save()
        self.analyse(specs, idx, delta, ref32, phi_ref, run_ss)

    def analyse(self, specs, idx, delta, ref32, phi_ref, run_ss):
        """T3, T4, T5-B, T6, energy distance, KL efficiency, on the first 8 noises (paired with A0)."""
        ks8 = list(range(1, N_DEFAULT + 1))
        a0 = self.arrays("A0", ks8)
        kl = self.res["steps"]["0"]["KL_per_frame"]
        meanL = float(np.mean(self.lengths))
        an = {"T3": {}, "T4": {}, "T5B": {}, "energy": {}}
        for name in [c["name"] for c in NT.CONDITIONS if c["kind"] in ("BH", "BH_arm", "LR")]:
            d = self.arrays(name, ks8)
            row = {k: S.paired_delta(d, a0, k, idx) for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr")}
            row["KL_per_sample_mean"] = (kl[name][0] + kl[name][1]) * meanL
            (an["T3"] if specs[name]["kind"] != "LR" else an["T4"])[name] = row
        side_key = {"R": "coord_arm_rhand", "L": "coord_arm_lhand"}
        t3 = S.t3_verdict(  # P-4: existence (registered, either side) kept separate from bilateral; sides named
            {s: an["T3"]["BH-r60-k0.9-seed0"][k] for s, k in side_key.items()},
            {s: [an["T3"][f"BH-r60-k{x}-seed0"][k]["delta"] for x in (0.3, 0.6, 0.9)] for s, k in side_key.items()},
            {s: [an["T3"][f"BH-r60-k0.9-seed{x}"][k] for x in (0, 1, 2)] for s, k in side_key.items()})
        t3["transmission_pass"] = t3["existence_registered_criterion"]
        t3["specificity_LR_max_abs_arm_hand"] = max(abs(an["T4"][n][k]["delta"]) for n in an["T4"] for k in side_key.values())
        t3["specificity_pass"] = t3["specificity_LR_max_abs_arm_hand"] <= 0.02
        bh_arm, bh_r60 = self.arrays("BH-arm12-k0.9", ks8), self.arrays("BH-r60-k0.9-seed0", ks8)
        t3["efficiency_arm12_over_r60"] = {  # P-11: descriptive, with bootstrap CIs
            s: S.efficiency(bh_arm, bh_r60, a0, k, sum(kl["BH-arm12-k0.9"]), sum(kl["BH-r60-k0.9-seed0"]), self.lengths, idx)
            for s, k in side_key.items()}
        an["T3_summary"] = t3
        g4 = an["T4"]["LR-r90-k0.9-seed0"]["coord_lr"]
        an["T4_summary"] = {"transmission_pass": S.transmission(g4),
                            "orientation_pass_count": sum(S.transmission(an["T4"][f"LR-r90-k0.9-seed{s}"]["coord_lr"]) for s in (0, 1, 2)),
                            "induced_under_BH": {n: an["T3"][n]["coord_lr"] for n in an["T3"]}}
        n_star = self.res["steps"]["2_3"]["n_star"]
        ks_star = list(range(1, n_star + 1))
        a0_star = self.arrays("A0", ks_star)
        an["gate_at_n_star_descriptive"] = {  # P-10: descriptive only; gating T3/T4 above use n = 8
            "n_star": n_star, "note": "descriptive; the registered T3/T4 verdicts use the first 8 noises",
            **{g: {k: S.paired_delta(self.arrays(g, ks_star), a0_star, k, idx)
                   for k in ("coord_arm_rhand", "coord_arm_lhand", "coord_lr")} for g in NT.GATE}}
        if run_ss:
            a0p = self.arrays("A0p", ks8)
            for c in [c for c in NT.CONDITIONS if c["kind"] == "SS"]:
                cd = self.arrays(c["name"], ks8)
                an["T5B"][c["name"]] = S.dominance(cd, a0, a0p, ref32, phi_ref, c["sigma"], idx, delta)
                an["T5B"][c["name"]]["extreme_meanjoint_descriptive"] = {  # P-2: descriptive; gating uses any-joint
                    s: S.paired_delta(cd, a0, f"extreme_frac_meanjoint_{s}", idx) for s in ("L", "R")}
                self.log("T5B", c["name"], an["T5B"][c["name"]]["D_c"]["pass"])
            an["T5B_summary"] = {"M-C/sigma feasible at D-c (exploratory)": any(v["D_c"]["pass"] for v in an["T5B"].values())}
        for g in NT.GATE:  # non-gating energy-distance diagnostic on the T2 features
            ks = list(range(1, self.res["steps"]["2_3"]["n_star"] + 1))
            fc = np.stack([self.arrays(g, ks)[k].ravel() for k in S.T2_METRICS], 1)
            fa = np.stack([self.arrays("A0", ks)[k].ravel() for k in S.T2_METRICS], 1)
            mu, sd = np.vstack([fc, fa]).mean(0), np.vstack([fc, fa]).std(0)
            clip = np.repeat(np.arange(J), len(ks))
            ok = np.isfinite(fc).all(1) & np.isfinite(fa).all(1)
            an["energy"][g] = S.energy_distance((fc[ok] - mu) / sd, (fa[ok] - mu) / sd, clip[ok], clip[ok])
        self.res["analysis"] = an
        self.res["status"] = "completed"
        self.save()


def plan():
    return {"conditions": [c["name"] for c in NT.CONDITIONS], "gate": NT.GATE, "clips": "dev-256 clips 0..31",
            "noise_seeds": {k: f"{v} + 1000*j + k" for k, v in NOISE_BASE.items()}, "bootstrap": {"B": S.B_BOOT, "seed": BOOT_SEED},
            "n_default": N_DEFAULT, "n_list": N_LIST, "h_max_pct": H_MAX, "cap_s": CAP_S,
            "T1_margins_registered_initial": S.T1_MARGINS, "T1_caps_registered": S.T1_CAPS,
            "T1_lag1": "registered 0.03, no cap registered, never widened (P-1)", "T1_procedure": S.T1_PROCEDURE, "T1_null_sets": T1_NULL_SETS, "dev256_reference_dump": str(DEV256_HAND)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "experiments/stage4/e2e/out"))
    ap.add_argument("--dumps", default=str(ROOT / "experiments/stage4/e2e/dumps"))
    ap.add_argument("--plan", action="store_true", help="print the frozen plan and exit (loads nothing)")
    args = ap.parse_args()
    if args.plan:
        print(json.dumps(plan(), indent=1))
        return
    out, dumps = Path(args.out), Path(args.dumps)
    if (out / "results.json").exists():
        sys.exit("results.json exists: refusing to overwrite a previous E2e run")
    free = shutil.disk_usage(dumps.resolve().anchor).free / 2**30  # campaign fix: relative path had an empty anchor
    if free < 10:
        sys.exit(f"only {free:.1f} GiB free; need >= 10 GiB")
    r = Runner(out, dumps)
    r.res["plan"] = plan()
    try:
        r.run()
    except Stop as e:
        r.res["status"] = f"stopped: {e}"
        r.log("STOP:", e)
        r.save()
    except Exception as e:  # noqa: BLE001  (crash: record and re-raise; never treated as a pass)
        r.res["status"] = f"error: {type(e).__name__}: {e}"
        r.save()
        raise


if __name__ == "__main__":
    main()
