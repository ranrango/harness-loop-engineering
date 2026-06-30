/**
 * 04-timers.test.js — 计时器 Mock
 *
 * 真实的 setTimeout/setInterval 会让测试变慢。
 * jest.useFakeTimers() 让时间变成可控的变量。
 */

const { debounce } = require('../src/cart')

describe('Fake Timers', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()  // 每个测试后恢复真实计时器
  })

  // ── debounce ──────────────────────────────────────────

  describe('debounce', () => {
    it('does not call fn immediately', () => {
      const fn = jest.fn()
      const debounced = debounce(fn, 300)

      debounced()

      expect(fn).not.toHaveBeenCalled()
    })

    it('calls fn after delay has elapsed', () => {
      const fn = jest.fn()
      const debounced = debounce(fn, 300)

      debounced()
      jest.advanceTimersByTime(300)   // 让时间快进 300ms

      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('resets timer on repeated calls (only fires once)', () => {
      const fn = jest.fn()
      const debounced = debounce(fn, 300)

      debounced('call 1')
      jest.advanceTimersByTime(200)   // 还没到 300ms

      debounced('call 2')             // 重置计时器
      jest.advanceTimersByTime(200)   // 又过了 200ms（总共 400ms，但重置了）

      // 第二次调用重置了计时器，300ms 还没到，fn 不该被调用
      expect(fn).not.toHaveBeenCalled()

      jest.advanceTimersByTime(100)   // 再过 100ms，第二次计时器到期

      expect(fn).toHaveBeenCalledTimes(1)
      expect(fn).toHaveBeenCalledWith('call 2')   // 只用最后一次的参数
    })

    it('can be called again after debounce settles', () => {
      const fn = jest.fn()
      const debounced = debounce(fn, 100)

      debounced('first')
      jest.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledTimes(1)

      debounced('second')
      jest.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledTimes(2)
    })
  })

  // ── setInterval ──────────────────────────────────────

  describe('polling with setInterval', () => {
    function createPoller(callback, intervalMs) {
      const id = setInterval(callback, intervalMs)
      return { stop: () => clearInterval(id) }
    }

    it('calls callback on each interval', () => {
      const callback = jest.fn()
      const poller = createPoller(callback, 1000)

      jest.advanceTimersByTime(3000)  // 快进 3 秒

      expect(callback).toHaveBeenCalledTimes(3)
      poller.stop()
    })

    it('stops calling after cleared', () => {
      const callback = jest.fn()
      const poller = createPoller(callback, 1000)

      jest.advanceTimersByTime(2000)
      poller.stop()
      jest.advanceTimersByTime(5000)  // 停止后继续快进

      expect(callback).toHaveBeenCalledTimes(2)   // 只调用了停止前的 2 次
    })
  })

  // ── runAllTimers vs advanceTimersByTime ──────────────

  describe('timer control methods', () => {
    it('jest.runAllTimers() fires all pending timers immediately', () => {
      const fn = jest.fn()
      setTimeout(() => fn('first'), 100)
      setTimeout(() => fn('second'), 500)
      setTimeout(() => fn('third'), 1000)

      jest.runAllTimers()

      expect(fn).toHaveBeenCalledTimes(3)
    })

    it('jest.runOnlyPendingTimers() fires only currently-queued timers', () => {
      const fn = jest.fn()
      setTimeout(() => {
        fn('outer')
        setTimeout(() => fn('inner'), 100)  // 在回调中创建新计时器
      }, 100)

      jest.runOnlyPendingTimers()   // 只运行当前队列，不运行嵌套的

      expect(fn).toHaveBeenCalledWith('outer')
      expect(fn).not.toHaveBeenCalledWith('inner')
    })
  })
})

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 实现一个 throttle(fn, limit) 函数（节流：在 limit 时间内最多执行一次），
//    用 fake timers 写测试验证：快速多次调用时只触发一次。
//
// 2. 实现一个带超时的 fetchWithTimeout(url, timeoutMs) 函数，
//    用 fake timers 验证：超时时 Promise reject。
