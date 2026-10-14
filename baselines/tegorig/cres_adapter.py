# CRES 어댑터 (R001, 015): TEG-orig의 모델·학습 로직은 그대로 두고 다음만 더한다.
#   1. 클래스 분할: /workspace/CRES/splits/<ds>_class_split.json (원본 random.sample 호출은 순서 유지를 위해 그대로 실행하고 결과를 대조)
#   2. 평가: valid 최고 에폭(동점은 나중 에폭, TEG-choi --fixed_eval 규칙)의 가중치를 복사해 두고, 학습 후
#      /workspace/CRES/splits/episodes/<ds>_seed<s>_K<k>.json 의 고정 test 200 / valid 100 에피소드로 평가.
# 출처: refs/TEG-orig (sung-won-kim/TEG, b5a8e03, MIT).
import json

CRES = "/workspace/CRES"
STATE = {"seed": None, "split_check": None}


def override_split(dataset, train, valid, test):
    sp = json.load(open(f"{CRES}/splits/{dataset}_class_split.json"))["seeds"][str(STATE["seed"])]
    same = ([int(c) for c in valid] == sp["class_list_valid"] and sorted(int(c) for c in train) == sorted(sp["class_list_train"])
            and sorted(int(c) for c in test) == sorted(sp["class_list_test"]))
    STATE["split_check"] = {"valid_order_equal": [int(c) for c in valid] == sp["class_list_valid"],
                            "train_order_equal": [int(c) for c in train] == sp["class_list_train"],
                            "test_order_equal": [int(c) for c in test] == sp["class_list_test"], "sets_equal": same}
    return sp["class_list_train"], sp["class_list_valid"], sp["class_list_test"]


def fixed_episodes(dataset, seed, k):
    d = json.load(open(f"{CRES}/splits/episodes/{dataset}_seed{seed}_K{k}.json"))
    assert d["K"] == k
    return d
