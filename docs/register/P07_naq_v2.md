# P07 NaQ 재구현 v2 — 사전 등록 (판정 없음)

- 등록 2026-10-13 (2차 큐, 011 실행 전) · 지시서 `instructions/011_naq_fix_and_rerun.md` · 결정 R004 §6

## 실행

- 생성기 `baselines/naq/generator.py` `NaQGenerator`(v2): support = way마다 anchor 1개(원 NaQ, test K와 무관), query = anchor 유사도 목록 상위 Q=5개. 에피소드 안 중복 금지(anchor 예약, way 순서대로 채우며 쓴 노드 건너뜀, 목록 길이 50 바닥 시 anchor 재추첨). 풀 U(base 제외), rng `22000+seed`.
- {Feat, Diff} × λ{0.5, 1.0} × 3 데이터셋 × K{1,5} × seed 0–2 = 72. 003 백본, 006과 같은 설정. λ 선택: seed 평균 고정 valid 최고, 동률이면 작은 λ → `records/011_naq_v2/lambda_selected.json`.
- 참고 arm `naqfeat_allpool`: 전체 노드 풀(base 포함), NaQ-Feat 선택 λ, 3 데이터셋 × K{1,5} × seed 0–2 = 18.

## 기록할 것

(a) 수정 코드 점검: 006에서 중복이 없던 칸(중복률 0인 데이터셋·생성기)은 K=1에서 006과 에피소드 단위로 같은 결과여야 한다. 다르면 원인을 적는다.
(b) 비교 계획(016): +NaQ − sup, +NaQ − sup2(012). "분명" 표기는 CLAUDE.md §5.

판정 기준 없음.
