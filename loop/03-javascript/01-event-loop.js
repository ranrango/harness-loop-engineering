/**
 * loop/03-javascript/01-event-loop.js
 *
 * Node.js 事件循环深入演示
 * 运行：node 01-event-loop.js
 */

'use strict'

// ─────────────────────────────────────────────────────────
// 1. 任务队列优先级（macrotask vs microtask）
// ─────────────────────────────────────────────────────────

console.log('=== 任务队列优先级 ===')
console.log('1. 同步代码（Call Stack）')

setTimeout(() => console.log('4. setTimeout（macrotask）'), 0)
setImmediate(() => console.log('5. setImmediate（check phase）'))

Promise.resolve()
  .then(() => console.log('3. Promise.then（microtask）'))
  .then(() => console.log('3b. 第二个 then（microtask 队列继续清空）'))

process.nextTick(() => console.log('2. process.nextTick（nextTick 队列，最优先）'))

console.log('1b. 同步代码继续')

// 预期输出顺序：1 → 1b → 2 → 3 → 3b → 4 或 5（顺序取决于 I/O 阶段）


// ─────────────────────────────────────────────────────────
// 2. 为什么 async/await 不阻塞
// ─────────────────────────────────────────────────────────

async function fetchData(id) {
  // 模拟异步 I/O（数据库查询、网络请求等）
  return new Promise(resolve => {
    setTimeout(() => resolve({ id, data: `result-${id}` }), 100)
  })
}

async function processSequential() {
  console.log('\n=== 顺序 await（串行）===')
  const start = Date.now()

  const a = await fetchData(1)   // 等 100ms
  const b = await fetchData(2)   // 再等 100ms
  const c = await fetchData(3)   // 再等 100ms

  console.log(`顺序完成: ${Date.now() - start}ms（预期 ~300ms）`)
  return [a, b, c]
}

async function processConcurrent() {
  console.log('\n=== Promise.all（并发）===')
  const start = Date.now()

  // 同时发起，等最慢的那个
  const [a, b, c] = await Promise.all([
    fetchData(1),
    fetchData(2),
    fetchData(3),
  ])

  console.log(`并发完成: ${Date.now() - start}ms（预期 ~100ms）`)
  return [a, b, c]
}


// ─────────────────────────────────────────────────────────
// 3. Promise 工具方法对比
// ─────────────────────────────────────────────────────────

async function demoPromiseMethods() {
  console.log('\n=== Promise 工具方法 ===')

  const promises = [
    Promise.resolve('成功 A'),
    Promise.reject(new Error('失败 B')),
    Promise.resolve('成功 C'),
  ]

  // all：全成功才成功，一个失败就失败
  try {
    await Promise.all(promises)
  } catch (e) {
    console.log(`Promise.all 失败: ${e.message}`)
  }

  // allSettled：等全部完成，不管成功还是失败
  const results = await Promise.allSettled(promises)
  results.forEach(r => {
    if (r.status === 'fulfilled') console.log(`  fulfilled: ${r.value}`)
    else console.log(`  rejected: ${r.reason.message}`)
  })

  // race：第一个完成的（无论成功失败）
  const first = await Promise.race([
    new Promise(r => setTimeout(() => r('慢 500ms'), 500)),
    new Promise(r => setTimeout(() => r('快 100ms'), 100)),
  ])
  console.log(`Promise.race 赢家: ${first}`)

  // any（ES2021）：第一个成功的
  const firstSuccess = await Promise.any([
    Promise.reject(new Error('失败')),
    new Promise(r => setTimeout(() => r('成功 200ms'), 200)),
    new Promise(r => setTimeout(() => r('成功 100ms'), 100)),
  ])
  console.log(`Promise.any 赢家: ${firstSuccess}`)
}


// ─────────────────────────────────────────────────────────
// 4. 常见陷阱：忘记 await
// ─────────────────────────────────────────────────────────

async function commonMistakes() {
  console.log('\n=== 常见陷阱 ===')

  // 陷阱 1：忘记 await，拿到的是 Promise 对象不是值
  const raw = fetchData(1)    // 没有 await！
  console.log('忘记 await:', raw instanceof Promise ? 'Promise 对象（不是数据！）' : raw)

  // 正确
  const data = await fetchData(1)
  console.log('正确 await:', data)

  // 陷阱 2：在循环里 await（串行，通常不是你想要的）
  const ids = [1, 2, 3]
  const sequential = []
  const start = Date.now()
  for (const id of ids) {
    sequential.push(await fetchData(id))   // 串行！
  }
  console.log(`循环内 await（串行）: ${Date.now() - start}ms`)

  // 正确：用 Promise.all 并发
  const concurrent = await Promise.all(ids.map(id => fetchData(id)))
  console.log(`Promise.all（并发）: ${Date.now() - start}ms`)
}


// ─────────────────────────────────────────────────────────
// 入口
// ─────────────────────────────────────────────────────────

async function main() {
  await new Promise(r => setTimeout(r, 10))  // 等上面的同步代码打印完

  await processSequential()
  await processConcurrent()
  await demoPromiseMethods()
  await commonMistakes()
}

main().catch(console.error)

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 实现一个 pLimit(concurrency) 函数：
//    限制同时运行的 Promise 数量，返回一个包装函数。
//    例：const limit = pLimit(3)
//        await Promise.all(urls.map(url => limit(() => fetch(url))))
//
// 2. 用 Promise.race 实现一个 withTimeout(promise, ms) 工具：
//    如果 promise 在 ms 内没有 resolve，则 reject 一个 TimeoutError。
