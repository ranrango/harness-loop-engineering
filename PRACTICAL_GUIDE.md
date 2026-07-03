# Harness & Loop Engineering 实践手册

本文是仓库的落地指南：把 `Harness Engineering` 和 `Loop Engineering` 从概念转成可实施的 AI 应用架构。

## 1. 总体方法

一个生产级 AI 应用通常不是“一个 Prompt + 一个模型”，而是下面这个组合：

```text
业务目标
  ↓
Harness Engineering
  - Prompt
  - RAG
  - Tool Schema
  - Guardrails
  - Structured Output
  - Evals
  - 权限、日志、审计
  ↓
Loop Engineering
  - Trigger
  - Plan / ReAct
  - Action
  - Observation
  - Step Eval
  - Repair
  - Stop / Escalation
  ↓
业务结果
```

先做 Harness，再做 Loop。Harness 没有建好时，Loop 会把错误放大；Loop 没有建好时，Harness 只能支撑单次问答。

## 2. Harness 设计清单

| 模块 | 要回答的问题 | 交付物 |
|---|---|---|
| 任务边界 | Agent 能做什么，不能做什么？ | scope 文档、拒绝策略 |
| Prompt | 角色、规则、输出格式是什么？ | system prompt、user template |
| RAG | 哪些资料可信，是否必须引用？ | 知识库、索引策略、引用规则 |
| Tools | 能调用哪些工具，参数如何约束？ | tool schema、风险等级 |
| Guardrails | 哪些输入输出必须拦截？ | PII 检测、注入检测、格式校验 |
| Structured Output | 下游系统如何消费结果？ | JSON Schema、Pydantic model |
| Evals | 怎么知道改动没有退步？ | golden set、regression set |
| Observability | 失败后如何复盘？ | trace、日志、成本、版本记录 |
| Permissions | 什么操作必须人工批准？ | RBAC、审批、沙箱、回滚策略 |

### Harness 模板

```yaml
agent_harness:
  name: customer-support-kb
  purpose: "根据客服工单生成知识库草稿"

  prompt:
    role: "客服知识库编辑"
    rules:
      - "只基于已关闭工单和产品文档回答"
      - "事实必须带来源"
      - "不能输出客户 PII"
    output_format: "markdown"

  rag:
    sources:
      - "product_docs"
      - "closed_tickets"
      - "release_notes"
    require_citations: true

  tools:
    read_only:
      - "ticket_reader"
      - "docs_search"
    write_draft:
      - "kb_draft_writer"
    forbidden:
      - "publish_to_production"

  guardrails:
    input:
      - "prompt_injection_check"
      - "pii_redaction"
    output:
      - "citation_check"
      - "pii_check"
      - "markdown_format_check"

  evals:
    smoke:
      - "answer_contains_source"
      - "no_customer_email"
    regression:
      - "known_sso_cookie_issue"
      - "known_refund_policy_issue"

  permissions:
    production_write: false
    human_approval_required: true
```

## 3. Loop 设计清单

| 阶段 | 要回答的问题 | 例子 |
|---|---|---|
| Trigger | 什么时候启动？ | 用户请求、CI 失败、定时任务、告警 |
| Intake | 读取什么输入？ | issue、工单、日志、传感器数据 |
| State | 当前任务做到哪一步？ | 历史尝试、上下文摘要、预算 |
| Plan | 下一步怎么做？ | ReAct、Plan-and-Execute、任务图 |
| Act | 调用什么工具？ | search、read_file、run_tests、write_draft |
| Observe | 工具返回了什么？ | 测试结果、API 响应、搜索结果 |
| Verify | 这一步是否合格？ | schema、lint、单测、人工 review |
| Repair | 失败如何修正？ | 重试、换工具、缩小范围、重规划 |
| Stop | 什么时候结束？ | 成功、超预算、高风险、连续失败 |

### Loop 模板

```yaml
agent_loop:
  name: ci-failure-repair-loop

  trigger:
    type: "webhook"
    event: "ci_failure"

  intake:
    source: "github_actions"
    filter:
      - "branch == main"
      - "label == agent-ready"
      - "not security-sensitive"

  plan:
    strategy: "reproduce -> diagnose -> patch -> verify"

  act:
    branch_prefix: "agent/fix-ci-"
    allowed_tools:
      - "read_file"
      - "edit_file"
      - "run_tests"
      - "git_diff"

  verify:
    commands:
      - "pytest"
      - "ruff check ."
    reviewer: "separate_review_agent"

  termination:
    max_steps: 20
    max_runtime_minutes: 30
    max_repair_attempts: 2
    escalate_if:
      - "permission_denied"
      - "production_write_required"
      - "same_error_repeated_3_times"

  output:
    on_success: "open_pull_request"
    on_failure: "write_investigation_note"
```

## 4. 最小可行落地路线

### 第 1 阶段：单次调用可控

目标：让 LLM 输出稳定。

- 写 system prompt 和输出 schema
- 加 JSON/Markdown/表格格式校验
- 保存 20-50 条 golden eval cases
- 记录 prompt 版本和输入输出

### 第 2 阶段：接入知识和工具

目标：让 LLM 能基于事实和工具工作。

- 建 RAG 管道并强制引用来源
- 给每个工具写 schema 和错误返回
- 给工具分风险等级：read-only、write、destructive
- 对 write/destructive 工具加人工审批

### 第 3 阶段：形成 Agent Loop

目标：让系统能完成多步任务。

- 选择 ReAct 或 Plan-and-Execute
- 加 step-level eval
- 加最大步数、最大时间、最大 token
- 失败后最多重试 1-2 次
- 把失败原因写入日志

### 第 4 阶段：生产化

目标：接入真实业务流程。

- 接入 Webhook、定时任务、队列或告警
- 加监控指标：成功率、人工接管率、平均成本、平均步数
- 加回归评估流水线
- 定期复盘失败案例并加入 eval set

## 5. 风险分级

| 风险等级 | 示例 | 推荐策略 |
|---|---|---|
| 低风险 | 检索资料、生成草稿、只读查询 | 自动执行，记录日志 |
| 中风险 | 写文档、创建 PR、发内部通知 | 自动生成，人工审核 |
| 高风险 | 删除数据、修改生产配置、付款、外发邮件 | 默认禁止，必须人工批准 |
| 禁止自动化 | 法律/医疗最终建议、人身安全控制、不可逆生产操作 | Human-as-the-loop |

## 6. 常见反模式

- 只写 Prompt，不做 Evals。
- RAG 没有来源质量控制，检索到什么就喂什么。
- 工具没有参数 schema，Agent 自由拼接命令。
- Loop 没有停止条件，失败后无限重试。
- 让同一个 Agent 既生成结果又批准结果。
- 生产环境权限过大，没有沙箱和回滚。
- 没有 trace，线上失败后无法解释。

## 7. 验收标准

一个可上线的 Harness + Loop 系统至少应满足：

- 输出可解析：结构化结果能被程序稳定消费。
- 事实可追踪：关键事实有来源或工具返回记录。
- 操作可审计：每次工具调用、审批、失败原因可回放。
- 风险可拦截：高风险操作不会自动执行。
- 质量可回归：每次 Prompt、RAG、工具改动能跑 eval。
- 循环可停止：成功、失败、超预算、高风险都有终止路径。
