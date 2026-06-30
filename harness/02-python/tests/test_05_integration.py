"""
test_05_integration.py — 集成测试：SQLite 内存库 + 事务回滚

与单元测试不同，集成测试使用真实的数据库操作。
关键技术：用事务回滚保证每个测试的数据隔离，而不需要每次重建数据库。
"""

import pytest
import sqlite3


# ─────────────────────────────────────────────────────────
# 轻量级"数据库层"（用于演示）
# ─────────────────────────────────────────────────────────

class ProductRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, name: str, price: float, stock: int) -> dict:
        cursor = self.conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name, price, stock),
        )
        return {"id": cursor.lastrowid, "name": name, "price": price, "stock": stock}

    def find_by_id(self, product_id: int) -> dict | None:
        cursor = self.conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "price": row[2], "stock": row[3]}

    def update_stock(self, product_id: int, delta: int) -> None:
        self.conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (delta, product_id),
        )

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_connection():
    """
    整个模块共享一个内存数据库连接（建表一次）。
    scope="module" 的 fixture 只初始化一次，所有测试共用。
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE products (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def db(db_connection):
    """
    每个测试在独立事务中运行。
    yield 之后回滚事务——无论测试成功还是失败。

    这样做的好处：
    - 不需要在每个测试里手动清理数据
    - 测试之间完全隔离
    - 比重建数据库快得多
    """
    db_connection.execute("BEGIN")
    yield db_connection
    db_connection.execute("ROLLBACK")


@pytest.fixture
def repo(db) -> ProductRepository:
    return ProductRepository(db)


# ─────────────────────────────────────────────────────────
# 集成测试
# ─────────────────────────────────────────────────────────

class TestProductRepository:

    def test_create_and_find_product(self, repo):
        product = repo.create(name="Laptop", price=999.99, stock=10)

        found = repo.find_by_id(product["id"])

        assert found is not None
        assert found["name"] == "Laptop"
        assert found["price"] == 999.99
        assert found["stock"] == 10

    def test_find_nonexistent_returns_none(self, repo):
        result = repo.find_by_id(99999)
        assert result is None

    def test_update_stock_increases_correctly(self, repo):
        product = repo.create(name="Mouse", price=29.99, stock=5)

        repo.update_stock(product["id"], -2)  # 购买 2 个

        updated = repo.find_by_id(product["id"])
        assert updated["stock"] == 3

    def test_each_test_starts_with_empty_table(self, repo):
        """
        验证事务回滚隔离：每个测试开始时表都是空的。
        上一个测试创建的 Laptop 已经被回滚，不会出现在这里。
        """
        assert repo.count() == 0

    def test_create_multiple_products_get_different_ids(self, repo):
        p1 = repo.create(name="Keyboard", price=79.99, stock=20)
        p2 = repo.create(name="Monitor", price=299.99, stock=5)

        assert p1["id"] != p2["id"]
        assert repo.count() == 2


# ─────────────────────────────────────────────────────────
# 演示：没有事务隔离时会发生什么（反例）
# ─────────────────────────────────────────────────────────

class TestWithoutIsolation:
    """
    这组测试故意不用事务隔离，演示测试间数据污染的问题。
    注意：如果顺序改变或其他测试创建了数据，这组测试会随机失败。
    """

    def test_bad_practice_creates_data(self, db_connection):
        """这会真正提交数据，影响后续测试"""
        db_connection.execute(
            "INSERT INTO products (name, price, stock) VALUES ('Polluting Product', 1.0, 1)"
        )
        db_connection.commit()
        # ↑ 这条数据在所有后续测试中都可见！

    def test_bad_practice_count_is_unpredictable(self, db_connection):
        """
        这个测试的结果取决于上面那个测试是否先运行——这就是测试顺序依赖。
        """
        count = db_connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        # 如果上面的测试跑了，count 是 1；否则是 0
        # 这类测试是随机失败的根源，应该避免
        assert count >= 0  # 只能做这么弱的断言

    @pytest.fixture(autouse=True)
    def cleanup(self, db_connection):
        """补救措施：每个测试后清理脏数据"""
        yield
        db_connection.execute("DELETE FROM products")
        db_connection.commit()


# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 给 ProductRepository 添加一个 search_by_name(keyword) 方法，
#    然后写集成测试验证模糊匹配功能。
#
# 2. 实现一个 transfer_stock(from_id, to_id, amount) 方法，
#    写测试验证：转移成功时两端库存正确更新；
#    如果来源库存不足，抛出异常且两端库存不变。
