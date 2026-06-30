// calculator_test.go — Go 测试惯用写法

package calculator_test

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	calc "harness-go-examples"
)

// ─────────────────────────────────────────────────────────
// 表格驱动测试（Table-Driven Test）
// Go 社区最推荐的测试写法
// ─────────────────────────────────────────────────────────

func TestAdd(t *testing.T) {
	tests := []struct {
		name     string
		a, b     int
		expected int
	}{
		{"两个正数", 2, 3, 5},
		{"正负相加", 10, -3, 7},
		{"两个负数", -4, -6, -10},
		{"加零", 5, 0, 5},
		{"大数", 1000000, 2000000, 3000000},
	}

	for _, tt := range tests {
		// t.Run 创建子测试，失败时报告 "TestAdd/两个正数"
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Add(tt.a, tt.b)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDivide(t *testing.T) {
	t.Run("正常除法", func(t *testing.T) {
		result, err := calc.Divide(10, 2)
		require.NoError(t, err)          // require：失败则立即停止当前测试
		assert.InDelta(t, 5.0, result, 0.001) // 浮点比较用 InDelta
	})

	t.Run("除以零返回错误", func(t *testing.T) {
		_, err := calc.Divide(10, 0)
		require.Error(t, err)
		assert.ErrorIs(t, err, calc.ErrDivisionByZero) // 验证具体错误类型
	})

	t.Run("除以负数", func(t *testing.T) {
		result, err := calc.Divide(10, -2)
		require.NoError(t, err)
		assert.InDelta(t, -5.0, result, 0.001)
	})
}

func TestSquare(t *testing.T) {
	tests := []struct {
		input    int
		expected int
	}{
		{0, 0},
		{1, 1},
		{2, 4},
		{-3, 9}, // 负数平方为正
		{10, 100},
	}

	for _, tt := range tests {
		t.Run("", func(t *testing.T) { // 空名称用输入值自动命名
			assert.Equal(t, tt.expected, calc.Square(tt.input))
		})
	}
}

func TestFibonacci(t *testing.T) {
	// 已知 Fibonacci 数列前几项
	known := map[int]int{
		0: 0, 1: 1, 2: 1, 3: 2, 4: 3,
		5: 5, 6: 8, 7: 13, 8: 21, 9: 34, 10: 55,
	}

	for n, expected := range known {
		n, expected := n, expected // 捕获循环变量
		t.Run("", func(t *testing.T) {
			assert.Equal(t, expected, calc.Fibonacci(n),
				"Fibonacci(%d) 应为 %d", n, expected)
		})
	}
}

// ─────────────────────────────────────────────────────────
// 并行测试（独立的测试可以并行运行）
// ─────────────────────────────────────────────────────────

func TestAddParallel(t *testing.T) {
	t.Parallel() // 标记此测试可并行运行

	assert.Equal(t, 5, calc.Add(2, 3))
}

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 给 calculator.go 添加一个 IsPrime(n int) bool 函数，
//    用表格驱动测试覆盖：负数、0、1、质数、合数。
//
// 2. 给 Fibonacci 添加一个错误返回（n < 0 时返回 error），
//    修改测试并验证这个边界条件。
