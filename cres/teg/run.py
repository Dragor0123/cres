# TEG 이식본 실행 (003). 한 프로세스 = (dataset, K, seed, arm) 하나.
# 사용: CUDA_VISIBLE_DEVICES=<UUID> /venv/cres/bin/python -m cres.teg.run --dataset Amazon_clothing --shot 1 --seed 0 \
#         --arm sup --out_dir results/003/runs/<id> [--records_dir records/003_teg_port]
# 출력: out_dir/run.json, out_dir/ep_acc.csv (mode, ep_idx, acc; 고정 test 200 + valid 100)
#       records_dir/ep_acc_<dataset>_K<k>_seed<s>_<arm>.csv, records_dir/run_meta.jsonl (한 줄 추가)
import argparse
import json
import os
import socket
import subprocess
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cres.data import ROOT  # noqa: E402
from cres.teg.trainer import TEGTrainer  # noqa: E402


def git_head():
    try:
        return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return None


def build_pseudo(args, trainer):
    """pseudo-episode 생성기. 반환: 인자 없는 callable → (support ids, query ids, 지역 레이블 tensor) 또는 None."""
    if args.pseudo == "none":
        return None
    if args.pseudo in ("naq_feat", "naq_diff"):
        from baselines.naq.generator import NaQGenerator
        import numpy as np
        # 풀 U = base가 아닌 노드(분할 파일의 base 클래스로 제외). 생성기는 레이블을 받지 않는다.
        U = np.where(~np.isin(trainer.labels_np, trainer.class_list_train))[0]
        g = NaQGenerator(args.dataset, args.seed, args.shot, args.qry, kind=args.pseudo.split("_")[1], U=U)
    elif args.pseudo == "cres":
        from cres.episodes import CRESGenerator
        g = CRESGenerator(args.dataset, args.seed, args.shot, args.qry)
    else:
        raise ValueError(args.pseudo)
    dev = trainer.device

    def fn():
        sup, qry, y = g.sample()
        return sup, qry, torch.LongTensor(y).to(dev)

    fn.gen = g
    return fn


def trainer_split(trainer):
    return {"base": trainer.class_list_train, "valid": trainer.class_list_valid, "test": trainer.class_list_test}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--qry", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--lam", type=float, default=0.0)
    ap.add_argument("--pseudo", default="none", choices=["none", "naq_feat", "naq_diff", "cres"])
    ap.add_argument("--arm", default="sup")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--records_dir", default=None)
    a = ap.parse_args()
    t0 = time.time()
    torch.set_num_threads(3)  # TEG-choi main.py:16과 같음
    os.makedirs(a.out_dir, exist_ok=True)
    tr = TEGTrainer(a.dataset, a.seed, a.shot, qry=a.qry, epochs=a.epochs, episodes=a.episodes, device="cuda:0")
    t_init = time.time() - t0
    pseudo_fn = build_pseudo(a, tr)
    res = tr.train(pseudo_fn, a.lam)
    eps = json.load(open(os.path.join(ROOT, "splits", "episodes", f"{a.dataset}_seed{a.seed}_K{a.shot}.json")))
    assert eps["Q"] == a.qry and eps["K"] == a.shot
    acc_test = tr.eval_fixed(eps["test"]["episodes"])
    acc_valid = tr.eval_fixed(eps["valid"]["episodes"])
    rows = [("test", i, x) for i, x in enumerate(acc_test)] + [("valid", i, x) for i, x in enumerate(acc_valid)]
    csv = "mode,ep_idx,acc\n" + "".join(f"{m},{i},{x:.6f}\n" for m, i, x in rows)
    open(os.path.join(a.out_dir, "ep_acc.csv"), "w").write(csv)
    meta = {
        "dataset": a.dataset, "K": a.shot, "seed": a.seed, "arm": a.arm, "pseudo": a.pseudo, "lam": a.lam, "Q": a.qry,
        "epochs": a.epochs, "episodes": a.episodes, "git": git_head(),
        "gpu": os.environ.get("CUDA_VISIBLE_DEVICES"), "gpu_name": torch.cuda.get_device_name(0), "host": socket.gethostname(),
        "sec_total": time.time() - t0, "sec_init": t_init, "max_mem_alloc_MB": torch.cuda.max_memory_allocated() / 2**20,
        "best_acc_valid": res["best_acc_valid"], "best_epoch_valid": res["best_epoch_valid"], "ckpt_epoch": res["ckpt_epoch"],
        "test_acc_at_best_valid": res["test_acc_at_best_valid"],
        "fixed_test_acc": sum(acc_test) / len(acc_test), "fixed_valid_acc": sum(acc_valid) / len(acc_valid),
        "episodes_sha1": {"test": eps["test"]["sha1"], "valid": eps["valid"]["sha1"]},
    }
    if pseudo_fn is not None and hasattr(pseudo_fn.gen, "stats"):
        meta["pseudo_stats"] = pseudo_fn.gen.stats()
    json.dump({**meta, "history": res["history"]}, open(os.path.join(a.out_dir, "run.json"), "w"), indent=1)
    if a.records_dir:
        os.makedirs(a.records_dir, exist_ok=True)
        open(os.path.join(a.records_dir, f"ep_acc_{a.dataset}_K{a.shot}_seed{a.seed}_{a.arm}.csv"), "w").write(csv)
        with open(os.path.join(a.records_dir, "run_meta.jsonl"), "a") as f:
            f.write(json.dumps(meta) + "\n")
    print("FIXED_TEST", meta["fixed_test_acc"], "FIXED_VALID", meta["fixed_valid_acc"], "SEC", meta["sec_total"])


if __name__ == "__main__":
    main()
