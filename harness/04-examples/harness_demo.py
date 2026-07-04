"""
Harness Engineering 代码示例

展示核心 Harness 组件的最简实现：
1. Structured Output（结构化输出）
2. Guardrail（输出护栏）
3. Eval（自动评估）
4. RAG 管道骨架

运行前需要设置 ANTHROPIC_API_KEY 环境变量。
"""

# ─────────────────────────────────────────────────────────
# 1. Structured Output — 确保 LLM 输出是可解析的 JSON
# ─────────────────────────────────────────────────────────

from __future__ import annotations
import json
import re


def build_structured_prompt(user_query: str, schema: dict) -> str:
    """
    把 JSON Schema 注入 Prompt，约束 LLM 的输出格式。
    这是不依赖特定 SDK 的通用方法。
    """
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    return f"""请严格按照以下 JSON Schema 格式回答用户的问题。
只输出 JSON，不要输出任何解释文字。

Schema:
{schema_str}

用户问题: {user_query}

JSON 输出:"""


def parse_structured_output(raw_output: str, schema: dict) -> dict:
    """
    解析 LLM 的结构化输出，包含容错处理。

    LLM 有时会在 JSON 前后加解释文字，这里做清洗。
    """
    # 尝试直接解析
    try:
        return json.loads(raw_output.strip())
    except json.JSONDecodeError:
        pass

    # 提取 JSON 块（处理 LLM 在 JSON 前后加文字的情况）
    json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从输出中解析 JSON: {raw_output[:200]}")


# 示例 Schema
PRODUCT_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "key_points": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "summary": {"type": "string"},
    },
    "required": ["sentiment", "score", "key_points", "summary"],
}


# ─────────────────────────────────────────────────────────
# 2. Guardrail — 输出验证护栏
# ─────────────────────────────────────────────────────────


class OutputGuardrail:
    """
    对 LLM 输出做多层验证，不符合要求的输出不放行。

    设计原则：
    - 每个 check 独立，方便扩展和测试
    - 失败时返回原因，便于追踪和改进 Prompt
    """

    def __init__(self):
        self._checks = []

    def add_check(self, name: str, fn):
        """注册一个验证函数，fn(output) -> (bool, str)"""
        self._checks.append((name, fn))
        return self  # 支持链式调用

    def validate(self, output: str) -> tuple[bool, list[str]]:
        """运行所有检查，返回 (通过?, 失败原因列表)"""
        failures = []
        for name, fn in self._checks:
            passed, reason = fn(output)
            if not passed:
                failures.append(f"[{name}] {reason}")
        return len(failures) == 0, failures


# 内置的常用 Guardrail 检查
def check_no_pii(output: str) -> tuple[bool, str]:
    """检测是否包含手机号、邮箱等 PII"""
    phone_pattern = r"1[3-9]\d{9}"
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    if re.search(phone_pattern, output):
        return False, "输出包含手机号码"
    if re.search(email_pattern, output):
        return False, "输出包含电子邮件地址"
    return True, ""


def check_length(min_len: int = 10, max_len: int = 2000):
    """工厂函数：生成长度检查器"""

    def _check(output: str) -> tuple[bool, str]:
        if len(output) < min_len:
            return False, f"输出过短（{len(output)} 字符，最少 {min_len}）"
        if len(output) > max_len:
            return False, f"输出过长（{len(output)} 字符，最多 {max_len}）"
        return True, ""

    return _check


def check_no_refusal(output: str) -> tuple[bool, str]:
    """检测 LLM 是否拒绝回答（对某些场景是异常情况）"""
    refusal_keywords = ["我无法", "我不能", "抱歉，我不", "I cannot", "I'm unable"]
    for kw in refusal_keywords:
        if kw in output:
            return False, f"LLM 拒绝回答（包含关键词: {kw!r}）"
    return True, ""


# 组装护栏
customer_service_guardrail = (
    OutputGuardrail().add_check("no_pii", check_no_pii).add_check("length", check_length(20, 500))
)


# ─────────────────────────────────────────────────────────
# 3. Eval 框架骨架
# ─────────────────────────────────────────────────────────

from dataclasses import dataclass


@dataclass
class EvalCase:
    """单个测试用例"""

    id: str
    input: str
    expected_keywords: list[str]  # 输出中应该包含的关键词
    forbidden_keywords: list[str]  # 输出中不应该包含的关键词
    min_score: float = 0.6  # 最低通过分数


@dataclass
class EvalResult:
    case_id: str
    score: float
    passed: bool
    details: dict


def run_keyword_eval(case: EvalCase, actual_output: str) -> EvalResult:
    """
    基于关键词的确定性 Eval（Level 1，最快，适合冒烟测试）。
    """
    output_lower = actual_output.lower()
    hits = sum(1 for kw in case.expected_keywords if kw.lower() in output_lower)
    violations = sum(1 for kw in case.forbidden_keywords if kw.lower() in output_lower)

    keyword_score = hits / len(case.expected_keywords) if case.expected_keywords else 1.0
    violation_penalty = violations * 0.3
    score = max(0.0, keyword_score - violation_penalty)

    return EvalResult(
        case_id=case.id,
        score=score,
        passed=score >= case.min_score and violations == 0,
        details={
            "keyword_hits": hits,
            "keyword_total": len(case.expected_keywords),
            "violations": violations,
            "score": score,
        },
    )


