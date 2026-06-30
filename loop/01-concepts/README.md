# Loop Engineering — 核心概念

## 1. 什么是 Loop Engineering？

Loop Engineering 研究如何构建 AI Agent 的**感知-推理-行动反馈闭环**，使 Agent 能够：

1. 观察当前状态和上下文
2. 推理下一步该做什么
3. 执行动作（调用工具、写代码、发消息……）
4. 观察动作结果，进入下一轮循环
5. 持续迭代直到目标完成或达到终止条件

> **Loop Engineering = 让 AI Agent 不止步于"回答问题"，而是能够"完成任务"的工程体系。**

---

## 2. 为什么需要 Loop Engineering？

### 单次推理的局限

传统 LLM 应用是**单轮问答**：一个问题 → 一个回答 → 结束。这适合聊天，但不适合真实工作：

```
真实任务："帮我分析竞品，生成 PPT，发给团队"

单次推理：LLM 只能说"好的，你可以这样做……"（给建议）
Loop 模式：
  第 1 轮：搜索竞品信息
  第 2 轮：分析数据，识别关键信息
  第 3 轮：生成 PPT 大纲
  第 4 轮：调用 PPT 工具生成文件
  第 5 轮：发送邮件
  完成 ✓
```

### Loop 使 Agent 具备"任务完成"能力

```
问答模式（无 Loop）          Agent 模式（有 Loop）
    │                           │
用户输入 ──▶ LLM ──▶ 输出      用户输入
                                  │
                              ┌───▼───────────────┐
                              │  感知：读取环境状态   │
                              └───────────┬───────┘
                                          │
                              ┌───────────▼───────┐
                              │  推理：规划下一步    │
                              └───────────┬───────┘
                                          │
                              ┌───────────▼───────┐
                              │  行动：调用工具/API  │
                              └───────────┬───────┘
                                          │
                              ┌───────────▼───────┐
                              │  观察：处理结果      │◀─ 循环
                              └───────────┬───────┘
                                          │
                                     任务完成？
                                    Y ↓    N ↑ 返回感知
                                   输出结果
```

---

## 3. Loop 的核心模式

### ReAct（Reasoning + Acting）

由普林斯顿大学 2022 年提出，是目前最广泛使用的 Agent Loop 模式：

```
Thought: 我需要知道今天的天气才能建议穿什么
Action: search("北京今天天气")
Observation: 北京今天气温 28°C，晴天

Thought: 气温偏高，应该建议穿轻薄的衣服
Action: generate_outfit_recommendation(temp=28, weather="sunny")
Observation: 建议：短袖 + 薄长裤，防晒霜必备

Thought: 信息足够了，可以给出最终答案
Final Answer: 今天北京 28°C 晴天，建议穿短袖……
```

**工程要点**：
- Thought 是给 LLM 看的推理空间，不直接暴露给用户
- Action 触发工具调用，结果作为 Observation 注入下一轮
- 循环直到 LLM 输出 `Final Answer`

### Plan-and-Execute

先整体规划，再逐步执行，适合复杂长任务：

```
Plan:
  1. 收集竞品数据
  2. 分析数据差异
  3. 生成报告
  4. 发送邮件

Execute Step 1: [调用搜索工具] ...
Execute Step 2: [调用分析工具] ...
Execute Step 3: [调用写作工具] ...
Execute Step 4: [调用邮件工具] ...
```

**优点**：可以并行执行无依赖的步骤，总体更快。  
**缺点**：计划生成后执行时环境可能已变化，需要重新规划机制。

### Reflexion（反思循环）

Agent 执行完一次任务后，对结果进行**自我反思**，生成改进方案，再次尝试：

```
第 1 次尝试 → 失败
反思：我没有考虑到 X 情况，下次应该先检查 Y
第 2 次尝试（加入反思结论）→ 成功
```

这是让 Agent 具备**自我改进能力**的基础模式。

---

## 4. Loop 的终止条件工程

Loop 最常见的问题是**死循环**和**无限消耗 Token**。工程上必须设计明确的终止机制：

```python
# 终止条件的工程设计
termination_conditions = {
    "max_steps": 20,          # 最多执行 20 步
    "max_tokens": 100_000,    # Token 预算
    "timeout_seconds": 300,   # 5 分钟超时
    "goal_achieved": True,    # LLM 判断任务完成
    "error_threshold": 3,     # 连续 3 次工具调用失败则放弃
}
```

---

## 5. 与 Harness Engineering 的关系

```
Harness Engineering          Loop Engineering
        │                           │
约束 LLM 的输入和输出         编排 LLM 的行动序列
        │                           │
        └──────────┬────────────────┘
                   │
             AI Agent 系统
```

**Loop 运行在 Harness 之上**：
- Harness 的 Guardrails 确保每一步的工具调用是安全的
- Harness 的 Evals 评估整个 Loop 的最终输出质量
- Harness 的 Structured Output 确保每一轮的 Action 格式正确

---

## 6. 一句话理解

> Loop Engineering = 把 LLM 从"回答问题的助手"变成"完成任务的 Agent"的工程体系，核心是设计感知-推理-行动的反馈闭环及其终止与评估机制。
