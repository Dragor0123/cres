# 007 공식 베이스라인 어댑터: VISION (실행), TEG-orig (skip)

작성 2026-10-13 (야간 큐) · R001 어댑터 정의

## 1. 무엇을 했는지

### VISION

- 사본: `/workspace/scratch/VISION-run` = `git clone /workspace/refs/VISION`(`0524eae`, MIT). (`cp -r`은 권한 규칙에 막혀 `git clone`으로 만들었다.)
- 환경: 지시서 1순위 `conda create -n vision --clone cres`는 **conda 실행 파일이 없어** 쓰지 못했다(`which conda mamba` 결과 없음; `/venv/cres`는 conda-meta가 있는 conda 형식 디렉터리). 대신 `/venv/cres/bin/python -m venv --system-site-packages /venv/vision` 후 `pip install ogb`(README 패키지). 결과: ogb 1.3.6, torch 2.4.1+cu124, torch_geometric 2.8.1, scikit-learn 1.7.2(cres 공유). 추가로 설치된 의존 패키지: pandas 2.3.3, outdated 0.2.2 등(ogb 의존).
- 어댑터: `baselines/vision/cres_adapter.py`(추가 파일), `baselines/vision/main.py.diff`(사본 `main.py` 변경, 24줄 추가·14줄 삭제, 바뀐 줄마다 `# CRES adapter`).
- 실행: `cd /workspace/scratch/VISION-run && /venv/vision/bin/python main.py --dataset <ds> --n_way 5 --k_shot <K> --seed <s> --cres_seed <s> --out_dir <dir>` (job_runner, 006 뒤 대기열). 기록 `records/007_vision/ep_acc_<ds>_K<k>_seed<s>_vision.csv`(test 200), `run_meta.jsonl`.

### TEG-orig: skip

- 지시서 환경: python 3.8.13, torch 1.10.1 cu113, torch-geometric 2.0.3.
- conda 실행 파일이 없어 python 3.8 인터프리터를 만들 수 없고, torch 1.10.1은 python 3.10용 wheel이 없다(1.11부터 3.10 지원). 000 §9 설치 허용 범위 안에서 환경을 만들 방법이 없어 skip.
- 참고 사실: TEG-orig의 모델·데이터·학습 함수는 TEG-choi 기본 경로와 AST가 같고(001 §3-5), 003 이식본은 TEG-choi와 고정 test 에피소드별 정확도가 완전히 같았다(G3 2차, Clothing K=1 seed 0–2).

## 2. 사실

### VISION 코드 사실 (refs/VISION `0524eae`를 읽고 확인)

| 항목 | 사실 | 위치 |
|---|---|---|
| 학습 레이블 사용 | 학습 에피소드는 `unsupervised_task_generator(all_nodes_idx, …)`로 만든다. 무작위 anchor N개와 `pool_size`(4096) 무작위 후보 중 적응형 특징(`precompute_adaptive_task_features`: 원시 특징과 Â X의 게이트 결합) 유사도 상위 K+Q개. 레이블을 쓰지 않는다. 노드 풀은 전체 노드(test 클래스 노드 포함) | `main.py:194`, `data_split.py:146-208` |
| 레이블을 쓰는 곳 | dev 선택(`test(model, dev_class, …)`, 20에폭마다, 100 에피소드)과 최종 test | `main.py:234-243, 251` |
| `train_class` | `split()`이 반환하지만 학습에 쓰이지 않음(`train_idx`도 미사용) | `main.py:123` |
| 모델 선택 | dev 정확도 최고 시 `best_model_ligt_v5.pth` 저장(작업 디렉터리), `stop_cnt > patience`이면 중단, 최대 `epochs` 10000 | `main.py:234-249` |
| 실행 반복 | 한 번 실행에 5회(`for run in range(5)`) 학습·평가 | `main.py:256` |
| 지원 데이터셋 | Cora, CiteSeer, Amazon-Computer, Coauthor-CS, CoraFull, Reddit, ogbn-arxiv, dblp, Cora_ML. **Amazon_clothing·Amazon_electronics 없음** | `data_split.py:71-91` |
| dblp 처리 | `./few_shot_data/dblp_network`에서 n1 > n2인 엣지만 남김(인접 목록에서 양방향화). 클래스 분할은 137개 클래스를 `random.shuffle` 후 77/30/30 | `data_split.py:35-69, 13-23, 100` |
| 하이퍼파라미터 | `get_dataset_hyperparams`: dblp·Amazon 항목 없음 → default(patience 20, dropout 0.1). 그 외 argparse 기본값(lr 2e-4, hidden 256, nhead 4, nlayers 2, max_neighbors 30, drop_label 0.2, input_noise 0.02, drop_edge 0.2, con_weight 0.5, pool_size 4096, m_qry 10) | `utils.py:29-59`, `main.py:13-34` |
| m_qry와 모델 | `LabelInjectedTransformer`는 `m_qry`를 계산에 쓰지 않는다(n_way, k_shot만 사용) | `models.py:8-104` |

### 어댑터 변경 (사본 `main.py`, 전체 diff는 `baselines/vision/main.py.diff`)

