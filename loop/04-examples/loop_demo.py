"""
Loop Engineering 代码示例

展示 Agent Loop 的核心实现模式：
1. ReAct Loop — Thought-Action-Observation 循环
2. Plan-and-Execute — 先规划再执行
3. Reflexion — 失败后自我反思重试
4. Human-in-the-Loop — 关键步骤人工确认

这些示例是独立可运行的（使用模拟的 LLM 和工具），
无需 API Key。在真实项目中替换 mock_llm() 和各工具实现即可。
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Callable


# ─────────────────────────────────────────────────────────
# 基础工具系统
# ─────────────────────────────────────────────────────────

@dataclass
class Tool:
    name: str
    description: str
    fn: Callable
    risk_level: str = "low"  # low / medium / high


class ToolRegistry:
    """工具注册表，管理 Agent 可调用的工具"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_for_prompt(self) -> str:
        """生成给 LLM 看的工具列表描述"""
        lines = []
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)


# 模拟工具实现
def mock_web_search(query: str) -> str:
    """模拟搜索工具"""
    results = {
        "北京天气": "北京今天晴天，气温 28°C，空气质量良好",
        "苹果股价": "AAPL 当前价格：$195.23，今日涨幅 +1.2%",
        "Python 最新版本": "Python 3.12 于 2023 年 10 月发布，主要改进了错误提示",
    }
    for key, val in results.items():
        if key in query:
            return val
    return f"搜索 '{query}' 的结果：未找到相关信息"


