/**
 * 被测代码：购物车服务
 *
 * 依赖通过构造函数注入，这是让 JS 代码易于测试的关键。
 */

class CartItem {
  constructor(productId, name, price, quantity) {
    if (price < 0) throw new Error('Price cannot be negative')
    if (quantity < 1) throw new Error('Quantity must be at least 1')
    this.productId = productId
    this.name = name
    this.price = price
    this.quantity = quantity
  }

  get subtotal() {
    return this.price * this.quantity
  }
}

class Cart {
  constructor(userId, discountService, inventoryApi) {
    this.userId = userId
    this.items = new Map()               // productId → CartItem
    this.discountService = discountService
    this.inventoryApi = inventoryApi
  }

  async addItem(productId, name, price, quantity = 1) {
    const available = await this.inventoryApi.checkStock(productId, quantity)
    if (!available) {
      throw new Error(`Product ${productId} is out of stock`)
    }

    if (this.items.has(productId)) {
      const existing = this.items.get(productId)
      this.items.set(
        productId,
        new CartItem(productId, name, price, existing.quantity + quantity)
      )
    } else {
      this.items.set(productId, new CartItem(productId, name, price, quantity))
    }
  }

  removeItem(productId) {
    if (!this.items.has(productId)) {
      throw new Error(`Item ${productId} not found in cart`)
    }
    this.items.delete(productId)
  }

  get subtotal() {
    let total = 0
    for (const item of this.items.values()) {
      total += item.subtotal
    }
    return total
  }

  async checkout() {
    if (this.items.size === 0) {
      throw new Error('Cannot checkout empty cart')
    }

    const discount = await this.discountService.getDiscount(this.userId)
    const discountedTotal = this.subtotal * (1 - discount)

    return {
      userId: this.userId,
      items: Array.from(this.items.values()).map(item => ({
        productId: item.productId,
        name: item.name,
        quantity: item.quantity,
        subtotal: item.subtotal,
      })),
      subtotal: this.subtotal,
      discount,
      total: Math.round(discountedTotal * 100) / 100,
    }
  }
}

// 防抖工具函数（用于演示计时器 Mock）
function debounce(fn, delay) {
  let timer = null
  return function (...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

module.exports = { Cart, CartItem, debounce }
