# 004 관문 1 (G1, P02). calibrator 학습·평가.
# 레이블 사용(경로 분리, CLAUDE.md §4): base–base 쌍 레이블 = calibrator 학습, valid–valid 쌍 = C 선택·MLP 조기 종료,
# test–test 쌍 = 지표만. 사용 레이블 집합은 로그와 summary json에 남긴다.
# 사용: CUDA_VISIBLE_DEVICES=<UUID> /venv/cres/bin/python tools/gate1.py --dataset Amazon_clothing --seeds 0,1,2
import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cres.data import ROOT, load_raw, load_split  # noqa: E402
from cres.relations import PSI_NAMES, Relations  # noqa: E402

CS = [0.01, 0.1, 1, 10]
MAX_PAIRS = 200_000
TOPN = 10
REC = os.path.join(ROOT, "records", "004_gate1")


def sub_idx(n, rng, m=MAX_PAIRS):
    return np.arange(n) if n <= m else np.sort(rng.choice(n, m, replace=False))


def anchor_purity(u, v, score, same, topn=TOPN):
    """anchor u마다 점수 상위 topn(동점은 v 오름차순) 중 같은 클래스 비율. 후보 < topn인 anchor 제외."""
    order = np.lexsort((v, -score, u))
    uu, ss = u[order], same[order]
    starts = np.r_[0, np.flatnonzero(np.diff(uu)) + 1]
    counts = np.diff(np.r_[starts, len(uu)])
    keep = counts >= topn
    anchors = uu[starts[keep]]
    pur = np.array([ss[s:s + topn].mean() for s in starts[keep]])
    return anchors, pur, int((~keep).sum())


def ece(prob, y, bins=10):
    b = np.minimum((prob * bins).astype(int), bins - 1)
    e = 0.0
    for i in range(bins):
        m = b == i
        if m.any():
            e += m.mean() * abs(prob[m].mean() - y[m].mean())
    return float(e)


class MLP(torch.nn.Module):
    def __init__(self, d):
        super().__init__()
        self.f = torch.nn.Sequential(torch.nn.Linear(d, 32), torch.nn.ReLU(), torch.nn.Linear(32, 32), torch.nn.ReLU(), torch.nn.Linear(32, 1))

    def forward(self, x):
        return self.f(x).squeeze(1)


