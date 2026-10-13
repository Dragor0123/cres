# 데이터 통계 (지시서 001 작업 4). 사실 수집만 한다.
# 사용: /venv/cres/bin/python tools/data_stats.py [--data_dir data] [--split_dir splits] [--out results/001/data_stats.json]
#
# 레이블 사용: 클래스 수·교집합·분할별 노드 수 집계에만 쓴다(모델 계산 없음).
import argparse
import json
import os
from collections import Counter

import numpy as np
import scipy.io as sio
import scipy.sparse as sp

DATASETS = ["Amazon_clothing", "Amazon_electronics", "dblp"]


def feat_kind(X):
    X = sp.csr_matrix(X)
    vals = X.data
    nnz = X.nnz
    total = X.shape[0] * X.shape[1]
    uniq = np.unique(vals)
    is_binary = bool(np.all(np.isin(uniq, [0.0, 1.0])))
    is_integer = bool(np.all(np.equal(np.mod(vals, 1), 0)))
    row_nnz = np.diff(X.indptr)
    return {
        "dtype": str(X.dtype),
        "nnz": int(nnz),
        "density": nnz / total,
        "n_unique_nonzero_values": int(len(uniq)),
        "nonzero_min": float(vals.min()) if nnz else None,
        "nonzero_max": float(vals.max()) if nnz else None,
        "binary": is_binary,
        "integer_valued": is_integer,
        "has_negative": bool((vals < 0).any()),
        "rows_all_zero": int((row_nnz == 0).sum()),
        "row_nnz_mean": float(row_nnz.mean()),
    }


def network_stats(path, n_nodes_mat):
    rows = []
    n_lines = 0
    bad = 0
    with open(path) as f:
        for line in f:
            n_lines += 1
            p = line.strip().split("\t")
            if len(p) != 2:
                bad += 1
                continue
            rows.append((int(p[0]), int(p[1])))
    e = np.array(rows, dtype=np.int64)
    pairs = Counter(map(tuple, e))
    n_dup_lines = sum(c - 1 for c in pairs.values())  # 같은 (u,v) 줄이 여러 번 나온 초과분
    self_loops = int((e[:, 0] == e[:, 1]).sum())
    directed = set(pairs)
    non_loop = {(u, v) for (u, v) in directed if u != v}
    has_reverse = sum(1 for (u, v) in non_loop if (v, u) in directed)
    undirected = {(min(u, v), max(u, v)) for (u, v) in non_loop}
    max_id = int(e.max())
    n = max(max_id + 1, n_nodes_mat)
    touched = np.zeros(n, dtype=bool)
    touched[e[:, 0]] = True
    touched[e[:, 1]] = True
    # 자기 루프만 있는 노드도 고립으로 센다(다른 노드와 연결 없음)
    nl = e[e[:, 0] != e[:, 1]]
    touched_nl = np.zeros(n, dtype=bool)
    touched_nl[nl[:, 0]] = True
    touched_nl[nl[:, 1]] = True
    return {
        "lines": n_lines,
        "malformed_lines": bad,
        "duplicate_lines": int(n_dup_lines),
        "distinct_directed_pairs": len(directed),
        "self_loops_lines": self_loops,
        "distinct_non_loop_pairs": len(non_loop),
        "non_loop_pairs_with_reverse_present": int(has_reverse),
        "non_loop_pairs_without_reverse": int(len(non_loop) - has_reverse),
        "both_directions_fully_present": bool(has_reverse == len(non_loop)),
        "distinct_undirected_edges": len(undirected),
        "min_node_id": int(e.min()),
        "max_node_id": max_id,
        "nodes_with_no_edge_line": int((~touched[:n]).sum()),
        "isolated_nodes_excluding_self_loops": int((~touched_nl[:n]).sum()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="data")
    ap.add_argument("--split_dir", default="splits")
    ap.add_argument("--out", default="results/001/data_stats.json")
    a = ap.parse_args()
    res = {}
    for ds in DATASETS:
        d = {}
        tr = sio.loadmat(f"{a.data_dir}/{ds}/{ds}_train.mat")
        te = sio.loadmat(f"{a.data_dir}/{ds}/{ds}_test.mat")
        idx_tr = tr["Index"].reshape(-1).astype(np.int64)
        idx_te = te["Index"].reshape(-1).astype(np.int64)
        y_tr = tr["Label"].reshape(-1)
        y_te = te["Label"].reshape(-1)
        d["mat_keys"] = sorted(k for k in tr if not k.startswith("__"))
        d["train"] = {"nodes": int(len(idx_tr)), "feat_dim": int(tr["Attributes"].shape[1]),
                      "attr_type": type(tr["Attributes"]).__name__, "label_dtype": str(tr["Label"].dtype),
                      "features": feat_kind(tr["Attributes"])}
        d["test"] = {"nodes": int(len(idx_te)), "feat_dim": int(te["Attributes"].shape[1]),
                     "attr_type": type(te["Attributes"]).__name__, "label_dtype": str(te["Label"].dtype),
                     "features": feat_kind(te["Attributes"])}
        ctr, cte = set(np.unique(y_tr).tolist()), set(np.unique(y_te).tolist())
        d["classes"] = {"train_mat": len(ctr), "test_mat": len(cte), "intersection": len(ctr & cte),
                        "label_min": float(min(ctr | cte)), "label_max": float(max(ctr | cte)),
                        "labels_integer_valued": bool(all(float(c).is_integer() for c in ctr | cte))}
        cnt_tr = Counter(y_tr.tolist())
        cnt_te = Counter(y_te.tolist())
        d["nodes_per_class"] = {
            "train_mat": {"min": min(cnt_tr.values()), "max": max(cnt_tr.values())},
            "test_mat": {"min": min(cnt_te.values()), "max": max(cnt_te.values())},
        }
        all_idx = np.concatenate([idx_tr, idx_te])
        N = int(all_idx.max()) + 1
        d["index"] = {
            "min": int(all_idx.min()), "max": int(all_idx.max()),
            "train_unique": int(len(np.unique(idx_tr))), "test_unique": int(len(np.unique(idx_te))),
            "train_test_overlap": int(len(np.intersect1d(idx_tr, idx_te))),
            "union_unique": int(len(np.unique(all_idx))),
            "covers_0_to_N_minus_1": bool(all_idx.min() == 0 and len(np.unique(all_idx)) == N),
            "N_from_index": N,
        }
        net = network_stats(f"{a.data_dir}/{ds}/{ds}_network", N)
        net["max_node_id_le_index_max"] = bool(net["max_node_id"] <= int(all_idx.max()))
        d["network"] = net

        sp_path = os.path.join(a.split_dir, f"{ds}_class_split.json")
        if os.path.exists(sp_path):
            spl = json.load(open(sp_path))
            labels = np.full(N, np.nan)
            labels[idx_tr] = y_tr
            labels[idx_te] = y_te
            per_seed = {}
            for s, v in spl["seeds"].items():
                per_seed[s] = {
                    g: {"classes": len(v[k]), "nodes": int(np.isin(labels, np.array(v[k], dtype=float)).sum())}
                    for g, k in (("base", "class_list_train"), ("valid", "class_list_valid"), ("test", "class_list_test"))
                }
            d["split_counts_per_seed"] = per_seed
        res[ds] = d
        print(ds, json.dumps({k: d[k] for k in ("train", "test", "classes", "index", "network")}, ensure_ascii=False))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print("written", a.out)


if __name__ == "__main__":
    main()
