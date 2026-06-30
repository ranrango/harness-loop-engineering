"""
test_04_parametrize.py — 参数化测试

参数化让你用一份测试逻辑覆盖多组输入，避免复制粘贴。
关键原则：每组参数都是一个独立测试用例，失败时只显示那一组。
"""

import pytest
from src.order import OrderItem, Order


# ─────────────────────────────────────────────────────────
# 基础参数化
# ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("quantity, price, expected", [
    (1,   10.0,  10.0),   # 单件
    (3,   10.0,  30.0),   # 多件
    (0,   10.0,   0.0),   # 边界：数量为 0
    (1,    0.0,   0.0),   # 边界：价格为 0
    (100, 99.99, 9999.0), # 大数值
])
def test_order_item_subtotal(quantity, price, expected):
    item = OrderItem(product_id=1, quantity=quantity, unit_price=price)
    assert item.subtotal == pytest.approx(expected)  # approx 处理浮点误差


# ─────────────────────────────────────────────────────────
# 用 ids 让参数化测试名称更可读
# ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("email, is_valid", [
    ("user@example.com",   True),
    ("name+tag@domain.io", True),
    ("invalid-email",      False),
    ("@missing-local.com", False),
    ("missing-domain@",    False),
    ("",                   False),
], ids=[
    "valid_standard",
    "valid_with_plus_tag",
    "invalid_no_at",
    "invalid_no_local",
    "invalid_no_domain",
    "invalid_empty",
])
def test_email_format(email, is_valid):
    """演示：ids 参数让测试失败时报告更易读"""
    import re
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    result = bool(re.match(pattern, email))
    assert result == is_valid


# ─────────────────────────────────────────────────────────
# 多个参数化装饰器：笛卡尔积
# ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("quantity", [1, 5, 10])
@pytest.mark.parametrize("price", [1.0, 10.0, 100.0])
def test_subtotal_combinations(quantity, price):
    """
    3 × 3 = 9 个测试用例自动生成。
    适合验证组合逻辑，但注意数量爆炸——通常 2-3 个维度即可。
    """
    item = OrderItem(product_id=1, quantity=quantity, unit_price=price)
    assert item.subtotal == pytest.approx(quantity * price)


# ─────────────────────────────────────────────────────────
# 参数化测试 + 异常
# ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("items, expected_total", [
    ([], 0.0),
    ([{"product_id": 1, "quantity": 2, "unit_price": 5.0}], 10.0),
    (
        [
            {"product_id": 1, "quantity": 1, "unit_price": 10.0},
            {"product_id": 2, "quantity": 3, "unit_price": 20.0},
        ],
        70.0,
    ),
])
def test_order_total_with_various_items(items, expected_total):
    order = Order(
        id=1,
        customer_id=42,
        items=[
            OrderItem(
                product_id=i["product_id"],
                quantity=i["quantity"],
                unit_price=i["unit_price"],
            )
            for i in items
        ],
    )
    assert order.total == pytest.approx(expected_total)


# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 为一个 `calculate_discount(price, tier)` 函数写参数化测试：
#    - tier="bronze" → 5% 折扣
#    - tier="silver" → 10% 折扣
#    - tier="gold"   → 20% 折扣
#    - tier="unknown" → 0% 折扣
#
# 2. 使用 pytest.mark.parametrize 结合 pytest.raises，
#    验证多种无效输入都会抛出相同的异常类型。
