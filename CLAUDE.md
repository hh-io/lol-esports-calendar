# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

抓取英雄联盟职业赛程（LPL/LCK/MSI/Worlds），生成 Apple 日历可订阅的 `.ics`。GitHub Actions 每小时刷新，托管在 GitHub Pages。文档与用户可见文案使用中文。

## Run

```bash
python3 src/main.py   # 生成 dist/lpl.ics、lck.ics、intl.ics
```

`src/` 模块用平铺导入（`from fetch import ...`），依赖 `src/` 在 `sys.path` 上 —— 直接 `python3 src/main.py` 运行即可。不要改成包结构（`src.fetch`）而不同步调整所有导入。CI 固定 Python 3.12（`.github/workflows/update.yml`）。

## 硬性约束

- **运行时零第三方依赖**：`src/` 只用标准库。不要 `pip install` 任何运行时依赖。本地开发工具（如 linter）可装，但不能进入运行时代码或 CI。
- **失败时保留旧文件**：任一赛区抓取失败，`main.py` 退出码非 0 且不写任何 `.ics`，保证已订阅文件不被空/残缺数据覆盖。改动抓取/输出流程时必须保持这个不变量。
- **`.ics` 手写实现**：`ics.py` 手写符合 RFC 5545（CRLF 行尾、75 字节折叠、TEXT 转义、稳定 UID）。不要引入 `icalendar` 之类的库来替代。
- **时间以 UTC 存储**，由客户端按本地时区显示。

## 常见改动

- 增删赛区：改 `src/main.py` 的 `OUTPUTS`（slug 列表）。`leagueId` 运行时由 `getLeagues` 按 slug 动态解析，不硬编码。
- 回看比分窗口：`src/main.py` 的 `KEEP_COMPLETED_DAYS`。
- `fetch.py` 里的 `API_KEY` 是官网公开固定 key（非机密），不是需要保护的密钥。

## Lint / Format

```bash
ruff check src/        # 检查（--fix 自动修）
ruff format src/       # 格式化
```

配置见 `ruff.toml`。ruff 仅为本地/CI 开发工具，**不是运行时依赖** —— 不要把它写进运行时代码或当成 `src/` 的依赖。

## 提交规范

Conventional Commits（`feat:` / `fix:` / `chore:`），与 CI 自动提交风格一致。
