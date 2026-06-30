// 02_channel.go — channel 深入演示
//
// channel 是 Go 并发的核心通信机制。
// 运行：go run 02_channel.go

package main

import (
	"fmt"
	"time"
)

// ─────────────────────────────────────────────────────────
// 1. 无缓冲 vs 有缓冲 channel
// ─────────────────────────────────────────────────────────

func demoBuffered() {
	fmt.Println("=== 1. 无缓冲 vs 有缓冲 ===")

	// 无缓冲：发送方和接收方必须同时就绪（"握手"）
	unbuffered := make(chan string)
	go func() {
		fmt.Println("  [无缓冲] 发送方：准备发送...")
		unbuffered <- "hello"
		fmt.Println("  [无缓冲] 发送方：发送完成（接收方已就绪）")
	}()
	time.Sleep(100 * time.Millisecond)
	msg := <-unbuffered
	fmt.Printf("  [无缓冲] 接收方：收到 %q\n", msg)

	// 有缓冲：发送方不等接收方，直到缓冲满
	buffered := make(chan int, 3)
	fmt.Println("\n  [有缓冲 cap=3] 连续发送 3 个不阻塞：")
	buffered <- 1
	buffered <- 2
	buffered <- 3
	fmt.Printf("  缓冲区已满，当前大小: %d\n", len(buffered))
	// buffered <- 4  // 如果取消注释，这里会死锁（缓冲已满，没有接收方）

	fmt.Printf("  接收: %d, %d, %d\n", <-buffered, <-buffered, <-buffered)
}

// ─────────────────────────────────────────────────────────
// 2. range over channel（生产者-消费者）
// ─────────────────────────────────────────────────────────

func generate(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		for _, n := range nums {
			out <- n
		}
		close(out) // 生产完毕，关闭 channel，通知消费者
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		for n := range in { // range 自动在 channel 关闭后退出
			out <- n * n
		}
		close(out)
	}()
	return out
}

func demoPipeline() {
	fmt.Println("\n=== 2. Pipeline（流水线）===")

	// 链式：生成 → 平方 → 打印
	nums := generate(2, 3, 4, 5)
	squares := square(nums)

	for s := range squares {
		fmt.Printf("  %d\n", s)
	}
}

// ─────────────────────────────────────────────────────────
// 3. select：监听多个 channel
// ─────────────────────────────────────────────────────────

func demoSelect() {
	fmt.Println("\n=== 3. select ===")

	ch1 := make(chan string, 1)
	ch2 := make(chan string, 1)

	go func() {
		time.Sleep(200 * time.Millisecond)
		ch1 <- "来自 ch1"
	}()
	go func() {
		time.Sleep(100 * time.Millisecond)
		ch2 <- "来自 ch2"
	}()

	// select 等待多个 channel，哪个先就绪就处理哪个
	for i := 0; i < 2; i++ {
		select {
		case msg := <-ch1:
			fmt.Printf("  收到: %s\n", msg)
		case msg := <-ch2:
			fmt.Printf("  收到: %s\n", msg)
		}
	}
}

// ─────────────────────────────────────────────────────────
// 4. done channel：优雅退出
// ─────────────────────────────────────────────────────────

func demoGracefulShutdown() {
	fmt.Println("\n=== 4. done channel 优雅退出 ===")

	done := make(chan struct{}) // 空结构体，不占内存
	jobs := make(chan int, 10)

	// Worker
	go func() {
		for {
			select {
			case job, ok := <-jobs:
				if !ok {
					fmt.Println("  [worker] jobs channel 已关闭，退出")
					return
				}
				fmt.Printf("  [worker] 处理任务 %d\n", job)
			case <-done:
				fmt.Println("  [worker] 收到退出信号，停止工作")
				return
			}
		}
	}()

	// 发送几个任务后发送退出信号
	for i := 1; i <= 3; i++ {
		jobs <- i
	}
	time.Sleep(50 * time.Millisecond)

	fmt.Println("  [main] 发送退出信号")
	close(done) // 关闭 done，所有监听它的 goroutine 都会收到信号
	time.Sleep(50 * time.Millisecond)
}

// ─────────────────────────────────────────────────────────
// 5. fan-out / fan-in
// ─────────────────────────────────────────────────────────

func fanOut(in <-chan int, workers int) []<-chan int {
	channels := make([]<-chan int, workers)
	for i := 0; i < workers; i++ {
		out := make(chan int)
		channels[i] = out
		go func(ch chan<- int) {
			for v := range in {
				ch <- v * 2
			}
			close(ch)
		}(out)
	}
	return channels
}

func demoFanOutFanIn() {
	fmt.Println("\n=== 5. fan-out / fan-in ===")
	fmt.Println("  （概念演示，见 README）")
}

// ─────────────────────────────────────────────────────────
// 入口
// ─────────────────────────────────────────────────────────

func main() {
	demoBuffered()
	demoPipeline()
	demoSelect()
	demoGracefulShutdown()
	demoFanOutFanIn()
}

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 实现一个 merge(channels ...<-chan int) <-chan int 函数（fan-in），
//    将多个 channel 的输出合并到一个 channel。
//
// 2. 用 select + time.After 实现一个带超时的 channel 接收：
//    如果 1 秒内没有收到数据，打印"超时"并退出。
