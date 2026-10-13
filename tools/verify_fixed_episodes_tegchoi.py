# 002 검증: TEG-choi 사본(/workspace/scratch/TEG-choi-run)의 utils.load_data와 teg_trainer.fixed_episodes를
# 직접 호출해 만든 고정 에피소드의 해시를 splits/episodes/hashes.json과 대조한다.
# 실행: cd /workspace/scratch/TEG-choi-run && /venv/cres/bin/python /workspace/CRES/tools/verify_fixed_episodes_tegchoi.py
import json
import os
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, os.getcwd())
import utils as tc_utils  # noqa: E402  (TEG-choi utils)
from model import teg_trainer  # noqa: E402  (TEG-choi model)

sys.path.insert(0, "/workspace/CRES")
from tools.make_fixed_episodes import episodes_hash  # noqa: E402

ours = json.load(open("/workspace/CRES/splits/episodes/hashes.json"))
rows = []
for ds in ["Amazon_clothing", "Amazon_electronics", "dblp"]:
    for s in (0, 1, 2):
        tc_utils.seed_everything(s)
        out = tc_utils.load_data(ds)
        cl_train, cl_valid, cl_test, ibc = out[5], out[6], out[7], out[8]
        for k in (1, 5):
            fake = SimpleNamespace(args=SimpleNamespace(way=5), k_shot=k, n_query=5, id_by_class=ibc)
            for mode, off, n, cls in (("test", 9000, 200, cl_test), ("valid", 9100, 100, cl_valid)):
                eps = teg_trainer.fixed_episodes(fake, random.Random(off + s), cls, n)
                conv = [{"classes": [int(c) for c in c_], "support": [list(map(int, sup[i * k:(i + 1) * k])) for i in range(5)],
                         "query": [list(map(int, qry[i * 5:(i + 1) * 5])) for i in range(5)]} for sup, qry, c_ in eps]
                h = episodes_hash(conv)
                key = f"{ds}_seed{s}_K{k}_{mode}"
                rows.append((key, h, ours[key], h == ours[key]))
                print(key, h[:12], ours[key][:12], h == ours[key], flush=True)
json.dump([dict(key=r[0], tegchoi=r[1], ours=r[2], match=r[3]) for r in rows],
          open("/workspace/CRES/results/002/verify_tegchoi.json", "w"), indent=1)
print("ALL_MATCH" if all(r[3] for r in rows) else "MISMATCH")
