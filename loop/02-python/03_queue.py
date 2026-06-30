"""
03_queue.py — asyncio.Queue：生产者-消费者模式

Queue 是协程间安全传递数据的标准方式。
直接运行：python 03_queue.py
"""

import asyncio
import random
import time


# ─────────────────────────────────────────────────────────
# 1. 基础生产者-消费者
# ─────────────────────────────────────────────────────────

async def producer(queue: asyncio.Queue, name: str, count: int):
    for i in range(count):
        item = f"{name}-item-{i}"
        await queue.put(item)             # 如果队列满，这里会等待
        print(f"  [生产] {item} (队列大小: {queue.qsize()})")
        await asyncio.sleep(random.uniform(0.05, 0.2))
    print(f"  [{name}] 生产完毕")


async def consumer(queue: asyncio.Queue, name: str):
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=1.0)
            print(f"  [消费] {name} 处理 {item}")
            await asyncio.sleep(random.uniform(0.1, 0.3))   # 模拟处理耗时
            queue.task_done()            # 通知 queue.join() 这个任务完成了
        except asyncio.TimeoutError:
            print(f"  [{name}] 超时无任务，退出")
            break


async def demo_basic_queue():
    queue = asyncio.Queue(maxsize=5)   # 最多存 5 个，满了生产者等待

    # 启动 2 个消费者，1 个生产者
    consumers = [
        asyncio.create_task(consumer(queue, f"consumer-{i}"))
        for i in range(2)
    ]
    prod = asyncio.create_task(producer(queue, "prod", count=10))

    await prod                # 等生产完成
    await queue.join()        # 等队列全部消费完
    for c in consumers:
        c.cancel()


# ─────────────────────────────────────────────────────────
# 2. 限速（Semaphore）：控制并发数量
# ─────────────────────────────────────────────────────────

async def fetch_url(url: str, semaphore: asyncio.Semaphore) -> dict:
    """
    Semaphore 限制同时运行的任务数量。
    适合：并发调用外部 API 时不超过 API 的速率限制。
    """
    async with semaphore:   # 最多 N 个任务同时持有锁
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)
        return {"url": url, "status": 200}


async def demo_semaphore():
    print("\n--- Semaphore 限速演示 ---")
    urls = [f"https://api.example.com/item/{i}" for i in range(20)]

    # 不限速：同时发起 20 个请求
    start = time.perf_counter()
    results_unlimited = await asyncio.gather(
        *[fetch_url(url, asyncio.Semaphore(9999)) for url in urls]
    )
    elapsed_unlimited = time.perf_counter() - start

    # 限速：最多同时 3 个请求
    semaphore = asyncio.Semaphore(3)
    start = time.perf_counter()
    results_limited = await asyncio.gather(
        *[fetch_url(url, semaphore) for url in urls]
    )
    elapsed_limited = time.perf_counter() - start

    print(f"不限速（20 并发）: {elapsed_unlimited:.2f}s")
    print(f"限速（3 并发）:    {elapsed_limited:.2f}s")
    print(f"两种方式都成功获取了 {len(results_limited)} 条数据")


# ─────────────────────────────────────────────────────────
# 3. 事件（Event）：协程间同步信号
# ─────────────────────────────────────────────────────────

async def waiter(event: asyncio.Event, name: str):
    print(f"  [{name}] 等待信号...")
    await event.wait()           # 阻塞直到 event 被 set()
    print(f"  [{name}] 收到信号，继续执行！")


async def demo_event():
    print("\n--- Event 信号演示 ---")
    event = asyncio.Event()

    # 启动多个等待者
    waiters = [
        asyncio.create_task(waiter(event, f"waiter-{i}"))
        for i in range(3)
    ]

    print("  [main] 2秒后发送信号...")
    await asyncio.sleep(0.5)

    print("  [main] 发送信号！")
    event.set()   # 唤醒所有等待者

    await asyncio.gather(*waiters)


# ─────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────

async def main():
    print("=== 1. 生产者-消费者 ===")
    await demo_basic_queue()

    await demo_semaphore()
    await demo_event()


if __name__ == "__main__":
    asyncio.run(main())

# ─────────────────────────────────────────────────────────
# 练习
# ─────────────────────────────────────────────────────────
#
# 1. 实现一个"工作池（Worker Pool）"：
#    - 固定 N 个 worker coroutine 持续从队列取任务
#    - 主协程往队列放任务
#    - 所有任务完成后优雅退出（用 sentinel None 值通知 worker 退出）
#
# 2. 用 asyncio.Lock 实现一个线程安全的计数器，
#    验证 1000 个并发任务同时递增不会丢失更新。
