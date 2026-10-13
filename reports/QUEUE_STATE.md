# QUEUE_STATE (야간 큐 2026-10-13 → 10-14)

T0: 2026-10-13T15:08:55Z  GPU-A: GPU-16eb803b-cabc-049e-0a5c-c5e7667128b4 (index 0)  GPU-B: GPU-c7939e10-56dd-ef42-8af1-3833c860307b (index 1)  동시 실행: 2 (003 측정: 이식본 단일 실행 GPU 사용률 평균 35.8%, 최대 메모리 2460 MiB)

- 새 작업 마감 T0+8h00 = 2026-10-13T23:08:55Z, 009 작성 T0+8h30 = 23:38:55Z
- 시작 시 디스크: overlay 60G, 사용 7.8G, 여유 53G. git clean (HEAD 1146a02).

| 항목 | 상태 | 시작 | 종료 | 게이트 | 커밋 | 비고 |
|---|---|---|---|---|---|---|
| 002 | done | 15:09 | 15:11 | — | a367635 | 36/36 해시 일치 |
| 003 | done | 15:11 | 15:28 | G3 1차 불충족 → 수정 후 2차 충족 | (003 report) | 동점 판정 합산 순서 버그 |
| 003 sweep | done | 15:19 | 15:27 | — | (003 report) | 18/18, 실패 0 |
| 004 | done | 15:20 | 15:31 | G1 불통과 (0/3) | (004 report) | Electronics 2/3, Clothing·dblp 0/3 |
| 005 | done | 15:31 | 15:38 | G2 통과 (2/3: Clothing·Electronics, dblp 불통과) | (005 report) | |
| 006 | done | 15:32 | 15:52 | — | (006 report) | 72/72, 실패 0 |
| 007 | running | 15:40 | | — | 5aca48f | VISION 18개 대기열(006 뒤). TEG-orig: 환경 불가로 skip |
| 008 | skipped | | | G1 불통과 | | 000 §6 |
| 009 | todo | | | — | | |

결정 필요:
1. (003) G3를 1차 불충족 → 이식 버그 수정 → 2차 충족으로 처리. 재실행 통과가 등록 취지에 맞는지 확인 필요.
2. (004) G1 불통과 → 008 skip. 다음 설계 방향은 사용자 판단.
3. (005) Electronics G2 통과는 B1(s_H)이 약한 데서 오는 차이가 대부분(core − B2 +0.1~1.0%p, core − B3 ≈ 0). 비교 기준 검토 필요.
4. (005) r 방향(ψ(u,v)의 u 우선) 구현 세부 검토.
5. (007) TEG-orig 공식 실행 skip: conda 실행 파일이 없어 python 3.8 환경을 만들 수 없고, torch 1.10.1은 python 3.10 wheel이 없음. 환경 구성 방법 결정 필요.
7. (006) NaQ 재구현의 K=5 support 구성(anchor + 상위 이웃)과 풀 U(base 제외) 검토. Electronics NaQ-Diff는 pseudo-episode의 52–68%에 중복 노드.
6. (007) VISION 환경은 conda clone 대신 /venv/cres 기반 --system-site-packages venv + ogb.

돌고 있는 작업:
- runner_all (pid in results/sweep/runner_all.pid): 006 NaQ 72개 + 007 VISION 18개, GPU-A·B 각 2개 동시, --stop_after 23:08:55Z
