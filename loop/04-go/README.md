# Loop Engineering — Go 示例（goroutine + channel）

## 快速开始

```bash
cd loop/04-go
go run 01_goroutine.go
go run 02_channel.go
go run 03_patterns.go
go test ./...
```

**无需第三方依赖**，全部使用 Go 标准库。

---

## Go 并发哲学

> "Do not communicate by sharing memory; instead, share memory by communicating."
>
> "不要通过共享内存来通信，而要通过通信来共享内存。"
> — Rob Pike, Go 核心设计者

```
传统方式（共享内存）：      Go 方式（消息传递）：
  goroutine A ──mutex──▶ 共享变量    goroutine A ──channel──▶ goroutine B
  goroutine B ──mutex──▶ 共享变量    数据的所有权随消息转移
  
  问题：死锁、竞争条件              优点：并发逻辑更清晰
```

---

## channel 速查

```go
ch := make(chan int)        // 无缓冲：发送方等接收方就绪
ch := make(chan int, 10)    // 有缓冲：最多存 10 个，满了才阻塞

ch <- 42          // 发送（可能阻塞）
v := <-ch         // 接收（可能阻塞）
v, ok := <-ch     // ok=false 表示 channel 已关闭且为空
close(ch)         // 关闭（只有发送方关闭！）

// range 自动检测 close
for v := range ch {
    process(v)
}
```
