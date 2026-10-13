# DIAG-ONLY 모듈 (013 순도 곡선 진단). 방법이 아니라 상한을 재는 진단이다.
# 에피소드 구성에 valid·test 노드의 실제 레이블을 읽는다(CLAUDE.md §4의 예외, 013 §0 격리 규칙).
# 이 모듈을 다른 모듈에서 import 하지 않는다. arm 접두어 diag_, records/013_purity_diag/.
#
# 출발 에피소드(A1): 011 NaQ-Feat v2 생성기(풀 U, rng 22000+seed, 중복 금지). 011 구성에서 support = anchor 1개,
#   비anchor 멤버 = query Q=5개(n = 5, test K와 무관).
# 치환: way마다 비anchor 멤버 중 anchor와 다른 클래스 노드 수를 round(ρ·n)으로 맞춘다. 유사도 s_X는 R003 정의
#   cos(L2정규화(log1p X)). 동률 처리 rng 25000+seed. 대체 노드는 풀 U 안, 에피소드에 없는 노드. 슬롯 위치 유지.
# 사용: CUDA_VISIBLE_DEVICES=<gpu> /venv/cres/bin/python -m cres.diag.purity_curve --dataset D --shot K --seed S
#        --rho {0,15,30,45,0_nocollide} --lam λ --arm diag_rho<ρ> --out_dir ... --records_dir records/013_purity_diag
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from baselines.naq.generator import NaQGenerator  # noqa: E402
from cres.teg.run import finish  # noqa: E402
from cres.teg.trainer import TEGTrainer  # noqa: E402

N_NATURAL = 1000
MAX_COLLIDE_TRIES = 50


