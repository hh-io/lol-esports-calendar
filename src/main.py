"""入口：抓取各赛区赛程，按订阅分组输出 dist/<name>.ics。

设计原则：任一赛区抓取失败时退出且不覆盖任何旧文件，
保证已订阅的 .ics 不会被写成空文件。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fetch import FetchError, get_events, get_league_ids
from ics import build_calendar

DIST = Path(__file__).resolve().parent.parent / "dist"

# 订阅分组：输出文件名 -> (日历显示名, 赛区 slug 列表)
OUTPUTS = {
    "lpl": ("LOL 赛程 · LPL", ["lpl"]),
    "lck": ("LOL 赛程 · LCK", ["lck"]),
    "intl": ("LOL 赛程 · 国际赛 (MSI/Worlds)", ["msi", "worlds"]),
}

# 所有需要抓取的赛区。
ALL_SLUGS = sorted({s for _, slugs in OUTPUTS.values() for s in slugs})

# 保留最近 N 天已结束的比赛，便于回看比分。
KEEP_COMPLETED_DAYS = 2


def main() -> int:
    try:
        leagues = get_league_ids(ALL_SLUGS)
        events_by_slug = {}
        for slug, info in leagues.items():
            evs = get_events(info["id"], include_completed_days=KEEP_COMPLETED_DAYS)
            events_by_slug[slug] = evs
            print(f"[info] {slug}: {len(evs)} 场比赛")
    except FetchError as err:
        print(f"[error] 抓取失败，保留现有 .ics 文件: {err}", file=sys.stderr)
        return 1

    DIST.mkdir(exist_ok=True)
    for filename, (cal_name, slugs) in OUTPUTS.items():
        events = []
        for slug in slugs:
            events.extend(events_by_slug.get(slug, []))
        events.sort(key=lambda e: e.start_utc)
        ics_text = build_calendar(cal_name, events)
        out_path = DIST / f"{filename}.ics"
        out_path.write_text(ics_text, encoding="utf-8")
        print(f"[info] 写入 {out_path} ({len(events)} 事件)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
