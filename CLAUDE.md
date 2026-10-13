# CLAUDE.md — CRES

CRES(Calibrated Relational Episode Sampling) 구현·실험 리포. 원격: `github.com/Dragor0123/cres`.

## 1. 역할

- 사용자(희태)가 결정하고, Agent는 지시서(`instructions/NNN_*.md`)를 실행하고 **사실만** 보고한다.
- 지시서에 없는 설계 결정(하이퍼파라미터, 분할, 평가 방식 변경)은 하지 않는다. 필요하면 보고서에 "결정 필요"로 적고 멈춘다.
- 추정·해석은 보고서에서 `[추정]`으로 표시하고 사실과 섞지 않는다.

## 2. 경로와 실행 환경

| 항목 | 경로 |
|---|---|
| 리포 루트 | `/workspace/CRES` |
| Python | `/venv/cres/bin/python` (python 3.10, torch 2.4.1+cu124, PyG 2.8.1) |
| 데이터 | `/workspace/data/dataset/{Amazon_clothing,Amazon_electronics,dblp}` (리포 안 `data/`는 심볼릭 링크) |
| 참고 리포 | `/workspace/refs/{TEG-orig,TEG-choi,NaQ,VISION}` |

- 모든 Python 실행은 `/venv/cres/bin/python ...` 절대 경로로 한다. 셸의 기본 `python`(`/venv/main`)에 의존하지 않는다.
- GPU 2장(RTX 3090 24GB). 실행마다 `CUDA_VISIBLE_DEVICES`를 명시한다. 기본 할당: GPU 0, GPU 1에 서로 다른 시드·설정을 병렬로.
- 장시간 실행은 `nohup` 또는 tmux 창에서 돌리고, 로그는 `results/<태스크>/logs/`에 남긴다.

## 3. 읽기 전용 영역

- `/workspace/refs/**`, `/workspace/data/**`는 **읽기만** 한다. 수정·삭제·커밋·push 금지.
- 참고 리포의 코드는 읽고 diff하는 데만 쓴다. 이식할 때는 출처(리포, 파일, 커밋)를 해당 파일 상단 주석과 보고서에 적는다.
- 라이선스: TEG-orig, VISION은 MIT(출처 표기 후 이식 가능). NaQ는 라이선스 표시가 확인되지 않았으므로 **코드 복사 금지**, 논문과 코드를 참고해 재구현한다.
- 지시서 종료 시 `git -C /workspace/refs/<리포> status`가 4개 모두 clean인지 확인하고 보고서에 적는다.

## 4. 레이블 규칙 (위반 시 실험 무효)

- **base 클래스 레이블만** calibrator 학습과 지도 에피소드에 쓴다.
- valid 클래스: 모델 선택에만. test 클래스: 최종 지표에만.
- `*_train.mat`에는 base와 valid 노드가 섞여 있다. 반드시 고정 분할 파일의 base 목록으로 걸러 쓴다.
- pseudo-episode 구성은 레이블을 읽지 않는다. 레이블을 읽는 코드는 경로 단위로 분리하고, 사용 레이블 집합을 로그에 남긴다.

## 5. 평가 규약 (TEG-choi 규약 승계)

- **고정 test 에피소드**: 데이터셋·N-way·K-shot마다 한 번 생성해 파일로 저장하고, 모든 방법이 같은 파일로 평가한다.
- **짝지은 차 판정**: 방법 A − B의 에피소드별 차이에 대해, 평균 > 0 이고 평균 > 2·SE 일 때만 "분명히 낫다"고 쓴다. 그 외는 "구분 안 됨".
- **사전 등록**: 실험 전에 예측과 판정 기준을 `docs/register/`에 P## 번호로 커밋한다. 결과가 나온 뒤 기준을 바꾸지 않는다.
- **게이트**: 지시서에 적힌 게이트(G#)를 통과하지 못하면 다음 단계로 가지 않고 멈춰 보고한다.
- 베이스라인 비교 방식은 `docs/register/R001_baseline_comparison_register.md`를 따른다.

## 6. 리포 구조

```
CRES/
├── CLAUDE.md
├── instructions/     지시서 (사용자 작성)
├── reports/          보고서 (Agent 작성, NNN_<이름>.md)
├── docs/register/    결정·사전 등록 기록 (R###, P##)
├── cres/             CRES 코드
├── baselines/        TEG·VISION 어댑터, NaQ식 재구현
├── splits/           고정 클래스 분할, 고정 test 에피소드 (커밋 대상)
├── tools/            분석 스크립트
├── data -> /workspace/data/dataset   (git 제외)
├── records/          다시 계산에 필요한 최소 결과 CSV/JSON (커밋 대상, 002)
└── results/          실행 출력 (git 제외, 요약만 reports/에)
```

- `records/<항목번호>_<이름>/`: 다시 계산에 필요한 최소 결과를 CSV/JSON으로 저장·커밋한다. 예: 실행별 에피소드 정확도 `ep_acc_<dataset>_K<k>_seed<s>_<arm>.csv`(열: `mode, ep_idx, acc`), 실행 메타 `run_meta.jsonl`(설정, 커밋, 소요 시간, best epoch, GPU). 파일 하나 5 MB 이하. 넘으면 요약만 저장하고 보고서에 적는다. (002)
- 고정 에피소드: `splits/episodes/<dataset>_seed<s>_K<k>.json`(R002). 평가는 이 파일만 읽는다.

### 전용 난수 오프셋 (seed에 더함, 002)

TEG-choi 등록부(1000 probe, 9000 / 9100 고정 test / valid 등)를 그대로 따르고, CRES용으로 다음을 등록한다. 전역 `random`의 호출 순서는 TEG 기본 경로와 같게 유지하고, 새 무작위성은 아래 전용 생성기만 쓴다.

| 오프셋 | 용도 |
|---|---|
| 9000 / 9100 | 고정 test / valid 에피소드 (R002) |
| 20000 + seed | k-means 초기화 (004) |
| 21000 + seed | calibrator 초기화·쌍 표본 추출 (004) |
| 22000 + seed | NaQ식 pseudo-episode 샘플링 (006) |
| 23000 + seed | CRES pseudo-episode 샘플링 (008) |
| 24000 + seed | 관문 2 에피소드 충돌 시뮬레이션 (005) |
| 25000 + seed | 순도 곡선 진단 치환 동률 처리 (013) |

## 7. git

- 리포는 현재 **공개** 상태다. 데이터(`*.mat`, `*_network`), 체크포인트, 토큰, `.env`는 절대 커밋하지 않는다. 커밋 전 `git status`와 `git diff --cached --stat`으로 확인한다.
- 커밋 메시지 접두어: `feat:`, `report:`, `docs:`, `chore:`, `analysis:`.
- 지시서 하나가 끝날 때마다 커밋하고 push한다. 서버는 단기 대여이므로 push되지 않은 것은 잃는다고 본다.
- `records/`는 커밋한다(`results/`는 서버와 함께 사라지므로 다시 계산에 필요한 것은 `records/`에). sweep 중에는 1시간마다 `records/`를 커밋·push한다.
- 삭제는 사용자가 지시한 경우에만 한다. 대체된 결과는 지우지 않고 보고서에 "superseded"로 기록한다.

## 8. 보고서 형식

`reports/NNN_<이름>.md`:
1. 무엇을 했는지 (명령, 커밋 해시)
2. 사실 (숫자는 출력에서 그대로, 출처 파일 명시)
3. 게이트 통과 여부
4. 결정 필요 사항 (있으면)
5. 참고 리포 clean 확인
