# Harness Engineering — Go 示例

## 快速开始

```bash
cd harness/04-go
go test ./... -v
go test -cover ./...
```

---

## 文件说明

| 文件 | 演示内容 |
|------|---------|
| `calculator.go` | 被测代码 |
| `calculator_test.go` | 基础：表格驱动测试 |
| `order/order.go` | 被测代码：订单服务 |
| `order/order_test.go` | Mock 接口 + gomock |

---

## 表格驱动测试（Go 惯用法）

```go
tests := []struct {
    name     string
    input    int
    expected int
}{
    {"正数", 2, 4},
    {"负数", -3, 9},
    {"零",   0, 0},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        assert.Equal(t, tt.expected, Square(tt.input))
    })
}
```

优点：新增测试用例只需添加一行数据，无需复制函数。
