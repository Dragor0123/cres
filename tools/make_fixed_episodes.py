# 고정 valid/test 에피소드 생성 (지시서 002, R002 §2-3).
# 규칙: refs/TEG-choi (3b7be89) model.py:366-377 fixed_episodes, :388 의 시드·개수와 같은 순서.
#   에피소드마다 rng.sample(classes, N) → 클래스마다 rng.sample(id_by_class[c], K+Q), 앞 K개 support.
#   test: Random(9000+seed), 200개, class_list_test / valid: Random(9100+seed), 100개, class_list_valid.
# 출력: splits/episodes/<dataset>_seed<s>_K<k>.json (한 파일에 "test", "valid" 두 키).
# 레이블 사용: 클래스별 노드 목록(id_by_class) 구성에만 쓴다(평가용 에피소드).
import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cres.data import DATASETS, id_by_class_of, load_raw, load_split  # noqa: E402

N_WAY, Q = 5, 5
SPEC = {"test": (9000, 200), "valid": (9100, 100)}


def fixed_episodes(rng, classes, n_epi, id_by_class, k, q=Q, n=N_WAY):
    eps = []
    for _ in range(n_epi):
        cls = rng.sample(classes, n)
        sup, qry = [], []
        for c in cls:
            ids = rng.sample(id_by_class[c], k + q)
            sup.append(ids[:k])
            qry.append(ids[k:])
        eps.append({"classes": cls, "support": sup, "query": qry})
    return eps


def episodes_hash(eps):
    """support·query·classes를 평탄화한 순서열의 sha1 (TEG-choi 출력과 대조용)."""
    h = hashlib.sha1()
    for e in eps:
        flat_s = [i for row in e["support"] for i in row]
        flat_q = [i for row in e["query"] for i in row]
        h.update(json.dumps([[int(c) for c in e["classes"]], [int(i) for i in flat_s], [int(i) for i in flat_q]]).encode())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--ks", default="1,5")
    ap.add_argument("--out_dir", default="splits/episodes")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    hashes = {}
    for ds in DATASETS:
        _, _, labels, _ = load_raw(ds)
        ibc = id_by_class_of(labels)
        for s in map(int, a.seeds.split(",")):
            split = load_split(ds, s)
            for k in map(int, a.ks.split(",")):
                out = {"dataset": ds, "seed": s, "K": k, "Q": Q, "N": N_WAY,
                       "source_rule": "TEG-choi 3b7be89 model.py:366-377,388"}
                for mode, (off, n_epi) in SPEC.items():
                    classes = split["test"] if mode == "test" else split["valid"]
                    eps = fixed_episodes(random.Random(off + s), classes, n_epi, ibc, k)
                    hv = episodes_hash(eps)
                    out[mode] = {"mode": mode, "rng": f"Random({off}+seed)", "n_episodes": n_epi, "sha1": hv, "episodes": eps}
                    hashes[f"{ds}_seed{s}_K{k}_{mode}"] = hv
                p = os.path.join(a.out_dir, f"{ds}_seed{s}_K{k}.json")
                with open(p, "w") as f:
                    json.dump(out, f, separators=(",", ":"))
                print(p, os.path.getsize(p), out["test"]["sha1"][:12], out["valid"]["sha1"][:12])
    with open(os.path.join(a.out_dir, "hashes.json"), "w") as f:
        json.dump(hashes, f, indent=1)


if __name__ == "__main__":
    main()
