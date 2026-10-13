# 지시서 001 — 리포 초기화, 결정 기록, 사실 조사

작성 2026-10-13 · GPU 불필요 · 설계 결정 없음(조사·기록만)

## 목적

CRES 리포의 뼈대를 만들고, D1 결정을 기록하고, 이후 지시서에 필요한 사실(TEG-choi의 분할·에피소드 고정 방식, 데이터 통계)을 모은다.

## 작업

### 1. 리포 뼈대

- `/workspace/CRES`에서 CLAUDE.md §6의 디렉토리를 만든다(빈 디렉토리는 `.gitkeep`).
- `data -> /workspace/data/dataset` 심볼릭 링크.
- `.gitignore`: `data`, `results/`, `*.mat`, `*_network`, `*.pt`, `*.pth`, `*.ckpt`, `.env`, `__pycache__/`, `*.pyc`, `.ipynb_checkpoints/`.
- `.claude/settings.json`: `/workspace/refs/**`와 `/workspace/data/**`에 대한 Edit·Write를 deny. (Claude Code의 절대 경로 표기 규칙을 확인해 맞게 쓰고, 쓴 내용을 보고서에 적는다.)
- `git remote add origin https://github.com/Dragor0123/cres.git`.

### 2. 결정 기록: `docs/register/R001_baseline_comparison_register.md`

아래 내용을 그대로 쓴다(날짜·결정자 포함).

```
# R001 베이스라인 비교 방식 (D1)

- 결정일: 2026-10-13 · 결정자: 이희태 · 상태: 확정, 실험 전 등록

## 결정: (c) 혼합안

| 비교 대상 | 방식 |
|---|---|
| 지도 단독 (TEG) | CRES 리포의 TEG 백본, 지도 에피소드만 |
| +NaQ식 | CRES 리포 안에서 재구현. 같은 TEG 백본, pseudo-episode 생성기만 NaQ 방식(NaQ-Feat, NaQ-Diff) |
| +CRES | 같은 TEG 백본, CRES pseudo-episode |
| TEG 공식 코드 | refs/TEG-orig + 어댑터 |
| VISION 공식 코드 | refs/VISION + 어댑터 |

## 어댑터의 정의

공식 코드의 모델·학습 로직은 바꾸지 않는다. 다음 두 가지만 바꾼다.
1. 클래스 분할을 `splits/`의 고정 분할 파일에서 읽는다.
2. test 에피소드를 자체 샘플링 대신 `splits/`의 고정 에피소드 파일에서 읽는다.
어댑터가 바꾼 줄은 diff로 보고서에 남긴다.

## 이유

- 모든 방법이 같은 test 에피소드를 풀어야 에피소드별 짝지은 차(평균 > 0, > 2·SE)를 계산할 수 있다.
- NaQ는 모델이 아니라 에피소드 생성 방법이므로, 같은 백본에 꽂아야 CRES와 생성기만 다른 비교가 된다.
- NaQ 리포는 라이선스 표시가 확인되지 않아 코드 복사 대신 재구현한다.

## 대안과 기각 사유

- (a) 각 공식 코드를 원래 프로토콜대로 실행: 에피소드가 달라 짝지은 비교 불가.
- (b) 모든 베이스라인을 어댑터로: NaQ 공식 코드는 ProtoNet 기반이라 TEG 백본 비교가 되지 않음.
```

### 3. TEG-choi 규약과 고정 방식 조사 (사실만)

`/workspace/refs/TEG-choi`의 `CLAUDE.md`, `instructions/`, `reports/`, `argument.py`, `utils.py`, `main.py`를 읽고 다음을 보고한다.

1. 클래스 분할(base/valid/test)을 고정하는 방법: 관련 인자, 코드 위치(파일:줄), 사용한 시드, 분할 결과가 파일로 저장되는지.
2. 고정 test 에피소드를 만드는 방법: 생성 함수, 에피소드 수, N-way/K-shot/query 수, 시드, 저장 경로와 형식.
3. 위 1·2로 세 데이터셋의 **실제 분할 목록을 재현**할 수 있는지. 가능하면 재현해 `splits/<dataset>_class_split.json`으로 저장하고, 재현 방법을 적는다. 불가능하면 이유를 적고 멈춘다(임의로 새 분할을 만들지 않는다).
4. TEG-choi CLAUDE.md의 규약 중 이 리포의 CLAUDE.md에 없는 항목 목록.
5. TEG-orig와 TEG-choi의 모델 코드(`model.py`, `layers/`, `embedder.py`) diff 요약: 백본 자체가 바뀌었는지, 실험용 추가만 있는지.

### 4. 데이터 통계 (사실만)

세 데이터셋 각각:
- train.mat/test.mat 노드 수, 특징 차원, 특징이 이진/희소/실수인지
- train.mat 클래스 수, test.mat 클래스 수, 두 집합의 교집합 크기
- `*_network`: 줄 수, 중복 엣지 수, 자기 루프 수, 양방향이 모두 들어 있는지(무방향 처리 필요 여부), 고립 노드 수
- Index가 0..N−1을 빠짐없이 덮는지
- (3에서 분할 재현에 성공한 경우) base/valid/test 클래스 수와 노드 수

스크립트는 `tools/data_stats.py`로 남긴다.

### 5. 마무리

- `reports/001_repo_init_and_facts.md` 작성(CLAUDE.md §8 형식).
- `git add` 전 `git status` 확인 → 커밋 → push.
- push가 인증 문제로 실패하면 재시도하지 말고 보고서에 적고 멈춘다.

## 하지 않을 것

- CRES 알고리즘 구현, 학습 실행, 분할 새로 만들기, 참고 리포 수정.
