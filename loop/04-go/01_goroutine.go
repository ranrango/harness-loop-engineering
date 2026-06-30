// 01_goroutine.go — goroutine 基础与同步
//
// goroutine 是 Go 的并发执行单元，极其轻量（~2KB 初始栈）。
// 运行：go run 01_goroutine.go

package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ─────────────────────────────────────────────────────────
// 1. goroutine 基础
// ─────────────────────────────────────────────────────────

func greet(name string, delay time.Duration) {
	time.Sleep(delay)
	fmt.Printf("[%s] 你好！\n", name)
}

func demoBasicGoroutine() {
	fmt.Println("=== 1. goroutine 基础 ===")

	// go 关键字启动 goroutine，立即返回，不等待
	go greet("Alice", 200*time.Millisecond)
	go greet("Bob", 100*time.Millisecond)
	go greet("Charlie", 300*time.Millisecond)

	fmt.Println("三个 goroutine 已启动，主 goroutine 继续执行")

	// 问题：没有等待，main 退出时所有 goroutine 也退出
	// 解决方案 1：time.Sleep（粗糙，不推荐）
	time.Sleep(500 * time.Millisecond)
	fmt.Println("主 goroutine 结束")
}

// ─────────────────────────────────────────────────────────
// 2. sync.WaitGroup：等待一组 goroutine 完成
// ─────────────────────────────────────────────────────────

func demoWaitGroup() {
	fmt.Println("\n=== 2. WaitGroup ===")

	var wg sync.WaitGroup

	for i := 0; i < 5; i++ {
		wg.Add(1) // 每启动一个 goroutine，计数器 +1
		go func(id int) {
			defer wg.Done() // goroutine 结束时计数器 -1
			delay := time.Duration(id*100) * time.Millisecond
			time.Sleep(delay)
			fmt.Printf("  worker-%d 完成（等待了 %v）\n", id, delay)
		}(i) // 注意：传入 i 的副本，避免闭包捕获变量的经典问题
	}

	wg.Wait() // 阻塞直到计数器为 0
	fmt.Println("所有 worker 完成")
}

// ─────────────────────────────────────────────────────────
// 3. 竞争条件 vs 原子操作
// ─────────────────────────────────────────────────────────

func demoRaceCondition() {
	fmt.Println("\n=== 3. 竞争条件 vs 原子操作 ===")

	const goroutines = 1000
	const increments = 100

	// 有竞争条件的计数器（不安全！）
	// 用 go run -race 01_goroutine.go 可以检测到这个问题
	unsafeCounter := 0
	var wg1 sync.WaitGroup
	for i := 0; i < goroutines; i++ {
		wg1.Add(1)
		go func() {
			defer wg1.Done()
			for j := 0; j < increments; j++ {
				unsafeCounter++ // 数据竞争！多个 goroutine 同时读改写
			}
		}()
	}
	wg1.Wait()
	fmt.Printf("不安全计数器: %d（预期 %d，实际可能更小！）\n",
		unsafeCounter, goroutines*increments)

	// 原子操作（安全）
	var safeCounter int64
	var wg2 sync.WaitGroup
	for i := 0; i < goroutines; i++ {
		wg2.Add(1)
		go func() {
			defer wg2.Done()
			for j := 0; j < increments; j++ {
				atomic.AddInt64(&safeCounter, 1) // 原子操作，无竞争
			}
		}()
	}
	wg2.Wait()
	fmt.Printf("原子计数器:   %d（预期 %d，始终正确）\n",
		safeCounter, goroutines*increments)

	// sync.Mutex 解法
	var mutexCounter int
	var mu sync.Mutex
	var wg3 sync.WaitGroup
	for i := 0; i < goroutines; i++ {
		wg3.Add(1)
		go func() {
			defer wg3.Done()
			for j := 0; j < increments; j++ {
				mu.Lock()
				mutexCounter++
				mu.Unlock()
			}
		}()
	}
	wg3.Wait()
	fmt.Printf("Mutex 计数器:  %d（预期 %d，始终正确）\n",
		mutexCounter, goroutines*increments)
}

// ─────────────────────────────────────────────────────────
// 入口
// ─────────────────────────────────────────────────────────

func main() {
	demoBasicGoroutine()
	demoWaitGroup()
	demoRaceCondition()
}

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 用 WaitGroup 实现一个并行下载模拟：
//    同时"下载" 10 个文件（用 time.Sleep 模拟），
//    所有文件下载完后打印总耗时。
//
// 2. 用 sync.Map 实现线程安全的缓存，
//    验证 100 个并发 goroutine 读写不会 panic。
