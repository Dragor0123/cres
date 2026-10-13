# NaQ식 pseudo-episode 생성기 (006, 011에서 수정). refs/NaQ(cfe5373)는 라이선스 표시가 확인되지 않아 코드를 복사하지 않고,
# 논문(Unsupervised Episode Generation for Graph Meta-learning, ICML'24)과 코드를 읽고 재구현했다.
# 읽은 위치(사실 확인용):
#   NaQ utils.py:28-50 graph_diffusion — Feat: 원시 특징 행 L2 정규화 후 코사인 행렬. Diff: torch_geometric GDC
#     transition_matrix(normalization='sym', 자기 루프 추가 없음) → diffusion_matrix_exact(method='ppr', alpha=PPR_alpha).
#     두 경우 모두 대각 0(자기 자신 제외).
#   NaQ arg.py:45 PPR_alpha 기본 0.1.
#   NaQ task_generator.py spt_sampling / query_generation_NaQ — 원 구성: way마다 무작위 노드 1개(support), 그 행의 상위 q개(query).
# 이 리포의 적응(006 지시서): anchor 5개(풀 U에서 무작위) → anchor마다 상위 (K+Q−1)개 → support = anchor + 처음 K−1개, query = 다음 Q개.
#   way 사이 충돌(같은 노드·같은 실제 클래스)은 막지 않는다.
#   이웃 후보도 풀 U 안으로 제한한다(005와 같은 풀; 원 NaQ는 전체 노드).
#   Diff의 PPR은 역행렬 대신 멱반복 200회로 계산(Π = α Σ_t ((1−α)T)^t, 잘림 오차 ≤ (1−α)^200 ≈ 7e-10).
# 011 수정(R004 §6, NaQGenerator = v2; 006 구성은 NaQGeneratorV1로 남김, superseded):
#   1. support는 원 NaQ처럼 way마다 anchor 1개(test K와 무관; NaQ task_generator.py:61, :98 spt_to_sample = 1,
#      :112-130 spt_sampling). query = anchor 유사도 목록의 상위 Q개(:133-155 query_generation_NaQ).
#   2. 에피소드 안 중복 금지: anchor 5개를 먼저 뽑아 예약하고, way를 순서대로 채우며 이미 쓴 노드는 목록에서 건너뛴다.
#      목록(길이 TOP_V2=50)이 바닥나면 그 anchor를 버리고 같은 rng로 새 anchor를 뽑는다(재추첨 횟수 기록).
#   3. 풀 U(base 제외) 유지, rng 22000+seed 유지. 이웃 표 캐시 results/011/<ds>/.
# 생성기는 레이블을 읽지 않는다. 풀 U(base가 아닌 노드)는 호출 측(run.py)이 분할 파일로 정해 넘긴다.
import os

import numpy as np
import torch
import torch.nn.functional as F

from cres.data import ROOT, load_raw

TOP = 9  # max(K)+Q-1 = 5+5-1 (006, v1)
TOP_V2 = 50  # 011 §1-4
ALPHA = 0.1
PPR_ITERS = 200


def _topk_in_pool(score_fn, U, dev, top=TOP, block=1024):
    Ut = torch.as_tensor(U, device=dev)
    out = []
    for s in range(0, len(U), block):
        S = score_fn(Ut[s:s + block], Ut)  # (b, |U|)
        S[torch.arange(S.shape[0], device=dev), torch.arange(s, s + S.shape[0], device=dev)] = -float("inf")
        _, order = torch.sort(-S, dim=1, stable=True)  # 동점: U 안 노드 id 오름차순
        out.append(Ut[order[:, :top]])
    return torch.cat(out).cpu().numpy()


