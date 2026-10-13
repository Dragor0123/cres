# P08 계산량 대조군 sup2 — 사전 등록

- 등록 2026-10-13 (2차 큐, 012 실행 전) · 지시서 `instructions/012_compute_matched_control.md` · 결정 R004 §5

## 실행

- arm `sup2_l<λ>`: 스텝마다 지도 에피소드 2개, L = L_sup(ep1) + λ·L_sup(ep2), λ ∈ {0.5, 1.0}. 두 번째 에피소드는 첫 번째와 같은 방식(전역 random, base 클래스 풀, base 레이블만). 003 백본 `train_step(sup, pseudo, lam)`의 pseudo 자리에 넣는다(`cres/teg/run.py --pseudo sup2`).
- 3 데이터셋 × K{1,5} × seed 0–2 × λ 2 = 36. λ 선택 규칙 동일(seed 평균 고정 valid 최고, 동률이면 작은 λ).

## 비교

- sup2(선택 λ) − sup, 그리고 016에서 +NaQ(선택 λ) − sup2(선택 λ). 고정 test 짝지은 차(seed 0–2 합친 600개), "분명" = 평균 > 0 이고 > 2·SE.

## 사용자 입장 (기록)

"NaQ의 이득이 레이블 없는 노드 덕분"이라는 주장은 +NaQ − sup2가 "분명"일 때만 할 수 있다.

## 예측 (Claude)

- sup2 − sup는 K=1에서 양수이되 +NaQ − sup보다 작다.
- +NaQ-Feat − sup2는 6칸 중 4칸 이상에서 "분명".
