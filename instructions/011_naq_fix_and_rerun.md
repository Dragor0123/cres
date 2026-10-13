# 011 — NaQ 재구현 수정과 재실행

R004 §6. 006의 결과를 대체한다.

## 1. 수정 (`baselines/naq/generator.py`)

1. **에피소드 안 중복 금지.** 한 pseudo-episode 안에서 같은 노드가 두 번 나오지 않는다(way 사이·support/query 사이 모두). 구현: way를 순서대로 채우면서 이미 쓴 노드는 유사도 목록에서 건너뛴다. 목록이 바닥나면 그 anchor를 버리고 새 anchor를 뽑는다(같은 rng). 재추첨 횟수를 기록한다.
2. **K-shot support 구성은 원 NaQ 방식.** 006 보고서에 적힌 "원 NaQ와의 차이" 사실을 근거로 원 방식대로 바꾼다. 원 NaQ가 학습 에피소드를 test K와 무관하게 구성한다면(예: 1-shot support로 학습하고 K=5로 평가) 그대로 따른다. 사실이 불명확하면 refs/NaQ `task_generator.py`를 다시 읽어 확정하고 파일:줄을 보고서에 적는다. 바꾼 구성을 `docs/register/R004` 아래에 부기한다(결정 사항 아님, 사실 기록).
3. 풀 U(base 제외)는 유지. rng 오프셋 `22000+seed` 유지.
4. 유사도 목록 길이를 중복 회피에 충분하게 늘린다(기존 K+Q−1 → 최소 50). 캐시 재생성.

수정 전후 생성기 통계를 세 데이터셋 × K × seed 0에 대해 기록: 에피소드 1000개당 중복 발생률(수정 전), 재추첨 횟수(수정 후), way 사이 실제 클래스 충돌률(레이블은 통계에만 사용, 생성에는 사용 금지).

## 2. 재실행

- {Feat, Diff} × λ{0.5, 1.0} × 3 데이터셋 × K{1,5} × seed 0–2 = 72. 006과 같은 백본·설정.
- λ 선택 규칙 동일(seed 평균 고정 valid 최고, 동률이면 작은 λ). 선택된 λ를 `records/011_naq_v2/lambda_selected.json`에 저장(013이 읽는다).
- 참고용: **전체 노드 풀**(base 포함, 원 NaQ 설정)로 NaQ-Feat, 선택된 λ, 3 데이터셋 × K{1,5} × seed 0–2 = 18. arm 이름 `naqfeat_allpool`.

## 3. 사전 등록 `docs/register/P07_naq_v2.md`

판정 없음. 기록할 것: (a) 중복이 없던 칸(006 보고서의 중복률 0인 데이터셋·생성기)은 K=1에서 006과 에피소드 단위로 같은 결과여야 한다 — 수정 코드의 점검. 다르면 원인을 적는다. (b) 비교 계획: 016에서 +NaQ − sup, +NaQ − sup2(012).

## 4. 산출물

`records/011_naq_v2/ep_acc_*.csv`, `run_meta.jsonl`, `lambda_selected.json`, 생성기 통계 json. `reports/011_naq_v2.md`: 수정 내용(diff 요약), 원 NaQ와의 차이 최종표, (a) 점검 결과, 정확도 표, 006 superseded 명시.
