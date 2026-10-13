# CRES 어댑터 (R001): VISION의 모델·학습 로직은 그대로 두고 다음만 바꾼다.
#   1. 데이터: /workspace/data/dataset/<ds>/의 .mat + edge list를 VISION load_DBLP와 같은 방식으로 읽는다
#      (엣지는 n1 > n2 한 방향만 남기고, split()의 adj_dict에서 양방향으로 만든다). Amazon 두 데이터셋에도 같은 함수를 쓴다.
#   2. 클래스 분할: /workspace/CRES/splits/<ds>_class_split.json의 seed별 분할(train = base, dev = valid, test = test).
#   3. 평가 에피소드: /workspace/CRES/splits/episodes/<ds>_seed<s>_K<k>.json (dev = valid 100개, test = test 200개).
# 레이블: VISION 학습 경로(unsupervised_task_generator)는 레이블을 쓰지 않는다. 레이블은 dev 선택(valid 에피소드)과 test 지표에만 쓰인다.
# 출처: refs/VISION (0524eae, MIT) data_split.py load_DBLP / split — 같은 식을 경로만 바꿔 옮김.
import json
from collections import defaultdict

import numpy as np
import scipy.io as sio
import torch
from sklearn import preprocessing

import data_split as ds_mod

DATA = "/workspace/data/dataset"
CRES = "/workspace/CRES"


def load_mat_graph(dataset_source):
    dataset = ds_mod.dblp_data()
    edge_file_path = f"{DATA}/{dataset_source}/{dataset_source}_network"
    edges = np.loadtxt(edge_file_path, dtype=np.int32)
    filtered_edges = edges[edges[:, 0] > edges[:, 1]]
    edge_index_tensor = torch.tensor(np.stack([filtered_edges[:, 0], filtered_edges[:, 1]]))
    num_nodes = int(edges.max()) + 1
    data_train = sio.loadmat(f"{DATA}/{dataset_source}/{dataset_source}_train.mat")
    data_test = sio.loadmat(f"{DATA}/{dataset_source}/{dataset_source}_test.mat")
    labels = np.zeros((num_nodes, 1))
    labels[data_train['Index']] = data_train["Label"]
    labels[data_test['Index']] = data_test["Label"]
    features = np.zeros((num_nodes, data_train["Attributes"].shape[1]))
    features[data_train['Index']] = data_train["Attributes"].toarray()
    features[data_test['Index']] = data_test["Attributes"].toarray()
    lb = preprocessing.LabelBinarizer()
    labels = lb.fit_transform(labels)
    dataset.x = torch.FloatTensor(features)
    dataset.y = torch.LongTensor(np.where(labels)[1])
    dataset.edge_index = edge_index_tensor
    dataset.num_nodes = num_nodes
    dataset.num_edges = dataset.edge_index.shape[1]
    dataset.num_features = features.shape[1]
    return ds_mod.dblp_dataset(dataset, num_classes=int(labels.shape[1]))


def split_from_files(dataset_name, seed):
    """data_split.split()과 같은 반환값. 클래스 분할만 파일에서 읽는다(random.shuffle 없음)."""
    dataset = load_mat_graph(dataset_name)
    data = dataset.data
    num_nodes = data.num_nodes
    sp = json.load(open(f"{CRES}/splits/{dataset_name}_class_split.json"))["seeds"][str(seed)]
    train_class, dev_class, test_class = sp["class_list_train"], sp["class_list_valid"], sp["class_list_test"]
    print(f"train_num: {len(train_class)}; dev_num: {len(dev_class)}; test_num: {len(test_class)}")
    id_by_class = defaultdict(list)
    for id, cla in enumerate(data.y.squeeze().tolist()):
        id_by_class[cla].append(id)
    train_idx = [item for cla in train_class for item in id_by_class[cla]]
    # 이하 data_split.split()의 인접 목록 구성과 같음
    adj_dict = defaultdict(list)
    edge_index = data.edge_index.numpy()
    for i in range(edge_index.shape[1]):
        u, v = edge_index[0, i], edge_index[1, i]
        adj_dict[u].append(v)
        adj_dict[v].append(u)
    max_degree = 0
    neighbor_counts = torch.zeros(num_nodes, dtype=torch.long)
    for i in range(num_nodes):
        count = len(adj_dict.get(i, []))
        neighbor_counts[i] = count
        if count > max_degree:
            max_degree = count
    print(f"Graph's max degree: {max_degree}")
    full_adj_tensor = torch.full((num_nodes, max_degree), -1, dtype=torch.long)
    for i in range(num_nodes):
        neighbors = adj_dict.get(i, [])
        if neighbors:
            full_adj_tensor[i, :len(neighbors)] = torch.tensor(neighbors)
    return data, np.array(train_idx), id_by_class, train_class, dev_class, test_class, full_adj_tensor, neighbor_counts


def fixed_episodes(dataset_name, seed, k_shot, mode):
    d = json.load(open(f"{CRES}/splits/episodes/{dataset_name}_seed{seed}_K{k_shot}.json"))
    blk = d["test" if mode == "test" else "valid"]
    out = []
    for e in blk["episodes"]:
        out.append((np.array([i for row in e["support"] for i in row]), np.array([i for row in e["query"] for i in row]), e["classes"]))
    return out, d["Q"], blk["sha1"]
