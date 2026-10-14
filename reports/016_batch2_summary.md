# 016 2차 큐 집계

작성 2026-10-14 · 지시서 `instructions/016_batch2_summary.md` · 집계 `tools/aggregate_batch2.py`(records/만 읽음) → `records/016_summary/aggregate.json`, `tables.md`

## 1. 큐 결과

T0 2026-10-13T22:57:40Z. 작업 240개(012 36, 011 72 + allpool 18, 013 90, 014 24), 실패·재시도 0 (`results/queue2/state.jsonl`).

| 항목 | 상태 | 시작–종료 (UTC) | 커밋 | 비고 |
|---|---|---|---|---|
| R004 | done | 22:57–22:58 | `9a5a117` | 010 §2 그대로 |
| 011 NaQ v2 | done | 22:58–23:40 | `04cbdce` | 72/72 + allpool 18/18. 006 superseded |
| 012 sup2 | done | 23:02–23:11 | `4317704` | 36/36 |
| 013 순도 곡선 (진단) | done | 23:00–23:55 | `e95ee26` | 90/90 |
| 014 CRES pilot (탐색) | done | 23:20–23:59 | `6feed4a` | 24/24 |
| 015 TEG-orig | skipped | 23:59–00:10 | `e40357b` | torch-sparse cu113 import 실패, 2회 시도 후 skip |
| 016 집계 | done | 00:10– | (이 커밋) | |

사전 등록: P07 `6ac1039`, P08 `6ac1039`, P09 `6bd4ac1`, P10 `925128b` (모두 해당 sweep 시작 전).

## 2. 표

### 2-1. 정확도 (고정 test %, seed 0 / 1 / 2, 평균; 선택 λ; 011 결과만 사용, 006 superseded)

