# Agent Mesh

> 多 AI Agent 协作网络 · 让 Claude Code 实例互通

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)

## 这是什么

Agent Mesh 让两台（或更多）设备上的 Claude Code 互相通信、协作、分工。

一个做"主脑"（决策、创意、对话），另一个做"工脑"（重计算、批量处理、研究），通过 GitHub 仓库做消息中转，不依赖网络直连。 

**实际运行案例**：银月（主脑，普通笔记本）指挥 幻梦（工脑，16核+31GB+RTX3080），每天处理 7-15 个任务。

## 架构

```
设备A（主脑·Leader）       GitHub 仓库            设备B（工脑·Worker）
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│ Claude Code  │ →→   │ hanli1999/       │  →→  │ Claude Code  │
│ + 决策·创造   │  写任务 │ agent-mesh-sync  │  接任务 │ + 听话干活    │
│ + 下命令      │ ←←   │                  │  ←←  │ + 汇报结果    │
│ + 验收        │  读结果 │ .tasks/          │  写结果 │              │
└──────────────┘      └──────────────────┘      └──────────────┘
```

**隐私模型**：工脑→主脑全透明；主脑→工脑选择性同步。私密对话和敏感数据不离开主脑设备。

## 快速开始

### 主脑设备

```bash
git clone https://github.com/YOU/agent-mesh-sync.git
cd agent-mesh-sync
python yinyue_sync.py cmd "工脑，通信测试。告诉我你的系统配置。"
python yinyue_sync.py check     # 查看工脑回复
```

### 工脑设备

```bash
git clone https://github.com/YOU/agent-mesh-sync.git
cd agent-mesh-sync
python huanmeng_daemon.py       # 开守护进程（10秒轮询指令）

# 另开终端，启动 Claude Code：
claude
# 进去后说：
/loop 60s 读取.tasks/下status=pending的任务，执行后写结果、git push汇报。
```

## 任务协议

任务以 JSON 存放在 `.tasks/` 目录：

```json
{
  "id": "task_xxx",
  "type": "command | compute | research | report",
  "status": "pending | running | done | failed",
  "assigned_to": "worker_name",
  "params": {"text": "指令内容"},
  "result": "执行结果"
}
```

**四级任务类型**：
- `command` — 口头指令
- `compute` — 重计算（批处理、渲染）
- `research` — 研究探索（搜索+分析）
- `report` — 工脑主动汇报

**三级优先级**：`[urgent]` 立即执行，`[normal]` 默认，`[low]` 空闲执行。

## 案例：银月 → 幻梦

真实运行记录：

```
银月: "帮我评估本地大模型可行性"
幻梦: [检测到任务] [执行] [回复]
      GPU: RTX 3080 16GB, CPU: 16核, RAM: 31GB
      推荐 Qwen3-14B Q4_K_M, VRAM需求 9GB
      可同时跑 46个技能
      [耗时: 180s]
```

## License

MIT

---

*由银月（Silver Moon）在与幻梦的磨合实战中提炼。*
