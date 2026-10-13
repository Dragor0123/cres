# 관계 신뢰도 r(u, v) = C1(ψ(u, v)) 계산과 Pseudo-Class Core 구성 (005, P03). 레이블을 읽지 않는다.
# r의 방향: ψ(u, v)의 u가 첫 번째(순위 특징이 방향을 가짐).
import math
import os

import numpy as np
import torch

from cres.relations import L_TOP, Relations

LR_MISS = math.log1p(L_TOP + 1)


class RScorer:
    def __init__(self, rel: Relations, c1_path):
        self.R = rel
        d = torch.load(c1_path, weights_only=False)
        dev = rel.device
        self.w = torch.tensor(d["coef"], dtype=torch.float32, device=dev)
        self.b = float(d["intercept"])
        self.mu = torch.tensor(d["mu"], dtype=torch.float32, device=dev)
        self.sd = torch.tensor(d["sd"], dtype=torch.float32, device=dev)
        # 희소 특징(홉) 키 → (행, 열)
        N = rel.N
        self.e_r, self.e_c = rel.edge_keys // N, rel.edge_keys % N
        self.h_r, self.h_c = rel.hop2_keys // N, rel.hop2_keys % N

    def prob_from_feats(self, F):
        z = (F - self.mu) / self.sd
        return torch.sigmoid(z @ self.w + self.b)

    def pairs(self, u, v):
        """임의 쌍의 r (ψ 함수 + C1)."""
        return self.prob_from_feats(self.R.psi(u, v))

    def block(self, A, U, posU):
        """anchor 블록 A(B,) × 풀 U(|U|,) 의 r 행렬 (B, |U|). posU: 노드 → U 위치(-1 없음)."""
        R, dev = self.R, self.R.device
        B, n = len(A), len(U)
        feats = torch.empty((9, B, n), device=dev)
        feats[0] = R.Xn[A] @ R.Xn[U].T
        feats[1] = R.Hn[A] @ R.Hn[U].T
        rank_val = torch.log1p(torch.arange(1, L_TOP + 1, device=dev, dtype=torch.float32))
        rows = torch.arange(B, device=dev).unsqueeze(1).expand(B, L_TOP)
        for fi, idx in ((2, R.idxX), (3, R.idxH)):  # 정방향 rank(v | a)
            feats[fi].fill_(LR_MISS)
            p = posU[idx[A]]
            m = p >= 0
            feats[fi][rows[m], p[m]] = rank_val.unsqueeze(0).expand(B, L_TOP)[m]
        posB = torch.full((R.N,), -1, dtype=torch.long, device=dev)
        posB[A] = torch.arange(B, device=dev)
        colsU = torch.arange(n, device=dev).unsqueeze(1).expand(n, L_TOP)
        for fi, idx in ((4, R.idxX), (5, R.idxH)):  # 역방향 rank(a | v)
            feats[fi].fill_(LR_MISS)
            p = posB[idx[U]]  # (n, L): v의 목록 안 노드가 블록 anchor면 그 위치
            m = p >= 0
            feats[fi][p[m], colsU[m]] = rank_val.unsqueeze(0).expand(n, L_TOP)[m]
        cl = R.clusters
        feats[6] = (cl[:, A].unsqueeze(2) == cl[:, U].unsqueeze(1)).float().mean(0)
        for fi, (er, ec) in ((7, (self.e_r, self.e_c)), (8, (self.h_r, self.h_c))):
            feats[fi].zero_()
            pr, pc = posB[er], posU[ec]
            m = (pr >= 0) & (pc >= 0)
            feats[fi][pr[m], pc[m]] = 1.0
        F = feats.permute(1, 2, 0)
        return self.prob_from_feats(F)

    def within(self, nodes):
        """nodes (A, k) 각 행 안의 모든 순서쌍 r (A, k, k). r[i, j] = r(nodes[i], nodes[j])."""
        R = self.R
        A_, k = nodes.shape
        out = torch.empty((A_, k, k), device=R.device)
        bs = max(1, 2_000_000 // (k * k))
        for s in range(0, A_, bs):
            nd = nodes[s:s + bs]
            b = len(nd)
            u = nd.unsqueeze(2).expand(b, k, k).reshape(-1)
            v = nd.unsqueeze(1).expand(b, k, k).reshape(-1)
            F = R.psi(u, v, with_sim=False).reshape(b, k, k, 9)
            for fi, Z in ((0, R.Xn), (1, R.Hn)):  # s_X, s_H 는 bmm으로
                for t in range(0, b, 256):
                    G = Z[nd[t:t + 256]]
                    F[t:t + 256, :, :, fi] = torch.bmm(G, G.transpose(1, 2))
            out[s:s + b] = self.prob_from_feats(F)
        return out


def stable_topk(score, k, exclude_cols=None):
    """행마다 점수 내림차순 상위 k (동점은 열 번호 = U 안 노드 id 오름차순)."""
    if exclude_cols is not None:
        score = score.clone()
        score[torch.arange(len(score), device=score.device), exclude_cols] = -float("inf")
    _, order = torch.sort(-score, dim=1, stable=True)
    return order[:, :k]


def greedy_core(Rw, m, tau):
    """Rw: (A, 1+C, 1+C) — 0번이 anchor, 1..C 후보(r(a,·) 내림차순). 반환 accepted (A,), members (A, m) 노드 위치(0=anchor, 추가 순서), -1 패딩."""
    A_, K, _ = Rw.shape
    dev = Rw.device
    inS = torch.zeros((A_, K), dtype=torch.bool, device=dev)
    inS[:, 0] = True
    alive = torch.ones((A_, K), dtype=torch.bool, device=dev)
    alive[:, 0] = False
    size = torch.ones(A_, dtype=torch.long, device=dev)
    members = torch.full((A_, m), -1, dtype=torch.long, device=dev)
    members[:, 0] = 0
    ar = torch.arange(A_, device=dev)
    for _ in range(K - 1):
        active = (size < m) & alive.any(1)
        if not active.any():
            break
        Sf = inS.float()
        mean_r = (Rw * Sf.unsqueeze(1)).sum(2) / size.unsqueeze(1).float()  # (A, K): v의 S와의 평균 r(v, w)
        mean_r = torch.where(alive, mean_r, torch.full_like(mean_r, -float("inf")))
        v = mean_r.argmax(1)  # 동점: 앞 후보(= r(a,·) 높은 쪽)
        min_r = torch.where(inS, Rw[ar, v], torch.full_like(mean_r, float("inf"))).min(1).values
        add = active & (min_r >= tau)
        alive[ar[active], v[active]] = False
        idx = ar[add]
        inS[idx, v[add]] = True
        members[idx, size[add]] = v[add]
        size[add] += 1
    accepted = size == m
    return accepted, members
