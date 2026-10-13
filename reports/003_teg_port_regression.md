# 003 TEG 백본 이식, 회귀 검사(G3), 지도 단독 sweep

작성 2026-10-13 (야간 큐) · GPU-A `GPU-16eb803b-…`(index 0), GPU-B `GPU-c7939e10-…`(index 1)

## 1. 무엇을 했는지

커밋: `6ec285f`(이식본·job_runner·P01), `62d11f6`(이식 수정, 아래 G3 1차), 이 보고서 커밋.

### 이식 범위 (출처 refs/TEG-orig `b5a8e03`, MIT; 고정 평가 규칙은 TEG-choi `3b7be89`)

| CRES | 원본 | 비고 |
|---|---|---|
| `cres/teg/layers.py` `GCN`, `EGCL`, `EGNN`, `diff_mean`, `msg_collect` | TEG-orig `layers/GCN.py`, `layers/EGNN.py` | 계산 동일(포맷만 정리) |
| `cres/teg/trainer.py` `seed_everything`, `euclidean_dist`, `accuracy`, `task_generator_in_class` | TEG-orig `utils.py` | `accuracy`는 float 반환 |
| `TEGTrainer.__init__` 데이터 부분 | TEG-orig `utils.py` load_data | `cres.data` 로더 + `splits/*_class_split.json`. 원본의 `random.sample(train_class, valid_num)`은 전역 random 순서 유지를 위해 그대로 한 번 호출하고 분할 파일과 같은지 assert |
| `TEGTrainer.__init__` 구조 특징·모델·optimizer | TEG-orig `embedder.py:35-80`, `model.py:14-25` | 동일(anchor 16, Adam lr 1e-3, wd 5e-4) |
| `episode_outputs`, `episode_loss`, `train_step(sup, pseudo, lam)` | TEG-orig `model.py` train_epoch 본문 | L = L_sup + lam·L_pseudo, lam = 0이면 pseudo 생성·forward 없음. 두 에피소드는 같은 GCN 출력 공유 |
| `run_epoch`, `train` | TEG-orig `model.py` train_epoch / train | 에폭 정확도 = sum/len(원본과 같은 순차 합). 체크포인트: valid == best일 때 저장(동점은 나중 에폭) = TEG-choi `--fixed_eval` |
| `eval_fixed` | TEG-choi `model.py` eval_episode / run_fixed_eval | `splits/episodes/*.json`만 읽음 |
| `cres/teg/run.py` | TEG-choi `main.py` | `torch.set_num_threads(3)` 동일. 출력 `run.json`, `ep_acc.csv`, `records/.../ep_acc_*.csv`, `run_meta.jsonl` |
| `tools/job_runner.py` | — | 000 §4 사양. GPU별 동시 상한, state jsonl, 1회 재시도(`_retry1`), `--stop_after`, 디스크 < 10 GB면 새 작업 안 띄움 |

f1(sklearn)은 계산하지 않는다(난수·계산 경로 영향 없음).

## 2. 사실

### G3 (P01, τ = 1.0%p — TEG-choi CLAUDE.md에 수치 허용치가 없어 지시서 기본값)

명령: `results/003/g3_jobs.jsonl`(1차), `results/003/g3_jobs2.jsonl`(2차) → `tools/job_runner.py`; 판정 `tools/g3_compare.py`. 기록 `records/003_teg_port/g3/`(2차), `records/003_teg_port/g3_attempt1/`(1차).

**1차 (커밋 `6ec285f`의 이식본): G3 불충족.**

| seed | TEG-choi r1 | r2 | 이식본 | 구간 | 해시 | 판정 |
|---|---|---|---|---|---|---|
| 0 | 81.46 | 81.46 | 81.46 | [80.46, 82.46] | 일치 | 충족 |
| 1 | 81.16 | 81.16 | 82.42 | [80.16, 82.16] | 일치 | **불충족** |
| 2 | 77.66 | 77.66 | 77.66 | [76.66, 78.66] | 일치 | 충족 |

- seed 1: 에폭별 train/valid/test 정확도가 TEG-choi `run.json`과 11에폭 모두 같았다. 다른 것은 체크포인트 에폭(TEG-choi 3, 이식본 6) 하나였다.
- epoch 3과 6의 valid 정확도는 모두 0.8096이다. TEG-choi 값은 0.8096000000000002(epoch 3) / 0.8096000000000001(epoch 6)로 epoch 6이 동점이 아니었다. 이식본은 `np.mean`(pairwise 합)으로 계산해 두 값이 같아졌고, 동점 규칙(나중 에폭)으로 epoch 6을 골랐다.
- 수정: 에폭 정확도를 원본처럼 `sum(acc)/len(acc)`로 계산(`62d11f6`). 판정 기준과 τ는 바꾸지 않았다.

