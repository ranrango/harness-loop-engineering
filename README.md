# Harness & Loop Engineering — 初学者参考指南

> 从零理解测试装具（Harness）与事件驱动循环（Loop）工程，每个概念都有可运行的示例代码。涵盖核心概念、多语言实践，以及工业界现状与前沿发展。

---

## 目录结构

```
harness-loop-engineering/
├── harness/               # 测试装具工程
│   ├── 01-concepts/       # 核心概念与术语
│   ├── 02-python/         # Python 示例（pytest）
│   ├── 03-javascript/     # JavaScript 示例（Jest）
│   ├── 04-go/             # Go 示例（testing + testify）
│   └── 05-industry/       # 行业发展 & 工业界实践 ← NEW
└── loop/                  # 事件循环工程
    ├── 01-concepts/       # 核心概念
    ├── 02-python/         # asyncio 示例
    ├── 03-javascript/     # Node.js Event Loop 示例
    ├── 04-go/             # goroutine + channel 示例
    └── 05-industry/       # 行业发展 & 工业界实践 ← NEW
```

---

## 快速导航

### Harness Engineering（测试装具工程）

| 章节 | 内容 | 难度 |
|------|------|------|
| [概念](./harness/01-concepts/) | Test Double、金字塔、生命周期 | ⭐ 入门 |
| [Python 示例](./harness/02-python/) | pytest、Fixture、Mock、参数化 | ⭐⭐ 初级 |
| [JavaScript 示例](./harness/03-javascript/) | Jest、Mock、快照、Timer | ⭐⭐ 初级 |
| [Go 示例](./harness/04-go/) | testing、表格驱动、testify | ⭐⭐ 初级 |
| [行业发展 & 工业界实践](./harness/05-industry/) | 发展历史、Google/Meta/Netflix 案例、AI 测试、Mutation Testing | ⭐⭐⭐ 扩展 |

### Loop Engineering（事件循环工程）

| 章节 | 内容 | 难度 |
|------|------|------|
| [概念](./loop/01-concepts/) | 事件循环原理、同步 vs 异步 | ⭐ 入门 |
| [Python 示例](./loop/02-python/) | asyncio、Task、Queue | ⭐⭐ 初级 |
| [JavaScript 示例](./loop/03-javascript/) | Event Loop、Promise、Worker | ⭐⭐ 初级 |
| [Go 示例](./loop/04-go/) | goroutine、channel、select | ⭐⭐ 初级 |
| [行业发展 & 工业界实践](./loop/05-industry/) | C10K 问题、Discord/Cloudflare/Uber 案例、Java Loom、结构化并发 | ⭐⭐⭐ 扩展 |

---

## 如何使用这份指南

1. **先读概念**：每个主题的 `01-concepts/` 目录包含无代码的概念解释，建立心智模型
2. **跑通示例**：选择你熟悉的语言，按 README 安装依赖后直接运行
3. **修改练习**：每个示例文件末尾都有 `# 练习` 注释，尝试自己动手改
4. **对照对比**：同一个概念在三种语言中的实现方式放在同级目录，便于横向比较

---

## 环境要求

| 语言 | 最低版本 | 包管理 |
|------|----------|--------|
| Python | 3.10+ | `pip` |
| JavaScript | Node 18+ | `npm` |
| Go | 1.21+ | `go mod` |

---

## 贡献

欢迎提交 PR 或 Issue！新增示例请遵循：
- 每个文件保持独立可运行
- 注释解释「为什么」而不是「做什么」
- 在文件末尾添加至少一个练习题
