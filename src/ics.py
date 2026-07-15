"""把归一化事件渲染成 iCalendar (.ics) 文本。

只手写标准库实现，输出符合 RFC 5545 的折叠/转义规则，无第三方依赖。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fetch import Event

PRODID = "-//lol-esports-calendar//EN//"

# 标题前缀用的赛事缩写，按 slug 索引（跨语言稳定，不受 API 显示名变动影响）。
# 只影响 SUMMARY；DESCRIPTION 仍保留 API 返回的全名。
SHORT_NAMES = {
    "ewc_lol": "EWC",
    "worlds": "Worlds",
}

# 日历正文的静态词条翻译。赛区名与阶段名由 API 按 hl 返回，不在此表内。
STRINGS = {
    "zh": {
        "league": "赛区",
        "stage": "阶段",
        "format": "赛制",
        "matchup": "对阵",
        "tbd": "待定",
    },
    "en": {
        "league": "League",
        "stage": "Stage",
        "format": "Format",
        "matchup": "Match",
        "tbd": "TBD",
    },
    "ko": {
        "league": "리그",
        "stage": "단계",
        "format": "방식",
        "matchup": "대진",
        "tbd": "미정",
    },
}


def _ics_dt(iso: str) -> str:
    """ISO8601 → iCalendar UTC 形式 YYYYMMDDTHHMMSSZ。"""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _dt_plus(iso: str, hours: float) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC)
    dt += timedelta(hours=hours)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _escape(text: str) -> str:
    """转义 TEXT 值中的特殊字符（RFC 5545 §3.3.11）。"""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """超过 75 字节的行按规范折叠（续行以单空格开头）。"""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out = []
    chunk = b""
    for ch in line:
        b = ch.encode("utf-8")
        # 续行前缀占 1 字节空格，限制 74 以留余量，避免拆断多字节字符。
        if len(chunk) + len(b) > 74:
            out.append(chunk.decode("utf-8"))
            chunk = b
        else:
            chunk += b
    out.append(chunk.decode("utf-8"))
    return "\r\n ".join(out)


def _summary(ev: Event, t: dict) -> str:
    if len(ev.teams) >= 2:
        a, b = ev.teams[0], ev.teams[1]
        vs = f"{a['code']} vs {b['code']}"
        # 已结束的场次附带比分。
        if ev.state == "completed" and a["score"] is not None and b["score"] is not None:
            vs = f"{a['code']} {a['score']}-{b['score']} {b['code']}"
    else:
        vs = t["tbd"]
    prefix = SHORT_NAMES.get(ev.league_slug) or ev.league_name or ev.league_slug.upper()
    block = f" ({ev.block})" if ev.block else ""
    return f"{prefix}: {vs}{block}"


def _description(ev: Event, t: dict) -> str:
    parts = [f"{t['league']}: {ev.league_name}"]
    if ev.block:
        parts.append(f"{t['stage']}: {ev.block}")
    if ev.best_of:
        parts.append(f"{t['format']}: BO{ev.best_of}")
    if len(ev.teams) >= 2:
        parts.append(f"{t['matchup']}: {ev.teams[0]['name']} vs {ev.teams[1]['name']}")
    return "\n".join(parts)


def build_calendar(name: str, events: list[Event], lang: str = "zh") -> str:
    """生成单个 VCALENDAR 文本。lang 决定日历正文静态词条的语言。

    输出是赛程数据的纯函数：DTSTAMP 由事件开始时间派生（不取当前时间），
    正文也不含生成时刻。这样赛程不变时每次输出逐字节一致，CI 不会每小时
    产生"只有时间戳变化"的空提交。
    """
    t = STRINGS.get(lang, STRINGS["zh"])

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
        "X-WR-TIMEZONE:UTC",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for ev in events:
        start = _ics_dt(ev.start_utc)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ev.uid}",
            # DTSTAMP 取开赛时间（稳定值），使输出不随生成时刻变化，见上方说明。
            f"DTSTAMP:{start}",
            f"DTSTART:{start}",
            f"DTEND:{_dt_plus(ev.start_utc, ev.duration_hours)}",
            f"SUMMARY:{_escape(_summary(ev, t))}",
            f"DESCRIPTION:{_escape(_description(ev, t))}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