def neighbor_table(dataset, kind, U, seed, dev="cuda:0", top=TOP, tag="006", pool="U"):
    """U의 각 노드에 대해 U 안 상위 top 이웃(유사도 내림차순). 캐시 results/<tag>/<ds>/."""
    d = os.path.join(ROOT, "results", tag, dataset)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"naq_{kind}_seed{seed}_top{top}.npy" if pool == "U" else f"naq_{kind}_{pool}_top{top}.npy")
    if os.path.exists(p):
        return np.load(p)
    edges, feats, _unused, N = load_raw(dataset)
    del _unused
    if kind == "feat":
        X = F.normalize(torch.from_numpy(feats).to(dev), dim=1)
        nb = _topk_in_pool(lambda a, u: X[a] @ X[u].T, U, dev, top=top)
    elif kind == "diff":
        ei = torch.as_tensor(edges, device=dev)
        w = torch.ones(ei.shape[1], device=dev)
        deg = torch.zeros(N, device=dev).index_add_(0, ei[0], w)
        dinv = deg.pow(-0.5)
        dinv[torch.isinf(dinv)] = 0
        T = torch.sparse_coo_tensor(ei, dinv[ei[0]] * w * dinv[ei[1]], (N, N)).coalesce()
        Ut = torch.as_tensor(U, device=dev)
        rows = []
        for s in range(0, len(U), 2048):
            cols = Ut[s:s + 2048]
            E = torch.zeros((N, len(cols)), device=dev)
            E[cols, torch.arange(len(cols), device=dev)] = 1.0
            X = ALPHA * E
            for _ in range(PPR_ITERS):
                X = (1 - ALPHA) * torch.sparse.mm(T, X) + ALPHA * E
            # Π 대칭(T 대칭) → 열 = 행. 풀 U 안 점수만.
            S = X[Ut].T  # (b, |U|)
            S[torch.arange(len(cols), device=dev), torch.arange(s, s + len(cols), device=dev)] = -float("inf")
            _, order = torch.sort(-S, dim=1, stable=True)
            rows.append(Ut[order[:, :top]].cpu())
        nb = torch.cat(rows).numpy()
    else:
        raise ValueError(kind)
    np.save(p, nb)
    return nb


class NaQGeneratorV1:
    """006 구성(superseded by 011): support = anchor + 상위 K−1, query = 다음 Q, 중복 허용."""
    def __init__(self, dataset, seed, shot, qry, kind, U, n_way=5, dev="cuda:0"):
        self.U = np.asarray(U)
        self.k, self.q, self.n = shot, qry, n_way
        self.nb = neighbor_table(dataset, kind, self.U, seed, dev)
        self.rng = np.random.default_rng(22000 + seed)
        self.n_sampled, self.n_dup = 0, 0

    def sample(self):
        a = self.rng.choice(len(self.U), self.n, replace=False)
        sup, qry = [], []
        for i in a:
            lst = self.nb[i]
            sup.extend([int(self.U[i])] + [int(x) for x in lst[: self.k - 1]])
            qry.extend(int(x) for x in lst[self.k - 1: self.k - 1 + self.q])
        y = [w for w in range(self.n) for _ in range(self.q)]
        self.n_sampled += 1
        allnodes = sup + qry
        self.n_dup += len(allnodes) != len(set(allnodes))
        return np.array(sup), np.array(qry), y

    def stats(self):
        return {"n_episodes": self.n_sampled, "episodes_with_duplicate_node": self.n_dup}


class NaQGenerator:
    """011 v2: support = anchor 1개(원 NaQ), query = 중복 없는 상위 Q개. 레이블을 읽지 않는다.
    pool="U"(base 제외, 기본) 또는 "all"(전체 노드, 원 NaQ 풀; 참고 arm naqfeat_allpool)."""
    def __init__(self, dataset, seed, shot, qry, kind, U, n_way=5, dev="cuda:0", pool="U"):
        self.U = np.asarray(U)
        self.k, self.q, self.n = shot, qry, n_way
        self.nb = neighbor_table(dataset, kind, self.U, seed, dev, top=TOP_V2, tag="011", pool=pool)
        self.rng = np.random.default_rng(22000 + seed)
        self.n_sampled, self.n_redraw, self.n_ep_redraw = 0, 0, 0
        self.last_anchor_pos = None

    def _fill(self, i, used):
        out = []
        for x in self.nb[i]:
            x = int(x)
            if x in used:
                continue
            out.append(x)
            if len(out) == self.q:
                return out
        return None

    def sample(self):
        a = [int(i) for i in self.rng.choice(len(self.U), self.n, replace=False)]
        used = {int(self.U[i]) for i in a}  # anchor 예약
        sup, qry, pos = [], [], []
        redraw = 0
        for w in range(self.n):
            i = a[w]
            while True:
                q = self._fill(i, used)
                if q is not None:
                    break
                # 목록 바닥: anchor 버리고 재추첨(아직 쓰지 않은 노드)
                used.discard(int(self.U[i]))
                redraw += 1
                while True:
                    i = int(self.rng.integers(len(self.U)))
                    if int(self.U[i]) not in used:
                        break
                used.add(int(self.U[i]))
            used.update(q)
            sup.append(int(self.U[i]))
            qry.extend(q)
            pos.append(i)
        y = [w for w in range(self.n) for _ in range(self.q)]
        self.n_sampled += 1
        self.n_redraw += redraw
        self.n_ep_redraw += redraw > 0
        self.last_anchor_pos = pos
        allnodes = sup + qry
        assert len(allnodes) == len(set(allnodes))
        return np.array(sup), np.array(qry), y

    def stats(self):
        return {"n_episodes": self.n_sampled, "anchor_redraws": self.n_redraw, "episodes_with_redraw": self.n_ep_redraw,
                "episodes_with_duplicate_node": 0}
