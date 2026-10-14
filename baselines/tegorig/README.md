# TEG-orig 공식 실행 어댑터 (015, R001)

- 원본: refs/TEG-orig (sung-won-kim/TEG, `b5a8e03`, MIT). 사본 `/workspace/scratch/TEG-orig-run` = `git clone`, `dataset -> /workspace/data/dataset` 심볼릭 링크.
- `cres_adapter.py`(사본 루트에 추가) + `tegorig.diff`(사본의 `argument.py`, `embedder.py`, `main.py`, `model.py`, `utils.py` 변경, 바뀐 줄마다 `# CRES adapter`).
- 변경: (1) 클래스 분할을 `splits/<ds>_class_split.json`으로(원본 `random.sample` 호출은 그대로 실행 후 대조), (2) `CUDA_VISIBLE_DEVICES`가 이미 있으면 덮어쓰지 않음, (3) valid 최고 에폭(동점은 나중) 가중치 복사 후 학습 종료 시 고정 test 200 / valid 100 에피소드 평가, `--out_dir`에 `ep_acc.csv`, `run.json`. 모델·손실·학습 에피소드 생성·옵티마이저는 바꾸지 않았다.
- 실행 예: `cd /workspace/scratch/TEG-orig-run && <python> main.py --dataset Amazon_clothing --way 5 --shot 1 --qry 5 --seed 0 --num_seed 1 --out_dir <dir>`
- 상태(015): 지시서 환경(python 3.8.13 + torch 1.10.1+cu113 + PyG 2.0.3)에서 torch-sparse import 실패로 공식 실행 skip. 보고서 `reports/015_tegorig.md`.
