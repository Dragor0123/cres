# P10 CRES pilot — 탐색용, 판정 없음, 방법 확정에 쓰지 않음

- 등록 2026-10-13 (2차 큐, 014 실행 전) · 지시서 `instructions/014_cres_pilot_exploratory.md`(008 생성기·학습 규칙) · 결정 R004 §4
- G1 불통과 상태의 탐색 실행이다. 결과로 설계를 확정하지 않는다.

## 실행

- 생성기 `cres/episodes.py` (008 §1 그대로, rng `23000+seed`). core 은행 `records/005_gate2/core_bank_<ds>_seed<s>_m<K+Q>.json`(선택 τ_in), r = C1(ψ).
- 데이터셋: Amazon_clothing, Amazon_electronics (G2 통과). dblp 제외.
- λ ∈ {0.5, 1.0}, 선택 규칙 동일(seed 평균 고정 valid 최고, 동률이면 작은 λ). 2 × K{1,5} × seed 0–2 × λ 2 = 24.
- 생성기 통계(anchor 재추첨, query 조건 재추첨, way 충돌률 — 레이블은 통계에만) 기록.

## 기록할 비교 (016)

+CRES − sup, +CRES − sup2, +CRES − +NaQ-Feat(011 선택 λ). 고정 test 짝지은 차(seed 0–2 합친 600개). 방향 예측은 적지 않는다.
