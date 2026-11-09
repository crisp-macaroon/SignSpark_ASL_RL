"""PF-0 preflight for the ACMS multi-seed replication (ACMS_MULTISEED_DESIGN.md §2.1) and the Stage 6 runs. CPU only.

  python -E -s experiments/stage5_multiseed/preflight.py --make-configs   (writes configs/config_500ep_s700{1..4}.json)
  python -E -s experiments/stage5_multiseed/preflight.py                  (all checks -> out/preflight.json; exit 1 on fail)
  python -E -s experiments/stage5_multiseed/preflight.py --verify-snapshot out/reference_snapshot.json

Checks: (1) config diff vs config_500ep.json limited to the five seed/name fields; (2) integer seed-range disjointness
across all runs and every prior/planned noise base; (3) noise-tensor checks; (4) clip overlap between the five training
sets (reported); (5) code / target / checkpoint SHA-256 identical to the Stage 5 reference record; (6) SHA-256 snapshot
of every existing Stage 4 / Stage 5 artifact (immutability record, re-verified at closure).
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S5 = ROOT / "experiments" / "stage5"
REF_CFG = S5 / "config_500ep.json"
REF_ENV = S5 / "out" / "env" / "environment.json"
SEEDS = (7001, 7002, 7003, 7004)
ALLOWED_DIFF = {"name", "design", "policy.init_seed", "seeds.train_clip_sampler", "seeds.train_noise_base"}
N_TRAIN = 29630


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def flat(d, p=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, f"{p}{k}."))
        else:
            out[f"{p}{k}"] = v
    return out


def seed_config(s):
    d = s - 7000
    cfg = json.loads(REF_CFG.read_text(encoding="utf-8-sig"))
    c = copy.deepcopy(cfg)
    c["name"] = f"stage5_acms_500ep_s{s}"
    c["design"] = "research/stage6_proposal/ACMS_MULTISEED_DESIGN.md (final authorisation 2026-11-07)"
    c["policy"]["init_seed"] = s
    c["seeds"]["train_clip_sampler"] = 5000 + d
    c["seeds"]["train_noise_base"] = 50_000_000 + d * 1_000_000
    return c


def config_path(s):
    return HERE / "configs" / f"config_500ep_s{s}.json"


def all_configs():
    out = {7000: json.loads(REF_CFG.read_text(encoding="utf-8-sig"))}
    for s in SEEDS:
        out[s] = json.loads(config_path(s).read_text(encoding="utf-8"))
    return out


def ranges(cfgs):
    """Every noise-seed integer range in the project, (name, lo, hi) inclusive."""
    r = [("E2e A0", 10_000_000, 10_000_000 + 1000 * 31 + 32), ("E2e A0p", 20_000_000, 20_000_000 + 1000 * 31 + 32),
         ("E2d", 20_261_103, 20_261_104), ("E2b fresh", 30_000_000, 30_000_000 + 1000 * 255 + 116),
         ("Stage5 eval", 40_000_001, 40_000_000 + 1000 * 255 + 4),
         ("OPT-G fresh", 45_000_001, 45_000_000 + 1000 * 124 + 4),
         ("FG-1 fit", 60_000_001, 60_000_000 + 1000 * 15 + 16), ("FG-1 held-out", 61_000_001, 61_000_000 + 1000 * 15 + 16)]
    for s, c in cfgs.items():
        b = c["seeds"]["train_noise_base"]
        r.append((f"train s{s}", b, b + 1000 * (c["n_groups"] - 1) + (c["group_size"] - 1)))
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-configs", action="store_true")
    ap.add_argument("--verify-snapshot")
    ap.add_argument("--out", default=str(HERE / "out"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.make_configs:
        (HERE / "configs").mkdir(exist_ok=True)
        for s in SEEDS:
            config_path(s).write_text(json.dumps(seed_config(s), indent=1), encoding="utf-8")
            print("wrote", config_path(s))
        return 0
    if a.verify_snapshot:
        snap = json.loads(Path(a.verify_snapshot).read_text(encoding="utf-8"))
        bad = [p for p, h in snap["files"].items() if not (ROOT / p).exists() or sha256(ROOT / p) != h]
        rep = {"n_files": len(snap["files"]), "changed_or_missing": bad, "pass": not bad}
        print(json.dumps(rep, indent=1))
        return 0 if not bad else 1
    res, ok = {}, True
    cfgs = all_configs()
    ref = flat(cfgs[7000])
    # (1) config diff
    diffs = {}
    for s in SEEDS:
        f = flat(cfgs[s])
        diffs[s] = sorted(k for k in set(ref) | set(f) if ref.get(k) != f.get(k))
    res["config_diff"] = {str(s): d for s, d in diffs.items()}
    res["config_diff_ok"] = all(set(d) <= ALLOWED_DIFF for d in diffs.values())
    res["config_sha256"] = {str(s): sha256(config_path(s)) for s in SEEDS} | {"7000": sha256(REF_CFG)}
    # (2) range disjointness
    rr = ranges(cfgs)
    overl = [(a1, b1) for i, (a1, l1, h1) in enumerate(rr) for (b1, l2, h2) in rr[i + 1:] if l1 <= h2 and l2 <= h1]
    res["noise_ranges"] = [{"name": n, "lo": lo, "hi": hi} for n, lo, hi in rr]
    res["noise_range_overlaps"] = overl
    init = {c["policy"]["init_seed"] for c in cfgs.values()}
    res["policy_init_seeds"] = sorted(init)
    res["policy_init_disjoint_from_e2c_family_init"] = not (init & set(range(1000, 1032)))
    # (3) noise tensors
    sys.path.insert(0, str(S5))
    import torch

    def noise(base, a1, b1):
        g = torch.Generator().manual_seed(int(base) + 1000 * int(a1) + int(b1))
        return torch.randn(240, 304, generator=g)

    tb = {s: c["seeds"]["train_noise_base"] for s, c in cfgs.items()}
    res["train_noise_first_tensors_distinct"] = all(
        not torch.equal(noise(tb[s], 0, 0), noise(tb[t], 0, 0)) for s in tb for t in tb if s < t)
    ref_samples = json.loads((S5 / "out" / "eval" / "eval_samples.json").read_text(encoding="utf-8"))
    res["reference_eval_seeds_match_formula"] = all(r["seed"] == 40_000_000 + 1000 * r["clip"] + r["k"] for r in ref_samples)
    res["eval_noise_base_shared"] = all(c["seeds"]["eval_noise_base"] == 40_000_000 for c in cfgs.values())
    # (4) clip overlap
    clips = {s: [int(i) for i in np.random.default_rng(c["seeds"]["train_clip_sampler"]).choice(N_TRAIN, c["n_groups"], replace=False)]
             for s, c in cfgs.items()}
    ref_run = json.loads((S5 / "out" / "train" / "run.json").read_text(encoding="utf-8"))
    res["seed7000_clips_reproduced"] = clips[7000] == ref_run["train_clips"]
    res["clip_overlap_pairs"] = {f"{s}-{t}": len(set(clips[s]) & set(clips[t])) for s in clips for t in clips if s < t}
    res["clip_overlap_expected_per_pair"] = 125 * 125 / N_TRAIN
    (out / "train_clips.json").write_text(json.dumps({str(s): v for s, v in clips.items()}), encoding="utf-8")
    # (5) code hash identity
    env = json.loads(REF_ENV.read_text(encoding="utf-8"))
    cur = {p: sha256(S5 / p) for p in env["code_sha256"]}
    cur4 = {p: sha256(ROOT / p) for p in env["stage4_and_upstream_sha256"]}
    curc = {p: sha256(ROOT / p) for p in env["signspark_checkpoint_sha256"]}
    res["code_mismatch"] = [p for p in cur if cur[p] != env["code_sha256"][p]]
    res["stage4_mismatch"] = [p for p in cur4 if cur4[p] != env["stage4_and_upstream_sha256"][p]]
    res["checkpoint_mismatch"] = [p for p in curc if curc[p] != env["signspark_checkpoint_sha256"][p]]
    res["checkpoint_sha256"] = curc
    # (6) immutability snapshot of all Stage 4 / Stage 5 artifacts
    files = {}
    for base in (ROOT / "experiments" / "stage4", S5, ROOT / "research" / "stage4", ROOT / "research" / "stage5"):
        for f in sorted(base.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                files[str(f.relative_to(ROOT)).replace("\\", "/")] = sha256(f)
    (out / "reference_snapshot.json").write_text(json.dumps({"files": files}, indent=0), encoding="utf-8")
    res["snapshot_files"] = len(files)
    checks = {"config_diff_ok": res["config_diff_ok"], "no_range_overlap": not overl,
              "init_disjoint": res["policy_init_disjoint_from_e2c_family_init"],
              "tensors_distinct": res["train_noise_first_tensors_distinct"],
              "eval_formula": res["reference_eval_seeds_match_formula"], "eval_base_shared": res["eval_noise_base_shared"],
              "seed7000_clips": res["seed7000_clips_reproduced"], "code_identical": not res["code_mismatch"],
              "stage4_identical": not res["stage4_mismatch"], "checkpoints_identical": not res["checkpoint_mismatch"]}
    res["checks"] = checks
    ok = all(checks.values())
    res["pass"] = ok
    (out / "preflight.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(checks, indent=1), "\nclip overlap", res["clip_overlap_pairs"], "\nPASS" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
