# 014 CRES 생성기 통계. 레이블은 통계(way 사이 실제 클래스 충돌, way 안 오염)에만 읽는다 — 생성에는 쓰지 않는다.
# 사용: CUDA_VISIBLE_DEVICES=<gpu> /venv/cres/bin/python tools/cres_gen_stats.py → records/014_cres_pilot/generator_stats.json
# 생성기 상태는 학습 실행과 독립(새 인스턴스, 같은 rng 23000+seed), 에피소드 N_EP개.
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cres.data import ROOT, load_raw  # noqa: E402
from cres.episodes import CRESGenerator  # noqa: E402

N_EP = 500
out = {"n_episodes": N_EP, "label_use": "stats only: true class of episode nodes", "cells": []}
for ds in ("Amazon_clothing", "Amazon_electronics"):
    _, _, labels, _ = load_raw(ds)
    print("LABELS-READ (stats only):", ds, flush=True)
    for k in (1, 5):
        for seed in (0, 1, 2):
            g = CRESGenerator(ds, seed, k, 5)
            coll, contam = 0, []
            for _ in range(N_EP):
                sup, qry, _ = g.sample()
                anchors = g.anchors[g.last_sel]
                coll += len(set(labels[anchors].tolist())) < len(anchors)
                S = sup.reshape(5, k)
                Q = qry.reshape(5, 5)
                mem = np.concatenate([S, Q], 1)
                contam.append(float((labels[mem] != labels[anchors][:, None]).sum() / (5 * (k + 5 - 1))))
            st = g.stats()
            cell = {"dataset": ds, "K": k, "seed": seed, **st, "way_class_collision_rate": coll / N_EP,
                    "within_way_contamination_mean": float(np.mean(contam)),
                    "anchor_tries_mean": st["anchor_tries_sum"] / N_EP, "query_redraw_episode_rate": st["episodes_with_query_redraw"] / N_EP}
            out["cells"].append(cell)
            print(cell, flush=True)
os.makedirs(os.path.join(ROOT, "records", "014_cres_pilot"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "records", "014_cres_pilot", "generator_stats.json"), "w"), indent=1)
