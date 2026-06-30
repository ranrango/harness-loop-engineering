"""
01_basics.py — asyncio 基础

从零理解 coroutine、await、事件循环的关系。
直接运行：python 01_basics.py
"""

import asyncio
import time


# ─────────────────────────────────────────────────────────
# 1. coroutine 和 await 的本质
# ─────────────────────────────────────────────────────────

async def say_hello(name: str, delay: float) -> str:
    """
    async def 定义 coroutine 函数。
    调用它不会立即执行——它返回一个 coroutine 对象。
    只有被 await（或放入事件循环）才真正运行。
    """
    print(f"[{name}] 开始等待 {delay}s...")
    await asyncio.sleep(delay)   # 让出控制权，等 delay 秒后继续
    print(f"[{name}] 等待完成")
    return f"Hello from {name}"


async def demo_sequential():
    """同步风格：顺序等待，总耗时 = 各任务之和"""
    start = time.perf_counter()

    result1 = await say_hello("Alice", 1.0)
    result2 = await say_hello("Bob", 0.5)

    elapsed = time.perf_counter() - start
    print(f"顺序执行耗时: {elapsed:.2f}s（预期 ~1.5s）")
    print(f"结果: {result1}, {result2}")


async def demo_concurrent():
    """并发风格：同时等待，总耗时 = 最长任务"""
    start = time.perf_counter()

    # asyncio.gather 并发运行多个 coroutine
    result1, result2 = await asyncio.gather(
        say_hello("Alice", 1.0),
        say_hello("Bob", 0.5),
    )

    elapsed = time.perf_counter() - start
    print(f"并发执行耗时: {elapsed:.2f}s（预期 ~1.0s）")
    print(f"结果: {result1}, {result2}")


# ─────────────────────────────────────────────────────────
# 2. 同步 vs 异步的速度对比
# ─────────────────────────────────────────────────────────

def slow_sync_fetch(url: str) -> str:
    """模拟同步 HTTP 请求（实际会 sleep）"""
    time.sleep(0.5)   # 阻塞整个程序
    return f"data from {url}"


async def fast_async_fetch(url: str) -> str:
    """模拟异步 HTTP 请求（等待期间让出控制权）"""
    await asyncio.sleep(0.5)   # 不阻塞，其他任务可以运行
    return f"data from {url}"


def benchmark_sync():
    """串行请求 5 个 URL"""
    urls = [f"https://api.example.com/item/{i}" for i in range(5)]
    start = time.perf_counter()

    results = [slow_sync_fetch(url) for url in urls]

    elapsed = time.perf_counter() - start
    print(f"同步（串行）: {elapsed:.2f}s，获取 {len(results)} 条数据")
    return results


async def benchmark_async():
    """并发请求 5 个 URL"""
    urls = [f"https://api.example.com/item/{i}" for i in range(5)]
    start = time.perf_counter()

    results = await asyncio.gather(*[fast_async_fetch(url) for url in urls])

    elapsed = time.perf_counter() - start
    print(f"异步（并发）: {elapsed:.2f}s，获取 {len(results)} 条数据")
    return results


# ─────────────────────────────────────────────────────────
# 3. 注意：CPU 密集型任务不适合 asyncio
# ─────────────────────────────────────────────────────────

async def cpu_heavy():
    """
    警告：CPU 密集型操作会阻塞事件循环！
    asyncio 的并发基于协作让步（await），如果你不 await，就会阻塞。
    """
    # 错误做法：在 async 函数里做 CPU 密集计算
    result = sum(range(10_000_000))   # 阻塞约 0.3s，其他任务无法运行

    # 正确做法：用 run_in_executor 放到线程池
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: sum(range(10_000_000)))
    return result


# ─────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────

async def main():
    print("=" * 50)
    print("1. 顺序 vs 并发")
    print("=" * 50)
    await demo_sequential()
    print()
    await demo_concurrent()

    print()
    print("=" * 50)
    print("2. 同步 vs 异步 Benchmark")
    print("=" * 50)
    benchmark_sync()
    await benchmark_async()


if __name__ == "__main__":
    # asyncio.run() 是 Python 3.7+ 的标准入口
    # 它创建事件循环、运行 coroutine、关闭循环
    asyncio.run(main())

# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 修改 demo_concurrent，同时运行 10 个不同延迟的任务，
#    验证总时间接近最长任务的时间。
#
# 2. 故意在 async 函数里调用 time.sleep(1)（非 await），
#    观察它如何阻塞整个事件循环——这是常见的异步 bug。
