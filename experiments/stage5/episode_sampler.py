"""Reproducible episode sampler (design §3, A5): train clips without replacement, registered-style noise seeds.

Train clips: numpy default_rng(5000).choice(N_train, n_groups, replace=False) over the How2Sign TRAIN dataset indices
(the R0 order, N_train = 29,630). Noise: common5.noise(base, a, b) with train base 50,000,000 (a = group, b = episode
in group) and eval base 40,000,000 (a = dev clip, b = noise 1..4); disjoint from E2e (10M, 20M) and from each other.
"""

import numpy as np

import common5 as C

N_TRAIN = 29630


def train_clips(n_groups, seed, n_train=N_TRAIN):
    return [int(i) for i in np.random.default_rng(seed).choice(n_train, n_groups, replace=False)]


def train_noise(base, g, i):
    return C.noise(base, g, i)


def eval_noise(base, j, k):
    return C.noise(base, j, k)


def seed_ranges(n_groups, group_size, n_eval_clips, n_eval_noises, train_base, eval_base):
    tr = (train_base, train_base + 1000 * (n_groups - 1) + (group_size - 1))
    ev = (eval_base + 1000 * 0 + 1, eval_base + 1000 * (n_eval_clips - 1) + n_eval_noises)
    e2e = (10_000_000, 20_000_000 + 1000 * 31 + 32)
    return {"train": tr, "eval": ev, "e2e": e2e}
