"""
test_03_mock.py — Mock 深入演示

涵盖：
- patch 的三种写法（decorator / context manager / mocker fixture）
- return_value vs side_effect
- assert_called_* 系列方法
- Mock 调用顺序验证
- 库存回滚场景（复杂交互验证）
"""

import pytest
from unittest.mock import MagicMock, call, patch
from src.order import (
    OrderService, InventoryClient, PaymentGateway,
    EmailService, OutOfStockError, PaymentDeclinedError,
)


# ─────────────────────────────────────────────────────────
# return_value vs side_effect
# ─────────────────────────────────────────────────────────

class TestMockReturnValues:

    def test_return_value_always_returns_same_thing(self):
        mock = MagicMock()
        mock.fetch.return_value = {"data": 42}

        assert mock.fetch() == {"data": 42}
        assert mock.fetch("ignored", "args") == {"data": 42}  # 参数无关

    def test_side_effect_list_returns_different_values_each_call(self):
        """side_effect 为列表时，每次调用返回下一个值"""
        mock = MagicMock()
        mock.get_status.side_effect = ["loading", "loading", "done"]

        assert mock.get_status() == "loading"
        assert mock.get_status() == "loading"
        assert mock.get_status() == "done"

    def test_side_effect_function_computes_return_value(self):
        """side_effect 为函数时，用调用参数计算返回值"""
        mock = MagicMock()
        mock.multiply.side_effect = lambda x, y: x * y

        assert mock.multiply(3, 4) == 12
        assert mock.multiply(2, 5) == 10

    def test_side_effect_exception_makes_mock_raise(self):
        """side_effect 为异常实例/类时，调用会抛出该异常"""
        mock = MagicMock()
        mock.connect.side_effect = ConnectionError("host unreachable")

        with pytest.raises(ConnectionError, match="host unreachable"):
            mock.connect()


# ─────────────────────────────────────────────────────────
# 断言 Mock 调用情况
# ─────────────────────────────────────────────────────────

class TestMockAssertions:

    def test_assert_called_once_with(self):
        mock = MagicMock()
        mock.send("hello", to="bob")

        mock.send.assert_called_once_with("hello", to="bob")

    def test_assert_called_with_only_checks_last_call(self):
        mock = MagicMock()
        mock.log("first")
        mock.log("second")

        # assert_called_with 只检查最近一次调用
        mock.log.assert_called_with("second")

    def test_assert_any_call_checks_all_calls(self):
        mock = MagicMock()
        mock.notify("admin")
        mock.notify("user")

        mock.notify.assert_any_call("admin")  # 曾经以这个参数调用过
        mock.notify.assert_any_call("user")

    def test_call_args_list_for_full_history(self):
        """call_args_list 记录所有调用，顺序很重要时用这个"""
        mock = MagicMock()
        mock.reserve(product_id=1, quantity=2)
        mock.reserve(product_id=3, quantity=1)

        assert mock.reserve.call_count == 2
        assert mock.reserve.call_args_list == [
            call(product_id=1, quantity=2),
            call(product_id=3, quantity=1),
        ]

    def test_not_called(self):
        mock = MagicMock()
        mock.send_email.assert_not_called()


# ─────────────────────────────────────────────────────────
# 关键业务场景：支付失败时库存回滚
# ─────────────────────────────────────────────────────────

class TestPaymentRollback:
    """
    这个测试演示了 Mock 最有价值的场景：
    验证"出错时系统是否正确清理了副作用"
    """

    def test_payment_failure_releases_all_reserved_inventory(self):
        # Arrange
        inventory = MagicMock(spec=InventoryClient)
        inventory.check_availability.return_value = True
        # 两件商品分别返回不同的预留 ID
        inventory.reserve.side_effect = ["res-001", "res-002"]

        payment = MagicMock(spec=PaymentGateway)
        payment.charge.side_effect = PaymentDeclinedError("Card declined")

        email = MagicMock(spec=EmailService)

        service = OrderService(inventory, payment, email)

        # Act
        with pytest.raises(PaymentDeclinedError):
            service.place_order(
                customer_id=1,
                customer_email="bob@example.com",
                items=[
                    {"product_id": 1, "quantity": 1, "unit_price": 10.0},
                    {"product_id": 2, "quantity": 1, "unit_price": 20.0},
                ],
            )

        # Assert：两个库存预留都被释放了
        assert inventory.release.call_count == 2
        inventory.release.assert_any_call("res-001")
        inventory.release.assert_any_call("res-002")

        # 支付失败后不应该发邮件
        email.send_confirmation.assert_not_called()

    def test_out_of_stock_does_not_attempt_payment(self):
        # 库存不足时，根本不应该尝试支付
        inventory = MagicMock(spec=InventoryClient)
        inventory.check_availability.return_value = False

        payment = MagicMock(spec=PaymentGateway)
        email = MagicMock(spec=EmailService)

        service = OrderService(inventory, payment, email)

        with pytest.raises(OutOfStockError):
            service.place_order(
                customer_id=1,
                customer_email="bob@example.com",
                items=[{"product_id": 1, "quantity": 100, "unit_price": 5.0}],
            )

        payment.charge.assert_not_called()


# ─────────────────────────────────────────────────────────
# patch 的使用方式
# ─────────────────────────────────────────────────────────

class TestPatchUsage:

    def test_patch_as_context_manager(self, mocker):
        """pytest-mock 的 mocker 是最简洁的写法"""
        mock_time = mocker.patch("time.sleep")

        import time
        time.sleep(100)  # 不会真正等 100 秒

        mock_time.assert_called_once_with(100)

    def test_mocker_patch_with_return_value(self, mocker):
        mocker.patch("os.getpid", return_value=99999)

        import os
        assert os.getpid() == 99999


# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 用 side_effect 列表模拟一个"第一次失败，第二次成功"的重试场景。
#    写一个 retry() 函数，然后为它写测试。
#
# 2. 验证 OrderService 在有 2 件商品时，check_availability 和 reserve
#    都被调用了恰好 2 次，且参数正确。
