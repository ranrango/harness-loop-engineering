// calculator.go — 被测代码（刻意简单，聚焦于测试演示）

package calculator

import "errors"

var ErrDivisionByZero = errors.New("division by zero")

func Add(a, b int) int      { return a + b }
func Subtract(a, b int) int { return a - b }
func Multiply(a, b int) int { return a * b }
func Square(n int) int      { return n * n }

func Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, ErrDivisionByZero
	}
	return a / b, nil
}

// Fibonacci 用于演示递归的测试
func Fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return Fibonacci(n-1) + Fibonacci(n-2)
}
