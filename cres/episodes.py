# CRES pseudo-episode 생성기 (008 지시서 §1, 014에서 탐색용으로 실행). 레이블을 읽지 않는다.
# 입력: 005 core 은행 records/005_gate2/core_bank_<ds>_seed<s>_m<K+Q>.json(선택 τ_in), r = C1(ψ) (results/004/<ds>/c1_seed<s>.pt).
# 한 에피소드 (rng 23000+seed):
#   1. core 5개 추첨, 조건 max_{i≠j} r(a_i, a_j) ≤ 0.3(양방향 모두). 최대 50회, 실패 시 마지막 추첨 사용·횟수 기록.
#   2. support: core 안에서 다른 멤버와의 평균 r(u, ·)이 가장 큰 K개(동률은 core 안 순서 앞쪽).
#   3. query: 나머지 Q개. 어떤 query q에서 max_{다른 way} r(a', q) > r(a, q)이면 그 core를 다시 추첨
#      (새 core는 현재 선택에 없는 core, 1의 anchor 조건도 만족하도록 최대 50회). 에피소드당 재추첨 최대 50회, 넘으면 그대로 쓰고 기록.
#      r 방향은 005 core 구성과 같이 anchor가 첫 번째(r(a, q)).
#   4. "support와 다른 변이 포함" 조건은 이번 pilot에서 구현하지 않는다.
# 지역 레이블 0–4.
import json
import os

import numpy as np
import torch

from cres.core import RScorer
from cres.data import ROOT
from cres.relations import Relations

TAU_ANCHOR = 0.3
MAX_TRIES = 50


class CRESGenerator:
    def __init__(self, dataset, seed, shot, qry, n_way=5, dev="cuda:0"):
        self.k, self.q, self.n, self.dev = shot, qry, n_way, dev
        m = shot + qry
        p = os.path.join(ROOT, "records", "005_gate2", f"core_bank_{dataset}_seed{seed}_m{m}.json")
        bank = json.load(open(p))
        assert bank["m"] == m
        self.bank_path, self.tau_in = os.path.relpath(p, ROOT), bank["tau_in"]
        self.cores = np.array([c["members"] for c in bank["cores"]], dtype=np.int64)
        assert self.cores.shape[1] == m
        self.anchors = self.cores[:, 0]
        R = Relations(dataset, dev, log=lambda *x: None).build()
        self.S = RScorer(R, os.path.join(R.cache_dir, f"c1_seed{seed}.pt"))
        self.rng = np.random.default_rng(23000 + seed)
        self.st = {"n_episodes": 0, "anchor_tries_sum": 0, "anchor_fail": 0, "query_redraws": 0,
                   "episodes_with_query_redraw": 0, "query_redraw_cap_hit": 0, "episodes_with_duplicate_node": 0}

    def r(self, u, v):
        u = torch.as_tensor(np.asarray(u), device=self.dev)
        v = torch.as_tensor(np.asarray(v), device=self.dev)
        return self.S.pairs(u, v).cpu().numpy()

    def _anchor_ok(self, idx):
        a = self.anchors[idx]
        n = len(a)
        uu, vv = np.repeat(a, n), np.tile(a, n)
        m = uu != vv
        return self.r(uu[m], vv[m]).max() <= TAU_ANCHOR

    def _split(self, ci):
        nodes = self.cores[ci]
        W = self.S.within(torch.as_tensor(nodes[None], device=self.dev))[0].cpu().numpy()
        m = len(nodes)
        mean_r = (W.sum(1) - np.diag(W)) / (m - 1)
        order = np.argsort(-mean_r, kind="stable")
        sp = np.sort(order[: self.k])
        qp = np.array([i for i in range(m) if i not in set(sp.tolist())])
        return nodes[sp], nodes[qp]

    def _bad_way(self, sel, parts):
        a = self.anchors[sel]
        for w in range(len(sel)):
            qn = parts[w][1]
            own = self.r(np.full(len(qn), a[w]), qn)
            others = [self.r(np.full(len(qn), a[x]), qn) for x in range(len(sel)) if x != w]
            if (np.max(others, axis=0) > own).any():
                return w
        return None

    def sample(self):
        tries = 0
        while True:
            sel = self.rng.choice(len(self.cores), self.n, replace=False)
            tries += 1
            if self._anchor_ok(sel) or tries >= MAX_TRIES:
                break
        self.st["anchor_tries_sum"] += tries
        self.st["anchor_fail"] += not self._anchor_ok(sel)
        parts = [self._split(c) for c in sel]
        redraws = 0
        while redraws < MAX_TRIES:
            w = self._bad_way(sel, parts)
            if w is None:
                break
            redraws += 1
            trial, c = sel.copy(), int(sel[w])
            for _ in range(MAX_TRIES):
                c = int(self.rng.integers(len(self.cores)))
                if c in set(sel.tolist()):
                    continue
                trial = sel.copy()
                trial[w] = c
                if self._anchor_ok(trial):
                    break
            sel = trial
            parts[w] = self._split(c)
        else:
            self.st["query_redraw_cap_hit"] += self._bad_way(sel, parts) is not None
        self.st["query_redraws"] += redraws
        self.st["episodes_with_query_redraw"] += redraws > 0
        sup = np.concatenate([p[0] for p in parts])
        qry = np.concatenate([p[1] for p in parts])
        allnodes = np.concatenate([sup, qry])
        self.st["episodes_with_duplicate_node"] += len(set(allnodes.tolist())) < len(allnodes)
        self.st["n_episodes"] += 1
        self.last_sel = sel
        y = [w for w in range(self.n) for _ in range(self.q)]
        return sup, qry, y

    def stats(self):
        return {**self.st, "bank": self.bank_path, "tau_in": self.tau_in, "n_cores": int(len(self.cores))}
