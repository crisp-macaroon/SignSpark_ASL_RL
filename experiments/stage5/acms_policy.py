"""ACMS: arm-conditioned temporal mean-shift policy on the right-hand initial noise (Stage 5 design §1.3, A1).

  eps_R[:, t] = mu_phi(s)[:, t] + xi[:, t],  xi ~ N(0, I),  t < L  (padded frames: mu = 0, eps_R = xi)
  mu_phi(s)[:, t] = beta * U @ tanh((W * s_hat)(t) + c),  beta = beta_max * sigmoid(b),  beta_max = sqrt(2 / r)

s_hat: z-scored right-arm geodesic speed of the GENERATED body (common5.arm_feature). W: r x 17 temporal kernel
(+-8 frames, zero padding), c in R^r, U: 90 x r Stiefel (sign-fixed QR). ||mu_t||^2 < beta^2 r <= 2, so the exact KL to
the uncoupled N(0, I) is 1/2 ||mu_t||^2 < 1 nat per frame (cap by construction). log pi is exact (identity covariance).
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

LOG2PI = math.log(2 * math.pi)


class ACMS(nn.Module):
    def __init__(self, rank=4, half_width=8, channels=90, init_seed=7000, init_beta_frac=0.1, init_w_std=0.1,
                 kl_cap_nats_per_frame=1.0):
        super().__init__()
        g = torch.Generator().manual_seed(init_seed)
        self.rank, self.half, self.C = rank, half_width, channels
        self.beta_max = math.sqrt(2.0 * kl_cap_nats_per_frame / rank)
        self.U_raw = nn.Parameter(torch.randn(channels, rank, generator=g))
        self.W = nn.Parameter(torch.randn(rank, 1, 2 * half_width + 1, generator=g) * init_w_std)
        self.c = nn.Parameter(torch.zeros(rank))
        self.b = nn.Parameter(torch.tensor(math.log(init_beta_frac / (1 - init_beta_frac))))

    def U(self):
        q, r = torch.linalg.qr(self.U_raw)
        return q * torch.sign(torch.diagonal(r))[None, :]

    def beta(self):
        return self.beta_max * torch.sigmoid(self.b)

    def mu(self, s_hat, L):
        """s_hat [n, T] (zeros beyond L), L list of n lengths -> mu [n, C, T] with mu = 0 on padded frames."""
        h = F.conv1d(s_hat[:, None, :], self.W, padding=self.half) + self.c[None, :, None]   # [n, r, T]
        m = self.beta() * torch.einsum("cr,nrt->nct", self.U(), torch.tanh(h))
        T = s_hat.shape[1]
        act = (torch.arange(T, device=s_hat.device)[None, :] < torch.as_tensor(L, device=s_hat.device)[:, None])
        return m * act[:, None, :].to(m.dtype)

    @staticmethod
    def log_prob(eps, mu, L):
        """Exact log N(eps; mu, I) over the active frames t < L (per row)."""
        T = eps.shape[-1]
        act = (torch.arange(T, device=eps.device)[None, :] < torch.as_tensor(L, device=eps.device)[:, None]).to(eps.dtype)
        sq = (((eps - mu) ** 2).sum(1) * act).sum(1)
        n = act.sum(1) * eps.shape[1]
        return -0.5 * sq - 0.5 * n * LOG2PI

    @staticmethod
    def kl_per_frame(mu, L):
        """Exact KL(N(mu, I) || N(0, I)) per active frame = 1/2 sum ||mu_t||^2 / L (per row)."""
        Lt = torch.as_tensor(L, device=mu.device, dtype=mu.dtype)
        return 0.5 * (mu ** 2).sum((1, 2)) / Lt

    def param_norm(self):
        return float(torch.sqrt(sum((p.detach() ** 2).sum() for p in self.parameters())))
