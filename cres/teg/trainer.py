# TEG 학습기 (CRES 이식본).
# 출처: refs/TEG-orig (sung-won-kim/TEG, commit b5a8e03, MIT License)
#   embedder.py  가상 anchor 16개 + networkx 최단거리 구조 특징
#   model.py     teg_trainer.train_epoch / train (손실 γ·L_N + (1−γ)·L_G, epoch 0은 갱신 없음)
#   utils.py     seed_everything, task_generator_in_class, euclidean_dist, accuracy
# 고정 평가·체크포인트 규칙은 refs/TEG-choi (3b7be89) model.py:366-411, 942-947 (--fixed_eval)과 같다.
#
# 이식에서 바뀐 점(계산 경로는 lam=0일 때 원본과 같게 유지):
#   1. 데이터: cres.data 로더 + splits/<dataset>_class_split.json. 원본 load_data의 전역 random 호출
#      (random.sample(train_class, valid_num))은 호출 순서를 지키기 위해 그대로 한 번 실행하고,
#      결과가 분할 파일과 같은지 assert 한다.
#   2. 고정 평가: splits/episodes/<dataset>_seed<s>_K<k>.json 만 읽는다(자체 생성 없음).
#   3. 학습 스텝을 train_step(sup, pseudo, lam)으로 분리: L = L_sup + lam·L_pseudo.
#      lam == 0 이면 pseudo 에피소드를 만들지도 forward 하지도 않는다.
#   4. f1(sklearn) 계산은 기록하지 않는다(난수·계산 경로 영향 없음).
import json
import os
import random
import time

import networkx as nx
import numpy as np
import scipy.io as sio
import torch
import torch.nn.functional as F
from torch import optim

from cres.data import DATA_DIR, ROOT, id_by_class_of, load_raw, load_split
from cres.teg.layers import EGNN, GCN

VALID_NUM = {"Amazon_clothing": 17, "Amazon_electronics": 36, "dblp": 27}
CONF = {"gcn_out": 64, "egnn_in": 64, "egnn_emb_hid": 128, "egnn_emb_out": 64}  # TEG-orig configuration.yaml


def seed_everything(seed=0):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)


def euclidean_dist(x, y):
    n, m, d = x.size(0), y.size(0), x.size(1)
    assert d == y.size(1)
    x = x.unsqueeze(1).expand(n, m, d)
    y = y.unsqueeze(0).expand(n, m, d)
    return torch.pow(x - y, 2).sum(2)


def accuracy(output, labels):
    preds = output.max(1)[1].type_as(labels)
    return float(preds.eq(labels).double().sum() / output.shape[0])


def task_generator_in_class(id_by_class, selected_class_list, n_way, k_shot, m_query):
    id_support, id_query = [], []
    for cla in selected_class_list:
        temp = random.sample(id_by_class[cla], k_shot + m_query)
        id_support.extend(temp[:k_shot])
        id_query.extend(temp[k_shot:])
    return np.array(id_support), np.array(id_query), selected_class_list


