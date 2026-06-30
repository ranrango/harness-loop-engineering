/**
 * loop/03-javascript/02-patterns.js
 *
 * 实用并发模式：重试、限速、批处理、流式处理
 * 运行：node 02-patterns.js
 */

'use strict'

// ─────────────────────────────────────────────────────────
// 1. 指数退避重试
// ─────────────────────────────────────────────────────────

/**
 * 自动重试失败的异步操作，使用指数退避策略。
 *
 * @param {Function} fn - 返回 Promise 的函数
 * @param {Object} opts
 * @param {number} opts.maxRetries - 最大重试次数（默认 3）
 * @param {number} opts.baseDelayMs - 初始等待时间（默认 100ms）
 */
async function withRetry(fn, { maxRetries = 3, baseDelayMs = 100 } = {}) {
  let lastError
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      lastError = err
      if (attempt === maxRetries) break

      const delay = baseDelayMs * 2 ** attempt   // 100, 200, 400, 800...
      console.log(`  重试 ${attempt + 1}/${maxRetries}，等待 ${delay}ms...`)
      await new Promise(r => setTimeout(r, delay))
    }
  }
  throw lastError
}

async function demoRetry() {
  console.log('=== 指数退避重试 ===')
  let attempts = 0

  try {
    const result = await withRetry(
      async () => {
        attempts++
        if (attempts < 3) throw new Error(`临时失败（第 ${attempts} 次）`)
        return '成功！'
      },
      { maxRetries: 5, baseDelayMs: 50 }
    )
    console.log(`结果: ${result}，共尝试 ${attempts} 次`)
  } catch (e) {
    console.error(`最终失败: ${e.message}`)
  }
}


// ─────────────────────────────────────────────────────────
// 2. 并发限制器
// ─────────────────────────────────────────────────────────

function createConcurrencyLimiter(limit) {
  let running = 0
  const queue = []

  function runNext() {
    if (running >= limit || queue.length === 0) return
    running++
    const { fn, resolve, reject } = queue.shift()
    fn()
      .then(resolve)
      .catch(reject)
      .finally(() => {
        running--
        runNext()
      })
  }

  return function (fn) {
    return new Promise((resolve, reject) => {
      queue.push({ fn, resolve, reject })
      runNext()
    })
  }
}

async function demoConcurrencyLimit() {
  console.log('\n=== 并发限制器 ===')
  const limit = createConcurrencyLimiter(3)   // 最多 3 个并发
  const activeCount = { max: 0, current: 0 }

  const tasks = Array.from({ length: 10 }, (_, i) => limit(async () => {
    activeCount.current++
    activeCount.max = Math.max(activeCount.max, activeCount.current)

    await new Promise(r => setTimeout(r, 100))

    activeCount.current--
    return i
  }))

  const results = await Promise.all(tasks)
  console.log(`完成 ${results.length} 个任务`)
  console.log(`同时运行的最大并发数: ${activeCount.max}（限制为 3）`)
}


// ─────────────────────────────────────────────────────────
// 3. 批处理（Batching）
// ─────────────────────────────────────────────────────────

/**
 * 将多个单独请求合并成一个批量请求。
 * 经典场景：DataLoader 模式（GraphQL 的 N+1 问题解决方案）
 */
class DataLoader {
  constructor(batchFn, { maxBatchSize = 10, waitMs = 10 } = {}) {
    this.batchFn = batchFn
    this.maxBatchSize = maxBatchSize
    this.waitMs = waitMs
    this._queue = []
    this._timer = null
  }

  load(key) {
    return new Promise((resolve, reject) => {
      this._queue.push({ key, resolve, reject })

      if (this._queue.length >= this.maxBatchSize) {
        this._flush()
      } else if (!this._timer) {
        this._timer = setTimeout(() => this._flush(), this.waitMs)
      }
    })
  }

  async _flush() {
    if (this._timer) {
      clearTimeout(this._timer)
      this._timer = null
    }
    if (this._queue.length === 0) return

    const batch = this._queue.splice(0, this.maxBatchSize)
    const keys = batch.map(item => item.key)

    console.log(`  [批处理] 合并 ${keys.length} 个请求: [${keys.join(', ')}]`)

    try {
      const results = await this.batchFn(keys)
      batch.forEach((item, i) => item.resolve(results[i]))
    } catch (err) {
      batch.forEach(item => item.reject(err))
    }
  }
}

async function demoBatching() {
  console.log('\n=== DataLoader 批处理 ===')

  let batchCount = 0
  const loader = new DataLoader(
    async (ids) => {
      batchCount++
      await new Promise(r => setTimeout(r, 20))   // 模拟一次批量 DB 查询
      return ids.map(id => ({ id, name: `User ${id}` }))
    },
    { waitMs: 5 }
  )

  // 模拟同时发起 10 个独立请求（如 GraphQL 解析器）
  const users = await Promise.all(
    Array.from({ length: 10 }, (_, i) => loader.load(i + 1))
  )

  console.log(`获取了 ${users.length} 个用户，但只发了 ${batchCount} 次批量请求`)
}


// ─────────────────────────────────────────────────────────
// 入口
// ─────────────────────────────────────────────────────────

async function main() {
  await demoRetry()
  await demoConcurrencyLimit()
  await demoBatching()
}

main().catch(console.error)

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 给 withRetry 添加一个 shouldRetry(error) 参数，
//    允许调用者决定哪些错误值得重试（如：只重试网络错误，不重试权限错误）。
//
// 2. 实现一个 processInBatches(items, batchSize, processFn) 函数：
//    将 items 切成每组 batchSize 大小，按顺序处理每批，
//    但批内的 items 并发处理。
