# 012 계산량을 맞춘 대조군 (sup2)

작성 2026-10-13 (2차 큐) · 등록 P08 (실행 전 커밋 `6ac1039`) · 결정 R004 §5

## 1. 무엇을 했는지

- `cres/teg/run.py --pseudo sup2 --lam λ`: 스텝마다 지도 에피소드 2개, L = L_sup(ep1) + λ·L_sup(ep2). 두 번째 에피소드는 `random.sample(class_list_train, 5)` → `task_generator_in_class`(첫 번째와 같은 함수, 전역 `random`, base 클래스, base 레이블만). 003 백본 `train_step(sup, pseudo, lam)`의 pseudo 자리에 넣었다(코드 경로 공유). epoch 0은 원본대로 갱신 없음이고 두 번째 에피소드도 만들지 않는다(+NaQ와 같은 규칙).
- 실행: `tools/make_jobs_queue2.py 012` → `results/queue2/jobs.jsonl`, `tools/job_runner.py --max_per_gpu 2` (GPU-A·B 교대). 23:02–23:11 UTC, 36/36 완료, 실패·재시도 0. 실행 시간 25–86 s(중앙값 40 s), `max_memory_allocated` 최대 3182 MB.
- 코드: 실행 시점 작업 트리 = 커밋 `acbc922`의 `cres/teg/run.py`·`trainer.py`(run_meta의 `git` 필드는 실행 당시 HEAD `6ac1039`/`6bd4ac1`/`925128b`이며, sup2 경로는 그 사이 바뀌지 않았다). sup 경로 회귀 점검: 리팩터(`finish` 분리) 후 sup Amazon_clothing K=1 seed 0을 다시 돌려 `records/003_teg_port/ep_acc_Amazon_clothing_K1_seed0_sup.csv`와 파일 단위로 같음을 확인.
- 기록: `records/012_sup2/ep_acc_<ds>_K<k>_seed<s>_sup2_l<λ>.csv`, `run_meta.jsonl`. 집계 `tools/aggregate_batch2.py` → `records/016_summary/`.

### 모델 선택에 쓰이는 valid (확인한 사실)

- 체크포인트 선택(R002 §5, TEG-choi 규칙)은 학습 중 에폭마다 `run_epoch("valid", 50)`으로 뽑는 **전역 random valid 에피소드 50개**의 정확도로 한다(`cres/teg/trainer.py` `train`, TEG-choi `model.py:878`과 같음). 고정 valid 100개는 학습 종료 후 평가와 **λ 선택**에만 쓴다.
- sup2는 두 번째 지도 에피소드로 전역 `random`을 더 소비하므로, sup2의 체크포인트 선택용 valid 50개(및 로그용 test 50개)는 sup의 것과 다르다. +NaQ·+CRES는 전용 rng를 쓰므로 sup과 같은 valid 50개를 본다. 고정 valid·test 파일 평가는 영향이 없다(R002). → 지시서 문구("모델 선택은 고정 valid 100개로 한다")와 실제 코드가 다르다. 결정 필요 1.

## 2. 사실

### 고정 test 정확도 (%, seed 0 / 1 / 2, 평균; 출처 `records/012_sup2/`, sup은 `records/003_teg_port/`)

| 데이터셋 | K | arm | seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|
| Amazon_clothing | 1 | sup | 81.46 / 81.16 / 77.66 | 80.09 |
| Amazon_clothing | 1 | sup2_l0.5 (선택) | 82.76 / 83.14 / 80.08 | 81.99 |
| Amazon_clothing | 5 | sup | 91.80 / 90.20 / 90.06 | 90.69 |
| Amazon_clothing | 5 | sup2_l0.5 (선택) | 91.70 / 90.06 / 90.24 | 90.67 |
| Amazon_electronics | 1 | sup | 75.10 / 71.16 / 75.84 | 74.03 |
| Amazon_electronics | 1 | sup2_l0.5 (선택) | 76.64 / 73.86 / 74.08 | 74.86 |
| Amazon_electronics | 5 | sup | 87.76 / 86.74 / 87.74 | 87.41 |
| Amazon_electronics | 5 | sup2_l0.5 (선택) | 87.36 / 86.36 / 88.48 | 87.40 |
| dblp | 1 | sup | 75.38 / 75.14 / 76.68 | 75.73 |
| dblp | 1 | sup2_l1.0 (선택) | 77.14 / 75.12 / 75.76 | 76.01 |
| dblp | 5 | sup | 84.24 / 84.88 / 84.04 | 84.39 |
| dblp | 5 | sup2_l1.0 (선택) | 84.50 / 85.38 / 85.32 | 85.07 |

(선택되지 않은 λ의 test도 `records/012_sup2/`에 있다.)

### λ 선택 (seed 평균 고정 valid, %; 최고, 동률이면 작은 λ)

| 데이터셋 | K | λ 0.5 | λ 1.0 | 선택 |
|---|---|---|---|---|
| Amazon_clothing | 1 | 76.29 | 76.07 | 0.5 |
| Amazon_clothing | 5 | 87.55 | 87.16 | 0.5 |
| Amazon_electronics | 1 | 81.87 | 81.75 | 0.5 |
| Amazon_electronics | 5 | 91.72 | 91.52 | 0.5 |
| dblp | 1 | 75.40 | 76.05 | 1.0 |
| dblp | 5 | 85.15 | 85.43 | 1.0 |

### sup2(선택 λ) − sup, 고정 test 짝지은 차 (%p, seed 0–2 합친 600 에피소드 ± SE)

| 데이터셋 | K | 평균 ± SE | 분명 | seed별 (0 / 1 / 2) |
|---|---|---|---|---|
| Amazon_clothing | 1 | +1.90 ± 0.39 | 예 | +1.30 / +1.98 / +2.42 |
| Amazon_clothing | 5 | −0.02 ± 0.21 | 아니오 | −0.10 / −0.14 / +0.18 |
| Amazon_electronics | 1 | +0.83 ± 0.44 | 아니오 | +1.54 / +2.70 / −1.76 |
| Amazon_electronics | 5 | −0.01 ± 0.25 | 아니오 | −0.40 / −0.38 / +0.74 |
| dblp | 1 | +0.27 ± 0.31 | 아니오 | +1.76 / −0.02 / −0.92 |
| dblp | 5 | +0.68 ± 0.21 | 예 | +0.26 / +0.50 / +1.28 |

+NaQ − sup2 비교와 P08 예측 대조는 016에서(011 결과 사용).

## 3. 게이트

012는 게이트 없음.

## 4. 결정 필요

1. 체크포인트 선택은 고정 valid 100개가 아니라 학습 중 전역 random valid 50개로 한다(TEG-choi 규칙, 003부터 모든 arm 공통). sup2에서는 이 50개가 sup과 달라진다. 현행 유지할지, 체크포인트 선택을 고정 valid 100개로 바꿀지(바꾸면 003 이후 전 arm 재실행) 사용자 결정 필요.

## 5. 참고 리포

012에서 refs는 읽지 않았다. clean 확인은 016에서.
