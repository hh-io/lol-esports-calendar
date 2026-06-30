"""把归一化事件渲染成 iCalendar (.ics) 文本。

只手写标准库实现，输出符合 RFC 5545 的折叠/转义规则，无第三方依赖。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fetch import Event

PRODID = "-//lol-esports-calendar//EN//"

# 日历正文的静态词条翻译。赛区名与阶段名由 API 按 hl 返回，不在此表内。
STRINGS = {
    "zh": {
        "league": "赛区",
        "stage": "阶段",
        "format": "赛制",
        "matchup": "对阵",
        "tbd": "待定",
        "updated": "数据更新",
    },
    "en": {
        "league": "League",
        "stage": "Stage",
        "format": "Format",
        "matchup": "Match",
        "tbd": "TBD",
        "updated": "Updated",
    },
    "ko": {
        "league": "리그",
        "stage": "단계",
        "format": "방식",
        "matchup": "대진",
        "tbd": "미정",
        "updated": "업데이트",
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
    prefix = ev.league_name or ev.league_slug.upper()
    block = f" ({ev.block})" if ev.block else ""
    return f"{prefix}: {vs}{block}"


def _description(ev: Event, generated_at: str, t: dict) -> str:
    parts = [f"{t['league']}: {ev.league_name}"]
    if ev.block:
        parts.append(f"{t['stage']}: {ev.block}")
    if ev.best_of:
        parts.append(f"{t['format']}: BO{ev.best_of}")
    if len(ev.teams) >= 2:
        parts.append(f"{t['matchup']}: {ev.teams[0]['name']} vs {ev.teams[1]['name']}")
    parts.append(f"{t['updated']}: {generated_at}")
    return "\n".join(parts)


def build_calendar(name: str, events: list[Event], lang: str = "zh") -> str:
    """生成单个 VCALENDAR 文本。lang 决定日历正文静态词条的语言。"""
    t = STRINGS.get(lang, STRINGS["zh"])
    now = datetime.now(UTC)
    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")
    generated_at = now.strftime("%Y-%m-%d %H:%M UTC")

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
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ev.uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{_ics_dt(ev.start_utc)}",
            f"DTEND:{_dt_plus(ev.start_utc, ev.duration_hours)}",
            f"SUMMARY:{_escape(_summary(ev, t))}",
            f"DESCRIPTION:{_escape(_description(ev, generated_at, t))}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
