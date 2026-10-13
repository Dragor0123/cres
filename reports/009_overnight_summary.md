# 009 야간 요약 (2026-10-13 ~)

작성 2026-10-13 16:25 UTC · T0 = 15:08:55Z · 모든 실행 항목 종료 시점 T0+1h10(16:16)에 작성(000 §5 "모든 작업 종료 또는 T0+8h30 중 먼저").
집계: `tools/aggregate_overnight.py` → `records/009_summary/aggregate.json`, `tables.md` (records/만 읽음).

## 1. 큐 결과

| 항목 | 상태 | 시작–종료 (UTC) | 소요 | 게이트 | 커밋(보고서) |
|---|---|---|---|---|---|
| 002 프로토콜·고정 에피소드 | done | 15:09–15:11 | 2분 | — | `a367635` |
| 003 TEG 이식·회귀 | done | 15:11–15:27 | 16분 | G3: 1차 불충족 → 수정 → 2차 충족 | `6ec285f`, `62d11f6`, `ba33865` |
| 003 지도 단독 sweep | done (18/18) | 15:19–15:27 | 8분 | — | `ba33865` |
| 004 관문 1 calibrator | done | 15:20–15:28 | 8분 | **G1 불통과 (0/3)** | `aa85165`(R003·P02), `5b14044` |
| 005 관문 2 core 순도 | done | 15:28–15:36 | 8분 | **G2 통과 (2/3)** | `2c63257`(P03), `99ca8e1` |
| 006 +NaQ식 arm | done (72/72) | 15:32–15:50 | 18분 | — | `50d4d53`(P04), `f5de614` |
| 007 VISION | done (18/18) | 15:39–16:16 | 37분 | — | `5aca48f`, `c2a72c8` |
| 007 TEG-orig | skipped | — | — | — | 환경 구성 불가 |
| 008 CRES pilot | skipped | — | — | G1 불통과 | `cd8cf6a` |
| 009 요약 | done | 16:17– | | — | 이 보고서 |

실패·재시도: job_runner 기준 120개 작업 모두 1회에 종료 코드 0.

## 2. 게이트

| 게이트 | 판정 | 핵심 수치 | 보고서 |
|---|---|---|---|
| G3 이식 회귀 | 충족(2차) | 1차: seed 1 이식본 82.42 vs TEG-choi 81.16(구간 [80.16, 82.16] 밖). 원인: 에폭 정확도를 `np.mean`으로 계산해 valid 동점 판정이 달라짐(체크포인트 에폭 6 vs 3). 수정 후 3 seed 모두 81.46 / 81.16 / 77.66으로 TEG-choi와 같고 에피소드별 정확도도 동일 | 003 |
| G1 calibrator | 불통과 0/3 | C1 − 최고 비교 대상 top-10 순도(%p): Clothing +0.08/+0.08/+0.08(SE 0.06–0.07), Electronics +0.21/+0.23/+0.05(SE 0.09), dblp −0.54/−0.63/−0.60(비교 대상 s_H) | 004 |
| G2 core 순도 (m=10) | 통과 2/3 | core − B1(%p): Clothing +0.41/+1.10/+0.93, Electronics +11.73/+10.28/+9.71(모두 분명, test 채택률 0.56–0.63), dblp −2.83/−3.70/−2.62 | 005 |

## 3. 정확도·짝지은 차

arm 이름: `sup` = 지도 단독(003 이식본), `naqfeat_l<λ>`/`naqdiff_l<λ>` = +NaQ식(006), `vision` = VISION 공식 코드 + 어댑터(007), `cres_*`·`tegorig` = 미실행.

### 고정 test 정확도 (%, seed 0 / 1 / 2, 평균)

