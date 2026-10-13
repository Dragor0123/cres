# 002 평가 프로토콜(임시 기본값)과 고정 에피소드 파일

작성 2026-10-13 (야간 큐) · GPU 사용 없음

## 1. 무엇을 했는지

- `docs/register/R002_eval_protocol_register.md`: 지시서 §1 본문 그대로 기록.
- `cres/data.py`: 공용 로더. 그래프·특징·레이블 구성은 TEG-orig `utils.py` load_data와 같은 식(출처 주석), 분할은 `splits/<dataset>_class_split.json`에서 읽음. `id_by_class`는 TEG와 같은 순서(클래스 키 = 노드 0..N−1 첫 등장 순, 노드 목록 = id 오름차순).
- `tools/make_fixed_episodes.py`: R002 §2 규칙으로 생성. **한 파일에 `test`, `valid` 두 키**를 두는 형식을 택함. `support`/`query`는 way별 리스트(5 × K, 5 × Q).
- `tools/verify_fixed_episodes_tegchoi.py`: `/workspace/scratch/TEG-choi-run`(refs/TEG-choi `cp -r` 사본, `dataset/<ds>` → `/workspace/data/dataset/<ds>` 심볼릭 링크)에서 TEG-choi의 `utils.seed_everything(s)` → `utils.load_data(ds)` → `teg_trainer.fixed_episodes(...)`를 직접 호출해 해시 대조.
- CLAUDE.md §6에 `records/` 규칙·고정 에피소드 경로·CRES 전용 난수 오프셋 표, §7에 `records/` 커밋 규칙 추가.

명령:
```
/venv/cres/bin/python tools/make_fixed_episodes.py
cd /workspace/scratch/TEG-choi-run && /venv/cres/bin/python /workspace/CRES/tools/verify_fixed_episodes_tegchoi.py   # exit 0, ALL_MATCH
```

## 2. 사실

### 파일 목록 (`splits/episodes/`, 합계 1.6 MB)

18개: `{Amazon_clothing, Amazon_electronics, dblp}_seed{0,1,2}_K{1,5}.json` (각 71–108 KB) + `hashes.json`.
각 파일: test 200개(`Random(9000+seed)`), valid 100개(`Random(9100+seed)`), N=5, Q=5.

### 해시 일치 표 (sha1 앞 12자리, 출처 `records/002_protocol/verify_tegchoi.json`)

해시 대상: 에피소드 순서대로 `[classes, support 평탄화, query 평탄화]` JSON의 sha1.

| 데이터셋 | seed | K | test (ours = TEG-choi) | valid (ours = TEG-choi) | 일치 |
|---|---|---|---|---|---|
| Amazon_clothing | 0 | 1 | 14b8d24f21b5 | 92c9345e6767 | 예 |
| Amazon_clothing | 0 | 5 | de95732cd5a7 | 1bab87ed4fe9 | 예 |
| Amazon_clothing | 1 | 1 | b8f704cf9ff4 | b5097b55f887 | 예 |
| Amazon_clothing | 1 | 5 | fc094b5d12b9 | 035df62815e3 | 예 |
| Amazon_clothing | 2 | 1 | bdf41b2f4c9a | a44e91481983 | 예 |
| Amazon_clothing | 2 | 5 | 99a4c883d771 | 7c2e38724c58 | 예 |
| Amazon_electronics | 0 | 1 | cd9bebe37239 | 7fa8f8127c41 | 예 |
| Amazon_electronics | 0 | 5 | edf3041aae83 | 76f47b1a1fb7 | 예 |
| Amazon_electronics | 1 | 1 | 32553df6f3c3 | adf471a7b1ee | 예 |
| Amazon_electronics | 1 | 5 | 5f0ade8f4f2a | bf8d0c4ad77a | 예 |
| Amazon_electronics | 2 | 1 | 1c985ab84532 | 169256a50645 | 예 |
| Amazon_electronics | 2 | 5 | d118e3ce09c4 | f6bc92246338 | 예 |
| dblp | 0 | 1 | 5bd7075130e4 | bf0674d288f5 | 예 |
| dblp | 0 | 5 | 94b2c7fc22b9 | d20d03a0e824 | 예 |
| dblp | 1 | 1 | 8bfc51dfbf94 | 87137a3fa938 | 예 |
| dblp | 1 | 5 | 211a197a35f3 | 1c4ad89a5b19 | 예 |
| dblp | 2 | 1 | 8d3b7a57755b | ae0d773ae3d2 | 예 |
| dblp | 2 | 5 | 239cd6389364 | bb1aefbb05c7 | 예 |

36/36 일치. TEG-choi 쪽은 `load_data`가 전역 `random`으로 만든 valid 분할을 썼으므로, 001의 seed 0–2 분할 파일(클래스 목록과 순서)도 이 대조로 함께 일치가 확인된다.

### 클래스 분포 (K=1 파일, 에피소드에 나온 클래스 수와 클래스별 등장 횟수 min–max)

| 데이터셋 | seed | test 클래스 / 등장 | valid 클래스 / 등장 |
|---|---|---|---|
| Amazon_clothing | 0 / 1 / 2 | 20 / 38–62, 41–61, 42–68 | 17 / 22–36, 22–36, 24–34 |
| Amazon_electronics | 0 / 1 / 2 | 40 / 18–36, 16–40, 12–41 | 36 / 7–23, 8–24, 8–21 |
| dblp | 0 / 1 / 2 | 30 / 25–41, 27–46, 20–43 | 27 / 11–28, 10–24, 9–29 |

모든 test·valid 클래스가 각 파일에 1회 이상 나온다.

## 3. 게이트

002에 게이트 없음.

## 4. 결정 필요

없음.

## 5. 참고 리포 clean 확인

refs 4개 `git status --porcelain` 0줄(009에서 최종 재확인). 검증은 `/workspace/scratch/TEG-choi-run` 사본에서만 실행.