def train_mlp(Xtr, ytr, Xva, yva, seed, dev):
    with torch.random.fork_rng(devices=[dev] if dev.startswith("cuda") else []):
        torch.manual_seed(21000 + seed)
        m = MLP(Xtr.shape[1]).to(dev)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        Xt, yt = torch.tensor(Xtr, device=dev), torch.tensor(ytr, dtype=torch.float32, device=dev)
        Xv = torch.tensor(Xva, device=dev)
        best, best_state, bad, ep_best = -1, None, 0, 0
        g = torch.Generator(device="cpu").manual_seed(21000 + seed)
        for ep in range(50):
            m.train()
            perm = torch.randperm(len(Xt), generator=g).to(dev)
            for s in range(0, len(Xt), 4096):
                i = perm[s:s + 4096]
                loss = torch.nn.functional.binary_cross_entropy_with_logits(m(Xt[i]), yt[i])
                opt.zero_grad(); loss.backward(); opt.step()
            m.eval()
            with torch.no_grad():
                auc = roc_auc_score(yva, m(Xv).cpu().numpy())
            if auc > best:
                best, best_state, bad, ep_best = auc, {k: v.clone() for k, v in m.state_dict().items()}, 0, ep
            else:
                bad += 1
                if bad >= 5:
                    break
        m.load_state_dict(best_state)
        m.eval()
    return m, best, ep_best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--seeds", default="0,1,2")
    a = ap.parse_args()
    dev = "cuda:0"
    t0 = time.time()
    os.makedirs(REC, exist_ok=True)
    R = Relations(a.dataset, dev).build()
    u_t, v_t = R.candidate_pairs()
    P = R.psi(u_t, v_t).cpu().numpy().astype(np.float64)
    u, v = u_t.cpu().numpy(), v_t.cpu().numpy()
    t_psi = time.time() - t0
    _, _, labels, N = load_raw(a.dataset)  # 레이블: 아래 경로에서 그룹별로만 사용
    same_all = labels[u] == labels[v]
    out_all = {}
    for seed in map(int, a.seeds.split(",")):
        ts = time.time()
        split = load_split(a.dataset, seed)
        grp = np.full(N, -1)
        for gi, g in enumerate(("base", "valid", "test")):
            grp[np.isin(labels, split[g])] = gi
        m_b = (grp[u] == 0) & (grp[v] == 0)
        m_v = (grp[u] == 1) & (grp[v] == 1)
        m_t = (grp[u] == 2) & (grp[v] == 2)
        rng = np.random.default_rng(21000 + seed)
        mu, sd = P[m_b].mean(0), P[m_b].std(0)
        sd[sd == 0] = 1.0
        Z = (P - mu) / sd
        ib = np.flatnonzero(m_b)[sub_idx(m_b.sum(), rng)]
        iv = np.flatnonzero(m_v)[sub_idx(m_v.sum(), rng)]
        Xtr, ytr = Z[ib], same_all[ib].astype(int)
        Xva, yva = Z[iv], same_all[iv].astype(int)
        # C1
        c_auc = {}
        models = {}
        for C in CS:
            lr = LogisticRegression(penalty="l2", C=C, solver="lbfgs", max_iter=1000).fit(Xtr, ytr)
            c_auc[C] = roc_auc_score(yva, lr.decision_function(Xva))
            models[C] = lr
        best_auc = max(c_auc.values())
        C_sel = min(C for C in CS if c_auc[C] == best_auc)
        lr = models[C_sel]
        # C2
        mlp, mlp_val_auc, mlp_ep = train_mlp(Xtr.astype(np.float32), ytr, Xva.astype(np.float32), yva, seed, dev)
        # test–test 점수
        it = np.flatnonzero(m_t)
        ut, vt, yt = u[it], v[it], same_all[it]
        Pt, Zt = P[it], Z[it]
        sX, sH, c = Pt[:, 0], Pt[:, 1], Pt[:, 6]
        with torch.no_grad():
            c2 = torch.sigmoid(mlp(torch.tensor(Zt.astype(np.float32), device=dev))).cpu().numpy().astype(np.float64)
        scores = {"s_X": sX, "s_H": sH, "c": c, "avg": (sX + sH + c) / 3, "C1": lr.predict_proba(Zt)[:, 1], "C2": c2}
        pur, anchors_ref, n_excl = {}, None, None
        pair_metrics = {}
        for name, sc in scores.items():
            anc, p_, n_ex = anchor_purity(ut, vt, sc, yt.astype(float))
            if anchors_ref is None:
                anchors_ref, n_excl = anc, n_ex
            assert np.array_equal(anc, anchors_ref)
            pur[name] = p_
            pair_metrics[name] = {"auroc": float(roc_auc_score(yt, sc)), "ap": float(average_precision_score(yt, sc)),
                                  "purity_mean": float(p_.mean())}
        for name in ("C1", "C2"):
            pair_metrics[name]["ece"] = ece(scores[name], yt.astype(float))
        comp = max(("s_X", "s_H", "avg"), key=lambda k: pur[k].mean())
        d = pur["C1"] - pur[comp]
        diff = {"vs": comp, "mean": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d))), "n_anchor": int(len(d))}
        diff["clear"] = bool(diff["mean"] > 0 and diff["mean"] > 2 * diff["se"])
        other = {}
        for k in ("s_X", "s_H", "c", "avg", "C2"):
            dd = pur["C1"] - pur[k]
            other[k] = {"mean": float(dd.mean()), "se": float(dd.std(ddof=1) / np.sqrt(len(dd)))}
        summ = {
            "dataset": a.dataset, "seed": seed, "labels_used": {"train": "base-base pairs", "select": "valid-valid pairs", "metric": "test-test pairs"},
            "n_pairs": {"all": int(len(u)), "base_base": int(m_b.sum()), "valid_valid": int(m_v.sum()), "test_test": int(m_t.sum()),
                        "train_used": int(len(ib)), "valid_used": int(len(iv))},
            "pos_rate": {"base_base": float(same_all[m_b].mean()), "valid_valid": float(same_all[m_v].mean()), "test_test": float(yt.mean())},
            "C_valid_auroc": {str(k): float(x) for k, x in c_auc.items()}, "C_selected": C_sel,
            "C1_coef": dict(zip(PSI_NAMES, map(float, lr.coef_[0]))), "C1_intercept": float(lr.intercept_[0]),
            "std_mean": dict(zip(PSI_NAMES, map(float, mu))), "std_sd": dict(zip(PSI_NAMES, map(float, sd))),
            "C2_valid_auroc": float(mlp_val_auc), "C2_best_epoch": int(mlp_ep),
            "n_anchor": int(len(anchors_ref)), "n_anchor_excluded": n_excl,
            "methods": pair_metrics, "G1_diff": diff, "C1_minus": other, "sec": time.time() - ts,
        }
        out_all[seed] = summ
        json.dump(summ, open(os.path.join(REC, f"summary_{a.dataset}_seed{seed}.json"), "w"), indent=1)
        with open(os.path.join(REC, f"anchor_purity_{a.dataset}_seed{seed}.csv"), "w") as f:
            f.write("anchor," + ",".join(scores) + "\n")
            for i, an in enumerate(anchors_ref):
                f.write(f"{an}," + ",".join(f"{pur[k][i]:.1f}" for k in scores) + "\n")
        # C1 은 005에서 쓴다(results/에 저장)
        torch.save({"coef": lr.coef_[0], "intercept": lr.intercept_[0], "mu": mu, "sd": sd, "C": C_sel},
                   os.path.join(R.cache_dir, f"c1_seed{seed}.pt"))
        print(json.dumps({"seed": seed, "C": C_sel, "G1_diff": diff, "purity": {k: round(v_["purity_mean"], 4) for k, v_ in pair_metrics.items()}}), flush=True)
    print("TOTAL_SEC", time.time() - t0, "PSI_SEC", t_psi, "PSI_TIMING", R.timing)


if __name__ == "__main__":
    main()
