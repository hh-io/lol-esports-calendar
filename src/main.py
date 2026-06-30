"""入口：抓取各赛区赛程，按订阅分组、按语言输出 .ics。

设计原则：任一赛区抓取失败时退出且不覆盖任何旧文件，
保证已订阅的 .ics 不会被写成空文件。

输出布局（默认语言中文放 dist 根目录，保持已发布订阅链接不变）：
    dist/<name>.ics        中文
    dist/en/<name>.ics     英文
    dist/ko/<name>.ics     韩文
"""

from __future__ import annotations

import sys
from pathlib import Path

from fetch import FetchError, get_events, get_league_ids
from ics import build_calendar

DIST = Path(__file__).resolve().parent.parent / "dist"

# 支持的语言：内部代码 -> API 的 hl 标签。默认语言（中文）输出到 dist 根目录。
LANGS = {
    "zh": "zh-CN",
    "en": "en-US",
    "ko": "ko-KR",
}
DEFAULT_LANG = "zh"

# 日历名前缀（按语言）。
CAL_PREFIX = {"zh": "LOL 赛程", "en": "LoL Schedule", "ko": "LoL 일정"}

# 订阅分组：输出文件名 -> (赛区 slug 列表, {语言: 该组显示名})。
OUTPUTS = {
    "lpl": (["lpl"], {"zh": "LPL", "en": "LPL", "ko": "LPL"}),
    "lck": (["lck"], {"zh": "LCK", "en": "LCK", "ko": "LCK"}),
    "lec": (["lec"], {"zh": "LEC", "en": "LEC", "ko": "LEC"}),
    "lcp": (["lcp"], {"zh": "LCP", "en": "LCP", "ko": "LCP"}),
    "lta": (
        ["lta_n", "lta_s"],
        {"zh": "LTA（美洲）", "en": "LTA (Americas)", "ko": "LTA (아메리카)"},
    ),
    "intl": (
        ["msi", "worlds", "first_stand"],
        {
            "zh": "国际赛 (MSI/Worlds/First Stand)",
            "en": "International (MSI/Worlds/First Stand)",
            "ko": "국제 대회 (MSI/Worlds/First Stand)",
        },
    ),
}

# 所有需要抓取的赛区。
ALL_SLUGS = sorted({s for slugs, _ in OUTPUTS.values() for s in slugs})

# 保留最近 N 天已结束的比赛，便于回看比分。
KEEP_COMPLETED_DAYS = 7


def main() -> int:
    # 先抓取所有语言、所有赛区。任一语言任一赛区失败即整体放弃，保留旧文件。
    events_by_lang: dict[str, dict] = {}
    try:
        for lang, hl in LANGS.items():
            leagues = get_league_ids(ALL_SLUGS, hl=hl)
            by_slug = {}
            for slug, info in leagues.items():
                evs = get_events(info["id"], include_completed_days=KEEP_COMPLETED_DAYS, hl=hl)
                by_slug[slug] = evs
                print(f"[info] {lang}/{slug}: {len(evs)} 场比赛")
            events_by_lang[lang] = by_slug
    except FetchError as err:
        print(f"[error] 抓取失败，保留现有 .ics 文件: {err}", file=sys.stderr)
        return 1

    for lang in LANGS:
        out_dir = DIST if lang == DEFAULT_LANG else DIST / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        by_slug = events_by_lang[lang]
        for filename, (slugs, names) in OUTPUTS.items():
            events = []
            for slug in slugs:
                events.extend(by_slug.get(slug, []))
            events.sort(key=lambda e: e.start_utc)
            cal_name = f"{CAL_PREFIX[lang]} · {names[lang]}"
            ics_text = build_calendar(cal_name, events, lang=lang)
            out_path = out_dir / f"{filename}.ics"
            out_path.write_text(ics_text, encoding="utf-8")
            print(f"[info] 写入 {out_path} ({len(events)} 事件)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