class TEGTrainer:
    def __init__(self, dataset, seed, shot, way=5, qry=5, epochs=10, episodes=50, meta_val_num=50, meta_test_num=50,
                 lr=0.001, dropout=0.5, gamma=0.5, n_layers=2, anchor_size=16, device="cuda:0", log=print):
        self.dataset, self.seed, self.k_shot, self.n_way, self.n_query = dataset, seed, shot, way, qry
        self.epochs, self.episodes, self.meta_val_num, self.meta_test_num = epochs, episodes, meta_val_num, meta_test_num
        self.gamma, self.device, self.log = gamma, device, log
        seed_everything(seed)

        # ---- 데이터 (레이블: 에피소드 구성·지역 레이블에만 사용) ----
        edges, feats, labels, n = load_raw(dataset)
        # 원본 load_data의 전역 random 호출을 같은 순서로 재현(utils.py:31, :67)
        d_tr = sio.loadmat(os.path.join(DATA_DIR, dataset, f"{dataset}_train.mat"))
        train_class = list(set(d_tr["Label"].reshape((1, len(d_tr["Label"])))[0]))
        cl_valid_rng = random.sample(train_class, VALID_NUM[dataset])
        split = load_split(dataset, seed)
        assert [int(c) for c in cl_valid_rng] == split["valid"], "valid split mismatch with splits/ file"
        self.class_list_train, self.class_list_valid, self.class_list_test = split["base"], split["valid"], split["test"]
        self.labels_np = labels
        self.id_by_class = id_by_class_of(labels)
        self.num_nodes = n
        self.edges = torch.LongTensor(edges).to(device)
        self.features = torch.FloatTensor(feats).to(device)
        self.labels = torch.LongTensor(labels).to(device)
        self.labels_list = labels.tolist()

        # ---- 구조 특징 (TEG-orig embedder.py:35-80) ----
        edges_hub = torch.LongTensor(edges)
        for i in range(anchor_size):
            hub_index = n + i
            num_sample_node = int(n / (2 ** (i + 1)))
            if num_sample_node < 1:
                num_sample_node = 1
            sel = random.sample(list(range(n)), num_sample_node)
            hi = torch.LongTensor([hub_index] * len(sel))
            hj = torch.LongTensor(sel)
            edges_hub = torch.cat([edges_hub, torch.stack((torch.cat([hi, hj]), torch.cat([hj, hi])))], 1)
        graph = nx.Graph()
        graph.add_edges_from(edges_hub.transpose(1, 0).tolist())
        sf = []
        for i in range(anchor_size):
            spd_i = nx.single_source_shortest_path_length(graph, n + i)
            sf.append([1 / (spd_i[j] + 1) if j in spd_i else 0.0 for j in range(n)])
        self.structural_features = torch.Tensor(sf).T.to(device)

        # ---- 모델 (TEG-orig model.py:14-25) ----
        self.conv = GCN(self.features.shape[1], CONF["gcn_out"], dropout).to(device)
        self.egnn = EGNN(self.structural_features.shape[1], CONF["egnn_in"], n_layers=n_layers).to(device)
        self.optim = optim.Adam([{"params": self.conv.parameters()}, {"params": self.egnn.parameters()}], lr=lr, weight_decay=5e-4)
        self.loss_fn = torch.nn.NLLLoss()

    # ------------------------------------------------------------------
    def episode_outputs(self, embeddings, id_support, id_query):
        """TEG-orig model.py:72-133. 반환 (output, output_gcn, output_softmax)."""
        ns, nq = len(id_support), len(id_query)
        k = ns // self.n_way
        embeds_epi = torch.cat([embeddings[id_support], embeddings[id_query]])
        epi_str = torch.cat([self.structural_features[id_support], self.structural_features[id_query]])
        gcn_spt = embeds_epi[:ns, :].view([self.n_way, k, embeds_epi.shape[1]])
        proto_gcn = gcn_spt.mean(1)
        output_gcn = F.log_softmax(-euclidean_dist(embeds_epi[ns:, :], proto_gcn), dim=1)
        edge1 = []
        for i in range(ns, ns + nq):
            edge1.extend([i] * ns)
        edge1 = torch.LongTensor(edge1)
        edge2 = torch.LongTensor(list(range(ns)) * nq)
        edge_index = torch.stack((torch.cat([edge1, edge2]), torch.cat([edge2, edge1]))).to(self.device)
        epi_str, embeds_epi = self.egnn(epi_str, embeds_epi, edge_index)
        spt = embeds_epi[:ns, :].view([self.n_way, k, embeds_epi.shape[1]])
        proto = spt.mean(1)
        dists = euclidean_dist(embeds_epi[ns:, :], proto)
        return F.log_softmax(-dists, dim=1), output_gcn, F.softmax(-dists, dim=1)

    def episode_loss(self, embeddings, id_support, id_query, label_list):
        output, output_gcn, output_softmax = self.episode_outputs(embeddings, id_support, id_query)
        loss = self.gamma * self.loss_fn(output, label_list) + (1 - self.gamma) * self.loss_fn(output_gcn, label_list)
        return loss, output_softmax

    def train_step(self, sup_episode, pseudo_episode=None, lam=0.0, update=True):
        """sup_episode = (id_support, id_query, label_list). pseudo_episode 같은 형식(지역 레이블 0..N-1).
        L = L_sup + lam·L_pseudo. lam == 0이면 pseudo는 쓰지 않는다. 같은 GCN 출력을 두 에피소드가 공유한다."""
        self.optim.zero_grad()
        embeddings = self.conv(self.features, self.edges)
        loss_sup, out_sm = self.episode_loss(embeddings, *sup_episode)
        loss = loss_sup
        loss_p = None
        if lam != 0.0 and pseudo_episode is not None:
            loss_p, _ = self.episode_loss(embeddings, *pseudo_episode)
            loss = loss_sup + lam * loss_p
        if update:
            loss.backward()
            self.optim.step()
        else:
            self.optim.zero_grad()
        return out_sm, float(loss_sup), (None if loss_p is None else float(loss_p))

    def label_list_of(self, class_selected, id_query):
        return torch.LongTensor([class_selected.index(self.labels_list[i]) for i in id_query]).to(self.device)

    # ------------------------------------------------------------------
    def run_epoch(self, mode, n_episode, epoch, pseudo_fn=None, lam=0.0):
        """TEG-orig model.py:30-180 (train_epoch). 전역 random 소비 순서 동일."""
        if mode == "train" and epoch != 0:
            self.conv.train(); self.egnn.train()
        else:
            self.conv.eval(); self.egnn.eval()
        accs, lsup, lps = [], [], []
        cl = {"train": self.class_list_train, "valid": self.class_list_valid, "test": self.class_list_test}[mode]
        for _ in range(n_episode):
            if mode == "train":
                self.optim.zero_grad()
            class_selected = random.sample(cl, self.n_way)
            id_support, id_query, class_selected = task_generator_in_class(self.id_by_class, class_selected, self.n_way, self.k_shot, self.n_query)
            label_list = self.label_list_of(class_selected, id_query)
            if mode == "train":
                pseudo = None
                if lam != 0.0 and pseudo_fn is not None and epoch != 0:
                    pseudo = pseudo_fn()
                out_sm, ls, lp = self.train_step((id_support, id_query, label_list), pseudo, lam, update=(epoch != 0))
                lsup.append(ls)
                if lp is not None:
                    lps.append(lp)
            else:
                embeddings = self.conv(self.features, self.edges)
                _, _, out_sm = self.episode_outputs(embeddings, id_support, id_query)
            accs.append(accuracy(out_sm.cpu().detach(), label_list.cpu().detach()))
        return float(np.mean(accs)), (float(np.mean(lsup)) if lsup else None), (float(np.mean(lps)) if lps else None)

    def eval_fixed(self, eps):
        """TEG-choi run_fixed_eval와 같은 forward. eps: 고정 에피소드 json 목록. 반환 에피소드별 정확도."""
        self.conv.eval(); self.egnn.eval()
        accs = []
        with torch.no_grad():
            for e in eps:
                sup = np.array([i for row in e["support"] for i in row])
                qry = np.array([i for row in e["query"] for i in row])
                cls = e["classes"]
                embeddings = self.conv(self.features, self.edges)
                _, _, out_sm = self.episode_outputs(embeddings, sup, qry)
                y = torch.LongTensor([cls.index(self.labels_list[i]) for i in qry])
                accs.append(accuracy(out_sm.cpu(), y))
        return accs

    def train(self, pseudo_fn=None, lam=0.0):
        """TEG-orig model.py:182-246 + TEG-choi --fixed_eval 체크포인트(valid == best일 때 저장, 동점은 나중 에폭)."""
        best_acc_valid, best_epoch_valid, test_at_best = 0, 0, None
        hist = []
        ckpt, ckpt_epoch = None, None
        for epoch in range(self.epochs + 1):
            t = time.time()
            acc_train, ls, lp = self.run_epoch("train", self.episodes, epoch, pseudo_fn, lam)
            with torch.no_grad():
                acc_valid, _, _ = self.run_epoch("valid", self.meta_val_num, epoch)
                acc_test, _, _ = self.run_epoch("test", self.meta_test_num, epoch)
            if best_acc_valid < acc_valid:
                best_acc_valid, best_epoch_valid = acc_valid, epoch
            if acc_valid == best_acc_valid:
                test_at_best = acc_test
                ckpt = {"conv": {k: v.detach().clone() for k, v in self.conv.state_dict().items()},
                        "egnn": {k: v.detach().clone() for k, v in self.egnn.state_dict().items()}}
                ckpt_epoch = epoch
            hist.append({"epoch": epoch, "acc_train": acc_train, "acc_valid": acc_valid, "acc_test": acc_test,
                         "loss_sup": ls, "loss_pseudo": lp, "sec": time.time() - t})
            self.log(f"epoch {epoch} train {acc_train:.4f} valid {acc_valid:.4f} test {acc_test:.4f} loss_sup {ls} loss_pseudo {lp}")
        self.conv.load_state_dict(ckpt["conv"])
        self.egnn.load_state_dict(ckpt["egnn"])
        return {"best_acc_valid": best_acc_valid, "best_epoch_valid": best_epoch_valid, "test_acc_at_best_valid": test_at_best,
                "ckpt_epoch": ckpt_epoch, "history": hist}
