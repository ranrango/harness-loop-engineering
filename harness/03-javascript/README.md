# Harness Engineering — JavaScript/TypeScript 示例（Jest）

## 快速开始

```bash
cd harness/03-javascript
npm install
npm test
npm run test:coverage  # 查看覆盖率
```

---

## 文件说明

| 文件 | 演示内容 |
|------|---------|
| `src/cart.js` | 被测代码：购物车（含外部依赖） |
| `__tests__/01-basics.test.js` | 基础：describe/it、toBe/toEqual |
| `__tests__/02-mock.test.js` | Mock：jest.fn()、jest.mock()、spyOn |
| `__tests__/03-async.test.js` | 异步测试：Promise、async/await |
| `__tests__/04-timers.test.js` | 计时器 Mock：fake timers、debounce |

---

## 核心概念速查

### jest.fn() 的三种角色

```js
// Stub：预设返回值
const stub = jest.fn().mockReturnValue(42)

// Spy：包装真实函数，记录调用
const spy = jest.spyOn(obj, 'method')

// Mock：验证交互
expect(mockFn).toHaveBeenCalledWith('expected-arg')
```

### 常用 Matcher 速查

```js
expect(x).toBe(y)           // 严格相等（===）
expect(x).toEqual(y)        // 深度相等（对象/数组用这个）
expect(x).toBeNull()
expect(x).toBeTruthy()
expect(fn).toThrow('msg')
expect(fn).toHaveBeenCalledTimes(2)
expect(fn).toHaveBeenCalledWith(arg1, arg2)
```
