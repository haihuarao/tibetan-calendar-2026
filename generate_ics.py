#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "calendar-2026.json"
DEFAULT_OUTPUT = ROOT / "calendar-2026.ics"

WEEKDAYS = "一二三四五六日"
GENERIC_NOTES = {"十斋日", "飞幡日"}
MONTH_LABELS = {
    "庄严月", "满意月", "神变月", "苦行月", "具香月", "萨嘎月",
    "作净月", "明净月", "具醉月", "具贤月", "天降月", "持众月",
}


def ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_line(line: str, limit: int = 75) -> list[str]:
    if not line:
        return [""]
    chunks: list[str] = []
    current = ""
    for char in line:
        candidate = current + char
        if current and len(candidate.encode("utf-8")) > limit:
            chunks.append(current)
            current = " " + char
        else:
            current = candidate
    chunks.append(current)
    return chunks


def tibetan_day_short(display: str) -> str:
    # 例如：八月初五 -> 初五；十一月闰初三 -> 闰初三。
    return display.split("月", 1)[-1]


def special_events(entry: dict, entries: list[dict]) -> list[str]:
    t = entry["tibetan"]
    month = t.get("month")
    day = t.get("day")
    events: list[str] = []

    if t.get("month_name") == "萨嘎月":
        if day in {7, 8, 15}:
            events.append("随念本师法会")
        if day is not None and 9 <= day <= 14:
            events.append("金刚萨埵法会")
        sagadawa_days = sorted(
            {e["tibetan"].get("day") for e in entries if e["tibetan"].get("month_name") == "萨嘎月"}
        )
        last_three = sagadawa_days[-3:]
        nirvana_names = [
            "三祖师涅槃法会-法王如意宝",
            "三祖师涅槃法会-麦彭仁波切",
            "三祖师涅槃法会-白玛邓灯尊者",
        ]
        if day in last_three:
            events.append(nirvana_names[last_three.index(day)])

    if month == 1 and day == 3:
        events.append("法王如意宝诞辰纪念日")
    if month == 6 and day in {1, 2, 3}:
        events.append("地藏法会")
    if month == 9 and day is not None and 15 <= day <= 22:
        events.append("极乐法会")
    if (month == 6 and day is not None and day >= 4) or (month == 7 and day is not None and day < 4):
        events.append("大藏经法会")
    if month == 11 and day == 15:
        events.append("法王涅槃日")
    if month == 7 and day == 8:
        events.append("大恩上师诞辰")
    if month == 8 and day == 25:
        events.append("嘎瓦上师诞辰")
    return events


def summary_for(entry: dict, fish: bool = False, entries: list[dict] | None = None) -> str:

    day = tibetan_day_short(entry["tibetan"]["display"])
    gatherings = [
        note
        for note in entry["notes"]
        if note in {"莲师荟供日", "空行母荟供日"}
    ]
    parts = [day]
    if entries is not None and fish:
        parts.extend(special_events(entry, entries))
    if gatherings:
        parts.append("、".join(gatherings))
    # 萨嘎月整月标记；其他月份只在藏历初八、十五、三十标记。
    should_mark_fish = (
        entry["tibetan"].get("month_name") == "萨嘎月"
        or entry["tibetan"].get("day") in {8, 15, 30}
    )
    if fish and should_mark_fish:
        parts.append("🐟")
    return " ".join(parts)

def description_for(entry: dict) -> str:
    date = dt.date.fromisoformat(entry["date"])
    lines = [
        f"公历：{date.year}年{date.month}月{date.day}日 星期{WEEKDAYS[date.weekday()]}",
        f"藏历火马年：{entry['tibetan']['display']}",
        f"藏历月名：{entry['tibetan']['month_name']}",
        f"农历丙午年：{entry['lunar']['display']}",
    ]
    if entry["tibetan"].get("previous_day_skipped"):
        lines.append("藏历备注：前一日为缺日")
    if entry["notes"]:
        lines.append("事项：")
        lines.extend(entry["notes"])
    lines.append("来源：2026（农历）藏历火马年月历.pdf")
    return "\n".join(lines)


def build_calendar(data_path: Path, output_path: Path, *, fish: bool = False, calendar_name: str | None = None, uid_prefix: str | None = None, calendar_description: str | None = None) -> None:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    entries = payload["entries"]
    if len(entries) != 365:
        raise ValueError(f"Expected 365 entries, got {len(entries)}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    calendar_name = calendar_name or ("2026 藏历火马年_v2" if fish else "2026 藏历火马年")
    uid_prefix = uid_prefix or ("tibetan-2026-fish" if fish else "tibetan-2026")
    calendar_description = calendar_description or (
        "2026 藏历火马年（萨嘎月整月及每月藏历初八、十五、三十标记 🐟，详情保留第一版信息）"
        if fish
        else payload["title"] + "（公历、农历、藏历对照，来源为用户提供的月历 PDF）"
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//M.R Bao//2026 Tibetan Calendar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(calendar_name)}",
        f"X-WR-CALDESC:{ics_escape(calendar_description)}",
        "X-WR-TIMEZONE:Asia/Shanghai",
        "X-PUBLISHED-TTL:PT1H",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-APPLE-CALENDAR-COLOR:#C24B2A",
    ]

    for entry in entries:
        start = dt.date.fromisoformat(entry["date"])
        end = start + dt.timedelta(days=1)
        uid = f"{uid_prefix}-{start:%Y%m%d}@tibetan-calendar.local"
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            f"SUMMARY:{ics_escape(summary_for(entry, fish=fish, entries=entries))}",
            f"DESCRIPTION:{ics_escape(description_for(entry))}",
            "TRANSP:TRANSPARENT",
            "SEQUENCE:0",
            "END:VEVENT",
        ]
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")
    output = "\r\n".join(
        folded
        for line in lines
        for folded in fold_line(line)
    ) + "\r\n"
    output_path.write_bytes(output.encode("utf-8"))
    print(f"Wrote {len(entries)} all-day events to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fish", action="store_true", help="Add 🐟 markers for Sagadawa month and Tibetan days 8, 15, and 30")
    parser.add_argument("--calendar-name")
    parser.add_argument("--uid-prefix")
    parser.add_argument("--calendar-description")
    args = parser.parse_args()
    build_calendar(args.data, args.output, fish=args.fish, calendar_name=args.calendar_name, uid_prefix=args.uid_prefix, calendar_description=args.calendar_description)


if __name__ == "__main__":
    main()
