# 014 — CRES pilot (탐색용, 판정 없음)

R004 §4. G1 불통과 상태이므로 **방법 검증이 아니라 탐색**이다. 결과로 설계를 확정하지 않는다. 008 지시서의 생성기·학습 규칙을 그대로 쓰되 아래만 다르다.

## 1. 범위

- 데이터셋: Amazon_clothing, Amazon_electronics(G2 통과). dblp는 제외.
- core 은행: 005의 `records/005_gate2/core_bank_*`(m = K+Q, 선택 τ_in). 은행이 results/에만 있으면 그 경로.
- λ ∈ {0.5, 1.0}, 선택 규칙 동일. 2 데이터셋 × K{1,5} × seed 0–2 × λ 2 = 24.
- 생성기 통계(재추첨 횟수, query 제외 비율, way 충돌률 — 레이블은 통계에만)를 기록.

## 2. 사전 등록 `docs/register/P10_cres_pilot_exploratory.md`

- "탐색용, 판정 없음, 방법 확정에 쓰지 않음"을 첫 줄에.
- 기록할 비교(016): +CRES − sup, +CRES − sup2, +CRES − +NaQ-Feat(011 선택 λ). 방향 예측은 적지 않는다.

## 3. 산출물

`records/014_cres_pilot/`, `reports/014_cres_pilot.md`(표, 생성기 통계, 008 대비 바뀐 점 없음 확인).
