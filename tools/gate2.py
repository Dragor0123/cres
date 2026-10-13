# 005 관문 2 (G2, P03). Pseudo-Class Core 순도 vs 같은 크기 top-K pseudo-class.
# 레이블 사용(경로 분리): core·B1–B3 구성에는 쓰지 않는다. 그룹 구분(풀 U = base 아닌 노드, valid/test anchor 구분)과
# 순도·충돌 지표 계산에만 쓴다. τ 선택은 valid anchor, 판정은 test anchor.
# 사용: CUDA_VISIBLE_DEVICES=<UUID> /venv/cres/bin/python tools/gate2.py --dataset dblp --seeds 0,1,2
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cres.core import RScorer, greedy_core, stable_topk  # noqa: E402
from cres.data import ROOT, load_raw, load_split  # noqa: E402
from cres.relations import Relations  # noqa: E402

N_CAND = 30
MS = [6, 10]
TAUS = [0.3, 0.5, 0.7]
TAU_OUT = 0.3
REC = os.path.join(ROOT, "records", "005_gate2")


def paired(d):
    d = np.asarray(d, dtype=float)
    if len(d) < 2:
        return {"mean": float(d.mean()) if len(d) else None, "se": None, "n": int(len(d)), "clear": False}
    m, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
    return {"mean": m, "se": se, "n": int(len(d)), "clear": bool(m > 0 and m > 2 * se)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--seeds", default="0,1,2")
    a = ap.parse_args()
    dev = "cuda:0"
    os.makedirs(REC, exist_ok=True)
    R = Relations(a.dataset, dev).build()
    _, _, labels, N = load_raw(a.dataset)
    lab_t = torch.as_tensor(labels, device=dev)
    result = {}
    for seed in map(int, a.seeds.split(",")):
        t0 = time.time()
        split = load_split(a.dataset, seed)
        S = RScorer(R, os.path.join(R.cache_dir, f"c1_seed{seed}.pt"))
        U = np.where(~np.isin(labels, split["base"]))[0]  # 풀(레이블로 base만 제외 — 004·005 규칙)
        grpU = np.where(np.isin(labels[U], split["valid"]), "valid", "test")
        Ut = torch.as_tensor(U, device=dev)
        posU = torch.full((N,), -1, dtype=torch.long, device=dev)
        posU[Ut] = torch.arange(len(U), device=dev)
        cand, top_h, top_x = [], [], []
        for s in range(0, len(U), 512):
            Ab = Ut[s:s + 512]
            self_cols = posU[Ab]
            rb = S.block(Ab, Ut, posU)
            cand.append(Ut[stable_topk(rb, N_CAND, self_cols)])
            top_h.append(Ut[stable_topk(R.Hn[Ab] @ R.Hn[Ut].T, max(MS) - 1, self_cols)])
            top_x.append(Ut[stable_topk(R.Xn[Ab] @ R.Xn[Ut].T, max(MS) - 1, self_cols)])
        cand, top_h, top_x = torch.cat(cand), torch.cat(top_h), torch.cat(top_x)
        nodes = torch.cat([Ut.unsqueeze(1), cand], 1)  # (|U|, 31), 0 = anchor
        Rw = S.within(nodes)
        t_r = time.time() - t0
        same = (lab_t[nodes] == lab_t[Ut].unsqueeze(1)).float()  # (|U|, 31) 지표용
        pur_of = lambda ids: (lab_t[ids] == lab_t[Ut].unsqueeze(1)).float().mean(1).cpu().numpy()
        is_valid, is_test = grpU == "valid", grpU == "test"
        res_seed = {"n_U": int(len(U)), "n_valid_anchor": int(is_valid.sum()), "n_test_anchor": int(is_test.sum()), "sec_r": t_r, "m": {}}
        for m in MS:
            B1, B2, B3 = pur_of(top_h[:, :m - 1]), pur_of(top_x[:, :m - 1]), pur_of(cand[:, :m - 1])
            tau_tab = {}
            cores = {}
            for tau in TAUS:
                acc, mem = greedy_core(Rw, m, tau)
                acc_np = acc.cpu().numpy()
                mem_c = mem.clamp(min=0)
                pc = (same.gather(1, mem_c[:, 1:]).mean(1)).cpu().numpy()
                cores[tau] = (acc_np, mem, pc)
                row = {}
                for gname, gm in (("valid", is_valid), ("test", is_test)):
                    sel = gm & acc_np
                    row[gname] = {"accept_rate": float(acc_np[gm].mean()), "n_accept": int(sel.sum()),
                                  "purity_core": float(pc[sel].mean()) if sel.any() else None}
                tau_tab[str(tau)] = row
            ok = [t for t in TAUS if tau_tab[str(t)]["valid"]["accept_rate"] >= 0.3 and tau_tab[str(t)]["valid"]["purity_core"] is not None]
            if ok:
                best = max(tau_tab[str(t)]["valid"]["purity_core"] for t in ok)
                tau_sel = min(t for t in ok if tau_tab[str(t)]["valid"]["purity_core"] == best)
            else:
                tau_sel = None
            mres = {"tau_table": tau_tab, "tau_selected": tau_sel,
                    "B1_all_test": float(B1[is_test].mean()), "B2_all_test": float(B2[is_test].mean()), "B3_all_test": float(B3[is_test].mean())}
            if tau_sel is not None:
                acc_np, mem, pc = cores[tau_sel]
                sel = is_test & acc_np
                rej = is_test & ~acc_np
                mres["test_accept_rate"] = float(acc_np[is_test].mean())
                mres["purity_accepted_test"] = {"core": float(pc[sel].mean()), "B1": float(B1[sel].mean()), "B2": float(B2[sel].mean()), "B3": float(B3[sel].mean())}
                mres["B1_rejected_test"] = float(B1[rej].mean()) if rej.any() else None
                mres["diff"] = {"core_minus_B1": paired(pc[sel] - B1[sel]), "core_minus_B2": paired(pc[sel] - B2[sel]),
                                "core_minus_B3": paired(pc[sel] - B3[sel]), "B3_minus_B1": paired(B3[sel] - B1[sel])}
                mres["pass_seed"] = bool(mres["diff"]["core_minus_B1"]["clear"] and mres["test_accept_rate"] >= 0.3)
                # core 은행 (선택 τ, 채택된 모든 U anchor)
                mem_nodes = nodes.gather(1, mem.clamp(min=0)).cpu().numpy()
                bank = {"dataset": a.dataset, "seed": seed, "m": m, "tau_in": tau_sel, "member_order": "anchor first, then greedy order",
                        "cores": [{"anchor": int(U[i]), "members": [int(x) for x in mem_nodes[i]]} for i in np.flatnonzero(acc_np)]}
                bp = os.path.join(REC, f"core_bank_{a.dataset}_seed{seed}_m{m}.json")
                txt = json.dumps(bank, separators=(",", ":"))
                if len(txt) <= 5 * 2**20:
                    open(bp, "w").write(txt)
                    mres["core_bank"] = os.path.relpath(bp, ROOT)
                else:
                    bp = os.path.join(R.cache_dir, f"core_bank_seed{seed}_m{m}.json")
                    open(bp, "w").write(txt)
                    mres["core_bank"] = os.path.relpath(bp, ROOT) + " (results only, > 5 MB)"
                # 충돌 시뮬레이션 (판정 아님)
                rng = np.random.default_rng(24000 + seed)
                test_idx = np.flatnonzero(is_test)
                acc_test_idx = np.flatnonzero(sel)
                labU = labels[U]
                coll_naq, coll_cres, fails, redraws = 0, 0, 0, []
                for _ in range(1000):
                    pick = rng.choice(test_idx, 5, replace=False)
                    coll_naq += len(set(labU[pick])) < 5
                    ok_draw = False
                    for t in range(51):
                        pc5 = rng.choice(acc_test_idx, 5, replace=False)
                        an = Ut[torch.as_tensor(pc5, device=dev)]
                        uu = an.repeat_interleave(5)
                        vv = an.repeat(5)
                        mm = uu != vv
                        if S.pairs(uu[mm], vv[mm]).max().item() <= TAU_OUT:
                            ok_draw = True
                            break
                    redraws.append(t)
                    fails += not ok_draw
                    coll_cres += len(set(labU[pc5])) < 5
                mres["collision"] = {"naq_rate": coll_naq / 1000, "cres_rate": coll_cres / 1000, "cres_fail_rate": fails / 1000,
                                     "cres_redraw_mean": float(np.mean(redraws))}
                # anchor별 기록
                with open(os.path.join(REC, f"anchor_{a.dataset}_seed{seed}_m{m}.csv"), "w") as f:
                    f.write("anchor,group,accepted,core,B1,B2,B3\n")
                    for i in range(len(U)):
                        f.write(f"{U[i]},{grpU[i]},{int(acc_np[i])},{pc[i]:.4f},{B1[i]:.4f},{B2[i]:.4f},{B3[i]:.4f}\n")
            else:
                mres["pass_seed"] = False
                mres["note"] = "no tau_in with valid accept rate >= 0.3"
            res_seed["m"][str(m)] = mres
            print(json.dumps({"seed": seed, "m": m, "tau": tau_sel, "test_accept": mres.get("test_accept_rate"),
                              "pur": mres.get("purity_accepted_test"), "d": mres.get("diff", {}).get("core_minus_B1"),
                              "pass": mres["pass_seed"], "coll": mres.get("collision")}), flush=True)
        res_seed["sec"] = time.time() - t0
        result[seed] = res_seed
        json.dump(res_seed, open(os.path.join(REC, f"summary_{a.dataset}_seed{seed}.json"), "w"), indent=1)
    passed = all(result[s]["m"]["10"]["pass_seed"] for s in result)
    json.dump({"dataset": a.dataset, "G2_dataset_pass_m10": passed}, open(os.path.join(REC, f"verdict_{a.dataset}.json"), "w"), indent=1)
    print("G2_DATASET", a.dataset, "PASS" if passed else "FAIL")


if __name__ == "__main__":
    main()
