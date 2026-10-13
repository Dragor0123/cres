# 관계 근거 ψ(u, v) (004, R003 §1). 레이블을 읽지 않는다. seed와 무관, 데이터셋마다 한 번 계산해 캐시.
#
# 특징 순서 PSI_NAMES:
#   s_X, s_H, lr_X, lr_H, lr_X_rev, lr_H_rev, c, hop1, hop2
#   lr_* = log(1 + rank), rank는 1부터, 목록(L = 50) 밖이면 L + 1.
import os
import time

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn.functional as F

from cres.data import ROOT, load_raw, sym_norm_adj

PSI_NAMES = ["s_X", "s_H", "lr_X", "lr_H", "lr_X_rev", "lr_H_rev", "c", "hop1", "hop2"]
L_TOP = 50
SVD_DIM = 128
KS = [25, 50, 100, 200]
RESTARTS = 2
KMEANS_ITERS = 50
KMEANS_SEED = 20000  # 20000 + 0 (seed 무관)
CACHE = os.path.join(ROOT, "results", "004")


def topk_cos(Z, L, block=4096):
    """Z: (N, d) L2 정규화 GPU 텐서. 자기 자신 제외 상위 L 이웃 (idx, sim)."""
    N = Z.shape[0]
    idx = torch.empty((N, L), dtype=torch.long, device=Z.device)
    sim = torch.empty((N, L), dtype=Z.dtype, device=Z.device)
    for s in range(0, N, block):
        e = min(N, s + block)
        S = Z[s:e] @ Z.T
        S[torch.arange(e - s, device=Z.device), torch.arange(s, e, device=Z.device)] = -float("inf")
        v, i = torch.topk(S, L, dim=1)  # 정렬됨(내림차순)
        idx[s:e], sim[s:e] = i, v
    return idx, sim


def kmeans_gpu(Z, k, gen, iters=KMEANS_ITERS):
    N = Z.shape[0]
    init = gen.choice(N, size=k, replace=False)
    C = Z[torch.as_tensor(init, device=Z.device)].clone()
    for _ in range(iters):
        d = torch.cdist(Z, C)
        a = d.argmin(1)
        Cn = torch.zeros_like(C).index_add_(0, a, Z)
        cnt = torch.bincount(a, minlength=k).to(Z.dtype).unsqueeze(1)
        C = torch.where(cnt > 0, Cn / cnt.clamp(min=1), C)
    return torch.cdist(Z, C).argmin(1)


