"""
test_01_basics.py — 最基础的 pytest 用法

涵盖：
- AAA（Arrange-Act-Assert）模式
- 断言语法
- 异常断言
- 测试命名约定
"""

import pytest
from src.order import Order, OrderItem, OutOfStockError


# ─────────────────────────────────────────────────────────
# 基础断言
# ─────────────────────────────────────────────────────────

class TestOrderItem:
    """测试 OrderItem 数据类"""

    def test_subtotal_is_quantity_times_unit_price(self):
        # Arrange
        item = OrderItem(product_id=1, quantity=3, unit_price=10.0)

        # Act
        result = item.subtotal

        # Assert
        assert result == 30.0

    def test_subtotal_with_single_item(self):
        item = OrderItem(product_id=1, quantity=1, unit_price=99.99)
        assert item.subtotal == 99.99

    def test_subtotal_with_zero_quantity(self):
        # 边界条件：数量为 0
        item = OrderItem(product_id=1, quantity=0, unit_price=50.0)
        assert item.subtotal == 0.0


class TestOrder:
    """测试 Order 数据类"""

    def test_total_sums_all_items(self):
        # Arrange
        order = Order(
            id=1,
            customer_id=42,
            items=[
                OrderItem(product_id=1, quantity=2, unit_price=10.0),  # 20
                OrderItem(product_id=2, quantity=1, unit_price=30.0),  # 30
            ],
        )

        # Act & Assert（简单逻辑可以合并）
        assert order.total == 50.0

    def test_total_with_no_items_is_zero(self):
        # 边界条件：空订单
        order = Order(id=1, customer_id=42, items=[])
        assert order.total == 0.0

    def test_default_status_is_pending(self):
        order = Order(id=1, customer_id=42)
        assert order.status == "pending"


# ─────────────────────────────────────────────────────────
# 异常断言
# ─────────────────────────────────────────────────────────

class TestExceptionAssertion:
    """演示如何断言代码应该抛出异常"""

    def test_out_of_stock_error_carries_message(self):
        # 断言：抛出特定异常，且消息包含关键词
        with pytest.raises(OutOfStockError, match="insufficient stock"):
            raise OutOfStockError("Product 5 has insufficient stock")

    def test_raises_captures_exception_for_inspection(self):
        # exc_info 让你检查异常对象本身
        with pytest.raises(ValueError) as exc_info:
            int("not-a-number")

        assert "invalid literal" in str(exc_info.value)

    def test_no_exception_raised(self):
        # 验证正常情况下不会抛出异常
        item = OrderItem(product_id=1, quantity=1, unit_price=10.0)
        # 如果下面这行抛出异常，测试失败
        _ = item.subtotal


# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 给 OrderItem 添加一个 `discount` 字段（0.0~1.0 之间的折扣率），
#    修改 subtotal 属性使其应用折扣，然后为这个新逻辑写测试。
#
# 2. 写一个测试，验证当 unit_price 为负数时抛出 ValueError。
#    （先写测试，再修改 OrderItem 让测试通过——这就是 TDD！）