1. 인자 추가: `--cres_seed`(분할·에피소드 seed), `--out_dir`.
2. `split(args.dataset)` → `cres_adapter.split_from_files(args.dataset, args.cres_seed)`: `.mat` + edge list를 `load_DBLP`와 같은 식(n1 > n2 엣지)으로 읽고, 클래스 분할을 `splits/<ds>_class_split.json`에서 읽음(train = base, dev = valid, test = test). 인접 목록 구성은 `split()`과 같은 코드.
3. 장치 이동 분기: `args.dataset == 'dblp'` → dblp·Amazon 두 데이터셋(같은 객체 형식이라 `.to()`가 없음).
4. `test()`: `test_task_generator` 무작위 추출 대신 `splits/episodes/<ds>_seed<s>_K<k>.json`(dev = valid 100, test = test 200). 평가 레이블은 파일의 Q(5)로 `repeat_interleave`.
5. 체크포인트 경로를 `out_dir` 아래로(동시 실행 충돌 방지).
6. 실행 반복 5회 → 1회(프로세스당 (데이터셋, K, seed) 하나).
7. 에피소드별 test 정확도 `ep_acc.csv`, `run.json` 저장.

모델·손실·학습 에피소드 생성·옵티마이저·조기 종료 규칙은 바꾸지 않았다. 학습 m_qry는 기본값 10, VISION 자체 seed(`--seed`)는 0/1/2(= `--cres_seed`)로 주었다(기본 1234).

## 3. 실행 결과 (VISION, 18/18 완료, 실패·재시도 0)

job_runner 15:50–16:15 UTC(GPU당 2개 동시, 006 이후). 출처 `records/007_vision/run_meta.jsonl`, `ep_acc_*_vision.csv`.

| 데이터셋 | K | seed | 고정 test % | best dev(고정 valid) % | best epoch | 시간 s |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | 0 | 84.08 | 81.88 | 1800 | 291 |
| Amazon_clothing | 1 | 1 | 82.78 | 77.96 | 700 | 100 |
| Amazon_clothing | 1 | 2 | 82.72 | 81.04 | 800 | 122 |
| Amazon_electronics | 1 | 0 | 76.66 | 88.48 | 1880 | 331 |
| Amazon_electronics | 1 | 1 | 77.06 | 82.52 | 2920 | 678 |
| Amazon_electronics | 1 | 2 | 78.68 | 88.00 | 2720 | 645 |
| dblp | 1 | 0 | 72.46 | 74.68 | 1060 | 384 |
| dblp | 1 | 1 | 70.16 | 73.40 | 720 | 290 |
| dblp | 1 | 2 | 72.20 | 69.76 | 1080 | 232 |
| Amazon_clothing | 5 | 0 | 90.48 | 89.16 | 780 | 163 |
| Amazon_clothing | 5 | 1 | 89.82 | 88.88 | 1100 | 198 |
| Amazon_clothing | 5 | 2 | 89.82 | 89.44 | 1500 | 223 |
| Amazon_electronics | 5 | 0 | 85.60 | 91.52 | 600 | 175 |
| Amazon_electronics | 5 | 1 | 86.66 | 89.72 | 1000 | 191 |
| Amazon_electronics | 5 | 2 | 88.60 | 93.28 | 2120 | 499 |
| dblp | 5 | 0 | 80.92 | 82.84 | 1320 | 438 |
| dblp | 5 | 1 | 81.38 | 84.68 | 1460 | 392 |
| dblp | 5 | 2 | 79.84 | 76.64 | 780 | 348 |

### 지도 단독(003 이식본) − VISION, 고정 test 짝지은 차 (%p, 600 에피소드 ± SE; seed별)

| 데이터셋 | K | 평균 ± SE | 분명(평균 > 0, > 2·SE) | seed 0 / 1 / 2 |
|---|---|---|---|---|
| Amazon_clothing | 1 | −3.10 ± 0.45 | 아니오 | −2.62 / −1.62 / −5.06 |
| Amazon_clothing | 5 | +0.65 ± 0.27 | 예 | +1.32 / +0.38 / +0.24 |
| Amazon_electronics | 1 | −3.43 ± 0.49 | 아니오 | −1.56 / −5.90 / −2.84 |
| Amazon_electronics | 5 | +0.46 ± 0.33 | 아니오 | +2.16 / +0.08 / −0.86 |
| dblp | 1 | +4.13 ± 0.45 | 예 | +2.92 / +4.98 / +4.48 |
| dblp | 5 | +3.67 ± 0.35 | 예 | +3.32 / +3.50 / +4.20 |

음수 행은 방향을 바꾸면(VISION − 지도) 평균 > 0 이고 > 2·SE다(Clothing K=1 +3.10 ± 0.45, Electronics K=1 +3.43 ± 0.49).

## 4. 게이트

007은 게이트 없음.

## 5. 결정 필요

1. TEG-orig 공식 실행: conda 없이 python 3.8 + torch 1.10.1(cu113) 환경을 만들 방법이 없어 skip. conda(또는 miniforge) 설치 허용 여부, 또는 cres 환경에서 TEG-orig를 돌릴지 결정 필요.
2. VISION 환경을 conda clone 대신 `/venv/cres` 기반 venv + ogb로 만들었다(지시서 1순위와 다름).
3. VISION은 학습에 레이블을 쓰지 않고 전체 노드(test 클래스 노드 포함)에서 pseudo-task를 만든다(원 코드 그대로). 지도 단독·+NaQ식은 base 레이블을 쓰고 pseudo 풀은 base 외 노드다. 비교 조건 차이에 대한 사용자 판단 필요.
4. VISION 모델 선택은 고정 valid 100 에피소드(어댑터)로 20에폭마다, 학습 m_qry 10(기본값), VISION 자체 seed = 0/1/2(기본 1234)로 실행했다.

## 6. 참고 리포

refs/VISION은 읽기만 했다(실행은 `git clone` 사본). clean 확인은 009에서.

