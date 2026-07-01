# lol-esports-calendar

**简体中文** · [English](README.en.md) · [한국어](README.ko.md)

自动抓取**英雄联盟职业联赛赛程**（**LPL / LCK / LEC / LCP / LTA / MSI / Worlds / 国际赛**），生成可订阅的 `.ics` 日历文件，
兼容 **Apple 日历、Google 日历、Outlook** 等任意支持 iCalendar（`.ics`）订阅的客户端。
由 GitHub Actions 每小时刷新一次并托管在 GitHub Pages 上。**纯标准库，零依赖。**

日历正文支持中文 / 英文 / 韩文三种语言（见下表）。

> 🌐 网页版订阅页：**<https://hh-io.github.io/lol-esports-calendar/>**（含各赛区订阅链接与订阅步骤）。

## 订阅链接

复制下面的链接即可订阅（日历正文为**中文**）。想要英文 / 韩文日历，点本页顶部的 **English / 한국어** 切换到对应说明。

| 赛区 | 订阅 URL |
|------|----------|
| LPL（中国） | `https://hh-io.github.io/lol-esports-calendar/dist/lpl.ics` |
| LCK（韩国） | `https://hh-io.github.io/lol-esports-calendar/dist/lck.ics` |
| LEC（欧洲） | `https://hh-io.github.io/lol-esports-calendar/dist/lec.ics` |
| LCP（太平洋） | `https://hh-io.github.io/lol-esports-calendar/dist/lcp.ics` |
| LTA（美洲） | `https://hh-io.github.io/lol-esports-calendar/dist/lta.ics` |
| 国际赛（MSI/Worlds/First Stand） | `https://hh-io.github.io/lol-esports-calendar/dist/intl.ics` |
| 全部赛区（含国际赛） | `https://hh-io.github.io/lol-esports-calendar/dist/all.ics` |

> 自己 fork 部署时，把 `hh-io` / `lol-esports-calendar` 换成你的用户名 / 仓库名。

> 比赛时间以 UTC 存储，Apple 日历会自动按你的本地时区（北京时间）显示。

## Apple 日历订阅步骤

**macOS**：日历 App → 菜单栏「文件」→「新建日历订阅…」→ 粘贴上面的 URL →
把「自动刷新」设为「每小时」或「每天」。

**iPhone/iPad**：设置 → 日历 → 账户 → 添加账户 → 其他 → 添加已订阅的日历 → 粘贴 URL。

把 URL 里的 `https://` 换成 `webcal://` 可以直接点链接唤起日历 App。

## Google 日历 / Outlook

同一个 `.ics` URL 也能在其它客户端订阅：

- **Google 日历**（网页版）：左侧「其他日历」→「＋」→「通过网址添加」→ 粘贴 URL。
- **Outlook**：「添加日历」→「从 Internet 订阅」→ 粘贴 URL。

## 本地运行

```bash
python3 src/main.py      # 生成 dist/*.ics 及 dist/en、dist/ko 多语言版本
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
src/fetch.py   调 getLeagues 解析赛区 ID，分页抓 getSchedule，归一化事件（hl 参数控制语言）
src/ics.py     事件 → RFC 5545 .ics 文本（稳定 UID、CRLF、75 字节折叠、静态词条多语言）
src/main.py    按语言 × 订阅分组输出 .ics；任一赛区抓取失败则保留旧文件
.github/workflows/update.yml   定时 + 手动触发，有变更才提交
dist/          中文 .ics；dist/en、dist/ko 为英文 / 韩文（被 Pages 托管）
```

## 数据源与风险

数据来自 lolesports 官网自身使用的非官方接口
（`esports-api.lolesports.com/persisted/gw`，公开固定 `x-api-key`，非机密）。
该接口非官方，Riot 可能随时调整。脚本已做容错：

- `leagueId` 每次运行都从 `getLeagues` 动态解析（按 slug 匹配，不硬编码）。
- 网络/接口失败时退出并**保留上一次的 `.ics`**，不会写出空文件覆盖订阅。
- 休赛期某赛区暂无未来赛程时，对应 `.ics` 为空日历（正常现象，新赛程发布后自动出现）。

可在 `src/main.py` 的 `OUTPUTS` 里增删赛区，在 `LANGS` 里增删语言（`slug` 见 `getLeagues`）。

## 许可

本项目**代码**以 [MIT](LICENSE) 许可发布。

赛程数据来自 lolesports，版权归 Riot Games 及相关方所有；本项目仅做格式转换、不主张任何数据权利，也与 Riot Games 无任何隶属或背书关系。
