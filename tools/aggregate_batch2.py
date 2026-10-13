# 2차 큐 집계(012–016). records/ 만 읽는다. 006은 superseded(011 결과만 사용).
# 사용: /venv/cres/bin/python tools/aggregate_batch2.py  → records/016_summary/aggregate.json, tables.md
import csv
import json
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(ROOT, "records")
DS = ["Amazon_clothing", "Amazon_electronics", "dblp"]
KS = [1, 5]
SEEDS = [0, 1, 2]
LAMS = ["0.5", "1.0"]
DIRS = {"sup": "003_teg_port", "sup2": "012_sup2", "naqfeat": "011_naq_v2", "naqdiff": "011_naq_v2",
        "naqfeat_allpool": "011_naq_v2", "cres": "014_cres_pilot", "vision": "007_vision", "tegorig": "015_tegorig",
        "diag": "013_purity_diag"}
DIAG_ARMS = ["diag_rho0", "diag_rho15", "diag_rho30", "diag_rho45", "diag_rho0_nocollide"]


def load(d, arm, ds, k, s):
    p = os.path.join(REC, d, f"ep_acc_{ds}_K{k}_seed{s}_{arm}.csv")
    if not os.path.exists(p):
        return None
    out = defaultdict(dict)
    for r in csv.DictReader(open(p)):
        out[r["mode"]][int(r["ep_idx"])] = float(r["acc"])
    if len(out["test"]) != 200:
        return None
    return {m: np.array([out[m][i] for i in sorted(out[m])]) for m in out}


def runs(name, ds, k):
    """name: 'sup' | 'vision' | 'tegorig' | 'naqfeat_allpool' | '<prefix>_l<λ>' | 'diag_*'. 3 seed 모두 있으면 리스트."""
    if name.startswith("diag_"):
        d = DIRS["diag"]
    else:
        d = DIRS[name.split("_l")[0]] if "_l" in name else DIRS[name]
    r = [load(d, name, ds, k, s) for s in SEEDS]
    return None if any(x is None for x in r) else r


def select_lam(prefix, ds, k):
    means = {}
    for lam in LAMS:
        r = runs(f"{prefix}_l{lam}", ds, k)
        if r is None or any("valid" not in x for x in r):
            return None, None
        means[lam] = float(np.mean([x["valid"].mean() for x in r]))
    best = max(means.values())
    return min((l for l in LAMS if means[l] == best), key=float), means


def paired(a, b):
    per = []
    D = []
    for s, (x, y) in enumerate(zip(a, b)):
        d = x["test"] - y["test"]
        per.append({"seed": s, "mean": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d)))})
        D.append(d)
    d = np.concatenate(D)
    m, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
    return {"mean": m, "se": se, "n": int(len(d)), "clear": bool(m > 0 and m > 2 * se), "per_seed": per}


