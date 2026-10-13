# CRES 데이터 로더.
# 그래프·특징·레이블 구성은 refs/TEG-orig utils.py load_data (b5a8e03, MIT, sung-won-kim/TEG)와
# 같은 식이다(TEG-choi 3b7be89 utils.py:16-69와 AST 동일). 클래스 분할은 전역 random 대신
# splits/<dataset>_class_split.json(001에서 재현한 TEG-choi seed별 분할)에서 읽는다.
#
# id_by_class는 TEG와 같은 순서: 클래스 키는 노드 0..N-1을 차례로 보며 처음 나온 순서,
# 각 클래스의 노드 목록은 노드 id 오름차순.
import json
import os

import numpy as np
import scipy.io as sio
import scipy.sparse as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
SPLIT_DIR = os.path.join(ROOT, "splits")
DATASETS = ["Amazon_clothing", "Amazon_electronics", "dblp"]


def load_raw(dataset, data_dir=DATA_DIR):
    """레이블 포함 원자료. 반환: edges (2, E) int64, features (N, F) float32 dense, labels (N,) int64, N."""
    e = np.loadtxt(os.path.join(data_dir, dataset, f"{dataset}_network"), dtype=np.int64, delimiter="\t")
    edges = e.T.copy()
    tr = sio.loadmat(os.path.join(data_dir, dataset, f"{dataset}_train.mat"))
    te = sio.loadmat(os.path.join(data_dir, dataset, f"{dataset}_test.mat"))
    n = int(max(edges.max(), tr["Index"].max(), te["Index"].max())) + 1
    labels = np.zeros(n, dtype=np.float64)
    labels[tr["Index"].reshape(-1)] = tr["Label"].reshape(-1)
    labels[te["Index"].reshape(-1)] = te["Label"].reshape(-1)
    feats = np.zeros((n, tr["Attributes"].shape[1]), dtype=np.float32)
    feats[tr["Index"].reshape(-1)] = tr["Attributes"].toarray()
    feats[te["Index"].reshape(-1)] = te["Attributes"].toarray()
    return edges, feats, labels.astype(np.int64), n


def id_by_class_of(labels):
    order = []
    seen = set()
    for c in labels.tolist():
        if c not in seen:
            seen.add(c)
            order.append(c)
    d = {c: [] for c in order}
    for i, c in enumerate(labels.tolist()):
        d[c].append(i)
    return d


def load_split(dataset, seed, split_dir=SPLIT_DIR):
    s = json.load(open(os.path.join(split_dir, f"{dataset}_class_split.json")))["seeds"][str(seed)]
    return {"base": s["class_list_train"], "valid": s["class_list_valid"], "test": s["class_list_test"]}


def node_groups(labels, split):
    """그룹별 노드 id 배열(레이블 사용 — 호출 측에서 용도를 로그에 남길 것)."""
    return {g: np.where(np.isin(labels, np.array(cs)))[0] for g, cs in split.items()}


def sym_norm_adj(edges, n, self_loops=True):
    a = sp.coo_matrix((np.ones(edges.shape[1], dtype=np.float32), (edges[0], edges[1])), shape=(n, n)).tocsr()
    if self_loops:
        a = a + sp.eye(n, dtype=np.float32, format="csr")
    d = np.asarray(a.sum(1)).reshape(-1)
    dinv = np.where(d > 0, d ** -0.5, 0).astype(np.float32)
    return (sp.diags(dinv) @ a @ sp.diags(dinv)).tocsr()
