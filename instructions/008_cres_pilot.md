# 008 — CRES pilot (조건부)

**조건: G3 통과, 그리고 G1·G2 모두 통과.** 하나라도 실패면 skip하고 이유를 기록.
실행 대상 데이터셋: G1과 G2를 **둘 다** 통과한 데이터셋만.
이 실험은 pilot이다. 설계값(R003 + 아래)은 사용자 검토 전 임시값이며, 결과는 아침에 설계 결정을 위한 자료로만 쓴다.

## 1. 생성기 — `cres/episodes.py`

- 005의 core 은행(seed·데이터셋별, m = K+Q, 선택된 τ_in) 사용.
- 한 pseudo-episode (rng `23000+seed`):
  1. core 5개 추첨, 조건 max_{i≠j} r(a_i, a_j) ≤ 0.3 (최대 50회 재추첨, 실패 시 마지막 추첨 사용하고 횟수 기록).
  2. Support: core 안에서 다른 멤버와의 평균 r이 가장 큰 K개.
  3. Query: 나머지 Q개. 단, 어떤 query q가 다른 core anchor와의 r이 자기 anchor와의 r보다 크면 그 core를 다시 추첨.
  4. "support와 다른 변이 포함" 조건은 이번 pilot에서 구현하지 않는다(보고서에 명시).
- 지역 레이블 0–4.

## 2. 학습

- 003 백본 `train_step(sup, pseudo, lam)`, λ ∈ {0.5, 1.0}, 선택 규칙은 006과 같음.
- 실행: λ 2 × (통과 데이터셋) × K{1,5} × seed 0–2. K=1 먼저. 000 §5 축소 규칙 적용.

## 3. 먼저 커밋: `docs/register/P05_cres_pilot.md`

- 비교: +CRES(선택된 λ) − +NaQ식(Feat·Diff 중 valid로 고른 쪽) 및 − 지도 단독, 고정 test 에피소드 짝지은 차(seed 0–2 합친 600개, 그리고 seed별).
- 예측(Claude, 근거 약함): +CRES > +NaQ식이 dblp를 제외한 통과 데이터셋에서 "분명"(평균 > 0, > 2·SE).
- pilot이므로 이 예측의 성패로 설계를 확정하지 않는다고 명시.

## 4. 산출물

`records/008_cres_pilot/ep_acc_*.csv`, 생성기 통계(재추첨 횟수, query 제외로 인한 재추첨 비율), `reports/008_cres_pilot.md`.
