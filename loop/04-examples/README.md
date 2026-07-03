# Loop 示例说明

`loop_demo.py` 是一个无外部依赖的最小示例，演示 Agent Loop 的四种常见模式。

## 运行方式

```bash
python3 loop/04-examples/loop_demo.py
```

脚本使用模拟 LLM 和模拟工具，不需要 API Key。

## 示例包含什么

| 模块 | 代码位置 | 说明 |
|---|---|---|
| Tool Registry | `Tool` / `ToolRegistry` | 给工具定义名称、描述、函数和风险等级 |
| ReAct Loop | `run_react_loop` | Thought -> Action -> Observation -> Final Answer |
| Plan-and-Execute | `run_plan_execute` | 先规划子任务，再按依赖执行 |
| Reflexion | `run_reflexion_loop` | 验证失败后生成反思，再次尝试 |
| Human-in-the-Loop | `human_confirm_risks` | 高风险工具调用需要人工确认 |

## 如何扩展到真实项目

### 1. Tool Registry

真实工具应该包含：

- 输入 JSON Schema
- 风险等级
- 权限要求
- 超时设置
- 可重试错误和不可重试错误
- 审计日志

### 2. ReAct Loop

适合搜索、问答、工具调用型任务。必须加：

- `max_steps`
- `timeout`
- `max_tokens`
- 工具失败阈值
- 最终答案 schema

### 3. Plan-and-Execute

适合报告、代码修复、数据分析等多步骤任务。建议增加：

- 任务依赖图
- 可并行任务识别
- 失败后的重规划
- 每个子任务的验收条件

### 4. Reflexion

适合有明确验证器的任务，例如：

- 代码测试
- 数学计算
- SQL 查询结果校验
- 格式化输出校验

不要把 Reflexion 当成万能自我纠错。没有外部验证器时，模型可能只是把错误解释得更自信。

### 5. Human-in-the-Loop

建议把工具按风险分层：

| 风险等级 | 示例 | 策略 |
|---|---|---|
| low | 搜索、读取文件、只读查询 | 自动执行 |
| medium | 写草稿、创建 PR、发内部通知 | 自动生成，人工审核 |
| high | 删除数据、发外部邮件、改生产配置 | 必须人工确认 |
| forbidden | 付款、泄露 secret、绕过权限 | 禁止执行 |

## 最小生产改造清单

- 每个 Loop 必须有停止条件。
- 每个动作必须有 Observation。
- 每个关键步骤必须有验证器。
- 高风险工具必须人工确认。
- 连续失败必须升级人工或写失败报告。
- 记录完整 trace，方便复盘。