| 데이터셋 | K | arm | seed 0 / 1 / 2 | 평균 |
|---|---|---|---|---|
| Amazon_clothing | 1 | sup | 81.46 / 81.16 / 77.66 | 80.09 |
| Amazon_clothing | 1 | naqfeat_l0.5 | 85.42 / 86.46 / 87.42 | 86.43 |
| Amazon_clothing | 1 | naqfeat_l1.0 | 86.20 / 85.76 / 87.80 | 86.59 |
| Amazon_clothing | 1 | naqdiff_l0.5 | 86.80 / 86.14 / 84.10 | 85.68 |
| Amazon_clothing | 1 | naqdiff_l1.0 | 88.16 / 86.30 / 85.70 | 86.72 |
| Amazon_clothing | 1 | cres_l0.5 | 미완료 | 미완료 |
| Amazon_clothing | 1 | cres_l1.0 | 미완료 | 미완료 |
| Amazon_clothing | 1 | vision | 84.08 / 82.78 / 82.72 | 83.19 |
| Amazon_clothing | 1 | tegorig | 미완료 | 미완료 |
| Amazon_clothing | 5 | sup | 91.80 / 90.20 / 90.06 | 90.69 |
| Amazon_clothing | 5 | naqfeat_l0.5 | 93.94 / 91.24 / 92.26 | 92.48 |
| Amazon_clothing | 5 | naqfeat_l1.0 | 93.48 / 91.58 / 92.46 | 92.51 |
| Amazon_clothing | 5 | naqdiff_l0.5 | 90.62 / 90.54 / 90.40 | 90.52 |
| Amazon_clothing | 5 | naqdiff_l1.0 | 90.12 / 90.68 / 90.58 | 90.46 |
| Amazon_clothing | 5 | cres_l0.5 | 미완료 | 미완료 |
| Amazon_clothing | 5 | cres_l1.0 | 미완료 | 미완료 |
| Amazon_clothing | 5 | vision | 90.48 / 89.82 / 89.82 | 90.04 |
| Amazon_clothing | 5 | tegorig | 미완료 | 미완료 |
| Amazon_electronics | 1 | sup | 75.10 / 71.16 / 75.84 | 74.03 |
| Amazon_electronics | 1 | naqfeat_l0.5 | 79.26 / 76.54 / 80.54 | 78.78 |
| Amazon_electronics | 1 | naqfeat_l1.0 | 80.20 / 77.50 / 81.28 | 79.66 |
| Amazon_electronics | 1 | naqdiff_l0.5 | 77.64 / 71.66 / 77.10 | 75.47 |
| Amazon_electronics | 1 | naqdiff_l1.0 | 77.24 / 71.58 / 77.58 | 75.47 |
| Amazon_electronics | 1 | cres_l0.5 | 미완료 | 미완료 |
| Amazon_electronics | 1 | cres_l1.0 | 미완료 | 미완료 |
| Amazon_electronics | 1 | vision | 76.66 / 77.06 / 78.68 | 77.47 |
| Amazon_electronics | 1 | tegorig | 미완료 | 미완료 |
| Amazon_electronics | 5 | sup | 87.76 / 86.74 / 87.74 | 87.41 |
| Amazon_electronics | 5 | naqfeat_l0.5 | 89.80 / 89.44 / 90.82 | 90.02 |
| Amazon_electronics | 5 | naqfeat_l1.0 | 90.20 / 89.22 / 91.12 | 90.18 |
| Amazon_electronics | 5 | naqdiff_l0.5 | 86.38 / 86.62 / 87.54 | 86.85 |
| Amazon_electronics | 5 | naqdiff_l1.0 | 85.16 / 85.40 / 87.50 | 86.02 |
| Amazon_electronics | 5 | cres_l0.5 | 미완료 | 미완료 |
| Amazon_electronics | 5 | cres_l1.0 | 미완료 | 미완료 |
| Amazon_electronics | 5 | vision | 85.60 / 86.66 / 88.60 | 86.95 |
| Amazon_electronics | 5 | tegorig | 미완료 | 미완료 |
| dblp | 1 | sup | 75.38 / 75.14 / 76.68 | 75.73 |
| dblp | 1 | naqfeat_l0.5 | 77.08 / 75.62 / 78.06 | 76.92 |
| dblp | 1 | naqfeat_l1.0 | 77.24 / 75.86 / 78.08 | 77.06 |
| dblp | 1 | naqdiff_l0.5 | 77.58 / 76.68 / 78.38 | 77.55 |
| dblp | 1 | naqdiff_l1.0 | 78.04 / 76.74 / 79.64 | 78.14 |
| dblp | 1 | cres_l0.5 | 미완료 | 미완료 |
| dblp | 1 | cres_l1.0 | 미완료 | 미완료 |
| dblp | 1 | vision | 72.46 / 70.16 / 72.20 | 71.61 |
| dblp | 1 | tegorig | 미완료 | 미완료 |
| dblp | 5 | sup | 84.24 / 84.88 / 84.04 | 84.39 |
| dblp | 5 | naqfeat_l0.5 | 85.02 / 86.26 / 85.46 | 85.58 |
| dblp | 5 | naqfeat_l1.0 | 84.90 / 86.22 / 85.86 | 85.66 |
| dblp | 5 | naqdiff_l0.5 | 85.48 / 86.38 / 85.82 | 85.89 |
| dblp | 5 | naqdiff_l1.0 | 85.78 / 86.60 / 86.24 | 86.21 |
| dblp | 5 | cres_l0.5 | 미완료 | 미완료 |
| dblp | 5 | cres_l1.0 | 미완료 | 미완료 |
| dblp | 5 | vision | 80.92 / 81.38 / 79.84 | 80.71 |
| dblp | 5 | tegorig | 미완료 | 미완료 |

