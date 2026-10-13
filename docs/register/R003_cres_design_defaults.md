# R003 CRES 설계 기본값 (관계 근거 ψ, calibrator)

- 기록 2026-10-13 (야간 큐, 004 실행 전) · 상태: **임시 기본값 (사용자 부재로 Claude 제안, 사용자 검토 대기)**
- 출처: `instructions/004_gate1_calibrator.md` §1·§2. 값은 지시서 그대로이며 실행 중 바꾸지 않는다.

## 1. 관계 근거 ψ(u, v) — `cres/relations.py` (레이블 사용 없음, seed 무관, 데이터셋마다 한 번)

- 특징: X' = L2정규화(log1p(X)). 구조 평활: Â = D^−½(A+I)D^−½, H = L2정규화(Â²X').
- 후보 쌍: 노드 u마다 s_X 상위 L = 50, s_H 상위 L = 50의 합집합(방향 쌍 u→v, 자기 자신 제외). GPU 블록 행렬곱.
- ψ 구성(쌍마다):
  1. s_X = cos(X'_u, X'_v)
  2. s_H = cos(H_u, H_v)
  3. 순위: log(1+rank_X(v|u)), log(1+rank_H(v|u)), 역방향 log(1+rank_X(u|v)), log(1+rank_H(u|v)) (목록 밖이면 rank = L+1)
  4. c(u, v) = M개 클러스터링에서 같은 클러스터 비율. 뷰 {X'의 TruncatedSVD 128차원, H의 TruncatedSVD 128차원} × k ∈ {25, 50, 100, 200} × 재시작 2회 = M 16. GPU k-means 50회 반복, 초기화 rng `20000+0`(seed 무관, 데이터셋마다 고정).
  5. 홉: 1[(u, v) ∈ E], 1[u, v가 2홉 이내]
- 임의 쌍의 ψ 계산 함수 제공(005 core 내부 쌍).
- 캐시: `results/004/<dataset>/psi_*.pt`(git 제외).

## 2. Calibrator — seed마다

- 학습 쌍: 후보 쌍 중 두 끝이 모두 base 노드(그 seed 분할). 레이블 1[y_u = y_v].
- 표준화: base 쌍으로 평균·분산 적합.
- C1(주): 로지스틱 회귀(L2). C ∈ {0.01, 0.1, 1, 10} 중 valid–valid 쌍 AUROC 최고(동률이면 작은 C).
- C2(보조): MLP 2층 × 32, 초기화 rng `21000+seed`, valid AUROC로 조기 종료.
- valid–valid 쌍은 모델 선택에만, test–test 쌍은 지표에만.

## 3. 구현에서 정한 세부(지시서에 값이 없어 Claude가 정함, 검토 대상)

- 코사인 동점·순위: 순위는 1부터(가장 가까운 이웃 = 1). 자기 자신은 순위 계산에서 뺀다.
- "2홉 이내" = (A + A²)의 비대각 원소 > 0 (자기 루프 제외, 1홉 포함).
- k-means: 초기 중심 = rng로 뽑은 서로 다른 노드 k개(재시작마다 다른 추첨), 유클리드 거리, 50회 고정 반복. TruncatedSVD는 sklearn `randomized`, `random_state = 20000`.
- 로지스틱 회귀: sklearn `LogisticRegression(penalty="l2", solver="lbfgs", max_iter=1000)`. 학습 쌍이 많으면 rng `21000+seed`로 최대 200,000쌍 표본 추출(양성 전부 + 음성 표본은 아님 — 무작위 균등 표본). valid–valid 쌍 AUROC 계산도 같은 방식으로 최대 200,000쌍.
- MLP: 은닉 32 × 2층(ReLU), Adam lr 1e-3, 배치 4096, 최대 50 에폭, valid AUROC가 5 에폭 연속 개선되지 않으면 중단, 최고 valid 시점 가중치 사용.
