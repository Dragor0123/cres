# TEG-choi 클래스 분할 재현 (지시서 001 작업 3-3).
#
# 출처: refs/TEG-choi (commit 3b7be89, 브랜치 erasure_diagnosis)
#   - utils.py:13        valid_num_dic
#   - utils.py:30-34     train_class / class_list_test 구성 (list(set(Label)))
#   - utils.py:67-69     class_list_valid = random.sample(train_class, valid_num); base = 차집합
#   - utils.py:259-267   seed_everything: random.seed(seed) (전역 random)
#   - main.py:360-362    seed_everything(set_seed) 직후 main() -> teg_trainer -> embedder -> load_data
#   load_data 이전에 전역 random 호출이 없으므로, 분할은 random.seed(seed) 직후 첫 random.sample 결과다.
# 원본 load_data는 TEG-orig(MIT, sung-won-kim/TEG)의 utils.py와 같은 로직이다.
#
# 이 스크립트는 레이블을 읽어 클래스 목록과 그룹별 노드 수만 계산한다(학습·에피소드 생성 없음).
import argparse
import json
import os
import random
import sys

import numpy as np
import scipy.io as sio

VALID_NUM = {"Amazon_clothing": 17, "Amazon_electronics": 36, "dblp": 27}  # TEG-choi utils.py:13

# 검증 기준 1: refs/TEG-choi/reports/T13_dim_collapse.md 표 1 (n = 그룹 노드 수, C = 클래스 수).
#   열 이름은 "n (seed 0/1/2)"이지만 값은 sorted({seed 0,1,2의 n})이다(refs/TEG-choi/tools/analyze_t13.py:128).
#   그래서 seed 0-2의 n을 정렬해 비교한다(seed별 대응은 확인 불가).
# 검증 기준 2: refs/TEG-choi/reports/T16a_impl_facts.md G3(c) 표, Clothing seed 0: base 11720, valid 3839, test 9360.
# 검증 기준 3: 같은 보고서 J2, seed 0: 클래스 0은 Clothing·Electronics에서 base, dblp에서 test.
SEED0_CLOTHING = {"base": 11720, "valid": 3839, "test": 9360}
CLASS0_GROUP_SEED0 = {"Amazon_clothing": "class_list_train", "Amazon_electronics": "class_list_train", "dblp": "class_list_test"}
EXPECTED = {
    "Amazon_clothing": {"base_n": [10618, 11067, 11720], "valid_n": [3839, 4492, 4941], "test_n": 9360, "C": (40, 17, 20)},
    "dblp": {"base_n": [23178, 23503, 24023], "valid_n": [6902, 7422, 7747], "test_n": 9747, "C": (80, 27, 30)},
    "Amazon_electronics": {"base_n": [21843, 23117, 23562], "valid_n": [8540, 8985, 10259], "test_n": 10216, "C": (91, 36, 40)},
}


def teg_split(data_dir, ds, seed):
    d_tr = sio.loadmat(f"{data_dir}/{ds}/{ds}_train.mat")
    d_te = sio.loadmat(f"{data_dir}/{ds}/{ds}_test.mat")
    # utils.py:31, :34 와 같은 식
    train_class = list(set(d_tr["Label"].reshape((1, len(d_tr["Label"])))[0]))
    class_list_test = list(set(d_te["Label"].reshape((1, len(d_te["Label"])))[0]))
    random.seed(seed)  # seed_everything 의 전역 random 부분
    class_list_valid = random.sample(train_class, VALID_NUM[ds])  # utils.py:67
    class_list_train = list(set(train_class).difference(set(class_list_valid)))  # utils.py:69
    # 노드 수 (utils.py:36-38 의 labels 배열과 같은 방식)
    n = max(d_tr["Index"].max(), d_te["Index"].max()) + 1
    labels = np.zeros(n)
    labels[d_tr["Index"]] = d_tr["Label"].reshape(1, -1)
    labels[d_te["Index"]] = d_te["Label"].reshape(1, -1)
    to_int = lambda xs: [int(x) for x in xs]
    count = lambda cs: int(np.isin(labels, np.array(cs, dtype=float)).sum())
    return {
        "class_list_train": to_int(class_list_train),
        "class_list_valid": to_int(class_list_valid),
        "class_list_test": to_int(class_list_test),
        "n_nodes": {"base": count(class_list_train), "valid": count(class_list_valid), "test": count(class_list_test)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="data")
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--out_dir", default="splits")
    a = ap.parse_args()
    lo, hi = map(int, a.seeds.split("-"))
    ok_all = True
    for ds in ["Amazon_clothing", "Amazon_electronics", "dblp"]:
        out = {
            "dataset": ds,
            "source": "refs/TEG-choi@3b7be89 utils.py:67-69 (random.seed(seed); random.sample(train_class, valid_num))",
            "note": "TEG-choi split depends on seed. Classes are integer label ids from *.mat Label.",
            "valid_num": VALID_NUM[ds],
            "verified_against": "TEG-choi reports T13 table 1 (sorted n, seeds 0-2), T16a G3(c) (Clothing seed 0 n), T16a J2 (class 0, seed 0)",
            "seeds": {},
        }
        e = EXPECTED[ds]
        for s in range(lo, hi + 1):
            sp = teg_split(a.data_dir, ds, s)
            sp["verified"] = None
            out["seeds"][str(s)] = sp
            print(ds, s, sp["n_nodes"], len(sp["class_list_train"]), len(sp["class_list_valid"]),
                  len(sp["class_list_test"]))
        checks = {}
        if all(str(s) in out["seeds"] for s in (0, 1, 2)):
            sps = [out["seeds"][str(s)] for s in (0, 1, 2)]
            checks["T13_base_n_sorted"] = sorted(x["n_nodes"]["base"] for x in sps) == e["base_n"]
            checks["T13_valid_n_sorted"] = sorted(x["n_nodes"]["valid"] for x in sps) == e["valid_n"]
            checks["T13_test_n"] = all(x["n_nodes"]["test"] == e["test_n"] for x in sps)
            checks["T13_C"] = all((len(x["class_list_train"]), len(x["class_list_valid"]), len(x["class_list_test"])) == e["C"] for x in sps)
        if "0" in out["seeds"]:
            s0 = out["seeds"]["0"]
            checks["T16a_J2_class0_seed0"] = 0 in s0[CLASS0_GROUP_SEED0[ds]]
            if ds == "Amazon_clothing":
                checks["T16a_G3c_seed0_counts"] = s0["n_nodes"] == SEED0_CLOTHING
        out["checks"] = checks
        print(ds, "checks", checks)
        ok_all &= all(checks.values())
        for s in (0, 1, 2):
            if str(s) in out["seeds"]:
                out["seeds"][str(s)]["verified"] = "T13 sorted counts" + (" + T16a seed-0 counts" if (s == 0 and ds == "Amazon_clothing") else "")
        os.makedirs(a.out_dir, exist_ok=True)
        with open(os.path.join(a.out_dir, f"{ds}_class_split.json"), "w") as f:
            json.dump(out, f, indent=1)
    print("ALL_VERIFIED" if ok_all else "VERIFICATION_FAILED")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