| 데이터셋 | K | arm | 사용 arm | seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | sup | sup | 81.46 / 81.16 / 77.66 | 80.09 |
| Amazon_clothing | 1 | sup2 | sup2_l0.5 | 82.76 / 83.14 / 80.08 | 81.99 |
| Amazon_clothing | 1 | naqfeat | naqfeat_l1.0 | 85.84 / 86.58 / 87.82 | 86.75 |
| Amazon_clothing | 1 | naqdiff | naqdiff_l1.0 | 88.02 / 86.00 / 84.68 | 86.23 |
| Amazon_clothing | 1 | naqfeat_allpool | naqfeat_allpool | 86.42 / 86.76 / 82.56 | 85.25 |
| Amazon_clothing | 1 | cres | cres_l0.5 | 81.10 / 78.92 / 80.46 | 80.16 |
| Amazon_clothing | 1 | vision | vision | 84.08 / 82.78 / 82.72 | 83.19 |
| Amazon_clothing | 1 | tegorig | — | 미완료 | 미완료 |
| Amazon_clothing | 5 | sup | sup | 91.80 / 90.20 / 90.06 | 90.69 |
| Amazon_clothing | 5 | sup2 | sup2_l0.5 | 91.70 / 90.06 / 90.24 | 90.67 |
| Amazon_clothing | 5 | naqfeat | naqfeat_l1.0 | 92.76 / 91.88 / 92.80 | 92.48 |
| Amazon_clothing | 5 | naqdiff | naqdiff_l0.5 | 93.22 / 91.48 / 91.54 | 92.08 |
| Amazon_clothing | 5 | naqfeat_allpool | naqfeat_allpool | 92.04 / 91.10 / 91.48 | 91.54 |
| Amazon_clothing | 5 | cres | cres_l1.0 | 93.32 / 90.68 / 91.82 | 91.94 |
| Amazon_clothing | 5 | vision | vision | 90.48 / 89.82 / 89.82 | 90.04 |
| Amazon_clothing | 5 | tegorig | — | 미완료 | 미완료 |
| Amazon_electronics | 1 | sup | sup | 75.10 / 71.16 / 75.84 | 74.03 |
| Amazon_electronics | 1 | sup2 | sup2_l0.5 | 76.64 / 73.86 / 74.08 | 74.86 |
| Amazon_electronics | 1 | naqfeat | naqfeat_l1.0 | 80.04 / 77.54 / 81.20 | 79.59 |
| Amazon_electronics | 1 | naqdiff | naqdiff_l1.0 | 77.62 / 73.42 / 78.32 | 76.45 |
| Amazon_electronics | 1 | naqfeat_allpool | naqfeat_allpool | 77.80 / 75.06 / 79.18 | 77.35 |
| Amazon_electronics | 1 | cres | cres_l1.0 | 80.44 / 76.56 / 82.22 | 79.74 |
| Amazon_electronics | 1 | vision | vision | 76.66 / 77.06 / 78.68 | 77.47 |
| Amazon_electronics | 1 | tegorig | — | 미완료 | 미완료 |
| Amazon_electronics | 5 | sup | sup | 87.76 / 86.74 / 87.74 | 87.41 |
| Amazon_electronics | 5 | sup2 | sup2_l0.5 | 87.36 / 86.36 / 88.48 | 87.40 |
| Amazon_electronics | 5 | naqfeat | naqfeat_l0.5 | 90.00 / 88.40 / 89.88 | 89.43 |
| Amazon_electronics | 5 | naqdiff | naqdiff_l0.5 | 87.54 / 87.00 / 88.62 | 87.72 |
| Amazon_electronics | 5 | naqfeat_allpool | naqfeat_allpool | 88.56 / 88.30 / 89.24 | 88.70 |
| Amazon_electronics | 5 | cres | cres_l1.0 | 89.18 / 90.02 / 90.82 | 90.01 |
| Amazon_electronics | 5 | vision | vision | 85.60 / 86.66 / 88.60 | 86.95 |
| Amazon_electronics | 5 | tegorig | — | 미완료 | 미완료 |
| dblp | 1 | sup | sup | 75.38 / 75.14 / 76.68 | 75.73 |
| dblp | 1 | sup2 | sup2_l1.0 | 77.14 / 75.12 / 75.76 | 76.01 |
| dblp | 1 | naqfeat | naqfeat_l1.0 | 77.16 / 76.34 / 78.24 | 77.25 |
| dblp | 1 | naqdiff | naqdiff_l1.0 | 78.76 / 76.70 / 79.28 | 78.25 |
| dblp | 1 | naqfeat_allpool | naqfeat_allpool | 77.60 / 75.78 / 77.92 | 77.10 |
| dblp | 1 | cres | — | 미완료 | 미완료 |
| dblp | 1 | vision | vision | 72.46 / 70.16 / 72.20 | 71.61 |
| dblp | 1 | tegorig | — | 미완료 | 미완료 |
| dblp | 5 | sup | sup | 84.24 / 84.88 / 84.04 | 84.39 |
| dblp | 5 | sup2 | sup2_l1.0 | 84.50 / 85.38 / 85.32 | 85.07 |
| dblp | 5 | naqfeat | naqfeat_l0.5 | 85.00 / 85.98 / 84.92 | 85.30 |
| dblp | 5 | naqdiff | naqdiff_l1.0 | 85.74 / 86.62 / 85.66 | 86.01 |
| dblp | 5 | naqfeat_allpool | naqfeat_allpool | 84.96 / 85.86 / 84.58 | 85.13 |
| dblp | 5 | cres | — | 미완료 | 미완료 |
| dblp | 5 | vision | vision | 80.92 / 81.38 / 79.84 | 80.71 |
| dblp | 5 | tegorig | — | 미완료 | 미완료 |

- vision: 레이블 없이 전체 노드(test 클래스 노드 포함)로 학습, VISION 기본 하이퍼파라미터(R004 §7 단서). 007 결과.
- tegorig: 015 skip으로 미완료.
- cres: Amazon_clothing, Amazon_electronics만(014, 탐색용).

### λ 선택 (seed 평균 고정 valid, %; 최고, 동률이면 작은 λ)

| 데이터셋 | K | arm | λ 0.5 | λ 1.0 | 선택 |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | sup2 | 76.29 | 76.07 | 0.5 |
| Amazon_clothing | 1 | naqfeat | 81.48 | 82.00 | 1.0 |
| Amazon_clothing | 1 | naqdiff | 81.36 | 82.00 | 1.0 |
| Amazon_clothing | 1 | cres | 79.40 | 79.28 | 0.5 |
| Amazon_clothing | 5 | sup2 | 87.55 | 87.16 | 0.5 |
| Amazon_clothing | 5 | naqfeat | 89.53 | 89.56 | 1.0 |
| Amazon_clothing | 5 | naqdiff | 89.52 | 89.52 | 0.5 |
| Amazon_clothing | 5 | cres | 89.47 | 89.60 | 1.0 |
| Amazon_electronics | 1 | sup2 | 81.87 | 81.75 | 0.5 |
| Amazon_electronics | 1 | naqfeat | 84.60 | 86.43 | 1.0 |
| Amazon_electronics | 1 | naqdiff | 83.43 | 84.19 | 1.0 |
| Amazon_electronics | 1 | cres | 85.75 | 86.87 | 1.0 |
| Amazon_electronics | 5 | sup2 | 91.72 | 91.52 | 0.5 |
| Amazon_electronics | 5 | naqfeat | 92.80 | 92.45 | 0.5 |
| Amazon_electronics | 5 | naqdiff | 91.79 | 91.55 | 0.5 |
| Amazon_electronics | 5 | cres | 93.41 | 93.47 | 1.0 |
| dblp | 1 | sup2 | 75.40 | 76.05 | 1.0 |
| dblp | 1 | naqfeat | 76.05 | 76.55 | 1.0 |
| dblp | 1 | naqdiff | 77.05 | 77.39 | 1.0 |
| dblp | 1 | cres | 미완료 | 미완료 | 미완료 |
| dblp | 5 | sup2 | 85.15 | 85.43 | 1.0 |
| dblp | 5 | naqfeat | 84.95 | 84.77 | 0.5 |
| dblp | 5 | naqdiff | 85.72 | 85.95 | 1.0 |
| dblp | 5 | cres | 미완료 | 미완료 | 미완료 |

