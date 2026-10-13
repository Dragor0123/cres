# 013 순도 곡선 진단 — 진단, 방법 아님

작성 2026-10-13 (2차 큐) · 등록 P09 (실행 전 커밋 `6bd4ac1`) · 결정 R004 §4·§10

**이 실험은 pseudo-episode 구성에 valid·test 노드의 실제 레이블을 쓴다(CLAUDE.md §4 예외).** 방법이 아니라 상한을 재는 진단이다.

## 1. 무엇을 했는지

- 격리: 코드 `cres/diag/purity_curve.py`(레이블을 읽는 클래스에 `# DIAG-ONLY: reads non-base labels`, 다른 모듈에서 import 없음 — `grep -rn "cres.diag\|purity_curve"`로 확인: 참조는 `tools/make_jobs_queue2.py`의 실행 명령 문자열뿐), arm 접두어 `diag_`(코드에서 assert), records `records/013_purity_diag/`. 실행 로그 첫 줄 `DIAG: non-base labels used for episode construction`(90개 로그 모두 확인), 둘째 줄에 사용 레이블 집합(valid·test 클래스 목록).
- 출발 에피소드(A1): 011 NaQ-Feat v2 생성기(풀 U, rng `22000+seed`, 중복 금지). 011 구성상 way = anchor(support 1개) + query 5개 → 비anchor 멤버 n = 5(K=1, 5 모두). 지시서 예시의 n = 9(K=5)는 011 구성에서 생기지 않는다.
- 목표 다른 클래스 멤버 수 round(ρ·5): ρ 0 / 0.15 / 0.30 / 0.45 → **0 / 1 / 2 / 2**(Python round; 지시서 예시와 같음). 따라서 **rho30과 rho45는 같은 목표(0.4)** 다.
- 치환(013 §2): 줄일 때 다른 클래스 멤버를 anchor와 s_X 낮은 순으로 빼고, U 안·에피소드 밖 같은 클래스 노드를 s_X 높은 순으로 넣음. 늘릴 때 같은 클래스 멤버를 s_X 낮은 순으로 빼고, U 안·에피소드 밖 다른 클래스 노드를 s_X 높은 순으로 넣음. 슬롯 유지. s_X = R003 정의 cos(L2정규화(log1p X)). 동률 rng `25000+seed`(CLAUDE.md 오프셋 표에 추가, 커밋 `6bd4ac1`).
- B2 `diag_rho0_nocollide`: anchor 5개 실제 클래스가 모두 다를 때까지 에피소드 재생성(011 생성기 다음 추첨, 최대 50회) + ρ=0 치환.
- 학습: 003 백본, L = L_sup + λ·L_pseudo, λ = `records/011_naq_v2/lambda_selected.json`의 NaQ-Feat 값(탐색 없음).
- 실행: job_runner(`results/queue2/`), 90개 23:33–23:50 UTC, 실패·재시도 0, 실행 시간 중앙값 44 s(최대 54 s). K=1 먼저.

## 2. 사실

### ρ별 고정 test 정확도 (%, 출처 `records/013_purity_diag/`)

