# 014 CRES pilot — 탐색용, 판정 없음

작성 2026-10-13 (2차 큐) · 등록 P10 (실행 전 커밋 `925128b`) · 결정 R004 §4 · 지시서 008 §1–2의 생성기·학습 규칙

**탐색용이다. G1 불통과 상태이며 결과로 설계를 확정하지 않는다.**

## 1. 무엇을 했는지

- 생성기 `cres/episodes.py` `CRESGenerator`(커밋 `925128b`, 레이블 미사용, rng `23000+seed`). 008 §1 그대로:
  1. core 5개 추첨, 조건 max_(i≠j) r(a_i, a_j) ≤ 0.3(양방향 모두 확인). 최대 50회, 실패 시 마지막 추첨 사용·기록.
  2. support: core 안에서 다른 멤버와의 평균 r(u, ·)이 가장 큰 K개(동률은 core 안 순서 앞쪽).
  3. query: 나머지 Q=5개. 어떤 query q에서 max_(다른 way) r(a', q) > r(a, q)이면 그 core 재추첨(새 core도 1의 조건, 최대 50회; 에피소드당 재추첨 최대 50회). r 방향은 005 core 구성과 같이 anchor가 첫 번째.
  4. "support와 다른 변이 포함" 조건은 구현하지 않았다(008 §1-4).
- 입력: core 은행 `records/005_gate2/core_bank_<ds>_seed<s>_m<K+Q>.json`(m = 6 / 10, τ_in 0.7), r = C1(ψ)(`results/004/<ds>/c1_seed<s>.pt`, `cres/core.py` `RScorer`).
- 학습: 003 백본 `train_step(sup, pseudo, lam)`, λ ∈ {0.5, 1.0}. Amazon_clothing, Amazon_electronics × K{1,5} × seed 0–2 × λ 2 = 24.
- 실행: job_runner(`results/queue2/`) 23:29–23:56 UTC, 24/24, 실패·재시도 0. 처음 4개는 대기열 재정렬 전에 013보다 먼저 시작했고 나머지 20개는 013 뒤에 돌았다. 실행 시간 중앙값 54 s(최대 65 s), `max_memory_allocated` 최대 6167 MB.
- 생성기 통계: `tools/cres_gen_stats.py`(새 생성기 인스턴스, 같은 rng, (데이터셋, K, seed)마다 500 에피소드; 레이블은 통계에만) → `records/014_cres_pilot/generator_stats.json`.
- **008 대비 바뀐 점 없음**: 생성기 규칙·학습 규칙·λ 격자·선택 규칙은 008 지시서 그대로다. 다른 점은 실행 범위뿐이다(G1·G2 모두 통과한 데이터셋 대신 G2 통과 2개, 탐색용).

## 2. 사실

### 고정 test 정확도 (%, 출처 `records/014_cres_pilot/`)

| 데이터셋 | K | arm | seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|
| Amazon_clothing | 1 | cres_l0.5 (선택) | 81.10 / 78.92 / 80.46 | 80.16 |
| Amazon_clothing | 1 | cres_l1.0 | 80.98 / 79.02 / 80.40 | 80.13 |
| Amazon_electronics | 1 | cres_l0.5 | 79.98 / 75.08 / 81.12 | 78.73 |
| Amazon_electronics | 1 | cres_l1.0 (선택) | 80.44 / 76.56 / 82.22 | 79.74 |
| Amazon_clothing | 5 | cres_l0.5 | 93.70 / 91.08 / 91.68 | 92.15 |
| Amazon_clothing | 5 | cres_l1.0 (선택) | 93.32 / 90.68 / 91.82 | 91.94 |
| Amazon_electronics | 5 | cres_l0.5 | 89.24 / 89.74 / 90.54 | 89.84 |
| Amazon_electronics | 5 | cres_l1.0 (선택) | 89.18 / 90.02 / 90.82 | 90.01 |

### λ 선택 (seed 평균 고정 valid, %)

| 데이터셋 | K | λ 0.5 | λ 1.0 | 선택 |
|---|---|---|---|---|
| Amazon_clothing | 1 | 79.40 | 79.28 | 0.5 |
| Amazon_clothing | 5 | 89.47 | 89.60 | 1.0 |
| Amazon_electronics | 1 | 85.75 | 86.87 | 1.0 |
| Amazon_electronics | 5 | 93.41 | 93.47 | 1.0 |

### 짝지은 차 (선택 λ, seed 0–2 합친 600 에피소드; 016 기록용 비교, P10 판정 없음)

| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE (%p) | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | cres − sup | cres_l0.5 − sup | +0.07 ± 0.35 | 아니오 | -0.36 / -2.24 / +2.80 |
| Amazon_clothing | 1 | cres − sup2 | cres_l0.5 − sup2_l0.5 | -1.83 ± 0.42 | 아니오 | -1.66 / -4.22 / +0.38 |
| Amazon_clothing | 1 | cres − naqfeat | cres_l0.5 − naqfeat_l1.0 | -6.59 ± 0.39 | 아니오 | -4.74 / -7.66 / -7.36 |
| Amazon_clothing | 5 | cres − sup | cres_l1.0 − sup | +1.25 ± 0.19 | 예 | +1.52 / +0.48 / +1.76 |
| Amazon_clothing | 5 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +1.27 ± 0.21 | 예 | +1.62 / +0.62 / +1.58 |
| Amazon_clothing | 5 | cres − naqfeat | cres_l1.0 − naqfeat_l1.0 | -0.54 ± 0.20 | 아니오 | +0.56 / -1.20 / -0.98 |
| Amazon_electronics | 1 | cres − sup | cres_l1.0 − sup | +5.71 ± 0.36 | 예 | +5.34 / +5.40 / +6.38 |
| Amazon_electronics | 1 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +4.88 ± 0.42 | 예 | +3.80 / +2.70 / +8.14 |
| Amazon_electronics | 1 | cres − naqfeat | cres_l1.0 − naqfeat_l1.0 | +0.15 ± 0.34 | 아니오 | +0.40 / -0.98 / +1.02 |
| Amazon_electronics | 5 | cres − sup | cres_l1.0 − sup | +2.59 ± 0.24 | 예 | +1.42 / +3.28 / +3.08 |
| Amazon_electronics | 5 | cres − sup2 | cres_l1.0 − sup2_l0.5 | +2.61 ± 0.25 | 예 | +1.82 / +3.66 / +2.34 |
| Amazon_electronics | 5 | cres − naqfeat | cres_l1.0 − naqfeat_l0.5 | +0.58 ± 0.23 | 예 | -0.82 / +1.62 / +0.94 |

("분명" = 평균 > 0 이고 > 2·SE. Clothing K=1의 cres − naqfeat −6.59 ± 0.39는 방향을 바꾸면 naqfeat가 "분명"히 높다.)

### 생성기 통계 (500 에피소드)

| 데이터셋 | K | seed | core 수 (τ_in) | anchor 추첨 횟수/에피소드 | anchor 조건 실패 | query 조건 재추첨 에피소드 비율 | 중복 노드 에피소드 | way 사이 실제 클래스 충돌률 | way 안 오염률 |
|---|---|---|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 0 | 9703 (0.7) | 1.774 | 0 | 0.000 | 0 | 0.158 | 0.1206 |
| Amazon_clothing | 1 | 1 | 9375 (0.7) | 1.848 | 0 | 0.000 | 0 | 0.136 | 0.1226 |
| Amazon_clothing | 1 | 2 | 9460 (0.7) | 1.628 | 0 | 0.000 | 0 | 0.156 | 0.1250 |
| Amazon_clothing | 5 | 0 | 8168 (0.7) | 1.800 | 0 | 0.000 | 0 | 0.128 | 0.1361 |
| Amazon_clothing | 5 | 1 | 7591 (0.7) | 1.826 | 0 | 0.000 | 0 | 0.126 | 0.1081 |
| Amazon_clothing | 5 | 2 | 7785 (0.7) | 1.676 | 0 | 0.000 | 0 | 0.104 | 0.1266 |
| Amazon_electronics | 1 | 0 | 15742 (0.7) | 1.484 | 0 | 0.000 | 0 | 0.028 | 0.1382 |
| Amazon_electronics | 1 | 1 | 13990 (0.7) | 1.664 | 0 | 0.000 | 0 | 0.032 | 0.1676 |
| Amazon_electronics | 1 | 2 | 12853 (0.7) | 1.522 | 0 | 0.000 | 0 | 0.068 | 0.1309 |
| Amazon_electronics | 5 | 0 | 13462 (0.7) | 1.534 | 0 | 0.000 | 0 | 0.024 | 0.1382 |
| Amazon_electronics | 5 | 1 | 11422 (0.7) | 1.690 | 0 | 0.000 | 0 | 0.054 | 0.1681 |
| Amazon_electronics | 5 | 2 | 10764 (0.7) | 1.528 | 0 | 0.000 | 0 | 0.060 | 0.1448 |

- 학습 실행 24개 합계: anchor 조건 실패 0, query 조건 재추첨 0, 중복 노드 에피소드 0, anchor 추첨 평균 1.66회/에피소드.
- query 조건(3)은 한 번도 발동하지 않았다.
- 참고(011·013): NaQ-Feat v2의 way 안 오염률(자연 오염률)은 Clothing 0.248, Electronics 0.245, way 사이 충돌률 0.344 / 0.179(seed 0).

## 3. 게이트

014는 게이트 없음(P10: 탐색용, 판정 없음).

## 4. 결정 필요

1. query 조건(008 §1-3)이 학습·통계 모든 에피소드에서 발동하지 않았다. 조건을 유지할지.
2. 이 결과를 설계 검토 자료로만 쓴다(P10). 다음 단계 방향은 013 결과와 함께 사용자 검토.

## 5. 참고 리포

014에서 refs는 읽지 않았다. clean 확인은 016에서.
