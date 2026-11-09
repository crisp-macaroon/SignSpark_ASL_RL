"""Run an unmodified upstream SignSparK script (sample.py, ...) with the offline M-CLIP
construction patch applied and timing / peak-GPU-memory logged.

    python experiments/common/run_upstream.py sample.py <hydra overrides...>
"""

import json
import runpy
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "third_party" / "SignSparK"
sys.path.insert(0, str(UPSTREAM))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import offline_mclip  # noqa: E402,F401  (patches M-CLIP construction)

# Upstream dist_util.setup_dist() initialises an NCCL process group, which Windows PyTorch
# does not ship (and gloo cannot resolve this host). Single-GPU sampling makes no collective
# calls, so setup reduces to selecting the device.
from signspark.utils import dist_util  # noqa: E402


def _single_gpu_setup():
    if torch.cuda.is_available():
        torch.cuda.set_device(dist_util.dev())
        torch.cuda.empty_cache()


dist_util.setup_dist = _single_gpu_setup

script = UPSTREAM / sys.argv[1]
sys.argv = [str(script)] + sys.argv[2:]
t0 = time.time()
if torch.cuda.is_available():
    torch.cuda.reset_peak_memory_stats()
try:
    runpy.run_path(str(script), run_name="__main__")
except SystemExit as exc:
    if exc.code not in (None, 0):
        raise
finally:
    stats = {"script": sys.argv[0], "overrides": sys.argv[1:], "wall_s": round(time.time() - t0, 2)}
    if torch.cuda.is_available():
        stats["peak_gpu_alloc_GB"] = round(torch.cuda.max_memory_allocated() / 2**30, 3)
        stats["peak_gpu_reserved_GB"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
        stats["gpu"] = torch.cuda.get_device_name(0)
    print("### RUN_STATS " + json.dumps(stats), flush=True)
