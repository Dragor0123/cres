# 2차 큐 작업 목록(jsonl) 생성. 사용: /venv/cres/bin/python tools/make_jobs_queue2.py <item> >> results/queue2/jobs.jsonl
# item: 011 | 012 | 011allpool | 013 | 014. K=1 먼저, GPU-A·B 교대.
import json
import sys

GPUS = ["GPU-16eb803b-cabc-049e-0a5c-c5e7667128b4", "GPU-c7939e10-56dd-ef42-8af1-3833c860307b"]
DS = ["Amazon_clothing", "Amazon_electronics", "dblp"]
PY = "/venv/cres/bin/python"


def emit(rows):
    for i, (jid, cmd) in enumerate(rows):
        print(json.dumps({"id": jid, "gpu": GPUS[i % 2], "log": f"results/queue2/logs/{jid}.log", "cmd": cmd}))


def teg(ds, k, s, pseudo, lam, arm, item, rec, extra=""):
    jid = f"{item}_{arm}_{ds}_K{k}_s{s}"
    return jid, (f"{PY} -m cres.teg.run --dataset {ds} --shot {k} --seed {s} --pseudo {pseudo} --lam {lam} --arm {arm} "
                 f"--out_dir results/{item}/runs/{jid} --records_dir {rec}{extra}")


item = sys.argv[1]
rows = []
for k in (1, 5):
    for ds in DS:
        if item == "014" and ds == "dblp":
            continue
        for s in (0, 1, 2):
            if item == "011":
                for kind in ("feat", "diff"):
                    for lam in ("0.5", "1.0"):
                        rows.append(teg(ds, k, s, f"naq_{kind}", lam, f"naq{kind}_l{lam}", "011", "records/011_naq_v2"))
            elif item == "012":
                for lam in ("0.5", "1.0"):
                    rows.append(teg(ds, k, s, "sup2", lam, f"sup2_l{lam}", "012", "records/012_sup2"))
            elif item == "011allpool":
                lam = json.load(open("records/011_naq_v2/lambda_selected.json"))[f"{ds}_K{k}_naq_feat"]
                rows.append(teg(ds, k, s, "naq_feat", lam, "naqfeat_allpool", "011", "records/011_naq_v2", " --pool all"))
            elif item == "014":
                for lam in ("0.5", "1.0"):
                    rows.append(teg(ds, k, s, "cres", lam, f"cres_l{lam}", "014", "records/014_cres_pilot"))
            elif item == "013":
                lam = json.load(open("records/011_naq_v2/lambda_selected.json"))[f"{ds}_K{k}_naq_feat"]
                for rho in ("0", "15", "30", "45", "0_nocollide"):
                    arm = f"diag_rho{rho}"
                    jid = f"013_{arm}_{ds}_K{k}_s{s}"
                    rows.append((jid, f"{PY} -m cres.diag.purity_curve --dataset {ds} --shot {k} --seed {s} --rho {rho} --lam {lam} "
                                      f"--arm {arm} --out_dir results/013/runs/{jid} --records_dir records/013_purity_diag"))
emit(rows)
