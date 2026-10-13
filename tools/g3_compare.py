# 003 G3 판정 (P01). TEG-choi 기준 실행 2회 × seed 0-2 vs 이식본 1회.
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.make_fixed_episodes import episodes_hash  # noqa: E402

TAU = 1.0  # %p (P01)
hashes = json.load(open("splits/episodes/hashes.json"))
os.makedirs("records/003_teg_port/g3", exist_ok=True)
rows, ok_all = [], True
for s in (0, 1, 2):
    base = []
    hash_ok = True
    for r in (1, 2):
        d = np.load(f"results/003/tegchoi/clo_K1_s{s}_r{r}/fixed_eval_logits.npz", allow_pickle=True)
        m = d["mode"] == 1
        acc = (d["logits"][m].argmax(-1) == d["query_y"][m]).mean(1)
        base.append(acc.mean() * 100)
        eps = [{"classes": list(c), "support": [list(x) for x in np.array(sp).reshape(5, -1)], "query": [list(x) for x in np.array(q).reshape(5, -1)]}
               for c, sp, q in zip(d["classes"][m], d["support"][m], d["query"][m])]
        h = episodes_hash(eps)
        hash_ok &= h == hashes[f"Amazon_clothing_seed{s}_K1_test"]
        with open(f"records/003_teg_port/g3/ep_acc_Amazon_clothing_K1_seed{s}_tegchoi_r{r}.csv", "w") as f:
            f.write("mode,ep_idx,acc\n" + "".join(f"test,{i},{x:.6f}\n" for i, x in enumerate(acc)))
            mv = d["mode"] == 0
            accv = (d["logits"][mv].argmax(-1) == d["query_y"][mv]).mean(1)
            f.write("".join(f"valid,{i},{x:.6f}\n" for i, x in enumerate(accv)))
        rj = json.load(open(f"results/003/tegchoi/clo_K1_s{s}_r{r}/run.json"))
    port = json.load(open(f"results/003/g3/port_clo_K1_s{s}/run.json"))
    p = port["fixed_test_acc"] * 100
    lo, hi = min(base) - TAU, max(base) + TAU
    ok = hash_ok and lo <= p <= hi
    ok_all &= ok
    rows.append({"seed": s, "tegchoi_r1": base[0], "tegchoi_r2": base[1], "port": p, "lo": lo, "hi": hi, "hash_ok": bool(hash_ok), "pass": bool(ok),
                 "port_ckpt_epoch": port["ckpt_epoch"], "port_test_at_best_valid": port["test_acc_at_best_valid"]})
    print(rows[-1])
json.dump({"tau": TAU, "rows": rows, "G3": bool(ok_all)}, open("records/003_teg_port/g3/g3_result.json", "w"), indent=1)
print("G3", "PASS" if ok_all else "FAIL")
