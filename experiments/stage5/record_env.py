"""Stage 5 reproducibility record: environment, dependency list, SHA-256 of code, config, inputs and checkpoints.

  python -E -s experiments/stage5/record_env.py --out experiments/stage5/out/env [--lmdb]
(--lmdb also hashes the train/dev LMDB data files, ~7.8 GB, about 1 min.)
"""

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common5 as C  # noqa: E402

CODE = ["common5.py", "acms_policy.py", "rewards.py", "episode_sampler.py", "train_500ep.py", "evaluate.py", "plots.py",
        "record_env.py", "config_500ep.json", "tests/run_tests.py", "tests/config_test.json"]
STAGE4 = ["experiments/stage4/e2d/unrolled_sampler.py", "experiments/stage4/e2e/metrics.py", "experiments/stage4/validity/validity.py",
          "experiments/stage4/jspace.py", "experiments/stage4/e2c/typicality.py", "research/stage4/FROZEN_TARGETS_R0.json",
          "experiments/stage4/r0/out/r0_results.json", "third_party/SignSparK/signspark/pose_datasets_lmdb.py",
          "third_party/SignSparK/signspark/unet_model.py"]
CKPT = ["models/SignSparK/body/ema_0.9999_200000.pt", "models/SignSparK/hand/ema_0.9999_200000.pt"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--lmdb", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
           "code_sha256": {p: C.sha256(HERE / p) for p in CODE if (HERE / p).exists()},
           "stage4_and_upstream_sha256": {p: C.sha256(C.ROOT / p) for p in STAGE4},
           "signspark_checkpoint_sha256": {p: C.sha256(C.ROOT / p) for p in CKPT}}
    if a.lmdb:
        rec["lmdb_sha256"] = {str(f.relative_to(C.ROOT)): C.sha256(f) for s in ("train", "dev")
                              for f in sorted(C.lmdb_path(s).glob("*.mdb"))}
    try:
        import torch
        rec["torch"] = torch.__version__
        rec["cuda"] = torch.version.cuda
        rec["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception as e:  # recorded, not fatal
        rec["torch_error"] = repr(e)
    rec["nvidia_smi"] = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                                       capture_output=True, text=True).stdout.strip()
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    (out / "pip_freeze.txt").write_text(freeze, encoding="utf-8")
    (out / "environment.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    print(json.dumps(main(), indent=1)[:3000])