### 2-2. 짝지은 차 (seed 0–2 합친 600 에피소드, 평균 ± SE, 분명 = 평균 > 0 이고 > 2·SE)

| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | sup2 − sup | sup2_l0.5 − sup | +1.90 ± 0.39 | 예 | +1.30 / +1.98 / +2.42 |
| Amazon_clothing | 1 | naqfeat − sup | naqfeat_l1.0 − sup | +6.65 ± 0.39 | 예 | +4.38 / +5.42 / +10.16 |
| Amazon_clothing | 1 | naqfeat − sup2 | naqfeat_l1.0 − sup2_l0.5 | +4.75 ± 0.41 | 예 | +3.08 / +3.44 / +7.74 |
| Amazon_clothing | 1 | naqdiff − sup | naqdiff_l1.0 − sup | +6.14 ± 0.36 | 예 | +6.56 / +4.84 / +7.02 |
| Amazon_clothing | 1 | naqdiff − sup2 | naqdiff_l1.0 − sup2_l0.5 | +4.24 ± 0.41 | 예 | +5.26 / +2.86 / +4.60 |
| Amazon_clothing | 1 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l1.0 | -1.50 ± 0.34 | 아니오 | +0.58 / +0.18 / -5.26 |
| Amazon_clothing | 1 | cres − sup | cres_l0.5 − sup | +0.07 ± 0.35 | 아니오 | -0.36 / -2.24 / +2.80 |
| Amazon_clothing | 1 | cres − sup2 | cres_l0.5 − sup2_l0.5 | -1.83 ± 0.42 | 아니오 | -1.66 / -4.22 / +0.38 |
| Amazon_clothing | 1 | cres − naqfeat | cres_l0.5 − naqfeat_l1.0 | -6.59 ± 0.39 | 아니오 | -4.74 / -7.66 / -7.36 |
| Amazon_clothing | 1 | sup − vision | sup − vision | -3.10 ± 0.45 | 아니오 | -2.62 / -1.62 / -5.06 |
| Amazon_clothing | 1 | sup − tegorig | — | 미완료 | — | — |
| Amazon_clothing | 5 | sup2 − sup | sup2_l0.5 − sup | -0.02 ± 0.21 | 아니오 | -0.10 / -0.14 / +0.18 |
| Amazon_clothing | 5 | naqfeat − sup | naqfeat_l1.0 − sup | +1.79 ± 0.22 | 예 | +0.96 / +1.68 / +2.74 |
| Amazon_clothing | 5 | naqfeat − sup2 | naqfeat_l1.0 − sup2_l0.5 | +1.81 ± 0.22 | 예 | +1.06 / +1.82 / +2.56 |
| Amazon_clothing | 5 | naqdiff − sup | naqdiff_l0.5 − sup | +1.39 ± 0.21 | 예 | +1.42 / +1.28 / +1.48 |
| Amazon_clothing | 5 | naqdiff − sup2 | naqdiff_l0.5 − sup2_l0.5 | +1.41 ± 0.21 | 예 | +1.52 / +1.42 / +1.30 |
| Amazon_clothing | 5 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l1.0 | -0.94 ± 0.20 | 아니오 | -0.72 / -0.78 / -1.32 |
| Amazon_clothing | 5 | cres − sup | cres_l1.0 − sup | +1.25 ± 0.19 | 예 | +1.52 / +0.48 / +1.76 |
| Amazon_clothing | 5 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +1.27 ± 0.21 | 예 | +1.62 / +0.62 / +1.58 |
| Amazon_clothing | 5 | cres − naqfeat | cres_l1.0 − naqfeat_l1.0 | -0.54 ± 0.20 | 아니오 | +0.56 / -1.20 / -0.98 |
| Amazon_clothing | 5 | sup − vision | sup − vision | +0.65 ± 0.27 | 예 | +1.32 / +0.38 / +0.24 |
| Amazon_clothing | 5 | sup − tegorig | — | 미완료 | — | — |
| Amazon_electronics | 1 | sup2 − sup | sup2_l0.5 − sup | +0.83 ± 0.44 | 아니오 | +1.54 / +2.70 / -1.76 |
| Amazon_electronics | 1 | naqfeat − sup | naqfeat_l1.0 − sup | +5.56 ± 0.40 | 예 | +4.94 / +6.38 / +5.36 |
| Amazon_electronics | 1 | naqfeat − sup2 | naqfeat_l1.0 − sup2_l0.5 | +4.73 ± 0.43 | 예 | +3.40 / +3.68 / +7.12 |
| Amazon_electronics | 1 | naqdiff − sup | naqdiff_l1.0 − sup | +2.42 ± 0.44 | 예 | +2.52 / +2.26 / +2.48 |
| Amazon_electronics | 1 | naqdiff − sup2 | naqdiff_l1.0 − sup2_l0.5 | +1.59 ± 0.44 | 예 | +0.98 / -0.44 / +4.24 |
| Amazon_electronics | 1 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l1.0 | -2.25 ± 0.36 | 아니오 | -2.24 / -2.48 / -2.02 |
| Amazon_electronics | 1 | cres − sup | cres_l1.0 − sup | +5.71 ± 0.36 | 예 | +5.34 / +5.40 / +6.38 |
| Amazon_electronics | 1 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +4.88 ± 0.42 | 예 | +3.80 / +2.70 / +8.14 |
| Amazon_electronics | 1 | cres − naqfeat | cres_l1.0 − naqfeat_l1.0 | +0.15 ± 0.34 | 아니오 | +0.40 / -0.98 / +1.02 |
| Amazon_electronics | 1 | sup − vision | sup − vision | -3.43 ± 0.49 | 아니오 | -1.56 / -5.90 / -2.84 |
| Amazon_electronics | 1 | sup − tegorig | — | 미완료 | — | — |
| Amazon_electronics | 5 | sup2 − sup | sup2_l0.5 − sup | -0.01 ± 0.25 | 아니오 | -0.40 / -0.38 / +0.74 |
| Amazon_electronics | 5 | naqfeat − sup | naqfeat_l0.5 − sup | +2.01 ± 0.25 | 예 | +2.24 / +1.66 / +2.14 |
| Amazon_electronics | 5 | naqfeat − sup2 | naqfeat_l0.5 − sup2_l0.5 | +2.03 ± 0.26 | 예 | +2.64 / +2.04 / +1.40 |
| Amazon_electronics | 5 | naqdiff − sup | naqdiff_l0.5 − sup | +0.31 ± 0.26 | 아니오 | -0.22 / +0.26 / +0.88 |
| Amazon_electronics | 5 | naqdiff − sup2 | naqdiff_l0.5 − sup2_l0.5 | +0.32 ± 0.27 | 아니오 | +0.18 / +0.64 / +0.14 |
| Amazon_electronics | 5 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l0.5 | -0.73 ± 0.24 | 아니오 | -1.44 / -0.10 / -0.64 |
| Amazon_electronics | 5 | cres − sup | cres_l1.0 − sup | +2.59 ± 0.24 | 예 | +1.42 / +3.28 / +3.08 |
| Amazon_electronics | 5 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +2.61 ± 0.25 | 예 | +1.82 / +3.66 / +2.34 |
| Amazon_electronics | 5 | cres − naqfeat | cres_l1.0 − naqfeat_l0.5 | +0.58 ± 0.23 | 예 | -0.82 / +1.62 / +0.94 |
| Amazon_electronics | 5 | sup − vision | sup − vision | +0.46 ± 0.33 | 아니오 | +2.16 / +0.08 / -0.86 |
| Amazon_electronics | 5 | sup − tegorig | — | 미완료 | — | — |
| dblp | 1 | sup2 − sup | sup2_l1.0 − sup | +0.27 ± 0.31 | 아니오 | +1.76 / -0.02 / -0.92 |
| dblp | 1 | naqfeat − sup | naqfeat_l1.0 − sup | +1.51 ± 0.30 | 예 | +1.78 / +1.20 / +1.56 |
| dblp | 1 | naqfeat − sup2 | naqfeat_l1.0 − sup2_l1.0 | +1.24 ± 0.33 | 예 | +0.02 / +1.22 / +2.48 |
| dblp | 1 | naqdiff − sup | naqdiff_l1.0 − sup | +2.51 ± 0.28 | 예 | +3.38 / +1.56 / +2.60 |
| dblp | 1 | naqdiff − sup2 | naqdiff_l1.0 − sup2_l1.0 | +2.24 ± 0.31 | 예 | +1.62 / +1.58 / +3.52 |
| dblp | 1 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l1.0 | -0.15 ± 0.28 | 아니오 | +0.44 / -0.56 / -0.32 |
| dblp | 1 | cres − sup | — | 미완료 | — | — |
| dblp | 1 | cres − sup2 | — | 미완료 | — | — |
| dblp | 1 | cres − naqfeat | — | 미완료 | — | — |
| dblp | 1 | sup − vision | sup − vision | +4.13 ± 0.45 | 예 | +2.92 / +4.98 / +4.48 |
| dblp | 1 | sup − tegorig | — | 미완료 | — | — |
| dblp | 5 | sup2 − sup | sup2_l1.0 − sup | +0.68 ± 0.21 | 예 | +0.26 / +0.50 / +1.28 |
| dblp | 5 | naqfeat − sup | naqfeat_l0.5 − sup | +0.91 ± 0.20 | 예 | +0.76 / +1.10 / +0.88 |
| dblp | 5 | naqfeat − sup2 | naqfeat_l0.5 − sup2_l1.0 | +0.23 ± 0.22 | 아니오 | +0.50 / +0.60 / -0.40 |
| dblp | 5 | naqdiff − sup | naqdiff_l1.0 − sup | +1.62 ± 0.21 | 예 | +1.50 / +1.74 / +1.62 |
| dblp | 5 | naqdiff − sup2 | naqdiff_l1.0 − sup2_l1.0 | +0.94 ± 0.22 | 예 | +1.24 / +1.24 / +0.34 |
| dblp | 5 | naqfeat_allpool − naqfeat | naqfeat_allpool − naqfeat_l0.5 | -0.17 ± 0.19 | 아니오 | -0.04 / -0.12 / -0.34 |
| dblp | 5 | cres − sup | — | 미완료 | — | — |
| dblp | 5 | cres − sup2 | — | 미완료 | — | — |
| dblp | 5 | cres − naqfeat | — | 미완료 | — | — |
| dblp | 5 | sup − vision | sup − vision | +3.67 ± 0.35 | 예 | +3.32 / +3.50 / +4.20 |
| dblp | 5 | sup − tegorig | — | 미완료 | — | — |

