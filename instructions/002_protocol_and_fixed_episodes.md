# 002 — 평가 프로토콜 확정(임시 기본값), 고정 에피소드 파일, records 규칙

GPU 불필요. 001 보고서 §4 "결정 필요" 1–4에 대한 **임시 기본값**(사용자 부재, Claude 제안)을 기록하고 그대로 구현한다.

## 1. `docs/register/R002_eval_protocol_register.md` (그대로 기록)

```
# R002 평가 프로토콜 (001 결정 필요 1–4)

- 기록 2026-10-13 · 상태: 임시 기본값 (사용자 부재로 Claude 제안, 사용자 검토 대기)

1. 분할 단위: TEG-choi와 같이 seed별 분할 (001 결정 필요 1의 (b)).
   - 주 분석 seed: 0, 1, 2 (외부 기록과 대조된 범위).
   - 근거: TEG-choi·EATS 결과와 같은 분할에서 비교 가능. calibrator는 seed별 base 레이블로 따로 학습.
2. 고정 에피소드: TEG-choi `--fixed_eval`과 같은 규칙으로 생성해 파일로 저장.
   - test 200개 `random.Random(9000 + seed)`, valid 100개 `random.Random(9100 + seed)`.
   - 5-way, K ∈ {1, 5}, query 5. 절차는 TEG-choi `model.py:366–377`과 같은 순서.
   - (dataset, seed, K)마다 파일 하나. 근거: TEG-choi 결과와 에피소드 단위 대조 가능.
3. 파일 형식: JSON. `splits/episodes/<dataset>_seed<s>_K<k>.json`.
4. seed 3–9: 이번 단계에서 쓰지 않음.
5. 모델 선택: TEG-choi와 같이 valid 최고 에폭 체크포인트(동점은 나중 에폭) → 고정 test 에피소드로 평가.
```

## 2. 고정 에피소드 생성

- `tools/make_fixed_episodes.py`: 001의 `splits/<dataset>_class_split.json`과 데이터 로더로 id_by_class를 만들고, 위 규칙으로 생성.
- JSON 내용: `{"dataset","seed","K","Q","N","mode","rng":"Random(9000+seed)","episodes":[{"classes":[...],"support":[[...]...],"query":[[...]...]}]}` (test·valid 각각 파일 또는 한 파일의 두 키, 택일 후 기록).
- **검증**: TEG-choi의 `fixed_episodes`를 직접 호출해 만든 에피소드와 같은지 확인한다. refs는 읽기 전용이므로 `/workspace/scratch/TEG-choi-run/`에 `cp -r`로 복사하고 데이터 심볼릭 링크를 걸어 그 사본에서 import/실행한다. 세 데이터셋 × seed 0–2 × K∈{1,5}에서 해시 일치 여부를 표로.
- 불일치 시: 원인(id_by_class 순서 등)을 기록하고, TEG-choi 쪽 결과를 기준으로 맞춘다. 맞출 수 없으면 "결정 필요"로 적고 우리 생성 결과로 진행.

## 3. `records/` 규칙 (CLAUDE.md에 추가)

CLAUDE.md §6·§7에 다음을 추가하고 커밋:
- `records/<항목번호>_<이름>/`에 다시 계산에 필요한 최소 결과를 CSV/JSON으로 저장·커밋. 예: 실행별 에피소드 정확도 `ep_acc_<dataset>_K<k>_seed<s>_<arm>.csv`(열: `mode, ep_idx, acc`), 실행 메타 `run_meta.jsonl`(설정, 커밋, 소요 시간, best epoch, GPU).
- 파일 하나 5 MB 이하. 넘으면 요약만 저장하고 보고서에 적는다.

## 4. 전용 난수 오프셋 (CLAUDE.md에 추가)

TEG-choi 등록부(9000/9100 등)를 그대로 따르고, CRES용으로 다음을 등록:

| 오프셋 | 용도 |
|---|---|
| 20000 + seed | k-means 초기화 (004) |
| 21000 + seed | calibrator 초기화·쌍 표본 추출 (004) |
| 22000 + seed | NaQ식 pseudo-episode 샘플링 (006) |
| 23000 + seed | CRES pseudo-episode 샘플링 (008) |
| 24000 + seed | 관문 2 에피소드 충돌 시뮬레이션 (005) |

전역 `random`의 호출 순서는 TEG 기본 경로와 같게 유지한다(새 무작위성은 위 전용 생성기만 사용).

## 5. 보고서

`reports/002_protocol_and_fixed_episodes.md`: 파일 목록, 해시 일치 표, 에피소드 수·클래스 분포 요약. 커밋·push.
