"""
被测代码：订单服务

这个模块故意依赖外部服务（数据库、支付、邮件），
让我们能演示如何用 Mock 隔离这些依赖。
"""

from dataclasses import dataclass, field
from typing import Optional


class OutOfStockError(Exception):
    pass


class PaymentDeclinedError(Exception):
    pass


@dataclass
class OrderItem:
    product_id: int
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    id: int
    customer_id: int
    items: list[OrderItem] = field(default_factory=list)
    status: str = "pending"

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)


class InventoryClient:
    """真实库存服务客户端（会发 HTTP 请求）"""

    def check_availability(self, product_id: int, quantity: int) -> bool:
        raise NotImplementedError("需要连接真实库存服务")

    def reserve(self, product_id: int, quantity: int) -> str:
        raise NotImplementedError("需要连接真实库存服务")

    def release(self, reservation_id: str) -> None:
        raise NotImplementedError("需要连接真实库存服务")


class PaymentGateway:
    """真实支付网关（会真实扣款）"""

    def charge(self, customer_id: int, amount: float) -> dict:
        raise NotImplementedError("需要连接真实支付网关")


class EmailService:
    """真实邮件服务"""

    def send_confirmation(self, to: str, order_id: int) -> None:
        raise NotImplementedError("需要连接真实邮件服务")


class OrderService:
    """
    订单处理服务。

    依赖通过构造函数注入——这是让代码可测试的关键：
    生产代码传入真实实现，测试代码传入 Mock。
    """

    def __init__(
        self,
        inventory: InventoryClient,
        payment: PaymentGateway,
        email: EmailService,
    ):
        self.inventory = inventory
        self.payment = payment
        self.email = email
        self._orders: dict[int, Order] = {}
        self._next_id = 1

    def place_order(
        self,
        customer_id: int,
        customer_email: str,
        items: list[dict],
    ) -> Order:
        """
        下单流程：
        1. 检查库存
        2. 预留库存
        3. 发起支付
        4. 如支付失败，释放库存
        5. 发送确认邮件
        """
        order_items = [
            OrderItem(
                product_id=i["product_id"],
                quantity=i["quantity"],
                unit_price=i["unit_price"],
            )
            for i in items
        ]

        # Step 1: 检查所有商品库存
        for item in order_items:
            if not self.inventory.check_availability(item.product_id, item.quantity):
                raise OutOfStockError(
                    f"Product {item.product_id} has insufficient stock"
                )

        # Step 2: 预留库存
        reservation_ids = []
        for item in order_items:
            rid = self.inventory.reserve(item.product_id, item.quantity)
            reservation_ids.append(rid)

        # Step 3: 支付（失败则回滚库存预留）
        order = Order(
            id=self._next_id,
            customer_id=customer_id,
            items=order_items,
        )
        self._next_id += 1

        try:
            self.payment.charge(customer_id, order.total)
        except PaymentDeclinedError:
            # 回滚：释放已预留的库存
            for rid in reservation_ids:
                self.inventory.release(rid)
            raise

        # Step 4: 确认
        order.status = "confirmed"
        self._orders[order.id] = order
        self.email.send_confirmation(customer_email, order.id)

        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self._orders.get(order_id)