| 데이터셋 | K | arm | 목표 오염 | 달성 오염 (seed 0/1/2) | 고정 test seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 86.98 / 87.26 / 88.34 | 87.53 |
| Amazon_clothing | 1 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 87.36 / 86.00 / 86.52 | 86.63 |
| Amazon_clothing | 1 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 85.38 / 84.44 / 84.16 | 84.66 |
| Amazon_clothing | 1 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 85.38 / 84.44 / 84.12 | 84.65 |
| Amazon_clothing | 1 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 88.58 / 89.74 / 87.00 | 88.44 |
| Amazon_electronics | 1 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 81.62 / 77.82 / 82.42 | 80.62 |
| Amazon_electronics | 1 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 81.00 / 77.52 / 81.40 | 79.97 |
| Amazon_electronics | 1 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 80.84 / 76.66 / 81.20 | 79.57 |
| Amazon_electronics | 1 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 80.68 / 76.66 / 81.14 | 79.49 |
| Amazon_electronics | 1 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 81.02 / 77.14 / 82.22 | 80.13 |
| dblp | 1 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 80.42 / 78.34 / 81.02 | 79.93 |
| dblp | 1 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 80.00 / 78.02 / 80.50 | 79.51 |
| dblp | 1 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 78.10 / 76.66 / 80.02 | 78.26 |
| dblp | 1 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 78.10 / 76.66 / 80.02 | 78.26 |
| dblp | 1 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 79.46 / 78.42 / 81.30 | 79.73 |
| Amazon_clothing | 5 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 93.52 / 92.26 / 92.54 | 92.77 |
| Amazon_clothing | 5 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 91.74 / 91.90 / 92.46 | 92.03 |
| Amazon_clothing | 5 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 92.12 / 91.00 / 91.92 | 91.68 |
| Amazon_clothing | 5 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 92.12 / 90.98 / 91.92 | 91.67 |
| Amazon_clothing | 5 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 93.20 / 93.22 / 93.90 | 93.44 |
| Amazon_electronics | 5 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 89.56 / 89.18 / 90.08 | 89.61 |
| Amazon_electronics | 5 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 89.74 / 89.00 / 89.78 | 89.51 |
| Amazon_electronics | 5 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 89.48 / 88.40 / 89.68 | 89.19 |
| Amazon_electronics | 5 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 89.52 / 88.40 / 89.68 | 89.20 |
| Amazon_electronics | 5 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 90.08 / 89.98 / 90.98 | 90.35 |
| dblp | 5 | diag_rho0 | 0.0 | 0.000 / 0.000 / 0.000 | 86.34 / 87.42 / 85.50 | 86.42 |
| dblp | 5 | diag_rho15 | 0.2 | 0.200 / 0.200 / 0.200 | 86.12 / 86.90 / 85.32 | 86.11 |
| dblp | 5 | diag_rho30 | 0.4 | 0.400 / 0.400 / 0.400 | 85.74 / 86.70 / 84.98 | 85.81 |
| dblp | 5 | diag_rho45 | 0.4 | 0.400 / 0.400 / 0.400 | 85.74 / 86.70 / 84.98 | 85.81 |
| dblp | 5 | diag_rho0_nocollide | 0.0 | 0.000 / 0.000 / 0.000 | 86.22 / 87.60 / 85.48 | 86.43 |

- 달성 오염률은 90개 실행 모두 목표와 같다(`contam_note` 없음). 치환 실패(후보 부족) way 0개.
- 오염 위치: 011 구성에서 support는 anchor 1개뿐이므로 **오염은 모두 query에 있다**(support 0개, query 225,000 노드·실행 합계).
- B2 재생성 횟수: 에피소드당 평균 1.332회, 50회 실패 0.

### 자연 오염률 (NaQ 점; 치환 전 011 NaQ-Feat v2, seed별 1000 에피소드)

| 데이터셋 | seed 0 / 1 / 2 자연 오염률 (1000 에피소드) | 평균 | NaQ 점 위치 (목표 오염 기준) |
|---|---|---|---|
| Amazon_clothing | 0.2482 / 0.2381 / 0.2571 | 0.2478 | 0.2(rho15) ~ 0.4(rho30·45) 사이 |
| Amazon_electronics | 0.2231 / 0.2773 / 0.2352 | 0.2452 | 0.2(rho15) ~ 0.4(rho30·45) 사이 |
| dblp | 0.7269 / 0.6750 / 0.7312 | 0.7110 | 0.4(rho45) 초과 — 곡선 범위 밖 |

(v2 생성기는 K와 무관하므로 K=1, 5 값이 같다.)

### 주 비교: diag_rho0 − diag_rho45 (고정 test, seed 0–2 합친 600 에피소드)

