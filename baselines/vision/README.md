# VISION 어댑터 (007, R001)

- 원본: refs/VISION `0524eae` (MIT). 실행 사본: `/workspace/scratch/VISION-run` (`git clone /workspace/refs/VISION`).
- `cres_adapter.py`: 사본에 추가한 파일(데이터 로딩·분할·고정 에피소드 읽기). 출처 주석 포함.
- `main.py.diff`: 사본 `main.py`의 변경(`git diff`). 바뀐 줄에는 `# CRES adapter` 주석.
- 환경: `/venv/vision` = `/venv/cres` 파이썬으로 만든 `--system-site-packages` venv + `pip install ogb`(1.3.6). conda 실행 파일이 없어 `conda create --clone`을 쓰지 못했다.
- 실행: `cd /workspace/scratch/VISION-run && /venv/vision/bin/python main.py --dataset <ds> --n_way 5 --k_shot <K> --seed <s> --cres_seed <s> --out_dir <dir>`
