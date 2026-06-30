# Loop Engineering — 核心组件详解

## 组件一：Memory（记忆系统）

Agent 在循环过程中需要记住已经做了什么、学到了什么。记忆系统分四层：

```
记忆类型        存储位置         特点              典型用途
──────────────────────────────────────────────────────────────
In-Context     Context Window   最快，但有限       当前任务的步骤历史
External       向量数据库        持久，可检索       跨会话的历史经验
Episodic       结构化存储        可查询             过去成功/失败案例
Procedural     Fine-tuning       烧进权重           高频技能的内化
```

### 上下文窗口管理

长 Loop 会让 Context Window 快速耗尽，工程上需要**记忆压缩（Memory Compression）**：

```
原始历史：
  Step 1: [完整的工具调用和结果，2000 tokens]
  Step 2: [完整的工具调用和结果，1500 tokens]
  Step 3: [完整的工具调用和结果，3000 tokens]
  ...
  
压缩后：
  Summary: 已完成数据收集（3个数据源，共 150 条记录）。
           发现关键问题：价格差异在 Q3 尤为明显。
           当前进度：分析阶段 60%。
  [300 tokens]
```

---

## 组件二：Tool Use / Function Calling（工具调用）

工具是 Agent 与外部世界交互的唯一合法通道。工程化的工具系统需要：

### 工具的标准结构

```python
# 每个工具需要定义：
# 1. 名称和描述（LLM 根据这个决定是否调用）
# 2. 输入 Schema（严格的参数定义）
# 3. 执行逻辑
# 4. 错误处理

tool_definition = {
    "name": "web_search",
    "description": "搜索互联网获取最新信息。当需要查询实时数据、新闻、
                    产品信息时使用。不要用于查询已有的内部知识库。",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，建议使用英文以获得更好结果"
            },
            "num_results": {
                "type": "integer",
                "default": 5,
                "maximum": 20
            }
        },
        "required": ["query"]
    }
}
```

### 工具的错误处理与重试

```
工具调用失败的处理策略：

Transient Error（网络超时、限流）→ 自动重试（指数退避）
Permanent Error（权限不足）      → 报告给 LLM，换其他工具
Invalid Input（参数格式错误）    → 返回详细错误，让 LLM 修正参数
Unexpected Result（结果为空）    → 作为 Observation 传给 LLM，让其判断下一步
```

### 工具的权限分级

```
READ-ONLY 工具（低风险，可自由调用）
  ├── web_search
  ├── read_file
  └── query_database (SELECT only)

WRITE 工具（中风险，需要确认）
  ├── write_file
  ├── send_email
  └── create_calendar_event

DESTRUCTIVE 工具（高风险，需要 Human-in-the-Loop）
  ├── delete_records
  ├── execute_code
  └── make_payment
```

---

## 组件三：Planning（规划引擎）

复杂任务需要在执行前做规划。规划组件负责：
- 把高层目标分解为可执行的子任务
- 识别任务间的依赖关系
- 决定串行 vs 并行执行

### 任务图（Task Graph）

```
目标：生成季度报告

任务图：
  [收集销售数据] ──▶ [计算关键指标] ──▶ [生成图表] ──▶ [撰写报告]
  [收集用户反馈] ──▶                  ──▶
  [收集竞品数据] ──▶ [竞品分析]       ──▶
  
  可并行：收集销售数据、收集用户反馈、收集竞品数据（无依赖）
  必须串行：计算指标 → 生成图表 → 撰写报告
```

---

## 组件四：Multi-Agent 协作

单一 Agent 的上下文窗口和能力有限，复杂任务需要多个 Agent 协作：

### 常见多 Agent 模式

**Orchestrator-Worker 模式**
```
Orchestrator Agent（协调者）
  ├── 分解任务，分发给 Worker
  ├── 汇总 Worker 的结果
  └── 做最终决策

Worker Agent（执行者）
  ├── Research Agent  → 负责信息收集
  ├── Code Agent      → 负责写代码和调试
  └── Review Agent    → 负责质量审核
```

**Debate 模式**
```
Agent A 提出方案 → Agent B 批评 → Agent A 改进 → 人工仲裁
```
用于高风险决策，通过多角度批判提高方案质量。

**Specialized Agent Pipeline**
```
用户请求 → Router → [Customer Service Agent]
                 → [Technical Support Agent]
                 → [Billing Agent]
```

---

## 组件五：Human-in-the-Loop（人工介入）

完全自动化的 Agent 在关键决策点需要人工确认，这是**Loop Engineering 的安全机制**：

### 介入触发条件

```
自动继续（不需要人工）：
  - 低风险只读操作
  - 置信度高的标准操作
  - 可回滚的操作

暂停等待人工确认（Human-in-the-Loop）：
  - 不可逆操作（发送邮件、删除数据、付款）
  - 置信度低（LLM 不确定时主动请求确认）
  - 超出预算（Token 消耗、API 调用次数）
  - 异常状态（工具连续失败）

完全移交给人工（Human-as-the-Loop）：
  - 监管合规要求
  - 涉及敏感数据
  - 首次执行新类型任务
```

### 介入设计原则

1. **最小化打扰**：只在真正需要时打断用户，频繁确认会导致用户绕过
2. **提供足够上下文**：人工看到的不只是"确认这步操作"，而是"当前目标、已完成步骤、这步的影响"
3. **支持拒绝和修正**：人工不只能"确认"，还能"拒绝"、"修改参数"、"建议替代方案"

---

## 组件六：Evaluation in the Loop（循环内评估）

不只是在 Loop 结束后评估，而是在**每一步**检查质量：

```
步骤完成
    │
    ▼
Step-level Eval
  ├── 这一步的工具输出是否符合预期？
  ├── 是否发现了新信息需要更新计划？
  └── 是否达到了这一步的子目标？
    │
    ▼
继续下一步 or 重试 or 放弃
```

这使 Agent 具备**自我纠错**能力，而不是一路跑完才发现第一步就错了。
