# TEG 백본 레이어.
# 출처: refs/TEG-orig (sung-won-kim/TEG, commit b5a8e03, MIT License)
#   layers/GCN.py  GCN (1층 GCNConv, cached, normalize)
#   layers/EGNN.py EGCL, EGNN, diff_mean, msg_collect
# 계산은 원본과 같다(포맷만 정리).
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import GCNConv


class GCN(torch.nn.Module):
    def __init__(self, in_dim, out_dim, dropout):
        super().__init__()
        self.conv1 = GCNConv(in_dim, out_dim, cached=True, normalize=True)
        self.dropout = dropout

    def forward(self, x, edge_index, edge_weight=None):
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv1(x, edge_index, edge_weight)
        return x


class EGCL(nn.Module):
    def __init__(self, raw_dim, hid_dim):
        super(EGCL, self).__init__()
        linear_xavier = nn.Linear(hid_dim, 1, bias=False)
        torch.nn.init.xavier_uniform_(linear_xavier.weight, gain=0.001)
        self.msg_mlp = nn.Sequential(nn.Linear(raw_dim + raw_dim + 1, hid_dim), nn.SiLU(), nn.Linear(hid_dim, hid_dim), nn.SiLU())
        self.trans_mlp = nn.Sequential(nn.Linear(hid_dim, hid_dim), nn.SiLU(), nn.Linear(hid_dim, hid_dim), nn.SiLU(), linear_xavier)
        self.posi_mlp = nn.Sequential(nn.Linear(raw_dim + hid_dim, hid_dim), nn.SiLU(), nn.Linear(hid_dim, raw_dim))

    def msg_model(self, h_i, h_j, sqr_dist):
        out = torch.cat([h_i, h_j, sqr_dist], dim=1)
        return self.msg_mlp(out)

    def coord_model(self, x, edge_index, coord_diff, msg):
        row, col = edge_index
        trans = coord_diff * self.trans_mlp(msg)
        trans = diff_mean(trans, row, num_nodes=x.size(0))
        return x + trans

    def posi_model(self, p, edge_index, msg):
        row, col = edge_index
        msg_sum = msg_collect(msg, row, num_nodes=p.size(0))
        out = torch.cat([p, msg_sum], dim=1)
        out = self.posi_mlp(out)
        return p + out

    def coord2dist(self, edge_index, x):
        row, col = edge_index
        coord_diff = x[row] - x[col]
        sqr_dist = torch.sum(coord_diff**2, 1).unsqueeze(1)
        return sqr_dist, coord_diff

    def forward(self, edge_index, str_feature, coord_feature):
        row, col = edge_index
        sqr_dist, coord_diff = self.coord2dist(edge_index, coord_feature)
        msg = self.msg_model(str_feature[row], str_feature[col], sqr_dist)
        coord_feature = self.coord_model(coord_feature, edge_index, coord_diff, msg)
        str_feature = self.posi_model(str_feature, edge_index, msg)
        return str_feature, coord_feature


class EGNN(nn.Module):
    def __init__(self, str_dim, in_dim, n_layers):
        super(EGNN, self).__init__()
        for i in range(0, n_layers):
            self.add_module("gcl_%d" % i, EGCL(str_dim, in_dim))
        self.n_layers = n_layers
        self.LayerNorm = nn.LayerNorm(in_dim)

    def forward(self, str_feature, coord_feature, edge_index):
        coord_feature = self.LayerNorm(coord_feature)
        for i in range(0, self.n_layers):
            str_feature, coord_feature = self._modules["gcl_%d" % i](edge_index, str_feature, coord_feature)
        return str_feature, coord_feature


def diff_mean(data, segment_ids, num_nodes):
    result_shape = (num_nodes, data.size(1))
    segment_ids = segment_ids.unsqueeze(-1).expand(-1, data.size(1))
    result = data.new_full(result_shape, 0)
    count = data.new_full(result_shape, 0)
    result.scatter_add_(0, segment_ids, data)
    count.scatter_add_(0, segment_ids, torch.ones_like(data))
    return result / count.clamp(min=1)


def msg_collect(data, segment_ids, num_nodes):
    result_shape = (num_nodes, data.size(1))
    result = data.new_full(result_shape, 0)
    segment_ids = segment_ids.unsqueeze(-1).expand(-1, data.size(1))
    result.scatter_add_(0, segment_ids, data)
    return result
