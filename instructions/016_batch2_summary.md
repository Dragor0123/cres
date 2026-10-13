# 016 — 2차 큐 집계

011–014(와 015가 끝났으면 015)가 끝난 뒤. `tools/aggregate_overnight.py`를 확장하거나 `tools/aggregate_batch2.py`를 새로 쓴다. records/만 읽는다.

## 1. 표

1. **정확도 표** (dataset × K × arm, seed 0/1/2, 평균): sup, sup2(선택 λ), naqfeat(선택 λ), naqdiff(선택 λ), naqfeat_allpool, cres(선택 λ, 2 데이터셋), vision, tegorig(있으면). 011 결과만 사용(006은 superseded).
2. **짝지은 차 표** (seed 0–2 합친 600 에피소드, 평균 ± SE, "분명"):
   - sup2 − sup
   - naqfeat − sup, naqfeat − **sup2**
   - naqdiff − sup, naqdiff − **sup2**
   - naqfeat_allpool − naqfeat
   - cres − sup2, cres − naqfeat (2 데이터셋)
   - sup − vision, sup − tegorig(있으면)
3. **순도 곡선 표** (별도 섹션 "진단, 방법 아님"): dataset × K에 대해 ρ 0/15/30/45 정확도(seed 평균), nocollide, 자연 오염률(NaQ 점)과 naqfeat 정확도, rho0 − rho45 짝지은 차와 판정, 사용자·Claude 예측 중 어느 쪽이 맞았는지(P09 규칙 기계 적용).
4. **생성기 통계**: 011 중복률 수정 전/후, 재추첨, way 충돌률; 014 통계.

## 2. `reports/016_batch2_summary.md`

1. 큐 결과 표(항목, 상태, 소요, 커밋)
2. 위 표 1–4
3. 사전 등록 P07–P10 대비 결과(예측 적중 여부, 기계 적용)
4. 결정 필요 목록(전 항목)
5. 자원·디스크, refs 4개 clean 확인
6. 해석은 `[추정]` 표시로 최대 5줄

## 3. 마무리

`QUEUE_STATE_2.md` 최종 갱신 → 커밋 → push. 채팅으로 요약: 순도 곡선 판정, naq − sup2 판정, cres 위치, 결정 필요 개수.
