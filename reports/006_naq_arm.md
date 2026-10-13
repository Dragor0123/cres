# 006 +NaQ식 arm (재구현)과 sweep

작성 2026-10-13 (야간 큐) · 등록 P04 (실행 전 커밋 `50d4d53`)

## 1. 무엇을 했는지

- `baselines/naq/generator.py`: NaQ-Feat, NaQ-Diff 재구현(refs/NaQ 코드 복사 없음). rng `22000+seed`(numpy Generator).
- `cres/teg/run.py --pseudo naq_feat|naq_diff --lam λ`: 003 백본 `train_step(sup, pseudo, lam)`. 스텝마다 지도 에피소드 1개 + pseudo-episode 1개, 두 에피소드가 같은 GCN 출력을 공유, L = L_sup + λ·L_pseudo(L_pseudo도 γ·L_N + (1−γ)·L_G). epoch 0은 원본대로 갱신 없음이며 pseudo도 만들지 않는다.
- 이웃 표 사전 계산(데이터셋 × seed × 종류 18개, 합계 3분 48초) → `results/006/<ds>/naq_<kind>_seed<s>_top9.npy`.
- sweep: `results/sweep/jobs_all.jsonl`(72개, K=1 먼저), `tools/job_runner.py --max_per_gpu 2`, GPU-A·B 교대 배정. 기록 `records/006_naq/ep_acc_<ds>_K<k>_seed<s>_naq<kind>_l<λ>.csv`, `run_meta.jsonl`.

### 원 NaQ와의 차이 (refs/NaQ `cfe5373`를 읽고 확인한 사실)

| 항목 | 원 NaQ | 이 재구현 |
|---|---|---|
| support | way마다 무작위 노드 1개(`task_generator.py` `spt_sampling`, `spt_to_sample = 1`, UMTRA식) | anchor 1개 + anchor의 상위 이웃 K−1개(K=5면 4개) |
| query | support 노드 행의 상위 q개(`query_generation_NaQ`; 학습 `q_query` 기본 10, `arg.py:23, 76`) | 상위 이웃 중 support로 쓰지 않은 다음 Q=5개 |
| 노드 풀 | `id_train` = 모든 클래스의 모든 노드(`data.py:96-98`) | U = 그 seed의 base가 아닌 노드(valid ∪ test). 이웃 후보도 U 안 |
| Feat 유사도 | 원시 특징 행 L2 정규화 후 코사인(`utils.py:33-39`) | 같음(log1p 없음) |
| Diff 유사도 | GDC `transition_matrix(normalization='sym')`(자기 루프 추가 없음) → `diffusion_matrix_exact(method='ppr', alpha=0.1)`(`utils.py:42-45`, `arg.py:45`) | 같은 정의. 역행렬 대신 멱반복 200회(잘림 오차 ≤ 0.9^200) |
| 자기 자신 | 대각 0(`utils.py:48`) | 자기 자신 제외(점수 −inf) |
| way 충돌 | 막지 않음 | 막지 않음 |
| 학습 방식 | 비지도 메타학습(ProtoNet/MAML 등, 레이블 없음) | 지도 에피소드 + λ·pseudo 에피소드(TEG 백본) |
| 동점 | `topk` | 안정 정렬(노드 id 오름차순) |

## 2. 사실

실행: 72/72 완료, 실패·재시도 0 (`results/sweep/state_all.jsonl`, 15:36–15:50 UTC). 실행 시간 25–49 s(중앙값 41 s), `max_memory_allocated` 최대 3182 MB. 각 실행에서 pseudo-episode 500개(10 에폭 × 50).

### 고정 test 정확도 (%, seed 0 / 1 / 2, 평균; 출처 `records/006_naq/`, 지도 단독은 `records/003_teg_port/`)

