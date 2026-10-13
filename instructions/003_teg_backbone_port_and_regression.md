# 003 — TEG 백본 이식, 회귀 검사(G3), 지도 단독 sweep

GPU 사용. 이후 006·008이 이 백본을 쓴다.

## 1. 이식

- `cres/teg/`에 TEG 백본을 옮긴다. 출처: `refs/TEG-orig` (`b5a8e03`, MIT). 각 파일 상단에 출처 주석.
  - GCN(1층 64차원) + EGNN 2층, 손실 γ·L_N + (1−γ)·L_G, configuration.yaml의 데이터셋별 값.
  - 데이터 로딩은 우리 로더 + `splits/<dataset>_class_split.json`(seed별).
  - 고정 평가는 `splits/episodes/*.json`을 읽는다(자체 생성 금지).
- 학습 루프는 **보조 손실을 꽂을 수 있게** 만든다: `train_step(sup_episode, pseudo_episode=None, lam=0.0)` → `L = L_sup + lam · L_pseudo`, 두 에피소드는 같은 인코더·과제 모듈을 쓴다. `lam=0`이면 pseudo 에피소드를 만들지도 forward하지도 않는다(지도 단독 경로가 원본과 같은 계산이어야 함).
- 기본 설정은 TEG-choi CLAUDE.md의 실험 기본값(5-way, K∈{1,5}, query 5, epochs 10, episodes 50, valid·test 50/에폭, γ 0.5, EGNN 2층, anchor 16). 모델 선택 규칙은 R002 §5.
- 실행 결과: `results/003/...` + `records/003_teg_port/ep_acc_*.csv`, `run_meta.jsonl`.

## 2. `tools/job_runner.py`

000 §4의 사양대로 작성. 입력 jsonl 한 줄 = 작업 하나(`id, cmd, gpu, log`). GPU별 동시 실행 상한 인자. 상태 파일로 재시작 안전.

## 3. 회귀 검사 G3 (사전 등록 후 실행)

`docs/register/P01_teg_port_regression.md`에 먼저 커밋:

- 기준 실행: `/workspace/scratch/TEG-choi-run`(002에서 만든 사본)으로 TEG-choi 기본 경로 `--fixed_eval`, Amazon_clothing, K=1, seed 0–2, **각 seed 2회**(재실행 변동 측정).
- 이식본: 같은 데이터셋·K·seed로 각 1회.
- 비교 지표: 고정 test 200 에피소드 평균 정확도.
- **G3 통과**: (a) 이식본과 기준 실행의 고정 test 에피소드가 같다(support·query id 해시 일치), 그리고 (b) seed 0–2 각각에서 이식본 정확도가 [기준 2회 중 최소 − τ, 최대 + τ] 안. τ는 TEG-choi CLAUDE.md의 회귀 허용치(찾지 못하면 τ = 1.0%p로 두고 그렇게 했다고 기록).
- 실행 중 단일 실행 시간, GPU 사용률(`nvidia-smi dmon` 또는 `--query-gpu`), 최대 메모리를 측정해 `QUEUE_STATE.md`에 기록하고 000 §4·§5에 따라 동시 실행 수와 예상 일정을 정한다.

G3 실패: 원인 후보를 기록, 006·008 skip(000 §6). 004·005·007은 계속.

## 4. 지도 단독 sweep (G3 통과 시, 백그라운드)

- 3 데이터셋 × K∈{1,5} × seed 0–2 = 18 실행, `lam=0`. GPU-B.
- 띄운 직후 004로 넘어간다. 끝나면 `records/003_teg_port/`에 저장·커밋.

## 5. 보고서

`reports/003_teg_port_regression.md`: 이식 범위(파일·함수 대응표), G3 표(seed별 기준 2회·이식본·판정), 시간·자원 측정치, sweep 상태.
