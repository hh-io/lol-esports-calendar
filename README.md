# lol-esports-calendar

自动抓取英雄联盟职业赛程（**LPL / LCK / MSI / 世界赛**），生成 Apple 日历可订阅的 `.ics` 文件，
由 GitHub Actions 每小时刷新一次并托管在 GitHub Pages 上。**纯标准库，零依赖。**

## 订阅链接

| 赛区 | 订阅 URL |
|------|----------|
| LPL（中国） | `https://hh-io.github.io/lol-esports-calendar/dist/lpl.ics` |
| LCK（韩国） | `https://hh-io.github.io/lol-esports-calendar/dist/lck.ics` |
| 国际赛（MSI/Worlds） | `https://hh-io.github.io/lol-esports-calendar/dist/intl.ics` |

> 自己 fork 部署时，把 `hh-io` / `lol-esports-calendar` 换成你的用户名 / 仓库名。

> 比赛时间以 UTC 存储，Apple 日历会自动按你的本地时区（北京时间）显示。

## Apple 日历订阅步骤

**macOS**：日历 App → 菜单栏「文件」→「新建日历订阅…」→ 粘贴上面的 URL →
把「自动刷新」设为「每小时」或「每天」。

**iPhone/iPad**：设置 → 日历 → 账户 → 添加账户 → 其他 → 添加已订阅的日历 → 粘贴 URL。

把 URL 里的 `https://` 换成 `webcal://` 可以直接点链接唤起日历 App。

## 本地运行

```bash
python3 src/main.py      # 生成 dist/lpl.ics、lck.ics、intl.ics
```

## 部署

1. 把本仓库推到 GitHub。
2. **Settings → Pages**：Source 选 `Deploy from a branch`，分支选 `main`、目录选 `/ (root)`。
   订阅路径即 `https://<user>.github.io/<repo>/dist/lpl.ics`。
   （如想去掉路径里的 `dist/`，可把 Pages 目录设为 `/docs` 并把输出目录改成 `docs/`。）
3. **Settings → Actions → General**：确保 Workflow 有 `Read and write permissions`。
4. 到 **Actions** 页手动点一次 `Update LoL calendars` → `Run workflow` 验证能生成并提交。
   之后每小时自动更新（比赛打完约 1～2 小时内，日历上该场会带上比分）。

## 结构

```
src/fetch.py   调 getLeagues 解析赛区 ID，分页抓 getSchedule，归一化事件
src/ics.py     事件 → RFC 5545 .ics 文本（稳定 UID、CRLF、75 字节折叠）
src/main.py    按订阅分组输出 dist/*.ics；任一赛区抓取失败则保留旧文件
.github/workflows/update.yml   定时 + 手动触发，有变更才提交
dist/          生成的 .ics（被 Pages 托管）
```

## 数据源与风险

数据来自 lolesports 官网自身使用的非官方接口
（`esports-api.lolesports.com/persisted/gw`，公开固定 `x-api-key`，非机密）。
该接口非官方，Riot 可能随时调整。脚本已做容错：

- `leagueId` 每次运行都从 `getLeagues` 动态解析（按 slug 匹配，不硬编码）。
- 网络/接口失败时退出并**保留上一次的 `.ics`**，不会写出空文件覆盖订阅。
- 休赛期某赛区暂无未来赛程时，对应 `.ics` 为空日历（正常现象，新赛程发布后自动出现）。

可在 `src/main.py` 的 `OUTPUTS` 里增删赛区（如加入 `lcs`、`lec`）。