(sup − vision의 음수 행은 방향을 바꾸면 vision이 "분명"히 높다: Clothing K=1, Electronics K=1. 007과 같은 값.)

### 2-3. 진단, 방법 아님 — 순도 곡선 (013; valid·test 레이블로 에피소드 구성)

| 데이터셋 | K | rho0 | rho15 | rho30 | rho45 | rho0_nocollide | naqfeat(선택 λ) |
|---|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 87.53 | 86.63 | 84.66 | 84.65 | 88.44 | 86.75 |
| Amazon_clothing | 5 | 92.77 | 92.03 | 91.68 | 91.67 | 93.44 | 92.48 |
| Amazon_electronics | 1 | 80.62 | 79.97 | 79.57 | 79.49 | 80.13 | 79.59 |
| Amazon_electronics | 5 | 89.61 | 89.51 | 89.19 | 89.20 | 90.35 | 89.43 |
| dblp | 1 | 79.93 | 79.51 | 78.26 | 78.26 | 79.73 | 77.25 |
| dblp | 5 | 86.42 | 86.11 | 85.81 | 85.81 | 86.43 | 85.30 |

(rho30과 rho45는 n = 5에서 같은 목표 0.4. 차이는 GPU 간 비결정성, 013 §2.)

| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | rho0 − rho45 | diag_rho0 − diag_rho45 | +2.88 ± 0.32 | 예 | +1.60 / +2.82 / +4.22 |
| Amazon_clothing | 1 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | +0.91 ± 0.26 | 예 | +1.60 / +2.48 / -1.34 |
| Amazon_clothing | 1 | rho0 − naqfeat | diag_rho0 − naqfeat_l1.0 | +0.78 ± 0.22 | 예 | +1.14 / +0.68 / +0.52 |
| Amazon_clothing | 1 | naqfeat − rho45 | naqfeat_l1.0 − diag_rho45 | +2.10 ± 0.32 | 예 | +0.46 / +2.14 / +3.70 |
| Amazon_clothing | 5 | rho0 − rho45 | diag_rho0 − diag_rho45 | +1.10 ± 0.18 | 예 | +1.40 / +1.28 / +0.62 |
| Amazon_clothing | 5 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | +0.67 ± 0.17 | 예 | -0.32 / +0.96 / +1.36 |
| Amazon_clothing | 5 | rho0 − naqfeat | diag_rho0 − naqfeat_l1.0 | +0.29 ± 0.17 | 아니오 | +0.76 / +0.38 / -0.26 |
| Amazon_clothing | 5 | naqfeat − rho45 | naqfeat_l1.0 − diag_rho45 | +0.81 ± 0.17 | 예 | +0.64 / +0.90 / +0.88 |
| Amazon_electronics | 1 | rho0 − rho45 | diag_rho0 − diag_rho45 | +1.13 ± 0.27 | 예 | +0.94 / +1.16 / +1.28 |
| Amazon_electronics | 1 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | -0.49 ± 0.30 | 아니오 | -0.60 / -0.68 / -0.20 |
| Amazon_electronics | 1 | rho0 − naqfeat | diag_rho0 − naqfeat_l1.0 | +1.03 ± 0.27 | 예 | +1.58 / +0.28 / +1.22 |
| Amazon_electronics | 1 | naqfeat − rho45 | naqfeat_l1.0 − diag_rho45 | +0.10 ± 0.28 | 아니오 | -0.64 / +0.88 / +0.06 |
| Amazon_electronics | 5 | rho0 − rho45 | diag_rho0 − diag_rho45 | +0.41 ± 0.19 | 예 | +0.04 / +0.78 / +0.40 |
| Amazon_electronics | 5 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | +0.74 ± 0.21 | 예 | +0.52 / +0.80 / +0.90 |
| Amazon_electronics | 5 | rho0 − naqfeat | diag_rho0 − naqfeat_l0.5 | +0.18 ± 0.17 | 아니오 | -0.44 / +0.78 / +0.20 |
| Amazon_electronics | 5 | naqfeat − rho45 | naqfeat_l0.5 − diag_rho45 | +0.23 ± 0.19 | 아니오 | +0.48 / -0.00 / +0.20 |
| dblp | 1 | rho0 − rho45 | diag_rho0 − diag_rho45 | +1.67 ± 0.22 | 예 | +2.32 / +1.68 / +1.00 |
| dblp | 1 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | -0.20 ± 0.21 | 아니오 | -0.96 / +0.08 / +0.28 |
| dblp | 1 | rho0 − naqfeat | diag_rho0 − naqfeat_l1.0 | +2.68 ± 0.25 | 예 | +3.26 / +2.00 / +2.78 |
| dblp | 1 | naqfeat − rho45 | naqfeat_l1.0 − diag_rho45 | -1.01 ± 0.21 | 아니오 | -0.94 / -0.32 / -1.78 |
| dblp | 5 | rho0 − rho45 | diag_rho0 − diag_rho45 | +0.61 ± 0.14 | 예 | +0.60 / +0.72 / +0.52 |
| dblp | 5 | nocollide − rho0 | diag_rho0_nocollide − diag_rho0 | +0.01 ± 0.13 | 아니오 | -0.12 / +0.18 / -0.02 |
| dblp | 5 | rho0 − naqfeat | diag_rho0 − naqfeat_l0.5 | +1.12 ± 0.17 | 예 | +1.34 / +1.44 / +0.58 |
| dblp | 5 | naqfeat − rho45 | naqfeat_l0.5 − diag_rho45 | -0.51 ± 0.15 | 아니오 | -0.74 / -0.72 / -0.06 |

