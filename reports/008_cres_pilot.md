# 008 CRES pilot — skip

작성 2026-10-13 (야간 큐)

## 1. 무엇을 했는지

실행하지 않았다. `cres/episodes.py`(CRES 생성기)와 `docs/register/P05_cres_pilot.md`도 만들지 않았다.

## 2. 사실 (skip 근거)

- 008 조건: G3 통과, 그리고 G1·G2 모두 통과(지시서 008 첫 줄, 000 §6 "G1 또는 G2 실패 → 008 skip").
- G3: 2차 충족(`reports/003_teg_port_regression.md`).
- **G1: 불통과(0/3 데이터셋)** (`reports/004_gate1_calibrator.md`).
- G2: 통과(2/3, Clothing·Electronics) (`reports/005_gate2_core_purity.md`).
- 실행 대상 데이터셋 규칙(G1과 G2를 둘 다 통과한 데이터셋)으로도 해당 데이터셋이 없다(G1 통과 데이터셋 0개).
- 005의 core 은행(`records/005_gate2/core_bank_*.json`)은 만들어 두었다.

## 3. 게이트

해당 없음(skip).

## 4. 결정 필요

1. G1 불통과 상태에서 CRES pilot을 돌릴지(예: G2만 통과한 Clothing·Electronics에서), 또는 관문 1의 설계를 바꿀지 사용자 판단.

## 5. 참고 리포

해당 없음.
