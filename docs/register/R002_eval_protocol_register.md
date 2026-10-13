# R002 평가 프로토콜 (001 결정 필요 1–4)

- 기록 2026-10-13 · 상태: 임시 기본값 (사용자 부재로 Claude 제안, 사용자 검토 대기)

1. 분할 단위: TEG-choi와 같이 seed별 분할 (001 결정 필요 1의 (b)).
   - 주 분석 seed: 0, 1, 2 (외부 기록과 대조된 범위).
   - 근거: TEG-choi·EATS 결과와 같은 분할에서 비교 가능. calibrator는 seed별 base 레이블로 따로 학습.
2. 고정 에피소드: TEG-choi `--fixed_eval`과 같은 규칙으로 생성해 파일로 저장.
   - test 200개 `random.Random(9000 + seed)`, valid 100개 `random.Random(9100 + seed)`.
   - 5-way, K ∈ {1, 5}, query 5. 절차는 TEG-choi `model.py:366–377`과 같은 순서.
   - (dataset, seed, K)마다 파일 하나. 근거: TEG-choi 결과와 에피소드 단위 대조 가능.
3. 파일 형식: JSON. `splits/episodes/<dataset>_seed<s>_K<k>.json`.
4. seed 3–9: 이번 단계에서 쓰지 않음.
5. 모델 선택: TEG-choi와 같이 valid 최고 에폭 체크포인트(동점은 나중 에폭) → 고정 test 에피소드로 평가.
