# 001 리포 초기화, 결정 기록, 사실 조사

작성 2026-10-13 · 지시서 `instructions/001_repo_init_and_facts.md` · GPU 사용 없음

## 1. 무엇을 했는지

| 작업 | 내용 |
|---|---|
| 1 뼈대 | `reports/ docs/register/ cres/ baselines/ splits/ tools/`(`.gitkeep`), `results/`(git 제외), `data -> /workspace/data/dataset` 심볼릭 링크 |
| 1 .gitignore | 지시서 목록과 대조. 빠진 항목 없음(`*.pyc`는 기존 `*.py[cod]`가 덮음). **수정하지 않음** |
| 1 settings | `.claude/settings.json` 작성(아래) |
| 1 remote | 사용자 완료분이라 건너뜀 |
| 2 R001 | `docs/register/R001_baseline_comparison_register.md`에 지시서 본문 그대로 기록 |
| 3 조사 | TEG-choi `CLAUDE.md`, `instructions/`, `reports/`, `argument.py`, `utils.py`, `main.py`, `model.py`, `embedder.py` 읽음 |
| 3-3 재현 | `tools/reproduce_teg_choi_split.py` → `splits/<dataset>_class_split.json` |
| 4 통계 | `tools/data_stats.py` → `results/001/data_stats.json` |

명령:
```
/venv/cres/bin/python tools/reproduce_teg_choi_split.py   > results/001/logs/reproduce_split.log   # exit 0, ALL_VERIFIED
/venv/cres/bin/python tools/data_stats.py                 > results/001/logs/data_stats.log        # exit 0
```
커밋: `b4b2a16`(뼈대·R001·도구·분할 파일), 이 보고서는 다음 `report:` 커밋.

`.claude/settings.json`:
```json
{
  "permissions": {
    "deny": [
      "Edit(//workspace/refs/**)",
      "Write(//workspace/refs/**)",
      "Edit(//workspace/data/**)",
      "Write(//workspace/data/**)"
    ]
  }
}
```
- 경로 표기: Claude Code 권한 규칙에서 `//path`는 파일시스템 절대 경로, `/path`는 설정 파일 기준 상대 경로다. 그래서 `//workspace/...`로 썼다.
- `Edit(...)` 규칙은 파일을 수정하는 내장 도구 전체에 적용된다. `Write(...)`는 명시를 위해 함께 넣었다.
- 차단 동작은 실제로 시험하지 않았다(참고 리포·데이터에 쓰기 시도를 하지 않기 위해). 참고로 `/workspace/refs/*` 디렉터리는 파일시스템 권한이 `dr-xr-xr-x`다.

## 2. 사실

### 3-1. 클래스 분할 고정 방법 (TEG-choi `3b7be89`, 브랜치 `erasure_diagnosis`)

- 코드: `utils.py:67` `class_list_valid = random.sample(train_class, valid_num_dic[dataset_source])`, `utils.py:69` base = `train_class − valid`.
  - `train_class = list(set(train.mat Label))`(`utils.py:31`), `class_list_test = list(set(test.mat Label))`(`utils.py:34`).
  - `valid_num_dic = {Amazon_clothing: 17, Amazon_electronics: 36, dblp: 27}`(`utils.py:13`).
- 시드: 전용 인자 없음. `--seed`(기본 4, `argument.py:15`)와 `--num_seed`로 `main.py:360–361`에서 `seed_everything(set_seed)` → 전역 `random.seed(seed)`(`utils.py:267`). load_data 이전에 전역 `random` 호출은 없다(`embedder.py:25–36`이 첫 호출 지점).
- **분할은 seed마다 다르다.** 하나의 고정 분할이 아니다. TEG-choi CLAUDE.md §8도 "seed마다 다른 valid 분할"로 적고 있다.
- 파일 저장: 분할 전용 파일은 없다. `--dump_emb --out_dir` 실행 시 `out_dir/split.json`(`class_list_train/valid/test`)과 `labels.npy`가 저장된다(`model.py:203–214`). `results/`는 git 제외이며, refs와 `TEG-choi.tgz`(60개 항목)에 `results/`·`split.json`은 없다.
- TEG-orig `utils.py`의 load_data와 AST가 같다(아래 3-5). 즉 분할 방식은 TEG 원본 그대로다.
- TEG-choi 보고서에 쓰인 seed: T07·T09·T13 등 0–2, T10r·T12 0–9, T16a 0.

### 3-2. 고정 test 에피소드 방법

