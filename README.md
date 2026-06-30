# Harness & Loop Engineering — AI 应用开发工程指南

> **Harness Engineering（驾驭工程）** 和 **Loop Engineering（循环工程）** 是 2025–2026 年 AI 应用开发领域的两个核心工程方向，描述了如何系统性地构建可控、可靠、可持续演进的 AI 应用。

---

## 什么是这两个概念？

| | Harness Engineering | Loop Engineering |
|---|---|---|
| **中文** | 驾驭工程 | 循环工程 |
| **核心问题** | 如何让 LLM 可控、可预测地完成任务 | 如何构建 AI Agent 的感知-推理-行动闭环 |
| **关键词** | Prompt 工程、Guardrails、Evals、RAG、Tool Use | ReAct、Agent Loop、RLHF、Human-in-the-Loop |
| **终极目标** | 把不可控的 LLM "驾驭"成可靠的业务组件 | 让 Agent 通过反馈不断自我改进 |

---

## 目录结构

```
harness-loop-engineering/
├── harness/                    # 驾驭工程
│   ├── 01-concepts/            # 核心概念：什么是 Harness Engineering
│   ├── 02-core-components/     # 核心组件详解
│   ├── 03-industry/            # 工业界现状与发展
│   └── 04-examples/            # 实际代码示例
└── loop/                       # 循环工程
    ├── 01-concepts/            # 核心概念：什么是 Loop Engineering
    ├── 02-core-components/     # 核心组件详解
    ├── 03-industry/            # 工业界现状与发展
    └── 04-examples/            # 实际代码示例
```

---

## 快速导航

### Harness Engineering

| 章节 | 内容 |
|------|------|
| [核心概念](./harness/01-concepts/) | 定义、起源、与传统工程的关系 |
| [核心组件](./harness/02-core-components/) | Prompt 工程、Guardrails、Evals、RAG、Tool Use |
| [工业界现状](./harness/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [代码示例](./harness/04-examples/) | 可运行的工程实践示例 |

### Loop Engineering

| 章节 | 内容 |
|------|------|
| [核心概念](./loop/01-concepts/) | 定义、起源、Agent Loop 心智模型 |
| [核心组件](./loop/02-core-components/) | ReAct、Memory、Planning、Multi-Agent |
| [工业界现状](./loop/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [代码示例](./loop/04-examples/) | 可运行的 Agent Loop 示例 |

---

## 两者的关系

```
                    ┌─────────────────────────────┐
                    │      AI 应用系统               │
                    │                             │
   Harness ────────▶│  约束 · 驱动 · 评估 LLM       │
   Engineering      │                             │
                    │  ┌─────────────────────┐    │
   Loop  ──────────▶│  │  Agent 感知→推理→行动  │    │
   Engineering      │  │  ←─── 反馈闭环 ────   │    │
                    │  └─────────────────────┘    │
                    └─────────────────────────────┘
```

**Harness 是基础设施层**（怎么让 LLM 可靠工作），**Loop 是执行逻辑层**（Agent 如何在 Harness 之上循环行动）。一个好的 AI 应用，两者缺一不可。

---

## 推荐阅读顺序

1. 先读 Harness 概念 → 理解为什么 LLM 需要被"驾驭"
2. 再读 Loop 概念 → 理解 Agent 如何在约束下持续运行
3. 对照工业界章节 → 看真实公司怎么做
4. 跑通代码示例 → 动手实践