P09 기계 적용:

| 데이터셋 | K | 자연 오염률(NaQ 점) | naqfeat(선택 λ) | rho0 − rho45 | 판정 | 사용자 예측 적중 | Claude 예측 적중 |
|---|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 0.248 | 86.75 | +2.88 ± 0.32 | 분명 | 아니오 | 아니오 |
| Amazon_clothing | 5 | 0.248 | 92.48 | +1.10 ± 0.18 | 분명 | 아니오 | 예 |
| Amazon_electronics | 1 | 0.245 | 79.59 | +1.13 ± 0.27 | 분명 | 아니오 | 예 |
| Amazon_electronics | 5 | 0.245 | 89.43 | +0.41 ± 0.19 | 분명 | 예 | 예 |
| dblp | 1 | 0.711 | 77.25 | +1.67 ± 0.22 | 분명 | 아니오 | 예 |
| dblp | 5 | 0.711 | 85.30 | +0.61 ± 0.14 | 분명 | 예 | 예 |

- 사용자 예측 적중 2/6칸, Claude 주 예측 적중 5/6칸, Claude 보조 예측(nocollide − rho0 구분 안 됨) 3/6칸.

### 2-4. 생성기 통계

011 NaQ (seed 0, 1000 에피소드; v1 = 006 구성, v2 = 011):

