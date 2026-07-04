// Cloudflare Worker：定时通过 GitHub API 触发 workflow_dispatch。
// 为什么存在：GitHub Actions 的 schedule 事件是尽力而为，高负载时会大量丢弃定时运行。
// 由外部可靠 cron 走 workflow_dispatch 触发不受此丢弃机制影响。
const WORKFLOW_DISPATCH_URL =
  "https://api.github.com/repos/hh-io/lol-esports-calendar/actions/workflows/update.yml/dispatches";

export default {
  async scheduled(event, env, ctx) {
    const res = await fetch(WORKFLOW_DISPATCH_URL, {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${env.GH_TOKEN}`,
        "X-GitHub-Api-Version": "2022-11-28",
        // GitHub API 强制要求 User-Agent，缺失会被拒。
        "User-Agent": "cf-worker-lol-esports-cron",
      },
      body: JSON.stringify({ ref: "main" }),
    });

    // 成功返回 204 No Content。任何非 2xx 都抛出，让失败显式出现在 Worker 日志/告警里，不静默吞掉。
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`GitHub workflow_dispatch failed: ${res.status} ${detail}`);
    }
    console.log(`workflow_dispatch ok: ${res.status}`);
  },
};
