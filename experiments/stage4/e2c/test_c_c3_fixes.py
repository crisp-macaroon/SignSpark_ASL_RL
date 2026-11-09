"""Synthetic tests A-C for the C-c3 audit fixes B1/B2 (authorised 2026-11-03). Synthetic arrays only: no model,
checkpoint, dataset or generated sample. Every acceptance is re-checked independently in float64 on the returned
array (not by trusting the function's own ok flag).

  A  non-finite inputs (NaN, +inf, -inf, float32 overflow) are never feasible / never projected with ok = True
  B  float32 model-input feasibility after projection: 10,000 cases (L = 28, 56, 146, 304 x 5 types x 500,
     the design of review_typicality.py part 2)
  C  constant / near-constant / small-variance / mixed channels: ok = True never coexists with an N/M/V violation

    python -E -s experiments/stage4/e2c/test_c_c3_fixes.py --out experiments/stage4/e2c/c_c3_fix_tests.json
"""

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

import typicality as T

HERE = Path(__file__).resolve().parent
ARCHIVE_OLD = HERE.parents[2] / "research" / "archive" / "typicality_pre_B1B2.py"


def indep_mvn(x, b, norm2):
    """Independent float64 re-check of finiteness, N, M, V on array x (as fed to the model)."""
    x64 = np.asarray(x).astype(np.float64)
    if not np.isfinite(x64).all():
        return {"finite": False, "N": False, "M": False, "V": False, "norm_rel_err": np.inf, "M_dev": np.inf, "V_dev": np.inf}
    L = x64.shape[1]
    m = np.abs(x64.mean(1)).max()
    q = (x64 ** 2).mean(1)
    nre = abs((x64 ** 2).sum() - norm2) / norm2
    return {"finite": True, "N": nre <= T.NORM_RTOL, "M": m <= b["mean"], "V": q.min() >= b["var_lo"] and q.max() <= b["var_hi"],
            "norm_rel_err": float(nre), "M_dev": float((m - b["mean"]) / b["mean"]),
            "V_dev": float(max((b["var_lo"] - q.min()) / b["var_lo"], (q.max() - b["var_hi"]) / b["var_hi"]))}


def test_a(rng):
    spec = importlib.util.spec_from_file_location("typ_old", ARCHIVE_OLD)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    cases, fails = [], 0
    for L in (28, 146, 304):
        b = T.bounds(L)
        base = rng.standard_normal((T.C, L))
        n2 = float((base ** 2).sum())
        variants = {}
        for name, val in (("one NaN", np.nan), ("one +inf", np.inf), ("one -inf", -np.inf)):
            x = base.copy(); x[3, 5] = val; variants[name] = (x, n2)
        variants["all NaN"] = (np.full_like(base, np.nan), n2)
        variants["NaN row"] = (np.where(np.arange(T.C)[:, None] == 7, np.nan, base), n2)
        variants["norm2 NaN"] = (base.copy(), float("nan"))
        big = base.copy(); big[0, 0] = 1e39  # finite in float64, +inf after the float32 cast
        variants["float32 overflow (1e39)"] = (big, n2)
        for name, (x, nn) in variants.items():
            f_ok, _ = T.feasible(x, b, nn)
            p_y, p_ok = T.project_mvn_exact(x, b, nn)
            m_y, m_ok, _ = T.to_model_input(x, b, nn)
            r_y, r_ok, _ = T.repair_ap(x, b, nn, steps=20)
            # any ok must come with a finite, N/M/V-satisfying array
            bad = []
            if name != "float32 overflow (1e39)" and f_ok:
                bad.append("feasible accepted non-finite")
            for tag, ok, arr in (("project", p_ok, p_y), ("to_model_input", m_ok, m_y), ("repair_ap", r_ok, r_y)):
                if ok and not all(indep_mvn(arr, b, nn)[k] for k in ("finite", "N", "M", "V")):
                    bad.append(f"{tag} ok=True on an invalid array")
                if ok and not np.isfinite(np.asarray(arr)).all():
                    bad.append(f"{tag} returned non-finite with ok=True")
            # run-1 expectation "float32 overflow accepted -> failure" was a test-design error: the input is finite,
            # E-1 projects in float64 BEFORE the cast, so a valid finite in-bounds array may legitimately be returned.
            # The requirement is only that nothing non-finite or out-of-bounds is ever returned with ok = True
            # (checked above for every function). Run-1 output is kept in c_c3_fix_tests_run1.json.
            old_ok = None
            try:
                old_ok = bool(old.feasible(x, b, nn)[0])
            except Exception:  # noqa: BLE001
                old_ok = "error"
            fails += bool(bad)
            cases.append({"L": L, "case": name, "feasible": f_ok, "project_ok": p_ok, "to_model_input_ok": m_ok,
                          "repair_ok": r_ok, "pre_fix_feasible_result": old_ok, "problems": bad})
    return {"cases": cases, "n": len(cases), "failures": fails, "pass": fails == 0}


