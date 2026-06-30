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

    # 先把所有文件构建到内存，再统一校验、统一写入，保持全有或全无。
    planned: list[tuple[Path, str, int]] = []  # (路径, 内容, 事件数)
    for lang in LANGS:
        out_dir = DIST if lang == DEFAULT_LANG else DIST / lang
        by_slug = events_by_lang[lang]
        for filename, (slugs, names) in OUTPUTS.items():
            events = []
            for slug in slugs:
                events.extend(by_slug.get(slug, []))
            events.sort(key=lambda e: e.start_utc)
            cal_name = f"{CAL_PREFIX[lang]} · {names[lang]}"
            ics_text = build_calendar(cal_name, events, lang=lang)
            planned.append((out_dir / f"{filename}.ics", ics_text, len(events)))

    # 退化保护：接口可能返回 HTTP 200 却是空/残缺数据（赛区列表为空、结构变更），
    # 这种情况不会抛 FetchError，表现为「所有赛区一起归零」。仅当全部计划文件
    # 事件总数为 0、而磁盘上仍有非空旧文件时，才判为系统性退化、整体放弃写入。
    #
    # 注意只看「系统性归零」而非「任一文件归零」：单个赛区休赛期合法地变 0
    # （旧完赛记录滑出回看窗口）不应阻塞其余赛区的正常更新，其空日历照常写出。
    total_events = sum(count for _path, _text, count in planned)
    had_data = any(
        path.exists() and _existing_event_count(path) > 0 for path, _text, _count in planned
    )
    if total_events == 0 and had_data:
        print(
            "[error] 数据疑似系统性退化（全部赛区均为 0 事件，旧文件非空），保留现有 .ics 文件",
            file=sys.stderr,
        )
        return 1

    for path, ics_text, count in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ics_text, encoding="utf-8")
        print(f"[info] 写入 {path} ({count} 事件)")

    return 0


def _existing_event_count(path: Path) -> int:
    """已写出的 .ics 中 VEVENT 数量，用于判断数据是否退化。"""
    return path.read_text(encoding="utf-8").count("BEGIN:VEVENT")


if __name__ == "__main__":
    raise SystemExit(main())
