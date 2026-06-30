"""
test_02_fixtures.py — pytest Fixture 深入演示

涵盖：
- scope 层级（function / class / module / session）
- yield fixture（setup + teardown 合一）
- fixture 依赖其他 fixture
- conftest.py 中的共享 fixture（见 conftest.py）
"""

import pytest
from unittest.mock import MagicMock
from src.order import InventoryClient, PaymentGateway, EmailService, OrderService


# ─────────────────────────────────────────────────────────
# Fixture 定义
# ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_inventory():
    """
    每个测试都获得一个全新的 Mock——scope 默认是 function。
    这保证了测试之间的 Mock 调用记录互不干扰。
    """
    inv = MagicMock(spec=InventoryClient)
    inv.check_availability.return_value = True
    inv.reserve.return_value = "reservation-abc"
    return inv


@pytest.fixture
def mock_payment():
    pay = MagicMock(spec=PaymentGateway)
    pay.charge.return_value = {"status": "success", "transaction_id": "txn-001"}
    return pay


@pytest.fixture
def mock_email():
    return MagicMock(spec=EmailService)


@pytest.fixture
def order_service(mock_inventory, mock_payment, mock_email):
    """
    组合 fixture：依赖上面三个 fixture。
    pytest 自动解析依赖图，按正确顺序初始化。
    """
    return OrderService(
        inventory=mock_inventory,
        payment=mock_payment,
        email=mock_email,
    )


@pytest.fixture
def sample_items():
    """复用的测试数据"""
    return [
        {"product_id": 1, "quantity": 2, "unit_price": 15.0},
        {"product_id": 2, "quantity": 1, "unit_price": 30.0},
    ]


# ─────────────────────────────────────────────────────────
# 演示 yield fixture（含 teardown）
# ─────────────────────────────────────────────────────────

@pytest.fixture
def tracked_resource():
    """
    yield 前是 setup，yield 后是 teardown。
    即使测试失败，teardown 也会执行。
    """
    resource = {"log": [], "closed": False}
    resource["log"].append("opened")

    yield resource  # 这里把资源交给测试

    # 测试结束后（无论成功或失败）自动执行：
    resource["closed"] = True
    resource["log"].append("closed")


# ─────────────────────────────────────────────────────────
# 测试
# ─────────────────────────────────────────────────────────

class TestFixtureBasics:

    def test_yield_fixture_teardown_always_runs(self, tracked_resource):
        tracked_resource["log"].append("used")
        assert tracked_resource["log"] == ["opened", "used"]
        # teardown 在这之后执行，在当前测试范围内看不到

    def test_each_test_gets_fresh_fixture(self, mock_inventory):
        # 每次都是全新的 Mock，call_count 从 0 开始
        assert mock_inventory.check_availability.call_count == 0


class TestOrderServiceWithFixtures:

    def test_successful_order_returns_confirmed_status(
        self, order_service, sample_items
    ):
        order = order_service.place_order(
            customer_id=1,
            customer_email="alice@example.com",
            items=sample_items,
        )
        assert order.status == "confirmed"
        assert order.total == 60.0  # 2×15 + 1×30

    def test_successful_order_calls_all_dependencies(
        self, order_service, mock_inventory, mock_payment, mock_email, sample_items
    ):
        order = order_service.place_order(
            customer_id=1,
            customer_email="alice@example.com",
            items=sample_items,
        )
        # 验证每个依赖都被正确调用
        assert mock_inventory.check_availability.call_count == 2  # 两件商品
        assert mock_inventory.reserve.call_count == 2
        mock_payment.charge.assert_called_once_with(1, 60.0)
        mock_email.send_confirmation.assert_called_once_with(
            "alice@example.com", order.id
        )


# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 创建一个 scope="module" 的 fixture，并在两个测试中使用它。
#    打印一条消息验证它只被初始化了一次。
#
# 2. 创建一个 fixture，模拟"数据库连接"并在 teardown 里打印"连接已关闭"。
