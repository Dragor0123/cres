# 005 — 관문 2: Pseudo-Class Core가 같은 크기의 유사도 top-K pseudo-class보다 순수한가 (G2)

GPU-A 짧게. 학습 없음. 004의 ψ·C1 calibrator(seed별)를 쓴다. 004가 실패해도 C1이 만들어졌으면 실행한다(G2는 G1과 독립 판정).

## 0. 먼저 커밋: `docs/register/P03_gate2_core_purity.md` (§3·§4)

## 1. 풀과 레이블 규칙

- 풀 U = base가 아닌 노드(valid ∪ test 노드). 구성에는 레이블을 쓰지 않는다.
- τ 선택은 **valid anchor**로, 최종 지표는 **test anchor**로.
- 순도 정의: core의 anchor 외 멤버 중 anchor와 같은 클래스 비율(사용자 기존 "다른 클래스 노드 비율" 정의와 같은 방향).

## 2. Core 구성 (anchor a, 크기 m)

1. 후보: U 안에서 r(a,·) 상위 30개(r는 C1, 필요한 쌍은 ψ 함수로 계산).
2. 탐욕 추가: 멤버 집합 S = {a}. 남은 후보 중 S와의 평균 r이 가장 큰 v를 고른다. min_{w∈S} r(v,w) ≥ τ_in이면 추가, 아니면 그 후보를 버리고 다음 후보.
3. |S| = m이 되면 채택, 후보가 떨어지면 anchor 기각.
- m ∈ {6 (K=1, Q=5), 10 (K=5, Q=5)}.
- τ_in ∈ {0.3, 0.5, 0.7}. 선택: valid anchor에서 채택률 ≥ 0.3인 값 중 평균 순도 최고(동률이면 작은 τ). seed·m·데이터셋마다.
- **모든 U 노드를 anchor로 시도**한다(anchor 선택 편향 없이 채택률만 남게).

## 3. 비교 (같은 anchor에서 짝지음)

- B1: s_H 상위 (m−1)개 (사용자 기존 top-K pseudo-class와 같은 종류)
- B2: s_X 상위 (m−1)개 (NaQ-Feat 방식)
- B3: r 상위 (m−1)개, 일관성 검사 없음 (r 순위 효과와 일관성 검사 효과를 나눠 보기 위함)
- CRES core
- 채택된 anchor에서 네 방법을 짝지어 비교. 기각된 anchor에서의 B1 순도와 전체 anchor B1 순도도 따로 적는다(채택이 쉬운 anchor만 남긴 효과를 드러내기 위함).

## 4. 판정 (P03)

- **G2 데이터셋 통과** (m = 10 기준, m = 6은 보고): seed 0–2 모두에서 [CRES core − B1] 순도의 anchor 짝지은 차가 평균 > 0 이고 > 2·SE, **그리고** 선택된 τ_in에서 test anchor 채택률 ≥ 0.3.
- **G2 통과**: 3개 중 2개 이상. dblp 따로 기재.
- 예측(Claude, 근거 약함): 순도는 오르지만 dblp는 채택률 조건이 빠듯할 것.

## 5. 보조: way 충돌률 (판정 아님)

- 충돌 = 한 pseudo-episode의 5개 way 중 둘 이상의 anchor가 같은 실제 클래스.
- 1000개 pseudo-episode, rng `24000+seed`, test anchor 기준:
  - NaQ식: 무작위 anchor 5개.
  - CRES: 채택된 core 5개, 조건 max_{i≠j} r(a_i, a_j) ≤ τ_out(= 0.3), 최대 50회 재추첨.
- 두 방법의 충돌률, CRES의 재추첨 실패율.

## 6. 산출물

- core 은행(채택된 core 목록, anchor, 멤버, 선택된 τ_in) → `records/005_gate2/core_bank_<dataset>_seed<s>_m<m>.json` (008이 사용; 5 MB 넘으면 results/에만 두고 경로 기록).
- `reports/005_gate2_core_purity.md`: τ 선택표, 순도 비교표, 채택률, 충돌률, 판정.