| 데이터셋 | K | arm | seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|
| Amazon_clothing | 1 | sup | 81.46 / 81.16 / 77.66 | 80.09 |
| Amazon_clothing | 1 | naqfeat_l0.5 | 85.42 / 86.46 / 87.42 | 86.43 |
| Amazon_clothing | 1 | naqfeat_l1.0 | 86.20 / 85.76 / 87.80 | 86.59 |
| Amazon_clothing | 1 | naqdiff_l0.5 | 86.80 / 86.14 / 84.10 | 85.68 |
| Amazon_clothing | 1 | naqdiff_l1.0 | 88.16 / 86.30 / 85.70 | 86.72 |
| Amazon_clothing | 5 | sup | 91.80 / 90.20 / 90.06 | 90.69 |
| Amazon_clothing | 5 | naqfeat_l0.5 | 93.94 / 91.24 / 92.26 | 92.48 |
| Amazon_clothing | 5 | naqfeat_l1.0 | 93.48 / 91.58 / 92.46 | 92.51 |
| Amazon_clothing | 5 | naqdiff_l0.5 | 90.62 / 90.54 / 90.40 | 90.52 |
| Amazon_clothing | 5 | naqdiff_l1.0 | 90.12 / 90.68 / 90.58 | 90.46 |
| Amazon_electronics | 1 | sup | 75.10 / 71.16 / 75.84 | 74.03 |
| Amazon_electronics | 1 | naqfeat_l0.5 | 79.26 / 76.54 / 80.54 | 78.78 |
| Amazon_electronics | 1 | naqfeat_l1.0 | 80.20 / 77.50 / 81.28 | 79.66 |
| Amazon_electronics | 1 | naqdiff_l0.5 | 77.64 / 71.66 / 77.10 | 75.47 |
| Amazon_electronics | 1 | naqdiff_l1.0 | 77.24 / 71.58 / 77.58 | 75.47 |
| Amazon_electronics | 5 | sup | 87.76 / 86.74 / 87.74 | 87.41 |
| Amazon_electronics | 5 | naqfeat_l0.5 | 89.80 / 89.44 / 90.82 | 90.02 |
| Amazon_electronics | 5 | naqfeat_l1.0 | 90.20 / 89.22 / 91.12 | 90.18 |
| Amazon_electronics | 5 | naqdiff_l0.5 | 86.38 / 86.62 / 87.54 | 86.85 |
| Amazon_electronics | 5 | naqdiff_l1.0 | 85.16 / 85.40 / 87.50 | 86.02 |
| dblp | 1 | sup | 75.38 / 75.14 / 76.68 | 75.73 |
| dblp | 1 | naqfeat_l0.5 | 77.08 / 75.62 / 78.06 | 76.92 |
| dblp | 1 | naqfeat_l1.0 | 77.24 / 75.86 / 78.08 | 77.06 |
| dblp | 1 | naqdiff_l0.5 | 77.58 / 76.68 / 78.38 | 77.55 |
| dblp | 1 | naqdiff_l1.0 | 78.04 / 76.74 / 79.64 | 78.14 |
| dblp | 5 | sup | 84.24 / 84.88 / 84.04 | 84.39 |
| dblp | 5 | naqfeat_l0.5 | 85.02 / 86.26 / 85.46 | 85.58 |
| dblp | 5 | naqfeat_l1.0 | 84.90 / 86.22 / 85.86 | 85.66 |
| dblp | 5 | naqdiff_l0.5 | 85.48 / 86.38 / 85.82 | 85.89 |
| dblp | 5 | naqdiff_l1.0 | 85.78 / 86.60 / 86.24 | 86.21 |
| Amazon_clothing | 1 | naq_feat | 81.53 | 81.84 | 1.0 |
| Amazon_clothing | 1 | naq_diff | 81.52 | 82.43 | 1.0 |
| Amazon_clothing | 5 | naq_feat | 89.60 | 89.91 | 1.0 |
| Amazon_clothing | 5 | naq_diff | 87.67 | 87.48 | 0.5 |
| Amazon_electronics | 1 | naq_feat | 84.55 | 86.29 | 1.0 |
| Amazon_electronics | 1 | naq_diff | 83.53 | 84.12 | 1.0 |
| Amazon_electronics | 5 | naq_feat | 93.01 | 92.93 | 0.5 |
| Amazon_electronics | 5 | naq_diff | 91.00 | 90.76 | 0.5 |
| dblp | 1 | naq_feat | 76.01 | 76.21 | 1.0 |
| dblp | 1 | naq_diff | 77.01 | 77.32 | 1.0 |
| dblp | 5 | naq_feat | 85.80 | 85.56 | 0.5 |
| dblp | 5 | naq_diff | 85.64 | 85.69 | 1.0 |
| Amazon_clothing | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +6.49 ± 0.40 | 예 | +4.74 / +4.60 / +10.14 |
| Amazon_clothing | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +6.63 ± 0.39 | 예 | +6.70 / +5.14 / +8.04 |
| Amazon_clothing | 5 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.82 ± 0.20 | 예 | +1.68 / +1.38 / +2.40 |
| Amazon_clothing | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.17 ± 0.22 | 아니오 | -1.18 / +0.34 / +0.34 |
| Amazon_electronics | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +5.63 ± 0.40 | 예 | +5.10 / +6.34 / +5.44 |
| Amazon_electronics | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.43 ± 0.39 | 예 | +2.14 / +0.42 / +1.74 |
| Amazon_electronics | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +2.61 ± 0.23 | 예 | +2.04 / +2.70 / +3.08 |
| Amazon_electronics | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.57 ± 0.28 | 아니오 | -1.38 / -0.12 / -0.20 |
| dblp | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.33 ± 0.31 | 예 | +1.86 / +0.72 / +1.40 |
| dblp | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +2.41 ± 0.25 | 예 | +2.66 / +1.60 / +2.96 |
| dblp | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +1.19 ± 0.21 | 예 | +0.78 / +1.38 / +1.42 |
| dblp | 5 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.82 ± 0.21 | 예 | +1.54 / +1.72 / +2.20 |