| 항목 | 값 | 출처 |
|---|---|---|
| 켜는 인자 | `--fixed_eval` (+ `--out_dir` 필요) | `argument.py:50`, `model.py:957` |
| 생성 함수 | `teg_trainer.fixed_episodes(rng, classes, n_epi)` | `model.py:366–377` |
| 절차 | 에피소드마다 `rng.sample(classes, way)` → 클래스마다 `rng.sample(id_by_class[c], K + Q)`, 앞 K개 support | 같은 곳 (`task_generator_in_class`와 같은 순서) |
| test | 200개, `random.Random(9000 + seed)`, `class_list_test` | `model.py:388` |
| valid | 100개, `random.Random(9100 + seed)`, `class_list_valid` | `model.py:388` |
| N / K / Q | `--way`(5) / `--shot`(1, 5) / `--qry`(5) | TEG-choi CLAUDE.md §5 |
| 사용 시점 | 학습 후 model-selection 체크포인트(valid 최고 에폭, 동점은 나중 에폭)를 다시 불러 평가 | `model.py:942–947`, `379–384` |
| 저장 | 에피소드 전용 파일 없음. 실행마다 메모리에서 다시 생성. 결과는 `out_dir/fixed_eval_logits.npz`(키 `epoch, ep_idx, mode, support, query, classes, query_y, logits`) | `model.py:390–411` |

- 에피소드는 (seed, K)마다 다르다. test 클래스 목록은 seed와 무관하지만, rng 시드가 `9000 + seed`이고 K + Q개를 뽑기 때문이다.
- 학습 루프 안의 valid·test 에피소드(에폭마다 50개)는 전역 `random`으로 뽑으며 고정되지 않는다(`model.py:601–607`).

### 3-3. 분할 재현: **재현됨 (seed 0–9 계산, seed 0–2 외부 기록과 대조 통과)**

방법: TEG-choi의 `utils.py:31,34,67,69`와 같은 식을 `random.seed(seed)` 직후 실행(`tools/reproduce_teg_choi_split.py`). seed 0–9를 `splits/<dataset>_class_split.json`의 `seeds.<s>`에 저장. 클래스는 `.mat` Label의 정수 id.

대조 결과(`results/001/logs/reproduce_split.log`, 세 데이터셋 모두 `True`):

| 검사 | 기준 출처 | 결과 |
|---|---|---|
| seed 0–2의 base·valid 노드 수(정렬), test 노드 수, 클래스 수 | TEG-choi `reports/T13_dim_collapse.md` 표 1 | 3/3 일치 |
| Clothing seed 0: base 11720, valid 3839, test 9360 | TEG-choi `reports/T16a_impl_facts.md` G3(c) 표 | 일치 |
| seed 0에서 클래스 0의 소속(Clothing·Electronics base, dblp test) | 같은 보고서 J2 | 3/3 일치 |

재현된 seed별 노드 수(base / valid / test):

| 데이터셋 | 클래스 base / valid / test | seed 0 | seed 1 | seed 2 |
|---|---|---|---|---|
| Amazon_clothing | 40 / 17 / 20 | 11720 / 3839 / 9360 | 11067 / 4492 / 9360 | 10618 / 4941 / 9360 |
| Amazon_electronics | 91 / 36 / 40 | 21843 / 10259 / 10216 | 23117 / 8985 / 10216 | 23562 / 8540 / 10216 |
| dblp | 80 / 27 / 30 | 23503 / 7422 / 9747 | 24023 / 6902 / 9747 | 23178 / 7747 / 9747 |

seed 3–9의 노드 수는 `splits/*.json`과 `results/001/data_stats.json`(`split_counts_per_seed`)에 있다.

검증의 한계:
1. T13 표의 열 이름은 "n (seed 0/1/2)"이지만 값은 `sorted({...})`다(`refs/TEG-choi/tools/analyze_t13.py:128`). 따라서 T13으로는 seed별 대응이 아니라 집합 일치만 확인된다. seed별 대응이 외부 기록으로 확인된 것은 Clothing seed 0 하나다.
2. seed 3–9는 대조할 외부 기록이 없다(`verified: null`).
3. 클래스 id 목록 자체를 담은 외부 기록(`split.json`)은 refs에 없다. 대조는 노드 수·클래스 수·클래스 0 소속으로만 했다.

### 3-4. TEG-choi CLAUDE.md 규약 중 이 리포 CLAUDE.md에 없는 항목

