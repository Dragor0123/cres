# P09 순도 곡선 진단 — 사전 등록

- 등록 2026-10-13 (2차 큐, 013 실행 전) · 지시서 `instructions/013_purity_curve.md` · 결정 R004 §4·§10
- **진단, 방법 아님.** 에피소드 구성에 valid·test 노드의 실제 레이블을 쓴다(격리: `cres/diag/purity_curve.py`, arm `diag_*`, `records/013_purity_diag/`).

## 실행

- 출발 에피소드(A1): 011 NaQ-Feat v2(풀 U, rng `22000+seed`, 중복 금지). 011 구성상 way = anchor(support 1개) + query Q=5개 → 비anchor 멤버 n = 5(K=1, 5 모두).
- 목표 오염률 ρ ∈ {0, 0.15, 0.30, 0.45}: way마다 다른 클래스 멤버 수 round(ρ·5) = 0 / 1 / 2 / 2 (Python round). 치환 규칙 013 §2, 유사도 s_X(R003), 동률 rng `25000+seed`.
- B2: `diag_rho0_nocollide` (anchor 5개 실제 클래스가 모두 다를 때까지 재추첨, 최대 50회) + way 안 오염 0.
- λ = 011 NaQ-Feat 선택값(`records/011_naq_v2/lambda_selected.json`), 탐색 없음. 3 데이터셋 × K{1,5} × seed 0–2 × (ρ 4 + B2 1) = 90.

## 비교

- 주 지표: ρ별 고정 test 정확도.
- 주 비교: **diag_rho0 − diag_rho45**, 고정 test 짝지은 차(seed 0–2 합친 600개), "분명" = 평균 > 0 이고 > 2·SE.
- 보조: diag_rho0_nocollide − diag_rho0; NaQ 점(011 naqfeat 선택 λ)이 곡선의 어느 ρ 사이에 놓이는지(자연 오염률과 정확도).

## 예측

- **사용자 예측(이희태)**: 순도는 정확도를 크게 바꾸지 않는다 — rho0 − rho45가 "분명"이 아니거나, 분명이어도 1%p 미만.
- **Claude 예측**: 완만한 기울기 — rho0 − rho45가 K=1에서 1–2%p로 "분명", K=5에서는 더 작음. nocollide − rho0는 구분 안 됨.

## 해석 규칙 (미리 적음)

사용자 예측이 맞으면 "순도를 높이는 설계(CRES)는 이득의 여지가 작다". Claude 예측이 맞으면 "여지는 있으나 작다 — 순도 개선폭이 NaQ 점 대비 몇 %p인지로 환산". 어느 쪽이든 014 결과와 함께 아침 검토.

## 기계 적용 방법 (016)

(dataset, K) 6칸마다 rho0 − rho45를 판정한다. 사용자 예측 적중 칸 = "분명 아님" 또는 "분명이고 평균 < 1%p". Claude 예측 적중 칸 = K=1에서 "분명이고 1 ≤ 평균 ≤ 2%p", K=5에서 해당 데이터셋 K=1 평균보다 작음(그리고 nocollide − rho0 "분명 아님"은 별도 집계).