def mock_calculator(expression: str) -> str:
    """模拟计算工具"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


def mock_write_file(filename: str, content: str) -> str:
    """模拟文件写入（high risk，需要 Human-in-the-Loop）"""
    return f"已将内容写入 {filename}（{len(content)} 字符）"


# ─────────────────────────────────────────────────────────
# 1. ReAct Loop
# ─────────────────────────────────────────────────────────

@dataclass
class ReActStep:
    thought: str
    action: str | None = None
    action_input: dict = field(default_factory=dict)
    observation: str | None = None
    is_final: bool = False
    final_answer: str | None = None


def mock_llm_react(prompt: str, step_num: int) -> dict:
    """
    模拟 ReAct 模式下的 LLM 输出。
    真实项目中替换为 anthropic.messages.create() 或 openai.chat.completions.create()
    """
    # 模拟多步推理
    steps = [
        {
            "thought": "我需要查询北京天气才能给出穿衣建议",
            "action": "web_search",
            "action_input": {"query": "北京天气"}
        },
        {
            "thought": "天气是 28°C 晴天，适合穿薄衣服。需要计算一下体感温度",
            "action": "calculator",
            "action_input": {"expression": "28 * 0.9"}
        },
        {
            "thought": "体感温度约 25.2°C，信息足够了，可以给出建议",
            "is_final": True,
            "final_answer": "北京今天 28°C 晴天，建议穿短袖 T 恤 + 轻薄长裤，做好防晒准备。"
        }
    ]
    idx = min(step_num, len(steps) - 1)
    return steps[idx]


def run_react_loop(
    task: str,
    tools: ToolRegistry,
    max_steps: int = 10,
    human_confirm_risks: list[str] = None,
) -> str:
    """
    ReAct Loop 主循环。

    返回最终答案，或超过 max_steps 后的失败信息。
    """
    print(f"\n{'='*50}")
    print(f"任务: {task}")
    print(f"{'='*50}")

    history: list[ReActStep] = []
    human_confirm_risks = human_confirm_risks or ["high"]

    for step_num in range(max_steps):
        print(f"\n--- Step {step_num + 1} ---")

        # 调用 LLM 决定下一步（真实场景传入完整的历史上下文）
        llm_output = mock_llm_react(task, step_num)

        step = ReActStep(
            thought=llm_output.get("thought", ""),
            action=llm_output.get("action"),
            action_input=llm_output.get("action_input", {}),
            is_final=llm_output.get("is_final", False),
            final_answer=llm_output.get("final_answer"),
        )

        print(f"💭 Thought: {step.thought}")

        # 终止条件：LLM 认为任务完成
        if step.is_final:
            print(f"\n✅ Final Answer: {step.final_answer}")
            return step.final_answer

        # 执行工具调用
        tool = tools.get(step.action)
        if not tool:
            step.observation = f"错误：工具 '{step.action}' 不存在"
        else:
            print(f"🔧 Action: {step.action}({step.action_input})")

            # Human-in-the-Loop 检查
            if tool.risk_level in human_confirm_risks:
                print(f"⚠️  高风险操作，需要人工确认")
                # 实际中这里弹出 UI 或发送通知等待确认
                # 这里模拟自动批准
                print(f"✓  [模拟] 人工已批准")

            step.observation = tool.fn(**step.action_input)

        print(f"👁️  Observation: {step.observation}")
        history.append(step)

    return "超过最大步数限制，任务未完成"


# ─────────────────────────────────────────────────────────
# 2. Plan-and-Execute Loop
# ─────────────────────────────────────────────────────────

@dataclass
class SubTask:
    id: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending / running / done / failed
    result: str | None = None


def mock_planner(goal: str) -> list[SubTask]:
    """模拟规划 LLM，把目标分解为子任务"""
    return [
        SubTask(id="t1", description="收集市场数据", depends_on=[]),
        SubTask(id="t2", description="分析竞品价格", depends_on=[]),
        SubTask(id="t3", description="计算价格建议", depends_on=["t1", "t2"]),
        SubTask(id="t4", description="生成报告", depends_on=["t3"]),
    ]


def mock_executor(task: SubTask, context: dict) -> str:
    """模拟执行单个子任务"""
    time.sleep(0.1)  # 模拟执行耗时
    return f"[{task.id}] {task.description} 已完成"


def run_plan_execute(goal: str):
    """Plan-and-Execute Loop：先规划，再按依赖顺序执行"""
    print(f"\n{'='*50}")
    print(f"目标: {goal}")
    print(f"{'='*50}")

    # 规划阶段
    tasks = mock_planner(goal)
    task_map = {t.id: t for t in tasks}
    print(f"\n📋 规划完成，共 {len(tasks)} 个子任务:")
    for t in tasks:
        deps = f" (依赖: {t.depends_on})" if t.depends_on else ""
        print(f"  {t.id}: {t.description}{deps}")

    # 执行阶段：按依赖顺序执行
    print("\n🚀 开始执行:")
    context = {}
    completed = set()

    while len(completed) < len(tasks):
        # 找出所有依赖已满足的待执行任务
        ready = [
            t for t in tasks
            if t.status == "pending" and all(dep in completed for dep in t.depends_on)
        ]

        if not ready:
            print("❌ 发现死锁或所有任务完成")
            break

        for task in ready:
            task.status = "running"
            print(f"  ▶ 执行: {task.description}")
            task.result = mock_executor(task, context)
            task.status = "done"
            context[task.id] = task.result
            completed.add(task.id)
            print(f"  ✓ 完成: {task.result}")

    print(f"\n✅ 所有任务完成，共 {len(completed)} 个")


# ─────────────────────────────────────────────────────────
# 3. Reflexion Loop（反思循环）
# ─────────────────────────────────────────────────────────

def mock_llm_with_reflection(task: str, reflection: str | None, attempt: int) -> dict:
    """模拟带反思的 LLM"""
    if attempt == 0:
        return {"answer": "42", "confidence": 0.3}  # 第一次给出错误答案
    elif attempt == 1:
        return {"answer": "47", "confidence": 0.9}  # 反思后给出正确答案
    return {"answer": "47", "confidence": 0.95}


def verify_answer(answer: str, task: str) -> tuple[bool, str]:
    """验证答案是否正确（实际中可以运行测试用例、调用验证 API 等）"""
    # 模拟验证：正确答案是 47
    correct = answer == "47"
    feedback = "正确！" if correct else f"答案 '{answer}' 不正确，预期结果应为一个两位数"
    return correct, feedback


def run_reflexion_loop(task: str, max_attempts: int = 3) -> str:
    """
    Reflexion Loop：失败后反思，再次尝试。
    """
    print(f"\n{'='*50}")
    print(f"任务: {task}")
    print(f"{'='*50}")

    reflection = None

    for attempt in range(max_attempts):
        print(f"\n--- 第 {attempt + 1} 次尝试 ---")
        if reflection:
            print(f"📝 反思: {reflection}")

        result = mock_llm_with_reflection(task, reflection, attempt)
        answer = result["answer"]
        confidence = result["confidence"]
        print(f"💡 答案: {answer}（置信度: {confidence:.0%}）")

        # 验证答案
        correct, feedback = verify_answer(answer, task)
        print(f"🔍 验证: {feedback}")

        if correct:
            print(f"\n✅ 成功！经过 {attempt + 1} 次尝试找到正确答案: {answer}")
            return answer

        # 失败时生成反思
        reflection = f"上次回答了 '{answer}'，验证失败：{feedback}。需要重新检查计算过程。"

    print(f"\n❌ 达到最大尝试次数，未能找到正确答案")
    return answer


# ─────────────────────────────────────────────────────────
# 入口：运行所有示例
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 初始化工具注册表
    registry = ToolRegistry()
    registry.register(Tool("web_search", "搜索互联网", mock_web_search, risk_level="low"))
    registry.register(Tool("calculator", "数学计算", mock_calculator, risk_level="low"))
    registry.register(Tool("write_file", "写入文件（不可逆）", mock_write_file, risk_level="high"))

    # 1. ReAct Loop
    run_react_loop(
        task="北京今天适合穿什么衣服？",
        tools=registry,
        human_confirm_risks=["high"],
    )

    # 2. Plan-and-Execute
    run_plan_execute("为新产品制定定价策略报告")

    # 3. Reflexion Loop
    run_reflexion_loop("计算 6 × 7 + 5 的结果")
