# P02 관문 1: calibrator (G1) — 사전 등록

- 등록 2026-10-13 (야간 큐, 004 실행 전) · 지시서 `instructions/004_gate1_calibrator.md` §4 · 설계값 R003

## 지표 (test–test 후보 쌍에서)

- 주 지표: **anchor top-10 순도**. test 노드 u마다(test–test 후보가 10개 이상인 것만) 점수 상위 10개 중 u와 같은 클래스 비율. 방법 간 차는 anchor별로 짝지어 계산.
- 보조: 쌍 단위 AUROC, AP; ECE(정보용, 판정에 쓰지 않음 — test 양성 비율이 base와 다름); 제외된 anchor 수.
- 비교 대상: s_X 단독, s_H 단독, c 단독, avg = (s_X + s_H + c)/3, C1, C2.
- 정합성 확인(판정 아님): s_H top-10 순도를 사용자 기존 수치(학습 없는 Â²X top-10 순도 Clothing 0.846, Electronics 0.682, dblp 0.584)와 나란히 적는다. 정의 차이: 여기서 후보 범위는 test–test 후보 쌍으로 제한되고, X'에 log1p를 적용한다.

## 판정

- **G1 데이터셋 통과**: seed 0, 1, 2 **모두**에서 [C1 순도 − max(s_X, s_H, avg 순도)]의 anchor 짝지은 차가 평균 > 0 이고 평균 > 2·SE. max는 test에서 순도 평균이 가장 높은 비교 대상(보수적 기준).
- **G1 통과**: 3개 데이터셋 중 2개 이상 통과. dblp 결과는 통과 여부와 무관하게 따로 적는다.

## 한계

- 한 노드가 여러 anchor의 이웃으로 겹치므로 anchor들은 독립이 아니며 SE가 작게 나올 수 있다.

## 예측 (Claude, 근거 약함)

G1 통과. 다만 dblp에서 차이가 가장 작을 것.
