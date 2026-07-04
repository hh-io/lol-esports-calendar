# cron-worker

Cloudflare Worker，定时通过 GitHub API 触发本仓库的 `update.yml`
workflow（`workflow_dispatch`）。用来替代 GitHub Actions 不可靠的 `schedule`
事件——`schedule` 在高负载时会被大量丢弃，而外部 cron 走 `workflow_dispatch`
不受影响。

与 `src/` 的 Python 运行时完全无关，只负责“定时触发”这一件事。

## 部署

用 `npx` 即可，无需全局安装 wrangler（需本机有 Node/npm）。

```bash
cd cron-worker
npx wrangler login             # 登录 Cloudflare 账号

# 写入 GitHub token（fine-grained PAT，仅本仓库 Actions: Read and write 权限）。
# token 不入库，只存在 Cloudflare secret 里。
npx wrangler secret put GH_TOKEN

npx wrangler deploy
```

## 验证

- 部署后在 Cloudflare Dashboard → Workers → 本 Worker → Settings → Triggers
  可看到 Cron。
- 手动测试定时逻辑：`wrangler dev --test-scheduled`，然后
  `curl "http://localhost:8787/__scheduled"`，成功会在日志打印 `workflow_dispatch ok: 204`。
- 或直接看 GitHub Actions 页面是否按点出现 `workflow_dispatch` 触发的运行。

## 改触发频率

改 `wrangler.toml` 的 `crons`，重新 `wrangler deploy`。
