# 013 — 순도 곡선 진단: pseudo-episode의 오염률이 정확도를 바꾸는가

R004 §4·§10. **이것은 방법이 아니라 상한을 재는 진단이다.** 에피소드 생성에 valid·test 노드의 실제 레이블을 쓴다. CLAUDE.md §4의 예외로, 아래 격리 규칙을 지킨다.

## 0. 격리 규칙

- 코드는 `cres/diag/purity_curve.py`에만 둔다. 레이블을 읽는 함수에 `# DIAG-ONLY: reads non-base labels` 주석. 다른 모듈에서 import 금지.
- arm 이름 접두어 `diag_`. records 디렉토리 `records/013_purity_diag/`. 016 집계표에서 별도 섹션("진단, 방법 아님").
- 실행 로그 첫 줄에 "DIAG: non-base labels used for episode construction"을 남긴다.

## 1. 출발 에피소드 (A1)

- 011의 수정된 NaQ-Feat 생성기로 pseudo-episode를 만든다(풀 U, rng `22000+seed`, 중복 금지). 각 way = anchor a + 비anchor 멤버 K+Q−1개(원 NaQ 구성대로 support/query 슬롯 배정).
- **오염 정의**: way 안의 비anchor 멤버 중 실제 클래스가 anchor의 클래스와 다른 노드의 비율. 에피소드 오염률 = 5개 way의 평균.
- 자연 오염률(치환 전)을 (dataset, K, seed)마다 1000개 에피소드로 측정해 기록한다. 이것이 "NaQ 점"이다.

## 2. 목표 오염률로 치환

목표 ρ ∈ {0, 0.15, 0.30, 0.45}. way마다 비anchor 멤버 n = K+Q−1개 중 다른 클래스 노드 수를 round(ρ·n)개로 맞춘다(n=5면 0/1/2/2, n=9면 0/1/3/4 — 실제 round 값을 기록).

- **줄여야 할 때**(자연 > 목표): 다른 클래스 멤버 중 **anchor와 s_X가 낮은 것부터** 제거하고, 그 슬롯에 anchor와 같은 클래스이며 아직 에피소드에 없는 노드를 **s_X가 높은 순**으로 넣는다.
- **늘려야 할 때**(자연 < 목표): 같은 클래스 멤버 중 **s_X가 낮은 것부터** 제거하고, 그 슬롯에 anchor와 다른 클래스이며 에피소드에 없는 노드를 **s_X가 높은 순**으로 넣는다(NaQ가 실제로 뽑을 법한 오염).
- 슬롯(support/query 위치)은 유지한다. 오염이 support에 들어간 비율과 query에 들어간 비율을 따로 기록한다.
- 치환 rng 오프셋 `25000+seed`(동률 처리용). CLAUDE.md 오프셋 표에 추가.
- 같은 클래스 노드는 풀 U 안에서 고른다(base 노드 금지).

## 3. B2 점: way 사이 충돌 제거

ρ=0에 더해, anchor 5개의 실제 클래스가 모두 다를 때까지 anchor를 재추첨한 에피소드(`diag_rho0_nocollide`). 최대 50회, 실패 시 마지막 추첨 사용·횟수 기록. way 안 오염도 0.

## 4. 학습·실행

- 003 백본, `L = L_sup + λ·L_pseudo`. λ는 **011에서 NaQ-Feat에 선택된 값**을 (dataset, K)마다 그대로 쓴다(`lambda_selected.json`). λ 탐색 없음.
- 실행: 3 데이터셋 × K{1,5} × seed 0–2 × ρ 4개 = 72, + B2 18 = 90. K=1 먼저.
- 각 실행에서 실제 달성 오염률(에피소드 평균)을 run_meta에 기록(목표와 다르면 그 이유).

## 5. 사전 등록 `docs/register/P09_purity_curve.md`

- 주 지표: ρ별 고정 test 정확도. 주 비교: **diag_rho0 − diag_rho45**의 고정 test 짝지은 차(seed 0–2 합친 600개), "분명" 규칙 적용. 보조: diag_rho0_nocollide − diag_rho0, 그리고 NaQ 점(011 naqfeat 선택 λ)이 곡선의 어느 ρ 사이에 놓이는지.
- **사용자 예측(이희태)**: 순도는 정확도를 크게 바꾸지 않는다 — rho0 − rho45가 "분명"이 아니거나, 분명이어도 1%p 미만.
- **Claude 예측**: 완만한 기울기 — rho0 − rho45가 K=1에서 1–2%p로 "분명", K=5에서는 더 작음. nocollide − rho0는 구분 안 됨.
- 해석 규칙(미리 적음): 사용자 예측이 맞으면 "순도를 높이는 설계(CRES)는 이득의 여지가 작다". Claude 예측이 맞으면 "여지는 있으나 작다 — 순도 개선폭이 NaQ 점 대비 몇 %p인지로 환산". 어느 쪽이든 014 결과와 함께 아침 검토.

## 6. 산출물

`records/013_purity_diag/`(ep_acc, run_meta, 자연 오염률·달성 오염률 표), `reports/013_purity_curve.md`(ρ별 정확도 표, 주 비교, NaQ 점 위치, support/query 오염 비율, 치환 실패 사례).