class Relations:
    """데이터셋 하나의 ψ 계산기. build() 후 psi(u, v) 사용."""

    def __init__(self, dataset, device="cuda:0", log=print):
        self.dataset, self.device, self.log = dataset, device, log
        self.cache_dir = os.path.join(CACHE, dataset)
        os.makedirs(self.cache_dir, exist_ok=True)

    def build(self):
        p = os.path.join(self.cache_dir, "psi_base.pt")
        if os.path.exists(p):
            d = torch.load(p)
            self.log(f"[relations] loaded cache {p}")
        else:
            d = self._compute()
            torch.save(d, p)
        self.N = d["N"]
        self.Xn = d["Xn"].to(self.device)
        self.Hn = d["Hn"].to(self.device)
        self.idxX, self.idxH = d["idxX"].to(self.device), d["idxH"].to(self.device)
        self.clusters = d["clusters"].to(self.device)  # (M, N)
        self.keysX = (torch.arange(self.N, device=self.device).unsqueeze(1) * self.N + self.idxX).reshape(-1)
        self.keysH = (torch.arange(self.N, device=self.device).unsqueeze(1) * self.N + self.idxH).reshape(-1)
        self.sortX, self.ordX = torch.sort(self.keysX)
        self.sortH, self.ordH = torch.sort(self.keysH)
        self.edge_keys = d["edge_keys"].to(self.device)    # 정렬됨
        self.hop2_keys = d["hop2_keys"].to(self.device)    # 정렬됨 (A + A^2 비대각)
        self.timing = d.get("timing", {})
        return self

    def _compute(self):
        t0 = time.time()
        edges, feats, _labels_unused, N = load_raw(self.dataset)  # 레이블은 쓰지 않는다
        del _labels_unused
        dev = self.device
        Xn = F.normalize(torch.log1p(torch.from_numpy(feats)), dim=1)
        A = sym_norm_adj(edges, N, self_loops=True)
        Xs = Xn.numpy()
        Hs = A @ (A @ Xs)
        Hn = F.normalize(torch.from_numpy(np.ascontiguousarray(Hs, dtype=np.float32)), dim=1)
        t_feat = time.time() - t0
        idxX, _ = topk_cos(Xn.to(dev), L_TOP)
        idxH, _ = topk_cos(Hn.to(dev), L_TOP)
        t_knn = time.time() - t0 - t_feat
        # 클러스터링: 뷰 {X', H} × k × 재시작 2
        from sklearn.decomposition import TruncatedSVD
        gen = np.random.default_rng(KMEANS_SEED)
        clusters = []
        for name, M in (("X", sp.csr_matrix(Xs)), ("H", np.asarray(Hn.numpy()))):
            Z = TruncatedSVD(n_components=SVD_DIM, algorithm="randomized", random_state=KMEANS_SEED).fit_transform(M)
            Z = torch.from_numpy(np.ascontiguousarray(Z, dtype=np.float32)).to(dev)
            for k in KS:
                for r in range(RESTARTS):
                    clusters.append(kmeans_gpu(Z, k, gen).cpu())
        clusters = torch.stack(clusters)
        t_km = time.time() - t0 - t_feat - t_knn
        # 홉
        Ab = sp.coo_matrix((np.ones(edges.shape[1]), (edges[0], edges[1])), shape=(N, N)).tocsr()
        Ab.data[:] = 1
        Ab.setdiag(0)
        Ab.eliminate_zeros()
        e = Ab.tocoo()
        edge_keys = torch.sort(torch.from_numpy(e.row.astype(np.int64) * N + e.col))[0]
        A2 = (Ab @ Ab + Ab).tocsr()
        A2.setdiag(0)
        A2.eliminate_zeros()
        a2 = A2.tocoo()
        hop2_keys = torch.sort(torch.from_numpy(a2.row.astype(np.int64) * N + a2.col))[0]
        timing = {"feat": t_feat, "knn": t_knn, "kmeans": t_km, "total": time.time() - t0}
        self.log(f"[relations] {self.dataset} computed {timing}")
        return {"N": N, "Xn": Xn, "Hn": Hn, "idxX": idxX.cpu(), "idxH": idxH.cpu(), "clusters": clusters,
                "edge_keys": edge_keys, "hop2_keys": hop2_keys, "timing": timing}

    # ------------------------------------------------------------------
    @staticmethod
    def _member(sorted_keys, q):
        pos = torch.searchsorted(sorted_keys, q).clamp(max=len(sorted_keys) - 1)
        return sorted_keys[pos] == q, pos

    def _rank(self, sorted_keys, order, q):
        hit, pos = self._member(sorted_keys, q)
        rank = (order[pos] % L_TOP) + 1
        return torch.where(hit, rank, torch.full_like(rank, L_TOP + 1))

    def candidate_pairs(self):
        """노드마다 s_X 상위 L ∪ s_H 상위 L (방향 쌍, 자기 제외). 반환 (u, v) GPU long, u 오름차순·v 오름차순."""
        N = self.N
        u = torch.arange(N, device=self.device).unsqueeze(1).expand(N, L_TOP)
        keys = torch.cat([(u * N + self.idxX).reshape(-1), (u * N + self.idxH).reshape(-1)])
        keys = torch.unique(keys)  # 정렬 + 중복 제거
        return keys // N, keys % N

    def psi(self, u, v, block=16384, with_sim=True):
        """임의 쌍의 ψ. u, v: GPU long 텐서. 반환 (P, 9) float32. with_sim=False면 s_X, s_H 자리는 0(호출 측에서 채움)."""
        out = []
        N = self.N
        if not with_sim:
            block = max(block, 1_000_000)
        for s in range(0, len(u), block):
            uu, vv = u[s:s + block], v[s:s + block]
            if with_sim:
                sX = (self.Xn[uu] * self.Xn[vv]).sum(1)
                sH = (self.Hn[uu] * self.Hn[vv]).sum(1)
            else:
                sX = sH = torch.zeros(len(uu), device=uu.device)
            q, qr = uu * N + vv, vv * N + uu
            rX, rH = self._rank(self.sortX, self.ordX, q), self._rank(self.sortH, self.ordH, q)
            rXr, rHr = self._rank(self.sortX, self.ordX, qr), self._rank(self.sortH, self.ordH, qr)
            c = (self.clusters[:, uu] == self.clusters[:, vv]).float().mean(0)
            h1 = self._member(self.edge_keys, q)[0].float()
            h2 = self._member(self.hop2_keys, q)[0].float()
            lr = lambda r: torch.log1p(r.float())
            out.append(torch.stack([sX, sH, lr(rX), lr(rH), lr(rXr), lr(rHr), c, h1, h2], 1))
        return torch.cat(out)