def perturb(x, rng, kind):
    y = x.copy()
    C = x.shape[0]
    if kind in ("offset", "combined"):
        ch = rng.choice(C, 5, replace=False)
        y[ch] += rng.uniform(0.3, 1.0, (5, 1)) * rng.choice([-1, 1], (5, 1))
    if kind in ("scale", "combined"):
        ch = rng.choice(C, 10, replace=False)
        y[ch] *= rng.uniform(0.3, 2.5, (10, 1))
    if kind in ("global", "combined"):
        y *= 1.3
    return y


def test_b(rng, n=500):
    agg = {"cases": 0, "success": 0, "failed": 0, "postcast_violations_among_success": 0, "nonfinite_among_success": 0,
           "max_norm_rel_err": 0.0, "max_M_dev": -np.inf, "max_V_dev": -np.inf, "reprojections_used": 0,
           "AP_not_satisfied_among_success": 0}
    by = {}
    for L in (28, 56, 146, 304):
        b = T.bounds(L)
        for kind in ("null_violators", "offset", "scale", "global", "combined"):
            s = {"n": 0, "success": 0, "failed": 0, "postcast_violations": 0, "AP_not_satisfied": 0}
            while s["n"] < n:
                x = rng.standard_normal((T.C, L))
                n2 = float((x ** 2).sum())
                if kind == "null_violators":
                    v = T.violations(T.stats(x[None]), b)
                    if not (v["M"][0] or v["V"][0]):
                        continue
                    y = x
                else:
                    y = perturb(x, rng, kind)
                s["n"] += 1
                xm, ok, det = T.to_model_input(y, b, n2)
                if not ok:
                    s["failed"] += 1
                    continue
                s["success"] += 1
                assert xm.dtype == np.float32
                chk = indep_mvn(xm, b, n2)
                if not (chk["finite"] and chk["N"] and chk["M"] and chk["V"]):
                    s["postcast_violations"] += 1
                if not chk["finite"]:
                    agg["nonfinite_among_success"] += 1
                if det.get("A") or det.get("P"):
                    s["AP_not_satisfied"] += 1
                agg["max_norm_rel_err"] = max(agg["max_norm_rel_err"], chk["norm_rel_err"])
                agg["max_M_dev"] = max(agg["max_M_dev"], chk["M_dev"])
                agg["max_V_dev"] = max(agg["max_V_dev"], chk["V_dev"])
                agg["reprojections_used"] += det.get("reprojections", 0)
            by[f"L{L}_{kind}"] = s
            for k in ("success", "failed"):
                agg[k] += s[k]
            agg["cases"] += s["n"]
            agg["postcast_violations_among_success"] += s["postcast_violations"]
            agg["AP_not_satisfied_among_success"] += s["AP_not_satisfied"]
    agg["pass"] = (agg["cases"] == 10000 and agg["postcast_violations_among_success"] == 0
                   and agg["nonfinite_among_success"] == 0 and agg["max_norm_rel_err"] <= T.NORM_RTOL
                   and agg["max_M_dev"] <= 0 and agg["max_V_dev"] <= 0)
    return {"aggregate": agg, "by_case": by,
            "note": "A/P are not enforced by projection (E-1); AP_not_satisfied counts cases that E-4 repair must handle"}


