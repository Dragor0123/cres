# 007 — 공식 베이스라인 어댑터: VISION (우선), TEG-orig (후순위)

R001의 어댑터 정의를 따른다: 공식 코드의 모델·학습 로직은 그대로, **클래스 분할과 고정 test 에피소드만 우리 파일에서 읽게** 한다. refs는 읽기 전용이므로 `/workspace/scratch/<리포>-run/`으로 복사한 사본에 어댑터를 붙이고, 어댑터 소스와 사본 대비 diff를 `baselines/<이름>/`에 커밋한다.

## 1. VISION

1. 환경: 먼저 `conda create -n vision --clone cres` 후 `pip install ogb`로 시도. import·실행이 안 되면 VISION README대로(python 3.8, torch 2.4.1 + pytorch-cuda 11.8, 해당 PyG wheel) 새로 만든다. 어느 쪽으로 했는지 기록.
2. 코드를 읽고 사실로 기록: 학습에 레이블을 쓰는지(쓴다면 어떤 클래스의 레이블), pseudo-task 생성 방식, 모델 선택 방식, 지원 데이터셋.
3. 어댑터:
   - 우리 데이터 로더(.mat + edge list)로 features·adjacency를 넘긴다.
   - 레이블을 쓰는 경로가 있으면 base 클래스(seed별 분할)만 보이게 한다.
   - 평가: `splits/episodes/*_seed<s>_K<k>.json`의 test 에피소드. 모델 선택이 있으면 valid 에피소드 파일 사용.
   - 하이퍼파라미터: VISION 기본값. 데이터셋별 값이 없으면 기본값 그대로 쓰고 기록.
4. 모델·학습 로직을 바꿔야만 돌아가는 경우: 바꾸지 말고 "결정 필요"에 적고 멈춘다.
5. 실행: 3 데이터셋 × K{1,5} × seed 0–2 = 18 (K=1 먼저). 비어 있는 GPU에.

## 2. TEG-orig (시간이 남을 때만, 000 §5 축소 1순위)

- 환경: python 3.8.13, torch 1.10.1 **cu113 빌드**(3090은 cu102 불가), torch-geometric 2.0.3 + 해당 wheel.
- 어댑터: 분할 json + 고정 에피소드 json 읽기. 3 데이터셋 × K{1,5} × seed 0–2.
- 목적: 003 이식본·TEG-choi와의 일치 확인(같은 에피소드에서 정확도 비교).

## 3. 산출물

`records/007_<이름>/ep_acc_*.csv`, `baselines/<이름>/`(어댑터 + diff), `reports/007_official_baselines.md`(환경, 코드 사실, 어댑터 변경 줄, 실행 현황).