1. 지시서 하나 = 커밋 하나 + **태그 하나**(CRES는 태그 규정 없음).
2. 기본 manual mode, 멈춤 지점 두 곳(코드 수정 전 파일 단위 계획 승인, 실행 후 보고).
3. 지시서에 없는 판단은 가장 단순한 쪽을 택하고 "이상 징후"에 기록, 수치 동작을 바꾸는 판단만 멈춤(CRES는 "결정 필요"로 멈춤).
4. 기본 플래그 = 원본 동작, 끈 상태 계산 경로 동일, 원본 함수 삭제 금지.
5. 전역 `random`의 호출 순서·횟수 불변. 새 무작위성은 등록된 오프셋의 전용 생성기만 사용.
6. 진단·덤프용 추가 forward는 `torch.random.fork_rng` 안에서.
7. 새 arm은 같은 에피소드를 재사용하고 난수를 소비하지 않음(CRES §5 고정 에피소드 파일과 목적이 겹치나 문구는 없음).
8. 재실행 변동 범위로 회귀 판정(원본 TEG는 같은 seed에서도 재실행 결과가 다를 수 있음).
9. valid 동점 규칙(`test_acc_at_best_valid`는 나중 에폭, `best_epoch_valid`는 먼저 에폭), 체크포인트 비교는 `ckpt_epoch` 기준.
10. GPU를 UUID로 지정, GPU당 run 하나, 동시 실행 상한, 프로세스당 seed 하나(`--num_seed 1`).
11. 실험 기본 설정 명시(5-way {1,5}-shot, query 5, epochs 10, episodes 50, valid·test 50/에폭, γ 0.5, EGNN 2층, anchor 16).
12. 고정 평가 구체값(seed당 test 200 `Random(9000+seed)`, valid 100 `Random(9100+seed)`).
13. 원 보고 방식(`test_acc_at_best_valid`) 병기.
14. λ 선택 규칙(seed 평균 `best_acc_valid` 최고, 동률이면 작은 값).
15. 게이트 diff 기준 = 지시서 착수 시점 HEAD.
16. 사전 등록 예측은 수정하지 않고 날짜 있는 부기만 단다(CRES §5는 "기준을 바꾸지 않는다"만 있음).
17. 보고서 금지어 목록("따라서", "의미한다", "시사한다", "때문이다", "원인", "권고")과 해석 금지(CRES는 `[추정]` 표시로 허용).
18. `results/` 삭제 조건과 디스크 부족 시 절차.
19. 재시도 로그 파일명 `_retry1` 등, 기존 로그 덮어쓰기 금지.
20. 승인 없는 패키지 설치·외부 다운로드 금지.
21. git 강제 push·히스토리 재작성 금지.
22. 클래스 그룹 용어(base / valid / test, "학습 미사용 클래스" = valid ∪ test)와 진단 용어(주체, 조건).
23. 전용 난수 오프셋 등록부(1000 probe, 3000, …, 9000/9100 고정 test/valid, 15000; 16000 이후 미배정).

### 3-5. TEG-orig ↔ TEG-choi 모델 코드 diff 요약

비교: TEG-orig `b5a8e03`, TEG-choi `3b7be89`. 줄 diff는 대부분 포맷(줄바꿈·따옴표) 차이라서 함수·클래스 단위 AST 비교(`ast.dump`)를 함께 했다.

| 파일 | AST 동일 | 바뀜 | TEG-choi에만 |
|---|---|---|---|
| `embedder.py` | 전부 | — | — |
| `utils.py` | 전부(load_data, seed_everything, task_generator_in_class 등 9개) | — | — |
| `layers/GCN.py` | `GCN` | — | `GCN2`(T06b, `--gcn_layers 2`) |
| `layers/EGNN.py` | `EGCL.__init__`, `msg_model`, `posi_model`, `coord2dist`, `EGNN.__init__`, `diff_mean`, `msg_collect` | `EGCL.coord_model`, `EGCL.forward`, `EGNN.forward`: 선택 인자 `msg_fn=None`, `w_fn=None` 추가. None이면 원 계산과 같은 식 | — |
| `model.py`(248 → 1047줄) | — | `__init__`, `train_epoch`, `train` | 25개 메서드 + `diffusion_teacher`(메모리, 보존·대조 손실, BSC, 덤프, 고정 평가, 궤적·gradient 측정) |
| `configuration.yaml` | 값 동일(끝 줄바꿈만 다름) | | |

- `model.py __init__`: `gcn_out`/`egnn_in`(기본 0 → yaml 값), optimizer(기본 Adam, weight_decay 기본 5e-4 = 원본 상수)가 인자화됨. `train_epoch`: EGNN 이후 부분을 `episode_forward`로 분리, 손실 γ·L_N + (1−γ)·L_G 유지(`model.py:715`), 플래그로 켜는 보조 손실·측정 추가.
- 백본(1층 GCN 64차원 + EGNN 2층, 손실 형태) 자체는 기본 플래그에서 바뀌지 않았다. TEG-choi T16a G1(회귀) 보고는 기본 경로가 옛 코드와 에피소드·`random` 해시 일치, 정확도 τ 이내라고 기록한다. 본 001에서 회귀 실행은 하지 않았다.
- 환경 차이: TEG-choi는 torch 2.5.1 / PyG 2.8.0.post1, 이 리포는 torch 2.4.1 / PyG 2.8.1.

