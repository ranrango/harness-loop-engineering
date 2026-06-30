/**
 * 01-basics.test.js — Jest 基础用法
 *
 * 涵盖：describe/it 嵌套结构、常用 Matcher、
 * 异常断言、beforeEach/afterEach 钩子
 */

const { CartItem, Cart } = require('../src/cart')

// ─────────────────────────────────────────────────────────
// describe 嵌套：按"被测对象 → 场景"组织
// ─────────────────────────────────────────────────────────

describe('CartItem', () => {
  describe('constructor', () => {
    it('creates item with correct properties', () => {
      const item = new CartItem(1, 'Laptop', 999.99, 2)

      // toEqual 做深度比较，适合对象；toBe 做严格相等（===）
      expect(item.productId).toBe(1)
      expect(item.name).toBe('Laptop')
      expect(item.price).toBe(999.99)
      expect(item.quantity).toBe(2)
    })

    it('throws when price is negative', () => {
      expect(() => new CartItem(1, 'Bad', -10, 1)).toThrow('Price cannot be negative')
    })

    it('throws when quantity is zero', () => {
      expect(() => new CartItem(1, 'Bad', 10, 0)).toThrow('Quantity must be at least 1')
    })
  })

  describe('subtotal', () => {
    it('multiplies price by quantity', () => {
      const item = new CartItem(1, 'Mouse', 25.0, 3)
      expect(item.subtotal).toBe(75.0)
    })

    it('returns price when quantity is 1', () => {
      const item = new CartItem(1, 'Keyboard', 79.99, 1)
      expect(item.subtotal).toBe(79.99)
    })
  })
})

// ─────────────────────────────────────────────────────────
// beforeEach：共享测试状态初始化
// ─────────────────────────────────────────────────────────

describe('Cart', () => {
  let cart
  let mockInventoryApi

  beforeEach(() => {
    // 每个测试前重置——避免测试间状态污染
    mockInventoryApi = { checkStock: jest.fn().mockResolvedValue(true) }
    cart = new Cart('user-1', { getDiscount: jest.fn() }, mockInventoryApi)
  })

  afterEach(() => {
    // 清除所有 mock 记录（可选，beforeEach 重新创建也能达到同样效果）
    jest.clearAllMocks()
  })

  describe('subtotal', () => {
    it('returns 0 for empty cart', () => {
      expect(cart.subtotal).toBe(0)
    })

    it('sums all item subtotals', async () => {
      await cart.addItem(1, 'Laptop', 1000, 1)
      await cart.addItem(2, 'Mouse', 25, 2)

      expect(cart.subtotal).toBe(1050)   // 1000 + 25×2
    })
  })

  describe('removeItem', () => {
    it('removes existing item', async () => {
      await cart.addItem(1, 'Laptop', 1000, 1)
      cart.removeItem(1)

      expect(cart.items.size).toBe(0)
    })

    it('throws when item not in cart', () => {
      expect(() => cart.removeItem(999)).toThrow('Item 999 not found in cart')
    })
  })
})

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 给 Cart 添加一个 itemCount 属性（所有商品 quantity 之和），
//    然后写测试覆盖：空购物车、单品多件、多品。
//
// 2. 给 Cart 添加一个 clear() 方法，写测试验证清空后 subtotal 为 0。
