/**
 * 02-mock.test.js — Jest Mock 深入演示
 *
 * 涵盖：jest.fn() / mockReturnValue / mockResolvedValue /
 * side_effect 模拟 / toHaveBeenCalledWith / spyOn
 */

const { Cart } = require('../src/cart')

describe('Cart - Mock 演示', () => {
  let inventoryApi
  let discountService
  let cart

  beforeEach(() => {
    inventoryApi = {
      checkStock: jest.fn().mockResolvedValue(true),   // 默认库存充足
    }
    discountService = {
      getDiscount: jest.fn().mockResolvedValue(0),     // 默认无折扣
    }
    cart = new Cart('user-42', discountService, inventoryApi)
  })

  // ── return_value 系列 ────────────────────────────────

  describe('mockReturnValue vs mockResolvedValue', () => {
    it('mockReturnValue returns sync value', () => {
      const fn = jest.fn().mockReturnValue(42)
      expect(fn()).toBe(42)
    })

    it('mockResolvedValue wraps value in Promise', async () => {
      const fn = jest.fn().mockResolvedValue({ ok: true })
      const result = await fn()
      expect(result).toEqual({ ok: true })
    })

    it('mockRejectedValue simulates async failure', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('network error'))
      await expect(fn()).rejects.toThrow('network error')
    })
  })

  // ── side_effect 风格：mockImplementation ────────────

  describe('mockImplementation for dynamic responses', () => {
    it('returns different values based on argument', async () => {
      // 模拟真实的库存查询：商品 1 有货，商品 2 缺货
      inventoryApi.checkStock.mockImplementation(async (productId) => {
        return productId !== 2   // product 2 缺货
      })

      await cart.addItem(1, 'Laptop', 1000, 1)     // 应成功

      await expect(
        cart.addItem(2, 'OutOfStock', 50, 1)
      ).rejects.toThrow('out of stock')

      expect(cart.items.size).toBe(1)
    })

    it('can fail once then succeed (retry simulation)', async () => {
      let callCount = 0
      inventoryApi.checkStock.mockImplementation(async () => {
        callCount++
        if (callCount === 1) throw new Error('Service temporarily unavailable')
        return true
      })

      // 第一次调用失败
      await expect(cart.addItem(1, 'Item', 10, 1)).rejects.toThrow('temporarily')

      // 第二次调用成功
      await cart.addItem(1, 'Item', 10, 1)
      expect(cart.items.size).toBe(1)
    })
  })

  // ── 调用验证 ─────────────────────────────────────────

  describe('call verification', () => {
    it('verifies checkStock called with correct args', async () => {
      await cart.addItem(5, 'Monitor', 299, 3)

      expect(inventoryApi.checkStock).toHaveBeenCalledTimes(1)
      expect(inventoryApi.checkStock).toHaveBeenCalledWith(5, 3)
    })

    it('verifies discount service called during checkout', async () => {
      await cart.addItem(1, 'Laptop', 1000, 1)
      await cart.checkout()

      expect(discountService.getDiscount).toHaveBeenCalledTimes(1)
      expect(discountService.getDiscount).toHaveBeenCalledWith('user-42')
    })

    it('verifies inventory NOT called when checkout fails on empty cart', async () => {
      await expect(cart.checkout()).rejects.toThrow('empty cart')

      // 空购物车结账失败，不应该调用库存或折扣服务
      expect(discountService.getDiscount).not.toHaveBeenCalled()
    })
  })

  // ── checkout 完整场景 ────────────────────────────────

  describe('checkout', () => {
    it('applies discount correctly', async () => {
      discountService.getDiscount.mockResolvedValue(0.1)  // 10% 折扣

      await cart.addItem(1, 'Laptop', 1000, 1)
      const receipt = await cart.checkout()

      expect(receipt.discount).toBe(0.1)
      expect(receipt.total).toBe(900)   // 1000 × 0.9
    })

    it('receipt contains all items', async () => {
      await cart.addItem(1, 'Laptop', 1000, 1)
      await cart.addItem(2, 'Mouse', 25, 2)

      const receipt = await cart.checkout()

      expect(receipt.items).toHaveLength(2)
      expect(receipt.subtotal).toBe(1050)
      expect(receipt.items).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ productId: 1, quantity: 1 }),
          expect.objectContaining({ productId: 2, quantity: 2 }),
        ])
      )
    })
  })
})

// ─────────────────────────────────────────────────────────
// spyOn 演示：监视真实方法
// ─────────────────────────────────────────────────────────

describe('jest.spyOn - 监视真实对象', () => {
  it('spyOn records calls without replacing implementation', () => {
    const arr = [1, 2, 3]
    const spy = jest.spyOn(arr, 'push')

    arr.push(4)
    arr.push(5)

    // 记录了调用
    expect(spy).toHaveBeenCalledTimes(2)
    expect(spy).toHaveBeenNthCalledWith(1, 4)
    expect(spy).toHaveBeenNthCalledWith(2, 5)

    // 但真实行为没有改变
    expect(arr).toEqual([1, 2, 3, 4, 5])

    spy.mockRestore()   // 还原被 spy 的方法
  })

  it('spyOn can override implementation temporarily', () => {
    const math = { square: (x) => x * x }
    const spy = jest.spyOn(math, 'square').mockReturnValue(999)

    expect(math.square(5)).toBe(999)   // 被覆盖了

    spy.mockRestore()

    expect(math.square(5)).toBe(25)    // 还原后恢复真实行为
  })
})

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 模拟 discountService.getDiscount 连续返回不同折扣率（用 mockResolvedValueOnce），
//    验证两次 checkout 分别得到正确的折扣金额。
//
// 2. 用 jest.spyOn 监视 console.warn，验证某条错误路径下调用了警告。
