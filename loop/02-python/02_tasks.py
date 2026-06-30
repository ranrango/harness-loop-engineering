"""
02_tasks.py — asyncio.Task 与并发控制

Task 是被事件循环"托管"的 coroutine，可以独立运行。
直接运行：python 02_tasks.py
"""

import asyncio
import time
import random


# ─────────────────────────────────────────────────────────
# 1. create_task：后台运行，不等待
# ─────────────────────────────────────────────────────────

async def background_job(name: str, duration: float) -> str:
    await asyncio.sleep(duration)
    return f"{name} done"


async def demo_create_task():
    """
    create_task 立即把任务放入事件循环后台，
    当前协程可以继续做其他事。
    """
    print("主任务开始")

    # 创建任务但不等待
    task1 = asyncio.create_task(background_job("job-1", 1.0), name="job-1")
    task2 = asyncio.create_task(background_job("job-2", 0.5), name="job-2")

    print("任务已在后台启动，主任务继续执行...")
    await asyncio.sleep(0.1)           # 让出控制权，任务开始运行
    print("主任务做了一些其他工作")

    # 等待所有任务完成
    result1 = await task1
    result2 = await task2
    print(f"结果: {result1}, {result2}")


# ─────────────────────────────────────────────────────────
# 2. gather vs as_completed
# ─────────────────────────────────────────────────────────

async def fetch_item(item_id: int) -> dict:
    """模拟耗时不均的 API 请求"""
    delay = random.uniform(0.1, 1.0)
    await asyncio.sleep(delay)
    return {"id": item_id, "delay": round(delay, 2)}


async def demo_gather():
    """
    gather：等所有任务完成后，按原始顺序返回结果。
    适合：需要全部结果才能继续处理。
    """
    print("\n[gather] 等待所有任务完成...")
    start = time.perf_counter()

    results = await asyncio.gather(*[fetch_item(i) for i in range(5)])

    elapsed = time.perf_counter() - start
    print(f"[gather] 全部完成，耗时 {elapsed:.2f}s")
    print(f"结果（按原始顺序）: {[r['id'] for r in results]}")


async def demo_as_completed():
    """
    as_completed：哪个先完成先处理哪个。
    适合：可以流式处理结果，不需要等全部完成。
    """
    print("\n[as_completed] 谁先好就处理谁...")
    start = time.perf_counter()

    tasks = [asyncio.create_task(fetch_item(i)) for i in range(5)]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        elapsed = time.perf_counter() - start
        print(f"  [{elapsed:.2f}s] item-{result['id']} 完成（等待了 {result['delay']}s）")


# ─────────────────────────────────────────────────────────
# 3. 任务取消
# ─────────────────────────────────────────────────────────

async def long_running_task():
    try:
        print("长任务开始...")
        await asyncio.sleep(10)
        print("长任务完成（不会执行到这里）")
    except asyncio.CancelledError:
        print("长任务被取消——做清理工作...")
        # 重要：取消后可以做清理（关闭连接、释放锁等）
        raise  # 必须重新抛出，让调用方知道任务已取消


async def demo_cancel():
    task = asyncio.create_task(long_running_task())

    await asyncio.sleep(0.5)   # 让任务跑一会儿

    print("主动取消任务...")
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("确认：任务已取消")

    print(f"任务状态: cancelled={task.cancelled()}")


# ─────────────────────────────────────────────────────────
# 4. 超时控制
# ─────────────────────────────────────────────────────────

async def demo_timeout():
    print("\n--- 超时演示 ---")

    # wait_for 在超时后取消任务
    try:
        result = await asyncio.wait_for(
            fetch_item(99),
            timeout=0.05   # 50ms 超时，但任务需要 100ms~1s
        )
        print(f"成功: {result}")
    except asyncio.TimeoutError:
        print("任务超时，已取消")

    # Python 3.11+ 的 timeout() context manager（更现代）
    try:
        async with asyncio.timeout(0.05):
            result = await fetch_item(88)
    except TimeoutError:
        print("timeout() context manager 超时")


# ─────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────

async def main():
    print("=== 1. create_task ===")
    await demo_create_task()

    print("\n=== 2. gather vs as_completed ===")
    await demo_gather()
    await demo_as_completed()

    print("\n=== 3. 任务取消 ===")
    await demo_cancel()

    print("\n=== 4. 超时 ===")
    await demo_timeout()


if __name__ == "__main__":
    asyncio.run(main())

# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 用 gather(return_exceptions=True) 运行一组任务，
#    其中一个会抛出异常，验证其他任务仍然完成。
#
# 2. 实现一个 run_with_retry(coro_fn, max_retries=3) 函数，
#    自动重试失败的 coroutine，每次重试前等待 2^attempt 秒（指数退避）。