### λ 선택 (seed 평균 고정 valid, %)

| 데이터셋 | K | 생성기 | λ 0.5 | λ 1.0 | 선택 |
|---|---|---|---|---|---|
| Amazon_clothing | 1 | naq_feat | 81.53 | 81.84 | 1.0 |
| Amazon_clothing | 1 | naq_diff | 81.52 | 82.43 | 1.0 |
| Amazon_clothing | 1 | cres | 미완료 | 미완료 | 미완료 |
| Amazon_clothing | 5 | naq_feat | 89.60 | 89.91 | 1.0 |
| Amazon_clothing | 5 | naq_diff | 87.67 | 87.48 | 0.5 |
| Amazon_clothing | 5 | cres | 미완료 | 미완료 | 미완료 |
| Amazon_electronics | 1 | naq_feat | 84.55 | 86.29 | 1.0 |
| Amazon_electronics | 1 | naq_diff | 83.53 | 84.12 | 1.0 |
| Amazon_electronics | 1 | cres | 미완료 | 미완료 | 미완료 |
| Amazon_electronics | 5 | naq_feat | 93.01 | 92.93 | 0.5 |
| Amazon_electronics | 5 | naq_diff | 91.00 | 90.76 | 0.5 |
| Amazon_electronics | 5 | cres | 미완료 | 미완료 | 미완료 |
| dblp | 1 | naq_feat | 76.01 | 76.21 | 1.0 |
| dblp | 1 | naq_diff | 77.01 | 77.32 | 1.0 |
| dblp | 1 | cres | 미완료 | 미완료 | 미완료 |
| dblp | 5 | naq_feat | 85.80 | 85.56 | 0.5 |
| dblp | 5 | naq_diff | 85.64 | 85.69 | 1.0 |
| dblp | 5 | cres | 미완료 | 미완료 | 미완료 |

### 짝지은 차 (%p, seed 0–2 에피소드 600개 합침; 분명 = 평균 > 0 이고 > 2·SE)