**2차 (수정 후): G3 충족.**

| seed | TEG-choi r1 | r2 | 이식본 | 구간 | 해시 | 판정 |
|---|---|---|---|---|---|---|
| 0 | 81.46 | 81.46 | 81.46 | [80.46, 82.46] | 일치 | 충족 |
| 1 | 81.16 | 81.16 | 81.16 | [80.16, 82.16] | 일치 | 충족 |
| 2 | 77.66 | 77.66 | 77.66 | [76.66, 78.66] | 일치 | 충족 |

- 3 seed 모두 고정 test 200 에피소드의 에피소드별 정확도가 TEG-choi r1과 완전히 같았다(`diff` 0줄).
- TEG-choi는 seed마다 2회 실행 결과가 같았다(재실행 변동 0).
- TEG-choi 사본은 `embedder.py:21`이 `CUDA_VISIBLE_DEVICES`를 `str(args.device)`로 덮어써서 job_runner가 준 UUID 대신 CUDA 장치 0번에서 돌았다(기준 실행은 GPU-A 대기열에 넣었음).

### 시간·자원 (2차 이식본, Amazon_clothing K=1, GPU-B 단독 실행)

| 항목 | 값 | 출처 |
|---|---|---|
| 단일 실행 시간 | 15.3 / 16.6 / 15.7 s | `records/003_teg_port/g3/run_meta.jsonl` |
| `torch.cuda.max_memory_allocated` | 1966 MB | 같음 |
| GPU 사용률(1초 간격, 실행 구간 66 표본) | 평균 35.8%, 최대 67% | `results/003/logs/gpu_g3_2.csv` |
| 메모리 사용(nvidia-smi) | 최대 2460 MiB | 같음 |

→ 000 §4 조건(사용률 < 40%, 메모리 < 8 GB) 충족, **GPU당 동시 2개**로 정함.

sweep 실행 시간(GPU당 2개 동시): Clothing 25–42 s, Electronics 33–59 s, dblp 35–43 s. 18개 합 약 7분. 남은 sweep(006 72개, 008, 007)은 GPU 2장 × 2개 기준 1시간 이내로 계산되어 T0+8h 안에 끝나므로 000 §5 축소를 적용하지 않는다.

### 지도 단독 sweep (18/18 완료, 실패·재시도 0)

`records/003_teg_port/ep_acc_<dataset>_K<k>_seed<s>_sup.csv`, `run_meta.jsonl`. 정확도 %, 고정 test 200 에피소드 평균(seed 0 / 1 / 2), 원 보고 방식 `test_acc_at_best_valid`(학습 루프 test 50 에피소드) 병기.

| 데이터셋 | K | 고정 test (s0 / s1 / s2) | 평균 | test_acc_at_best_valid | 평균 | ckpt 에폭 | 시간 s |
|---|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 81.46 / 81.16 / 77.66 | 80.09 | 80.16 / 81.20 / 79.44 | 80.27 | 7/3/2 | 25/25/30 |
| Amazon_electronics | 1 | 75.10 / 71.16 / 75.84 | 74.03 | 72.08 / 73.36 / 74.64 | 73.36 | 9/5/6 | 33/46/46 |
| dblp | 1 | 75.38 / 75.14 / 76.68 | 75.73 | 72.72 / 72.40 / 78.40 | 74.51 | 7/8/10 | 35/36/43 |
| Amazon_clothing | 5 | 91.80 / 90.20 / 90.06 | 90.69 | 91.12 / 91.84 / 90.48 | 91.15 | 7/1/3 | 39/42/42 |
| Amazon_electronics | 5 | 87.76 / 86.74 / 87.74 | 87.41 | 87.76 / 85.76 / 86.16 | 86.56 | 4/9/4 | 59/59/39 |
| dblp | 5 | 84.24 / 84.88 / 84.04 | 84.39 | 85.68 / 83.36 / 84.64 | 84.56 | 10/9/4 | 40/39/39 |

## 3. 게이트

G3: 1차 불충족(seed 1, 원인 위 기재) → 이식 수정 → 2차 충족. 006·008의 G3 조건은 2차 결과로 충족으로 본다. [추정] 1차와 2차의 차이는 동점 판정의 부동소수 합산 순서 하나이며, 1차 결과는 superseded로 `records/003_teg_port/g3_attempt1/`에 남긴다.

## 4. 결정 필요

1. G3를 "1차 불충족 → 버그 수정 → 2차 충족"으로 처리했다. 사전 등록 기준은 바꾸지 않았지만, 재실행으로 통과시킨 것이 등록 취지에 맞는지 사용자 확인 필요.

## 5. 참고 리포

refs는 읽기만 했다(TEG-choi 실행은 `/workspace/scratch/TEG-choi-run` 사본). clean 확인은 009에서.
