#!/usr/bin/env python3
"""幻梦守护进程 — 自动监听银月的指令

开机自启，每10秒检查一次 GitHub 有没有新任务。
有就执行，完成后自动汇报。不需要手动操作。

用法：
    python huanmeng_daemon.py           # 前台运行
    python huanmeng_daemon.py --once    # 只检查一次
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SYNC_DIR = Path("D:/GameDownload/github/silvermoon-sync")
TASKS_DIR = SYNC_DIR / ".tasks"
CHECK_INTERVAL = 10  # 每10秒检查一次


def git_pull():
    result = subprocess.run(["git", "pull", "origin", "master"], cwd=SYNC_DIR, capture_output=True, text=True)
    return "Already up to date" in result.stdout or "Already up-to-date" in result.stdout or result.returncode == 0


def git_push():
    subprocess.run(["git", "add", ".tasks/"], cwd=SYNC_DIR, capture_output=True)
    subprocess.run(["git", "commit", "-m", "huanmeng: task completed"], cwd=SYNC_DIR, capture_output=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=SYNC_DIR, capture_output=True)


def process_pending_tasks():
    """只负责发现新任务，写入提示文件。不修改任务状态。
    Claude Code 的 /loop 负责真正执行并标记 done、push 汇报。"""
    if not TASKS_DIR.exists():
        return

    new_found = 0
    for task_file in sorted(TASKS_DIR.glob("*.json")):
        task = json.loads(task_file.read_text(encoding="utf-8"))
        if task.get("status") != "pending":
            continue
        if task.get("assigned_to") not in ("huanmeng", "device_b"):
            continue

        new_found += 1
        text = task.get("params", {}).get("text", task.get("description", ""))
        print(f"\n[幻梦] [{datetime.now().strftime('%H:%M:%S')}] 发现新指令: {text[:80]}")

        # 写入指令文件，供 Claude Code /loop 读取
        instruction_file = SYNC_DIR / ".state" / "current_instruction.txt"
        instruction_file.parent.mkdir(parents=True, exist_ok=True)
        instruction_file.write_text(
            f"任务ID: {task['id']}\n指令: {text}\n"
            f"请在Claude Code中执行此指令，完成后把结果写回 {task_file} 的result字段，"
            f"将status改为done，然后 git add+commit+push。",
            encoding="utf-8"
        )

    if new_found == 0:
        # 检查是否有已处理但未 push 的任务（Claude Code 改的）
        for task_file in sorted(TASKS_DIR.glob("*.json")):
            task = json.loads(task_file.read_text(encoding="utf-8"))
            if task.get("status") == "done" and not task.get("pushed"):
                task["pushed"] = True
                task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
                new_found += 1

        if new_found > 0:
            git_push()
            print(f"[幻梦] 已推送 {new_found} 个完成的任务汇报\n")

    return new_found


def run_once():
    git_pull()
    process_pending_tasks()


def run_daemon():
    print("幻梦守护进程启动。每10秒检查一次银月的指令。")
    print("按 Ctrl+C 停止。\n")

    try:
        while True:
            git_pull()
            process_pending_tasks()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n幻梦: 守护进程已停止。")


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_daemon()