| 데이터셋 | K | 쌍 | 사용 arm | 평균 ± SE | 분명 | seed별 평균 (0 / 1 / 2) |
|---|---|---|---|---|---|---|
| Amazon_clothing | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +6.49 ± 0.40 | 예 | +4.74 / +4.60 / +10.14 |
| Amazon_clothing | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +6.63 ± 0.39 | 예 | +6.70 / +5.14 / +8.04 |
| Amazon_clothing | 1 | +CRES − sup | — | 미완료 | — | — |
| Amazon_clothing | 1 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| Amazon_clothing | 1 | sup − VISION | sup − vision | -3.10 ± 0.45 | 아니오 | -2.62 / -1.62 / -5.06 |
| Amazon_clothing | 1 | sup − TEG-orig | — | 미완료 | — | — |
| Amazon_clothing | 5 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.82 ± 0.20 | 예 | +1.68 / +1.38 / +2.40 |
| Amazon_clothing | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.17 ± 0.22 | 아니오 | -1.18 / +0.34 / +0.34 |
| Amazon_clothing | 5 | +CRES − sup | — | 미완료 | — | — |
| Amazon_clothing | 5 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| Amazon_clothing | 5 | sup − VISION | sup − vision | +0.65 ± 0.27 | 예 | +1.32 / +0.38 / +0.24 |
| Amazon_clothing | 5 | sup − TEG-orig | — | 미완료 | — | — |
| Amazon_electronics | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +5.63 ± 0.40 | 예 | +5.10 / +6.34 / +5.44 |
| Amazon_electronics | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.43 ± 0.39 | 예 | +2.14 / +0.42 / +1.74 |
| Amazon_electronics | 1 | +CRES − sup | — | 미완료 | — | — |
| Amazon_electronics | 1 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| Amazon_electronics | 1 | sup − VISION | sup − vision | -3.43 ± 0.49 | 아니오 | -1.56 / -5.90 / -2.84 |
| Amazon_electronics | 1 | sup − TEG-orig | — | 미완료 | — | — |
| Amazon_electronics | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +2.61 ± 0.23 | 예 | +2.04 / +2.70 / +3.08 |
| Amazon_electronics | 5 | +NaQ-Diff − sup | naqdiff_l0.5 − sup | -0.57 ± 0.28 | 아니오 | -1.38 / -0.12 / -0.20 |
| Amazon_electronics | 5 | +CRES − sup | — | 미완료 | — | — |
| Amazon_electronics | 5 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| Amazon_electronics | 5 | sup − VISION | sup − vision | +0.46 ± 0.33 | 아니오 | +2.16 / +0.08 / -0.86 |
| Amazon_electronics | 5 | sup − TEG-orig | — | 미완료 | — | — |
| dblp | 1 | +NaQ-Feat − sup | naqfeat_l1.0 − sup | +1.33 ± 0.31 | 예 | +1.86 / +0.72 / +1.40 |
| dblp | 1 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +2.41 ± 0.25 | 예 | +2.66 / +1.60 / +2.96 |
| dblp | 1 | +CRES − sup | — | 미완료 | — | — |
| dblp | 1 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| dblp | 1 | sup − VISION | sup − vision | +4.13 ± 0.45 | 예 | +2.92 / +4.98 / +4.48 |
| dblp | 1 | sup − TEG-orig | — | 미완료 | — | — |
| dblp | 5 | +NaQ-Feat − sup | naqfeat_l0.5 − sup | +1.19 ± 0.21 | 예 | +0.78 / +1.38 / +1.42 |
| dblp | 5 | +NaQ-Diff − sup | naqdiff_l1.0 − sup | +1.82 ± 0.21 | 예 | +1.54 / +1.72 / +2.20 |
| dblp | 5 | +CRES − sup | — | 미완료 | — | — |
| dblp | 5 | +CRES − +NaQ(valid 선택) | — | 미완료 | — | — |
| dblp | 5 | sup − VISION | sup − vision | +3.67 ± 0.35 | 예 | +3.32 / +3.50 / +4.20 |
| dblp | 5 | sup − TEG-orig | — | 미완료 | — | — |

