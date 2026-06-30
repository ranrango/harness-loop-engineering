# Loop Engineering — 核心概念

Loop Engineering 研究如何高效管理**并发任务的调度与执行**，核心工具是**事件循环（Event Loop）**。

---

## 1. 为什么需要 Loop？

考虑这个场景：你的服务器需要同时处理 10,000 个连接。

**方案 A：每个连接一个线程**
```
连接 1 → 线程 1（等待数据库...）
连接 2 → 线程 2（等待数据库...）
...
连接 10000 → 线程 10000（等待数据库...）

问题：10000 个线程同时等待，大量 CPU/内存被占用在"什么都不做"的线程上。
```

**方案 B：事件循环（Event Loop）**
```
单线程循环：
while true:
    event = get_next_ready_event()
    handle(event)              ← 处理就绪的事件

等待数据库时，控制权还给循环，去处理其他就绪事件。
没有等待，没有浪费。
```

---

## 2. 事件循环的本质

```
┌─────────────────────────────────────────────────────────┐
│                    Event Loop                           │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌────────────────────┐ │
│  │ 任务队列  │───▶│  执行栈  │───▶│  I/O / Timer 就绪  │ │
│  │(Task Queue)   │(Call Stack)   │  → 放入任务队列     │ │
│  └──────────┘    └──────────┘    └────────────────────┘ │
│       ↑                                    │            │
│       └────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

**关键行为**：
1. 执行栈清空后，从任务队列取下一个任务
2. 每次只执行一个任务（单线程）
3. 任务执行期间，循环等待（不抢占）
4. I/O 完成后，回调进入队列等待下次循环

---

## 3. 同步 vs 异步 vs 并行

| 模式 | 描述 | 适合场景 |
|------|------|---------|
| **同步（Sync）** | 一件做完再做下一件 | CPU 密集型，简单脚本 |
| **异步（Async）** | 发起后立即继续，完成时回调 | I/O 密集型（网络、数据库、文件） |
| **并行（Parallel）** | 真正同时在多个 CPU 核心执行 | CPU 密集型计算 |

> **常见误区**：异步 ≠ 并行。JavaScript 的异步是单线程的，Python 的 asyncio 也是单线程的。
> 它们在等待 I/O 时"切换"，不是"同时"。

---

## 4. 三种并发模型对比

### 4.1 回调（Callback）
```js
// 嵌套回调 → "回调地狱"
fetchUser(id, (user) => {
    fetchOrders(user.id, (orders) => {
        fetchDetails(orders[0].id, (detail) => {
            // 深度嵌套，难以维护
        })
    })
})
```

### 4.2 Promise / Future
```js
fetchUser(id)
    .then(user => fetchOrders(user.id))
    .then(orders => fetchDetails(orders[0].id))
    .then(detail => process(detail))
    .catch(err => handleError(err))
// 链式，但错误处理仍然分散
```

### 4.3 async/await（现代推荐）
```js
async function processUser(id) {
    const user = await fetchUser(id)         // 看起来像同步
    const orders = await fetchOrders(user.id)
    const detail = await fetchDetails(orders[0].id)
    return process(detail)
}
// 同步风格，但底层是异步——可读性最佳
```

---

## 5. 任务队列的优先级（以 Node.js 为例）

```
每次事件循环的执行顺序：

1. process.nextTick 队列     ← 优先级最高，当前操作完成后立即
2. Promise microtask 队列    ← 微任务，优先于宏任务
3. setTimeout / setInterval  ← 宏任务（timer 阶段）
4. I/O 回调                 ← I/O 阶段
5. setImmediate              ← check 阶段
```

---

## 6. Goroutine 模型（Go 的并发哲学）

Go 不是事件循环，而是 **M:N 线程模型**：

```
Go Runtime 调度器
├── OS 线程 1 (M) ──── Goroutine A, C, E, ...
├── OS 线程 2 (M) ──── Goroutine B, D, F, ...
└── OS 线程 N (M) ──── ...

用户感知：轻量级 goroutine（~2KB 栈）
实际执行：被调度器复用到有限的 OS 线程
```

**channel 作为通信机制**：
```go
// "不要通过共享内存来通信，而要通过通信来共享内存"
// — Go 官方核心哲学

ch := make(chan int)
go func() { ch <- 42 }()   // 发送
value := <-ch              // 接收（阻塞直到有值）
```

---

## 7. 选择哪种模型？

| 场景 | 推荐模型 |
|------|---------|
| Web API 服务（I/O 密集） | asyncio / Node Event Loop / goroutine |
| 数据处理（CPU 密集） | 多进程 / 线程池 / goroutine |
| 简单脚本 | 同步即可 |
| 实时消息系统 | goroutine + channel |
| 浏览器 UI 事件 | JS Event Loop |

---

## 延伸阅读

- [What the heck is the event loop anyway?](https://www.youtube.com/watch?v=8aGhZQkoFbQ) — Philip Roberts（JS Event Loop 最佳讲解）
- *Designing Data-Intensive Applications* — Martin Kleppmann（第 2 章）
- Go 官方：[Effective Go - Concurrency](https://go.dev/doc/effective_go#concurrency)
- Python 官方：[asyncio 文档](https://docs.python.org/3/library/asyncio.html)