| 데이터셋 | K | 생성기 | v1(006) 중복 에피소드 비율 | v2(011) anchor 재추첨 / 1000 | way 사이 클래스 충돌률 |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | feat | 0.025 | 0 | 0.344 |
| Amazon_clothing | 5 | feat | 0.055 | 0 | 0.344 |
| Amazon_clothing | 1 | diff | 0.083 | 0 | 0.344 |
| Amazon_clothing | 5 | diff | 0.126 | 0 | 0.344 |
| Amazon_electronics | 1 | feat | 0.013 | 0 | 0.179 |
| Amazon_electronics | 5 | feat | 0.040 | 0 | 0.179 |
| Amazon_electronics | 1 | diff | 0.517 | 0 | 0.179 |
| Amazon_electronics | 5 | diff | 0.682 | 0 | 0.179 |
| dblp | 1 | feat | 0.047 | 0 | 0.213 |
| dblp | 5 | feat | 0.101 | 0 | 0.213 |
| dblp | 1 | diff | 0.016 | 0 | 0.213 |
| dblp | 5 | diff | 0.041 | 0 | 0.213 |

- 011 학습 실행 90개(72 + allpool 18)에서 anchor 재추첨 합계 0, 중복 노드 에피소드 0.

014 CRES (500 에피소드, 학습과 독립 인스턴스):

