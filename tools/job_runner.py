# 작업 실행기 (000 §4, 003 §2).
# 사용: nohup /venv/cres/bin/python tools/job_runner.py --jobs <jobs.jsonl> --state <state.jsonl> --max_per_gpu 1 > <runner.log> 2>&1 &
# jobs.jsonl 한 줄 = {"id", "cmd", "gpu"(UUID), "log"}. cmd는 리포 루트에서 bash -c로 실행, CUDA_VISIBLE_DEVICES=gpu.
# state.jsonl: 이벤트 append (start / done / failed / retry). 같은 jobs를 다시 넣으면 done·failed인 id는 건너뛴다.
# 실패 시 같은 설정으로 1회 재시도(로그 <log>_retry1), 다시 실패하면 failed (000 §6).
# --stop_after: 이 UTC 시각(ISO) 이후 새 작업을 시작하지 않는다(000 §5 T0+8h).
# --jobs 파일은 루프마다 다시 읽으므로, 실행 중에 줄을 추가하면 대기열에 들어간다.
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def now():
    return dt.datetime.now(dt.timezone.utc)


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def append(p, rec):
    with open(p, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--max_per_gpu", type=int, default=1)
    ap.add_argument("--stop_after", default=None, help="ISO UTC, e.g. 2026-10-13T23:08:55Z")
    ap.add_argument("--min_free_gb", type=float, default=10.0)
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("--exit_when_idle", type=int, default=1)
    a = ap.parse_args()
    stop_after = dt.datetime.fromisoformat(a.stop_after.replace("Z", "+00:00")) if a.stop_after else None
    finished = {}
    for r in read_jsonl(a.state):
        if r.get("event") in ("done", "failed"):
            finished[r["id"]] = r["event"]
    running = {}  # id -> (Popen, job, attempt, t0, log)
    attempts = {}
    halted_reason = None
    while True:
        jobs = read_jsonl(a.jobs)
        # 완료 처리
        for jid, (p, job, att, t0, log) in list(running.items()):
            rc = p.poll()
            if rc is None:
                continue
            dur = time.time() - t0
            del running[jid]
            if rc == 0:
                finished[jid] = "done"
                append(a.state, {"id": jid, "event": "done", "rc": rc, "sec": dur, "attempt": att, "log": log, "t": now().isoformat()})
            elif att == 0:
                attempts[jid] = 1
                append(a.state, {"id": jid, "event": "retry", "rc": rc, "sec": dur, "attempt": att, "log": log, "t": now().isoformat()})
            else:
                finished[jid] = "failed"
                append(a.state, {"id": jid, "event": "failed", "rc": rc, "sec": dur, "attempt": att, "log": log, "t": now().isoformat()})
        pending = [j for j in jobs if j["id"] not in finished and j["id"] not in running]
        # 새 작업 시작 조건
        can_start = True
        if stop_after and now() >= stop_after:
            can_start, halted_reason = False, "stop_after"
        free_gb = shutil.disk_usage(ROOT).free / 2**30
        if free_gb < a.min_free_gb:
            can_start, halted_reason = False, f"disk free {free_gb:.1f} GB"
        if can_start:
            for j in pending:
                n_on = sum(1 for (_, jj, _, _, _) in running.values() if jj["gpu"] == j["gpu"])
                if n_on >= a.max_per_gpu:
                    continue
                att = attempts.get(j["id"], 0)
                log = j["log"] + ("_retry1" if att == 1 else "")
                os.makedirs(os.path.dirname(os.path.join(ROOT, log)), exist_ok=True)
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=j["gpu"])
                lf = open(os.path.join(ROOT, log), "w")
                p = subprocess.Popen(["bash", "-c", j["cmd"]], cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
                running[j["id"]] = (p, j, att, time.time(), log)
                append(a.state, {"id": j["id"], "event": "start", "gpu": j["gpu"], "attempt": att, "pid": p.pid, "log": log, "t": now().isoformat()})
        if not running and (not pending or not can_start) and a.exit_when_idle:
            append(a.state, {"id": "_runner", "event": "exit", "pending": len(pending), "halted": halted_reason, "t": now().isoformat()})
            break
        time.sleep(a.poll)


if __name__ == "__main__":
    main()