| 데이터셋 | K | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | diag_rho0 − diag_rho45 | +2.88 ± 0.32 | 예 | +1.60 / +2.82 / +4.22 |
| Amazon_clothing | 5 | diag_rho0 − diag_rho45 | +1.10 ± 0.18 | 예 | +1.40 / +1.28 / +0.62 |
| Amazon_electronics | 1 | diag_rho0 − diag_rho45 | +1.13 ± 0.27 | 예 | +0.94 / +1.16 / +1.28 |
| Amazon_electronics | 5 | diag_rho0 − diag_rho45 | +0.41 ± 0.19 | 예 | +0.04 / +0.78 / +0.40 |
| dblp | 1 | diag_rho0 − diag_rho45 | +1.67 ± 0.22 | 예 | +2.32 / +1.68 / +1.00 |
| dblp | 5 | diag_rho0 − diag_rho45 | +0.61 ± 0.14 | 예 | +0.60 / +0.72 / +0.52 |

### 보조: diag_rho0_nocollide − diag_rho0

| 데이터셋 | K | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | diag_rho0_nocollide − diag_rho0 | +0.91 ± 0.26 | 예 | +1.60 / +2.48 / -1.34 |
| Amazon_clothing | 5 | diag_rho0_nocollide − diag_rho0 | +0.67 ± 0.17 | 예 | -0.32 / +0.96 / +1.36 |
| Amazon_electronics | 1 | diag_rho0_nocollide − diag_rho0 | -0.49 ± 0.30 | 아니오 | -0.60 / -0.68 / -0.20 |
| Amazon_electronics | 5 | diag_rho0_nocollide − diag_rho0 | +0.74 ± 0.21 | 예 | +0.52 / +0.80 / +0.90 |
| dblp | 1 | diag_rho0_nocollide − diag_rho0 | -0.20 ± 0.21 | 아니오 | -0.96 / +0.08 / +0.28 |
| dblp | 5 | diag_rho0_nocollide − diag_rho0 | +0.01 ± 0.13 | 아니오 | -0.12 / +0.18 / -0.02 |

### 보조: NaQ 점(011 naqfeat 선택 λ)과 곡선

| 데이터셋 | K | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | diag_rho0 − naqfeat_l1.0 | +0.78 ± 0.22 | 예 | +1.14 / +0.68 / +0.52 |
| Amazon_clothing | 5 | diag_rho0 − naqfeat_l1.0 | +0.29 ± 0.17 | 아니오 | +0.76 / +0.38 / -0.26 |
| Amazon_electronics | 1 | diag_rho0 − naqfeat_l1.0 | +1.03 ± 0.27 | 예 | +1.58 / +0.28 / +1.22 |
| Amazon_electronics | 5 | diag_rho0 − naqfeat_l0.5 | +0.18 ± 0.17 | 아니오 | -0.44 / +0.78 / +0.20 |
| dblp | 1 | diag_rho0 − naqfeat_l1.0 | +2.68 ± 0.25 | 예 | +3.26 / +2.00 / +2.78 |
| dblp | 5 | diag_rho0 − naqfeat_l0.5 | +1.12 ± 0.17 | 예 | +1.34 / +1.44 / +0.58 |

| 데이터셋 | K | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | naqfeat_l1.0 − diag_rho45 | +2.10 ± 0.32 | 예 | +0.46 / +2.14 / +3.70 |
| Amazon_clothing | 5 | naqfeat_l1.0 − diag_rho45 | +0.81 ± 0.17 | 예 | +0.64 / +0.90 / +0.88 |
| Amazon_electronics | 1 | naqfeat_l1.0 − diag_rho45 | +0.10 ± 0.28 | 아니오 | -0.64 / +0.88 / +0.06 |
| Amazon_electronics | 5 | naqfeat_l0.5 − diag_rho45 | +0.23 ± 0.19 | 아니오 | +0.48 / -0.00 / +0.20 |
| dblp | 1 | naqfeat_l1.0 − diag_rho45 | -1.01 ± 0.21 | 아니오 | -0.94 / -0.32 / -1.78 |
| dblp | 5 | naqfeat_l0.5 − diag_rho45 | -0.51 ± 0.15 | 아니오 | -0.74 / -0.72 / -0.06 |