class DiagPurityGenerator:
    # DIAG-ONLY: reads non-base labels
    def __init__(self, dataset, seed, shot, qry, U, labels, feats, rho, nocollide, dev="cuda:0"):
        self.base = NaQGenerator(dataset, seed, shot, qry, "feat", U)
        self.U = np.asarray(U)
        self.labels = labels  # 전체 레이블(진단 전용)
        self.yU = labels[self.U]
        self.q = qry
        self.rho, self.nocollide = rho, nocollide
        self.target = int(round(rho * qry))
        self.rng = np.random.default_rng(25000 + seed)
        X = torch.from_numpy(np.log1p(feats)).to(dev)
        self.Xn = F.normalize(X, dim=1)
        self.XU = self.Xn[torch.as_tensor(self.U, device=dev)]
        self.posU = {int(u): i for i, u in enumerate(self.U)}
        self.st = {"n_episodes": 0, "natural_contam_sum": 0.0, "achieved_contam_sum": 0.0, "n_ways": 0,
                   "ways_short_same": 0, "ways_short_diff": 0, "contam_in_support": 0, "contam_in_query": 0,
                   "collide_tries_sum": 0, "collide_fail": 0, "replaced_nodes": 0}

    def _sims(self, a):
        return (self.XU @ self.Xn[a]).cpu().numpy()

    def _order(self, s, idx, ascending):
        """idx를 s 오름/내림차순으로, 동률은 rng(25000+seed) 무작위."""
        keys = self.rng.random(len(idx))
        v = s[idx]
        o = np.lexsort((keys, v if ascending else -v))
        return idx[o]

    def contamination(self, sup, qry):
        ca = self.labels[sup]
        Q = qry.reshape(len(sup), -1)
        return float((self.labels[Q] != ca[:, None]).mean())

    def sample(self):
        tries = 1
        sup, qry, y = self.base.sample()
        if self.nocollide:
            while len(set(self.labels[sup].tolist())) < len(sup) and tries < MAX_COLLIDE_TRIES:
                sup, qry, y = self.base.sample()
                tries += 1
            self.st["collide_tries_sum"] += tries
            self.st["collide_fail"] += len(set(self.labels[sup].tolist())) < len(sup)
        nat = self.contamination(sup, qry)
        Q = qry.reshape(len(sup), self.q).copy()
        usedU = np.zeros(len(self.U), dtype=bool)
        usedU[[self.posU[int(x)] for x in np.concatenate([sup, qry])]] = True
        for w, a in enumerate(sup.tolist()):
            ya = self.labels[a]
            mem = Q[w]
            diff = self.labels[mem] != ya
            nd = int(diff.sum())
            if nd == self.target:
                continue
            s = self._sims(a)
            spos = np.array([self.posU[int(m)] for m in mem])
            sm = s[spos]
            free = ~usedU
            if nd > self.target:  # 다른 클래스 멤버 중 s_X 낮은 것부터 제거, 같은 클래스(U, 에피소드 밖) s_X 높은 순으로
                slots = np.where(diff)[0]
                slots = slots[np.lexsort((self.rng.random(len(slots)), sm[slots]))]
                need = nd - self.target
                cand = np.where(free & (self.yU == ya))[0]
            else:  # 같은 클래스 멤버 중 s_X 낮은 것부터 제거, 다른 클래스(U, 에피소드 밖) s_X 높은 순으로
                slots = np.where(~diff)[0]
                slots = slots[np.lexsort((self.rng.random(len(slots)), sm[slots]))]
                need = self.target - nd
                cand = np.where(free & (self.yU != ya))[0]
            cand = self._order(s, cand, False)
            k = min(need, len(cand))
            if k < need:
                self.st["ways_short_same" if nd > self.target else "ways_short_diff"] += 1
            for j in range(k):
                old, new = int(mem[slots[j]]), int(self.U[cand[j]])
                usedU[self.posU[old]] = False
                usedU[cand[j]] = True
                Q[w, slots[j]] = new
                self.st["replaced_nodes"] += 1
        qry = Q.reshape(-1)
        assert len(set(sup.tolist()) | set(qry.tolist())) == len(sup) + len(qry)
        ach = self.contamination(sup, qry)
        self.st["n_episodes"] += 1
        self.st["natural_contam_sum"] += nat
        self.st["achieved_contam_sum"] += ach
        self.st["n_ways"] += len(sup)
        self.st["contam_in_query"] += int((self.labels[Q] != self.labels[sup][:, None]).sum())
        return sup, qry, y

    def stats(self):
        n = max(self.st["n_episodes"], 1)
        return {**self.st, "natural_contam_mean": self.st["natural_contam_sum"] / n,
                "achieved_contam_mean": self.st["achieved_contam_sum"] / n, "target_per_way": self.target,
                "rho": self.rho, "nocollide": self.nocollide, "base_generator": self.base.stats()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--qry", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--rho", required=True, choices=["0", "15", "30", "45", "0_nocollide"])
    ap.add_argument("--lam", type=float, required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--records_dir", default=None)
    a = ap.parse_args()
    print("DIAG: non-base labels used for episode construction", flush=True)
    assert a.arm.startswith("diag_")
    t0 = time.time()
    torch.set_num_threads(3)
    os.makedirs(a.out_dir, exist_ok=True)
    tr = TEGTrainer(a.dataset, a.seed, a.shot, qry=a.qry, epochs=a.epochs, episodes=a.episodes, device="cuda:0")
    t_init = time.time() - t0
    U = np.where(~np.isin(tr.labels_np, tr.class_list_train))[0]
    rho = 0.0 if a.rho.startswith("0") else int(a.rho) / 100
    nocollide = a.rho == "0_nocollide"
    feats = tr.features.cpu().numpy()
    print(f"DIAG label sets used for episode construction: valid {tr.class_list_valid} test {tr.class_list_test}", flush=True)
    # 자연 오염률(NaQ 점): 같은 seed의 새 NaQ-Feat v2 생성기로 1000 에피소드(치환 없음)
    nat_g = DiagPurityGenerator(a.dataset, a.seed, a.shot, a.qry, U, tr.labels_np, feats, 0.0, False)
    nat = [nat_g.contamination(*nat_g.base.sample()[:2]) for _ in range(N_NATURAL)]
    del nat_g
    g = DiagPurityGenerator(a.dataset, a.seed, a.shot, a.qry, U, tr.labels_np, feats, rho, nocollide)
    dev = tr.device

    def fn():
        sup, qry, y = g.sample()
        return sup, qry, torch.LongTensor(y).to(dev)

    fn.gen = g
    res = tr.train(fn, a.lam)
    st = g.stats()
    note = None
    if abs(st["achieved_contam_mean"] - st["target_per_way"] / a.qry) > 1e-9:
        note = f"achieved {st['achieved_contam_mean']:.4f} != target {st['target_per_way']}/{a.qry}: ways_short_same {st['ways_short_same']}, ways_short_diff {st['ways_short_diff']}"
    finish(a, tr, res, t0, t_init, fn, extra_meta={
        "diag": True, "rho": rho, "nocollide": nocollide, "natural_contam_1000": float(np.mean(nat)),
        "achieved_contam": st["achieved_contam_mean"], "target_contam": st["target_per_way"] / a.qry, "contam_note": note,
        "contam_in_support_nodes": st["contam_in_support"], "contam_in_query_nodes": st["contam_in_query"],
        "label_use": "DIAG: valid/test labels for pseudo-episode construction"})


if __name__ == "__main__":
    main()
