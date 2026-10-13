# 004 — 관문 1: base 레이블로 배운 관계 신뢰도 r이 안 본 클래스 쌍에서 원시 유사도보다 나은가 (G1)

GPU-A 짧게 사용(kNN·k-means). 학습 없는 관문(GNN 학습 없음). 설계값은 R003 임시 기본값.

## 0. 먼저 커밋할 것

1. `docs/register/R003_cres_design_defaults.md` — 아래 §1·§2의 설계값을 "임시 기본값(사용자 부재, Claude 제안)"으로 기록.
2. `docs/register/P02_gate1_calibrator.md` — §4의 지표·판정 기준·예측.

## 1. 관계 근거 ψ(u,v) — `cres/relations.py`

데이터셋마다 한 번 계산(레이블 사용 없음, seed와 무관):

- 특징: X' = L2정규화(log1p(X)). 구조 평활: Â = D^−½(A+I)D^−½, H = L2정규화(Â²X').
- 후보 쌍: 노드 u마다 s_X 상위 L=50, s_H 상위 L=50의 합집합(방향 쌍 u→v, 자기 자신 제외). GPU에서 블록 행렬곱으로 계산.
- ψ 구성(쌍마다):
  1. s_X = cos(X'_u, X'_v)
  2. s_H = cos(H_u, H_v)
  3. 순위: log(1+rank_X(v|u)), log(1+rank_H(v|u)), 역방향 log(1+rank_X(u|v)), log(1+rank_H(u|v)) (목록 밖이면 rank = L+1)
  4. c(u,v) = M개 클러스터링에서 같은 클러스터 비율. 뷰 {X'의 TruncatedSVD 128차원, H의 TruncatedSVD 128차원} × k ∈ {25, 50, 100, 200} × 재시작 2회 = M 16. GPU k-means 50회 반복, 초기화 rng `20000+0`(seed 무관, 데이터셋마다 고정).
  5. 홉: 1[(u,v) ∈ E], 1[u,v가 2홉 이내]
- 임의 쌍에 대해서도 ψ를 계산할 수 있는 함수를 제공(005에서 core 내부 쌍에 필요).
- 캐시: `results/004/<dataset>/psi_*.pt`(git 제외).

## 2. Calibrator — seed마다

- 학습 쌍: 후보 쌍 중 **두 끝이 모두 base 노드**인 것(그 seed의 분할). 레이블 1[y_u = y_v].
- 표준화: base 쌍으로 평균·분산 적합.
- C1(주): 로지스틱 회귀(L2). C ∈ {0.01, 0.1, 1, 10} 중 valid–valid 쌍의 AUROC 최고(동률이면 작은 C).
- C2(보조): MLP 2층 × 32, 초기화 rng `21000+seed`, valid AUROC로 조기 종료.
- valid–valid 쌍은 모델 선택에만, test–test 쌍은 지표에만.

## 3. 비교 대상

s_X 단독, s_H 단독, c 단독, 단순 평균 avg = (s_X + s_H + c)/3.

## 4. 지표와 판정 (P02에 등록)

test–test 후보 쌍에서:
- 주 지표: **anchor top-10 순도**. test 노드 u마다(test–test 후보 ≥ 10개인 것만) 점수 상위 10개 중 u와 같은 클래스 비율. 방법 간 차는 anchor별로 짝지어 계산.
- 보조: 쌍 단위 AUROC, AP; ECE(정보용 — test의 양성 비율은 base와 다르므로 판정에 쓰지 않음); 제외된 anchor 수.
- 정합성 확인(판정 아님): s_H top-10 순도를 사용자 기존 수치(학습 없는 Â²X top-10 순도 Clothing 0.846, Electronics 0.682, dblp 0.584)와 나란히 적는다. 정의 차이(후보 범위가 test–test로 제한됨)를 명시.
- **G1 데이터셋 통과**: seed 0, 1, 2 **모두**에서 [C1 순도 − max(s_X, s_H, avg 순도)]의 anchor 짝지은 차가 평균 > 0 이고 > 2·SE. (max는 test에서 가장 좋은 비교 대상 = 보수적 기준.)
- **G1 통과**: 3개 데이터셋 중 2개 이상 통과. dblp 결과는 통과 여부와 관계없이 따로 적는다.
- 한계(등록 문서에 기재): 한 노드가 여러 anchor의 이웃으로 겹치므로 anchor들이 독립이 아니며 SE가 작게 나올 수 있다.
- 예측(Claude, 근거 약함): G1 통과, 다만 dblp는 차이가 가장 작을 것.

## 5. 산출물

- `records/004_gate1/`: (dataset, seed)별 방법별 순도·AUROC·AP 표, anchor별 순도 CSV(용량 규칙 준수), C1 계수와 선택된 C.
- `reports/004_gate1_calibrator.md`: 표, 판정, C1 계수(어떤 근거에 무게가 실렸는지 — 사실로만), 소요 시간.
