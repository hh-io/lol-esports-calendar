# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

抓取英雄联盟职业赛程（LPL/LCK/LEC/LCP/LTA/国际赛），生成 Apple 日历可订阅的 `.ics`。GitHub Actions 每小时刷新，托管在 GitHub Pages。

日历正文支持多语言：`main.py` 的 `LANGS` 定义语言→`hl` 映射。默认中文输出到 `dist/`,其余语言到 `dist/<lang>/`(如 `dist/en/`、`dist/ko/`)。**中文路径 `dist/*.ics` 是已发布的订阅地址,不要改动其位置。** README 有 `README.md`(中) / `README.en.md` / `README.ko.md` 三份,改动面向用户的内容时三份都要同步。

## Run

```bash
python3 src/main.py   # 生成 dist/ 及 dist/en、dist/ko 下各赛区 .ics
```

`src/` 模块用平铺导入（`from fetch import ...`），依赖 `src/` 在 `sys.path` 上 —— 直接 `python3 src/main.py` 运行即可。不要改成包结构（`src.fetch`）而不同步调整所有导入。CI 固定 Python 3.12（`.github/workflows/update.yml`）。

## 硬性约束

- **运行时零第三方依赖**：`src/` 只用标准库。不要 `pip install` 任何运行时依赖。本地开发工具（如 linter）可装，但不能进入运行时代码或 CI。
- **失败时保留旧文件**：任一赛区抓取失败，`main.py` 退出码非 0 且不写任何 `.ics`，保证已订阅文件不被空/残缺数据覆盖。改动抓取/输出流程时必须保持这个不变量。
- **`.ics` 手写实现**：`ics.py` 手写符合 RFC 5545（CRLF 行尾、75 字节折叠、TEXT 转义、稳定 UID）。不要引入 `icalendar` 之类的库来替代。
- **时间以 UTC 存储**，由客户端按本地时区显示。

## 常见改动

- 增删赛区：改 `src/main.py` 的 `OUTPUTS`(`文件名 -> (slug 列表, {语言: 显示名})`)。`leagueId` 运行时由 `getLeagues` 按 slug 动态解析,不硬编码。
- 增删语言：改 `LANGS`(`main.py`),并在 `ics.py` 的 `STRINGS` 加该语言的静态词条;赛区名/阶段名由 API 按 `hl` 返回。
- 回看比分窗口：`src/main.py` 的 `KEEP_COMPLETED_DAYS`。
- `dist/all.ics` 是聚合所有赛区的派生订阅(`main.py` 里复用 `ALL_SLUGS` 自动生成,写在 `OUTPUTS` 字面量外),增删赛区时自动跟随,无需单独维护。
- `fetch.py` 里的 `API_KEY` 是官网公开固定 key（非机密），不是需要保护的密钥。

## Lint / Format

```bash
ruff check src/        # 检查（--fix 自动修）
ruff format src/       # 格式化
```

配置见 `ruff.toml`。ruff 仅为本地/CI 开发工具，**不是运行时依赖** —— 不要把它写进运行时代码或当成 `src/` 的依赖。

## 提交规范

Conventional Commits（`feat:` / `fix:` / `chore:`），与 CI 自动提交风格一致。
