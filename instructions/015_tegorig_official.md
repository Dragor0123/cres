# 015 — TEG-orig 공식 실행 (최저 우선순위)

R004 §8. 011–014가 모두 끝나고 016 집계 전에만 시작한다. 007 §2의 내용에 환경 경로만 더한다.

## 1. 환경

```
CONDA=/workspace/miniforge3/bin/conda
$CONDA create -n tegorig python=3.8.13 -y
$CONDA run -n tegorig pip install --no-cache-dir torch==1.10.1+cu113 -f https://download.pytorch.org/whl/torch_stable.html
$CONDA run -n tegorig pip install --no-cache-dir torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-1.10.1+cu113.html
$CONDA run -n tegorig pip install --no-cache-dir torch-geometric==2.0.3 numpy==1.23.4 scipy scikit-learn pyyaml
```

cu113 wheel이 없거나 import에 실패하면 2회 이내 시도 후 "결정 필요"로 기록하고 skip. 실행 파일은 `/venv`가 아니라 `$CONDA info --envs`로 경로 확인 후 절대 경로로.

## 2. 어댑터와 실행

- `/workspace/scratch/TEG-orig-run/`에 사본. 어댑터: 분할 json + 고정 에피소드 json 읽기(R001 정의: 모델·학습 로직 불변). diff를 `baselines/tegorig/`에 커밋.
- 3 데이터셋 × K{1,5} × seed 0–2 = 18. arm `tegorig`.
- 비교 목적: sup(이식본) − tegorig가 에피소드 단위로 어느 정도 같은지. 재실행 변동(G3에서 측정)과 함께 적는다.

## 3. 산출물

`records/015_tegorig/`, `reports/015_tegorig.md`.
