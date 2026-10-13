# 011 λ 선택값 저장(013이 읽는다). 규칙: seed 0–2 평균 고정 valid 최고, 동률이면 작은 λ.
# 출력 records/011_naq_v2/lambda_selected.json: {"<ds>_K<k>_naq_feat": "1.0", ..., "_valid_seed_mean": {...}}
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.aggregate_batch2 import DS, KS, REC, select_lam  # noqa: E402

out, means = {}, {}
for ds in DS:
    for k in KS:
        for p, name in (("naqfeat", "naq_feat"), ("naqdiff", "naq_diff")):
            lam, m = select_lam(p, ds, k)
            assert lam is not None, (ds, k, p)
            out[f"{ds}_K{k}_{name}"] = lam
            means[f"{ds}_K{k}_{name}"] = m
out["_valid_seed_mean"] = means
out["_rule"] = "seed 0-2 mean fixed-valid (100 episodes) best; tie -> smaller lambda"
json.dump(out, open(os.path.join(REC, "011_naq_v2", "lambda_selected.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
