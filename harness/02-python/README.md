# Harness Engineering — Python 示例（pytest）

## 快速开始

```bash
cd harness/02-python
pip install -r requirements.txt
pytest -v
```

---

## 文件说明

| 文件 | 演示内容 |
|------|---------|
| `src/order.py` | 被测代码：订单服务（含外部依赖） |
| `tests/test_01_basics.py` | 基础：AAA 模式、异常断言 |
| `tests/test_02_fixtures.py` | Fixture：scope、yield、依赖注入 |
| `tests/test_03_mock.py` | Mock：patch、side_effect、assert_called |
| `tests/test_04_parametrize.py` | 参数化：边界值、等价类 |
| `tests/test_05_integration.py` | 集成测试：SQLite 内存库 + 事务回滚 |

---

## 核心知识点速查

### Fixture 的 scope 层级
```
session  > package  > module  > class  > function（默认）
贵/慢     ←────────────────────────────→  便宜/快
共享范围大                               每个测试独立
```

### Mock vs Stub vs Spy（Python 视角）
```python
from unittest.mock import Mock, MagicMock, patch

stub = Mock(return_value=42)          # Stub：固定返回值
spy  = MagicMock(wraps=real_obj)      # Spy：包装真实对象，同时记录调用
mock = Mock()                          # Mock：手动设置 return_value 后验证调用
```