- "분명" 열은 평균 > 0 이고 > 2·SE의 기계적 적용이다. 음수 차(예: sup − VISION, Clothing·Electronics K=1)는 반대 방향으로 보면 기준을 넘는다(007 보고서).
- [추정] +NaQ식이 지도 단독보다 높은 칸이 많은 것은 pseudo-episode가 base가 아닌 노드(valid·test 클래스 노드 포함, 레이블 없음)를 학습에 쓰기 때문일 수 있다. 이 해석은 검증하지 않았다.

## 4. 축소 규칙

적용하지 않음. 003 측정(단일 실행 15–60 s, GPU당 2개 동시) 기준 전체 sweep 예상 종료가 T0+8h보다 훨씬 이르렀다. TEG-orig는 축소가 아니라 환경 구성 불가로 skip.

## 5. 돌고 있는 작업

없음(runner_all 16:16 종료).

## 6. 결정 필요 (전 항목)

1. (003) G3를 1차 불충족 → 이식 버그 수정 → 2차 충족으로 처리했다. 사전 등록 기준은 바꾸지 않았다. 재실행 통과가 등록 취지에 맞는지 확인 필요.
2. (004) G1 불통과로 008 skip. 다음 설계 방향은 사용자 판단(c가 모든 seed에서 계수가 가장 큰 근거였고, avg가 이미 c를 포함).
3. (005) Electronics의 G2 통과는 B1(s_H)이 약한 데서 오는 차이가 대부분(core − B2 +0.1 ~ +1.0%p, core − B3 ≈ 0). 비교 기준 검토 필요.
4. (005) r의 방향(ψ(u, v)의 u 우선)과 탐욕 단계 r(v, w) 방향은 Claude가 정한 구현 세부(P03에 기재).
5. (006) NaQ 재구현의 K=5 support 구성(anchor + 상위 이웃 K−1개)과 풀 U(base 제외, 원 NaQ는 전체 노드) 검토. Electronics NaQ-Diff는 pseudo-episode의 52–68%에 중복 노드.
6. (007) TEG-orig: conda 실행 파일이 없어 python 3.8 + torch 1.10.1 환경을 만들 수 없음. conda/miniforge 설치 허용 또는 대안 결정 필요.
7. (007) VISION 환경을 conda clone 대신 `/venv/cres` 기반 `--system-site-packages` venv + ogb로 만듦.
8. (007) VISION은 학습에 레이블을 쓰지 않고 전체 노드(test 클래스 노드 포함)에서 pseudo-task를 만든다(원 코드 그대로). 비교 조건 차이 판단 필요.
9. (008) G1 불통과 상태에서 CRES pilot을 G2 통과 데이터셋(Clothing·Electronics)만으로 돌릴지 판단 필요.
10. (R002·R003) 사용자 부재로 Claude가 정한 임시 기본값 전체 검토 대기.

## 7. 자원

- GPU 작업 시간 합(job_runner 기록, 동시 실행 포함 프로세스 시간 합): 120개 작업 10381 s(2.88 h). 별도 실행(004 gate1 3회 약 2.3분, 005 gate2 3회 약 1분, NaQ 이웃 표 3.8분, smoke 3회)은 제외.
- 디스크: overlay 60G 중 사용 15G(시작 7.8G), 여유 46G. `results/` 7.2G(git 제외), `records/` 31M, `splits/` 1.7M, `/workspace/scratch` 2.4M, `/venv/vision` 24M.

## 8. 참고 리포 clean 확인

| 리포 | HEAD | `git status --porcelain` 줄 수 |
|---|---|---|
| TEG-orig | `b5a8e03` | 0 |
| TEG-choi | `3b7be89` | 0 |
| NaQ | `cfe5373` | 0 |
| VISION | `0524eae` | 0 |

push: `ef30047`까지 origin/main에 push 성공(`c2a72c8..ef30047  main -> main`). 이 줄을 더한 마지막 커밋의 push 결과는 채팅 보고에 적는다.