- Clothing·Electronics: 자연 오염률 0.24–0.25(목표 0.2와 0.4 사이). Clothing K=1에서 naqfeat 정확도 86.75는 rho15(86.63)와 rho30(84.66) 사이보다 위(rho15보다 높음), Electronics K=1 79.59는 rho15(79.97)와 rho30(79.57) 사이.
- dblp: 자연 오염률 0.71로 곡선 범위(0–0.4) 밖. naqfeat 정확도가 rho45보다 낮다(K=1 −1.01%p, K=5 −0.51%p; 방향을 바꾸면 rho45 − naqfeat가 "분명").

### P09 기계 적용

| 데이터셋 | K | rho0 − rho45 | 사용자 예측 적중 | Claude 예측 적중 | nocollide − rho0 '구분 안 됨' (Claude) |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | +2.88 ± 0.32 (분명) | 아니오 | 아니오 | 아니오 |
| Amazon_clothing | 5 | +1.10 ± 0.18 (분명) | 아니오 | 예 | 아니오 |
| Amazon_electronics | 1 | +1.13 ± 0.27 (분명) | 아니오 | 예 | 예 |
| Amazon_electronics | 5 | +0.41 ± 0.19 (분명) | 예 | 예 | 아니오 |
| dblp | 1 | +1.67 ± 0.22 (분명) | 아니오 | 예 | 예 |
| dblp | 5 | +0.61 ± 0.14 (분명) | 예 | 예 | 예 |

- 사용자 예측 적중 2/6칸, Claude 주 예측 적중 5/6칸, Claude 보조 예측(nocollide − rho0 구분 안 됨) 3/6칸.
- P09 해석 규칙의 기계 적용: Claude 예측 쪽 칸이 더 많으므로 "여지는 있으나 작다 — 순도 개선폭을 NaQ 점 대비 %p로 환산" 문구에 해당한다. 환산(rho0 − naqfeat): Clothing K=1 +0.78 / K=5 +0.29(분명 아님), Electronics K=1 +1.03 / K=5 +0.18(분명 아님), dblp K=1 +2.68 / K=5 +1.12. 단, 이 판정은 칸마다 갈린다(사용자 예측은 Electronics K=5, dblp K=5에서 적중).

### 재현성 관찰

- rho30과 rho45는 목표가 같아 같은 에피소드를 만든다(치환 노드 수 동일). 18쌍 중 11쌍은 ep_acc가 파일 단위로 같고, 7쌍은 고정 test 평균이 최대 0.16%p 다르다. 18쌍 모두 서로 다른 GPU(GPU-A·B 교대 배정)에서 돌았다. [추정] GPU 간 부동소수 비결정성.

## 3. 게이트

013은 게이트 없음(진단).

## 4. 결정 필요

1. 011 구성(support 1개)에서는 비anchor 멤버가 n = 5뿐이라 rho30과 rho45가 같은 점(0.4)이다. 곡선에 서로 다른 점 4개가 필요하면 ρ 격자나 n을 바꿔야 한다.
2. dblp는 자연 오염률(0.71)이 곡선 범위 밖이라 "NaQ 점이 어느 ρ 사이에 놓이는지"가 정의되지 않는다. 범위를 넓힐지(ρ 0.6, 0.8 추가 등).
3. s_X로 R003 정의(log1p 후 코사인)를 썼다. NaQ-Feat 생성기의 유사도(원시 특징 코사인)와 다르다.
4. 같은 설정이 GPU에 따라 소수 에피소드에서 달라진다(위 재현성 관찰). 재실행 변동 평가 방식 검토.

## 5. 참고 리포

013에서 refs는 읽지 않았다. clean 확인은 016에서.
