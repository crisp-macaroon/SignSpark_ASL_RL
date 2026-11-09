"""Closure test run: every automated test suite in the project, outputs redirected to experiments/stage6_final/test_out/
so that no Stage 4 / Stage 5 artifact is rewritten. Integration suites that generate on the GPU are run with --integration
only when requested (they re-open dev and regenerate small samples; nothing is written outside test_out/).

  python -E -s experiments/stage6_final/run_all_tests.py [--integration]
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
OUT = HERE / "test_out"

WRAP_S5 = """import sys; from pathlib import Path
sys.path.insert(0, r"{root}\\experiments\\stage5\\tests"); sys.path.insert(0, r"{root}\\experiments\\stage5")
import run_tests as T
T.OUT = Path(r"{out}")
sys.argv = ["run_tests.py", "{flag}"]
T.main()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--integration", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    suites = [
        ("stage5_unit", [PY, "-E", "-s", "-c", WRAP_S5.format(root=ROOT, out=OUT / "stage5", flag="--unit")]),
        ("stage6_unit", [PY, "-E", "-s", ROOT / "experiments/stage5_multiseed/tests/test_stage6.py"]),
        ("mc_reward", [PY, "-E", "-s", ROOT / "experiments/mc_reward/test_mc_reward.py"]),
        # J tests need smplx, installed only in .venv-render (the environment the suite was originally run in)
        ("validity", [ROOT / ".venv-render/Scripts/python.exe", "-E", "-s", ROOT / "experiments/stage4/validity/test_validity.py",
                      "--out", OUT / "validity.json"]),
        ("c_c3_fixes", [PY, "-E", "-s", ROOT / "experiments/stage4/e2c/test_c_c3_fixes.py", "--out", OUT / "c_c3_fixes.json"]),
        ("phase0_selftest", [PY, "-E", "-s", ROOT / "experiments/stage4/phase0_selftest.py"]),
        ("e2e_selftest", [PY, "-E", "-s", ROOT / "experiments/stage4/e2e/selftest.py"]),
    ]
    if a.integration:
        suites.append(("stage5_integration", [PY, "-E", "-s", "-c", WRAP_S5.format(root=ROOT, out=OUT / "stage5", flag="--integration")]))
    res = []
    for name, cmd in suites:
        t0 = time.time()
        p = subprocess.run([str(c) for c in cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / f"{name}.log").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr, encoding="utf-8")
        tail = [ln for ln in p.stdout.strip().splitlines()[-3:]]
        res.append({"suite": name, "exit": p.returncode, "seconds": round(time.time() - t0, 1), "tail": tail})
        print(name, p.returncode, tail[-1] if tail else "", flush=True)
    (OUT / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
