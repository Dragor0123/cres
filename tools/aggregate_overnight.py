# 009 야간 집계. records/ 만 읽는다(results/ 의존 없음).
# 출력: records/009_summary/aggregate.json, records/009_summary/tables.md
import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(ROOT, "records")
DS = ["Amazon_clothing", "Amazon_electronics", "dblp"]
KS = [1, 5]
SEEDS = [0, 1, 2]
ARM_DIRS = {
    "sup": "003_teg_port",
    "naqfeat_l0.5": "006_naq", "naqfeat_l1.0": "006_naq", "naqdiff_l0.5": "006_naq", "naqdiff_l1.0": "006_naq",
    "cres_l0.5": "008_cres_pilot", "cres_l1.0": "008_cres_pilot",
    "vision": "007_vision", "tegorig": "007_tegorig",
}
LAMS = ["0.5", "1.0"]


def load(arm, ds, k, s):
    p = os.path.join(REC, ARM_DIRS[arm], f"ep_acc_{ds}_K{k}_seed{s}_{arm}.csv")
    if not os.path.exists(p):
        return None
    out = defaultdict(dict)
    for r in csv.DictReader(open(p)):
        out[r["mode"]][int(r["ep_idx"])] = float(r["acc"])
    test = [out["test"][i] for i in sorted(out["test"])]
    if len(test) != 200:
        return None
    valid = [out["valid"][i] for i in sorted(out["valid"])] if "valid" in out else None
    return {"test": np.array(test), "valid": None if valid is None else np.array(valid)}


def select_lam(prefix, ds, k):
    """seed 평균 고정 valid 최고 λ, 동률이면 작은 λ. 미완료면 None."""
    means = {}
    for lam in LAMS:
        runs = [load(f"{prefix}_l{lam}", ds, k, s) for s in SEEDS]
        if any(r is None or r["valid"] is None for r in runs):
            return None, None
        means[lam] = float(np.mean([r["valid"].mean() for r in runs]))
    best = max(means.values())
    return min((l for l in LAMS if means[l] == best), key=float), means


def paired(a_runs, b_runs):
    per_seed = []
    alld = []
    for s, (a, b) in enumerate(zip(a_runs, b_runs)):
        d = a["test"] - b["test"]
        per_seed.append({"seed": s, "mean": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d)))})
        alld.append(d)
    d = np.concatenate(alld)
    m, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))
    return {"mean": m, "se": se, "n": int(len(d)), "clear": bool(m > 0 and m > 2 * se), "per_seed": per_seed}


def main():
    res = {"accuracy": {}, "lam_selection": {}, "pairs": {}}
    arms_eff = {}
    for ds in DS:
        for k in KS:
            key = f"{ds}_K{k}"
            acc = {}
            for arm in ARM_DIRS:
                runs = [load(arm, ds, k, s) for s in SEEDS]
                acc[arm] = None if any(r is None for r in runs) else {
                    "seeds": [float(r["test"].mean()) for r in runs], "mean": float(np.mean([r["test"].mean() for r in runs]))}
            res["accuracy"][key] = acc
            eff = {"sup": "sup", "vision": "vision", "tegorig": "tegorig"}
            for prefix, name in (("naqfeat", "naq_feat"), ("naqdiff", "naq_diff"), ("cres", "cres")):
                lam, means = select_lam(prefix, ds, k)
                res["lam_selection"][f"{key}_{name}"] = {"lam": lam, "valid_seed_mean": means}
                eff[name] = None if lam is None else f"{prefix}_l{lam}"
            # +NaQ (valid로 고른 쪽): 선택된 λ의 Feat·Diff 중 seed 평균 valid가 높은 쪽(동률이면 Feat)
            cand = []
            for name in ("naq_feat", "naq_diff"):
                if eff[name] is not None:
                    v = res["lam_selection"][f"{key}_{name}"]["valid_seed_mean"][eff[name].split("_l")[1]]
                    cand.append((v, name))
            eff["naq_best"] = None
            if len(cand) == 2:
                best = max(c[0] for c in cand)
                eff["naq_best"] = eff[[c[1] for c in cand if c[0] == best][0]]
            arms_eff[key] = eff
            pairs = {
                "+NaQ-Feat − sup": ("naq_feat", "sup"), "+NaQ-Diff − sup": ("naq_diff", "sup"),
                "+CRES − sup": ("cres", "sup"), "+CRES − +NaQ(valid 선택)": ("cres", "naq_best"),
                "sup − VISION": ("sup", "vision"), "sup − TEG-orig": ("sup", "tegorig"),
            }
            pr = {}
            for label, (a, b) in pairs.items():
                aa, bb = eff.get(a), eff.get(b)
                if aa is None or bb is None:
                    pr[label] = "미완료"
                    continue
                ra = [load(aa, ds, k, s) for s in SEEDS]
                rb = [load(bb, ds, k, s) for s in SEEDS]
                if any(r is None for r in ra + rb):
                    pr[label] = "미완료"
                    continue
                pr[label] = {"a": aa, "b": bb, **paired(ra, rb)}
            res["pairs"][key] = pr
    res["effective_arms"] = arms_eff
    os.makedirs(os.path.join(REC, "009_summary"), exist_ok=True)
    json.dump(res, open(os.path.join(REC, "009_summary", "aggregate.json"), "w"), indent=1, ensure_ascii=False)
    # 표
    L = ["### 고정 test 정확도 (%, seed 0 / 1 / 2, 평균)", "",
         "| 데이터셋 | K | arm | seed 0 / 1 / 2 | 평균 |", "|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            for arm, v in res["accuracy"][f"{ds}_K{k}"].items():
                if v is None:
                    L.append(f"| {ds} | {k} | {arm} | 미완료 | 미완료 |")
                else:
                    L.append(f"| {ds} | {k} | {arm} | " + " / ".join(f"{x*100:.2f}" for x in v["seeds"]) + f" | {v['mean']*100:.2f} |")
    L += ["", "### λ 선택 (seed 평균 고정 valid, %)", "", "| 데이터셋 | K | 생성기 | λ 0.5 | λ 1.0 | 선택 |", "|---|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            for name in ("naq_feat", "naq_diff", "cres"):
                x = res["lam_selection"][f"{ds}_K{k}_{name}"]
                if x["lam"] is None:
                    L.append(f"| {ds} | {k} | {name} | 미완료 | 미완료 | 미완료 |")
                else:
                    L.append(f"| {ds} | {k} | {name} | {x['valid_seed_mean']['0.5']*100:.2f} | {x['valid_seed_mean']['1.0']*100:.2f} | {x['lam']} |")
    L += ["", "### 짝지은 차 (%p, seed 0–2 에피소드 600개 합침; 분명 = 평균 > 0 이고 > 2·SE)", "",
          "| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE | 분명 | seed별 평균 (0 / 1 / 2) |", "|---|---|---|---|---|---|---|"]
    for ds in DS:
        for k in KS:
            for label, v in res["pairs"][f"{ds}_K{k}"].items():
                if v == "미완료":
                    L.append(f"| {ds} | {k} | {label} | — | 미완료 | — | — |")
                else:
                    L.append(f"| {ds} | {k} | {label} | {v['a']} − {v['b']} | {v['mean']*100:+.2f} ± {v['se']*100:.2f} | {'예' if v['clear'] else '아니오'} | "
                             + " / ".join(f"{p['mean']*100:+.2f}" for p in v["per_seed"]) + " |")
    open(os.path.join(REC, "009_summary", "tables.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
