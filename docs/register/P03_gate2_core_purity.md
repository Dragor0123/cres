# P03 관문 2: Pseudo-Class Core 순도 (G2) — 사전 등록

- 등록 2026-10-13 (야간 큐, 005 실행 전) · 지시서 `instructions/005_gate2_core_purity.md` §3·§4 · 설계값 R003 + 지시서
- 004 결과(G1 미통과)를 본 뒤 등록하지만, 지시서 §0에 따라 G2는 G1과 독립 판정이며 기준·값은 지시서 그대로다.

## 구성 (지시서 §1·§2)

- 풀 U = base가 아닌 노드(그 seed의 valid ∪ test 노드). 구성에 레이블을 쓰지 않는다. r = 그 seed의 C1 확률(004).
- Core(anchor a, 크기 m): U 안 r(a,·) 상위 30개 후보 → S = {a}에서 탐욕 추가(남은 후보 중 S와의 평균 r 최대인 v, min_{w∈S} r(v,w) ≥ τ_in이면 추가, 아니면 버림) → |S| = m이면 채택, 후보가 떨어지면 기각.
- m ∈ {6, 10}, τ_in ∈ {0.3, 0.5, 0.7}. τ 선택: valid anchor에서 채택률 ≥ 0.3인 값 중 평균 순도 최고(동률이면 작은 τ), seed·m·데이터셋마다. 모든 U 노드를 anchor로 시도.
- 순도 = core의 anchor 외 멤버 중 anchor와 같은 클래스 비율.
- 비교(같은 anchor 짝지음): B1 s_H 상위 (m−1), B2 s_X 상위 (m−1), B3 r 상위 (m−1)(일관성 검사 없음), CRES core. 기각 anchor의 B1 순도, 전체 anchor B1 순도도 기재.

## 구현 세부 (지시서에 값이 없어 Claude가 정함)

- r의 방향: r(a, v)는 ψ(a, v)(a가 첫 번째)에 C1을 적용한 값. 탐욕 단계의 r(v, w)는 v(후보)가 첫 번째. ψ의 순위 특징이 방향을 가지므로 r은 비대칭일 수 있다.
- "U 안 r(a,·) 상위 30개", B1·B2·B3의 상위 목록은 U 전체(a 제외)에서 정확히 계산한다(후보 쌍 목록으로 제한하지 않음). 동점은 노드 id 오름차순.
- 충돌 시뮬레이션의 anchor 사이 조건 max_{i≠j} r(a_i, a_j)는 두 방향 모두 포함.

## 판정 (P03)

- **G2 데이터셋 통과** (m = 10 기준, m = 6은 보고만): seed 0–2 모두에서 [CRES core − B1] 순도의 test anchor 짝지은 차가 평균 > 0 이고 평균 > 2·SE, **그리고** 선택된 τ_in에서 test anchor 채택률 ≥ 0.3.
- **G2 통과**: 3개 중 2개 이상. dblp는 따로 기재.

## 보조 (판정 아님)

way 충돌률: 1000개 pseudo-episode, rng `24000+seed`, test anchor 기준. NaQ식 = 무작위 test anchor 5개, CRES = 채택된 test core 5개 + max_{i≠j} r(a_i, a_j) ≤ 0.3(최대 50회 재추첨). 두 방법의 충돌률, CRES 재추첨 실패율.

## 예측 (Claude, 근거 약함)

순도는 오르지만 dblp는 채택률 조건이 빠듯할 것.
