# P01 TEG 이식본 회귀 검사 (G3) — 사전 등록

- 등록 2026-10-13 (야간 큐, 003 실행 전) · 지시서 `instructions/003_teg_backbone_port_and_regression.md` §3

## 실행

- 기준 실행: `/workspace/scratch/TEG-choi-run`(refs/TEG-choi `3b7be89` 사본, 002에서 생성)의 기본 경로 + `--fixed_eval --out_dir`, Amazon_clothing, 5-way K=1, seed 0, 1, 2, **seed마다 2회**(재실행 변동 측정). 명령:
  `cd /workspace/scratch/TEG-choi-run && python main.py --dataset Amazon_clothing --way 5 --shot 1 --seed <s> --num_seed 1 --device 0 --fixed_eval --out_dir <dir>`
- 이식본: `python -m cres.teg.run --dataset Amazon_clothing --shot 1 --seed <s> --arm sup` (lam = 0), seed마다 1회.
- 비교 지표: 고정 test 200 에피소드 평균 정확도(TEG-choi는 `fixed_eval_logits.npz`의 mode = 1 행에서 argmax(logits) = query_y 비율의 에피소드 평균).

## 판정 기준 G3

- (a) 이식본과 기준 실행의 고정 test 에피소드가 같다: TEG-choi `fixed_eval_logits.npz`의 support·query·classes로 계산한 해시(`tools/make_fixed_episodes.episodes_hash`)가 `splits/episodes/hashes.json`과 같다.
- (b) seed 0, 1, 2 **각각**에서 이식본 정확도가 [기준 2회 중 최소 − τ, 최대 + τ] 안.
- τ = **1.0%p**. TEG-choi `CLAUDE.md`에는 회귀 허용치의 수치가 없다(§3 "재실행 변동 범위로 판정"만 있음). 지시서 규칙에 따라 τ = 1.0%p로 둔다. 참고: TEG-choi T16a 지시서는 τ = max(|old2 − old1|, 0.1%p)를 썼다(이 등록에서는 쓰지 않음).
- G3 통과 = (a)와 (b) 모두.

## 함께 측정 (판정 아님)

단일 실행 시간, GPU 사용률(`nvidia-smi --query-gpu=utilization.gpu,memory.used` 1초 간격), 최대 메모리. 000 §4에 따라 사용률 < 40%이고 메모리 < 8 GB이면 GPU당 동시 2개.

## 예측 (Claude)

G3 통과. 이식본은 전역 `random` 소비 순서(분할 → anchor → 에피소드)와 torch 초기화 순서를 원본과 같게 두었으므로 재실행 변동 수준의 차이만 날 것.