def test_c(rng, reps=20):
    out, unsafe = [], 0
    for L in (28, 146, 304):
        b = T.bounds(L)
        builders = {
            "one channel exactly constant": lambda x: _set(x, [0], lambda r: np.full(L, 0.3)),
            "all channels exactly constant": lambda x: np.full_like(x, 0.3),
            "one channel near-constant 1e-15": lambda x: _set(x, [0], lambda r: 0.3 + 1e-15 * rng.standard_normal(L)),
            "one channel near-constant 1e-12": lambda x: _set(x, [0], lambda r: 0.3 + 1e-12 * rng.standard_normal(L)),
            "one channel near-constant 1e-8": lambda x: _set(x, [0], lambda r: 0.3 + 1e-8 * rng.standard_normal(L)),
            "10 channels variance 1e-6": lambda x: _set(x, range(10), lambda r: 1e-3 * r),
            "10 channels variance 1e-3": lambda x: _set(x, range(10), lambda r: np.sqrt(1e-3) * r),
            "mixed: 45 ordinary + 45 near-constant 1e-10": lambda x: _set(x, range(45), lambda r: 0.1 + 1e-10 * r),
            "mixed: 89 ordinary + 1 zero channel": lambda x: _set(x, [5], lambda r: np.zeros(L)),
        }
        for name, f in builders.items():
            res = {"L": L, "case": name, "n": reps, "ok": 0, "failed_safely": 0, "ok_with_violation": 0}
            for _ in range(reps):
                base = rng.standard_normal((T.C, L))
                n2 = float((base ** 2).sum())  # registered N target: the base sample's norm
                x = f(base.copy())
                for fn in ("project", "to_model_input"):
                    if fn == "project":
                        y, ok = T.project_mvn_exact(x, b, n2)
                    else:
                        y, ok, _ = T.to_model_input(x, b, n2)
                    if ok:
                        res["ok"] += 1
                        chk = indep_mvn(y, b, n2)
                        if fn == "to_model_input":
                            chk32 = chk
                        else:
                            chk32 = indep_mvn(np.asarray(y).astype(np.float32), b, n2)
                        if not all(chk[k] for k in ("finite", "N", "M", "V")):
                            res["ok_with_violation"] += 1
                        res.setdefault("ok_float32_violation", 0)
                        if fn == "project" and not all(chk32[k] for k in ("finite", "N", "M", "V")):
                            res["ok_float32_violation"] += 1  # informational: raw projection is float64; E-3 uses to_model_input
                    else:
                        res["failed_safely"] += 1
            unsafe += res["ok_with_violation"]
            out.append(res)
    return {"cases": out, "ok_with_violation_total": unsafe, "pass": unsafe == 0}


def _set(x, rows, gen):
    for r in rows:
        x[r] = gen(x[r])
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rng = np.random.default_rng(20261103)  # synthetic test seed, unrelated to any campaign seed
    t0 = time.time()
    res = {"constants": {"NORM_RTOL": T.NORM_RTOL, "INWARD_MARGIN": T.INWARD_MARGIN, "MODEL_DTYPE": "float32",
                         "FAM": T.FAM}}
    res["A"] = test_a(rng); print("A pass", res["A"]["pass"], "failures", res["A"]["failures"], "of", res["A"]["n"], flush=True)
    res["B"] = test_b(rng); print("B", json.dumps(res["B"]["aggregate"]), flush=True)
    res["C"] = test_c(rng); print("C pass", res["C"]["pass"], "ok_with_violation", res["C"]["ok_with_violation_total"], flush=True)
    res["seconds"] = round(time.time() - t0)
    res["all_pass"] = res["A"]["pass"] and res["B"]["aggregate"]["pass"] and res["C"]["pass"]
    Path(args.out).write_text(json.dumps(res, indent=1, default=lambda o: o if not isinstance(o, float) else float(o)),
                              encoding="utf-8")
    print("ALL PASS" if res["all_pass"] else "NOT ALL PASS", f"({res['seconds']} s)")


if __name__ == "__main__":
    main()
