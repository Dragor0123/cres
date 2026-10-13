# 011 생성기 통계와 점검. 레이블은 통계(way 사이 실제 클래스 충돌)에만 읽는다 — 생성에는 쓰지 않는다.
# 사용 레이블 집합: 풀 U 노드의 실제 클래스(valid ∪ test 클래스), allpool은 전체 노드.
# 사용: CUDA_VISIBLE_DEVICES=<gpu> /venv/cres/bin/python tools/naq_v2_stats.py [--build_only]
# 출력: records/011_naq_v2/generator_stats.json
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from baselines.naq.generator import TOP, TOP_V2, NaQGenerator, NaQGeneratorV1, neighbor_table  # noqa: E402
from cres.data import DATASETS, ROOT, load_raw, load_split  # noqa: E402

N_EP = 1000


def pool_U(labels, seed, ds):
    return np.where(~np.isin(labels, load_split(ds, seed)["base"]))[0]


def collide(labels, sup):
    c = labels[np.asarray(sup)]
    return len(set(c.tolist())) < len(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build_only", action="store_true")
    a = ap.parse_args()
    out = {"n_episodes": N_EP, "label_use": "stats only: true class of anchors (way collision)", "cells": [], "prefix_check": [], "k1_sequence_check": []}
    for ds in DATASETS:
        _, _, labels, n = load_raw(ds)
        print("LABELS-READ (stats only):", ds, flush=True)
        for seed in (0, 1, 2):
            U = pool_U(labels, seed, ds)
            for kind in ("feat", "diff"):
                nb50 = neighbor_table(ds, kind, U, seed, top=TOP_V2, tag="011")
                p9 = os.path.join(ROOT, "results", "006", ds, f"naq_{kind}_seed{seed}_top{TOP}.npy")
                if os.path.exists(p9):
                    nb9 = np.load(p9)
                    out["prefix_check"].append({"dataset": ds, "seed": seed, "kind": kind,
                                                "top50[:, :9] == top9 (006)": bool((nb50[:, :TOP] == nb9).all()),
                                                "rows_differ": int((nb50[:, :TOP] != nb9).any(1).sum())})
        neighbor_table(ds, "feat", np.arange(n), 0, top=TOP_V2, tag="011", pool="all")
        if a.build_only:
            continue
        seed = 0
        U = pool_U(labels, seed, ds)
        for kind in ("feat", "diff"):
            for K in (1, 5):
                g1 = NaQGeneratorV1(ds, seed, K, 5, kind, U)
                g2 = NaQGenerator(ds, seed, K, 5, kind, U)
                c1 = c2 = 0
                for _ in range(N_EP):
                    s1, _, _ = g1.sample()
                    s2, _, _ = g2.sample()
                    c1 += collide(labels, s1[::K])  # v1: support는 way마다 K개, anchor = 각 way 첫 노드
                    c2 += collide(labels, s2)
                st1, st2 = g1.stats(), g2.stats()
                out["cells"].append({"dataset": ds, "K": K, "seed": seed, "kind": kind,
                                     "v1_dup_rate": st1["episodes_with_duplicate_node"] / N_EP,
                                     "v1_way_class_collision_rate": c1 / N_EP,
                                     "v2_anchor_redraws": st2["anchor_redraws"], "v2_episodes_with_redraw": st2["episodes_with_redraw"],
                                     "v2_way_class_collision_rate": c2 / N_EP})
                print(out["cells"][-1], flush=True)
            # K=1 점검: v1과 v2 에피소드 열이 v1의 첫 중복 에피소드 전까지 같은지
            g1 = NaQGeneratorV1(ds, seed, 1, 5, kind, U)
            g2 = NaQGenerator(ds, seed, 1, 5, kind, U)
            first_dup, same_until = None, None
            for e in range(N_EP):
                s1, q1, _ = g1.sample()
                s2, q2, _ = g2.sample()
                same = np.array_equal(s1, s2) and np.array_equal(q1, q2)
                if g1.n_dup and first_dup is None:
                    first_dup = e
                if not same and same_until is None:
                    same_until = e
                if first_dup is not None and same_until is not None:
                    break
            out["k1_sequence_check"].append({"dataset": ds, "seed": seed, "kind": kind,
                                             "v1_first_duplicate_episode": first_dup, "first_differing_episode": same_until})
            print(out["k1_sequence_check"][-1], flush=True)
    if not a.build_only:
        os.makedirs(os.path.join(ROOT, "records", "011_naq_v2"), exist_ok=True)
        json.dump(out, open(os.path.join(ROOT, "records", "011_naq_v2", "generator_stats.json"), "w"), indent=1)
    else:
        print(json.dumps(out["prefix_check"], indent=0))


if __name__ == "__main__":
    main()