| 데이터셋 | K | seed | anchor 추첨/에피소드 | anchor 조건 실패 | query 조건 재추첨 비율 | 중복 노드 | way 사이 클래스 충돌률 | way 안 오염률 |
|---|---|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 0 | 1.774 | 0 | 0.000 | 0 | 0.158 | 0.1206 |
| Amazon_clothing | 1 | 1 | 1.848 | 0 | 0.000 | 0 | 0.136 | 0.1226 |
| Amazon_clothing | 1 | 2 | 1.628 | 0 | 0.000 | 0 | 0.156 | 0.1250 |
| Amazon_clothing | 5 | 0 | 1.800 | 0 | 0.000 | 0 | 0.128 | 0.1361 |
| Amazon_clothing | 5 | 1 | 1.826 | 0 | 0.000 | 0 | 0.126 | 0.1081 |
| Amazon_clothing | 5 | 2 | 1.676 | 0 | 0.000 | 0 | 0.104 | 0.1266 |
| Amazon_electronics | 1 | 0 | 1.484 | 0 | 0.000 | 0 | 0.028 | 0.1382 |
| Amazon_electronics | 1 | 1 | 1.664 | 0 | 0.000 | 0 | 0.032 | 0.1676 |
| Amazon_electronics | 1 | 2 | 1.522 | 0 | 0.000 | 0 | 0.068 | 0.1309 |
| Amazon_electronics | 5 | 0 | 1.534 | 0 | 0.000 | 0 | 0.024 | 0.1382 |
| Amazon_electronics | 5 | 1 | 1.690 | 0 | 0.000 | 0 | 0.054 | 0.1681 |
| Amazon_electronics | 5 | 2 | 1.528 | 0 | 0.000 | 0 | 0.060 | 0.1448 |

- 014 학습 실행 24개: anchor 조건 실패 0, query 조건 재추첨 0, 중복 노드 0.

## 3. 사전 등록 대비 결과 (기계 적용)

| 등록 | 항목 | 결과 |
|---|---|---|
| P07 | (a) 006 중복률 0 칸의 K=1 에피소드 단위 동일성 | 해당 칸 없음(006 중복률 최소 0.015). 생성기 단위 대체 점검: v1·v2 열은 첫 중복 에피소드 직전까지 동일(6/6) |
| P07 | (b) 비교 계획 | 위 2-2에 기록 |
| P08 | 예측 1: sup2 − sup는 K=1에서 양수, +NaQ − sup보다 작다 | K=1 평균: Clothing +1.90, Electronics +0.83, dblp +0.27 (모두 양수, "분명"은 Clothing만); 세 칸 모두 naqfeat − sup·naqdiff − sup보다 작음 → **적중** |
| P08 | 예측 2: +NaQ-Feat − sup2가 6칸 중 4칸 이상 "분명" | 5/6칸 → **적중** (dblp K=5만 구분 안 됨) |
| P08 | 사용자 입장: "NaQ 이득이 레이블 없는 노드 덕분"은 +NaQ − sup2 "분명"일 때만 | naqfeat − sup2 "분명" 5/6, naqdiff − sup2 "분명" 5/6 |
| P09 | 사용자 예측 | 2/6칸 적중 (Electronics K=5, dblp K=5) |
| P09 | Claude 예측 (주) | 5/6칸 적중 (Clothing K=1은 +2.88로 2%p 초과) |
| P09 | Claude 예측 (보조, nocollide − rho0 구분 안 됨) | 3/6칸 적중 |
| P09 | 해석 규칙 기계 적용 | Claude 예측 쪽 칸이 많음 → "여지는 있으나 작다 — 순도 개선폭을 NaQ 점 대비 %p로 환산": rho0 − naqfeat = Clothing +0.78 / +0.29, Electronics +1.03 / +0.18, dblp +2.68 / +1.12 (K=1 / K=5; K=5 Amazon 두 칸은 분명 아님) |
| P10 | 판정 없음 | cres − sup2 "분명" 3/4, cres − naqfeat "분명" 1/4 (Electronics K=5 +0.58), Clothing K=1은 naqfeat가 6.59%p 높음 |