def run_eval_suite(cases: list[EvalCase], llm_fn) -> dict:
    """
    运行一组 Eval 用例，返回汇总报告。

    llm_fn: 接受 prompt str，返回 output str 的函数
    """
    results = []
    for case in cases:
        output = llm_fn(case.input)
        result = run_keyword_eval(case, output)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    avg_score = sum(r.score for r in results) / len(results)

    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": passed / len(results),
        "avg_score": avg_score,
        "results": [vars(r) for r in results],
    }


# ─────────────────────────────────────────────────────────
# 4. 简单 RAG 管道骨架（无需外部依赖的示意版）
# ─────────────────────────────────────────────────────────


class SimpleRAGPipeline:
    """
    最简化的 RAG 管道，演示核心流程。
    生产环境需替换为真实的向量数据库和 Embedding 模型。
    """

    def __init__(self):
        self._chunks: list[dict] = []  # {text: str, metadata: dict}

    def index(self, text: str, metadata: dict = None):
        """
        离线阶段：把文档切块并存储。
        生产中：对每个 chunk 做 Embedding，存入向量库。
        """
        # 简单按句子切块（生产中用语义分块）
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        for sent in sentences:
            self._chunks.append(
                {
                    "text": sent,
                    "metadata": metadata or {},
                }
            )

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        在线阶段：检索最相关的内容块。
        生产中：对 query 做 Embedding，向量相似度检索。
        """
        # 这里用关键词重叠做简单模拟（生产中用向量检索 + Rerank）
        query_words = set(query.lower().split())
        scored = []
        for chunk in self._chunks:
            chunk_words = set(chunk["text"].lower().split())
            overlap = len(query_words & chunk_words)
            scored.append((overlap, chunk["text"]))

        scored.sort(reverse=True)
        return [text for _, text in scored[:top_k] if text]

    def build_prompt(self, query: str, retrieved_chunks: list[str]) -> str:
        """把检索结果注入 Prompt"""
        context = "\n\n".join(f"[来源 {i+1}]\n{chunk}" for i, chunk in enumerate(retrieved_chunks))
        return f"""请根据以下参考资料回答问题。
如果参考资料中没有相关信息，请明确说明"根据现有资料无法回答"，不要编造。

参考资料：
{context}

问题：{query}

回答："""


# ─────────────────────────────────────────────────────────
# 使用示例
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 1. Structured Output Prompt ===")
    prompt = build_structured_prompt(
        "这款耳机音质很好，但续航只有 4 小时，有点失望", PRODUCT_REVIEW_SCHEMA
    )
    print(prompt[:300] + "...\n")

    # 模拟 LLM 输出（实际需要调用 API）
    mock_llm_output = '{"sentiment": "neutral", "score": 3, "key_points": ["音质好", "续航短"], "summary": "音质出色但续航不足"}'
    parsed = parse_structured_output(mock_llm_output, PRODUCT_REVIEW_SCHEMA)
    print("解析结果:", parsed)

    print("\n=== 2. Guardrail 验证 ===")
    safe_output = "您好！您的订单将在 3 个工作日内发货，请耐心等待。"
    risky_output = "您好！请联系 13812345678 获取帮助。"

    passed, failures = customer_service_guardrail.validate(safe_output)
    print(f"安全输出: {'通过 ✓' if passed else '失败 ✗'}")

    passed, failures = customer_service_guardrail.validate(risky_output)
    print(f"危险输出: {'通过 ✓' if passed else '失败 ✗'} — {failures}")

    print("\n=== 3. Eval Suite ===")
    eval_cases = [
        EvalCase(
            id="test_order_status",
            input="我的订单什么时候发货？",
            expected_keywords=["工作日", "发货"],
            forbidden_keywords=["手机", "电话"],
        ),
    ]
    mock_llm = lambda prompt: "您的订单将在 3 个工作日内发货。"
    report = run_eval_suite(eval_cases, mock_llm)
    print(f"Eval 结果: {report['passed']}/{report['total']} 通过，平均分 {report['avg_score']:.2f}")

    print("\n=== 4. RAG 管道 ===")
    rag = SimpleRAGPipeline()
    rag.index("退款政策：购买后 7 天内支持无理由退款。退款将在 3–5 个工作日内到账。")
    rag.index("发货政策：所有订单在确认付款后 24 小时内发货，节假日除外。")

    query = "我能退款吗？"
    chunks = rag.retrieve(query)
    prompt = rag.build_prompt(query, chunks)
    print("RAG 构建的 Prompt（前 200 字）:")
    print(prompt[:200] + "...")
