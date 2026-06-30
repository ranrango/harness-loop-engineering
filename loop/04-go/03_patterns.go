// 03_patterns.go — 实用并发模式
//
// Worker Pool、信号量限速、context 取消
// 运行：go run 03_patterns.go

package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ─────────────────────────────────────────────────────────
// 1. Worker Pool（固定大小的工作池）
// ─────────────────────────────────────────────────────────

type Job struct {
	ID    int
	Input int
}

type Result struct {
	JobID  int
	Output int
}

func workerPool(ctx context.Context, numWorkers int, jobs <-chan Job) <-chan Result {
	results := make(chan Result, numWorkers)
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		workerID := i
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					fmt.Printf("    worker-%d 被取消\n", workerID)
					return
				case job, ok := <-jobs:
					if !ok {
						return // jobs channel 关闭，退出
					}
					// 模拟工作
					time.Sleep(50 * time.Millisecond)
					results <- Result{
						JobID:  job.ID,
						Output: job.Input * job.Input,
					}
				}
			}
		}()
	}

	// 所有 worker 结束后关闭 results channel
	go func() {
		wg.Wait()
		close(results)
	}()

	return results
}

func demoWorkerPool() {
	fmt.Println("=== 1. Worker Pool ===")

	ctx := context.Background()
	jobs := make(chan Job, 20)

	// 启动 3 个 worker
	results := workerPool(ctx, 3, jobs)

	// 分发 10 个任务
	start := time.Now()
	for i := 1; i <= 10; i++ {
		jobs <- Job{ID: i, Input: i}
	}
	close(jobs) // 告知 worker 没有更多任务了

	// 收集结果
	var all []Result
	for r := range results {
		all = append(all, r)
	}

	fmt.Printf("完成 %d 个任务，耗时 %v（3 worker 并发，每任务 50ms）\n",
		len(all), time.Since(start).Round(time.Millisecond))
	// 预期约 200ms（10任务 / 3worker ≈ 4批 × 50ms）
}

// ─────────────────────────────────────────────────────────
// 2. 信号量限速
// ─────────────────────────────────────────────────────────

type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
	return make(Semaphore, n)
}

func (s Semaphore) Acquire() { s <- struct{}{} }
func (s Semaphore) Release() { <-s }

func demoSemaphore() {
	fmt.Println("\n=== 2. 信号量限速 ===")

	sem := NewSemaphore(3) // 最多 3 个并发
	var wg sync.WaitGroup
	active := 0
	var mu sync.Mutex
	maxActive := 0

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			sem.Acquire()
			defer sem.Release()

			mu.Lock()
			active++
			if active > maxActive {
				maxActive = active
			}
			mu.Unlock()

			time.Sleep(100 * time.Millisecond)

			mu.Lock()
			active--
			mu.Unlock()
		}(i)
	}

	wg.Wait()
	fmt.Printf("同时运行的最大并发数: %d（限制为 3）\n", maxActive)
}

// ─────────────────────────────────────────────────────────
// 3. context 取消与超时
// ─────────────────────────────────────────────────────────

func longTask(ctx context.Context, id int) error {
	select {
	case <-time.After(500 * time.Millisecond): // 模拟耗时操作
		fmt.Printf("  task-%d 正常完成\n", id)
		return nil
	case <-ctx.Done():
		fmt.Printf("  task-%d 被取消: %v\n", id, ctx.Err())
		return ctx.Err()
	}
}

func demoContext() {
	fmt.Println("\n=== 3. context 取消 ===")

	// 3a. 手动取消
	ctx, cancel := context.WithCancel(context.Background())

	go func() {
		time.Sleep(200 * time.Millisecond)
		fmt.Println("  [main] 200ms 后手动取消")
		cancel() // 触发取消
	}()

	if err := longTask(ctx, 1); err != nil {
		fmt.Printf("  task-1 失败: %v\n", err)
	}

	// 3b. 超时取消
	fmt.Println()
	ctx2, cancel2 := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel2()

	if err := longTask(ctx2, 2); err != nil {
		fmt.Printf("  task-2 超时: %v\n", err)
	}

	// 3c. context 传递给多个 goroutine（全部被取消）
	fmt.Println()
	ctx3, cancel3 := context.WithTimeout(context.Background(), 150*time.Millisecond)
	defer cancel3()

	var wg sync.WaitGroup
	for i := 3; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			longTask(ctx3, id)
		}(i)
	}
	wg.Wait()
}

// ─────────────────────────────────────────────────────────
// 入口
// ─────────────────────────────────────────────────────────

func main() {
	demoWorkerPool()
	demoSemaphore()
	demoContext()
}

// ─────────────────────────────────────────────────────────
// 练习
// ─────────────────────────────────────────────────────────
//
// 1. 修改 workerPool，让它接受 context，
//    当 context 被取消时，正在执行的 job 应当被中断并记录。
//
// 2. 实现一个带指数退避的重试函数：
//    func RetryWithBackoff(ctx context.Context, fn func() error, maxRetries int) error
//    每次失败后等待 2^attempt 秒，直到成功或超过最大重试次数。