## 4. 결정 필요 (전 항목, `reports/QUEUE_STATE_2.md`와 같음)

1. (012) 체크포인트 선택이 고정 valid 100이 아니라 학습 중 전역 random valid 50(TEG-choi 규칙). sup2는 이 50개가 sup과 다름. 현행 유지 여부.
2. (011) (a) 점검 해당 칸 없음(006 중복률 0 칸 없음) → 생성기 단위 점검으로 대체. 충분한지.
3. (011) pseudo query 수 Q=5 유지(원 NaQ 학습 q_query 10).
4. (011) allpool 이웃 표는 전체 노드·seed 무관 1회.
5. (013) n=5라 rho30 = rho45(목표 0.4 동일). ρ 격자/n 변경 여부.
6. (013) dblp 자연 오염률 0.71 — 곡선 범위 밖. 범위 확장 여부.
7. (013) 치환 유사도 s_X = R003(log1p 코사인), NaQ-Feat(원시 코사인)와 다름.
8. (013) GPU 간 비결정성: 같은 설정 18쌍 중 7쌍 최대 0.16%p 차이. 재실행 변동 평가 방식.
9. (014) query 조건(008 §1-3) 미발동 — 유지 여부.
10. (015) TEG-orig 환경: torch-sparse cu113 import 실패(libcusparse.so.11 없음). cudatoolkit 추가 설치 / cres 환경 실행 / skip 유지.
11. (015) PyG 확장 버전을 휠 있는 버전(2.0.9 / 0.6.13)으로 고정해 시도.

## 5. 자원·디스크, 참고 리포

- GPU 2장(RTX 3090) GPU당 2개 동시. 실행 시간 중앙값: 012 40 s, 011 42.5 s, 013 44 s, 014 54 s. `max_memory_allocated` 최대 6167 MB(014).
- 디스크: 시작 15G 사용 → 종료 20G 사용 / 60G (+4.1G `/venv/tegorig` conda 환경, 지우지 않음). 
- 참고 리포 4개 `git status --porcelain` 모두 빈 출력(clean): TEG-orig `b5a8e03`, TEG-choi `3b7be89`, NaQ `cfe5373`, VISION `0524eae`.
- job_runner는 대기열이 빈 뒤 Agent가 종료했다(`exit_when_idle 0`으로 띄웠으므로, state에 `killed_by_agent_idle` 기록).

## 6. 해석 ([추정], 최대 5줄)

- [추정] +NaQ-Feat의 이득은 계산량(스텝당 에피소드 2개)만으로는 대부분 설명되지 않는다(sup2 대비 5/6칸 분명).
- [추정] 순도는 정확도를 바꾸지만 폭이 작다: 오염 0.4→0에서 K=1 1.1–2.9%p, K=5 0.4–1.1%p. Amazon 두 데이터셋에서 NaQ 점 대비 상한 여지는 K=1 약 0.8–1.0%p, K=5는 구분 안 됨.
- [추정] dblp는 NaQ-Feat의 자연 오염률이 0.71로 높아 순도 개선 여지가 가장 크다(rho0 − naqfeat K=1 +2.68%p) — 그러나 dblp는 G2 불통과로 014에서 제외됐다.
- [추정] 현 CRES 생성기는 way 안 오염(0.11–0.17)이 NaQ(0.25)보다 낮은데도 Amazon_clothing K=1에서 naqfeat보다 크게 낮다 — 순도 외 요인(다양성, core 은행 편향 등)이 작용하는 것으로 보인다.
- [추정] TEG-orig 공식 대조는 아직 없다(015 skip).
