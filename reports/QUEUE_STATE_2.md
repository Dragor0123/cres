# QUEUE_STATE_2 (2차 큐 2026-10-13 → 10-14, 010 규칙)

T0: 2026-10-13T22:57:40Z  GPU-A: GPU-16eb803b-cabc-049e-0a5c-c5e7667128b4 (index 0)  GPU-B: GPU-c7939e10-56dd-ef42-8af1-3833c860307b (index 1)  동시 실행: GPU당 2
- 시간 예산 없음(010 §1). 015는 011–014 종료 후.
- 시작 시 디스크: overlay 60G, 사용 15G, 여유 46G. git clean (HEAD 31a270e). GPU 둘 다 유휴(1 MiB, 0%).

| 항목 | 상태 | 시작 | 종료 | 게이트 | 커밋 | 비고 |
|---|---|---|---|---|---|---|
| R004 | done | 22:57 | 22:58 | — | (this) | 010 §2 그대로 |
| 011 | running | 22:58 | | — | | 구현 완료, sweep 23:11~ |
| 012 | done | 23:02 | 23:11 | — | (012 report) | 36/36, 실패 0 |
| 013 | pending | | | — | | |
| 014 | pending | | | — | | |
| 015 | pending | | | — | | |
| 016 | pending | | | — | | |

결정 필요:
1. (012) 체크포인트 선택이 고정 valid 100이 아니라 학습 중 전역 random valid 50(TEG-choi 규칙). sup2는 이 50개가 sup과 다름. 현행 유지 여부.

돌고 있는 작업:
- job_runner (results/queue2/, exit_when_idle 0): 011 72 → 014 24