### λ 선택 (P04 규칙: seed 평균 고정 valid 최고, 동률이면 작은 λ; %)

| 데이터셋 | K | 생성기 | λ 0.5 | λ 1.0 | 선택 |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | naq_feat | 81.53 | 81.84 | 1.0 |
| Amazon_clothing | 1 | naq_diff | 81.52 | 82.43 | 1.0 |
| Amazon_clothing | 5 | naq_feat | 89.60 | 89.91 | 1.0 |
| Amazon_clothing | 5 | naq_diff | 87.67 | 87.48 | 0.5 |
| Amazon_electronics | 1 | naq_feat | 84.55 | 86.29 | 1.0 |
| Amazon_electronics | 1 | naq_diff | 83.53 | 84.12 | 1.0 |
| Amazon_electronics | 5 | naq_feat | 93.01 | 92.93 | 0.5 |
| Amazon_electronics | 5 | naq_diff | 91.00 | 90.76 | 0.5 |
| dblp | 1 | naq_feat | 76.01 | 76.21 | 1.0 |
| dblp | 1 | naq_diff | 77.01 | 77.32 | 1.0 |
| dblp | 5 | naq_feat | 85.80 | 85.56 | 0.5 |
| dblp | 5 | naq_diff | 85.64 | 85.69 | 1.0 |

### 선택된 λ의 짝지은 차 (+NaQ식 − 지도 단독, %p, seed 0–2 에피소드 600개 합침 ± SE; seed별 평균)

| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE | 분명 | seed별 평균 (0 / 1 / 2) |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +6.49 ± 0.40 | 예 | +4.74 / +4.60 / +10.14 |
| Amazon_clothing | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +6.63 ± 0.39 | 예 | +6.70 / +5.14 / +8.04 |
| Amazon_clothing | 5 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.82 ± 0.20 | 예 | +1.68 / +1.38 / +2.40 |
| Amazon_clothing | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.17 ± 0.22 | 아니오 | -1.18 / +0.34 / +0.34 |
| Amazon_electronics | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +5.63 ± 0.40 | 예 | +5.10 / +6.34 / +5.44 |
| Amazon_electronics | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.43 ± 0.39 | 예 | +2.14 / +0.42 / +1.74 |
| Amazon_electronics | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +2.61 ± 0.23 | 예 | +2.04 / +2.70 / +3.08 |
| Amazon_electronics | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.57 ± 0.28 | 아니오 | -1.38 / -0.12 / -0.20 |
| dblp | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.33 ± 0.31 | 예 | +1.86 / +0.72 / +1.40 |
| dblp | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +2.41 ± 0.25 | 예 | +2.66 / +1.60 / +2.96 |
| dblp | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +1.19 ± 0.21 | 예 | +0.78 / +1.38 / +1.42 |
| dblp | 5 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.82 ± 0.21 | 예 | +1.54 / +1.72 / +2.20 |

- "분명" 표기는 CLAUDE.md §5 규칙(평균 > 0 이고 > 2·SE)의 기계적 적용이다. P04는 판정 기준이 없는 측정 arm이다.

### 생성기 통계 (pseudo-episode 중 같은 노드가 두 번 이상 들어간 비율, seed·λ 평균)

| 데이터셋 | K | Feat | Diff |
|---|---|---|---|
| Amazon_clothing | 1 | 0.021 | 0.077 |
| Amazon_electronics | 1 | 0.015 | 0.521 |
| dblp | 1 | 0.043 | 0.015 |
| Amazon_clothing | 5 | 0.049 | 0.116 |
| Amazon_electronics | 5 | 0.035 | 0.683 |
| dblp | 5 | 0.092 | 0.041 |

(way 사이 충돌을 막지 않으므로 서로 다른 anchor의 이웃 목록이 겹치면 같은 노드가 여러 way에 들어간다. 실제 클래스 충돌률은 생성기가 레이블을 읽지 않아 기록하지 않았다.)

## 3. 게이트

006은 게이트 없음(P04: 측정 arm). 실행 조건 G3: 충족(003 2차).

## 4. 결정 필요

1. 이 재구현은 원 NaQ와 support 구성(anchor + 상위 이웃 K−1개)과 노드 풀(U, base 제외)이 다르다(위 표). 원 NaQ 학습은 support 1개(K=1)만 다루므로 K=5 구성 방식과 풀 선택은 사용자 검토 대상.
2. Electronics에서 NaQ-Diff pseudo-episode의 52–68%가 같은 노드를 두 번 이상 포함한다(PPR 상위 목록이 겹침). 중복 허용 여부 검토 필요.

## 5. 참고 리포

refs/NaQ는 읽기만 했고 코드를 복사하지 않았다. clean 확인은 009에서.

