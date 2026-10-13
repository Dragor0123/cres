# 006 +NaQ식 arm (재구현)과 sweep

작성 2026-10-13 (야간 큐) · 등록 P04 (실행 전 커밋 `50d4d53`)

## 1. 무엇을 했는지

- `baselines/naq/generator.py`: NaQ-Feat, NaQ-Diff 재구현(refs/NaQ 코드 복사 없음). rng `22000+seed`(numpy Generator).
- `cres/teg/run.py --pseudo naq_feat|naq_diff --lam λ`: 003 백본 `train_step(sup, pseudo, lam)`. 스텝마다 지도 에피소드 1개 + pseudo-episode 1개, 두 에피소드가 같은 GCN 출력을 공유, L = L_sup + λ·L_pseudo(L_pseudo도 γ·L_N + (1−γ)·L_G). epoch 0은 원본대로 갱신 없음이며 pseudo도 만들지 않는다.
- 이웃 표 사전 계산(데이터셋 × seed × 종류 18개, 합계 3분 48초) → `results/006/<ds>/naq_<kind>_seed<s>_top9.npy`.
- sweep: `results/sweep/jobs_all.jsonl`(72개, K=1 먼저), `tools/job_runner.py --max_per_gpu 2`, GPU-A·B 교대 배정. 기록 `records/006_naq/ep_acc_<ds>_K<k>_seed<s>_naq<kind>_l<λ>.csv`, `run_meta.jsonl`.

### 원 NaQ와의 차이 (refs/NaQ `cfe5373`를 읽고 확인한 사실)

| 항목 | 원 NaQ | 이 재구현 |
|---|---|---|
| support | way마다 무작위 노드 1개(`task_generator.py` `spt_sampling`, `spt_to_sample = 1`, UMTRA식) | anchor 1개 + anchor의 상위 이웃 K−1개(K=5면 4개) |
| query | support 노드 행의 상위 q개(`query_generation_NaQ`; 학습 `q_query` 기본 10, `arg.py:23, 76`) | 상위 이웃 중 support로 쓰지 않은 다음 Q=5개 |
| 노드 풀 | `id_train` = 모든 클래스의 모든 노드(`data.py:96-98`) | U = 그 seed의 base가 아닌 노드(valid ∪ test). 이웃 후보도 U 안 |
| Feat 유사도 | 원시 특징 행 L2 정규화 후 코사인(`utils.py:33-39`) | 같음(log1p 없음) |
| Diff 유사도 | GDC `transition_matrix(normalization='sym')`(자기 루프 추가 없음) → `diffusion_matrix_exact(method='ppr', alpha=0.1)`(`utils.py:42-45`, `arg.py:45`) | 같은 정의. 역행렬 대신 멱반복 200회(잘림 오차 ≤ 0.9^200) |
| 자기 자신 | 대각 0(`utils.py:48`) | 자기 자신 제외(점수 −inf) |
| way 충돌 | 막지 않음 | 막지 않음 |
| 학습 방식 | 비지도 메타학습(ProtoNet/MAML 등, 레이블 없음) | 지도 에피소드 + λ·pseudo 에피소드(TEG 백본) |
| 동점 | `topk` | 안정 정렬(노드 id 오름차순) |

<!-- RESULTS -->