### 4. 데이터 통계 (`results/001/data_stats.json`)

| 항목 | Amazon_clothing | Amazon_electronics | dblp |
|---|---|---|---|
| train.mat / test.mat 노드 | 15559 / 9360 | 32102 / 10216 | 30925 / 9747 |
| 특징 차원 | 9034 | 8669 | 7202 |
| 특징 형식 | scipy coo, float64, 정수값(1–99), 비이진, 밀도 0.35% | 정수값(1–375), 비이진, 밀도 0.47% / 0.45% | 정수값(1–68), 비이진, 밀도 0.64% / 0.66% |
| 특징이 전부 0인 행 | 0 | 0 | 0 |
| train.mat / test.mat 클래스, 교집합 | 57 / 20, 0 | 127 / 40, 0 | 107 / 30, 0 |
| 클래스당 노드 수 min–max (train / test) | 101–934 / 104–1039 | 103–945 / 101–823 | 101–1003 / 110–816 |
| Label | float64, 정수값 0–76 | 0–166 | 0–136 |
| Index가 0..N−1을 빠짐없이 덮음 | 예 (N = 24919), train·test 겹침 0 | 예 (N = 42318), 겹침 0 | 예 (N = 40672), 겹침 0 |
| `_network` 줄 수 | 183360 | 87112 | 576540 |
| 중복 줄 / 자기 루프 / 형식 오류 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| 양방향 모두 존재 | 예 (역방향 없는 쌍 0) | 예 | 예 |
| 무방향 엣지 수 | 91680 | 43556 | 288270 |
| 고립 노드 | 0 | 0 | 0 |
| 엣지 최대 id ≤ Index 최대 | 예 | 예 | 예 |
| base / valid / test 클래스 | 40 / 17 / 20 | 91 / 36 / 40 | 80 / 27 / 30 |
| base / valid / test 노드 (seed 0) | 11720 / 3839 / 9360 | 21843 / 10259 / 10216 | 23503 / 7422 / 9747 |

- 특징 밀도는 train / test 순(Clothing은 0.348% / 0.357%).
- 네트워크 파일에 양방향이 모두 들어 있으므로, TEG의 `load_data`처럼 파일을 그대로 읽으면 대칭 인접 행렬이 된다(추가 대칭화 불필요). 자기 루프는 파일에 없고 TEG는 `adj + I`로 더한다(`utils.py:61`).

## 3. 게이트 통과 여부

지시서 001에 G# 게이트는 없다. 작업 3-3의 정지 조건(재현 불가 시 멈춤)은 해당 없음: 재현 검사 전부 통과.

## 4. 결정 필요

1. **고정 분할의 단위.** TEG-choi 분할은 seed마다 다르다. `splits/*_class_split.json`에는 seed 0–9를 모두 넣었다. CRES의 "고정 분할"을 (a) 한 seed의 분할 하나로 고정할지(어느 seed인지), (b) TEG-choi처럼 seed별 분할을 쓸지 결정 필요.
2. **고정 test 에피소드의 생성 규칙.** TEG-choi는 파일 없이 seed마다 `Random(9000 + seed)`로 200개를 다시 만든다. CRES §5는 (데이터셋, N, K)마다 한 번 만든 파일을 요구한다. 결정 필요: 에피소드 수, query 수, 생성 rng 시드, TEG-choi의 `Random(9000 + seed)` 에피소드와 같게 만들지(같게 만들면 TEG-choi 결과와 에피소드 단위 대조 가능), 1번이 (b)일 때 seed별 파일 여부.
3. **에피소드 파일 형식과 `.gitignore`.** 현재 `.gitignore`가 `*.npy`, `*.npz`를 제외하므로 `splits/`에 npz로 저장하면 커밋되지 않는다. 형식(json 등) 또는 `splits/` 예외 규칙 결정 필요.
4. seed 3–9 분할은 외부 기록과 대조되지 않았다. 사용 범위가 seed 0–2를 넘으면 그대로 쓸지 결정 필요.

## 5. 참고 리포 clean 확인

`git -C /workspace/refs/<리포> status --porcelain` 줄 수(보고서 작성 직전):

| 리포 | HEAD | 변경 |
|---|---|---|
| TEG-orig | `b5a8e03` | 0 (clean) |
| TEG-choi | `3b7be89` | 0 (clean) |
| NaQ | `cfe5373` | 0 (clean) |
| VISION | `0524eae` | 0 (clean) |
