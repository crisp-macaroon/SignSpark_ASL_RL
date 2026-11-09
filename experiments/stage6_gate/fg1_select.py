"""FG-1 clip selection (MC_REDESIGN_PROPOSAL.md §5.1). CPU only; opens the TRAIN split only.

numpy default_rng(5100).permutation(29,630) over the How2Sign TRAIN indices (R0 order); walk the permutation, skip any
clip used by the five ACMS training sets (stage5_multiseed/out/train_clips.json); take the first 8 with L < 100 and the
first 8 with L >= 100 (length-stratified; E2c (ii) length effect). Gate position a = 0..15 in the order taken
(short clips first, then long).

  python -E -s experiments/stage6_gate/fg1_select.py
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage5"))
import common5 as C  # noqa: E402

N_TRAIN, SEED, PER_STRATUM = 29630, 5100, 8


def main():
    used = set()
    for v in json.loads((ROOT / "experiments/stage5_multiseed/out/train_clips.json").read_text(encoding="utf-8")).values():
        used |= set(v)
    ds = C.open_dataset("train")
    assert len(ds) == N_TRAIN
    short, long_, skipped = [], [], 0
    for i in np.random.default_rng(SEED).permutation(N_TRAIN):
        i = int(i)
        if i in used:
            skipped += 1
            continue
        L = int(ds[i][1])
        stratum = short if L < 100 else long_
        if len(stratum) < PER_STRATUM:
            stratum.append((i, L))
        if len(short) == PER_STRATUM and len(long_) == PER_STRATUM:
            break
    clips = short + long_
    rec = {"rule": __doc__.split("  python")[0].strip(), "seed": SEED, "clips": [c for c, _ in clips],
           "lengths": [L for _, L in clips], "names": [str(ds[c][4]) for c, _ in clips],
           "skipped_acms_training_clips": skipped, "opened_splits": list(C.OPENED_SPLITS)}
    out = HERE / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gate_clips.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
