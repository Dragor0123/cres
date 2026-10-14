# 015 TEG-orig 공식 실행 — skip (환경 import 실패)

작성 2026-10-14 (2차 큐) · 결정 R004 §8 · 011–014 종료 후 시작(23:59 UTC)

## 1. 무엇을 했는지

### 환경 (지시서 §1, 로그 `results/queue2/logs/015_conda_create.log`, `015_pip.log`)

| 단계 | 명령 | 결과 |
|---|---|---|
| 1 | `/workspace/miniforge3/bin/conda create -n tegorig python=3.8.13 -y` | 성공, `/venv/tegorig` (conda 26.7.2, `conda info --envs`로 경로 확인) |
| 2 | `conda run -n tegorig pip install --no-cache-dir torch==1.10.1+cu113 -f https://download.pytorch.org/whl/torch_stable.html` | 성공 (torch 1.10.1+cu113) |
| 3 (시도 1) | `conda run -n tegorig pip install --no-cache-dir torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-1.10.1+cu113.html` | **실패**: pip가 휠이 아닌 최신 소스(torch_scatter-2.1.2.tar.gz, torch_sparse-0.6.18.tar.gz)를 골라 빌드 실패("Failed to build installable wheels") |
| 4 | `conda run -n tegorig pip install --no-cache-dir torch-geometric==2.0.3 numpy==1.23.4 scipy scikit-learn pyyaml` | 성공 (torch-geometric 2.0.3, numpy 1.23.4, scipy 1.10.1, scikit-learn 1.3.2, pyyaml 6.0.3) |
| 3 (시도 2) | 같은 인덱스에서 휠이 있는 버전으로 고정: `torch-scatter==2.0.9 torch-sparse==0.6.13` | 설치 성공, **import 실패**: `import torch_geometric` → `torch_sparse/__init__.py:19` `OSError: libcusparse.so.11: cannot open shared object file` |

- 확인한 사실: torch 1.10.1+cu113 휠의 `torch/lib`에는 `libcudart-a7b20f20.so.11.0`만 있고 cusparse는 없다. 시스템에는 `libcusparse.so.12`(`/usr/local/cuda/lib64`)만 있다. 드라이버 570.195.03(CUDA 12.8).
- 지시서 §1 규칙("cu113 wheel이 없거나 import에 실패하면 2회 이내 시도 후 결정 필요로 기록하고 skip")에 따라 **2회 시도 후 skip**. 3번째 시도(예: CUDA 11 cusparse 런타임 추가 설치, LD_LIBRARY_PATH)는 하지 않았다.
- 만든 환경 `/venv/tegorig`(4.1 GB)는 지우지 않고 남겼다(삭제는 사용자 지시 시에만).

### 어댑터 (준비 완료, 공식 실행은 안 함)

- 사본 `/workspace/scratch/TEG-orig-run`(`git clone /workspace/refs/TEG-orig`, `b5a8e03`), `dataset` → `/workspace/data/dataset` 심볼릭 링크.
- `baselines/tegorig/cres_adapter.py`, `baselines/tegorig/tegorig.diff`(5개 파일 37줄 추가 수준, 바뀐 줄마다 `# CRES adapter`), `baselines/tegorig/README.md`. 변경 내용: 분할 json 읽기(원본 `random.sample`은 그대로 실행 후 대조), 고정 에피소드 평가(valid 최고 에폭, 동점은 나중 에폭의 가중치), `CUDA_VISIBLE_DEVICES` 덮어쓰기 방지(원본 `embedder.py`는 `--device` 값으로 덮어써 job_runner의 UUID 지정을 무시함). 모델·학습 로직 불변(R001).
- 어댑터 동작 점검(공식 실행 아님): cres 환경(python 3.10, torch 2.4.1)에서 Amazon_clothing K=1 seed 0, `--epochs 1`로 실행 → 분할 대조 4항목 모두 일치(`valid_order_equal`, `train_order_equal`, `test_order_equal`, `sets_equal` = true), 고정 test 200·valid 100 평가와 출력 파일 생성 확인(값은 1에폭 점검이라 보고하지 않음).

## 2. 사실

- tegorig arm 실행 0/18. `records/015_tegorig/` 없음. 016 집계의 sup − tegorig는 "미완료".
- 참고(재게시): TEG-orig의 모델·데이터·학습 함수는 TEG-choi 기본 경로와 AST가 같고(001 §3-5), 003 이식본은 TEG-choi와 고정 test 에피소드별 정확도가 완전히 같았다(G3 2차). 재실행 변동: 013에서 같은 설정이 GPU-A·B에서 돌면 18쌍 중 7쌍이 고정 test 평균 최대 0.16%p 달랐다.

## 3. 게이트

015는 게이트 없음.

## 4. 결정 필요

1. TEG-orig 공식 환경: torch-sparse 0.6.13(cu113)이 `libcusparse.so.11`을 찾지 못한다. 선택지 예: (a) CUDA 11.3 cusparse 런타임을 conda로 추가(`cudatoolkit=11.3`) 후 재시도, (b) cres 환경(torch 2.4)에서 어댑터로 실행, (c) 현행 skip 유지. 설치 범위 확장이 필요하므로 사용자 결정.
2. 시도 2에서 PyG 확장 버전을 휠이 있는 버전으로 고정했다(지시서 명령에는 버전 없음).

## 5. 참고 리포

refs/TEG-orig는 읽기와 `git clone`만 했다. clean 확인은 016에서.
