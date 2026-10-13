# 006 — +NaQ식 arm (재구현) 과 sweep

조건: G3 통과. GPU 사용. R001에 따라 NaQ 코드는 복사하지 않고 논문과 refs/NaQ를 **읽고** 재구현한다(라이선스 미확인).

## 1. 생성기 — `baselines/naq/generator.py`

- 풀 U = base가 아닌 노드(005와 같음). 레이블은 읽지 않는다.
- 한 pseudo-episode: rng `22000+seed`로 U에서 anchor 5개 무작위 → anchor마다 유사도 상위 (K+Q−1)개 → anchor + 처음 K−1개 = support, 다음 Q개 = query. way 사이 충돌은 막지 않는다(NaQ 원 방식).
  - 이 K-shot 구성(anchor와 상위 이웃을 support로)은 우리 적응이다. NaQ 원 구성과의 차이를 refs/NaQ `task_generator.py`를 읽어 보고서에 사실로 적는다.
- NaQ-Feat: 원시 특징 코사인(NaQ 원문과 같은 전처리; refs를 읽어 확인한 값을 기록).
- NaQ-Diff: 그래프 확산(PPR/GDC) 점수. α·top-k 등은 refs/NaQ 코드에서 읽은 값을 쓰고 출처 줄을 기록.
- 유사도 상위 목록은 데이터셋마다 미리 계산해 캐시.

## 2. 학습

- 003 백본의 `train_step(sup, pseudo, lam)`. 스텝마다 지도 에피소드 1개 + pseudo-episode 1개.
- λ ∈ {0.5, 1.0}. 선택 규칙(TEG-choi와 같음): seed 평균 고정 valid 정확도 최고, 동률이면 작은 λ. test는 선택된 λ로만 보고(나머지 λ의 test도 records에는 저장).
- 실행: {Feat, Diff} × λ{0.5, 1.0} × 3 데이터셋 × K{1, 5} × seed 0–2 = 72. 순서: K=1 전부 → K=5. 000 §5 축소 규칙 적용.

## 3. 먼저 커밋: `docs/register/P04_naq_arm.md`

판정 기준은 없음(측정 arm). 비교 계획만 등록: 아침 분석에서 +NaQ식(Feat·Diff 각각, 선택된 λ) − 지도 단독의 고정 test 에피소드 짝지은 차(seed 0–2의 600개 에피소드 합쳐서, 그리고 seed별).

## 4. 산출물

`records/006_naq/ep_acc_*.csv`, `run_meta.jsonl`, `reports/006_naq_arm.md`(재구현 설명, 원 NaQ와의 차이, 실행 현황, 완료분 표 — 해석 없이).
