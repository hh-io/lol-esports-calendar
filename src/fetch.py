"""抓取 lolesports 赛程并归一化为内部事件结构。

数据源为 lolesports 官网自身使用的非官方 persisted query 接口。
仅依赖标准库，便于在 GitHub Actions 中零依赖运行。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC

# 官网公开固定 key（非机密），见 README 风险说明。
API_KEY = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
BASE_URLS = (
    "https://esports-api.lolesports.com/persisted/gw",
    "https://prod-relapi.ewp.gg/persisted/gw",  # 备用镜像
)
HL = "zh-CN"

# 每场比赛按 BoX 估算的时长（小时），用于推算日历事件的结束时间。
BEST_OF_HOURS = {1: 1.0, 2: 2.0, 3: 3.0, 5: 4.5}
DEFAULT_HOURS = 2.0


class FetchError(RuntimeError):
    """网络或接口异常，调用方据此决定保留旧文件。"""


@dataclass
class Event:
    uid: str
    league_slug: str
    league_name: str
    start_utc: str  # ISO8601，形如 2026-06-14T09:00:00Z
    block: str
    state: str  # unstarted / inProgress / completed
    best_of: int
    teams: list[dict] = field(default_factory=list)  # [{name, code, score}]

    @property
    def duration_hours(self) -> float:
        return BEST_OF_HOURS.get(self.best_of, DEFAULT_HOURS)


def _request(path: str, params: dict) -> dict:
    """带镜像回退与简单重试的 GET，返回解析后的 JSON。"""
    query = urllib.parse.urlencode(params, doseq=True)
    last_err: Exception | None = None
    for base in BASE_URLS:
        url = f"{base}/{path}?{query}"
        for attempt in range(3):
            req = urllib.request.Request(
                url,
                headers={"x-api-key": API_KEY, "Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return json.load(resp)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
                last_err = err
                time.sleep(1.5 * (attempt + 1))
    raise FetchError(f"请求 {path} 失败: {last_err}")


def get_league_ids(slugs: Iterable[str]) -> dict[str, dict]:
    """返回 {slug: {id, name}}，仅包含命中的目标赛区。"""
    data = _request("getLeagues", {"hl": HL})
    leagues = data.get("data", {}).get("leagues", [])
    wanted = set(slugs)
    result: dict[str, dict] = {}
    for lg in leagues:
        slug = lg.get("slug")
        if slug in wanted:
            result[slug] = {"id": lg["id"], "name": lg.get("name", slug.upper())}
    missing = wanted - result.keys()
    if missing:
        # 不致命：赛区可能改名或暂未开放，记录但继续。
        print(f"[warn] 未找到赛区 slug: {sorted(missing)}")
    return result


def _normalize(ev: dict) -> Event | None:
    """把单个原始 event 转成 Event；非 match 或缺字段则返回 None。"""
    if ev.get("type") != "match":
        return None
    match = ev.get("match") or {}
    match_id = match.get("id")
    start = ev.get("startTime")
    if not match_id or not start:
        return None
    teams = []
    for t in match.get("teams", []):
        score = (t.get("result") or {}).get("gameWins")
        teams.append(
            {
                "name": t.get("name", "TBD"),
                "code": t.get("code", "TBD"),
                "score": score,
            }
        )
    strategy = match.get("strategy") or {}
    league = ev.get("league") or {}
    return Event(
        uid=f"lolmatch-{match_id}@lol-esports-calendar",
        league_slug=league.get("slug", ""),
        league_name=league.get("name", ""),
        start_utc=start,
        block=ev.get("blockName") or "",
        state=ev.get("state", "unstarted"),
        best_of=int(strategy.get("count") or 0),
        teams=teams,
    )


def get_events(league_id: str, include_completed_days: int = 0) -> list[Event]:
    """抓取某赛区赛程，跟随分页向后翻完所有未来事件。

    include_completed_days: 保留最近 N 天内已结束的比赛（便于回看），0 表示不保留。
    """
    from datetime import datetime, timedelta

    cutoff = None
    if include_completed_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=include_completed_days)

    events: dict[str, Event] = {}
    page_token: str | None = None
    seen_tokens: set[str] = set()

    while True:
        params = {"hl": HL, "leagueId": league_id}
        if page_token:
            params["pageToken"] = page_token
        data = _request("getSchedule", params)
        schedule = data.get("data", {}).get("schedule", {}) or {}
        for raw in schedule.get("events", []):
            ev = _normalize(raw)
            if ev is None:
                continue
            if ev.state == "completed":
                if cutoff is None:
                    continue
                if _parse(ev.start_utc) < cutoff:
                    continue
            events[ev.uid] = ev
        page_token = (schedule.get("pages") or {}).get("newer")
        # newer 为 None 表示已到最新一页；防御性地避免 token 环。
        if not page_token or page_token in seen_tokens:
            break
        seen_tokens.add(page_token)

    return sorted(events.values(), key=lambda e: e.start_utc)


def _parse(iso: str):
    from datetime import datetime

    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
