# Loop Engineering — Python asyncio 示例

## 快速开始

```bash
cd loop/02-python
python -m asyncio   # Python 3.12+ 可以直接进入 asyncio REPL
python 01_basics.py
python 02_tasks.py
python 03_queue.py
python 04_patterns.py
```

**无需安装依赖**，全部使用 Python 标准库。

---

## 文件说明

| 文件 | 演示内容 |
|------|---------|
| `01_basics.py` | coroutine、await、事件循环启动方式 |
| `02_tasks.py` | Task 并发、gather、as_completed |
| `03_queue.py` | asyncio.Queue 生产者-消费者模式 |
| `04_patterns.py` | 超时、重试、信号量限速 |

---

## 核心心智模型

```
普通函数：   def foo()    → 调用立即执行
协程函数：   async def foo() → 调用返回 coroutine 对象，不执行

启动执行：
  asyncio.run(foo())     → 创建事件循环并运行到完成
  await foo()            → 在已有事件循环中等待
  asyncio.create_task()  → 在后台并发执行，不等待
```
