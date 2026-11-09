"""Shared loader for the final report and deck: every number shown is read from measured JSON outputs here; anything
missing is reported as unavailable, never imputed."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MS = ROOT / "experiments" / "stage5_multiseed" / "out"
GATE = ROOT / "experiments" / "stage6_gate" / "out"
FIG = HERE / "figures"
NA = "unavailable"


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def f(x, d=4, sign=True):
    if x is None:
        return NA
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def ci(c, d=4):
    return NA if c is None else f"[{c[0]:+.{d}f}, {c[1]:+.{d}f}]"


def est(e, d=4):
    """'+0.0022 [+0.0014, +0.0031]' from a {mean, ci95} dict."""
    return NA if not e else f"{f(e['mean'], d)} {ci(e['ci95'], d)}"


class Data:
    def __init__(self):
        self.pooled = load(MS / "pooled_results.json")
        self.fg = load(GATE / "fg1_results.json")
        self.compute = load(HERE / "compute_table.json") or []
        self.figs = load(HERE / "figures_index.json") or {"drawn": {}, "unavailable": {}}
        self.tests = load(HERE / "test_out" / "summary.json")
        self.manifest = load(ROOT / "research" / "final" / "EXPERIMENT_MANIFEST.json")
        self.ms_status = load(MS / "runner_status.json") or []
        self.gate_status = load(GATE / "runner_status.json") or []
        self.preflight = load(MS / "preflight.json")
        self.e2c = load(ROOT / "experiments" / "stage4" / "e2c" / "out_ii" / "e2c_ii_aggregate.json")
        self.posthoc = load(HERE / "posthoc_return" / "posthoc_return_results.json")  # post-hoc, not pre-registered

    # ---- figures
    def fig(self, name):
        p = FIG / name
        return str(p) if name in self.figs["drawn"] and p.exists() else None

    # ---- ACMS multi-seed
    def runs(self):
        return [r for r in self.pooled["per_run"] if not r["missing"]]

    def pool(self, which="pooled_primary_new4"):
        return self.pooled[which]

    def optc_available(self):
        p = self.pool()["optc_progress_pooled"]
        return all(not p.get(k, {}).get("incomplete") for k in ("25", "50", "75", "100"))

    def optg_available(self):
        return not self.pool()["optg_pooled"].get("incomplete")

    # ---- FG-1
    def fg_variant(self, v):
        if not self.fg:
            return None
        e = self.fg["variants"].get(v)
        return e if e and e.get("status") == "completed" else None

    def fg_status(self, v):
        if not self.fg:
            st = load(GATE / f"run_{v}.json")
            return st.get("status") if st else "not run"
        return self.fg["variants"].get(v, {}).get("status", "not run")

    def job(self, name):
        for j in self.ms_status + self.gate_status:
            if j.get("name") == name:
                return j
        return None
