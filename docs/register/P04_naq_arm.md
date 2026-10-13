# P04 +NaQ식 arm — 사전 등록 (비교 계획만, 판정 기준 없음)

- 등록 2026-10-13 (야간 큐, 006 실행 전) · 지시서 `instructions/006_naq_arm.md`

## 실행

- 백본: 003 이식본 `train_step(sup, pseudo, lam)`, 스텝마다 지도 에피소드 1개 + pseudo-episode 1개(epoch 0은 원본대로 갱신 없음, pseudo도 만들지 않음).
- 생성기: `baselines/naq/generator.py` (NaQ-Feat, NaQ-Diff 재구현, rng `22000+seed`). 풀 U = base가 아닌 노드, 이웃도 U 안.
- λ ∈ {0.5, 1.0}. {Feat, Diff} × λ × 3 데이터셋 × K{1,5} × seed 0–2 = 72 실행. K=1 먼저.

## λ 선택 (TEG-choi 규칙)

(생성기, 데이터셋, K)마다 seed 0–2 평균 **고정 valid**(100 에피소드) 정확도가 최고인 λ, 동률이면 작은 λ. test는 선택된 λ로만 보고(다른 λ의 test도 records에 저장).

## 비교 계획 (아침 분석, 판정 기준 없음)

+NaQ식(Feat·Diff 각각, 선택된 λ) − 지도 단독(003 sweep)의 고정 test 에피소드 짝지은 차: seed 0–2 600개 에피소드 합쳐서, 그리고 seed별. "분명" 표기 규칙은 CLAUDE.md §5(평균 > 0, > 2·SE)를 따른다.