def main():
    res = {"accuracy": {}, "lam": {}, "pairs": {}, "diag": {}}
    for ds in DS:
        for k in KS:
            key = f"{ds}_K{k}"
            eff = {"sup": "sup", "vision": "vision", "tegorig": "tegorig", "naqfeat_allpool": "naqfeat_allpool"}
            for p in ("sup2", "naqfeat", "naqdiff", "cres"):
                lam, means = select_lam(p, ds, k)
                res["lam"][f"{key}_{p}"] = {"lam": lam, "valid_seed_mean": means}
                eff[p] = None if lam is None else f"{p}_l{lam}"
            acc = {}
            for a in ("sup", "sup2", "naqfeat", "naqdiff", "naqfeat_allpool", "cres", "vision", "tegorig"):
                nm = eff[a]
                r = None if nm is None else runs(nm, ds, k)
                acc[a] = None if r is None else {"arm": nm, "seeds": [float(x["test"].mean()) for x in r],
                                                 "mean": float(np.mean([x["test"].mean() for x in r]))}
            res["accuracy"][key] = acc
            pr = {}
            for label, (a, b) in {
                "sup2 − sup": ("sup2", "sup"),
                "naqfeat − sup": ("naqfeat", "sup"), "naqfeat − sup2": ("naqfeat", "sup2"),
                "naqdiff − sup": ("naqdiff", "sup"), "naqdiff − sup2": ("naqdiff", "sup2"),
                "naqfeat_allpool − naqfeat": ("naqfeat_allpool", "naqfeat"),
                "cres − sup": ("cres", "sup"), "cres − sup2": ("cres", "sup2"), "cres − naqfeat": ("cres", "naqfeat"),
                "sup − vision": ("sup", "vision"), "sup − tegorig": ("sup", "tegorig"),
            }.items():
                ra = None if eff[a] is None else runs(eff[a], ds, k)
                rb = None if eff[b] is None else runs(eff[b], ds, k)
                pr[label] = None if ra is None or rb is None else {"a": eff[a], "b": eff[b], **paired(ra, rb)}
            res["pairs"][key] = pr
            # 진단(방법 아님)
            dg = {"acc": {}, "pairs": {}}
            for a in DIAG_ARMS:
                r = runs(a, ds, k)
                dg["acc"][a] = None if r is None else {"seeds": [float(x["test"].mean()) for x in r], "mean": float(np.mean([x["test"].mean() for x in r]))}
            for label, (a, b) in {"rho0 − rho45": ("diag_rho0", "diag_rho45"), "nocollide − rho0": ("diag_rho0_nocollide", "diag_rho0"),
                                  "rho0 − naqfeat": ("diag_rho0", eff["naqfeat"]), "naqfeat − rho45": (eff["naqfeat"], "diag_rho45")}.items():
                ra = None if a is None else runs(a, ds, k)
                rb = None if b is None else runs(b, ds, k)
                dg["pairs"][label] = None if ra is None or rb is None else {"a": a, "b": b, **paired(ra, rb)}
            res["diag"][key] = dg
    os.makedirs(os.path.join(REC, "016_summary"), exist_ok=True)
    json.dump(res, open(os.path.join(REC, "016_summary", "aggregate.json"), "w"), indent=1, ensure_ascii=False)
    f = lambda x: f"{x*100:.2f}"
    L = ["### 고정 test 정확도 (%, seed 0 / 1 / 2, 평균; 선택 λ)", "", "| 데이터셋 | K | arm | 사용 arm | seed 0 / 1 / 2 | 평균 |", "|---|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            for a, v in res["accuracy"][f"{ds}_K{k}"].items():
                L.append(f"| {ds} | {k} | {a} | — | 미완료 | 미완료 |" if v is None else
                         f"| {ds} | {k} | {a} | {v['arm']} | " + " / ".join(map(f, v["seeds"])) + f" | {f(v['mean'])} |")
    L += ["", "### λ 선택 (seed 평균 고정 valid, %)", "", "| 데이터셋 | K | arm | λ 0.5 | λ 1.0 | 선택 |", "|---|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            for p in ("sup2", "naqfeat", "naqdiff", "cres"):
                x = res["lam"][f"{ds}_K{k}_{p}"]
                L.append(f"| {ds} | {k} | {p} | 미완료 | 미완료 | 미완료 |" if x["lam"] is None else
                         f"| {ds} | {k} | {p} | {f(x['valid_seed_mean']['0.5'])} | {f(x['valid_seed_mean']['1.0'])} | {x['lam']} |")
    def pair_rows(src, title):
        out = ["", title, "", "| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |", "|---|---|---|---|---|---|---|"]
        for ds in DS:
            for k in KS:
                for label, v in src(ds, k).items():
                    if v is None:
                        out.append(f"| {ds} | {k} | {label} | — | 미완료 | — | — |")
                    else:
                        out.append(f"| {ds} | {k} | {label} | {v['a']} − {v['b']} | {v['mean']*100:+.2f} ± {v['se']*100:.2f} | {'예' if v['clear'] else '아니오'} | "
                                   + " / ".join(f"{p['mean']*100:+.2f}" for p in v["per_seed"]) + " |")
        return out
    L += pair_rows(lambda ds, k: res["pairs"][f"{ds}_K{k}"], "### 짝지은 차 (seed 0–2 합친 600 에피소드; 분명 = 평균 > 0 이고 > 2·SE)")
    L += ["", "### 진단, 방법 아님 — 순도 곡선 정확도 (%, seed 평균)", "", "| 데이터셋 | K | rho0 | rho15 | rho30 | rho45 | rho0_nocollide | naqfeat(선택 λ) |", "|---|---|---|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            dg = res["diag"][f"{ds}_K{k}"]["acc"]
            nf = res["accuracy"][f"{ds}_K{k}"]["naqfeat"]
            L.append(f"| {ds} | {k} | " + " | ".join("미완료" if dg[a] is None else f(dg[a]["mean"]) for a in DIAG_ARMS) + f" | {'미완료' if nf is None else f(nf['mean'])} |")
    L += pair_rows(lambda ds, k: res["diag"][f"{ds}_K{k}"]["pairs"], "### 진단, 방법 아님 — 짝지은 차")
    open(os.path.join(REC, "016_summary", "tables.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
