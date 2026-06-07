#!/usr/bin/env python3
"""银月多设备同步脚本

让两台设备的银月共享技能、记忆、任务。
通过 GitHub 仓库 hanli1999/silvermoon-sync 做中间人。

用法：
    python yinyue_sync.py pull          # 从 GitHub 拉取最新
    python yinyue_sync.py push          # 推送本机变更到 GitHub
    python yinyue_sync.py sync          # 双向同步（先拉后推）
    python yinyue_sync.py task <json>   # 向 B 设备派发计算任务
    python yinyue_sync.py tasks         # 查看待处理任务
    python yinyue_sync.py status        # 查看同步状态
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
SYNC_DIR = Path("D:/GameDownload/github/silvermoon-sync")
SKILLS_DIR = Path.home() / ".claude" / "skills"
MEMORY_DIR = PROJECT_DIR / "memory"
STATE_FILE = Path.home() / ".claude" / "yinyue_device_state.json"

SYNC_REPO = "https://github.com/hanli1999/silvermoon-sync.git"


def git(cmd, cwd=None):
    """执行 git 命令"""
    return subprocess.run(
        f"git {cmd}", shell=True, cwd=cwd or SYNC_DIR,
        capture_output=True, text=True
    )


def ensure_sync_dir():
    """确保同步目录存在且有 git 仓库"""
    if not (SYNC_DIR / ".git").exists():
        print("首次设置...")
        SYNC_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(f"git clone {SYNC_REPO} {SYNC_DIR}", shell=True, check=True)


def pull():
    """从 GitHub 拉取并应用到本机"""
    ensure_sync_dir()
    print("拉取远程更新...")
    result = git("pull origin master")
    print(result.stdout.strip() or "已是最新")

    # 同步技能
    remote_skills = SYNC_DIR / ".skills"
    if remote_skills.exists():
        for skill_dir in remote_skills.iterdir():
            if skill_dir.is_dir():
                local = SKILLS_DIR / skill_dir.name
                if not local.exists():
                    subprocess.run(f'cp -r "{skill_dir}" "{local}"', shell=True)
                    print(f"  新技能: {skill_dir.name}")

    # 同步记忆
    remote_memory = SYNC_DIR / ".memory"
    if remote_memory.exists():
        for mem_file in remote_memory.iterdir():
            if mem_file.suffix in (".md", ".json"):
                local = MEMORY_DIR / mem_file.name
                remote_mtime = mem_file.stat().st_mtime
                local_mtime = local.stat().st_mtime if local.exists() else 0
                if remote_mtime > local_mtime:
                    subprocess.run(f'cp "{mem_file}" "{local}"', shell=True)
                    print(f"  更新记忆: {mem_file.name}")

    print("拉取完成")


def push():
    """推送本机变更到 GitHub"""
    ensure_sync_dir()

    # 同步技能到仓库
    subprocess.run(f'cp -r "{SKILLS_DIR}/"* "{SYNC_DIR}/.skills/"', shell=True)
    # 同步记忆到仓库
    subprocess.run(f'cp "{MEMORY_DIR}/"*.md "{SYNC_DIR}/.memory/"', shell=True)

    print("推送本机变更...")
    git("add .")
    git('commit -m "sync: auto-push"')
    result = git("push origin master")
    print(result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "已推送")
    print("推送完成")


def sync():
    """双向同步"""
    pull()
    push()
    update_device_state("synced")


def update_device_state(status):
    """更新本机状态"""
    state = {"device": os.environ.get("COMPUTERNAME", "unknown"),
             "status": status, "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "current_task": None}
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def status():
    """查看同步状态"""
    ensure_sync_dir()
    pull()
    print(f"本机: {os.environ.get('COMPUTERNAME', 'unknown')}")
    if STATE_FILE.exists():
        s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        print(f"状态: {s['status']}, 更新时间: {s['last_seen']}")
    # 检查对方设备
    other = SYNC_DIR / ".state" / "other_device.json"
    if other.exists():
        o = json.loads(other.read_text(encoding="utf-8"))
        print(f"伙伴: {o.get('device','?')} - {o.get('status','?')} ({o.get('last_seen','?')})")
    else:
        print("伙伴: 未上线")


def create_task(task_type, params, description=""):
    """创建计算任务，派发给性能更好的设备"""
    ensure_sync_dir()
    task_dir = SYNC_DIR / ".tasks"
    task_dir.mkdir(exist_ok=True)

    task_id = f"task_{int(time.time())}"
    task = {"id": task_id, "type": task_type, "params": params,
            "description": description, "status": "pending",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "assigned_to": "device_b", "result": None}

    (task_dir / f"{task_id}.json").write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"任务已创建: {task_id}")
    git(f'add .tasks/{task_id}.json')
    git(f'commit -m "task: {task_type} - {description}"')
    git("push origin master")
    return task_id


def list_tasks():
    """查看所有任务状态"""
    ensure_sync_dir()
    pull()
    task_dir = SYNC_DIR / ".tasks"
    if not task_dir.exists():
        print("暂无任务")
        return
    for task_file in sorted(task_dir.glob("*.json")):
        t = json.loads(task_file.read_text(encoding="utf-8"))
        icon = {"pending": "⋯", "running": "⚡", "done": "✓", "failed": "✗"}.get(t["status"], "?")
        print(f"{icon} {t['id']}: [{t['type']}] {t['description'][:60]} ({t['status']})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "pull":
        pull()
    elif cmd == "push":
        push()
    elif cmd == "sync":
        sync()
    elif cmd == "status":
        status()
    elif cmd == "task":
        if len(sys.argv) < 3:
            print("用法: python yinyue_sync.py task '<json>'")
            sys.exit(1)
        params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        create_task(params.get("type", "unknown"), params, params.get("desc", ""))
    elif cmd == "tasks":
        list_tasks()
    else:
        print("银月同步脚本")
        print("  pull    从 GitHub 拉取最新技能和记忆")
        print("  push    推送本机变更")
        print("  sync    双向同步")
        print("  task    创建计算任务派发给 B 设备")
        print("  tasks   查看任务状态")
        print("  status  查看同步状态")
